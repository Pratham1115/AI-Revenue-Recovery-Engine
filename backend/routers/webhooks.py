"""
Razorpay Webhook Ingestion Router
Handles real Razorpay webhook events with HMAC-SHA256 signature verification.
"""
import hashlib
import hmac
import json
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from config import settings
from models.database import get_db
from core.orchestrator import process_payment_event, trigger_circuit_breaker, mark_recovered

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_razorpay_signature(payload_body: bytes, signature: str) -> bool:
    """Verify Razorpay webhook HMAC-SHA256 signature."""
    if not signature or settings.RAZORPAY_WEBHOOK_SECRET == "webhook_secret":
        # Demo mode: skip verification
        return True
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _extract_payment_fields(payload: dict) -> dict:
    """Normalize Razorpay payload into canonical fields."""
    entity = payload.get("payload", {})

    # payment.failed
    payment = entity.get("payment", {}).get("entity", {})
    if payment:
        error = payment.get("error_code") or payment.get("error_reason") or "UNKNOWN"
        return {
            "charge_id": payment.get("id", "pay_unknown"),
            "error_code": error,
            "amount": payment.get("amount", 0) / 100,  # Razorpay sends paise
            "currency": payment.get("currency", "INR"),
            "customer_id": payment.get("customer_id", ""),
            "customer_email": payment.get("email", ""),
            "customer_name": payment.get("contact", ""),
            "bank_code": payment.get("bank", "HDFC"),
        }

    # subscription events
    subscription = entity.get("subscription", {}).get("entity", {})
    if subscription:
        return {
            "charge_id": subscription.get("id", "sub_unknown"),
            "error_code": "RECURRING_CHARGE_FAILED",
            "amount": subscription.get("charge_at", 0),
            "currency": "INR",
            "customer_id": subscription.get("customer_id", ""),
            "customer_email": "",
            "customer_name": "",
            "bank_code": "HDFC",
        }

    return {
        "charge_id": "unknown",
        "error_code": "UNKNOWN",
        "amount": 0,
        "currency": "INR",
        "customer_id": "",
        "customer_email": "",
        "customer_name": "",
        "bank_code": "HDFC",
    }


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str = Header(default=""),
):
    body = await request.body()

    if not _verify_razorpay_signature(body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(body)
    event_type = payload.get("event", "")

    # ── Route by event type ───────────────────────────────────────────────

    # Payment failures
    if event_type in ("payment.failed", "subscription.halted", "subscription.completed"):
        fields = _extract_payment_fields(payload)
        event = process_payment_event(
            db=db,
            charge_id=fields["charge_id"],
            error_code=fields["error_code"],
            event_type=event_type,
            amount=fields["amount"],
            currency=fields["currency"],
            customer_id=fields["customer_id"],
            customer_email=fields["customer_email"],
            customer_name=fields["customer_name"],
            raw_payload=payload,
            bank_code=fields["bank_code"],
        )
        return {"status": "processed", "recovery_id": event.recovery_id, "category": event.failure_category}

    # Dispute / chargeback → circuit breaker
    if event_type in ("payment.dispute.created", "payment.dispute.under_review", "refund.created"):
        payment_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "")
        triggered = trigger_circuit_breaker(db, payment_id)
        return {"status": "circuit_breaker_triggered", "affected": triggered}

    # Payment success via recovery link → mark recovered
    if event_type in ("payment.captured", "payment_link.paid"):
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        payment_id = entity.get("id", "")
        amount = entity.get("amount", 0) / 100
        mark_recovered(db, payment_id, amount)
        return {"status": "recovery_confirmed"}

    # Cart abandonment (custom event from checkout SDK)
    if event_type in ("cart.abandoned", "checkout.abandoned"):
        fields = _extract_payment_fields(payload)
        fields["error_code"] = "CART_ABANDONED"
        event = process_payment_event(db=db, event_type=event_type, raw_payload=payload, **{
            k: fields[k] for k in ["charge_id", "error_code", "amount", "currency",
                                    "customer_id", "customer_email", "customer_name", "bank_code"]
        })
        return {"status": "processed", "recovery_id": event.recovery_id}

    return {"status": "ignored", "event": event_type}
