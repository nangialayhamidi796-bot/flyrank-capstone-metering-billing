from app.config import settings


def test_default_settings():
    """Default development settings should load correctly."""

    assert settings.app_name == "Usage Metering and Billing Engine"
    assert settings.app_env == "development"
    assert settings.free_api_call_limit == 1000
    assert settings.free_ai_token_limit == 100_000
    assert settings.pro_api_call_limit == 10_000
    assert settings.pro_ai_token_limit == 1_000_000