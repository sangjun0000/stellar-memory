# Design: stellar-memory-p2 (Production Readiness & Memory Intelligence)

## 1. Overview

P2는 v0.2.0 시스템을 실제 사용 가능한 수준으로 끌어올리는 5개 기능을 추가합니다.
P1 Gap 2개를 먼저 해결하고, 기억 통합/세션/직렬화 기능을 구현합니다.

**Target Version**: v0.3.0
**New Files**: 3 (consolidator.py, session.py, serializer.py)
**Modified Files**: 7 (stellar.py, config.py, models.py, llm_adapter.py, in_memory.py, sqlite_storage.py, __init__.py)

## 2. Config Extensions

### 2.1 ConsolidationConfig (NEW)

```python
@dataclass
class ConsolidationConfig:
    enabled: bool = True
    similarity_threshold: float = 0.85
    on_store: bool = True          # 저장 시 자동 병합 시도
    on_reorbit: bool = False       # reorbit 시 일괄 병합
    max_content_length: int = 2000 # 병합된 content 최대 길이
```

### 2.2 SessionConfig (NEW)

```python
@dataclass
class SessionConfig:
    enabled: bool = True
    auto_summarize: bool = True    # 세션 종료 시 자동 요약
    summary_max_items: int = 5     # 요약에 포함할 최대 기억 수
    scope_current_first: bool = True  # 현재 세션 기억 우선 recall
```

### 2.3 StellarConfig 확장

```python
@dataclass
class StellarConfig:
    # ... existing fields ...
    consolidation: ConsolidationConfig = field(default_factory=ConsolidationConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
```

## 3. Data Model Extensions

### 3.1 ConsolidationResult (NEW)

```python
@dataclass
class ConsolidationResult:
    merged_count: int = 0         # 병합된 쌍 수
    skipped_count: int = 0        # 유사도 미달 건너뛴 수
    target_id: str = ""           # 병합 대상 (기존 기억) ID
    source_id: str = ""           # 병합 원본 (새 기억) ID
```

### 3.2 SessionInfo (NEW)

```python
@dataclass
class SessionInfo:
    session_id: str
    started_at: float
    ended_at: float | None = None
    memory_count: int = 0
    summary: str | None = None
```

### 3.3 MemorySnapshot (NEW)

```python
@dataclass
class MemorySnapshot:
    timestamp: float
    total_memories: int
    zone_distribution: dict[int, int]   # zone_id -> count
    items: list[dict]                    # serialized MemoryItems
    version: str = "0.3.0"
```

### 3.4 RecallResult (NEW) - recall 메서드 반환값 확장

```python
@dataclass
class RecallResult:
    items: list[MemoryItem]
    result_ids: list[str]         # 피드백용 ID 추적
    query: str
    session_id: str | None = None
```

## 4. F4: WeightTuner Integration

### 4.1 StellarMemory 변경사항

```python
class StellarMemory:
    def __init__(self, config):
        # ... existing ...
        self._tuner = create_tuner(self.config.tuner, self.config.memory_function)
        self._last_recall_ids: list[str] = []  # 마지막 recall 결과 ID 추적

    def recall(self, query, limit=5) -> list[MemoryItem]:
        # ... existing search ...
        self._last_recall_ids = [item.id for item in results]
        return results

    def provide_feedback(self, query: str, used_ids: list[str]) -> None:
        """사용자가 실제로 사용한 기억을 피드백."""
        record = FeedbackRecord(
            query=query,
            result_ids=self._last_recall_ids,
            used_ids=used_ids,
        )
        self._tuner.record_feedback(record)

    def auto_tune(self) -> dict[str, float] | None:
        """피드백 기반 가중치 자동 조정."""
        return self._tuner.tune()
```

### 4.2 MemoryMiddleware 변경사항

```python
class MemoryMiddleware:
    def before_chat(self, user_message):
        memories = self._memory.recall(user_message, limit=self._recall_limit)
        self._last_result_ids = [m.id for m in memories]  # 추적
        # ... build context ...

    def after_chat(self, user_message, assistant_response):
        # auto feedback: 모든 recall 결과를 "사용됨"으로 간주
        if self._last_result_ids:
            self._memory.provide_feedback(user_message, self._last_result_ids)
        # ... auto store ...
```

## 5. F5: Performance Optimization

### 5.1 SqliteStorage Pre-filter + Re-rank

기존: 전체 테이블 스캔 → 시맨틱 비교
변경: 키워드 pre-filter (limit * 5) → 시맨틱 re-rank (limit)

```python
def search(self, query, limit=5, query_embedding=None):
    words = query.lower().split()
    if not words:
        return []
    if query_embedding is not None:
        # Phase 1: Pre-filter by keyword (fetch limit * 5 candidates)
        candidate_limit = limit * 5
        conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in words])
        params = [f"%{w}%" for w in words]
        cur = conn.execute(
            f"SELECT * FROM {self._table} WHERE {conditions} LIMIT ?",
            params + [candidate_limit],
        )
        candidates = [self._row_to_item(row) for row in cur.fetchall()]

        # Phase 1b: 키워드 매칭 없어도 임베딩 있는 최근 아이템 추가
        if len(candidates) < candidate_limit:
            existing_ids = {c.id for c in candidates}
            cur2 = conn.execute(
                f"SELECT * FROM {self._table} WHERE embedding IS NOT NULL "
                f"ORDER BY last_recalled_at DESC LIMIT ?",
                (candidate_limit - len(candidates),),
            )
            for row in cur2.fetchall():
                item = self._row_to_item(row)
                if item.id not in existing_ids:
                    candidates.append(item)

        # Phase 2: Re-rank by hybrid score
        scored = []
        for item in candidates:
            keyword_score = sum(1 for w in words if w in item.content.lower()) / len(words)
            semantic_score = 0.0
            if item.embedding is not None:
                semantic_score = cosine_similarity(query_embedding, item.embedding)
                score = 0.7 * semantic_score + 0.3 * keyword_score
            else:
                score = keyword_score
            if score > 0:
                scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]
    else:
        # ... existing keyword-only search ...
```

### 5.2 Embedding LRU Cache

```python
# stellar.py 또는 embedder.py에 추가
from functools import lru_cache

class Embedder:
    @lru_cache(maxsize=128)
    def _cached_embed(self, text: str) -> tuple[float, ...]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return tuple(vector.tolist())

    def embed(self, text: str) -> list[float]:
        self._ensure_model()
        return list(self._cached_embed(text))
```

NullEmbedder는 캐시 불필요 (항상 None 반환).

## 6. F1: Memory Consolidation

### 6.1 consolidator.py (NEW)

```python
class MemoryConsolidator:
    def __init__(self, config: ConsolidationConfig, embedder):
        self._config = config
        self._embedder = embedder

    def find_similar(self, new_item: MemoryItem,
                     candidates: list[MemoryItem]) -> MemoryItem | None:
        """새 아이템과 유사한 기존 아이템 찾기."""
        if new_item.embedding is None:
            return None
        best_match = None
        best_score = 0.0
        for candidate in candidates:
            if candidate.embedding is None or candidate.id == new_item.id:
                continue
            score = cosine_similarity(new_item.embedding, candidate.embedding)
            if score >= self._config.similarity_threshold and score > best_score:
                best_score = score
                best_match = candidate
        return best_match

    def merge(self, existing: MemoryItem, new_item: MemoryItem) -> MemoryItem:
        """두 기억을 병합. existing을 업데이트하여 반환."""
        # content: 구분자로 합침 (중복 방지)
        if new_item.content not in existing.content:
            merged_content = f"{existing.content}\n---\n{new_item.content}"
            if len(merged_content) <= self._config.max_content_length:
                existing.content = merged_content
        # recall_count: 합산
        existing.recall_count += new_item.recall_count
        # importance: max
        existing.arbitrary_importance = max(
            existing.arbitrary_importance, new_item.arbitrary_importance
        )
        # embedding: 새 content로 재생성
        existing.embedding = self._embedder.embed(existing.content)
        # metadata: 병합 이력 기록
        merge_history = existing.metadata.get("merged_from", [])
        merge_history.append(new_item.id)
        existing.metadata["merged_from"] = merge_history
        existing.metadata["last_merged_at"] = time.time()
        return existing

    def consolidate_zone(self, items: list[MemoryItem]) -> ConsolidationResult:
        """존 내 전체 아이템 일괄 병합."""
        result = ConsolidationResult()
        merged_ids = set()
        for i, item_a in enumerate(items):
            if item_a.id in merged_ids:
                continue
            for item_b in items[i + 1:]:
                if item_b.id in merged_ids:
                    continue
                if (item_a.embedding and item_b.embedding and
                    cosine_similarity(item_a.embedding, item_b.embedding)
                    >= self._config.similarity_threshold):
                    self.merge(item_a, item_b)
                    merged_ids.add(item_b.id)
                    result.merged_count += 1
            result.skipped_count += 1
        return result
```

### 6.2 StellarMemory.store() 변경

```python
def store(self, content, importance=0.5, metadata=None, auto_evaluate=False):
    item = MemoryItem.create(content, importance, metadata)
    # ... evaluate, embed ...

    # Consolidation: 유사 기억 찾아서 병합 시도
    if self._consolidation_cfg.enabled and self._consolidation_cfg.on_store:
        if item.embedding is not None:
            existing = self._find_similar_in_zones(item)
            if existing is not None:
                merged = self._consolidator.merge(existing, item)
                storage = self._orbit_mgr.get_storage(existing.zone)
                storage.update(merged)
                return merged  # 새 아이템 대신 병합된 기존 아이템 반환

    # ... existing place logic ...
```

## 7. F2: Session Context Manager

### 7.1 session.py (NEW)

```python
class SessionManager:
    def __init__(self, config: SessionConfig):
        self._config = config
        self._current_session: SessionInfo | None = None

    @property
    def current_session_id(self) -> str | None:
        return self._current_session.session_id if self._current_session else None

    def start_session(self) -> SessionInfo:
        session_id = str(uuid4())
        self._current_session = SessionInfo(
            session_id=session_id,
            started_at=time.time(),
        )
        return self._current_session

    def end_session(self) -> SessionInfo | None:
        if self._current_session is None:
            return None
        self._current_session.ended_at = time.time()
        ended = self._current_session
        self._current_session = None
        return ended

    def tag_memory(self, item: MemoryItem) -> None:
        """현재 세션 ID를 기억에 태깅."""
        if self._current_session:
            item.metadata["session_id"] = self._current_session.session_id
            self._current_session.memory_count += 1
```

### 7.2 StellarMemory 세션 메서드

```python
class StellarMemory:
    def __init__(self, config):
        # ... existing ...
        self._session_mgr = SessionManager(self.config.session)

    def start_session(self) -> SessionInfo:
        return self._session_mgr.start_session()

    def end_session(self, summarize: bool | None = None) -> SessionInfo | None:
        session = self._session_mgr.end_session()
        if session is None:
            return None
        should_summarize = summarize if summarize is not None else self.config.session.auto_summarize
        if should_summarize:
            session.summary = self._summarize_session(session.session_id)
            # 요약을 새 기억으로 저장
            if session.summary:
                self.store(
                    content=f"[Session Summary] {session.summary}",
                    importance=0.7,
                    metadata={"type": "session_summary", "session_id": session.session_id},
                )
        return session

    def _summarize_session(self, session_id: str) -> str:
        """세션의 기억들을 요약 (상위 N개 content 결합)."""
        items = self._get_session_items(session_id)
        items.sort(key=lambda x: x.arbitrary_importance, reverse=True)
        top = items[:self.config.session.summary_max_items]
        return " | ".join(item.content[:100] for item in top)

    def _get_session_items(self, session_id: str) -> list[MemoryItem]:
        all_items = self._orbit_mgr.get_all_items()
        return [i for i in all_items if i.metadata.get("session_id") == session_id]

    def store(self, content, importance=0.5, metadata=None, auto_evaluate=False):
        item = MemoryItem.create(content, importance, metadata)
        # 세션 태깅
        self._session_mgr.tag_memory(item)
        # ... rest of existing store logic ...
```

### 7.3 recall() 세션 우선 검색

```python
def recall(self, query, limit=5):
    query_embedding = self._embedder.embed(query)
    results = []
    session_id = self._session_mgr.current_session_id

    if session_id and self.config.session.scope_current_first:
        # Phase 1: 현재 세션 기억에서 먼저 검색
        for zone_id in sorted(self._orbit_mgr._zones.keys()):
            storage = self._orbit_mgr.get_storage(zone_id)
            matches = storage.search(query, limit, query_embedding=query_embedding)
            session_matches = [m for m in matches if m.metadata.get("session_id") == session_id]
            results.extend(session_matches)
        # Phase 2: 부족하면 전체에서 보충
        if len(results) < limit:
            remaining = limit - len(results)
            existing_ids = {r.id for r in results}
            for zone_id in sorted(self._orbit_mgr._zones.keys()):
                storage = self._orbit_mgr.get_storage(zone_id)
                matches = storage.search(query, remaining, query_embedding=query_embedding)
                for m in matches:
                    if m.id not in existing_ids:
                        results.append(m)
                        existing_ids.add(m.id)
                        if len(results) >= limit:
                            break
    else:
        # 기존 로직 유지
        for zone_id in sorted(self._orbit_mgr._zones.keys()):
            if len(results) >= limit:
                break
            storage = self._orbit_mgr.get_storage(zone_id)
            matches = storage.search(query, limit - len(results), query_embedding=query_embedding)
            results.extend(matches)

    # ... update recall counts ...
    self._last_recall_ids = [item.id for item in results]
    return results[:limit]
```

### 7.4 MemoryMiddleware 세션 통합

```python
class MemoryMiddleware:
    def __init__(self, memory, recall_limit=5, auto_store=True, auto_evaluate=True):
        # ... existing ...
        self._last_result_ids: list[str] = []

    def start_session(self) -> SessionInfo:
        return self._memory.start_session()

    def end_session(self) -> SessionInfo | None:
        return self._memory.end_session()

    def after_chat(self, user_message, assistant_response):
        # 피드백 (middleware 수준에서는 모든 결과를 사용으로 간주)
        if self._last_result_ids:
            self._memory.provide_feedback(user_message, self._last_result_ids)
        # ... existing auto_store ...
```

## 8. F3: Export/Import & Snapshot

### 8.1 serializer.py (NEW)

```python
import base64
import json
import time

class MemorySerializer:
    def __init__(self, embedder_dim: int = 384):
        self._dim = embedder_dim

    def export_json(self, items: list[MemoryItem],
                    include_embeddings: bool = True) -> str:
        """전체 기억을 JSON 문자열로 직렬화."""
        data = {
            "version": "0.3.0",
            "exported_at": time.time(),
            "count": len(items),
            "items": [self._item_to_dict(item, include_embeddings) for item in items],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def import_json(self, json_str: str) -> list[MemoryItem]:
        """JSON 문자열에서 기억 목록 복원."""
        data = json.loads(json_str)
        return [self._dict_to_item(d) for d in data["items"]]

    def _item_to_dict(self, item: MemoryItem, include_embedding: bool) -> dict:
        d = {
            "id": item.id,
            "content": item.content,
            "created_at": item.created_at,
            "last_recalled_at": item.last_recalled_at,
            "recall_count": item.recall_count,
            "arbitrary_importance": item.arbitrary_importance,
            "zone": item.zone,
            "metadata": item.metadata,
            "total_score": item.total_score,
        }
        if include_embedding and item.embedding is not None:
            blob = serialize_embedding(item.embedding)
            d["embedding_b64"] = base64.b64encode(blob).decode("ascii")
        return d

    def _dict_to_item(self, d: dict) -> MemoryItem:
        embedding = None
        if "embedding_b64" in d:
            blob = base64.b64decode(d["embedding_b64"])
            embedding = deserialize_embedding(blob, dim=self._dim)
        return MemoryItem(
            id=d["id"],
            content=d["content"],
            created_at=d["created_at"],
            last_recalled_at=d["last_recalled_at"],
            recall_count=d.get("recall_count", 0),
            arbitrary_importance=d.get("arbitrary_importance", 0.5),
            zone=d.get("zone", -1),
            metadata=d.get("metadata", {}),
            embedding=embedding,
            total_score=d.get("total_score", 0.0),
        )

    def snapshot(self, items: list[MemoryItem]) -> MemorySnapshot:
        """현재 시점 스냅샷 생성."""
        zone_dist: dict[int, int] = {}
        for item in items:
            zone_dist[item.zone] = zone_dist.get(item.zone, 0) + 1
        return MemorySnapshot(
            timestamp=time.time(),
            total_memories=len(items),
            zone_distribution=zone_dist,
            items=[self._item_to_dict(item, include_embedding=True) for item in items],
        )
```

### 8.2 StellarMemory 직렬화 메서드

```python
class StellarMemory:
    def export_json(self, include_embeddings: bool = True) -> str:
        items = self._orbit_mgr.get_all_items()
        serializer = MemorySerializer(self.config.embedder.dimension)
        return serializer.export_json(items, include_embeddings)

    def import_json(self, json_str: str) -> int:
        serializer = MemorySerializer(self.config.embedder.dimension)
        items = serializer.import_json(json_str)
        for item in items:
            # 기존 zone 정보가 있으면 해당 zone에 직접 배치
            if item.zone >= 0:
                self._orbit_mgr.place(item, item.zone, item.total_score)
            else:
                breakdown = self._memory_fn.calculate(item, time.time())
                self._orbit_mgr.place(item, breakdown.target_zone, breakdown.total)
        return len(items)

    def snapshot(self) -> MemorySnapshot:
        items = self._orbit_mgr.get_all_items()
        serializer = MemorySerializer(self.config.embedder.dimension)
        return serializer.snapshot(items)
```

## 9. Implementation Order

```
Step 1: Config extensions (ConsolidationConfig, SessionConfig + StellarConfig 확장)
Step 2: Model extensions (ConsolidationResult, SessionInfo, MemorySnapshot, RecallResult)
Step 3: F4 - WeightTuner integration (stellar.py: provide_feedback, auto_tune, _last_recall_ids)
Step 4: F4 - MemoryMiddleware feedback (llm_adapter.py: _last_result_ids, auto feedback)
Step 5: F5 - SqliteStorage pre-filter re-rank (sqlite_storage.py)
Step 6: F5 - Embedder LRU cache (embedder.py)
Step 7: F1 - consolidator.py (MemoryConsolidator: find_similar, merge, consolidate_zone)
Step 8: F1 - StellarMemory consolidation integration (store에 병합 로직)
Step 9: F2 - session.py (SessionManager: start/end/tag)
Step 10: F2 - StellarMemory session integration (start_session, end_session, session recall)
Step 11: F2 - MemoryMiddleware session passthrough
Step 12: F3 - serializer.py (MemorySerializer: export/import/snapshot)
Step 13: F3 - StellarMemory serialization methods
Step 14: __init__.py exports + pyproject.toml version bump
Step 15: Tests (5 new test files)
```

## 10. Test Design

### 10.1 test_tuner_integration.py (8 tests)
- provide_feedback 기록 확인
- auto_tune 충분한 피드백 후 동작
- auto_tune 부족한 피드백 시 None
- recall 시 _last_recall_ids 추적
- MemoryMiddleware auto feedback

### 10.2 test_performance.py (8 tests)
- SqliteStorage pre-filter 결과 일관성 (vs 전체 스캔)
- pre-filter 후보 부족 시 최근 아이템 보충
- Embedder LRU 캐시 히트 확인
- 키워드 전용 검색 하위 호환

### 10.3 test_consolidation.py (10 tests)
- 유사 기억 찾기 (threshold 이상)
- 유사하지 않은 기억 건너뛰기 (threshold 미만)
- merge: content 합침, recall_count 합산, importance max
- merge: max_content_length 초과 시 content 미합침
- store 시 자동 병합
- 이미 같은 content는 중복 합치지 않음
- consolidate_zone 일괄 병합
- 임베딩 없는 아이템 건너뛰기
- disabled 시 병합 안 함
- merge 이력 metadata 기록

### 10.4 test_session.py (10 tests)
- start_session 생성 확인
- end_session 종료 확인
- tag_memory 세션 ID 추가
- 세션 없을 때 tag 건너뛰기
- 세션 우선 recall (현재 세션 아이템 우선)
- 세션 외 아이템 fallback
- end_session 시 auto_summarize
- 세션 요약 기억 저장
- MemoryMiddleware session passthrough
- disabled 시 세션 기능 비활성

### 10.5 test_serializer.py (10 tests)
- export_json 직렬화 확인
- import_json 역직렬화 확인
- export -> import 라운드트립 데이터 무결성
- 임베딩 base64 인코딩/디코딩
- include_embeddings=False 시 임베딩 제외
- snapshot zone 분포 정확성
- 빈 목록 export/import
- import 시 zone 정보 보존
- import 시 zone=-1이면 재계산
- version 필드 확인

## 11. File Structure (v0.3.0)

```
stellar_memory/
├── __init__.py              # P2 type exports 추가
├── config.py                # + ConsolidationConfig, SessionConfig
├── models.py                # + ConsolidationResult, SessionInfo, MemorySnapshot
├── stellar.py               # + tuner/session/consolidation/serialization 통합
├── memory_function.py       # (변경 없음)
├── orbit_manager.py         # (변경 없음)
├── scheduler.py             # (변경 없음)
├── embedder.py              # + LRU cache
├── importance_evaluator.py  # (변경 없음)
├── weight_tuner.py          # (변경 없음)
├── llm_adapter.py           # + feedback, session passthrough
├── utils.py                 # (변경 없음)
├── consolidator.py          # NEW - 기억 통합
├── session.py               # NEW - 세션 관리
├── serializer.py            # NEW - 직렬화
└── storage/
    ├── __init__.py           # (변경 없음)
    ├── in_memory.py          # (변경 없음 - 이미 hybrid search)
    └── sqlite_storage.py     # + pre-filter re-rank

tests/
├── (기존 10개 유지)
├── test_tuner_integration.py  # NEW
├── test_performance.py        # NEW
├── test_consolidation.py      # NEW
├── test_session.py            # NEW
└── test_serializer.py         # NEW
```

## 12. Error Handling

| Scenario | Handling |
|----------|----------|
| Consolidation: 임베딩 없는 아이템 | 건너뛰기 (NullEmbedder 환경) |
| Session: 세션 없이 end_session 호출 | None 반환 |
| Import: 잘못된 JSON | json.JSONDecodeError raise |
| Import: 버전 불일치 | 로그 경고 후 best-effort 임포트 |
| Pre-filter: 후보 0건 | 빈 리스트 반환 (기존 동작) |
| LRU cache: 메모리 | maxsize=128 (약 200KB for 384-dim) |

## 13. Backward Compatibility

- 모든 새 기능은 config로 on/off 가능 (default: enabled)
- 기존 99개 테스트 변경 없이 통과해야 함
- store() 시그니처: auto_evaluate 파라미터 유지, 새 파라미터 없음
- recall() 반환 타입: 기존 `list[MemoryItem]` 유지 (RecallResult는 내부용)
- consolidation on_store=True가 기존 동작을 변경하지만, NullEmbedder 환경에서는 임베딩이 None이므로 병합 시도 안 함
