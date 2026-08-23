"""
Demo Event Simulator
Fires synthetic Razorpay-style payment failure events to demonstrate
the full recovery pipeline without needing live API keys.
"""
import uuid
import random
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db, RecoveryEvent, RecoveryStatus
from models.schemas import SimulateEventRequest
from core.orchestrator import process_payment_event, mark_recovered

router = APIRouter(prefix="/simulate", tags=["Simulator"])

# ── Scenario definitions ────────────────────────────────────────────────────

SCENARIOS = {
    "soft_decline": {
        "error_code": "INSUFFICIENT_FUNDS",
        "event_type": "payment.failed",
        "bank_code": "HDFC",
        "description": "💳 Soft Decline — Insufficient Funds",
    },
    "hard_decline": {
        "error_code": "DO_NOT_HONOR",
        "event_type": "payment.failed",
        "bank_code": "ICICI",
        "description": "🚫 Hard Decline — Card Blocked",
    },
    "expired_card": {
        "error_code": "EXPIRED_CARD",
        "event_type": "payment.failed",
        "bank_code": "SBI",
        "description": "⏰ Expired Card",
    },
    "mandate_failure": {
        "error_code": "MANDATE_REVOKED",
        "event_type": "mandate.revoked",
        "bank_code": "AXIS",
        "description": "📱 UPI Mandate / Autopay Failure",
    },
    "cart_abandoned": {
        "error_code": "CART_ABANDONED",
        "event_type": "cart.abandoned",
        "bank_code": "KOTAK",
        "description": "🛒 High-Intent Cart Abandonment",
    },
    "b2b_overdue": {
        "error_code": "INVOICE_OVERDUE",
        "event_type": "invoice.overdue",
        "bank_code": "HDFC",
        "description": "📄 B2B Invoice Overdue (Net-30)",
    },
}

DEMO_CUSTOMERS = [
    ("Rahul Sharma", "rahul.sharma@techcorp.in", "cust_RS001"),
    ("Priya Patel", "priya.patel@startup.io", "cust_PP002"),
    ("Arjun Mehta", "arjun.mehta@enterprise.com", "cust_AM003"),
    ("Ananya Singh", "ananya.singh@fintech.co", "cust_AS004"),
    ("Vikram Iyer", "vikram.iyer@saas.in", "cust_VI005"),
]


@router.post("/fire")
def simulate_event(req: SimulateEventRequest, db: Session = Depends(get_db)):
    """
    Fire a synthetic payment failure event.
    Runs the full pipeline: classify → enrich → attribute → retry schedule → notify.
    """
    scenario_key = req.scenario.lower().replace(" ", "_")
    scenario = SCENARIOS.get(scenario_key)

    if not scenario:
        return {
            "error": f"Unknown scenario '{req.scenario}'",
            "available": list(SCENARIOS.keys()),
        }

    charge_id = f"pay_{uuid.uuid4().hex[:16]}"
    customer = random.choice(DEMO_CUSTOMERS)
    name = req.customer_name or customer[0]
    email = req.customer_email or customer[1]
    cust_id = customer[2]

    event = process_payment_event(
        db=db,
        charge_id=charge_id,
        error_code=scenario["error_code"],
        event_type=scenario["event_type"],
        amount=req.amount,
        currency="INR",
        customer_id=cust_id,
        customer_email=email,
        customer_name=name,
        raw_payload={"simulated": True, "scenario": scenario_key},
        bank_code=scenario["bank_code"],
    )

    return {
        "scenario": scenario["description"],
        "recovery_id": event.recovery_id,
        "charge_id": charge_id,
        "failure_category": event.failure_category,
        "status": event.status,
        "attribution_status": event.attribution_status,
        "retry_schedule": event.retry_schedule,
        "intervention_trail": event.intervention_trail,
        "customer_ltv": event.customer_ltv,
        "churn_risk_score": event.churn_risk_score,
    }


@router.post("/recover/{recovery_id}")
def simulate_recovery(recovery_id: str, db: Session = Depends(get_db)):
    """Simulate a successful payment recovery (e.g. customer clicked the payment link)."""
    event = db.query(RecoveryEvent).filter(RecoveryEvent.recovery_id == recovery_id).first()
    if not event:
        return {"error": "Recovery event not found"}

    recovered_event = mark_recovered(db, event.original_charge_id, event.amount or 999.0)
    return {
        "status": "RECOVERED",
        "recovery_id": recovery_id,
        "settlement_amount": recovered_event.settlement_amount,
        "attribution_status": recovered_event.attribution_status,
    }


@router.post("/bulk")
def simulate_bulk(count: int = 20, db: Session = Depends(get_db)):
    """Fire multiple random events for demo data seeding."""
    scenario_keys = list(SCENARIOS.keys())
    results = []

    for i in range(min(count, 50)):  # cap at 50
        scenario_key = random.choice(scenario_keys)
        req = SimulateEventRequest(
            scenario=scenario_key,
            amount=random.choice([499, 999, 2499, 4999, 9999, 24999]),
        )
        result = simulate_event(req, db)
        results.append(result)

        # Randomly mark ~35% as recovered for realistic demo stats
        if random.random() < 0.35 and "recovery_id" in result:
            simulate_recovery(result["recovery_id"], db)

    return {"fired": len(results), "events": results}


@router.get("/scenarios")
def list_scenarios():
    """List all available simulation scenarios."""
    return [
        {"key": k, "description": v["description"], "error_code": v["error_code"]}
        for k, v in SCENARIOS.items()
    ]
