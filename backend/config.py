import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # App
    APP_NAME: str = "RevEngine AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Razorpay
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_demo")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "demo_secret")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "webhook_secret")

    # Database
    DATABASE_URL: str = "sqlite:///./revengine.db"

    # Attribution
    HOLDOUT_RATE: float = 0.05  # 5% holdout group
    MAX_TOUCHPOINTS_PER_7_DAYS: int = 3
    QUIET_HOURS_START: int = 21  # 9 PM local time
    QUIET_HOURS_END: int = 9    # 9 AM local time

    # Recovery
    MAX_DISCOUNT_PCT: float = 5.0
    MIN_LTV_FOR_DISCOUNT: float = 250000.0  # ₹2.5L
    MIN_CHURN_RISK_FOR_DISCOUNT: float = 0.85

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
