"""
Recovery Workflow Orchestrator — Event-Driven State Machine

States:
  DETECTED → TRIAGED → INTERVENTION_SCHEDULED → INTERVENTION_SENT → RECOVERED
                                                                   → FAILED
                                                                   → LAPSED
                                                                   → CIRCUIT_BROKEN

Compliance guardrails (hard-coded):
  - Quiet hours: No contact 21:00–09:00 customer local time
  - Max 3 touchpoints per 7 days per customer
  - Circuit breaker: stops all dunning on dispute/chargeback < 500ms
  - Discount authority: max 5% only if LTV > ₹2.5L and churn risk > 85%
"""
import uuid
from datetime import datetime
from typing import Optional
import pytz

from sqlalchemy.orm import Session

from config import settings
from models.database import RecoveryEvent, RecoveryStatus, AttributionStatus, FailureCategory
from models.schemas import ClassificationResult, CustomerProfile, RetrySlot
from core.classifier import classify
from core.enrichment import enrich_customer
from core.retry_sequencer import generate_retry_schedule
from core.attribution import assign_group
from services.notification import dispatch_notification


def process_payment_event(
    db: Session,
    charge_id: str,
    error_code: str,
    event_type: str,
    amount: float,
    currency: str,
    customer_id: str,
    customer_email: str,
    customer_name: str,
    raw_payload: dict,
    bank_code: str = "HDFC",
) -> RecoveryEvent:
    """
    Main entry point. Ingests a payment failure event and runs the full pipeline:
      1. Classify failure
      2. Enrich customer
      3. Assign attribution group
      4. Generate retry schedule (if applicable)
      5. Schedule intervention
      6. Persist to ledger
    """

    # ── Step 1: Classify ──────────────────────────────────────────────────
    classification: ClassificationResult = classify(error_code, event_type)

    # ── Step 2: Enrich customer ───────────────────────────────────────────
    profile: CustomerProfile = enrich_customer(
        customer_id=customer_id,
        customer_email=customer_email,
        customer_name=customer_name,
        amount=amount,
    )

    # ── Step 3: Create recovery event ─────────────────────────────────────
    recovery_id = str(uuid.uuid4())
    event = RecoveryEvent(
        recovery_id=recovery_id,
        original_charge_id=charge_id,
        customer_id=profile.customer_id,
        customer_email=profile.email,
        customer_name=profile.name,
        raw_error_code=error_code,
        failure_category=classification.category.value,
        failure_description=classification.description,
        amount=amount,
        currency=currency,
        customer_ltv=profile.ltv,
        churn_risk_score=profile.churn_risk_score,
        timezone=profile.timezone,
        language_preference=profile.language_preference,
        status=RecoveryStatus.TRIAGED.value,
        raw_payload=raw_payload,
        intervention_trail=[],
        retry_schedule=[],
    )

    # ── Step 4: Assign holdout group ──────────────────────────────────────
    group = assign_group(recovery_id)
    event.attribution_status = group.value

    if group == AttributionStatus.HOLDOUT:
        # Control group: no intervention, just log
        event.status = RecoveryStatus.TRIAGED.value
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # ── Step 5: Compliance check ──────────────────────────────────────────
    if not _passes_compliance(db, profile.customer_id, profile.timezone):
        event.status = RecoveryStatus.INTERVENTION_SCHEDULED.value
        trail_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "channel": "SYSTEM",
            "template_id": "COMPLIANCE_HOLD",
            "tone_confidence": 1.0,
            "message_preview": "Intervention held: quiet hours or touchpoint limit reached.",
            "payer_response": None,
        }
        event.intervention_trail = [trail_entry]
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # ── Step 6: Generate retry schedule (soft declines / mandates) ────────
    if classification.is_retriable:
        slots: list[RetrySlot] = generate_retry_schedule(
            previous_failure_count=0,
            bank_code=bank_code,
            customer_timezone=profile.timezone,
            num_retries=3,
        )
        event.retry_schedule = [s.model_dump() for s in slots]

    # ── Step 7: Determine intervention channel & dispatch ─────────────────
    channel, template_id, message = _select_intervention(
        classification=classification,
        profile=profile,
        amount=amount,
        currency=currency,
    )

    notification_result = dispatch_notification(
        channel=channel,
        recipient_email=profile.email,
        customer_name=profile.name,
        message=message,
        recovery_id=recovery_id,
    )

    trail_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "channel": channel,
        "template_id": template_id,
        "tone_confidence": 0.97,
        "message_preview": message[:120],
        "payer_response": None,
    }

    event.intervention_trail = [trail_entry]
    event.touchpoint_count = 1
    event.status = RecoveryStatus.INTERVENTION_SENT.value

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def trigger_circuit_breaker(db: Session, charge_id: str) -> bool:
    """
    Immediately stop all active recovery workflows for a charge.
    Called on dispute/chargeback webhook. Target: < 500ms.
    """
    events = db.query(RecoveryEvent).filter(
        RecoveryEvent.original_charge_id == charge_id,
        RecoveryEvent.status.in_([
            RecoveryStatus.DETECTED.value,
            RecoveryStatus.TRIAGED.value,
            RecoveryStatus.INTERVENTION_SCHEDULED.value,
            RecoveryStatus.INTERVENTION_SENT.value,
        ])
    ).all()

    for event in events:
        event.status = RecoveryStatus.CIRCUIT_BROKEN.value
        trail = list(event.intervention_trail or [])
        trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "channel": "SYSTEM",
            "template_id": "CIRCUIT_BREAKER",
            "tone_confidence": 1.0,
            "message_preview": "⚡ Circuit breaker triggered: dispute/chargeback received. All recovery halted.",
            "payer_response": None,
        })
        event.intervention_trail = trail

    db.commit()
    return len(events) > 0


def mark_recovered(db: Session, charge_id: str, settlement_amount: float) -> Optional[RecoveryEvent]:
    """Mark a recovery event as RECOVERED after payment confirmation."""
    event = db.query(RecoveryEvent).filter(
        RecoveryEvent.original_charge_id == charge_id
    ).order_by(RecoveryEvent.created_at.desc()).first()

    if not event:
        return None

    event.status = RecoveryStatus.RECOVERED.value
    event.settlement_amount = settlement_amount
    event.recovered_at = datetime.utcnow()

    # Compute final attribution
    trail = list(event.intervention_trail or [])
    last_sent = None
    for t in trail:
        if t.get("channel") not in ("SYSTEM",):
            last_sent = datetime.fromisoformat(t["timestamp"])

    from core.attribution import compute_attribution
    final_attr = compute_attribution(
        recovered_at=datetime.utcnow(),
        last_intervention_sent_at=last_sent,
    )
    if event.attribution_status != AttributionStatus.HOLDOUT.value:
        event.attribution_status = final_attr.value

    db.commit()
    db.refresh(event)
    return event


# ── Internal helpers ───────────────────────────────────────────────────────

def _passes_compliance(db: Session, customer_id: str, timezone: str) -> bool:
    """
    Returns True if intervention is allowed:
      - Not in quiet hours (21:00–09:00 customer local)
      - Touchpoints in last 7 days < MAX_TOUCHPOINTS_PER_7_DAYS
    """
    try:
        tz = pytz.timezone(timezone)
        local_hour = datetime.now(tz).hour
        if local_hour >= settings.QUIET_HOURS_START or local_hour < settings.QUIET_HOURS_END:
            return False
    except Exception:
        pass

    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=7)
    recent_events = db.query(RecoveryEvent).filter(
        RecoveryEvent.customer_id == customer_id,
        RecoveryEvent.created_at >= cutoff,
        RecoveryEvent.touchpoint_count > 0,
    ).all()

    total_touchpoints = sum(e.touchpoint_count or 0 for e in recent_events)
    return total_touchpoints < settings.MAX_TOUCHPOINTS_PER_7_DAYS


def _select_intervention(
    classification: ClassificationResult,
    profile: CustomerProfile,
    amount: float,
    currency: str,
) -> tuple[str, str, str]:
    """Returns (channel, template_id, message)."""
    cat = classification.category.value
    name = profile.name.split()[0] if profile.name else "there"
    amt_str = f"₹{amount:,.0f}" if currency == "INR" else f"${amount:,.0f}"

    # Discount eligibility
    offer_discount = (
        profile.ltv >= settings.MIN_LTV_FOR_DISCOUNT
        and profile.churn_risk_score >= settings.MIN_CHURN_RISK_FOR_DISCOUNT
    )
    discount_text = " We'd like to offer you a 5% discount on your next renewal." if offer_discount else ""

    # Language-aware prefix
    lang = profile.language_preference
    greeting = "Namaste" if lang == "hi" else ("வணக்கம்" if lang == "ta" else "Hello")

    if cat == "SOFT_DECLINE":
        channel = "WHATSAPP"
        template_id = "SOFT_DECLINE_RETRY_V2"
        message = (
            f"{greeting} {name}! Your payment of {amt_str} couldn't be processed due to "
            f"a temporary issue. We've scheduled an automatic retry at the optimal time.{discount_text} "
            f"You can also complete payment instantly: [pay link]"
        )

    elif cat == "HARD_DECLINE":
        channel = "EMAIL"
        template_id = "HARD_DECLINE_CARD_SWAP_V1"
        message = (
            f"{greeting} {name}, your payment of {amt_str} was declined. "
            f"Please update your payment method securely with one click: [card update link]. "
            f"No login required."
        )

    elif cat == "CREDENTIAL_EXPIRY":
        channel = "WHATSAPP"
        template_id = "CARD_EXPIRY_UPDATE_V3"
        message = (
            f"{greeting} {name}! Your saved card seems to have expired. "
            f"Update it in 30 seconds to keep your {amt_str} subscription active: [update link]"
        )

    elif cat == "MANDATE_FAILURE":
        channel = "WHATSAPP"
        template_id = "MANDATE_HINGLISH_V1"
        message = (
            f"{greeting} {name}! Aapka {amt_str} ka auto-payment process nahi ho saka. "
            f"Koi baat nahi — abhi ek tap mein pay karein: [UPI link]. "
            f"Ya apna mandate dobara activate karein: [mandate link]"
        )

    elif cat == "CART_ABANDONED":
        channel = "SMS"
        template_id = "CART_ABANDON_NUDGE_V2"
        message = (
            f"{greeting} {name}! You left {amt_str} worth of items in your cart. "
            f"Complete your purchase now — your cart is saved: [checkout link]"
        )

    elif cat == "B2B_OVERDUE":
        channel = "EMAIL"
        template_id = "B2B_AR_CHASER_V1"
        message = (
            f"Dear {name}, this is a gentle reminder regarding invoice #{profile.customer_id[:8].upper()} "
            f"for {amt_str} which is currently overdue. "
            f"Please confirm your payment date so we can update our records: [PTP link]"
        )

    else:
        channel = "EMAIL"
        template_id = "GENERIC_RECOVERY_V1"
        message = f"{greeting} {name}, we noticed an issue with your recent payment of {amt_str}. Please review: [link]"

    return channel, template_id, message
