from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Enum as SAEnum, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
import enum

DATABASE_URL = "sqlite:///./revengine.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Enums ──────────────────────────────────────────────────────────────────

class FailureCategory(str, enum.Enum):
    HARD_DECLINE = "HARD_DECLINE"
    SOFT_DECLINE = "SOFT_DECLINE"
    CREDENTIAL_EXPIRY = "CREDENTIAL_EXPIRY"
    MANDATE_FAILURE = "MANDATE_FAILURE"
    CART_ABANDONED = "CART_ABANDONED"
    B2B_OVERDUE = "B2B_OVERDUE"
    UNKNOWN = "UNKNOWN"


class RecoveryStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    INTERVENTION_SCHEDULED = "INTERVENTION_SCHEDULED"
    INTERVENTION_SENT = "INTERVENTION_SENT"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    LAPSED = "LAPSED"
    CIRCUIT_BROKEN = "CIRCUIT_BROKEN"


class AttributionStatus(str, enum.Enum):
    AGENT_DRIVEN = "AGENT_DRIVEN"
    ORGANIC_BASELINE = "ORGANIC_BASELINE"
    HOLDOUT = "HOLDOUT"
    PENDING = "PENDING"


# ── Models ─────────────────────────────────────────────────────────────────

class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    recovery_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_charge_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)

    # Failure details
    raw_error_code = Column(String, nullable=True)
    failure_category = Column(String, nullable=False, default=FailureCategory.UNKNOWN)
    failure_description = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String, default="INR")

    # Customer enrichment
    customer_ltv = Column(Float, default=0.0)
    churn_risk_score = Column(Float, default=0.0)
    timezone = Column(String, default="Asia/Kolkata")
    language_preference = Column(String, default="en")

    # State machine
    status = Column(String, default=RecoveryStatus.DETECTED)
    attribution_status = Column(String, default=AttributionStatus.PENDING)

    # Retry scheduling
    retry_schedule = Column(JSON, default=list)     # List of scheduled retry timestamps
    touchpoint_count = Column(Integer, default=0)

    # Attribution
    settlement_amount = Column(Float, nullable=True)

    # Intervention trail — ordered log of all touchpoints
    intervention_trail = Column(JSON, default=list)

    # Source event payload
    raw_payload = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    recovered_at = Column(DateTime, nullable=True)


class RetryAttempt(Base):
    __tablename__ = "retry_attempts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recovery_id = Column(String, nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    outcome = Column(String, nullable=True)  # SUCCESS / FAILED / PENDING
    confidence_score = Column(Float, nullable=True)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DashboardStats(Base):
    """Cached daily rollup stats for fast dashboard reads."""
    __tablename__ = "dashboard_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(String, nullable=False, unique=True)  # YYYY-MM-DD
    total_events = Column(Integer, default=0)
    total_recovered = Column(Integer, default=0)
    total_amount_recovered = Column(Float, default=0.0)
    agent_driven_count = Column(Integer, default=0)
    organic_count = Column(Integer, default=0)
    holdout_count = Column(Integer, default=0)
    breakdown = Column(JSON, default=dict)  # Per category counts
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
