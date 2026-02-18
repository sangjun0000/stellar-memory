"""Tests for P7 REST API server."""

import os
import pytest

try:
    from fastapi.testclient import TestClient
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

pytestmark = pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi not installed")


@pytest.fixture
def client():
    from stellar_memory.server import create_api_app
    from stellar_memory.config import StellarConfig
    config = StellarConfig(db_path=":memory:")
    app, memory = create_api_app(config)
    return TestClient(app)


@pytest.fixture
def auth_client():
    """Client with API key auth enabled."""
    os.environ["STELLAR_API_KEY"] = "test-key-123"
    try:
        from stellar_memory.server import create_api_app
        from stellar_memory.config import StellarConfig
        config = StellarConfig(db_path=":memory:")
        app, memory = create_api_app(config)
        yield TestClient(app)
    finally:
        del os.environ["STELLAR_API_KEY"]


class TestServerEndpoints:
    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["healthy"] is True

    def test_store(self, client):
        resp = client.post("/api/v1/store", json={
            "content": "Test memory", "importance": 0.7,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "zone" in data

    def test_recall(self, client):
        client.post("/api/v1/store", json={"content": "Python is great"})
        resp = client.get("/api/v1/recall", params={"q": "Python"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_forget(self, client):
        resp = client.post("/api/v1/store", json={"content": "to delete"})
        mem_id = resp.json()["id"]
        resp = client.delete(f"/api/v1/forget/{mem_id}")
        assert resp.status_code == 200
        assert resp.json()["removed"] is True

    def test_forget_not_found(self, client):
        resp = client.delete("/api/v1/forget/nonexistent-id")
        assert resp.status_code == 404

    def test_memories_list(self, client):
        client.post("/api/v1/store", json={"content": "Memory A"})
        client.post("/api/v1/store", json={"content": "Memory B"})
        resp = client.get("/api/v1/memories")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data

    def test_memories_zone_filter(self, client):
        client.post("/api/v1/store", json={"content": "Test", "importance": 0.5})
        resp = client.get("/api/v1/memories", params={"zone": 0})
        assert resp.status_code == 200

    def test_stats(self, client):
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_memories" in data
        assert "zones" in data

    def test_timeline(self, client):
        client.post("/api/v1/store", json={"content": "Timeline item"})
        resp = client.get("/api/v1/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_narrate(self, client):
        client.post("/api/v1/store", json={"content": "Python AI development"})
        resp = client.post("/api/v1/narrate", json={"topic": "Python"})
        assert resp.status_code == 200
        data = resp.json()
        assert "narrative" in data

    def test_openapi_docs(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["info"]["title"] == "Stellar Memory API"


class TestServerAuth:
    def test_unauthorized(self, auth_client):
        resp = auth_client.post("/api/v1/store", json={"content": "test"})
        assert resp.status_code == 401

    def test_api_key_header(self, auth_client):
        resp = auth_client.post(
            "/api/v1/store",
            json={"content": "test"},
            headers={"X-API-Key": "test-key-123"},
        )
        assert resp.status_code == 200

    def test_bearer_token(self, auth_client):
        resp = auth_client.post(
            "/api/v1/store",
            json={"content": "test"},
            headers={"Authorization": "Bearer test-key-123"},
        )
        assert resp.status_code == 200

    def test_health_no_auth_needed(self, auth_client):
        resp = auth_client.get("/api/v1/health")
        assert resp.status_code == 200
