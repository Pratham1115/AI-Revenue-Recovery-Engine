"""
Diagnostic Root-Cause Classifier
Maps Razorpay error codes → FailureCategory with recommended action.
Deterministic, no LLM — pure rule-based for auditability.
"""
from models.schemas import ClassificationResult, FailureCategory

# ── Error Code → Category Mapping ─────────────────────────────────────────

# Hard declines: do NOT retry, card is compromised or permanently blocked
HARD_DECLINE_CODES = {
    "STOLEN_CARD", "DO_NOT_HONOR", "PICKUP_CARD", "RESTRICTED_CARD",
    "SECURITY_VIOLATION", "LOST_CARD", "TRANSACTION_NOT_PERMITTED",
    "BAD_REQUEST_ERROR",  # Razorpay catch-all for invalid params
}

# Soft declines: temporary, retry with timing optimization
SOFT_DECLINE_CODES = {
    "INSUFFICIENT_FUNDS", "TRY_AGAIN_LATER", "NETWORK_ERROR",
    "GATEWAY_ERROR", "SERVER_ERROR", "PAYMENT_TIMEOUT",
    "EXCEEDS_WITHDRAWAL_LIMIT", "EXCEEDS_FREQUENCY_LIMIT",
    "insufficient_funds", "try_again_later", "network_timeout",
    "processing_error",
}

# Credential expiry: card details stale
CREDENTIAL_EXPIRY_CODES = {
    "EXPIRED_CARD", "INVALID_CARD", "INVALID_EXPIRY", "INVALID_CVV",
    "CARD_VELOCITY_EXCEEDED", "FORMAT_ERROR",
    "expired_card", "incorrect_cvc", "invalid_expiry_year",
    "card_velocity_exceeded",
}

# Mandate / UPI Autopay failures
MANDATE_FAILURE_CODES = {
    "MANDATE_REVOKED", "MANDATE_PAUSED", "MANDATE_CANCELLED",
    "UPI_PIN_FAILURE", "UPI_BALANCE_INSUFFICIENT", "PRE_DEBIT_NOTIFY_FAILED",
    "AUTOPAY_FAILED", "RECURRING_CHARGE_FAILED",
}

# Cart abandonment — not a PSP error, detected via event type
CART_ABANDONED_CODES = {"CART_ABANDONED", "CHECKOUT_ABANDONED", "SESSION_EXPIRED"}

# B2B overdue — invoice-level aging
B2B_OVERDUE_CODES = {"INVOICE_OVERDUE", "PAYMENT_TERMS_BREACHED", "NET30_OVERDUE", "NET60_OVERDUE"}

# ── Human-readable descriptions ────────────────────────────────────────────

DESCRIPTIONS = {
    FailureCategory.HARD_DECLINE: "Card permanently blocked or flagged for fraud. No retry on this instrument.",
    FailureCategory.SOFT_DECLINE: "Temporary failure — insufficient funds or transient network issue. Retry during optimal bank clearing window.",
    FailureCategory.CREDENTIAL_EXPIRY: "Card credentials are stale or invalid. Update payment method via secure magic link.",
    FailureCategory.MANDATE_FAILURE: "UPI Autopay or e-mandate failed. Trigger pre-debit notification retry with fallback payment link.",
    FailureCategory.CART_ABANDONED: "High-intent checkout abandoned. Send personalized recovery nudge within 10 minutes.",
    FailureCategory.B2B_OVERDUE: "B2B invoice unpaid beyond agreed terms. Initiate autonomous AR chaser workflow.",
    FailureCategory.UNKNOWN: "Unrecognized failure code. Route to manual review queue.",
}

ACTIONS = {
    FailureCategory.HARD_DECLINE: "Send secure 1-click payment method replacement link (WhatsApp/Email). Zero retries on current instrument.",
    FailureCategory.SOFT_DECLINE: "Schedule ML-optimized retry during issuer liquidity window (salary day peaks: 1st/5th of month, 06:00–09:00 IST).",
    FailureCategory.CREDENTIAL_EXPIRY: "Trigger Network Token fetch / Card Updater. If unavailable, dispatch zero-login card swap link.",
    FailureCategory.MANDATE_FAILURE: "Send Hinglish WhatsApp nudge for pre-debit approval. Offer instant UPI payment link as fallback.",
    FailureCategory.CART_ABANDONED: "Dispatch personalized WhatsApp/SMS with pre-filled payment link and contextual incentive within 10 minutes.",
    FailureCategory.B2B_OVERDUE: "Initiate AP verification email → PTP negotiation → auto-log Promise-to-Pay commitment.",
    FailureCategory.UNKNOWN: "Flag for manual triage. Do not auto-intervene.",
}

RETRIABLE = {
    FailureCategory.HARD_DECLINE: False,
    FailureCategory.SOFT_DECLINE: True,
    FailureCategory.CREDENTIAL_EXPIRY: False,
    FailureCategory.MANDATE_FAILURE: True,
    FailureCategory.CART_ABANDONED: False,
    FailureCategory.B2B_OVERDUE: False,
    FailureCategory.UNKNOWN: False,
}


def classify(error_code: str, event_type: str = "") -> ClassificationResult:
    """
    Classify a Razorpay failure event into a FailureCategory.

    Args:
        error_code: The raw error/reason code from Razorpay payload.
        event_type: Optional Razorpay event type (e.g. 'payment.failed', 'subscription.halted').

    Returns:
        ClassificationResult with category, confidence, and recommended action.
    """
    code_upper = (error_code or "").upper().strip()
    code_original = (error_code or "").strip()

    # Event-type shortcuts
    if event_type in ("cart.abandoned", "checkout.abandoned"):
        return _build(FailureCategory.CART_ABANDONED, code_original, 0.99)

    if event_type in ("invoice.overdue", "payment_link.expired"):
        return _build(FailureCategory.B2B_OVERDUE, code_original, 0.95)

    if event_type in ("mandate.revoked", "nach.debit_failed", "recurring.charge_failed"):
        return _build(FailureCategory.MANDATE_FAILURE, code_original, 0.97)

    # Code-based matching (check original casing too)
    if code_upper in HARD_DECLINE_CODES or code_original in HARD_DECLINE_CODES:
        return _build(FailureCategory.HARD_DECLINE, code_original, 0.99)

    if code_upper in SOFT_DECLINE_CODES or code_original in SOFT_DECLINE_CODES:
        return _build(FailureCategory.SOFT_DECLINE, code_original, 0.95)

    if code_upper in CREDENTIAL_EXPIRY_CODES or code_original in CREDENTIAL_EXPIRY_CODES:
        return _build(FailureCategory.CREDENTIAL_EXPIRY, code_original, 0.97)

    if code_upper in MANDATE_FAILURE_CODES or code_original in MANDATE_FAILURE_CODES:
        return _build(FailureCategory.MANDATE_FAILURE, code_original, 0.96)

    if code_upper in CART_ABANDONED_CODES or code_original in CART_ABANDONED_CODES:
        return _build(FailureCategory.CART_ABANDONED, code_original, 0.99)

    if code_upper in B2B_OVERDUE_CODES or code_original in B2B_OVERDUE_CODES:
        return _build(FailureCategory.B2B_OVERDUE, code_original, 0.94)

    # Fuzzy fallback: partial match on keywords
    for keyword, category in [
        ("INSUFFICIENT", FailureCategory.SOFT_DECLINE),
        ("EXPIRED", FailureCategory.CREDENTIAL_EXPIRY),
        ("STOLEN", FailureCategory.HARD_DECLINE),
        ("MANDATE", FailureCategory.MANDATE_FAILURE),
        ("ABANDONED", FailureCategory.CART_ABANDONED),
        ("OVERDUE", FailureCategory.B2B_OVERDUE),
    ]:
        if keyword in code_upper:
            return _build(category, code_original, 0.75)

    return _build(FailureCategory.UNKNOWN, code_original, 0.50)


def _build(category: FailureCategory, raw_code: str, confidence: float) -> ClassificationResult:
    return ClassificationResult(
        category=category,
        confidence=confidence,
        raw_code=raw_code,
        description=DESCRIPTIONS[category],
        recommended_action=ACTIONS[category],
        is_retriable=RETRIABLE[category],
    )
