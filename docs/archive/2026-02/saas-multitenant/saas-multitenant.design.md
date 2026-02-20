# SaaS Multi-Tenancy Design Document

> **Summary**: PostgreSQL Row-Level 멀티테넌시 구현 + 티어 동기화 상세 설계
>
> **Project**: stellar-memory
> **Version**: v1.0.0 → v1.1.0
> **Author**: Claude
> **Date**: 2026-02-20
> **Status**: Draft
> **Planning Doc**: [saas-multitenant.plan.md](../../01-plan/features/saas-multitenant.plan.md)

---

## 1. Overview

### 1.1 Design Goals

- PostgreSQL `memories` 테이블에 `user_id` 컬럼 추가로 완전한 테넌트 격리
- 기존 API 표면(endpoint paths, request/response format) 변경 없이 내부적으로 user_id 필터링
- `StorageBackend` 인터페이스에 `user_id` 파라미터 추가 (하위 호환성 유지)
- 백엔드 티어 코드와 랜딩 페이지 가격 완전 동기화

### 1.2 Design Principles

- **최소 변경 원칙**: 기존 로컬 모드(SQLite, 환경변수 인증)는 그대로 동작
- **하위 호환성**: `user_id=None`이면 기존 동작과 동일 (필터 없음)
- **Storage Layer 격리**: 테넌트 컨텍스트는 storage layer에서만 처리, StellarMemory 클래스 변경 최소화

---

## 2. Architecture

### 2.1 Tenant Context Flow (변경 후)

```
Request → check_api_key() → request.state.user_id
              ↓
         API endpoint → memory.store(content, ..., user_id=user_id)
              ↓
         StellarMemory.store() → self._orbit_mgr.place(item, zone, score)
              ↓
         OrbitManager.place() → storage.store(item)  # item.user_id 포함
              ↓
         PostgresStorage._async_store() → INSERT ... user_id=$16
```

### 2.2 Component Diagram (변경 범위)

```
┌──────────────┐     ┌──────────────────────────┐     ┌──────────────────┐
│   Client     │────▶│   server.py              │────▶│  PostgreSQL      │
│  (API Key)   │     │  ┌─────────────────────┐ │     │  ┌────────────┐  │
│              │     │  │ check_api_key()      │ │     │  │ memories   │  │
│              │     │  │ → user_id [EXISTING] │ │     │  │ + user_id  │  │ ← F1
│              │     │  └─────────────────────┘ │     │  │   [NEW]    │  │
│              │     │  ┌─────────────────────┐ │     │  └────────────┘  │
│              │     │  │ store/recall/forget  │ │     │                  │
│              │     │  │ + user_id 전달 [NEW]│ │     │  ┌────────────┐  │
│              │     │  └─────────────────────┘ │     │  │ users      │  │
│              │     └──────────────────────────┘     │  │ [EXISTING] │  │
│              │                                       │  └────────────┘  │
└──────────────┘                                       └──────────────────┘
```

### 2.3 Dependencies

| Component | Depends On | Change Type |
|-----------|-----------|-------------|
| `postgres_storage.py` | `models.py` (MemoryItem.user_id) | Schema + Query 변경 |
| `server.py` | `stellar.py` (store/recall user_id param) | 파라미터 전달 추가 |
| `stellar.py` | `orbit_manager.py` → `storage` | user_id 전파 |
| `auth.py` | `postgres_storage.py` (memories.user_id 존재) | 기존 쿼리 정상 동작 |
| `tiers.py` | None (독립) | 값 변경만 |
| `ws_server.py` | auth.py (user_id 인증) | Room 격리 추가 |

---

## 3. Data Model

### 3.1 MemoryItem 변경

```python
# stellar_memory/models.py - MemoryItem 클래스 (line 71)
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
    encrypted: bool = False
    source_type: str = "user"
    source_url: str | None = None
    ingested_at: float | None = None
    vector_clock: dict[str, int] | None = None
    emotion: EmotionVector | None = None
    content_type: str = "text"
    user_id: str | None = None          # NEW: 테넌트 격리
```

### 3.2 MemoryItem.create() 변경

```python
# stellar_memory/models.py - MemoryItem.create() (line 94)
@classmethod
def create(cls, content: str, importance: float = 0.5,
           metadata: dict | None = None,
           user_id: str | None = None) -> MemoryItem:   # NEW param
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
        user_id=user_id,                                 # NEW
    )
```

### 3.3 Database Schema 변경

```sql
-- migrations/001_add_user_id.sql

-- Step 1: Add user_id column (nullable for backward compat)
ALTER TABLE memories
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Step 2: Composite indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_memories_user_zone
    ON memories(user_id, zone);
CREATE INDEX IF NOT EXISTS idx_memories_user_score
    ON memories(user_id, total_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_recalled
    ON memories(user_id, last_recalled_at DESC);

-- Step 3: RLS policy (defense in depth)
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY memories_tenant_isolation ON memories
    FOR ALL
    USING (
        user_id = current_setting('app.current_user_id', true)::uuid
        OR user_id IS NULL  -- allow legacy data access
    );
```

### 3.4 PostgresStorage._ensure_schema() 변경

```python
# postgres_storage.py - CREATE TABLE에 user_id 추가 (line 55-73)
# pgvector variant:
await conn.execute("""
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
        vector_clock JSONB DEFAULT '{}',
        embedding vector(384),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE  -- NEW
    )
""")

# BYTEA variant: 동일하게 user_id 추가 (line 75-93)
```

---

## 4. API Specification

### 4.1 변경되는 엔드포인트 (내부 동작만 변경, 외부 인터페이스 유지)

| Method | Path | 변경 내용 |
|--------|------|----------|
| POST | `/api/v1/store` | `memory.store(..., user_id=user_id)` 추가 |
| GET | `/api/v1/recall` | `memory.recall(..., user_id=user_id)` 추가 |
| DELETE | `/api/v1/forget/{id}` | `memory.forget(id, user_id=user_id)` 추가 |
| GET | `/api/v1/memories` | user_id 기반 필터링 |
| GET | `/api/v1/timeline` | user_id 기반 필터링 |
| POST | `/api/v1/narrate` | user_id 기반 필터링 |
| GET | `/api/v1/stats` | user_id 기반 통계 |

### 4.2 server.py 엔드포인트 변경 상세

#### `POST /api/v1/store` (line 254)

```python
# 변경 전:
async def store(req: StoreRequest):
    item = memory.store(
        req.content, importance=req.importance,
        metadata=req.metadata, auto_evaluate=req.auto_evaluate,
    )

# 변경 후:
async def store(req: StoreRequest, request: Request):
    user_id = getattr(request.state, "user_id", None)
    item = memory.store(
        req.content, importance=req.importance,
        metadata=req.metadata, auto_evaluate=req.auto_evaluate,
        user_id=user_id,
    )
```

#### `GET /api/v1/recall` (line 273)

```python
# 변경 전:
async def recall(q: str, limit: int = 5, emotion: str | None = None):
    results = memory.recall(q, limit=min(limit, 50), emotion=emotion)

# 변경 후:
async def recall(q: str, limit: int = 5, emotion: str | None = None,
                 request: Request = None):
    user_id = getattr(request.state, "user_id", None) if request else None
    results = memory.recall(q, limit=min(limit, 50), emotion=emotion,
                            user_id=user_id)
```

#### `DELETE /api/v1/forget/{id}` (line 291)

```python
# 변경 전:
async def forget(memory_id: str):
    removed = memory.forget(memory_id)

# 변경 후:
async def forget(memory_id: str, request: Request):
    user_id = getattr(request.state, "user_id", None)
    removed = memory.forget(memory_id, user_id=user_id)
```

#### `GET /api/v1/memories` (line 305)

```python
# 변경 전:
async def memories(zone: int | None = None, limit: int = 50, offset: int = 0):
    all_items = memory._orbit_mgr.get_all_items()

# 변경 후:
async def memories(zone: int | None = None, limit: int = 50, offset: int = 0,
                   request: Request = None):
    user_id = getattr(request.state, "user_id", None) if request else None
    all_items = memory._orbit_mgr.get_all_items(user_id=user_id)
```

### 4.3 에러 응답 변경 없음

기존 에러 코드/포맷 그대로 유지. user_id 불일치 시 단순히 빈 결과 반환 (정보 노출 방지).

---

## 5. Storage Layer 변경

### 5.1 StorageBackend 인터페이스 (storage/__init__.py)

```python
class StorageBackend(ABC):
    """P6: Unified storage backend interface."""

    @abstractmethod
    def store(self, item: MemoryItem) -> None: ...
    # item.user_id를 통해 전달 → 인터페이스 변경 없음

    @abstractmethod
    def get(self, item_id: str, user_id: str | None = None) -> MemoryItem | None: ...
    # NEW: user_id 파라미터 추가

    @abstractmethod
    def remove(self, item_id: str, user_id: str | None = None) -> bool: ...
    # NEW: user_id 파라미터 추가

    @abstractmethod
    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None,
               zone: int | None = None,
               user_id: str | None = None) -> list[MemoryItem]: ...
    # NEW: user_id 파라미터 추가

    @abstractmethod
    def get_all(self, zone: int | None = None,
                user_id: str | None = None) -> list[MemoryItem]: ...
    # NEW: user_id 파라미터 추가

    @abstractmethod
    def count(self, zone: int | None = None,
              user_id: str | None = None) -> int: ...
    # NEW: user_id 파라미터 추가
```

### 5.2 PostgresStorage 쿼리 변경

#### store (line 135-169)

```python
async def _async_store(self, item: MemoryItem) -> None:
    # INSERT에 user_id 추가 (16번째 파라미터)
    await conn.execute("""
        INSERT INTO memories
            (id, content, created_at, last_recalled_at, recall_count,
             arbitrary_importance, zone, metadata, total_score,
             encrypted, source_type, source_url, ingested_at,
             vector_clock, embedding, user_id)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
        ON CONFLICT (id) DO UPDATE SET ...
    """, ..., item.user_id)
```

#### get (line 175-180)

```python
async def _async_get(self, item_id: str,
                     user_id: str | None = None) -> MemoryItem | None:
    if user_id:
        row = await conn.fetchrow(
            "SELECT * FROM memories WHERE id = $1 AND user_id = $2",
            item_id, user_id
        )
    else:
        row = await conn.fetchrow(
            "SELECT * FROM memories WHERE id = $1", item_id
        )
```

#### remove (line 186-191)

```python
async def _async_remove(self, item_id: str,
                        user_id: str | None = None) -> bool:
    if user_id:
        result = await conn.execute(
            "DELETE FROM memories WHERE id = $1 AND user_id = $2",
            item_id, user_id
        )
    else:
        result = await conn.execute(
            "DELETE FROM memories WHERE id = $1", item_id
        )
```

#### search (line 202-237)

모든 쿼리 변형에 `AND user_id = $N` 조건 추가:

```python
async def _async_search(self, query: str, limit: int,
                        query_embedding: list[float] | None,
                        zone: int | None,
                        user_id: str | None = None) -> list[MemoryItem]:
    # 4가지 쿼리 분기 모두에 user_id 필터 추가
    # pgvector + zone: WHERE zone = $2 AND user_id = $4
    # pgvector only: WHERE user_id = $3
    # text + zone: WHERE zone = $1 AND LOWER(content) LIKE $2 AND user_id = $4
    # text only: WHERE LOWER(content) LIKE $1 AND user_id = $3
```

#### get_all (line 243-251)

```python
async def _async_get_all(self, zone: int | None,
                         user_id: str | None = None) -> list[MemoryItem]:
    if zone is not None and user_id:
        rows = await conn.fetch(
            "SELECT * FROM memories WHERE zone = $1 AND user_id = $2",
            zone, user_id
        )
    elif user_id:
        rows = await conn.fetch(
            "SELECT * FROM memories WHERE user_id = $1", user_id
        )
    # ... 기존 분기 유지
```

#### count (line 257-265)

```python
async def _async_count(self, zone: int | None,
                       user_id: str | None = None) -> int:
    if zone is not None and user_id:
        row = await conn.fetchrow(
            "SELECT COUNT(*) FROM memories WHERE zone = $1 AND user_id = $2",
            zone, user_id
        )
    elif user_id:
        row = await conn.fetchrow(
            "SELECT COUNT(*) FROM memories WHERE user_id = $1", user_id
        )
    # ... 기존 분기 유지
```

#### _row_to_item (line 279-300)

```python
def _row_to_item(self, row) -> MemoryItem:
    return MemoryItem(
        ...,
        user_id=row.get("user_id"),  # NEW: user_id 매핑
    )
```

### 5.3 ZoneStorage & InMemoryStorage

`ZoneStorage` 인터페이스는 변경하지 않음. `item.user_id` 필드를 통해 전달.
InMemoryStorage/SqliteStorage는 user_id 필터링을 추가하지 않음 (로컬 단일 사용자 모드).

---

## 6. StellarMemory 클래스 변경

### 6.1 store() (stellar.py line 202)

```python
def store(self, content: str, importance: float = 0.5,
          metadata: dict | None = None,
          auto_evaluate: bool = False,
          skip_summarize: bool = False,
          encrypted: bool = False,
          role: str | None = None,
          emotion: EmotionVector | None = None,
          content_type: str | None = None,
          user_id: str | None = None) -> MemoryItem:   # NEW
    # ...
    item = MemoryItem.create(content, importance, metadata, user_id=user_id)
    # 이후 로직 동일 (item.user_id가 storage까지 전파)
```

### 6.2 recall() 변경

```python
def recall(self, query: str, limit: int = 5, ...,
           user_id: str | None = None) -> list[MemoryItem]:   # NEW
    # storage.search()에 user_id 전달
    # _orbit_mgr를 통하지 않고 직접 storage backend를 사용하는 경우 user_id 추가
```

### 6.3 forget() 변경

```python
def forget(self, item_id: str,
           user_id: str | None = None) -> bool:   # NEW
    # storage.remove()에 user_id 전달
    # 소유권 검증: 해당 user_id의 메모리만 삭제 가능
```

---

## 7. Tier 코드 동기화 (F3)

### 7.1 tiers.py 변경

```python
# 변경 전:
TIER_LIMITS: dict[str, dict] = {
    "free": {
        "max_memories": 5_000,
        "max_agents": 1,
        "rate_limit": 60,
        "max_api_keys": 1,
    },
    "pro": {
        "max_memories": 50_000,
        "max_agents": 5,
        "rate_limit": 300,
        "max_api_keys": 5,
    },
    "team": {
        "max_memories": 500_000,
        "max_agents": 20,
        "rate_limit": 1_000,
        "max_api_keys": 20,
    },
}
_TIER_ORDER = ["free", "pro", "team"]

# 변경 후:
TIER_LIMITS: dict[str, dict] = {
    "free": {
        "max_memories": 1_000,
        "max_agents": 1,
        "rate_limit": 60,
        "max_api_keys": 1,
    },
    "pro": {
        "max_memories": 50_000,
        "max_agents": 5,
        "rate_limit": 300,
        "max_api_keys": 5,
    },
    "promax": {
        "max_memories": 500_000,
        "max_agents": -1,       # unlimited
        "rate_limit": 1_000,
        "max_api_keys": 20,
    },
}
_TIER_ORDER = ["free", "pro", "promax"]
```

### 7.2 users 테이블 tier 값 마이그레이션

```sql
-- migrations/001_add_user_id.sql에 포함
UPDATE users SET tier = 'promax' WHERE tier = 'team';
```

### 7.3 기타 코드에서 "team" 참조 변경

| File | Location | Change |
|------|----------|--------|
| `tiers.py` | `TIER_LIMITS`, `_TIER_ORDER` | `team` → `promax` |
| `server.py` | webhook tier mapping | `team` → `promax` |
| `billing/webhooks.py` | event processing | `team` → `promax` (있는 경우) |

---

## 8. Memory Counting 수정 (F4)

### 8.1 auth.py get_memory_count() (line 249)

```python
# 변경 전 (line 258-261):
return await conn.fetchval(
    "SELECT COUNT(*) FROM memories WHERE user_id = $1",
    user_id,
) or 0
# 문제: memories 테이블에 user_id 컬럼이 없어서 에러

# 변경 후: F1 마이그레이션 적용 후 동일 쿼리가 정상 동작
# user_id 타입 불일치 수정 (str → UUID 캐스팅)
async def get_memory_count(self, user_id: str) -> int:
    async with self._pool.acquire() as conn:
        count = await conn.fetchval(
            """SELECT COUNT(*) FROM information_schema.tables
               WHERE table_name = 'memories'""",
        )
        if count:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM memories WHERE user_id = $1::uuid",
                user_id,
            ) or 0
    return 0
```

---

## 9. WebSocket Sync 테넌트 격리 (F5)

### 9.1 ws_server.py Room 기반 변경

```python
class WsServer:
    def __init__(self, manager, host="0.0.0.0", port=8765):
        self._manager = manager
        self._host = host
        self._port = port
        self._rooms: dict[str, set] = {}   # CHANGED: user_id → set[ws]
        self._client_user: dict = {}        # NEW: ws → user_id mapping
        # ...

    async def _handler(self, websocket, path):
        # NEW: 연결 시 인증
        user_id = await self._authenticate(websocket)
        if not user_id:
            await websocket.close(1008, "Authentication required")
            return

        # Room에 추가
        if user_id not in self._rooms:
            self._rooms[user_id] = set()
        self._rooms[user_id].add(websocket)
        self._client_user[websocket] = user_id

        try:
            async for message in websocket:
                data = json.loads(message)
                evt = ChangeEvent.from_dict(data)
                if self._manager.apply_remote(evt):
                    # 같은 user의 다른 클라이언트에만 브로드캐스트
                    await self._broadcast_to_room(
                        user_id, message, exclude=websocket
                    )
        finally:
            self._rooms.get(user_id, set()).discard(websocket)
            self._client_user.pop(websocket, None)

    async def _authenticate(self, websocket) -> str | None:
        """첫 메시지로 API key 인증, user_id 반환."""
        try:
            msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(msg)
            api_key = data.get("api_key", "")
            # auth_manager를 통해 user_id 조회
            if self._auth_manager:
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                user = await self._auth_manager.get_user_by_api_key(key_hash)
                if user:
                    await websocket.send(json.dumps({"authenticated": True}))
                    return user.id
        except Exception:
            pass
        return None

    async def _broadcast_to_room(self, user_id: str, message: str,
                                  exclude=None) -> None:
        """같은 user_id의 클라이언트에만 브로드캐스트."""
        for client in list(self._rooms.get(user_id, [])):
            if client is not exclude:
                try:
                    await client.send(message)
                except Exception:
                    self._rooms[user_id].discard(client)
```

### 9.2 ws_client.py 인증 추가

```python
class WsClient:
    async def connect(self, url: str, api_key: str | None = None):
        self._ws = await websockets.connect(url)
        if api_key:
            # 연결 후 첫 메시지로 인증
            await self._ws.send(json.dumps({"api_key": api_key}))
            resp = json.loads(await self._ws.recv())
            if not resp.get("authenticated"):
                raise ConnectionError("WebSocket authentication failed")
```

---

## 10. Security Considerations

- [x] user_id는 서버에서 API key를 통해 결정 (클라이언트가 지정 불가)
- [x] PostgreSQL RLS 정책으로 이중 보호
- [x] 교차 테넌트 접근 시 빈 결과 반환 (404 대신, 존재 여부 노출 방지)
- [x] WebSocket 연결 시 API key 인증 필수
- [x] user_id=None 허용 (로컬 모드 하위 호환성)
- [ ] HTTPS 적용 (Fly.io 기본 제공)
- [ ] Rate Limiting 유지 (기존 동작 그대로)

---

## 11. Test Plan

### 11.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| Unit Test | Storage layer user_id 필터링 | pytest |
| Integration Test | API endpoint 테넌트 격리 | pytest + httpx |
| Security Test | 교차 테넌트 접근 차단 | pytest |

### 11.2 Test Cases

- [ ] User A가 저장한 메모리를 User A만 recall 가능
- [ ] User B가 User A의 memory_id로 forget 시도 → 실패 (빈 결과)
- [ ] User A의 메모리 카운트가 정확히 User A의 것만 포함
- [ ] user_id=None (로컬 모드)에서 기존 동작 유지
- [ ] 티어 업그레이드 시 기존 메모리 유지
- [ ] WebSocket Sync: User A의 에이전트 간에만 동기화
- [ ] WebSocket Sync: 인증 없는 연결 거부

---

## 12. Implementation Guide

### 12.1 File Change List

```
수정 (10 files):
├── stellar_memory/models.py               # MemoryItem.user_id + create()
├── stellar_memory/storage/__init__.py      # StorageBackend 인터페이스
├── stellar_memory/storage/postgres_storage.py  # 스키마 + 모든 쿼리
├── stellar_memory/stellar.py              # store/recall/forget user_id param
├── stellar_memory/orbit_manager.py        # get_all_items user_id 전달
├── stellar_memory/server.py               # 엔드포인트 user_id 전파
├── stellar_memory/auth.py                 # get_memory_count UUID 캐스팅
├── stellar_memory/billing/tiers.py        # team→promax, 수치 변경
├── stellar_memory/sync/ws_server.py       # Room 기반 격리
└── stellar_memory/sync/ws_client.py       # 인증 추가

신규 (1 file):
└── migrations/001_add_user_id.sql         # DB 마이그레이션
```

### 12.2 Implementation Order

```
Step 1: Data Layer (F1)
  1. models.py - MemoryItem에 user_id 추가
  2. storage/__init__.py - StorageBackend 인터페이스에 user_id 파라미터
  3. postgres_storage.py - 스키마 + 모든 쿼리 변경
  4. migrations/001_add_user_id.sql - 마이그레이션 스크립트

Step 2: Tier Sync (F3)
  5. billing/tiers.py - team→promax, 수치 변경

Step 3: Memory Count Fix (F4)
  6. auth.py - get_memory_count UUID 캐스팅

Step 4: API Layer (F2)
  7. stellar.py - store/recall/forget에 user_id 파라미터
  8. orbit_manager.py - get_all_items에 user_id
  9. server.py - 엔드포인트에서 user_id 전파

Step 5: Sync (F5)
  10. ws_server.py - Room 기반 격리
  11. ws_client.py - 인증 추가
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-20 | Initial draft | Claude |
