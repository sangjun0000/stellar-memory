# SaaS Multi-Tenancy Planning Document

> **Summary**: PostgreSQL 멀티테넌시 구현 및 백엔드 티어 동기화로 SaaS 제품 수준 달성
>
> **Project**: stellar-memory
> **Version**: v1.0.0 → v1.1.0
> **Author**: Claude
> **Date**: 2026-02-20
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

stellar-memory를 단일 사용자 데모에서 실제 SaaS 제품으로 전환한다. 핵심은 PostgreSQL 기반 멀티테넌시를 구현하여 각 유료 사용자가 독립된 메모리 공간을 가지도록 하는 것이다.

### 1.2 Background

현재 SaaS 준비도: **65/100**

- Auth/Billing/API 인프라는 존재하나, 메모리 저장소가 테넌트 분리되지 않음
- `memories` 테이블에 `user_id` 컬럼 없음 → 모든 사용자가 동일 테이블 공유
- `get_memory_count(user_id)` 함수가 존재하지 않는 컬럼을 참조 → 에러
- 랜딩 페이지 가격(Free $0 / Pro $15 / Pro Max $29)과 백엔드 코드 불일치
- WebSocket Sync가 모든 클라이언트에게 브로드캐스트 (테넌트 격리 없음)

### 1.3 Related Documents

- SaaS 준비도 평가: 이전 세션 결과 (65/100)
- 랜딩 페이지: `landing/index.html` (Free/Pro/Pro Max 3-tier)
- 백엔드 티어: `stellar_memory/billing/tiers.py`

---

## 2. Scope

### 2.1 In Scope

- [ ] F1: PostgreSQL `memories` 테이블에 `user_id` 컬럼 추가 + 마이그레이션
- [ ] F2: API 서버 테넌트 컨텍스트 전파 (인증 → 메모리 연산)
- [ ] F3: 백엔드 티어 코드 동기화 (team → promax, 수치 일치)
- [ ] F4: 메모리 카운팅 수정 (user_id 기반 정상 동작)
- [ ] F5: WebSocket Sync 테넌트 격리

### 2.2 Out of Scope

- Cloud MCP 게이트웨이 (별도 피처로 분리)
- MCP 서버 원격 인증 (별도 피처)
- SSO/SAML 구현 (Pro Max 향후 로드맵)
- 결제 프로바이더 변경 (Lemon Squeezy 유지)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `memories` 테이블에 `user_id UUID` 컬럼 추가, `users.id` FK 연결 | Critical | Pending |
| FR-02 | 모든 PostgreSQL 쿼리에 `WHERE user_id = $N` 필터 추가 | Critical | Pending |
| FR-03 | `MemoryItem` 모델에 `user_id: str` 필드 추가 | Critical | Pending |
| FR-04 | API 미들웨어에서 `request.state.user_id` → StellarMemory 연산에 전달 | Critical | Pending |
| FR-05 | `get_memory_count(user_id)` 정상 동작 (memories 테이블 기준) | High | Pending |
| FR-06 | `TIER_LIMITS` 코드: free 1,000 / pro 50,000 / promax 500,000 | High | Pending |
| FR-07 | `team` → `promax` 네이밍 통일 (tiers.py, _TIER_ORDER 등) | High | Pending |
| FR-08 | Pro Max `max_agents` 20 → Unlimited (-1 또는 999999) | High | Pending |
| FR-09 | WebSocket Sync에 `user_id` 기반 룸/채널 격리 | Medium | Pending |
| FR-10 | PostgreSQL 인덱스: `(user_id, zone)`, `(user_id, total_score)` 추가 | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | user_id 필터 추가 후 쿼리 응답 < 50ms | PostgreSQL EXPLAIN ANALYZE |
| Security | Row-Level Security (RLS) 정책 적용 | PostgreSQL policy 검증 |
| Data Isolation | 타 사용자 메모리 접근 불가 | 교차 접근 테스트 |
| Migration | 기존 데이터 무중단 마이그레이션 | Fly.io 배포 테스트 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] PostgreSQL memories 테이블에 user_id 컬럼 존재
- [ ] 모든 CRUD 쿼리가 user_id 필터 포함
- [ ] API 엔드포인트에서 인증된 사용자의 메모리만 반환
- [ ] 메모리 카운팅이 user_id 기준으로 정상 작동
- [ ] 티어 코드가 랜딩 페이지와 일치 (free/pro/promax)
- [ ] WebSocket Sync가 같은 사용자의 에이전트끼리만 동기화
- [ ] 기존 테스트 통과 + 멀티테넌시 테스트 추가

### 4.2 Quality Criteria

- [ ] 교차 테넌트 접근 테스트 0건 통과
- [ ] PostgreSQL RLS 정책 활성화
- [ ] 마이그레이션 스크립트 롤백 가능

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 기존 memories 데이터에 user_id 없음 | High | High | 마이그레이션 시 default user_id 할당, NULL 허용 후 점진적 적용 |
| 쿼리 성능 저하 (user_id 조건 추가) | Medium | Low | 복합 인덱스 추가 (user_id, zone), (user_id, total_score) |
| StellarMemory 인스턴스 아키텍처 변경 | High | Medium | 기존 싱글 인스턴스 유지, storage layer에서만 user_id 필터 |
| WebSocket Sync 하위 호환성 | Medium | Medium | 로컬 모드(기존)와 클라우드 모드(신규) 분리 |
| 테스트 깨짐 | Medium | High | 기존 테스트는 user_id=None 기본값으로 통과시킨 후 점진 전환 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites, portfolios | |
| **Dynamic** | Feature-based modules, BaaS integration | Web apps with backend, SaaS | **X** |
| **Enterprise** | Strict layer separation, DI, microservices | High-traffic systems | |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 테넌트 격리 방식 | Row-level (user_id) / Schema-per-tenant / DB-per-tenant | **Row-level** | 단일 DB, 비용 효율적, Neon PostgreSQL 호환 |
| StellarMemory 인스턴스 | Per-user instance / Shared + user_id 파라미터 | **Shared + user_id** | 메모리 효율, 기존 아키텍처 최소 변경 |
| 마이그레이션 도구 | Alembic / Raw SQL / Custom script | **Raw SQL** | 단순, 의존성 없음, Neon 호환 |
| 티어 네이밍 | team→promax rename / alias 추가 | **Rename** | 깔끔, 코드 일관성 |
| Sync 격리 | Room-based / Subscription filter / Separate channels | **Room-based** | WebSocket 표준 패턴, 구현 간단 |

### 6.3 변경 대상 파일 목록

```
수정 대상:
├── stellar_memory/
│   ├── models.py                    # MemoryItem에 user_id 추가
│   ├── storage/
│   │   ├── postgres_storage.py      # 스키마 + 모든 쿼리에 user_id
│   │   ├── sqlite_storage.py        # user_id 지원 (선택적)
│   │   └── __init__.py              # Storage 인터페이스에 user_id 파라미터
│   ├── server.py                    # 테넌트 컨텍스트 전파
│   ├── auth.py                      # get_memory_count 수정
│   ├── billing/
│   │   └── tiers.py                 # team→promax, 수치 변경
│   ├── orbit_manager.py             # store/recall에 user_id 전달
│   ├── stellar.py                   # user_id 파라미터 전파
│   └── sync/
│       ├── ws_server.py             # Room-based 격리
│       └── ws_client.py             # user_id 인증 추가
│
신규 파일:
├── migrations/
│   └── 001_add_user_id.sql          # PostgreSQL 마이그레이션
```

---

## 7. Feature Details

### F1: PostgreSQL 멀티테넌시 스키마

**변경 파일**: `stellar_memory/storage/postgres_storage.py`

```sql
-- 마이그레이션: 001_add_user_id.sql
ALTER TABLE memories ADD COLUMN user_id UUID REFERENCES users(id);
CREATE INDEX idx_memories_user_zone ON memories(user_id, zone);
CREATE INDEX idx_memories_user_score ON memories(user_id, total_score DESC);

-- RLS 정책
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY memories_isolation ON memories
    USING (user_id = current_setting('app.current_user_id')::uuid);
```

**MemoryItem 모델 변경** (`models.py`):
```python
@dataclass
class MemoryItem:
    # ... 기존 필드
    user_id: str | None = None  # 신규 - 하위 호환성 위해 Optional
```

### F2: API 테넌트 컨텍스트 전파

**변경 파일**: `stellar_memory/server.py`

현재 `request.state.user_id`는 설정되지만 메모리 연산에 전달되지 않음.

```python
# 변경 전 (line 254-262):
@app.post("/api/v1/store")
async def store(req: StoreRequest):
    item = memory.store(req.content, ...)  # user_id 없음

# 변경 후:
@app.post("/api/v1/store")
async def store(req: StoreRequest, request: Request):
    user_id = getattr(request.state, "user_id", None)
    item = memory.store(req.content, ..., user_id=user_id)
```

모든 엔드포인트(store, recall, forget, search 등)에 동일 패턴 적용.

### F3: 티어 코드 동기화

**변경 파일**: `stellar_memory/billing/tiers.py`

```python
# 변경 전:
"free": {"max_memories": 5_000, "max_agents": 1, ...}
"team": {"max_memories": 500_000, "max_agents": 20, ...}

# 변경 후:
"free": {"max_memories": 1_000, "max_agents": 1, ...}
"promax": {"max_memories": 500_000, "max_agents": -1, ...}  # -1 = unlimited
```

### F4: 메모리 카운팅 수정

**변경 파일**: `stellar_memory/auth.py` (lines 249-262)

```python
# 변경 전: SELECT COUNT(*) FROM memories WHERE user_id = $1
# → memories 테이블에 user_id가 없어서 에러

# 변경 후: F1 마이그레이션 적용 후 동일 쿼리가 정상 동작
```

### F5: WebSocket Sync 테넌트 격리

**변경 파일**: `stellar_memory/sync/ws_server.py`

```python
# 변경 전: 모든 클라이언트에게 브로드캐스트
async def _handler(self, websocket, path):
    self._clients.add(websocket)

# 변경 후: user_id 기반 룸 분리
async def _handler(self, websocket, path):
    user_id = await self._authenticate(websocket)
    self._rooms[user_id].add(websocket)
```

---

## 8. Implementation Order

```
Phase 1 (Critical - 데이터 격리):
  F1 → F3 → F4 → F2

Phase 2 (Enhancement - 실시간):
  F5

구현 순서 상세:
1. F1: models.py + postgres_storage.py + migration SQL
2. F3: tiers.py (team→promax, 수치 변경)
3. F4: auth.py get_memory_count 수정
4. F2: server.py 모든 엔드포인트에 user_id 전파
5. F5: ws_server.py + ws_client.py 룸 기반 격리
```

---

## 9. Next Steps

1. [ ] Write design document (`saas-multitenant.design.md`)
2. [ ] Implementation (5 features)
3. [ ] Gap analysis
4. [ ] Deploy to Fly.io

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-20 | Initial draft | Claude |
