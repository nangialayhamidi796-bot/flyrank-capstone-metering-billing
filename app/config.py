from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load application settings from environment variables."""

    app_name: str = "Usage Metering and Billing Engine"
    app_env: str = "development"

    database_url: str = "sqlite:///./metering_billing.db"

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""

    free_api_call_limit: int = 1000
    free_ai_token_limit: int = 100_000
    pro_api_call_limit: int = 10_000
    pro_ai_token_limit: int = 1_000_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()