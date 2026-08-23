"""
Holdout-Group Attribution Engine

Formula:
  Net_Agent_Recovery = Total_Cohort_Recovered - (Control_Group_Recovery_Rate × Treatment_Cohort_Total)

A continuous 5% randomized holdout group is maintained per merchant tier.
Events routed to holdout receive NO intervention — their organic recovery rate
becomes the baseline for computing true agent lift.

Attribution statuses:
  HOLDOUT         — In control group. No intervention. Used to measure baseline.
  AGENT_DRIVEN    — Recovered after agent intervention within attribution window.
  ORGANIC_BASELINE— Recovered with no agent action (outside intervention window).
  PENDING         — Outcome not yet determined.
"""
import random
import hashlib
from datetime import datetime, timedelta
from typing import Tuple

from config import settings
from models.database import AttributionStatus


# Attribution window: if customer recovers within N hours of intervention, credit agent
ATTRIBUTION_WINDOW_HOURS = 72


def assign_group(recovery_id: str, merchant_tier: str = "standard") -> AttributionStatus:
    """
    Deterministically assign event to holdout or treatment group.
    Uses MD5 hash of recovery_id for stable, reproducible assignment.

    5% → HOLDOUT (no intervention)
    95% → Treatment (intervention proceeds normally)
    """
    h = int(hashlib.md5(recovery_id.encode()).hexdigest(), 16)
    # Map to 0-99 range
    bucket = h % 100
    holdout_pct = int(settings.HOLDOUT_RATE * 100)  # default 5

    if bucket < holdout_pct:
        return AttributionStatus.HOLDOUT
    return AttributionStatus.PENDING


def compute_attribution(
    recovered_at: datetime,
    last_intervention_sent_at: datetime | None,
    attribution_window_hours: int = ATTRIBUTION_WINDOW_HOURS,
) -> AttributionStatus:
    """
    Determine attribution status once a recovery is confirmed.

    If recovered within attribution window after intervention → AGENT_DRIVEN
    If no intervention was sent → ORGANIC_BASELINE
    """
    if last_intervention_sent_at is None:
        return AttributionStatus.ORGANIC_BASELINE

    window_end = last_intervention_sent_at + timedelta(hours=attribution_window_hours)
    if recovered_at <= window_end:
        return AttributionStatus.AGENT_DRIVEN
    return AttributionStatus.ORGANIC_BASELINE


def compute_net_agent_recovery(
    total_cohort_recovered: float,
    control_group_recovery_rate: float,
    treatment_cohort_total: int,
) -> dict:
    """
    Compute net agent recovery using holdout group formula.

    Args:
        total_cohort_recovered: Total $ recovered in treatment group.
        control_group_recovery_rate: Fraction recovered in holdout (organic baseline).
        treatment_cohort_total: Total number of events in treatment group.

    Returns:
        Dict with net_recovery, baseline_estimate, gross_lift_pct.
    """
    baseline_estimate = control_group_recovery_rate * treatment_cohort_total
    net_recovery = max(0.0, total_cohort_recovered - baseline_estimate)
    gross_lift_pct = (
        round((net_recovery / baseline_estimate * 100), 2)
        if baseline_estimate > 0 else 0.0
    )

    return {
        "net_agent_recovery": round(net_recovery, 2),
        "baseline_estimate": round(baseline_estimate, 2),
        "gross_lift_pct": gross_lift_pct,
        "formula": f"Net = {total_cohort_recovered:.2f} - ({control_group_recovery_rate:.3f} × {treatment_cohort_total}) = {net_recovery:.2f}",
    }
