"""Stellar Memory data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4
import time


@dataclass
class EmotionVector:
    """6-dimensional emotion vector."""
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0

    @property
    def intensity(self) -> float:
        """Emotion intensity = max emotion value."""
        return max(self.joy, self.sadness, self.anger,
                   self.fear, self.surprise, self.disgust)

    @property
    def dominant(self) -> str:
        """Name of the dominant emotion."""
        emotions = {
            "joy": self.joy, "sadness": self.sadness,
            "anger": self.anger, "fear": self.fear,
            "surprise": self.surprise, "disgust": self.disgust,
        }
        return max(emotions, key=emotions.get)

    def to_list(self) -> list[float]:
        return [self.joy, self.sadness, self.anger,
                self.fear, self.surprise, self.disgust]

    @classmethod
    def from_list(cls, values: list[float]) -> EmotionVector:
        names = ["joy", "sadness", "anger", "fear", "surprise", "disgust"]
        kwargs = {n: v for n, v in zip(names, values[:6])}
        return cls(**kwargs)

    def to_dict(self) -> dict[str, float]:
        return {
            "joy": self.joy, "sadness": self.sadness,
            "anger": self.anger, "fear": self.fear,
            "surprise": self.surprise, "disgust": self.disgust,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EmotionVector:
        return cls(**{k: float(data.get(k, 0.0)) for k in
                      ["joy", "sadness", "anger", "fear", "surprise", "disgust"]})


@dataclass
class TimelineEntry:
    """Timeline entry for memory stream."""
    timestamp: float = 0.0
    memory_id: str = ""
    content: str = ""
    zone: int = -1
    emotion: EmotionVector | None = None
    importance: float = 0.0


@dataclass
class MemoryItem:
    id: str
    content: str
    created_at: float
    last_recalled_at: float
    recall_count: int = 0
    arbitrary_importance: float = 0.5
    zone: int = -1
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    total_score: float = 0.0
    # P6 fields
    encrypted: bool = False
    source_type: str = "user"  # "user" | "web" | "file" | "api"
    source_url: str | None = None
    ingested_at: float | None = None
    vector_clock: dict[str, int] | None = None
    # P7 fields
    emotion: EmotionVector | None = None
    # P9 fields
    content_type: str = "text"  # "text" | "code" | "json" | "structured"

    @classmethod
    def create(cls, content: str, importance: float = 0.5,
               metadata: dict | None = None) -> MemoryItem:
        now = time.time()
        return cls(
            id=str(uuid4()),
            content=content,
            created_at=now,
            last_recalled_at=now,
            recall_count=0,
            arbitrary_importance=max(0.0, min(1.0, importance)),
            zone=-1,
            metadata=metadata or {},
        )


@dataclass
class ScoreBreakdown:
    recall_score: float
    freshness_score: float
    arbitrary_score: float
    context_score: float
    total: float
    target_zone: int
    emotion_score: float = 0.0  # P7: default 0.0 for backward compat


@dataclass
class ReorbitResult:
    moved: int = 0
    evicted: int = 0
    total_items: int = 0
    duration: float = 0.0


@dataclass
class MemoryStats:
    zone_counts: dict[int, int] = field(default_factory=dict)
    zone_capacities: dict[int, int | None] = field(default_factory=dict)
    total_memories: int = 0


@dataclass
class EvaluationResult:
    importance: float
    factual_score: float
    emotional_score: float
    actionable_score: float
    explicit_score: float
    method: str  # "rule" | "llm" | "default"


@dataclass
class FeedbackRecord:
    query: str
    result_ids: list[str] = field(default_factory=list)
    used_ids: list[str] = field(default_factory=list)
    timestamp: float = 0.0
    weights_snapshot: dict[str, float] = field(default_factory=dict)


@dataclass
class ConsolidationResult:
    merged_count: int = 0
    skipped_count: int = 0
    target_id: str = ""
    source_id: str = ""


@dataclass
class SessionInfo:
    session_id: str = ""
    started_at: float = 0.0
    ended_at: float | None = None
    memory_count: int = 0
    summary: str | None = None


@dataclass
class MemorySnapshot:
    timestamp: float = 0.0
    total_memories: int = 0
    zone_distribution: dict[int, int] = field(default_factory=dict)
    items: list[dict] = field(default_factory=list)
    version: str = "0.3.0"


@dataclass
class DecayResult:
    to_demote: list[tuple[str, int, int]] = field(default_factory=list)
    to_forget: list[str] = field(default_factory=list)
    demoted: int = 0
    forgotten: int = 0


@dataclass
class HealthStatus:
    healthy: bool = True
    db_accessible: bool = True
    scheduler_running: bool = False
    total_memories: int = 0
    graph_edges: int = 0
    zone_usage: dict[int, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class SummarizationResult:
    original_id: str = ""
    summary_id: str = ""
    summary_text: str = ""
    original_length: int = 0
    summary_length: int = 0


@dataclass
class MemoryEdge:
    source_id: str
    target_id: str
    edge_type: str  # "related_to" | "derived_from" | "contradicts" | "sequence"
    weight: float = 1.0
    created_at: float = 0.0


# P6 models

@dataclass
class ChangeEvent:
    """Sync change event for CRDT replication."""
    event_type: str  # "store" | "update" | "remove" | "move"
    item_id: str
    agent_id: str
    timestamp: float
    vector_clock: dict[str, int] = field(default_factory=dict)
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "item_id": self.item_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "vector_clock": self.vector_clock,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ChangeEvent:
        return cls(**data)


@dataclass
class AccessRole:
    """RBAC role definition."""
    name: str
    permissions: list[str] = field(default_factory=list)


@dataclass
class IngestResult:
    """Result of ingesting external knowledge."""
    source_url: str = ""
    memory_id: str = ""
    summary_text: str = ""
    was_duplicate: bool = False
    original_length: int = 0


@dataclass
class ZoneDistribution:
    """Zone distribution for dashboard."""
    zone_id: int = 0
    zone_name: str = ""
    count: int = 0
    capacity: int | None = None
    usage_percent: float = 0.0


# P9 models

@dataclass
class IntrospectionResult:
    """introspect() result."""
    topic: str = ""
    confidence: float = 0.0
    coverage: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    memory_count: int = 0
    avg_freshness: float = 0.0
    zone_distribution: dict[int, int] = field(default_factory=dict)


@dataclass
class ConfidentRecall:
    """recall_with_confidence() result."""
    memories: list[MemoryItem] = field(default_factory=list)
    confidence: float = 0.0
    warning: str | None = None


@dataclass
class RecallLog:
    """Single recall history entry."""
    query: str = ""
    result_ids: list[str] = field(default_factory=list)
    timestamp: float = 0.0
    feedback: str = "none"  # "positive" | "negative" | "none"


@dataclass
class OptimizationReport:
    """optimize() result."""
    before_weights: dict[str, float] = field(default_factory=dict)
    after_weights: dict[str, float] = field(default_factory=dict)
    improvement: str = ""
    pattern: str = ""
    simulation_score: float = 0.0
    rolled_back: bool = False


@dataclass
class ReasoningResult:
    """reason() result."""
    query: str = ""
    source_memories: list[MemoryItem] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    contradictions: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_chain: list[str] = field(default_factory=list)


@dataclass
class Contradiction:
    """Contradiction detection result."""
    memory_a_id: str = ""
    memory_b_id: str = ""
    description: str = ""
    severity: float = 0.0


@dataclass
class BenchmarkReport:
    """benchmark() result."""
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_5: float = 0.0
    avg_store_latency_ms: float = 0.0
    avg_recall_latency_ms: float = 0.0
    avg_reorbit_latency_ms: float = 0.0
    memory_usage_mb: float = 0.0
    db_size_mb: float = 0.0
    total_memories: int = 0
    zone_distribution: dict[int, int] = field(default_factory=dict)
    dataset_name: str = ""
    queries_run: int = 0

    def to_dict(self) -> dict:
        return {
            "recall_at_5": self.recall_at_5,
            "recall_at_10": self.recall_at_10,
            "precision_at_5": self.precision_at_5,
            "avg_store_latency_ms": self.avg_store_latency_ms,
            "avg_recall_latency_ms": self.avg_recall_latency_ms,
            "avg_reorbit_latency_ms": self.avg_reorbit_latency_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "db_size_mb": self.db_size_mb,
            "total_memories": self.total_memories,
            "zone_distribution": self.zone_distribution,
            "dataset_name": self.dataset_name,
            "queries_run": self.queries_run,
        }

    def to_html(self) -> str:
        """Generate HTML report of benchmark results."""
        zone_rows = "".join(
            f"<tr><td>Zone {z}</td><td>{c}</td></tr>"
            for z, c in sorted(self.zone_distribution.items())
        )
        return (
            "<html><head><title>Stellar Memory Benchmark</title>"
            "<style>body{font-family:sans-serif;margin:2em}"
            "table{border-collapse:collapse;margin:1em 0}"
            "th,td{border:1px solid #ccc;padding:8px;text-align:left}"
            "th{background:#f5f5f5}.metric{font-weight:bold}</style></head>"
            "<body><h1>Stellar Memory Benchmark Report</h1>"
            f"<p>Dataset: <b>{self.dataset_name}</b> | "
            f"Queries: <b>{self.queries_run}</b></p>"
            "<h2>Accuracy</h2><table><tr><th>Metric</th><th>Value</th></tr>"
            f"<tr><td>Recall@5</td><td class='metric'>{self.recall_at_5:.3f}</td></tr>"
            f"<tr><td>Recall@10</td><td class='metric'>{self.recall_at_10:.3f}</td></tr>"
            f"<tr><td>Precision@5</td><td class='metric'>{self.precision_at_5:.3f}</td></tr>"
            "</table><h2>Latency</h2><table><tr><th>Operation</th><th>Avg (ms)</th></tr>"
            f"<tr><td>Store</td><td>{self.avg_store_latency_ms:.2f}</td></tr>"
            f"<tr><td>Recall</td><td>{self.avg_recall_latency_ms:.2f}</td></tr>"
            f"<tr><td>Reorbit</td><td>{self.avg_reorbit_latency_ms:.2f}</td></tr>"
            "</table><h2>Resources</h2><table><tr><th>Resource</th><th>Value</th></tr>"
            f"<tr><td>Total Memories</td><td>{self.total_memories}</td></tr>"
            f"<tr><td>Memory Usage</td><td>{self.memory_usage_mb:.2f} MB</td></tr>"
            f"<tr><td>DB Size</td><td>{self.db_size_mb:.2f} MB</td></tr>"
            "</table><h2>Zone Distribution</h2>"
            f"<table><tr><th>Zone</th><th>Count</th></tr>{zone_rows}</table>"
            "</body></html>"
        )
