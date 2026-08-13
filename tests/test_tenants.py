from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_tenant_with_free_plan():
    """A new tenant should receive an active Free subscription."""

    response = client.post(
        "/tenants",
        json={"name": "Test Company"},
    )

    response_data = response.json()

    assert response.status_code == 201
    assert response_data["name"] == "Test Company"
    assert response_data["plan"] == "free"
    assert response_data["status"] == "active"
    assert response_data["id"]