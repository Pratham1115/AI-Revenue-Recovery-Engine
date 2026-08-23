from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


class FailureCategory(str, Enum):
    HARD_DECLINE = "HARD_DECLINE"
    SOFT_DECLINE = "SOFT_DECLINE"
    CREDENTIAL_EXPIRY = "CREDENTIAL_EXPIRY"
    MANDATE_FAILURE = "MANDATE_FAILURE"
    CART_ABANDONED = "CART_ABANDONED"
    B2B_OVERDUE = "B2B_OVERDUE"
    UNKNOWN = "UNKNOWN"


class RecoveryStatus(str, Enum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    INTERVENTION_SCHEDULED = "INTERVENTION_SCHEDULED"
    INTERVENTION_SENT = "INTERVENTION_SENT"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    LAPSED = "LAPSED"
    CIRCUIT_BROKEN = "CIRCUIT_BROKEN"


class AttributionStatus(str, Enum):
    AGENT_DRIVEN = "AGENT_DRIVEN"
    ORGANIC_BASELINE = "ORGANIC_BASELINE"
    HOLDOUT = "HOLDOUT"
    PENDING = "PENDING"


class InterventionTrailItem(BaseModel):
    timestamp: str
    channel: str  # EMAIL | SMS | WHATSAPP | VOICE | PAYMENT_LINK
    template_id: str
    tone_confidence: float = 1.0
    message_preview: str
    payer_response: Optional[str] = None


class ClassificationResult(BaseModel):
    category: FailureCategory
    confidence: float
    raw_code: str
    description: str
    recommended_action: str
    is_retriable: bool


class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    email: str
    ltv: float
    churn_risk_score: float
    timezone: str
    language_preference: str
    avg_settlement_days: float
    dispute_risk_score: float


class RetrySlot(BaseModel):
    scheduled_at: str
    confidence_score: float
    reason: str
    window_label: str  # e.g. "Salary Day Peak", "Morning Clearing Window"


class RecoveryEventResponse(BaseModel):
    recovery_id: str
    original_charge_id: str
    customer_id: Optional[str]
    customer_email: Optional[str]
    customer_name: Optional[str]
    raw_error_code: Optional[str]
    failure_category: str
    failure_description: Optional[str]
    amount: Optional[float]
    currency: str
    customer_ltv: float
    churn_risk_score: float
    status: str
    attribution_status: str
    retry_schedule: List[Any]
    touchpoint_count: int
    settlement_amount: Optional[float]
    intervention_trail: List[Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SimulateEventRequest(BaseModel):
    scenario: str = Field(..., description="Scenario key: soft_decline | expired_card | mandate_failure | cart_abandoned | b2b_overdue | hard_decline")
    amount: Optional[float] = 4999.0
    customer_name: Optional[str] = "Rahul Sharma"
    customer_email: Optional[str] = "rahul@example.com"


class DashboardSummary(BaseModel):
    total_events: int
    total_recovered: int
    total_amount_recovered: float
    gross_recovery_rate: float
    agent_driven_count: int
    organic_count: int
    holdout_count: int
    net_agent_recovery: float
    active_interventions: int
    category_breakdown: Dict[str, int]
    recent_events: List[RecoveryEventResponse]
