"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Bingo Market"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/bingo_market"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120  # 2 hours
    refresh_token_expire_days: int = 7

    # Login security
    login_max_attempts: int = 5  # Max failed login attempts
    login_lockout_duration_minutes: int = 30  # Lockout duration after max attempts

    # Compliance - Vietnam market limits
    vnd_daily_limit: int = 500_000  # 500K VND
    vnd_monthly_limit: int = 5_000_000  # 5M VND
    min_age: int = 18
    min_recharge_amount: int = 10_000  # 10K VND

    # L10n
    default_language: str = "vi"
    supported_languages: str = "vi,en"  # Comma-separated string

    def get_supported_languages(self) -> list[str]:
        """Get supported languages as a list."""
        return self.supported_languages.split(",")

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # LLM Service (Content Moderation)
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_test_mode: bool = True

    # Payment Gateway - MoMo
    momo_access_key: str = ""
    momo_secret_key: str = ""
    momo_partner_code: str = ""

    # Payment Gateway - ZaloPay
    zalopay_app_id: str = ""
    zalopay_key_1: str = ""
    zalopay_key_2: str = ""


settings = Settings()
