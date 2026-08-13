import hashlib
import hmac
import json
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


client = TestClient(app)

TEST_WEBHOOK_SECRET = "whsec_test_secret"


def create_signature(
    payload: bytes,
    secret: str,
    timestamp: int,
) -> str:
    """Create a Stripe-style webhook signature."""

    signed_payload = (
        f"{timestamp}.".encode("utf-8")
        + payload
    )

    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=signed_payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return f"t={timestamp},v1={signature}"


def create_test_tenant() -> str:
    """Create a tenant for webhook testing."""

    response = client.post(
        "/tenants",
        json={
            "name": f"Webhook Test {uuid4()}",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_forged_webhook_is_rejected(monkeypatch):
    """A webhook with an invalid signature must return 400."""

    monkeypatch.setattr(
        settings,
        "stripe_webhook_secret",
        TEST_WEBHOOK_SECRET,
    )

    response = client.post(
        "/webhooks/stripe",
        content=b'{"id":"evt_forged"}',
        headers={
            "Stripe-Signature": "invalid-signature",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid Stripe webhook signature."
    }


def test_checkout_webhook_upgrades_tenant_and_deduplicates(
    monkeypatch,
):
    """A valid Checkout event upgrades once and ignores replay."""

    monkeypatch.setattr(
        settings,
        "stripe_webhook_secret",
        TEST_WEBHOOK_SECRET,
    )

    tenant_id = create_test_tenant()
    event_id = f"evt_{uuid4().hex}"

    event = {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{uuid4().hex}",
                "object": "checkout.session",
                "client_reference_id": tenant_id,
                "metadata": {
                    "tenant_id": tenant_id,
                },
                "customer": f"cus_{uuid4().hex}",
                "subscription": f"sub_{uuid4().hex}",
            }
        },
    }

    payload = json.dumps(
        event,
        separators=(",", ":"),
    ).encode("utf-8")

    timestamp = int(time.time())

    signature = create_signature(
        payload=payload,
        secret=TEST_WEBHOOK_SECRET,
        timestamp=timestamp,
    )

    first_response = client.post(
        "/webhooks/stripe",
        content=payload,
        headers={
            "Stripe-Signature": signature,
        },
    )

    second_response = client.post(
        "/webhooks/stripe",
        content=payload,
        headers={
            "Stripe-Signature": signature,
        },
    )

    usage_response = client.get(
        f"/usage/{tenant_id}"
    )

    assert first_response.status_code == 200
    assert first_response.json()["duplicate"] is False

    assert second_response.status_code == 200
    assert second_response.json()["duplicate"] is True

    assert usage_response.status_code == 200
    assert usage_response.json()["plan"] == "pro"
    assert usage_response.json()["status"] == "active"
    assert usage_response.json()["api_calls"]["limit"] == 10_000
    assert usage_response.json()["ai_tokens"]["limit"] == 1_000_000