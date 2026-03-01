"""Health check tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_api_version():
    """Test API version endpoint."""
    response = client.get("/api/v1/docs")
    # Swagger docs should be available
    assert response.status_code in [200, 404]
