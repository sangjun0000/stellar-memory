"""Tests for P6 dashboard module."""

import pytest
from unittest.mock import MagicMock

from stellar_memory.models import MemoryStats, HealthStatus
from stellar_memory.config import DashboardConfig


class TestDashboardConfig:
    def test_defaults(self):
        cfg = DashboardConfig()
        assert not cfg.enabled
        assert cfg.host == "127.0.0.1"
        assert cfg.port == 8080
        assert not cfg.auto_start

    def test_custom(self):
        cfg = DashboardConfig(enabled=True, port=9090)
        assert cfg.enabled
        assert cfg.port == 9090


class TestDashboardApp:
    def test_create_app(self):
        """Test that the dashboard app can be created."""
        try:
            from stellar_memory.dashboard.app import create_app
            app = create_app(None)
            assert app is not None
            assert app.title == "Stellar Memory Dashboard"
        except ImportError:
            pytest.skip("fastapi not installed")

    def test_index_html(self):
        from stellar_memory.dashboard.app import _index_html
        html = _index_html()
        assert "Stellar Memory Dashboard" in html
        assert "<script>" in html
        assert "/api/stats" in html

    def test_routes_exist(self):
        try:
            from stellar_memory.dashboard.app import create_app
            app = create_app(None)
            routes = [r.path for r in app.routes]
            assert "/" in routes
            assert "/api/stats" in routes
            assert "/api/memories" in routes
            assert "/api/health" in routes
            assert "/api/graph" in routes
            assert "/api/events" in routes  # SSE endpoint
        except ImportError:
            pytest.skip("fastapi not installed")

    def test_index_html_has_svg(self):
        from stellar_memory.dashboard.app import _index_html
        html = _index_html()
        assert '<svg id="solar"' in html
        assert "drawSolar" in html
        assert "ZONE_COLORS" in html

    def test_index_html_has_sse(self):
        from stellar_memory.dashboard.app import _index_html
        html = _index_html()
        assert "EventSource" in html
        assert "/api/events" in html


class TestP6Models:
    """Test P6 model additions."""

    def test_memory_item_p6_fields(self):
        from stellar_memory.models import MemoryItem
        item = MemoryItem.create("test", importance=0.5)
        assert item.encrypted is False
        assert item.source_type == "user"
        assert item.source_url is None
        assert item.ingested_at is None

    def test_ingest_result(self):
        from stellar_memory.models import IngestResult
        result = IngestResult(
            source_url="https://example.com",
            memory_id="m1",
            summary_text="summary",
            original_length=1000,
        )
        assert result.source_url == "https://example.com"
        assert not result.was_duplicate

    def test_zone_distribution(self):
        from stellar_memory.models import ZoneDistribution
        zd = ZoneDistribution(zone_id=0, zone_name="core", count=10, capacity=20)
        assert zd.usage_percent == 0.0

    def test_access_role(self):
        from stellar_memory.models import AccessRole
        role = AccessRole(name="editor", permissions=["read", "write"])
        assert role.name == "editor"
        assert "write" in role.permissions

    def test_change_event(self):
        from stellar_memory.models import ChangeEvent
        evt = ChangeEvent(
            event_type="store", item_id="m1",
            agent_id="a1", timestamp=100.0,
        )
        assert evt.to_dict()["event_type"] == "store"


class TestP6Integration:
    """Test P6 features integrate into StellarMemory."""

    def test_version(self):
        import stellar_memory
        assert stellar_memory.__version__ is not None
        assert len(stellar_memory.__version__) > 0

    def test_p6_config_in_stellar_config(self):
        from stellar_memory.config import StellarConfig
        cfg = StellarConfig()
        assert hasattr(cfg, 'storage')
        assert hasattr(cfg, 'sync')
        assert hasattr(cfg, 'security')
        assert hasattr(cfg, 'connectors')
        assert hasattr(cfg, 'dashboard')
        assert cfg.storage.backend == "sqlite"
        assert cfg.sync.enabled is False
        assert cfg.security.enabled is False

    def test_p6_exports(self):
        from stellar_memory import (
            StorageConfig, SyncConfig, SecurityConfig,
            ConnectorConfig, DashboardConfig,
            ChangeEvent, AccessRole, IngestResult, ZoneDistribution,
            StorageBackend, EncryptionManager, AccessControl,
            SecurityAudit, MemorySyncManager,
        )
        assert StorageConfig is not None
        assert EncryptionManager is not None

    def test_stellar_memory_creates_without_p6(self):
        """P6 features should be disabled by default."""
        from stellar_memory import StellarMemory, StellarConfig
        cfg = StellarConfig(db_path=":memory:")
        cfg.embedder.enabled = False
        cfg.llm.enabled = False
        cfg.event_logger.enabled = False
        cfg.graph.persistent = False
        sm = StellarMemory(config=cfg)
        assert sm._encryption is None
        assert sm._sync is None
        assert sm._redis_cache is None
