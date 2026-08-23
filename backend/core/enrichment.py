"""
Customer Enrichment Engine
Appends LTV, churn risk score, timezone, language preference,
and dispute risk before the event enters triage.

Uses synthetic/heuristic scoring for demo — production would
query a CRM/DWH (HubSpot, Segment, BigQuery).
"""
import random
import hashlib
from models.schemas import CustomerProfile


# Synthetic timezone pool weighted toward Indian users (buildathon focus)
TIMEZONE_POOL = [
    ("Asia/Kolkata", 0.60),
    ("Asia/Dubai", 0.10),
    ("America/New_York", 0.10),
    ("Europe/London", 0.08),
    ("Asia/Singapore", 0.07),
    ("Australia/Sydney", 0.05),
]

LANGUAGE_POOL = [
    ("hi", 0.35),   # Hindi
    ("en", 0.40),   # English
    ("te", 0.08),   # Telugu
    ("ta", 0.07),   # Tamil
    ("mr", 0.05),   # Marathi
    ("bn", 0.05),   # Bengali
]


def _seeded_choice(pool, seed_str: str):
    """Deterministic weighted random choice based on customer ID seed."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    cumulative = 0.0
    threshold = (h % 10000) / 10000.0
    for value, weight in pool:
        cumulative += weight
        if threshold < cumulative:
            return value
    return pool[-1][0]


def enrich_customer(
    customer_id: str,
    customer_email: str = "",
    customer_name: str = "",
    amount: float = 0.0,
) -> CustomerProfile:
    """
    Generate enriched customer profile.

    In production this would:
    - Query BigQuery/Segment for historical LTV
    - Fetch churn risk from an ML model endpoint
    - Pull timezone from CRM/profile service

    For demo: deterministically derived from customer_id hash so
    the same customer always gets the same profile.
    """
    seed = customer_id or customer_email or "default"
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)

    # LTV: ₹5K – ₹10L range, seeded so same customer is consistent
    ltv = round(5000 + (h % 995000) / 10.0, 2)

    # Churn risk: 0.0 – 1.0
    churn_risk = round(0.1 + ((h >> 8) % 900) / 1000.0, 3)

    # Dispute risk: 0.0 – 0.3 (low by default)
    dispute_risk = round((h >> 16) % 300 / 1000.0, 3)

    # Average settlement days: 1–60
    avg_settlement = round(1 + (h >> 4) % 59, 1)

    timezone = _seeded_choice(TIMEZONE_POOL, seed + "_tz")
    language = _seeded_choice(LANGUAGE_POOL, seed + "_lang")

    return CustomerProfile(
        customer_id=customer_id or f"cust_{seed[:8]}",
        name=customer_name or "Unknown Customer",
        email=customer_email or f"{seed[:6]}@example.com",
        ltv=ltv,
        churn_risk_score=churn_risk,
        timezone=timezone,
        language_preference=language,
        avg_settlement_days=avg_settlement,
        dispute_risk_score=dispute_risk,
    )
