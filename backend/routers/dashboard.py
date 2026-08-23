"""
Dashboard Stats API
Provides aggregated metrics for the frontend dashboard.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from models.database import get_db, RecoveryEvent, RecoveryStatus, AttributionStatus
from models.schemas import DashboardSummary, RecoveryEventResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Aggregated KPIs for the main dashboard."""
    all_events = db.query(RecoveryEvent).all()
    total_events = len(all_events)

    recovered = [e for e in all_events if e.status == RecoveryStatus.RECOVERED.value]
    total_recovered = len(recovered)
    total_amount_recovered = sum(e.settlement_amount or 0 for e in recovered)

    gross_recovery_rate = round(total_recovered / total_events * 100, 1) if total_events > 0 else 0.0

    agent_driven = [e for e in recovered if e.attribution_status == AttributionStatus.AGENT_DRIVEN.value]
    organic = [e for e in recovered if e.attribution_status == AttributionStatus.ORGANIC_BASELINE.value]
    holdout = [e for e in all_events if e.attribution_status == AttributionStatus.HOLDOUT.value]

    # Net agent recovery formula
    holdout_recovered = len([e for e in holdout if e.status == RecoveryStatus.RECOVERED.value])
    control_rate = holdout_recovered / len(holdout) if holdout else 0.0
    treatment_total = total_events - len(holdout)
    baseline_estimate = control_rate * treatment_total
    net_agent_recovery = max(0.0, total_amount_recovered - baseline_estimate)

    active = [
        e for e in all_events
        if e.status in (
            RecoveryStatus.TRIAGED.value,
            RecoveryStatus.INTERVENTION_SCHEDULED.value,
            RecoveryStatus.INTERVENTION_SENT.value,
        )
    ]

    # Category breakdown
    category_breakdown = {}
    for e in all_events:
        cat = e.failure_category or "UNKNOWN"
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    # Recent events (last 10)
    recent = (
        db.query(RecoveryEvent)
        .order_by(RecoveryEvent.created_at.desc())
        .limit(10)
        .all()
    )

    return DashboardSummary(
        total_events=total_events,
        total_recovered=total_recovered,
        total_amount_recovered=round(total_amount_recovered, 2),
        gross_recovery_rate=gross_recovery_rate,
        agent_driven_count=len(agent_driven),
        organic_count=len(organic),
        holdout_count=len(holdout),
        net_agent_recovery=round(net_agent_recovery, 2),
        active_interventions=len(active),
        category_breakdown=category_breakdown,
        recent_events=[RecoveryEventResponse.model_validate(e) for e in recent],
    )


@router.get("/events", response_model=List[RecoveryEventResponse])
def get_all_events(
    limit: int = 50,
    offset: int = 0,
    status: str = None,
    category: str = None,
    db: Session = Depends(get_db),
):
    """Paginated list of all recovery events for the ledger view."""
    query = db.query(RecoveryEvent)
    if status:
        query = query.filter(RecoveryEvent.status == status)
    if category:
        query = query.filter(RecoveryEvent.failure_category == category)
    events = query.order_by(RecoveryEvent.created_at.desc()).offset(offset).limit(limit).all()
    return [RecoveryEventResponse.model_validate(e) for e in events]


@router.get("/attribution-stats")
def get_attribution_stats(db: Session = Depends(get_db)):
    """Attribution breakdown for the donut chart."""
    all_events = db.query(RecoveryEvent).all()
    stats = {
        "AGENT_DRIVEN": 0,
        "ORGANIC_BASELINE": 0,
        "HOLDOUT": 0,
        "PENDING": 0,
    }
    for e in all_events:
        key = e.attribution_status or "PENDING"
        stats[key] = stats.get(key, 0) + 1

    return stats


@router.get("/recovery-trend")
def get_recovery_trend(days: int = 7, db: Session = Depends(get_db)):
    """Daily recovery counts for the trend chart."""
    result = []
    for i in range(days - 1, -1, -1):
        day_start = datetime.utcnow().replace(hour=0, minute=0, second=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        total = db.query(RecoveryEvent).filter(
            RecoveryEvent.created_at >= day_start,
            RecoveryEvent.created_at < day_end,
        ).count()

        recovered = db.query(RecoveryEvent).filter(
            RecoveryEvent.created_at >= day_start,
            RecoveryEvent.created_at < day_end,
            RecoveryEvent.status == RecoveryStatus.RECOVERED.value,
        ).count()

        result.append({
            "date": day_start.strftime("%b %d"),
            "total": total,
            "recovered": recovered,
            "rate": round(recovered / total * 100, 1) if total > 0 else 0,
        })

    return result
