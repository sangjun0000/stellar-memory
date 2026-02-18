"""P9-F5: Memory Benchmark - quantitative performance measurement."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from stellar_memory.models import BenchmarkReport


# Standard dataset categories with template content
_CATEGORIES = ["daily", "work", "tech", "emotion", "code"]

_TEMPLATES = {
    "daily": [
        "I had coffee with {name} at the cafe this morning",
        "The weather today was {adj} and {adj2}",
        "Went grocery shopping and bought {item} and {item2}",
        "Watched a movie called {title} last night",
        "Took a walk in the park near {place}",
    ],
    "work": [
        "Meeting with {name} about the {topic} project",
        "Deadline for {topic} report is next {day}",
        "New team member {name} joined the {topic} team",
        "Completed the {topic} feature implementation",
        "Code review feedback on {topic} module was positive",
    ],
    "tech": [
        "Learned about {tech} framework for building {topic}",
        "{tech} version {ver} was released with new features",
        "The {tech} documentation recommends using {pattern}",
        "Benchmark shows {tech} is {num}x faster than alternatives",
        "Migrated from {tech} to {tech2} for better performance",
    ],
    "emotion": [
        "Felt really happy when {name} surprised me with {item}",
        "Frustrated with the {topic} bug that took hours to fix",
        "Excited about the upcoming {topic} conference",
        "Anxious about the {topic} presentation tomorrow",
        "Relieved that the {topic} deployment went smoothly",
    ],
    "code": [
        "def calculate_{func}(data): return sum(data) / len(data)",
        "class {cls}Manager: def __init__(self): self.items = []",
        "async def fetch_{func}(url): return await client.get(url)",
        "SELECT * FROM {table} WHERE status = 'active' ORDER BY created_at",
        "const {func} = ({param}) => {{ return {param}.filter(x => x > 0) }}",
    ],
}

_NAMES = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry"]
_TOPICS = ["memory", "search", "auth", "deploy", "cache", "sync", "graph", "api"]
_TECHS = ["React", "Python", "Rust", "Go", "Docker", "Redis", "PostgreSQL", "FastAPI"]
_ITEMS = ["milk", "bread", "coffee", "laptop", "book", "headphones", "cake", "flowers"]
_ADJS = ["sunny", "rainy", "cold", "warm", "windy", "cloudy", "beautiful", "foggy"]


class StandardDataset:
    """Reproducible benchmark dataset generator."""

    SIZES = {
        "small": (100, 20),
        "standard": (1000, 100),
        "large": (10000, 500),
    }

    def __init__(self, name: str = "standard", seed: int = 42):
        self._name = name
        self._seed = seed
        self._rng = random.Random(seed)
        count, query_count = self.SIZES.get(name, (1000, 100))
        self._memory_count = count
        self._query_count = query_count

    @property
    def name(self) -> str:
        return self._name

    def generate_memories(self) -> list[dict]:
        """Generate reproducible memory items."""
        memories = []
        for i in range(self._memory_count):
            cat = _CATEGORIES[i % len(_CATEGORIES)]
            template = self._rng.choice(_TEMPLATES[cat])
            content = self._fill_template(template)
            importance = self._rng.uniform(0.1, 0.9)
            tags = [cat]
            if cat == "code":
                tags.append("code")
            memories.append({
                "content": content,
                "importance": round(importance, 2),
                "tags": tags,
                "category": cat,
                "id_hint": f"bench_{i}",
            })
        return memories

    def generate_queries(self) -> list[dict]:
        """Generate queries with expected category matches."""
        queries = []
        for i in range(self._query_count):
            cat = _CATEGORIES[i % len(_CATEGORIES)]
            keywords = {
                "daily": ["coffee", "weather", "morning", "walk", "movie"],
                "work": ["meeting", "deadline", "team", "project", "review"],
                "tech": ["framework", "version", "documentation", "benchmark"],
                "emotion": ["happy", "frustrated", "excited", "anxious", "relieved"],
                "code": ["function", "class", "async", "SELECT", "const"],
            }
            query = self._rng.choice(keywords.get(cat, ["memory"]))
            queries.append({
                "query": query,
                "expected_category": cat,
            })
        return queries

    def _fill_template(self, template: str) -> str:
        replacements = {
            "{name}": self._rng.choice(_NAMES),
            "{topic}": self._rng.choice(_TOPICS),
            "{tech}": self._rng.choice(_TECHS),
            "{tech2}": self._rng.choice(_TECHS),
            "{item}": self._rng.choice(_ITEMS),
            "{item2}": self._rng.choice(_ITEMS),
            "{adj}": self._rng.choice(_ADJS),
            "{adj2}": self._rng.choice(_ADJS),
            "{place}": self._rng.choice(["river", "hill", "garden", "lake"]),
            "{title}": self._rng.choice(["Inception", "Matrix", "Arrival", "Dune"]),
            "{day}": self._rng.choice(["Monday", "Friday", "Wednesday"]),
            "{ver}": f"{self._rng.randint(1,5)}.{self._rng.randint(0,9)}",
            "{pattern}": self._rng.choice(["hooks", "middleware", "plugins"]),
            "{num}": str(self._rng.randint(2, 10)),
            "{func}": self._rng.choice(["average", "total", "count", "max"]),
            "{cls}": self._rng.choice(["Data", "Task", "User", "Event"]),
            "{table}": self._rng.choice(["users", "orders", "events", "logs"]),
            "{param}": self._rng.choice(["items", "data", "values", "records"]),
        }
        result = template
        for key, val in replacements.items():
            result = result.replace(key, val, 1)
        return result


class MemoryBenchmark:
    """Comprehensive memory system benchmark."""

    def __init__(self, stellar):
        self._stellar = stellar

    def run(self, queries: int = 100, dataset: str = "standard",
            seed: int = 42) -> BenchmarkReport:
        ds = StandardDataset(dataset, seed)
        memories = ds.generate_memories()
        query_list = ds.generate_queries()[:queries]

        # Measure store latency
        store_times = []
        stored_ids = []
        for mem in memories:
            t0 = time.perf_counter()
            mid = self._stellar.store(
                content=mem["content"],
                importance=mem["importance"],
                metadata={"category": mem["category"], "bench_id": mem["id_hint"]},
            )
            t1 = time.perf_counter()
            store_times.append((t1 - t0) * 1000)
            stored_ids.append(mid.id if hasattr(mid, 'id') else mid)

        # Measure recall latency + accuracy
        recall_times = []
        hits_at_5 = 0
        hits_at_10 = 0
        precision_hits_5 = 0
        for q in query_list:
            t0 = time.perf_counter()
            results = self._stellar.recall(q["query"], limit=10)
            t1 = time.perf_counter()
            recall_times.append((t1 - t0) * 1000)

            # Check if any result matches expected category
            top5 = results[:5]
            top10 = results[:10]
            cat = q["expected_category"]
            if any(r.metadata.get("category") == cat for r in top5):
                hits_at_5 += 1
            if any(r.metadata.get("category") == cat for r in top10):
                hits_at_10 += 1
            precision_hits_5 += sum(
                1 for r in top5 if r.metadata.get("category") == cat
            )

        # Measure reorbit latency
        t0 = time.perf_counter()
        self._stellar.reorbit()
        t1 = time.perf_counter()
        reorbit_ms = (t1 - t0) * 1000

        # Stats
        stats = self._stellar.stats()
        import os
        db_size = 0.0
        if hasattr(self._stellar, 'config') and self._stellar.config.db_path != ":memory:":
            try:
                db_size = os.path.getsize(self._stellar.config.db_path) / (1024 * 1024)
            except OSError:
                pass

        import sys
        mem_usage = sys.getsizeof(self._stellar) / (1024 * 1024)

        total_q = len(query_list) or 1
        return BenchmarkReport(
            recall_at_5=hits_at_5 / total_q,
            recall_at_10=hits_at_10 / total_q,
            precision_at_5=(precision_hits_5 / (total_q * 5)) if total_q else 0.0,
            avg_store_latency_ms=sum(store_times) / len(store_times) if store_times else 0.0,
            avg_recall_latency_ms=sum(recall_times) / len(recall_times) if recall_times else 0.0,
            avg_reorbit_latency_ms=reorbit_ms,
            memory_usage_mb=round(mem_usage, 2),
            db_size_mb=round(db_size, 2),
            total_memories=stats.total_memories,
            zone_distribution=dict(stats.zone_counts),
            dataset_name=dataset,
            queries_run=total_q,
        )
