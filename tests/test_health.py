from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    """The health endpoint should confirm that the API is running."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "usage-metering-billing-engine",
    }

def test_create_tenant_rejects_short_name():
    """Tenant names shorter than two characters should be rejected."""

    response = client.post(
        "/tenants",
        json={"name": "A"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_short"