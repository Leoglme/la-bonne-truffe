"""Smoke test: the app starts and /health answers."""

from fastapi.testclient import TestClient


def test_health_reports_api_and_database_healthy(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["services"] == {"api": "healthy", "database": "healthy"}


def test_openapi_schema_lists_the_routes(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    for path in ("/api/v1/health", "/api/v1/auth/login", "/api/v1/notifications/subscribe", "/api/v1/departments"):
        assert path in paths
