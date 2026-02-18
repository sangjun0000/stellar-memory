"""Tests for P8: OpenAPI documentation and response models."""

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


class TestOpenAPISchema:
    def test_openapi_json_accessible(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "openapi" in data
        assert "info" in data

    def test_openapi_title(self, client):
        resp = client.get("/openapi.json")
        data = resp.json()
        assert data["info"]["title"] == "Stellar Memory API"

    def test_openapi_version(self, client):
        resp = client.get("/openapi.json")
        data = resp.json()
        assert len(data["info"]["version"]) > 0

    def test_openapi_description(self, client):
        resp = client.get("/openapi.json")
        data = resp.json()
        assert "Celestial" in data["info"]["description"]

    def test_openapi_tags(self, client):
        resp = client.get("/openapi.json")
        data = resp.json()
        tag_names = [t["name"] for t in data.get("tags", [])]
        assert "Memories" in tag_names
        assert "Timeline" in tag_names
        assert "System" in tag_names

    def test_openapi_has_all_endpoints(self, client):
        resp = client.get("/openapi.json")
        data = resp.json()
        paths = list(data["paths"].keys())
        assert "/api/v1/store" in paths
        assert "/api/v1/recall" in paths
        assert "/api/v1/health" in paths
        assert "/api/v1/stats" in paths
        assert "/api/v1/memories" in paths
        assert "/api/v1/timeline" in paths

    def test_swagger_ui_accessible(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_accessible(self, client):
        resp = client.get("/redoc")
        assert resp.status_code == 200


class TestResponseModels:
    def test_store_response_fields(self, client):
        resp = client.post("/api/v1/store", json={
            "content": "Test memory", "importance": 0.7,
        })
        data = resp.json()
        assert "id" in data
        assert "zone" in data
        assert "score" in data
        assert isinstance(data["score"], float)

    def test_recall_response_fields(self, client):
        client.post("/api/v1/store", json={"content": "OpenAPI test"})
        resp = client.get("/api/v1/recall", params={"q": "OpenAPI"})
        data = resp.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "id" in item
            assert "content" in item
            assert "zone" in item
            assert "importance" in item
            assert "recall_count" in item

    def test_memories_response_fields(self, client):
        client.post("/api/v1/store", json={"content": "List test"})
        resp = client.get("/api/v1/memories")
        data = resp.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_stats_response_fields(self, client):
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert "total_memories" in data
        assert "zones" in data
        assert "capacities" in data

    def test_health_response_fields(self, client):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert "healthy" in data
        assert "total_memories" in data
        assert "warnings" in data


class TestRateLimitHeaders:
    def test_rate_limit_headers_present(self, client):
        resp = client.post("/api/v1/store", json={"content": "rate test"})
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers

    def test_rate_limit_remaining_decreases(self, client):
        resp1 = client.post("/api/v1/store", json={"content": "rate 1"})
        r1 = int(resp1.headers["X-RateLimit-Remaining"])
        resp2 = client.post("/api/v1/store", json={"content": "rate 2"})
        r2 = int(resp2.headers["X-RateLimit-Remaining"])
        assert r2 < r1
