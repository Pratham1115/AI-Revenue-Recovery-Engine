"""
Notification Service (Mock)
In demo mode: logs all notifications to console and returns a mock result.
In production: integrate Twilio (SMS/WhatsApp), SendGrid (Email), Exotel (Voice).
"""
import uuid
from datetime import datetime


def dispatch_notification(
    channel: str,
    recipient_email: str,
    customer_name: str,
    message: str,
    recovery_id: str,
) -> dict:
    """
    Mock notification dispatch.
    Returns a result dict simulating a successful send.
    """
    msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.utcnow().isoformat()

    # In production: call Twilio / SendGrid API here
    print(f"[{timestamp}] [SEND] [{channel}] -> {recipient_email} | Recovery: {recovery_id}")
    print(f"    Message: {message[:100]}...")

    return {
        "message_id": msg_id,
        "channel": channel,
        "recipient": recipient_email,
        "status": "SENT",
        "timestamp": timestamp,
        "recovery_id": recovery_id,
    }
