# Design: stellar-memory-p4 (Production Hardening & Persistence)

## 1. Overview

P4는 stellar-memory를 프로덕션 환경에서 안정적으로 운영할 수 있도록 5개 기능을 구현합니다.
핵심: 그래프 영속화, 자동 망각, 이벤트 로깅, 그래프 기반 검색 강화, 헬스 체크.

**Target Version**: v0.5.0
**New Files**: 3 (persistent_graph.py, decay_manager.py, event_logger.py)
**Modified Files**: 7 (stellar.py, config.py, models.py, mcp_server.py, cli.py, __init__.py, pyproject.toml)

## 2. F1: Graph Persistence (SQLite)

### 2.1 persistent_graph.py (NEW)

```python
"""Persistent memory graph using SQLite."""

from __future__ import annotations

import sqlite3
import threading
import time
from collections import defaultdict

from stellar_memory.models import MemoryEdge


class PersistentMemoryGraph:
    """SQLite-backed memory graph that survives restarts."""

    def __init__(self, db_path: str, max_edges_per_item: int = 20):
        self._db_path = db_path
        self._max_edges = max_edges_per_item
        self._local = threading.local()
        self._init_table()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_table(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL DEFAULT 'related_to',
                weight REAL NOT NULL DEFAULT 1.0,
                created_at REAL NOT NULL,
                PRIMARY KEY (source_id, target_id, edge_type)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)"
        )
        conn.commit()

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: str = "related_to", weight: float = 1.0) -> MemoryEdge:
        """Add a relationship between two memories."""
        conn = self._get_conn()
        now = time.time()

        # Enforce max edges: count existing, evict lowest if needed
        cur = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE source_id = ?", (source_id,)
        )
        count = cur.fetchone()[0]
        if count >= self._max_edges:
            conn.execute("""
                DELETE FROM edges WHERE rowid IN (
                    SELECT rowid FROM edges WHERE source_id = ?
                    ORDER BY weight ASC LIMIT 1
                )
            """, (source_id,))

        conn.execute(
            "INSERT OR REPLACE INTO edges "
            "(source_id, target_id, edge_type, weight, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (source_id, target_id, edge_type, weight, now),
        )
        conn.commit()
        return MemoryEdge(
            source_id=source_id, target_id=target_id,
            edge_type=edge_type, weight=weight, created_at=now,
        )

    def get_edges(self, item_id: str) -> list[MemoryEdge]:
        """Get all edges from a memory item."""
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT source_id, target_id, edge_type, weight, created_at "
            "FROM edges WHERE source_id = ?", (item_id,)
        )
        return [
            MemoryEdge(
                source_id=row[0], target_id=row[1], edge_type=row[2],
                weight=row[3], created_at=row[4],
            )
            for row in cur.fetchall()
        ]

    def get_related_ids(self, item_id: str, depth: int = 1) -> set[str]:
        """Get IDs of related memories up to a certain depth (BFS in memory)."""
        visited: set[str] = set()
        queue = [(item_id, 0)]
        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)
            if current_depth < depth:
                for edge in self.get_edges(current_id):
                    queue.append((edge.target_id, current_depth + 1))
        visited.discard(item_id)
        return visited

    def remove_item(self, item_id: str) -> None:
        """Remove all edges involving an item."""
        conn = self._get_conn()
        conn.execute("DELETE FROM edges WHERE source_id = ?", (item_id,))
        conn.execute("DELETE FROM edges WHERE target_id = ?", (item_id,))
        conn.commit()

    def count_edges(self) -> int:
        """Total number of edges in the graph."""
        conn = self._get_conn()
        cur = conn.execute("SELECT COUNT(*) FROM edges")
        return cur.fetchone()[0]
```

### 2.2 GraphConfig Extension

```python
@dataclass
class GraphConfig:
    enabled: bool = True
    auto_link: bool = True
    auto_link_threshold: float = 0.7
    max_edges_per_item: int = 20
    persistent: bool = True  # NEW: use SQLite-backed graph
```

### 2.3 StellarMemory Graph Selection

```python
class StellarMemory:
    def __init__(self, config, namespace=None):
        # ... existing ...
        if self.config.graph.persistent and self.config.db_path != ":memory:":
            from stellar_memory.persistent_graph import PersistentMemoryGraph
            self._graph = PersistentMemoryGraph(
                self.config.db_path, self.config.graph.max_edges_per_item
            )
        else:
            self._graph = MemoryGraph(self.config.graph.max_edges_per_item)
```

## 3. F2: Memory Decay (Auto-Forget)

### 3.1 DecayConfig (NEW)

```python
@dataclass
class DecayConfig:
    enabled: bool = True
    decay_days: int = 30          # days without recall → demote 1 zone
    auto_forget_days: int = 90    # days in cloud zone → auto-delete
    min_zone_for_decay: int = 2   # zones 0,1 protected from decay
```

### 3.2 decay_manager.py (NEW)

```python
"""Memory decay manager - automatic forgetting of stale memories."""

from __future__ import annotations

import logging
import time

from stellar_memory.config import DecayConfig
from stellar_memory.models import MemoryItem, DecayResult

logger = logging.getLogger(__name__)

SECONDS_PER_DAY = 86400


class DecayManager:
    """Manages automatic memory decay and forgetting."""

    def __init__(self, config: DecayConfig):
        self._config = config

    def check_decay(self, items: list[MemoryItem],
                    current_time: float) -> DecayResult:
        """Check which items should decay or be forgotten."""
        result = DecayResult()
        if not self._config.enabled:
            return result

        decay_threshold = current_time - (self._config.decay_days * SECONDS_PER_DAY)
        forget_threshold = current_time - (self._config.auto_forget_days * SECONDS_PER_DAY)

        for item in items:
            if item.zone < self._config.min_zone_for_decay:
                continue  # Core/Inner protected

            if (item.zone == 4
                    and item.last_recalled_at < forget_threshold):
                result.to_forget.append(item.id)
            elif item.last_recalled_at < decay_threshold:
                result.to_demote.append((item.id, item.zone, item.zone + 1))

        return result
```

### 3.3 DecayResult Model (NEW)

```python
@dataclass
class DecayResult:
    to_demote: list[tuple[str, int, int]] = field(default_factory=list)  # (id, from_zone, to_zone)
    to_forget: list[str] = field(default_factory=list)  # ids to delete
    demoted: int = 0
    forgotten: int = 0
```

### 3.4 StellarMemory Decay Integration

```python
class StellarMemory:
    def __init__(self, config):
        # ... existing ...
        self._decay_mgr = DecayManager(self.config.decay)

    def reorbit(self) -> ReorbitResult:
        result = self._orbit_mgr.reorbit_all(self._memory_fn, time.time())
        self._event_bus.emit("on_reorbit", result)

        # Apply decay after reorbit
        if self.config.decay.enabled:
            self._apply_decay()

        return result

    def _apply_decay(self) -> DecayResult:
        """Apply memory decay: demote stale memories, forget ancient ones."""
        all_items = self._orbit_mgr.get_all_items()
        decay = self._decay_mgr.check_decay(all_items, time.time())

        for item_id in decay.to_forget:
            self.forget(item_id)
            decay.forgotten += 1

        for item_id, from_zone, to_zone in decay.to_demote:
            max_zone = max(self._orbit_mgr._zones.keys())
            if to_zone <= max_zone:
                item = self._orbit_mgr.find_item(item_id)
                if item is not None:
                    self._orbit_mgr.move(item.id, from_zone, to_zone, item.total_score)
                    self._event_bus.emit("on_zone_change", item, from_zone, to_zone)
                    decay.demoted += 1

        return decay
```

### 3.5 EventBus Extension

Add two new events to `EventBus.EVENTS`:

```python
EVENTS = (
    "on_store",
    "on_recall",
    "on_forget",
    "on_reorbit",
    "on_consolidate",
    "on_zone_change",
    "on_decay",         # NEW: (decay_result: DecayResult)
    "on_auto_forget",   # NEW: (item_id: str)
)
```

## 4. F3: Event Logger (Persistent Audit Trail)

### 4.1 event_logger.py (NEW)

```python
"""Persistent event logger for memory activity audit trail."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from stellar_memory.event_bus import EventBus

logger = logging.getLogger(__name__)


class EventLogger:
    """Logs memory events to a JSONL file."""

    def __init__(self, log_path: str = "stellar_events.jsonl",
                 max_size_mb: float = 10.0):
        self._log_path = Path(log_path)
        self._max_size = int(max_size_mb * 1024 * 1024)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def attach(self, bus: EventBus) -> None:
        """Register handlers for all events on the bus."""
        bus.on("on_store", lambda item: self._log("store", item_id=item.id,
               content_preview=item.content[:80]))
        bus.on("on_recall", lambda items, query: self._log("recall",
               query=query, result_count=len(items)))
        bus.on("on_forget", lambda mid: self._log("forget", item_id=mid))
        bus.on("on_reorbit", lambda result: self._log("reorbit",
               moved=result.moved, evicted=result.evicted))
        bus.on("on_consolidate", lambda existing, new: self._log("consolidate",
               existing_id=existing.id, new_id=new.id))
        bus.on("on_zone_change", lambda item, fz, tz: self._log("zone_change",
               item_id=item.id, from_zone=fz, to_zone=tz))

    def _log(self, event_type: str, **kwargs) -> None:
        """Write a single event line to the log file."""
        self._rotate_if_needed()
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            **kwargs,
        }
        with open(self._log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _rotate_if_needed(self) -> None:
        """Rotate log file if it exceeds max size."""
        if not self._log_path.exists():
            return
        if self._log_path.stat().st_size >= self._max_size:
            rotated = self._log_path.with_suffix(".jsonl.1")
            if rotated.exists():
                rotated.unlink()
            self._log_path.rename(rotated)

    def read_logs(self, limit: int = 100) -> list[dict]:
        """Read recent log entries."""
        if not self._log_path.exists():
            return []
        lines = self._log_path.read_text().strip().split("\n")
        entries = []
        for line in lines[-limit:]:
            if line:
                entries.append(json.loads(line))
        return entries
```

### 4.2 EventLoggerConfig (NEW)

```python
@dataclass
class EventLoggerConfig:
    enabled: bool = True
    log_path: str = "stellar_events.jsonl"
    max_size_mb: float = 10.0
```

### 4.3 StellarMemory Logger Integration

```python
class StellarMemory:
    def __init__(self, config):
        # ... existing ...
        self._event_logger = None
        if self.config.event_logger.enabled:
            from stellar_memory.event_logger import EventLogger
            self._event_logger = EventLogger(
                self.config.event_logger.log_path,
                self.config.event_logger.max_size_mb,
            )
            self._event_logger.attach(self._event_bus)
```

## 5. F4: Recall Boost (Graph-Enhanced Search)

### 5.1 RecallConfig (NEW)

```python
@dataclass
class RecallConfig:
    graph_boost_enabled: bool = True
    graph_boost_score: float = 0.1
    graph_boost_depth: int = 1
```

### 5.2 StellarMemory Recall Boost Integration

```python
class StellarMemory:
    def recall(self, query, limit=5):
        # ... existing recall logic (zones search) ...

        results = results[:limit]

        # Graph boost: include graph-connected memories as bonus candidates
        if (self.config.recall_boost.graph_boost_enabled
                and self.config.graph.enabled
                and results):
            results = self._apply_graph_boost(results, query_embedding, limit)

        self._last_recall_ids = [item.id for item in results]
        self._event_bus.emit("on_recall", results, query)
        return results

    def _apply_graph_boost(self, results: list[MemoryItem],
                           query_embedding: list[float] | None,
                           limit: int) -> list[MemoryItem]:
        """Boost recall results using graph connections."""
        result_ids = {r.id for r in results}
        boosted: list[MemoryItem] = list(results)
        depth = self.config.recall_boost.graph_boost_depth
        boost_score = self.config.recall_boost.graph_boost_score

        # Collect graph neighbors of results
        neighbor_ids: set[str] = set()
        for item in results:
            related = self._graph.get_related_ids(item.id, depth=depth)
            neighbor_ids.update(related - result_ids)

        # Fetch neighbor items and score them
        for nid in neighbor_ids:
            neighbor = self._orbit_mgr.find_item(nid)
            if neighbor is not None:
                neighbor.total_score += boost_score
                boosted.append(neighbor)

        # Re-sort by total_score descending and trim
        boosted.sort(key=lambda x: x.total_score, reverse=True)
        return boosted[:limit]
```

## 6. F5: Health Check & Diagnostics

### 6.1 HealthStatus Model (NEW)

```python
@dataclass
class HealthStatus:
    healthy: bool = True
    db_accessible: bool = True
    scheduler_running: bool = False
    total_memories: int = 0
    graph_edges: int = 0
    zone_usage: dict[int, str] = field(default_factory=dict)  # {0: "15/20 (75%)"}
    warnings: list[str] = field(default_factory=list)
```

### 6.2 StellarMemory health()

```python
class StellarMemory:
    def health(self) -> HealthStatus:
        """Run health diagnostics on the memory system."""
        status = HealthStatus()

        # DB check
        try:
            self.stats()
            status.db_accessible = True
        except Exception:
            status.db_accessible = False
            status.healthy = False
            status.warnings.append("Database is not accessible")

        # Scheduler
        status.scheduler_running = self._scheduler.running

        # Stats
        stats = self.stats()
        status.total_memories = stats.total_memories
        status.graph_edges = self._graph.count_edges()

        # Zone usage
        for zone_id, count in stats.zone_counts.items():
            cap = stats.zone_capacities.get(zone_id)
            if cap:
                pct = count / cap * 100
                status.zone_usage[zone_id] = f"{count}/{cap} ({pct:.0f}%)"
                if pct >= 80:
                    status.warnings.append(
                        f"Zone {zone_id} at {pct:.0f}% capacity"
                    )
            else:
                status.zone_usage[zone_id] = f"{count}/unlimited"

        if status.warnings:
            status.healthy = len([w for w in status.warnings
                                  if "not accessible" in w]) == 0

        return status
```

### 6.3 MCP Server health tool

```python
@mcp.tool()
def memory_health() -> str:
    """Run health diagnostics on the memory system."""
    h = memory.health()
    return json.dumps({
        "healthy": h.healthy,
        "db_accessible": h.db_accessible,
        "scheduler_running": h.scheduler_running,
        "total_memories": h.total_memories,
        "graph_edges": h.graph_edges,
        "zone_usage": {str(k): v for k, v in h.zone_usage.items()},
        "warnings": h.warnings,
    })
```

### 6.4 CLI health command

```python
# In cli.py, add:
subparsers.add_parser("health", help="System health check")

# ... in command handler:
elif args.command == "health":
    h = memory.health()
    status_str = "HEALTHY" if h.healthy else "UNHEALTHY"
    print(f"Status: {status_str}")
    print(f"DB: {'OK' if h.db_accessible else 'FAIL'}")
    print(f"Scheduler: {'running' if h.scheduler_running else 'stopped'}")
    print(f"Memories: {h.total_memories}")
    print(f"Graph edges: {h.graph_edges}")
    for zone_id, usage in sorted(h.zone_usage.items()):
        print(f"  Zone {zone_id}: {usage}")
    if h.warnings:
        print("Warnings:")
        for w in h.warnings:
            print(f"  - {w}")
```

### 6.5 CLI logs command

```python
# In cli.py, add:
p_logs = subparsers.add_parser("logs", help="Show event logs")
p_logs.add_argument("--limit", "-l", type=int, default=20)

# ... in command handler:
elif args.command == "logs":
    from stellar_memory.event_logger import EventLogger
    el = EventLogger(log_path="stellar_events.jsonl")
    entries = el.read_logs(limit=args.limit)
    for entry in entries:
        ts = entry.get("timestamp", 0)
        event = entry.get("event", "?")
        detail = {k: v for k, v in entry.items()
                  if k not in ("timestamp", "event")}
        print(f"[{ts:.0f}] {event}: {json.dumps(detail)}")
```

## 7. Config Summary

### 7.1 New Config Classes

```python
@dataclass
class DecayConfig:
    enabled: bool = True
    decay_days: int = 30
    auto_forget_days: int = 90
    min_zone_for_decay: int = 2

@dataclass
class EventLoggerConfig:
    enabled: bool = True
    log_path: str = "stellar_events.jsonl"
    max_size_mb: float = 10.0

@dataclass
class RecallConfig:
    graph_boost_enabled: bool = True
    graph_boost_score: float = 0.1
    graph_boost_depth: int = 1
```

### 7.2 StellarConfig Extensions

```python
@dataclass
class StellarConfig:
    # ... existing P3 fields ...
    decay: DecayConfig = field(default_factory=DecayConfig)
    event_logger: EventLoggerConfig = field(default_factory=EventLoggerConfig)
    recall_boost: RecallConfig = field(default_factory=RecallConfig)
```

### 7.3 GraphConfig Extension

```python
@dataclass
class GraphConfig:
    # ... existing P3 fields ...
    persistent: bool = True  # NEW
```

## 8. Model Extensions

```python
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
```

## 9. Implementation Order

```
Step 1:  Config extensions (DecayConfig, EventLoggerConfig, RecallConfig + StellarConfig + GraphConfig.persistent)
Step 2:  Model extensions (DecayResult, HealthStatus)
Step 3:  F1 - persistent_graph.py (PersistentMemoryGraph)
Step 4:  F1 - StellarMemory graph selection (persistent vs in-memory)
Step 5:  F2 - decay_manager.py (DecayManager)
Step 6:  F2 - EventBus new events (on_decay, on_auto_forget)
Step 7:  F2 - StellarMemory decay integration (_apply_decay in reorbit)
Step 8:  F3 - event_logger.py (EventLogger)
Step 9:  F3 - StellarMemory logger integration
Step 10: F4 - StellarMemory recall boost (_apply_graph_boost)
Step 11: F5 - StellarMemory health() method
Step 12: F5 - MCP server memory_health tool
Step 13: F5 - CLI health + logs commands
Step 14: __init__.py exports + pyproject.toml (version 0.5.0)
Step 15: Tests (5 files)
```

## 10. Test Design

### 10.1 test_persistent_graph.py (10 tests)
- add_edge 기본 동작
- get_edges 조회
- get_related_ids depth=1
- get_related_ids depth=2
- max_edges eviction (SQLite에서)
- remove_item 양방향 삭제
- count_edges
- 재시작 후 엣지 유지 (persistence 검증)
- StellarMemory에서 persistent graph 사용
- in-memory fallback (:memory: DB 시)

### 10.2 test_decay.py (10 tests)
- DecayManager disabled 시 빈 결과
- decay_days 경과 아이템 demote 대상
- auto_forget_days 경과 cloud 아이템 forget 대상
- min_zone_for_decay로 Core/Inner 보호
- StellarMemory reorbit 시 decay 적용
- decay 후 존 이동 확인
- auto_forget 후 삭제 확인
- on_zone_change 이벤트 발생
- decay 미대상 아이템 유지
- decay_days 미경과 아이템 유지

### 10.3 test_event_logger.py (8 tests)
- EventLogger JSONL 파일 생성
- store 이벤트 로그 기록
- recall 이벤트 로그 기록
- forget 이벤트 로그 기록
- read_logs limit 동작
- 로그 로테이션 (max_size)
- StellarMemory 자동 attach
- 빈 로그 read_logs 빈 리스트

### 10.4 test_recall_boost.py (8 tests)
- graph_boost_enabled=False 시 기존 동작
- graph_boost로 결과에 이웃 포함
- boost_score 가산 확인
- depth=1 이웃만 포함
- 결과 limit 유지
- 중복 제거 (이미 결과에 있는 이웃)
- 빈 그래프에서 부스트 무영향
- NullEmbedder에서도 동작 (graph 수동 연결 시)

### 10.5 test_health.py (8 tests)
- health() 기본 상태
- zone 용량 80% 이상 경고
- total_memories 정확성
- graph_edges 수 정확성
- scheduler 상태 반영
- zone_usage 포맷 확인
- CLI health 명령
- CLI logs 명령

## 11. File Structure (v0.5.0)

```
stellar_memory/
├── __init__.py              # P4 exports 추가
├── config.py                # + DecayConfig, EventLoggerConfig, RecallConfig
├── models.py                # + DecayResult, HealthStatus
├── stellar.py               # + decay, logger, recall boost, health 통합
├── persistent_graph.py      # NEW - SQLite-backed graph
├── decay_manager.py         # NEW - 자동 망각 시스템
├── event_logger.py          # NEW - JSONL 이벤트 로거
├── event_bus.py             # + on_decay, on_auto_forget events
├── memory_graph.py          # (기존 in-memory graph 유지)
├── mcp_server.py            # + memory_health tool
├── cli.py                   # + health, logs commands
├── namespace.py
├── memory_function.py
├── orbit_manager.py
├── scheduler.py
├── embedder.py
├── importance_evaluator.py
├── weight_tuner.py
├── llm_adapter.py
├── consolidator.py
├── session.py
├── serializer.py
├── utils.py
└── storage/
    ├── __init__.py
    ├── in_memory.py
    └── sqlite_storage.py

tests/
├── (기존 21개 유지)
├── test_persistent_graph.py  # NEW
├── test_decay.py             # NEW
├── test_event_logger.py      # NEW
├── test_recall_boost.py      # NEW
└── test_health.py            # NEW
```

## 12. Error Handling

| Scenario | Handling |
|----------|----------|
| SQLite edges 테이블 생성 실패 | InMemory graph로 fallback |
| Decay 대상 아이템 이미 삭제됨 | 건너뜀 (no error) |
| EventLogger 파일 쓰기 실패 | 로그 후 계속 (이벤트 처리 중단 안 함) |
| Recall boost 그래프 조회 실패 | 부스트 없이 원래 결과 반환 |
| Health check DB 접근 실패 | healthy=False, warning 추가 |
| 로그 로테이션 실패 | 기존 파일 계속 사용 |

## 13. Backward Compatibility

- 모든 새 기능은 config로 on/off 가능 (default: enabled)
- `GraphConfig.persistent=True`가 기본이지만 `:memory:` DB에서는 자동 InMemory 사용
- PersistentMemoryGraph와 MemoryGraph는 동일 인터페이스 (duck typing)
- 기존 193개 테스트 변경 없이 통과 (`:memory:` DB 사용 → InMemory graph)
- EventBus에 새 이벤트 추가해도 기존 핸들러에 영향 없음
- CLI 기존 명령 변경 없음, health/logs만 추가
