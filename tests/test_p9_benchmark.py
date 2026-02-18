"""Tests for P9-F5: Memory Benchmark."""

import pytest

from stellar_memory.benchmark import StandardDataset, MemoryBenchmark
from stellar_memory.models import BenchmarkReport


class TestStandardDataset:
    def test_small_dataset_size(self):
        ds = StandardDataset("small", seed=42)
        memories = ds.generate_memories()
        assert len(memories) == 100

    def test_standard_dataset_size(self):
        ds = StandardDataset("standard", seed=42)
        memories = ds.generate_memories()
        assert len(memories) == 1000

    def test_large_dataset_size(self):
        ds = StandardDataset("large", seed=42)
        memories = ds.generate_memories()
        assert len(memories) == 10000

    def test_reproducible_with_same_seed(self):
        ds1 = StandardDataset("small", seed=42)
        ds2 = StandardDataset("small", seed=42)
        m1 = ds1.generate_memories()
        m2 = ds2.generate_memories()
        assert m1 == m2

    def test_different_seeds_produce_different_data(self):
        ds1 = StandardDataset("small", seed=42)
        ds2 = StandardDataset("small", seed=99)
        m1 = ds1.generate_memories()
        m2 = ds2.generate_memories()
        assert m1 != m2

    def test_memory_has_required_fields(self):
        ds = StandardDataset("small", seed=42)
        memories = ds.generate_memories()
        for mem in memories[:5]:
            assert "content" in mem
            assert "importance" in mem
            assert "tags" in mem
            assert "category" in mem
            assert "id_hint" in mem

    def test_importance_range(self):
        ds = StandardDataset("small", seed=42)
        memories = ds.generate_memories()
        for mem in memories:
            assert 0.0 <= mem["importance"] <= 1.0

    def test_categories_balanced(self):
        ds = StandardDataset("small", seed=42)
        memories = ds.generate_memories()
        cats = [m["category"] for m in memories]
        for cat in ["daily", "work", "tech", "emotion", "code"]:
            assert cats.count(cat) == 20  # 100/5 = 20 each

    def test_generate_queries(self):
        ds = StandardDataset("small", seed=42)
        queries = ds.generate_queries()
        assert len(queries) == 20  # small: 20 queries

    def test_query_has_expected_fields(self):
        ds = StandardDataset("small", seed=42)
        queries = ds.generate_queries()
        for q in queries:
            assert "query" in q
            assert "expected_category" in q

    def test_dataset_name_property(self):
        ds = StandardDataset("standard", seed=42)
        assert ds.name == "standard"

    def test_unknown_dataset_defaults(self):
        ds = StandardDataset("unknown", seed=42)
        memories = ds.generate_memories()
        assert len(memories) == 1000  # defaults to standard size


class TestBenchmarkReport:
    def test_to_dict(self):
        report = BenchmarkReport(
            recall_at_5=0.8,
            recall_at_10=0.9,
            precision_at_5=0.5,
            avg_store_latency_ms=1.0,
            avg_recall_latency_ms=2.0,
            avg_reorbit_latency_ms=3.0,
            memory_usage_mb=10.0,
            db_size_mb=5.0,
            total_memories=100,
            zone_distribution={0: 10, 1: 30, 2: 60},
            dataset_name="small",
            queries_run=20,
        )
        d = report.to_dict()
        assert d["recall_at_5"] == 0.8
        assert d["total_memories"] == 100
        assert d["dataset_name"] == "small"

    def test_recall_at_range(self):
        report = BenchmarkReport(recall_at_5=0.5, recall_at_10=0.8)
        assert 0.0 <= report.recall_at_5 <= 1.0
        assert 0.0 <= report.recall_at_10 <= 1.0

    def test_default_values(self):
        report = BenchmarkReport()
        assert report.recall_at_5 == 0.0
        assert report.total_memories == 0
        assert report.zone_distribution == {}


class TestMemoryBenchmark:
    def test_benchmark_runs(self):
        """Benchmark should run with a minimal in-memory StellarMemory."""
        from stellar_memory import StellarMemory, StellarConfig, EmbedderConfig
        config = StellarConfig(
            db_path=":memory:",
            embedder=EmbedderConfig(enabled=False),
        )
        stellar = StellarMemory(config)
        bench = MemoryBenchmark(stellar)
        report = bench.run(queries=5, dataset="small", seed=42)
        assert isinstance(report, BenchmarkReport)
        assert report.total_memories > 0
        assert report.queries_run == 5
        assert report.avg_store_latency_ms > 0
