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