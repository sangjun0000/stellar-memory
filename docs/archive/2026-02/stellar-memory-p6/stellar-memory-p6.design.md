# stellar-memory-p6 Design Document

> **Summary**: 분산 지능 & 실시간 협업 - 다중 에이전트 기억 공유 플랫폼
>
> **Project**: Stellar Memory
> **Version**: v0.7.0
> **Author**: User
> **Date**: 2026-02-17
> **Status**: Draft
> **Planning Doc**: [stellar-memory-p6.plan.md](../01-plan/features/stellar-memory-p6.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **분산 확장**: SQLite 단일 파일 → PostgreSQL/Redis 다중 백엔드 지원
2. **실시간 협업**: 여러 AI 에이전트가 같은 기억 공간을 안전하게 공유
3. **기억 보안**: 민감 기억의 암호화 + 역할 기반 접근 제어
4. **지식 자동화**: 외부 소스(웹, 파일, API)에서 자동 기억 수집
5. **시각화**: 태양계 모델 기반 기억 분포 대시보드
6. **하위 호환**: 기존 318개 테스트 100% 유지, 기존 API 변경 없음

### 1.2 Design Principles

- **ABC 추상화**: 모든 신규 서브시스템은 ABC/Protocol로 인터페이스 먼저 정의
- **Optional Everything**: 모든 신규 기능은 optional dependency로 분리, SQLite 기본값 유지
- **동기 API 우선**: 기존 동기 API 유지 + `async_` 접두사로 비동기 메서드 추가
- **Null 패턴 확장**: 외부 서비스 미연결 시 NullCache, NullSync 등으로 안전 동작
- **단순한 CRDT**: LWW-Register로 시작, 복잡한 병합은 향후 확장

---

## 2. Architecture

### 2.1 전체 시스템 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│                        StellarMemory (v0.7.0)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │ MCP     │  │ CLI      │  │ Dashboard│  │ LLM Adapter          │ │
│  │ Server  │  │ Tool     │  │ (FastAPI)│  │ (Claude/GPT/Ollama)  │ │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘ │
│       └────────────┼─────────────┼────────────────────┘             │
│                    ▼             ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Core Layer                                │   │
│  │  StellarMemory / OrbitManager / MemoryFunction / Scheduler  │   │
│  │  Embedder / Evaluator / Consolidator / SessionManager       │   │
│  │  Summarizer / AdaptiveDecay / GraphAnalyzer                 │   │
│  └──────────┬──────────────────┬──────────────┬────────────────┘   │
│             │                  │              │                     │
│  ┌──────────▼────┐  ┌─────────▼──────┐  ┌───▼──────────────────┐  │
│  │ SecurityLayer │  │ SyncLayer      │  │ ConnectorLayer       │  │
│  │ (P6-F3)      │  │ (P6-F2)        │  │ (P6-F4)              │  │
│  │ Encryption   │  │ CRDT Manager   │  │ Web/File/API         │  │
│  │ RBAC         │  │ WS Server      │  │ Connectors           │  │
│  │ Audit        │  │ WS Client      │  │                      │  │
│  └──────┬───────┘  └───────┬────────┘  └──────────────────────┘  │
│         │                  │                                       │
│  ┌──────▼──────────────────▼───────────────────────────────────┐  │
│  │                  StorageBackend (P6-F1)                      │  │
│  │  ┌──────────┐  ┌───────────────┐  ┌────────────┐           │  │
│  │  │ SQLite   │  │ PostgreSQL    │  │ Redis      │           │  │
│  │  │ (기존)   │  │ + pgvector    │  │ Cache      │           │  │
│  │  │ default  │  │ (분산)        │  │ (Core/Inner)│           │  │
│  │  └──────────┘  └───────────────┘  └────────────┘           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 기능별 데이터 플로우

**F1: 분산 스토리지**
```
store(item) → SecurityLayer.encrypt_if_needed(item)
            → StorageBackend.store(item)
            → RedisCache.invalidate(zone)

recall(query) → RedisCache.check(query)
              → [HIT] → return cached
              → [MISS] → StorageBackend.search(query) → RedisCache.set()
```

**F2: 실시간 동기화**
```
Agent A: store(item) → StorageBackend.store()
                     → SyncManager.broadcast(ChangeEvent)
                     → WebSocket Server → broadcast to connected clients

Agent B: WebSocket Client → receive(ChangeEvent)
                          → SyncManager.apply_remote(ChangeEvent)
                          → StorageBackend.store() (LWW merge)
```

**F3: 기억 보안**
```
store(item, encrypted=True) → SecurityManager.check_permission("write")
                             → SecurityManager.encrypt(item.content)
                             → StorageBackend.store(encrypted_item)

recall(query, role="reader") → SecurityManager.check_permission("read")
                              → StorageBackend.search(query)
                              → SecurityManager.decrypt(items)
                              → filter by role visibility
```

**F4: 외부 지식 커넥터**
```
ingest_url(url) → WebConnector.fetch(url)
               → Summarizer.summarize(content)
               → MemoryItem.create(summary, metadata={source_url: url})
               → Consolidator.check_duplicate()
               → store(item)
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| PostgresStorage | asyncpg, pgvector | 분산 스토리지 |
| RedisCache | redis | 캐시 레이어 |
| MemorySyncManager | StorageBackend, EventBus | CRDT 동기화 |
| WsServer / WsClient | websockets | 실시간 통신 |
| SecurityManager | cryptography | 암호화 |
| AccessControl | SecurityConfig | RBAC |
| WebConnector | httpx, Summarizer | URL 수집 |
| FileConnector | watchdog | 파일 감시 |
| DashboardApp | fastapi, uvicorn | 웹 대시보드 |

---

## 3. Data Model

### 3.1 신규/변경 모델

```python
# MemoryItem 확장 (기존 필드 유지 + 신규 필드)
@dataclass
class MemoryItem:
    # ... 기존 필드 모두 유지 ...
    encrypted: bool = False                      # P6: 암호화 여부
    source_type: str = "user"                    # P6: "user" | "web" | "file" | "api"
    source_url: str | None = None                # P6: 외부 소스 URL
    ingested_at: float | None = None             # P6: 수집 시각
    vector_clock: dict[str, int] | None = None   # P6: CRDT 버전 벡터

# 신규: 동기화 변경 이벤트
@dataclass
class ChangeEvent:
    event_type: str          # "store" | "update" | "remove" | "move"
    item_id: str
    agent_id: str            # 변경 에이전트 식별자
    timestamp: float
    vector_clock: dict[str, int]
    payload: dict = field(default_factory=dict)

# 신규: 보안 역할
@dataclass
class AccessRole:
    name: str                # "admin" | "writer" | "reader"
    permissions: list[str]   # ["store", "recall", "forget", "export", ...]

# 신규: 커넥터 수집 결과
@dataclass
class IngestResult:
    source_url: str
    memory_id: str
    summary_text: str
    was_duplicate: bool = False
    original_length: int = 0

# 신규: 대시보드 존 분포
@dataclass
class ZoneDistribution:
    zone_id: int
    zone_name: str
    count: int
    capacity: int | None
    usage_percent: float
```

### 3.2 PostgreSQL 스키마

```sql
-- 기억 테이블 (기존 SQLite 스키마 확장)
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    created_at DOUBLE PRECISION NOT NULL,
    last_recalled_at DOUBLE PRECISION NOT NULL,
    recall_count INTEGER DEFAULT 0,
    arbitrary_importance DOUBLE PRECISION DEFAULT 0.5,
    zone INTEGER DEFAULT -1,
    metadata JSONB DEFAULT '{}',
    total_score DOUBLE PRECISION DEFAULT 0.0,
    encrypted BOOLEAN DEFAULT FALSE,
    source_type TEXT DEFAULT 'user',
    source_url TEXT,
    ingested_at DOUBLE PRECISION,
    vector_clock JSONB
);

-- pgvector 임베딩 벡터
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS
    embedding vector(384);  -- 기본 dimension

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_memories_zone ON memories(zone);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(arbitrary_importance);
CREATE INDEX IF NOT EXISTS idx_memories_recalled ON memories(last_recalled_at);

-- 벡터 유사도 검색 인덱스 (IVFFlat)
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 그래프 엣지 테이블
CREATE TABLE IF NOT EXISTS memory_edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    weight DOUBLE PRECISION DEFAULT 1.0,
    created_at DOUBLE PRECISION DEFAULT 0,
    PRIMARY KEY (source_id, target_id, edge_type)
);

-- 보안 감사 로그
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp DOUBLE PRECISION NOT NULL,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,       -- "store", "recall", "forget", "decrypt"
    target_id TEXT,
    role TEXT,
    success BOOLEAN DEFAULT TRUE,
    details JSONB DEFAULT '{}'
);
```

---

## 4. Feature Design Details

### 4.1 F1: 분산 스토리지 백엔드 (StorageBackend)

#### 4.1.1 StorageBackend ABC

```python
# stellar_memory/storage/__init__.py (리팩토링)

class StorageBackend(ABC):
    """통합 스토리지 백엔드 인터페이스.

    기존 ZoneStorage를 포함하며, 백엔드 수준의 관리 메서드를 추가.
    ZoneStorage는 하위 호환을 위해 유지하되, 내부적으로 StorageBackend에 위임.
    """

    @abstractmethod
    def store(self, item: MemoryItem) -> None: ...

    @abstractmethod
    def get(self, item_id: str) -> MemoryItem | None: ...

    @abstractmethod
    def remove(self, item_id: str) -> bool: ...

    @abstractmethod
    def update(self, item: MemoryItem) -> None: ...

    @abstractmethod
    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None,
               zone: int | None = None) -> list[MemoryItem]: ...

    @abstractmethod
    def get_all(self, zone: int | None = None) -> list[MemoryItem]: ...

    @abstractmethod
    def count(self, zone: int | None = None) -> int: ...

    @abstractmethod
    def get_lowest_score_item(self, zone: int) -> MemoryItem | None: ...

    # P6 신규: 백엔드 관리
    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...

    def health_check(self) -> bool:
        return self.is_connected()
```

**하위 호환 전략**: 기존 `ZoneStorage` ABC는 유지. `StorageFactory`가 `StorageBackend`로 래핑하여 존별 `ZoneStorage`를 생성. 기존 코드는 변경 없이 동작.

#### 4.1.2 PostgresStorage

```python
# stellar_memory/storage/postgres_storage.py

class PostgresStorage(StorageBackend):
    """PostgreSQL + pgvector 기반 분산 스토리지."""

    def __init__(self, db_url: str, pool_size: int = 10):
        self._db_url = db_url
        self._pool_size = pool_size
        self._pool: asyncpg.Pool | None = None

    def connect(self) -> None:
        """동기 연결 (내부적으로 asyncio.run)."""
        import asyncio
        asyncio.run(self._async_connect())

    async def _async_connect(self) -> None:
        import asyncpg
        self._pool = await asyncpg.create_pool(
            self._db_url, min_size=2, max_size=self._pool_size
        )
        await self._ensure_schema()

    def store(self, item: MemoryItem) -> None:
        """동기 store - asyncio.run으로 래핑."""
        import asyncio
        asyncio.run(self._async_store(item))

    async def _async_store(self, item: MemoryItem) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memories (id, content, created_at, last_recalled_at,
                    recall_count, arbitrary_importance, zone, metadata,
                    total_score, encrypted, source_type, source_url,
                    ingested_at, embedding, vector_clock)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                ON CONFLICT (id) DO UPDATE SET
                    content=EXCLUDED.content, zone=EXCLUDED.zone,
                    total_score=EXCLUDED.total_score,
                    last_recalled_at=EXCLUDED.last_recalled_at
            """, item.id, item.content, item.created_at, ...)

    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None,
               zone: int | None = None) -> list[MemoryItem]:
        import asyncio
        return asyncio.run(self._async_search(query, limit, query_embedding, zone))

    async def _async_search(self, query: str, limit: int,
                            query_embedding: list[float] | None,
                            zone: int | None) -> list[MemoryItem]:
        async with self._pool.acquire() as conn:
            if query_embedding:
                # pgvector 코사인 유사도 검색
                rows = await conn.fetch("""
                    SELECT *, embedding <=> $1::vector AS distance
                    FROM memories
                    WHERE ($2::int IS NULL OR zone = $2)
                    ORDER BY distance ASC
                    LIMIT $3
                """, query_embedding, zone, limit)
            else:
                # 텍스트 ILIKE 검색
                rows = await conn.fetch("""
                    SELECT * FROM memories
                    WHERE content ILIKE $1
                    AND ($2::int IS NULL OR zone = $2)
                    ORDER BY total_score DESC
                    LIMIT $3
                """, f"%{query}%", zone, limit)
            return [self._row_to_item(r) for r in rows]
```

#### 4.1.3 RedisCache

```python
# stellar_memory/storage/redis_cache.py

class RedisCache:
    """Redis 기반 읽기 캐시 레이어 (Core/Inner 존)."""

    def __init__(self, redis_url: str, ttl: int = 300, cached_zones: tuple = (0, 1)):
        self._url = redis_url
        self._ttl = ttl
        self._cached_zones = cached_zones
        self._client: redis.Redis | None = None

    def connect(self) -> None:
        import redis as redis_lib
        self._client = redis_lib.from_url(self._url, decode_responses=False)

    def get(self, item_id: str) -> MemoryItem | None:
        if not self._client:
            return None
        data = self._client.get(f"sm:{item_id}")
        if data:
            return self._deserialize(data)
        return None

    def set(self, item: MemoryItem) -> None:
        if not self._client or item.zone not in self._cached_zones:
            return
        self._client.setex(f"sm:{item.id}", self._ttl, self._serialize(item))

    def invalidate(self, item_id: str) -> None:
        if self._client:
            self._client.delete(f"sm:{item_id}")

    def invalidate_zone(self, zone: int) -> None:
        """존 전체 캐시 무효화."""
        if not self._client:
            return
        # zone 태그 기반 삭제 패턴
        for key in self._client.scan_iter(f"sm:zone:{zone}:*"):
            self._client.delete(key)
```

#### 4.1.4 StorageConfig 확장

```python
# config.py에 추가

@dataclass
class StorageConfig:
    backend: str = "sqlite"         # "sqlite" | "postgresql" | "memory"
    db_url: str | None = None       # PostgreSQL URL (backend="postgresql"일 때)
    pool_size: int = 10
    redis_url: str | None = None    # Redis URL (없으면 캐시 비활성화)
    redis_ttl: int = 300            # Redis TTL (초)
    redis_cached_zones: tuple = (0, 1)  # 캐시 대상 존

# StellarConfig에 추가
@dataclass
class StellarConfig:
    # ... 기존 필드 모두 유지 ...
    storage: StorageConfig = field(default_factory=StorageConfig)
```

---

### 4.2 F2: 실시간 기억 동기화 (MemorySync)

#### 4.2.1 MemorySyncManager (CRDT LWW-Register)

```python
# stellar_memory/sync/sync_manager.py

class MemorySyncManager:
    """CRDT Last-Write-Wins Register 기반 동기화 관리자."""

    def __init__(self, agent_id: str, event_bus: EventBus):
        self._agent_id = agent_id
        self._event_bus = event_bus
        self._clock: dict[str, int] = {}  # vector clock
        self._ws_server: WsServer | None = None
        self._ws_client: WsClient | None = None
        self._pending_queue: list[ChangeEvent] = []

    def on_local_change(self, event_type: str, item: MemoryItem) -> ChangeEvent:
        """로컬 변경 → ChangeEvent 생성 + 브로드캐스트."""
        self._clock[self._agent_id] = self._clock.get(self._agent_id, 0) + 1
        event = ChangeEvent(
            event_type=event_type,
            item_id=item.id,
            agent_id=self._agent_id,
            timestamp=time.time(),
            vector_clock=dict(self._clock),
            payload={"content": item.content, "zone": item.zone, ...},
        )
        if self._ws_server:
            self._ws_server.broadcast(event)
        return event

    def apply_remote(self, event: ChangeEvent, backend: StorageBackend) -> bool:
        """원격 변경 수신 → LWW 머지 → 로컬 적용."""
        local_item = backend.get(event.item_id)
        if local_item is None:
            # 로컬에 없으면 그대로 적용
            new_item = self._event_to_item(event)
            backend.store(new_item)
            return True
        # LWW: 타임스탬프가 더 최신이면 적용
        if event.timestamp > local_item.last_recalled_at:
            self._merge_item(local_item, event)
            backend.update(local_item)
            return True
        return False  # 로컬이 더 최신 → 무시

    def start_server(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self._ws_server = WsServer(host, port, self)
        self._ws_server.start()

    def connect_to(self, url: str) -> None:
        self._ws_client = WsClient(url, self)
        self._ws_client.connect()
```

#### 4.2.2 WebSocket 서버/클라이언트

```python
# stellar_memory/sync/ws_server.py

class WsServer:
    """WebSocket 서버: ChangeEvent 브로드캐스트."""

    def __init__(self, host: str, port: int, sync_mgr: MemorySyncManager):
        self._host = host
        self._port = port
        self._sync_mgr = sync_mgr
        self._clients: set[websockets.WebSocketServerProtocol] = set()

    async def _handler(self, ws, path):
        self._clients.add(ws)
        try:
            async for message in ws:
                event = ChangeEvent.from_json(message)
                self._sync_mgr.apply_remote(event, ...)
                await self._broadcast_except(message, ws)
        finally:
            self._clients.discard(ws)

    def broadcast(self, event: ChangeEvent) -> None:
        message = event.to_json()
        import asyncio
        asyncio.run(self._broadcast_all(message))

    def start(self) -> None:
        import asyncio, threading
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=self._run_server, args=(loop,), daemon=True)
        thread.start()

# stellar_memory/sync/ws_client.py

class WsClient:
    """WebSocket 클라이언트: 원격 서버에 연결하여 변경 수신."""

    def __init__(self, url: str, sync_mgr: MemorySyncManager):
        self._url = url
        self._sync_mgr = sync_mgr
        self._ws = None
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0

    def connect(self) -> None:
        import asyncio, threading
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=self._run_client, args=(loop,), daemon=True)
        thread.start()

    async def _run_with_reconnect(self):
        while True:
            try:
                async with websockets.connect(self._url) as ws:
                    self._ws = ws
                    self._reconnect_delay = 1.0
                    async for message in ws:
                        event = ChangeEvent.from_json(message)
                        self._sync_mgr.apply_remote(event, ...)
            except (ConnectionError, websockets.ConnectionClosed):
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, self._max_reconnect_delay
                )
```

#### 4.2.3 SyncConfig

```python
@dataclass
class SyncConfig:
    enabled: bool = False
    agent_id: str = ""           # 이 에이전트의 고유 ID
    ws_host: str = "0.0.0.0"
    ws_port: int = 8765
    remote_url: str | None = None  # 연결할 원격 서버 URL
    auto_start_server: bool = False
```

---

### 4.3 F3: 기억 보안 & 접근 제어

#### 4.3.1 SecurityManager

```python
# stellar_memory/security/encryption.py

class EncryptionManager:
    """AES-256-GCM 암호화/복호화."""

    def __init__(self, key: bytes | None = None):
        if key is None:
            import os
            key_b64 = os.environ.get("STELLAR_ENCRYPTION_KEY")
            if key_b64:
                import base64
                key = base64.b64decode(key_b64)
        self._key = key  # 32 bytes for AES-256

    @property
    def available(self) -> bool:
        return self._key is not None

    def encrypt(self, plaintext: str) -> str:
        """평문 → base64(nonce + ciphertext + tag)."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os, base64
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, ciphertext_b64: str) -> str:
        """base64(nonce + ciphertext + tag) → 평문."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import base64
        data = base64.b64decode(ciphertext_b64)
        nonce, ct = data[:12], data[12:]
        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(nonce, ct, None).decode()
```

#### 4.3.2 AccessControl (RBAC)

```python
# stellar_memory/security/access_control.py

# 기본 역할 정의
DEFAULT_ROLES = {
    "admin":  ["store", "recall", "forget", "export", "import", "config", "decrypt"],
    "writer": ["store", "recall", "forget", "export"],
    "reader": ["recall"],
}

class AccessControl:
    """역할 기반 접근 제어."""

    def __init__(self, roles: dict[str, list[str]] | None = None):
        self._roles = roles or DEFAULT_ROLES

    def check(self, role: str, action: str) -> bool:
        """역할에 해당 액션 권한이 있는지 확인."""
        perms = self._roles.get(role, [])
        return action in perms or "*" in perms

    def require(self, role: str, action: str) -> None:
        """권한 없으면 PermissionError 발생."""
        if not self.check(role, action):
            raise PermissionError(
                f"Role '{role}' lacks permission for '{action}'"
            )
```

#### 4.3.3 SecurityAudit

```python
# stellar_memory/security/audit.py

class SecurityAudit:
    """보안 감사 로그 (P4 EventLogger 확장)."""

    def __init__(self, event_logger=None):
        self._logger = event_logger

    def log_access(self, agent_id: str, action: str, target_id: str,
                   role: str, success: bool = True) -> None:
        if self._logger:
            self._logger.log_event("security_audit", {
                "agent_id": agent_id,
                "action": action,
                "target_id": target_id,
                "role": role,
                "success": success,
                "timestamp": time.time(),
            })
```

#### 4.3.4 SecurityConfig

```python
@dataclass
class SecurityConfig:
    enabled: bool = False
    encryption_key_env: str = "STELLAR_ENCRYPTION_KEY"
    access_control: bool = False
    default_role: str = "writer"
    roles: dict[str, list[str]] | None = None  # None → DEFAULT_ROLES
    audit_enabled: bool = True
    auto_encrypt_tags: list[str] = field(default_factory=lambda: ["secret", "sensitive", "api_key"])
```

#### 4.3.5 StellarMemory 보안 통합

```python
# stellar.py에서 SecurityManager 통합
class StellarMemory:
    def __init__(self, config, ...):
        # ... 기존 초기화 ...

        # P6: Security
        self._security = None
        if config.security.enabled:
            from stellar_memory.security import SecurityManager
            self._security = SecurityManager(config.security, self._event_logger)

    def store(self, content: str, importance: float = 0.5,
              metadata: dict | None = None,
              encrypted: bool = False,     # P6 신규 파라미터
              role: str | None = None,     # P6 신규 파라미터
              ) -> MemoryItem:
        if self._security and role:
            self._security.access_control.require(role, "store")
        item = MemoryItem.create(content, importance, metadata)
        if encrypted and self._security:
            item.content = self._security.encryption.encrypt(content)
            item.encrypted = True
        # ... 기존 로직 ...

    def recall(self, query: str, limit: int = 5,
               role: str | None = None,  # P6
               ) -> list[MemoryItem]:
        if self._security and role:
            self._security.access_control.require(role, "recall")
        results = # ... 기존 로직 ...
        # 암호화된 기억 복호화
        if self._security:
            for item in results:
                if item.encrypted:
                    item.content = self._security.encryption.decrypt(item.content)
        return results
```

---

### 4.4 F4: 외부 지식 커넥터

#### 4.4.1 KnowledgeConnector ABC

```python
# stellar_memory/connectors/__init__.py

class KnowledgeConnector(ABC):
    """외부 지식 소스 커넥터 인터페이스."""

    @abstractmethod
    def ingest(self, source: str, **kwargs) -> IngestResult: ...

    @abstractmethod
    def can_handle(self, source: str) -> bool: ...
```

#### 4.4.2 WebConnector

```python
# stellar_memory/connectors/web_connector.py

class WebConnector(KnowledgeConnector):
    """URL → 기억 변환 커넥터."""

    def __init__(self, summarizer=None, consolidator=None):
        self._summarizer = summarizer
        self._consolidator = consolidator

    def can_handle(self, source: str) -> bool:
        return source.startswith("http://") or source.startswith("https://")

    def ingest(self, source: str, **kwargs) -> IngestResult:
        import httpx
        resp = httpx.get(source, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        text = self._extract_text(resp.text)

        # P5 Summarizer로 요약
        summary = text
        if self._summarizer and len(text) > 100:
            result = self._summarizer.summarize_text(text)
            summary = result.summary_text if result else text

        return IngestResult(
            source_url=source,
            memory_id="",  # store 시 할당
            summary_text=summary,
            original_length=len(text),
        )

    def _extract_text(self, html: str) -> str:
        """HTML → 순수 텍스트 추출 (간단 구현)."""
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
```

#### 4.4.3 FileConnector

```python
# stellar_memory/connectors/file_connector.py

class FileConnector(KnowledgeConnector):
    """파일/디렉토리 → 기억 변환 커넥터."""

    def __init__(self, summarizer=None):
        self._summarizer = summarizer
        self._watcher = None

    def can_handle(self, source: str) -> bool:
        from pathlib import Path
        return Path(source).exists()

    def ingest(self, source: str, **kwargs) -> IngestResult:
        from pathlib import Path
        path = Path(source)
        text = path.read_text(encoding="utf-8", errors="ignore")

        summary = text
        if self._summarizer and len(text) > 100:
            result = self._summarizer.summarize_text(text)
            summary = result.summary_text if result else text

        return IngestResult(
            source_url=f"file://{path.resolve()}",
            memory_id="",
            summary_text=summary,
            original_length=len(text),
        )

    def watch(self, directory: str, pattern: str = "*.md",
              callback=None) -> None:
        """디렉토리 감시 시작 (watchdog)."""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class Handler(FileSystemEventHandler):
            def on_modified(self_, event):
                if not event.is_directory and fnmatch(event.src_path, pattern):
                    result = self.ingest(event.src_path)
                    if callback:
                        callback(result)

        observer = Observer()
        observer.schedule(Handler(), directory, recursive=False)
        observer.start()
        self._watcher = observer
```

#### 4.4.4 ApiConnector

```python
# stellar_memory/connectors/api_connector.py

class ApiConnector(KnowledgeConnector):
    """주기적 API 호출 → 기억 변환."""

    def __init__(self, summarizer=None):
        self._summarizer = summarizer
        self._subscriptions: dict[str, float] = {}  # url → interval

    def can_handle(self, source: str) -> bool:
        return source.startswith("http") and "api" in source.lower()

    def ingest(self, source: str, **kwargs) -> IngestResult:
        import httpx, json
        resp = httpx.get(source, timeout=30)
        resp.raise_for_status()
        text = json.dumps(resp.json(), ensure_ascii=False, indent=2)

        summary = text
        if self._summarizer and len(text) > 100:
            result = self._summarizer.summarize_text(text)
            summary = result.summary_text if result else text

        return IngestResult(
            source_url=source,
            memory_id="",
            summary_text=summary,
            original_length=len(text),
        )

    def subscribe(self, url: str, interval: float = 3600) -> None:
        """주기적 API 호출 구독."""
        self._subscriptions[url] = interval
        # 스케줄러와 연동하여 주기적 호출
```

#### 4.4.5 ConnectorConfig

```python
@dataclass
class ConnectorConfig:
    enabled: bool = False
    web_enabled: bool = True
    file_enabled: bool = True
    api_enabled: bool = True
    auto_summarize: bool = True
    dedup_check: bool = True    # Consolidator로 중복 검사
```

---

### 4.5 F5: 기억 시각화 대시보드

#### 4.5.1 FastAPI 앱

```python
# stellar_memory/dashboard/app.py

def create_dashboard_app(memory: StellarMemory) -> FastAPI:
    """StellarMemory 인스턴스를 받아 대시보드 FastAPI 앱 생성."""
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    app = FastAPI(title="Stellar Memory Dashboard", version="0.7.0")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        stats = memory.stats()
        zones = memory.config.zones
        return render_solar_system(stats, zones)

    @app.get("/api/stats")
    async def api_stats():
        stats = memory.stats()
        return {
            "total_memories": stats.total_memories,
            "zone_counts": stats.zone_counts,
            "zone_capacities": stats.zone_capacities,
        }

    @app.get("/api/graph")
    async def api_graph():
        if memory._analyzer:
            return {
                "stats": memory.graph_stats().__dict__,
                "dot": memory._analyzer.export_dot(),
            }
        return {"error": "Graph analytics not enabled"}

    @app.get("/api/memories")
    async def api_memories(zone: int | None = None, limit: int = 50):
        items = []
        for z in (memory.config.zones if zone is None else [memory.config.zones[zone]]):
            storage = memory._orbit_mgr.get_zone_storage(z.zone_id)
            items.extend(storage.get_all())
        items.sort(key=lambda x: x.total_score, reverse=True)
        return [_item_to_dict(i) for i in items[:limit]]

    @app.get("/api/events")
    async def sse_events(request):
        """Server-Sent Events 스트림."""
        from sse_starlette.sse import EventSourceResponse
        async def event_generator():
            queue = asyncio.Queue()
            memory._event_bus.on("*", lambda e: queue.put_nowait(e))
            while True:
                event = await queue.get()
                yield {"data": json.dumps(event)}
        return EventSourceResponse(event_generator())

    return app
```

#### 4.5.2 태양계 모델 HTML 뷰

```python
# stellar_memory/dashboard/templates/index.html
# 서버사이드 렌더링으로 최소 JS 사용

def render_solar_system(stats: MemoryStats, zones: list[ZoneConfig]) -> str:
    """존별 기억 분포를 태양계 모델로 시각화."""
    # SVG 기반 동심원 표현
    # - Core: 중앙 원 (태양, 금색)
    # - Inner: 두 번째 궤도 (주황)
    # - Outer: 세 번째 궤도 (파랑)
    # - Belt: 네 번째 궤도 (회색 점선)
    # - Cloud: 외곽 희미한 원 (반투명)
    # 각 원 위에 기억 수/용량 표시
    ...
```

#### 4.5.3 DashboardConfig

```python
@dataclass
class DashboardConfig:
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8080
    auto_start: bool = False
```

---

## 5. StellarConfig 최종 확장

```python
@dataclass
class StellarConfig:
    # === 기존 필드 (변경 없음) ===
    memory_function: MemoryFunctionConfig
    zones: list[ZoneConfig]
    reorbit_interval: int = 300
    db_path: str = "stellar_memory.db"
    log_level: str = "INFO"
    auto_start_scheduler: bool = True
    embedder: EmbedderConfig
    llm: LLMConfig
    tuner: TunerConfig
    consolidation: ConsolidationConfig
    session: SessionConfig
    event: EventConfig
    namespace: NamespaceConfig
    graph: GraphConfig
    decay: DecayConfig
    event_logger: EventLoggerConfig
    recall_boost: RecallConfig
    vector_index: VectorIndexConfig
    summarization: SummarizationConfig
    graph_analytics: GraphAnalyticsConfig

    # === P6 신규 필드 ===
    storage: StorageConfig = field(default_factory=StorageConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    connectors: ConnectorConfig = field(default_factory=ConnectorConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
```

---

## 6. Error Handling

### 6.1 에러 코드 정의

| Error | Cause | Handling |
|-------|-------|----------|
| `StorageConnectionError` | PostgreSQL/Redis 연결 실패 | SQLite 폴백 + 경고 로그 |
| `EncryptionError` | 암호화 키 미설정/잘못됨 | 평문 저장 + 경고 |
| `PermissionError` | RBAC 권한 부족 | 예외 발생 (호출자 처리) |
| `SyncConflictError` | CRDT 충돌 (동시 수정) | LWW 자동 해결 + 이벤트 발행 |
| `ConnectorError` | 외부 소스 접근 실패 | 무시 + 경고 로그 |
| `DashboardStartError` | FastAPI 시작 실패 | 기능 비활성화 + 경고 |

### 6.2 Graceful Degradation

모든 P6 기능은 **실패 시 기존 기능에 영향 없음**:
- PostgreSQL 연결 실패 → SQLite 사용
- Redis 연결 실패 → 캐시 없이 동작
- WebSocket 연결 실패 → 동기화 없이 독립 동작
- 암호화 키 없음 → 평문 저장 (경고)
- 대시보드 시작 실패 → CLI/MCP는 정상 동작

---

## 7. Security Considerations

- [x] AES-256-GCM 인증 암호화 (무결성 보장)
- [x] 암호화 키는 환경변수로만 전달 (코드에 하드코딩 금지)
- [x] RBAC으로 역할별 액션 제한
- [x] 민감 기억 content 필드 로깅 금지 (마스킹)
- [x] 보안 감사 로그 (누가, 언제, 무엇에 접근)
- [x] WebSocket 연결은 로컬(127.0.0.1) 기본값 (외부 노출 시 사용자 명시 필요)
- [x] PostgreSQL 연결 문자열의 비밀번호 로깅 금지

---

## 8. Test Plan

### 8.1 Test Scope

| Type | Target | Tool | Files |
|------|--------|------|-------|
| Unit | StorageBackend ABC + 구현체 | pytest + mock | `test_storage_backend.py` |
| Unit | SecurityManager, RBAC, Encryption | pytest | `test_security.py` |
| Unit | MemorySyncManager, CRDT | pytest | `test_sync.py` |
| Unit | Connectors (Web/File/API) | pytest + httpx mock | `test_connectors.py` |
| Unit | Dashboard API | pytest + httpx (TestClient) | `test_dashboard.py` |
| Integration | StellarMemory + P6 전체 통합 | pytest | 기존 테스트 파일 확장 |

### 8.2 Test Cases (핵심)

**F1: 분산 스토리지 (16+ tests)**
- [ ] StorageBackend ABC 인터페이스 검증
- [ ] PostgresStorage store/get/search/remove (mock asyncpg)
- [ ] PostgresStorage pgvector 벡터 검색 (mock)
- [ ] RedisCache get/set/invalidate/invalidate_zone (mock redis)
- [ ] StorageFactory가 backend 설정에 따라 올바른 구현체 생성
- [ ] SQLite 폴백 (PostgreSQL 미연결 시)
- [ ] StorageConfig 기본값 검증

**F2: 실시간 동기화 (14+ tests)**
- [ ] ChangeEvent 직렬화/역직렬화
- [ ] SyncManager.on_local_change() → vector clock 증가
- [ ] SyncManager.apply_remote() → LWW 머지 (최신 타임스탬프 승리)
- [ ] SyncManager.apply_remote() → 로컬이 최신이면 무시
- [ ] WsServer 브로드캐스트 (mock websockets)
- [ ] WsClient 재연결 로직 (exponential backoff)
- [ ] SyncConfig 기본값 검증

**F3: 기억 보안 (16+ tests)**
- [ ] EncryptionManager.encrypt() → decrypt() 라운드트립
- [ ] EncryptionManager 키 없으면 available=False
- [ ] AccessControl.check("admin", "store") → True
- [ ] AccessControl.check("reader", "store") → False
- [ ] AccessControl.require() 권한 없으면 PermissionError
- [ ] StellarMemory.store(encrypted=True) → 암호화 저장
- [ ] StellarMemory.recall() → 암호화 기억 자동 복호화
- [ ] SecurityAudit 로그 기록 검증
- [ ] SecurityConfig 기본값 검증
- [ ] auto_encrypt_tags 기반 자동 암호화

**F4: 외부 지식 커넥터 (14+ tests)**
- [ ] WebConnector.can_handle("https://...") → True
- [ ] WebConnector.ingest() → IngestResult (mock httpx)
- [ ] WebConnector HTML 텍스트 추출
- [ ] FileConnector.can_handle("/path/file.md") → True
- [ ] FileConnector.ingest() → IngestResult
- [ ] ApiConnector.ingest() → IngestResult (mock httpx)
- [ ] KnowledgeConnector ABC 인터페이스 검증
- [ ] Summarizer 연동 (100자 이상 자동 요약)
- [ ] Consolidator 연동 (중복 검사)
- [ ] ConnectorConfig 기본값 검증

**F5: 시각화 대시보드 (12+ tests)**
- [ ] create_dashboard_app() → FastAPI 인스턴스
- [ ] GET / → HTML 응답 (태양계 모델)
- [ ] GET /api/stats → JSON (zone_counts)
- [ ] GET /api/graph → JSON (dot 포함)
- [ ] GET /api/memories → JSON (기억 목록)
- [ ] GET /api/memories?zone=0 → Core 존만
- [ ] render_solar_system() 출력 검증
- [ ] DashboardConfig 기본값 검증

**하위 호환 (기존 318개)**
- [ ] 기존 전체 테스트 변경 없이 통과

### 8.3 예상 테스트 수

| 기능 | 신규 테스트 | 누적 |
|------|:---------:|:----:|
| F1: 분산 스토리지 | 16 | 334 |
| F2: 실시간 동기화 | 14 | 348 |
| F3: 기억 보안 | 16 | 364 |
| F4: 외부 지식 커넥터 | 14 | 378 |
| F5: 시각화 대시보드 | 12 | 390 |
| 통합/엣지케이스 | 10+ | 400+ |
| **합계** | **82+** | **400+** |

---

## 9. Implementation Order

```
Phase 1: F1 분산 스토리지 (기반 인프라) ─────────────────────────────
  Step  1: StorageBackend ABC 정의
  Step  2: 기존 SqliteStorage/InMemoryStorage → StorageBackend 구현
  Step  3: StorageFactory 리팩토링 (backend 설정 기반)
  Step  4: PostgresStorage 구현 (asyncpg + pgvector)
  Step  5: RedisCache 구현
  Step  6: StorageConfig 추가 + StellarConfig 확장
  Step  7: StellarMemory 생성자에서 StorageBackend 통합

Phase 2: F3 기억 보안 (분산 환경 전제) ──────────────────────────────
  Step  8: EncryptionManager (AES-256-GCM)
  Step  9: AccessControl (RBAC: admin/writer/reader)
  Step 10: SecurityAudit (감사 로그)
  Step 11: SecurityConfig 추가 + StellarConfig 확장
  Step 12: StellarMemory.store()/recall()에 보안 통합

Phase 3: F2 실시간 동기화 ───────────────────────────────────────────
  Step 13: ChangeEvent 모델 + 직렬화
  Step 14: MemorySyncManager (CRDT LWW-Register)
  Step 15: WsServer (asyncio + websockets)
  Step 16: WsClient (재연결 로직)
  Step 17: SyncConfig 추가 + StellarConfig 확장
  Step 18: MCP 도구 memory_sync_status

Phase 4: F4 외부 지식 커넥터 ────────────────────────────────────────
  Step 19: KnowledgeConnector ABC
  Step 20: WebConnector (httpx + HTML 텍스트 추출)
  Step 21: FileConnector (pathlib + watchdog)
  Step 22: ApiConnector (httpx + JSON)
  Step 23: ConnectorConfig 추가 + StellarConfig 확장
  Step 24: StellarMemory.ingest() 메서드

Phase 5: F5 시각화 대시보드 ─────────────────────────────────────────
  Step 25: FastAPI 앱 + REST API 라우트
  Step 26: 태양계 모델 HTML/SVG 렌더링
  Step 27: 그래프 네트워크 HTML 뷰
  Step 28: SSE 실시간 이벤트 스트림
  Step 29: DashboardConfig 추가

Phase 6: 마무리 ─────────────────────────────────────────────────────
  Step 30: __init__.py P6 exports 추가 + version 0.7.0
  Step 31: pyproject.toml 업데이트 (9개 optional deps)
  Step 32: tests/test_storage_backend.py (16 tests)
  Step 33: tests/test_security.py (16 tests)
  Step 34: tests/test_sync.py (14 tests)
  Step 35: tests/test_connectors.py (14 tests)
  Step 36: tests/test_dashboard.py (12 tests)
  Step 37: 전체 회귀 테스트 (400+ tests)
```

---

## 10. Naming Conventions (P6 적용)

| Target | Rule | Example |
|--------|------|---------|
| 클래스 (ABC) | `PascalCase` + 역할 접미사 | `StorageBackend`, `KnowledgeConnector` |
| 클래스 (구현체) | `PascalCase` + 기술명 | `PostgresStorage`, `RedisCache` |
| Config 클래스 | `PascalCase` + `Config` | `SecurityConfig`, `SyncConfig` |
| 모듈 파일 | `snake_case` | `postgres_storage.py`, `access_control.py` |
| 패키지 디렉토리 | `snake_case` | `security/`, `connectors/`, `sync/` |
| 비동기 메서드 | `_async_` 접두사 (내부) | `_async_store()`, `_async_search()` |
| 공개 비동기 | `async_` 접두사 | `async_store()`, `async_recall()` |
| 환경변수 | `STELLAR_` 접두사 + `UPPER_SNAKE` | `STELLAR_ENCRYPTION_KEY` |
| 테스트 클래스 | `Test` + 대상 클래스명 | `TestPostgresStorage`, `TestEncryption` |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | Initial draft | User |
