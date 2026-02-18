# Design: stellar-memory-p3 (AI Integration & Real-World Deployment)

## 1. Overview

P3는 Stellar Memory를 실제 AI 시스템에 연결하기 위한 5개 기능을 구현합니다.
핵심 목표: Claude Code/Desktop에서 MCP 서버를 통해 직접 기억을 관리할 수 있게 한다.

**Target Version**: v0.4.0
**New Files**: 5 (event_bus.py, namespace.py, memory_graph.py, mcp_server.py, cli.py)
**Modified Files**: 5 (stellar.py, config.py, models.py, __init__.py, pyproject.toml)

## 2. F2: Event Hook System

### 2.1 event_bus.py (NEW)

```python
"""Event bus for memory lifecycle hooks."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable, Any

logger = logging.getLogger(__name__)

EventHandler = Callable[..., None]


class EventBus:
    """Publish-subscribe event system for memory lifecycle events."""

    # Supported events
    EVENTS = (
        "on_store",        # (item: MemoryItem)
        "on_recall",       # (items: list[MemoryItem], query: str)
        "on_forget",       # (item_id: str)
        "on_reorbit",      # (result: ReorbitResult)
        "on_consolidate",  # (existing: MemoryItem, new_item: MemoryItem)
        "on_zone_change",  # (item: MemoryItem, from_zone: int, to_zone: int)
    )

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event: str, handler: EventHandler) -> None:
        """Register a handler for an event."""
        if event not in self.EVENTS:
            raise ValueError(f"Unknown event: {event}. Valid: {self.EVENTS}")
        self._handlers[event].append(handler)

    def off(self, event: str, handler: EventHandler) -> None:
        """Remove a handler for an event."""
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Emit an event, calling all registered handlers."""
        for handler in self._handlers.get(event, []):
            try:
                handler(*args, **kwargs)
            except Exception:
                logger.exception(f"Error in event handler for {event}")

    def clear(self, event: str | None = None) -> None:
        """Clear handlers for a specific event or all events."""
        if event:
            self._handlers[event].clear()
        else:
            self._handlers.clear()
```

### 2.2 StellarMemory Event Integration

```python
class StellarMemory:
    def __init__(self, config):
        # ... existing ...
        self._event_bus = EventBus()

    @property
    def events(self) -> EventBus:
        return self._event_bus

    def store(self, content, importance=0.5, metadata=None, auto_evaluate=False):
        # ... existing logic ...
        self._event_bus.emit("on_store", item)
        return item

    def recall(self, query, limit=5):
        # ... existing logic ...
        self._event_bus.emit("on_recall", results, query)
        return results

    def forget(self, memory_id):
        # ... existing logic ...
        if removed:
            self._event_bus.emit("on_forget", memory_id)
        return removed

    def reorbit(self):
        result = self._orbit_mgr.reorbit_all(self._memory_fn, time.time())
        self._event_bus.emit("on_reorbit", result)
        return result
```

### 2.3 EventConfig (NEW)

```python
@dataclass
class EventConfig:
    enabled: bool = True
    log_events: bool = False  # 이벤트를 로그로 기록
```

## 3. F3: Memory Namespace

### 3.1 namespace.py (NEW)

```python
"""Namespace management for multi-tenant memory isolation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import StellarConfig

class NamespaceManager:
    """Manages isolated memory namespaces."""

    def __init__(self, base_path: str = "stellar_data"):
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def get_db_path(self, namespace: str) -> str:
        """Get the database path for a namespace."""
        safe_name = self._sanitize(namespace)
        ns_dir = self._base_path / safe_name
        ns_dir.mkdir(parents=True, exist_ok=True)
        return str(ns_dir / "memory.db")

    def list_namespaces(self) -> list[str]:
        """List all existing namespaces."""
        if not self._base_path.exists():
            return []
        return [
            d.name for d in self._base_path.iterdir()
            if d.is_dir() and (d / "memory.db").exists()
        ]

    def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace and all its data."""
        import shutil
        safe_name = self._sanitize(namespace)
        ns_dir = self._base_path / safe_name
        if ns_dir.exists():
            shutil.rmtree(ns_dir)
            return True
        return False

    def _sanitize(self, name: str) -> str:
        """Sanitize namespace name for filesystem safety."""
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
```

### 3.2 StellarConfig 확장

```python
@dataclass
class NamespaceConfig:
    enabled: bool = True
    base_path: str = "stellar_data"

@dataclass
class StellarConfig:
    # ... existing fields ...
    namespace: NamespaceConfig = field(default_factory=NamespaceConfig)
```

### 3.3 StellarMemory Namespace Support

```python
class StellarMemory:
    def __init__(self, config=None, namespace: str | None = None):
        self.config = config or StellarConfig()
        # namespace가 지정되면 해당 namespace의 DB를 사용
        if namespace and self.config.namespace.enabled:
            ns_mgr = NamespaceManager(self.config.namespace.base_path)
            self.config.db_path = ns_mgr.get_db_path(namespace)
        self._namespace = namespace
        # ... rest of existing init ...
```

## 4. F4: Memory Graph

### 4.1 models.py Extensions

```python
@dataclass
class MemoryEdge:
    source_id: str
    target_id: str
    edge_type: str  # "related_to" | "derived_from" | "contradicts" | "sequence"
    weight: float = 1.0
    created_at: float = 0.0
```

### 4.2 memory_graph.py (NEW)

```python
"""Memory graph for associative recall."""

from __future__ import annotations

import time
from collections import defaultdict

from stellar_memory.models import MemoryEdge


class MemoryGraph:
    """Manages relationships between memories."""

    def __init__(self, max_edges_per_item: int = 20):
        self._max_edges = max_edges_per_item
        self._edges: dict[str, list[MemoryEdge]] = defaultdict(list)

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: str = "related_to", weight: float = 1.0) -> MemoryEdge:
        """Add a relationship between two memories."""
        edge = MemoryEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            created_at=time.time(),
        )
        edges = self._edges[source_id]
        if len(edges) >= self._max_edges:
            # Remove lowest-weight edge
            edges.sort(key=lambda e: e.weight)
            edges.pop(0)
        edges.append(edge)
        return edge

    def get_edges(self, item_id: str) -> list[MemoryEdge]:
        """Get all edges from a memory item."""
        return list(self._edges.get(item_id, []))

    def get_related_ids(self, item_id: str, depth: int = 1) -> set[str]:
        """Get IDs of related memories up to a certain depth."""
        visited: set[str] = set()
        queue = [(item_id, 0)]
        while queue:
            current_id, current_depth = queue.pop(0)
            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)
            if current_depth < depth:
                for edge in self._edges.get(current_id, []):
                    queue.append((edge.target_id, current_depth + 1))
        visited.discard(item_id)  # 자기 자신 제거
        return visited

    def remove_item(self, item_id: str) -> None:
        """Remove all edges involving an item."""
        self._edges.pop(item_id, None)
        for edges in self._edges.values():
            edges[:] = [e for e in edges if e.target_id != item_id]

    def count_edges(self) -> int:
        """Total number of edges in the graph."""
        return sum(len(edges) for edges in self._edges.values())
```

### 4.3 StellarMemory Graph Integration

```python
class StellarMemory:
    def __init__(self, config):
        # ... existing ...
        self._graph = MemoryGraph()

    def store(self, content, importance=0.5, metadata=None, auto_evaluate=False):
        # ... existing logic ...
        # 저장 후 자동으로 유사 기억과 연결
        self._auto_link(item)
        return item

    def _auto_link(self, item: MemoryItem) -> None:
        """Automatically create edges to similar memories."""
        if item.embedding is None:
            return
        from stellar_memory.utils import cosine_similarity
        all_items = self._orbit_mgr.get_all_items()
        for other in all_items:
            if other.id == item.id or other.embedding is None:
                continue
            sim = cosine_similarity(item.embedding, other.embedding)
            if sim >= 0.7:  # auto-link threshold
                self._graph.add_edge(item.id, other.id, "related_to", weight=sim)

    def recall_graph(self, item_id: str, depth: int = 2) -> list[MemoryItem]:
        """Recall memories related through the graph."""
        related_ids = self._graph.get_related_ids(item_id, depth)
        items = []
        for rid in related_ids:
            item = self._orbit_mgr.find_item(rid)
            if item is not None:
                items.append(item)
        return items

    def forget(self, memory_id):
        # ... existing logic ...
        self._graph.remove_item(memory_id)
        return removed
```

### 4.4 GraphConfig (NEW)

```python
@dataclass
class GraphConfig:
    enabled: bool = True
    auto_link: bool = True
    auto_link_threshold: float = 0.7
    max_edges_per_item: int = 20
```

## 5. F1: MCP Server

### 5.1 mcp_server.py (NEW)

Uses the official `mcp` Python SDK with `FastMCP`.

```python
"""MCP Server for Stellar Memory - enables AI tools to use memory as tools."""

from __future__ import annotations

import json
import logging

from stellar_memory.config import StellarConfig
from stellar_memory.stellar import StellarMemory

logger = logging.getLogger(__name__)


def create_mcp_server(config: StellarConfig | None = None,
                      namespace: str | None = None):
    """Create and configure the MCP server with all memory tools."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("stellar-memory")
    memory = StellarMemory(config or StellarConfig(), namespace=namespace)

    @mcp.tool()
    def memory_store(content: str, importance: float = 0.5,
                     metadata_json: str = "{}") -> str:
        """Store a new memory. Returns the memory ID.

        Args:
            content: The content to remember
            importance: Importance score from 0.0 to 1.0
            metadata_json: Optional JSON string of metadata
        """
        metadata = json.loads(metadata_json) if metadata_json else {}
        item = memory.store(content, importance=importance,
                           metadata=metadata, auto_evaluate=True)
        return json.dumps({
            "id": item.id,
            "zone": item.zone,
            "total_score": item.total_score,
        })

    @mcp.tool()
    def memory_recall(query: str, limit: int = 5) -> str:
        """Search memories by query. Returns matching memories.

        Args:
            query: Search query text
            limit: Maximum number of results (1-20)
        """
        limit = max(1, min(20, limit))
        results = memory.recall(query, limit=limit)
        return json.dumps([{
            "id": item.id,
            "content": item.content,
            "zone": item.zone,
            "importance": item.arbitrary_importance,
            "recall_count": item.recall_count,
        } for item in results])

    @mcp.tool()
    def memory_get(memory_id: str) -> str:
        """Get a specific memory by ID.

        Args:
            memory_id: The UUID of the memory to retrieve
        """
        item = memory.get(memory_id)
        if item is None:
            return json.dumps({"error": "Memory not found"})
        return json.dumps({
            "id": item.id,
            "content": item.content,
            "zone": item.zone,
            "importance": item.arbitrary_importance,
            "recall_count": item.recall_count,
            "created_at": item.created_at,
            "metadata": item.metadata,
        })

    @mcp.tool()
    def memory_forget(memory_id: str) -> str:
        """Delete a specific memory by ID.

        Args:
            memory_id: The UUID of the memory to delete
        """
        removed = memory.forget(memory_id)
        return json.dumps({"removed": removed})

    @mcp.tool()
    def memory_stats() -> str:
        """Get memory statistics including zone counts and capacities."""
        stats = memory.stats()
        return json.dumps({
            "total_memories": stats.total_memories,
            "zone_counts": stats.zone_counts,
            "zone_capacities": {
                k: v for k, v in stats.zone_capacities.items()
            },
        })

    @mcp.tool()
    def memory_export(include_embeddings: bool = False) -> str:
        """Export all memories as JSON.

        Args:
            include_embeddings: Whether to include embedding vectors
        """
        return memory.export_json(include_embeddings=include_embeddings)

    @mcp.tool()
    def memory_import(json_data: str) -> str:
        """Import memories from JSON data.

        Args:
            json_data: JSON string containing memories to import
        """
        count = memory.import_json(json_data)
        return json.dumps({"imported": count})

    @mcp.tool()
    def session_start() -> str:
        """Start a new memory session for context grouping."""
        session = memory.start_session()
        return json.dumps({
            "session_id": session.session_id,
            "started_at": session.started_at,
        })

    @mcp.tool()
    def session_end() -> str:
        """End the current session and optionally create a summary."""
        session = memory.end_session()
        if session is None:
            return json.dumps({"error": "No active session"})
        return json.dumps({
            "session_id": session.session_id,
            "ended_at": session.ended_at,
            "memory_count": session.memory_count,
            "summary": session.summary,
        })

    @mcp.resource("memory://stats")
    def resource_stats() -> str:
        """Real-time memory statistics."""
        stats = memory.stats()
        return json.dumps({
            "total_memories": stats.total_memories,
            "zone_counts": stats.zone_counts,
        })

    @mcp.resource("memory://zones")
    def resource_zones() -> str:
        """Zone configuration information."""
        zones = []
        for z in memory.config.zones:
            zones.append({
                "zone_id": z.zone_id,
                "name": z.name,
                "max_slots": z.max_slots,
                "importance_range": [z.importance_min, z.importance_max],
            })
        return json.dumps(zones)

    return mcp, memory
```

### 5.2 Server Entry Point

```python
# stellar_memory/mcp_server.py (bottom of file)

def run_server(config: StellarConfig | None = None,
               namespace: str | None = None,
               transport: str = "stdio") -> None:
    """Run the MCP server."""
    mcp, memory = create_mcp_server(config, namespace)
    memory.start()
    try:
        mcp.run(transport=transport)
    finally:
        memory.stop()
```

### 5.3 Claude Code Configuration

```json
// .claude/settings.json 또는 claude_desktop_config.json
{
  "mcpServers": {
    "stellar-memory": {
      "command": "python",
      "args": ["-m", "stellar_memory.mcp_server"]
    }
  }
}
```

## 6. F5: CLI Tool

### 6.1 cli.py (NEW)

```python
"""CLI tool for Stellar Memory management."""

from __future__ import annotations

import argparse
import json
import sys

from stellar_memory.config import StellarConfig
from stellar_memory.stellar import StellarMemory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="stellar-memory",
        description="Stellar Memory - AI memory management CLI",
    )
    parser.add_argument("--db", default="stellar_memory.db", help="Database path")
    parser.add_argument("--namespace", "-n", default=None, help="Memory namespace")

    subparsers = parser.add_subparsers(dest="command")

    # store
    p_store = subparsers.add_parser("store", help="Store a new memory")
    p_store.add_argument("content", help="Memory content")
    p_store.add_argument("--importance", "-i", type=float, default=0.5)

    # recall
    p_recall = subparsers.add_parser("recall", help="Search memories")
    p_recall.add_argument("query", help="Search query")
    p_recall.add_argument("--limit", "-l", type=int, default=5)

    # stats
    subparsers.add_parser("stats", help="Show memory statistics")

    # export
    p_export = subparsers.add_parser("export", help="Export memories to JSON")
    p_export.add_argument("--output", "-o", default="-", help="Output file (- for stdout)")
    p_export.add_argument("--embeddings", action="store_true")

    # import
    p_import = subparsers.add_parser("import", help="Import memories from JSON")
    p_import.add_argument("input", help="Input JSON file")

    # forget
    p_forget = subparsers.add_parser("forget", help="Delete a memory")
    p_forget.add_argument("id", help="Memory ID to delete")

    # reorbit
    subparsers.add_parser("reorbit", help="Trigger manual reorbit")

    # serve
    p_serve = subparsers.add_parser("serve", help="Start MCP server")
    p_serve.add_argument("--transport", default="stdio",
                         choices=["stdio", "streamable-http"])

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return

    config = StellarConfig(db_path=args.db)
    memory = StellarMemory(config, namespace=args.namespace)

    if args.command == "store":
        item = memory.store(args.content, importance=args.importance)
        print(json.dumps({"id": item.id, "zone": item.zone}))

    elif args.command == "recall":
        results = memory.recall(args.query, limit=args.limit)
        for item in results:
            print(f"[{item.id[:8]}] (zone {item.zone}, score {item.total_score:.3f}) {item.content[:100]}")

    elif args.command == "stats":
        stats = memory.stats()
        print(f"Total memories: {stats.total_memories}")
        for zone_id, count in sorted(stats.zone_counts.items()):
            cap = stats.zone_capacities.get(zone_id)
            cap_str = str(cap) if cap else "unlimited"
            print(f"  Zone {zone_id}: {count}/{cap_str}")

    elif args.command == "export":
        data = memory.export_json(include_embeddings=args.embeddings)
        if args.output == "-":
            print(data)
        else:
            with open(args.output, "w") as f:
                f.write(data)
            print(f"Exported to {args.output}")

    elif args.command == "import":
        with open(args.input) as f:
            data = f.read()
        count = memory.import_json(data)
        print(f"Imported {count} memories")

    elif args.command == "forget":
        removed = memory.forget(args.id)
        print("Removed" if removed else "Not found")

    elif args.command == "reorbit":
        result = memory.reorbit()
        print(f"Moved: {result.moved}, Evicted: {result.evicted}, "
              f"Total: {result.total_items}, Duration: {result.duration:.3f}s")

    elif args.command == "serve":
        from stellar_memory.mcp_server import run_server
        run_server(config, namespace=args.namespace, transport=args.transport)


if __name__ == "__main__":
    main()
```

### 6.2 pyproject.toml Entry Points

```toml
[project.scripts]
stellar-memory = "stellar_memory.cli:main"

[project.optional-dependencies]
mcp = ["mcp[cli]>=1.2.0"]
cli = ["mcp[cli]>=1.2.0"]
# existing
embedding = ["sentence-transformers>=2.2.0"]
llm = ["anthropic>=0.18.0"]
ai = ["sentence-transformers>=2.2.0", "anthropic>=0.18.0"]
all = ["sentence-transformers>=2.2.0", "anthropic>=0.18.0", "mcp[cli]>=1.2.0"]
dev = ["pytest>=7.0", "pytest-cov>=4.0"]
```

## 7. Config Summary

### 7.1 New Config Classes

```python
@dataclass
class EventConfig:
    enabled: bool = True
    log_events: bool = False

@dataclass
class NamespaceConfig:
    enabled: bool = True
    base_path: str = "stellar_data"

@dataclass
class GraphConfig:
    enabled: bool = True
    auto_link: bool = True
    auto_link_threshold: float = 0.7
    max_edges_per_item: int = 20
```

### 7.2 StellarConfig Extensions

```python
@dataclass
class StellarConfig:
    # ... existing P2 fields ...
    event: EventConfig = field(default_factory=EventConfig)
    namespace: NamespaceConfig = field(default_factory=NamespaceConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
```

## 8. Model Extensions

```python
@dataclass
class MemoryEdge:
    source_id: str
    target_id: str
    edge_type: str  # "related_to" | "derived_from" | "contradicts" | "sequence"
    weight: float = 1.0
    created_at: float = 0.0
```

## 9. Implementation Order

```
Step 1:  Config extensions (EventConfig, NamespaceConfig, GraphConfig + StellarConfig)
Step 2:  Model extensions (MemoryEdge)
Step 3:  F2 - event_bus.py (EventBus: on, off, emit, clear)
Step 4:  F2 - StellarMemory event integration (emit in store, recall, forget, reorbit)
Step 5:  F3 - namespace.py (NamespaceManager: get_db_path, list, delete)
Step 6:  F3 - StellarMemory namespace support (constructor namespace param)
Step 7:  F4 - memory_graph.py (MemoryGraph: add_edge, get_edges, get_related_ids, remove)
Step 8:  F4 - StellarMemory graph integration (_auto_link, recall_graph, forget cleanup)
Step 9:  F1 - mcp_server.py (create_mcp_server, 9 tools, 2 resources, run_server)
Step 10: F5 - cli.py (8 commands: store, recall, stats, export, import, forget, reorbit, serve)
Step 11: __init__.py exports + pyproject.toml (version 0.4.0, scripts, mcp dep)
Step 12: Tests (5 files)
```

## 10. Test Design

### 10.1 test_event_bus.py (10 tests)
- on/emit 기본 동작
- 여러 핸들러 등록
- off로 핸들러 제거
- emit 시 핸들러 에러 무시 (로그만)
- clear 특정 이벤트
- clear 전체
- 잘못된 이벤트명 ValueError
- StellarMemory store 시 on_store 발생
- StellarMemory recall 시 on_recall 발생
- StellarMemory forget 시 on_forget 발생

### 10.2 test_namespace.py (8 tests)
- get_db_path 경로 생성
- list_namespaces 빈 목록
- list_namespaces 존재하는 네임스페이스
- delete_namespace 삭제
- delete_namespace 존재하지 않는 것
- _sanitize 특수문자 처리
- StellarMemory namespace 파라미터
- 서로 다른 namespace는 독립 데이터

### 10.3 test_memory_graph.py (10 tests)
- add_edge 기본
- get_edges 조회
- get_related_ids depth=1
- get_related_ids depth=2
- max_edges_per_item 초과 시 최저 weight 제거
- remove_item 양방향 정리
- count_edges
- StellarMemory recall_graph
- auto_link 동작 (NullEmbedder에서는 건너뜀)
- forget 시 graph cleanup

### 10.4 test_mcp_server.py (10 tests)
- create_mcp_server 생성 확인
- memory_store tool 호출
- memory_recall tool 호출
- memory_get tool 호출
- memory_forget tool 호출
- memory_stats tool 호출
- session_start/end tool 호출
- memory_export tool 호출
- memory_import tool 호출
- resource_stats/resource_zones 접근

### 10.5 test_cli.py (8 tests)
- store 명령
- recall 명령
- stats 명령
- export 명령 (stdout)
- export 명령 (파일)
- import 명령
- forget 명령
- reorbit 명령

## 11. File Structure (v0.4.0)

```
stellar_memory/
├── __init__.py              # P3 exports 추가
├── config.py                # + EventConfig, NamespaceConfig, GraphConfig
├── models.py                # + MemoryEdge
├── stellar.py               # + event, namespace, graph 통합
├── event_bus.py             # NEW - 이벤트 훅 시스템
├── namespace.py             # NEW - 네임스페이스 관리
├── memory_graph.py          # NEW - 기억 연상 그래프
├── mcp_server.py            # NEW - MCP 서버
├── cli.py                   # NEW - CLI 도구
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
├── (기존 16개 유지)
├── test_event_bus.py         # NEW
├── test_namespace.py         # NEW
├── test_memory_graph.py      # NEW
├── test_mcp_server.py        # NEW
└── test_cli.py               # NEW
```

## 12. Error Handling

| Scenario | Handling |
|----------|----------|
| Event handler 예외 | 로그 후 계속 (다른 핸들러 영향 없음) |
| Namespace 특수문자 | _sanitize로 안전한 이름 변환 |
| Graph max_edges 초과 | 최저 weight edge 자동 제거 |
| MCP tool 잘못된 입력 | JSON error 응답 반환 |
| CLI 잘못된 명령 | argparse help 출력 |
| mcp 미설치 | ImportError → CLI serve만 비활성 |

## 13. Backward Compatibility

- 모든 새 기능은 config로 on/off 가능 (default: enabled)
- StellarMemory의 기존 생성자 시그니처 유지 (namespace는 optional)
- 기존 147개 테스트 변경 없이 통과
- MCP와 CLI는 optional dependency (`pip install stellar-memory[mcp]`)
- EventBus가 없는 환경 = 이벤트 단순히 발생 안 함
