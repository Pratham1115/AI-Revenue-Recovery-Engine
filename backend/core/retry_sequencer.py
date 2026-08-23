"""
ML Retry Sequencer
Generates an optimal retry schedule for soft declines and mandate failures.

Model: RandomForestClassifier trained on synthetic bank clearing data.
Features: hour_of_day, day_of_month, bank_code_hash, prev_failure_count, is_salary_day
Target: recovery_success (binary)

Salary-day peaks (Indian market):
  - 1st and 5th of each month (corporate salary credits)
  - 25th–28th (some mid-month payroll cycles)
  - Optimal hours: 06:00–09:00 IST (post-settlement batch run)
"""
import numpy as np
import hashlib
from datetime import datetime, timedelta
from typing import List
import pytz

from models.schemas import RetrySlot

# ── Synthetic training data generation ────────────────────────────────────

def _generate_training_data(n_samples: int = 5000):
    """
    Generate synthetic bank clearing success rates by time window.
    Based on public RBI settlement cycle documentation and industry patterns.
    """
    rng = np.random.default_rng(42)
    hours = rng.integers(0, 24, n_samples)
    days = rng.integers(1, 29, n_samples)
    prev_failures = rng.integers(0, 5, n_samples)
    bank_hashes = rng.integers(0, 50, n_samples)

    # Success probability heuristic
    success_prob = np.zeros(n_samples)

    for i in range(n_samples):
        h, d, pf = hours[i], days[i], prev_failures[i]

        # Salary day bonus (1st, 5th, 25th-28th of month)
        salary_bonus = 0.25 if d in (1, 5) else (0.10 if 25 <= d <= 28 else 0.0)

        # Morning clearing window bonus (06:00-09:00 IST = 00:30-03:30 UTC)
        hour_bonus = 0.20 if 6 <= h <= 9 else (0.10 if 10 <= h <= 13 else -0.05)

        # Penalty for repeated failures
        failure_penalty = pf * 0.07

        base = 0.40 + salary_bonus + hour_bonus - failure_penalty
        success_prob[i] = np.clip(base + rng.normal(0, 0.05), 0.05, 0.95)

    labels = (rng.random(n_samples) < success_prob).astype(int)

    X = np.column_stack([hours, days, prev_failures, bank_hashes])
    return X, labels


# Train model at import time (fast, ~200ms on synthetic data)
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler

    _X, _y = _generate_training_data()
    _scaler = StandardScaler()
    _X_scaled = _scaler.fit_transform(_X)
    _model = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)
    _model.fit(_X_scaled, _y)
    _MODEL_READY = True
except ImportError:
    _MODEL_READY = False


# ── Retry Window Labels ────────────────────────────────────────────────────

def _label_window(hour: int, day: int) -> str:
    if day in (1, 5) and 6 <= hour <= 9:
        return "🌅 Salary Day Morning Peak"
    if day in (1, 5):
        return "📅 Salary Day Window"
    if 25 <= day <= 28 and 6 <= hour <= 9:
        return "🌅 Month-End Clearing Peak"
    if 6 <= hour <= 9:
        return "🌄 Morning Clearing Window"
    if 10 <= hour <= 13:
        return "☀️ Midday Settlement Window"
    if 14 <= hour <= 17:
        return "🌆 Afternoon Window"
    return "🌙 Off-Peak Window"


def _bank_hash(bank_code: str) -> int:
    return int(hashlib.md5((bank_code or "DEFAULT").encode()).hexdigest(), 16) % 50


# ── Public API ─────────────────────────────────────────────────────────────

def generate_retry_schedule(
    previous_failure_count: int = 0,
    bank_code: str = "HDFC",
    customer_timezone: str = "Asia/Kolkata",
    num_retries: int = 3,
) -> List[RetrySlot]:
    """
    Generate an optimized retry schedule for a failed payment.

    Returns up to `num_retries` slots ranked by predicted success probability,
    anchored to salary-day peaks and morning clearing windows.
    """
    tz = pytz.timezone(customer_timezone)
    now_local = datetime.now(tz)
    bh = _bank_hash(bank_code)

    candidates = []

    # Generate candidate windows over the next 7 days
    for delta_days in range(0, 8):
        candidate_date = now_local + timedelta(days=delta_days)
        day_of_month = candidate_date.day

        for hour in [6, 7, 9, 12, 15]:
            candidate_dt = candidate_date.replace(hour=hour, minute=0, second=0, microsecond=0)

            # Don't schedule in the past
            if candidate_dt <= now_local + timedelta(minutes=30):
                continue

            features = np.array([[hour, day_of_month, previous_failure_count, bh]])

            if _MODEL_READY:
                features_scaled = _scaler.transform(features)
                proba = _model.predict_proba(features_scaled)[0][1]
            else:
                # Fallback heuristic if sklearn not available
                salary_bonus = 0.25 if day_of_month in (1, 5) else 0.0
                hour_bonus = 0.20 if 6 <= hour <= 9 else 0.05
                proba = min(0.40 + salary_bonus + hour_bonus - previous_failure_count * 0.05, 0.95)

            candidates.append({
                "dt": candidate_dt,
                "score": proba,
                "hour": hour,
                "day": day_of_month,
            })

    # Sort by score descending, take top N
    candidates.sort(key=lambda x: x["score"], reverse=True)
    top = candidates[:num_retries]
    top.sort(key=lambda x: x["dt"])  # Re-sort chronologically

    slots = []
    for c in top:
        slots.append(RetrySlot(
            scheduled_at=c["dt"].isoformat(),
            confidence_score=round(c["score"], 3),
            reason=f"Predicted {round(c['score']*100, 1)}% success probability for {bank_code} at {c['hour']:02d}:00 local time",
            window_label=_label_window(c["hour"], c["day"]),
        ))

    return slots
