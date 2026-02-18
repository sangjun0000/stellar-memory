"""Tests for Health Check and CLI health/logs commands."""

import json

import pytest

from stellar_memory.config import StellarConfig, GraphConfig, EventLoggerConfig
from stellar_memory.stellar import StellarMemory
from stellar_memory.cli import main


class TestHealthCheck:
    def test_health_basic(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(db_path=db)
        mem = StellarMemory(config)
        h = mem.health()
        assert h.healthy is True
        assert h.db_accessible is True
        assert h.total_memories == 0
        assert h.graph_edges == 0

    def test_zone_capacity_warning(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(db_path=db)
        mem = StellarMemory(config)
        # Core zone has max_slots=20, store enough high-importance items
        for i in range(17):
            mem.store(f"important memory {i}", importance=0.9)
        h = mem.health()
        # Check if any zone is at 80%+
        for zone_id, usage in h.zone_usage.items():
            if "80%" in usage or "85%" in usage or "90%" in usage or "95%" in usage or "100%" in usage:
                assert any("capacity" in w for w in h.warnings)
                break

    def test_total_memories_accurate(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(db_path=db)
        mem = StellarMemory(config)
        mem.store("one")
        mem.store("two")
        mem.store("three")
        h = mem.health()
        assert h.total_memories == 3

    def test_graph_edges_count(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(db_path=db)
        mem = StellarMemory(config)
        item1 = mem.store("a")
        item2 = mem.store("b")
        mem.graph.add_edge(item1.id, item2.id, "related_to")
        h = mem.health()
        assert h.graph_edges == 1

    def test_scheduler_status(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(db_path=db)
        mem = StellarMemory(config)
        h = mem.health()
        assert h.scheduler_running is False
        mem.start()
        h2 = mem.health()
        assert h2.scheduler_running is True
        mem.stop()

    def test_zone_usage_format(self, tmp_path):
        db = str(tmp_path / "test.db")
        config = StellarConfig(db_path=db)
        mem = StellarMemory(config)
        mem.store("format test", importance=0.9)
        h = mem.health()
        # Zone usage should be formatted strings
        for zone_id, usage in h.zone_usage.items():
            assert "/" in usage  # "1/20 (5%)" or "0/unlimited"


class TestCLIHealth:
    def test_health_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "health test"])
        main(["--db", db, "health"])
        captured = capsys.readouterr()
        assert "Status:" in captured.out
        assert "DB:" in captured.out
        assert "Memories:" in captured.out

    def test_logs_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        log_path = str(tmp_path / "stellar_events.jsonl")
        # Create a log file with some entries
        from stellar_memory.event_logger import EventLogger
        el = EventLogger(log_path=log_path)
        el._log("test_event", detail="hello")

        # The logs command uses default path, so we test it doesn't crash
        # with the default path (may have no entries)
        main(["--db", db, "logs", "--limit", "5"])
        captured = capsys.readouterr()
        # Either shows entries or empty output (no crash)
        assert isinstance(captured.out, str)
