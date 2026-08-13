from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models import SubscriptionStatus, Tenant
from tests.conftest import TestingSessionLocal


client = TestClient(app)


def create_test_tenant() -> str:
    """Create a tenant and return its generated ID."""

    response = client.post(
        "/tenants",
        json={"name": f"Metering Test {uuid4()}"},
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_duplicate_request_does_not_double_count():
    """The same idempotency key must create only one usage event."""

    tenant_id = create_test_tenant()

    request_body = {
        "tenant_id": tenant_id,
        "input_tokens": 500,
        "cached_input_tokens": 100,
        "output_tokens": 200,
        "reasoning_tokens": 50,
    }

    headers = {
        "Idempotency-Key": "generate-request-001",
    }

    first_response = client.post(
        "/generate",
        json=request_body,
        headers=headers,
    )

    second_response = client.post(
        "/generate",
        json=request_body,
        headers=headers,
    )

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert first_data["duplicate"] is False
    assert second_data["duplicate"] is True

    assert first_data["event_id"] == second_data["event_id"]
    assert first_data["api_calls_used"] == 1
    assert second_data["api_calls_used"] == 1

    assert first_data["ai_tokens_used"] == 850
    assert second_data["ai_tokens_used"] == 850


def test_reused_key_with_different_data_returns_409():
    """One idempotency key cannot represent two different requests."""

    tenant_id = create_test_tenant()

    headers = {
        "Idempotency-Key": "reused-key-001",
    }

    first_response = client.post(
        "/generate",
        json={
            "tenant_id": tenant_id,
            "input_tokens": 100,
            "cached_input_tokens": 0,
            "output_tokens": 50,
            "reasoning_tokens": 0,
        },
        headers=headers,
    )

    second_response = client.post(
        "/generate",
        json={
            "tenant_id": tenant_id,
            "input_tokens": 200,
            "cached_input_tokens": 0,
            "output_tokens": 50,
            "reasoning_tokens": 0,
        },
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": (
            "This idempotency key was already used "
            "with different request data."
        )
    }


def test_ai_token_quota_boundary():
    """Just under and exactly at the quota are allowed; over is rejected."""

    tenant_id = create_test_tenant()

    just_under_response = client.post(
        "/generate",
        json={
            "tenant_id": tenant_id,
            "input_tokens": 99_999,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
        },
        headers={
            "Idempotency-Key": "quota-just-under",
        },
    )

    exact_limit_response = client.post(
        "/generate",
        json={
            "tenant_id": tenant_id,
            "input_tokens": 1,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
        },
        headers={
            "Idempotency-Key": "quota-exact-limit",
        },
    )

    over_limit_response = client.post(
        "/generate",
        json={
            "tenant_id": tenant_id,
            "input_tokens": 1,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
        },
        headers={
            "Idempotency-Key": "quota-over-limit",
        },
    )

    assert just_under_response.status_code == 201
    assert just_under_response.json()["ai_tokens_used"] == 99_999

    assert exact_limit_response.status_code == 201
    assert exact_limit_response.json()["ai_tokens_used"] == 100_000

    assert over_limit_response.status_code == 429
    assert over_limit_response.json() == {
        "detail": "Monthly AI-token quota exceeded."
    }
    assert over_limit_response.headers["Retry-After"] == "3600"


def test_inactive_subscription_returns_402():
    """An unpaid tenant must not perform billable actions."""

    tenant_id = create_test_tenant()

    database = TestingSessionLocal()

    try:
        tenant = database.get(Tenant, tenant_id)
        tenant.subscription.status = SubscriptionStatus.UNPAID
        database.commit()
    finally:
        database.close()

    response = client.post(
        "/generate",
        json={
            "tenant_id": tenant_id,
            "input_tokens": 100,
            "cached_input_tokens": 0,
            "output_tokens": 50,
            "reasoning_tokens": 0,
        },
        headers={
            "Idempotency-Key": "unpaid-request-001",
        },
    )

    assert response.status_code == 402
    assert response.json() == {
        "detail": (
            "The subscription is not active. "
            "Upgrade or update payment."
        )
    }