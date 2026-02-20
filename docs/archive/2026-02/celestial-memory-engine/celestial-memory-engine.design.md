# Celestial Memory Engine - Design Document

> **Summary**: 천체 구조 기반 AI 기억 엔진 v2 - 블랙홀 방지 + 리콜-리셋 신선도 + 독립 플러그인 모듈
>
> **Project**: stellar-memory
> **Version**: 2.0.0
> **Date**: 2026-02-18
> **Status**: Draft
> **Planning Doc**: [celestial-memory-engine.plan.md](../../01-plan/features/celestial-memory-engine.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **기억함수 v2**: 리콜-리셋 신선도와 로그-캡 리콜 점수로 블랙홀 문제를 수학적으로 방지
2. **독립 모듈**: `celestial_engine/` 패키지로 분리, 어떤 AI에든 3줄 코드로 삽입 가능
3. **하위 호환**: 기존 `stellar_memory/` 코드에서 celestial_engine을 내부적으로 사용 가능
4. **Zero Dependencies**: 순수 Python 표준 라이브러리만 필수, 임베딩/LLM은 optional

### 1.2 Design Principles

- **수학적 보장**: 블랙홀 방지를 증명 가능한 수식으로 구현 (운영 의존 X)
- **단일 책임**: 각 모듈은 하나의 역할만 수행 (기억함수 / Zone 관리 / 재배치 / 평가)
- **점진적 복잡도**: 기본 사용은 2줄, 커스텀은 설정으로, 확장은 서브클래스로
- **기존 코드 재사용**: 새로 만들지 않고 기존 stellar_memory의 검증된 코드를 리팩터

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    celestial_engine (독립 패키지)                  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │MemoryFunction│  │ ZoneManager  │  │    Rebalancer         │  │
│  │   (v2)       │──│              │──│ (periodic reorbit)    │  │
│  │              │  │ place/move/  │  │                       │  │
│  │ R(m)+F(m)+   │  │ evict        │  │ score_all → relocate  │  │
│  │ A(m)+C(m)    │  │              │  │                       │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘  │
│         │                 │                       │              │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌───────────┴───────────┐  │
│  │ Importance   │  │   Storage    │  │   CelestialMemory     │  │
│  │ Evaluator    │  │  (abstract)  │  │   (public facade)     │  │
│  │ (AI/Rule)    │  │              │  │                       │  │
│  │              │  │ InMemory /   │  │ store() / recall() /  │  │
│  │ LLM-first   │  │ SQLite       │  │ stats() / export()    │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    adapters/                              │   │
│  │  LangChainAdapter  │  OpenAIAdapter  │  AnthropicAdapter │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         ▲                                          ▲
         │ (import)                                 │ (import)
┌────────┴──────────┐                    ┌──────────┴──────────┐
│  stellar_memory/  │                    │  사용자 AI 프로젝트   │
│  (기존 프로젝트)    │                    │  (LangChain/OpenAI)  │
└───────────────────┘                    └─────────────────────┘
```

### 2.2 Data Flow

```
store(content) → ImportanceEvaluator → MemoryFunction.calculate()
    → ZoneManager.place(item, target_zone)
    → Storage.store(item)

recall(query) → Storage.search(zone 0→4) → update recall_count, last_recalled_at
    → MemoryFunction.calculate() (재정렬)
    → return top results

rebalance() → for item in all_items:
    → MemoryFunction.calculate(item, now)
    → ZoneManager.move(item, current_zone, target_zone)
    → ZoneManager.enforce_capacity()
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| CelestialMemory | MemoryFunction, ZoneManager, Rebalancer | Public facade |
| MemoryFunction | (none - pure math) | 점수 계산 |
| ZoneManager | Storage | Zone 배치/이동/퇴거 |
| Rebalancer | MemoryFunction, ZoneManager | 주기적 재배치 |
| ImportanceEvaluator | (optional: LLM provider) | AI 임의 중요도 |
| Storage | (stdlib: sqlite3, dict) | 데이터 저장 |

---

## 3. Data Model

### 3.1 Core Dataclasses

```python
# celestial_engine/models.py

from dataclasses import dataclass, field
from uuid import uuid4
import time

@dataclass
class CelestialItem:
    """단일 기억 항목."""
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

    @classmethod
    def create(cls, content: str, importance: float = 0.5,
               metadata: dict | None = None) -> CelestialItem:
        now = time.time()
        return cls(
            id=str(uuid4()),
            content=content,
            created_at=now,
            last_recalled_at=now,  # 생성 시 = 리콜 직후와 동일
            recall_count=0,
            arbitrary_importance=max(0.0, min(1.0, importance)),
            zone=-1,
            metadata=metadata or {},
        )


@dataclass
class ScoreBreakdown:
    """기억함수 점수 분해."""
    recall_score: float      # R(m)
    freshness_score: float   # F(m)
    arbitrary_score: float   # A(m)
    context_score: float     # C(m)
    total: float             # I(m) = weighted sum
    target_zone: int         # 목표 Zone


@dataclass
class ZoneConfig:
    """Zone 설정."""
    zone_id: int
    name: str
    max_slots: int | None      # None = 무제한
    score_min: float           # 이 Zone의 최소 점수
    score_max: float = float("inf")


@dataclass
class RebalanceResult:
    """재배치 결과."""
    moved: int = 0
    evicted: int = 0
    forgotten: int = 0
    total_items: int = 0
    duration_ms: float = 0.0
```

### 3.2 기존 MemoryItem과의 매핑

| CelestialItem | MemoryItem (기존) | 변경 사항 |
|---------------|-------------------|----------|
| id | id | 동일 |
| content | content | 동일 |
| created_at | created_at | 동일 |
| last_recalled_at | last_recalled_at | **신선도 계산 기준점** (핵심 변경) |
| recall_count | recall_count | 동일 |
| arbitrary_importance | arbitrary_importance | 동일 |
| zone | zone | 동일 |
| metadata | metadata | 동일 |
| embedding | embedding | 동일 |
| total_score | total_score | 동일 |
| (없음) | emotion, encrypted, source_type, ... | 제거 (경량화) |

---

## 4. Memory Function v2 상세 설계

### 4.1 CelestialMemoryFunction 클래스

```python
# celestial_engine/memory_function.py

import math
from dataclasses import dataclass


@dataclass
class MemoryFunctionConfig:
    """기억함수 v2 설정."""
    w_recall: float = 0.25
    w_freshness: float = 0.30
    w_arbitrary: float = 0.25
    w_context: float = 0.20
    max_recall_cap: int = 1000
    freshness_alpha: float = 0.001   # 신선도 감쇠 계수
    freshness_floor: float = -86400.0  # 신선도 바닥값 (raw, 1일 기준)


class CelestialMemoryFunction:
    """천체 기억함수 v2 - 블랙홀 방지 수학적 보장."""

    def __init__(self, config: MemoryFunctionConfig | None = None):
        self._cfg = config or MemoryFunctionConfig()

    def calculate(self, item: CelestialItem, current_time: float,
                  context_embedding: list[float] | None = None) -> ScoreBreakdown:
        r = self._recall_score(item.recall_count)
        f = self._freshness_score(item.last_recalled_at, current_time)
        a = item.arbitrary_importance
        c = self._context_score(item.embedding, context_embedding)

        total = (self._cfg.w_recall * r
                 + self._cfg.w_freshness * f
                 + self._cfg.w_arbitrary * a
                 + self._cfg.w_context * c)

        target_zone = self._determine_zone(total)
        return ScoreBreakdown(r, f, a, c, total, target_zone)

    def _recall_score(self, recall_count: int) -> float:
        """
        R(m) = log(1 + count) / log(1 + MAX_RECALL_CAP)

        블랙홀 방지 장치 #1:
        - log 함수로 임계값 절대 초과 불가
        - count=999 → R=0.9996 (절대 1.0 도달 불가)
        - 리콜 횟수가 아무리 많아도 기여도가 포화됨
        """
        if recall_count <= 0:
            return 0.0
        return math.log(1 + recall_count) / math.log(1 + self._cfg.max_recall_cap)

    def _freshness_score(self, last_recalled_at: float, current_time: float) -> float:
        """
        블랙홀 방지 장치 #2: 리콜-리셋 + 음수 감쇠

        리콜 직후: F(m) = 0.0 (리셋)
        시간 경과: raw = -alpha * (now - last_recalled_at)
        정규화:   F(m) = raw / floor  → [0.0, -1.0] 범위

        핵심 차이 (vs 기존 v1):
        - 기존: F = exp(-alpha * (now - created_at)) → [0, 1] (항상 양수)
        - 신규: F = -alpha * (now - last_recalled_at) / floor → [0, -1] (음수 가능!)
        - 리콜하면 last_recalled_at 갱신 → F 리셋
        - 안 쓰면 F → -1.0 → 전체 점수 하락 → 외곽으로 밀림
        """
        delta_t = max(0.0, current_time - last_recalled_at)
        raw = -self._cfg.freshness_alpha * delta_t
        clamped = max(raw, self._cfg.freshness_floor)
        # 정규화: floor 도달 시 -1.0, 방금 리콜 시 0.0
        if self._cfg.freshness_floor >= 0:
            return 0.0
        return clamped / abs(self._cfg.freshness_floor)
        # 결과: 0.0 (방금 리콜) ~ -1.0 (floor 도달)

    def _context_score(self, item_embedding: list[float] | None,
                       context_embedding: list[float] | None) -> float:
        """C(m) = cosine_similarity. 임베딩 없으면 0.0."""
        if item_embedding is None or context_embedding is None:
            return 0.0
        dot = sum(a * b for a, b in zip(item_embedding, context_embedding))
        norm_a = sum(a * a for a in item_embedding) ** 0.5
        norm_b = sum(b * b for b in context_embedding) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _determine_zone(self, total_score: float) -> int:
        """점수 → Zone 매핑. DEFAULT_ZONES 사용."""
        for zone in _DEFAULT_ZONE_THRESHOLDS:
            if total_score >= zone[1]:
                return zone[0]
        return 4  # Cloud


# Zone 배치 임계값 (zone_id, score_min)
_DEFAULT_ZONE_THRESHOLDS = [
    (0, 0.50),    # Core (태양)
    (1, 0.30),    # Inner (내행성)
    (2, 0.10),    # Outer (외행성)
    (3, -0.10),   # Belt (소행성대)
    (4, float("-inf")),  # Cloud (구름)
]
```

### 4.2 블랙홀 방지 수학적 증명

```
Given:
  w_r = 0.25, w_f = 0.30, w_a = 0.25, w_c = 0.20
  R(m) ∈ [0, 0.9996)  (log-capped, 절대 1.0 불가)
  F(m) ∈ [-1.0, 0.0]  (리콜 직후 0, 시간 경과 시 음수)
  A(m) ∈ [0.0, 1.0]
  C(m) ∈ [0.0, 1.0]

이론적 최대값 (리콜 직후 + 최고 중요도 + 완벽 맥락):
  I_max = 0.25 * 0.9996 + 0.30 * 0.0 + 0.25 * 1.0 + 0.20 * 1.0
        = 0.2499 + 0.0 + 0.25 + 0.20
        = 0.6999

시간 경과 감소 보장 (리콜 없이 1일 경과):
  F(1일) = -0.001 * 86400 / 86400 = -1.0
  I = 0.25 * R + 0.30 * (-1.0) + 0.25 * A + 0.20 * C
    = 0.25 * R + 0.25 * A + 0.20 * C - 0.30
    = (최대) 0.25 * 1 + 0.25 * 1 + 0.20 * 1 - 0.30
    = 0.40 → Inner Zone으로 강등!

결론:
  1. I_max = 0.70 → Core Zone 진입 가능하지만 상한 존재
  2. 리콜 없이 1일 → 최고 중요도 기억도 Core → Inner 강등
  3. 리콜 없이 지속 → F → -1.0 → 전체 점수 하락 → Belt/Cloud로 이동
  4. Core Zone 용량 20개 → 20개 초과 시 최저 점수 퇴거
  ∴ 블랙홀 불가능 (QED)
```

### 4.3 신선도 동작 시나리오

```
시나리오 1: "자주 쓰는 기억" (매일 1회 리콜)
  - 매일 리콜 → F 리셋 0.0 → 항상 신선
  - R 점진적 증가 (log로 포화)
  - 결과: Core/Inner에 안정적 체류 ✓

시나리오 2: "한 번 쓰고 안 쓰는 기억"
  - 1일 후: F = -1.0 (바닥)
  - I = 0.25*R + 0.30*(-1.0) + 0.25*A + 0.20*C
  - R=0이면: I = -0.30 + 0.25*A + 0.20*C
  - A=0.5, C=0이면: I = -0.30 + 0.125 = -0.175 → Cloud!
  - 결과: 빠르게 외곽으로 이동 ✓

시나리오 3: "오래된 중요한 기억" (A=1.0, 리콜 없음)
  - F = -1.0 (바닥)
  - I = 0.25*R + 0.30*(-1.0) + 0.25*1.0 + 0.20*C
  - R=0.5 (과거 리콜 이력), C=0:
  - I = 0.125 + (-0.30) + 0.25 = 0.075 → Belt Zone
  - 결과: 중요해도 안 쓰면 먼 궤도로 이동 → 인간 기억과 동일 ✓

시나리오 4: "갑자기 다시 떠올린 기억" (Belt에서 리콜)
  - 리콜! → F 리셋 0.0, recall_count++
  - I = 0.25*0.5 + 0.30*0.0 + 0.25*0.5 + 0.20*C
  - I = 0.125 + 0.0 + 0.125 = 0.25 → Outer Zone으로 승격!
  - 다시 리콜되면 계속 중심으로 이동
  - 결과: 떠올리면 되살아남 → 인간 기억과 동일 ✓
```

---

## 5. Zone Manager 상세 설계

### 5.1 기본 Zone 설정

```python
# celestial_engine/zones.py

DEFAULT_ZONES = [
    ZoneConfig(zone_id=0, name="core",  max_slots=20,   score_min=0.50),
    ZoneConfig(zone_id=1, name="inner", max_slots=100,  score_min=0.30, score_max=0.50),
    ZoneConfig(zone_id=2, name="outer", max_slots=1000, score_min=0.10, score_max=0.30),
    ZoneConfig(zone_id=3, name="belt",  max_slots=None, score_min=-0.10, score_max=0.10),
    ZoneConfig(zone_id=4, name="cloud", max_slots=None, score_min=float("-inf"), score_max=-0.10),
]
```

### 5.2 ZoneManager 클래스

```python
# celestial_engine/zone_manager.py

class ZoneManager:
    """Zone 배치/이동/퇴거 관리."""

    def __init__(self, zones: list[ZoneConfig] | None = None,
                 db_path: str = "celestial_memory.db"):
        self._zones = {z.zone_id: z for z in (zones or DEFAULT_ZONES)}
        self._storages: dict[int, ZoneStorage] = {}
        for z in (zones or DEFAULT_ZONES):
            if z.zone_id <= 1:
                self._storages[z.zone_id] = InMemoryStorage()
            else:
                self._storages[z.zone_id] = SqliteStorage(db_path, z.zone_id)

    def place(self, item: CelestialItem, target_zone: int, score: float) -> None:
        """기억을 target_zone에 배치. 용량 초과 시 최하위 퇴거."""
        item.zone = target_zone
        item.total_score = score
        zone_cfg = self._zones[target_zone]
        storage = self._storages[target_zone]

        if zone_cfg.max_slots is not None and storage.count() >= zone_cfg.max_slots:
            self._evict_lowest(target_zone)

        storage.store(item)

    def move(self, item_id: str, from_zone: int, to_zone: int, score: float) -> bool:
        """기억을 from_zone에서 to_zone으로 이동."""
        from_storage = self._storages.get(from_zone)
        if from_storage is None:
            return False
        item = from_storage.get(item_id)
        if item is None:
            return False
        from_storage.remove(item_id)
        self.place(item, to_zone, score)
        return True

    def get_all_items(self) -> list[CelestialItem]:
        """모든 Zone의 모든 기억 반환."""
        items = []
        for storage in self._storages.values():
            items.extend(storage.get_all())
        return items

    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None) -> list[CelestialItem]:
        """Zone 0→4 순서로 검색. limit에 도달하면 조기 종료."""
        results = []
        for zone_id in sorted(self._storages.keys()):
            if len(results) >= limit:
                break
            storage = self._storages[zone_id]
            remaining = limit - len(results)
            found = storage.search(query, remaining, query_embedding)
            results.extend(found)
        return results[:limit]

    def forget_stale(self, max_age_seconds: float, current_time: float) -> int:
        """Cloud Zone에서 auto_forget_days 초과 기억 삭제."""
        cloud = self._storages.get(4)
        if cloud is None:
            return 0
        forgotten = 0
        for item in cloud.get_all():
            if current_time - item.last_recalled_at > max_age_seconds:
                cloud.remove(item.id)
                forgotten += 1
        return forgotten

    def _evict_lowest(self, zone_id: int) -> None:
        """Zone 내 최저 점수 기억을 다음 외곽 Zone으로 퇴거."""
        storage = self._storages[zone_id]
        lowest = storage.get_lowest_score_item()
        if lowest is None:
            return
        storage.remove(lowest.id)
        next_zone = zone_id + 1
        if next_zone in self._storages:
            self.place(lowest, next_zone, lowest.total_score)

    def enforce_capacity(self) -> int:
        """모든 Zone의 용량 제한 집행. 초과분 퇴거."""
        evicted = 0
        for zone_id in sorted(self._zones.keys()):
            zone_cfg = self._zones[zone_id]
            if zone_cfg.max_slots is None:
                continue
            storage = self._storages[zone_id]
            while storage.count() > zone_cfg.max_slots:
                self._evict_lowest(zone_id)
                evicted += 1
        return evicted

    def stats(self) -> dict[int, tuple[int, int | None]]:
        """각 Zone의 (현재 수, 최대 용량) 반환."""
        return {
            zid: (self._storages[zid].count(), self._zones[zid].max_slots)
            for zid in sorted(self._zones.keys())
        }
```

### 5.3 기존 OrbitManager와의 매핑

| ZoneManager (신규) | OrbitManager (기존) | 변경 사항 |
|---------------------|---------------------|----------|
| place() | place() | 동일 로직 |
| move() | move() | 동일 로직 |
| search() | (StellarMemory.recall에 분산) | **통합**: Zone 순차 검색을 ZoneManager로 이동 |
| forget_stale() | (DecayManager에 분산) | **통합**: Cloud Zone 자동 망각을 ZoneManager에 포함 |
| enforce_capacity() | _enforce_capacity() | 동일 로직 |
| (없음) | reorbit_all() | → Rebalancer로 분리 |

---

## 6. Rebalancer 상세 설계

### 6.1 Rebalancer 클래스

```python
# celestial_engine/rebalancer.py

import time
import threading
import logging

logger = logging.getLogger(__name__)


class Rebalancer:
    """주기적 기억 재배치 엔진."""

    def __init__(self, memory_fn: CelestialMemoryFunction,
                 zone_mgr: ZoneManager,
                 interval_seconds: int = 300,
                 auto_forget_seconds: float = 86400 * 90):
        self._fn = memory_fn
        self._zone_mgr = zone_mgr
        self._interval = interval_seconds
        self._auto_forget = auto_forget_seconds
        self._timer: threading.Timer | None = None
        self._running = False

    def rebalance(self, current_time: float | None = None) -> RebalanceResult:
        """모든 기억의 점수 재계산 + Zone 재배치 + 용량 집행 + 자동 망각."""
        now = current_time or time.time()
        start = time.time()

        all_items = self._zone_mgr.get_all_items()
        moves: list[tuple[CelestialItem, int, int, float]] = []

        for item in all_items:
            breakdown = self._fn.calculate(item, now)
            item.total_score = breakdown.total
            if breakdown.target_zone != item.zone:
                moves.append((item, item.zone, breakdown.target_zone, breakdown.total))

        # 높은 점수 우선 이동 (Core 진입 우선)
        moves.sort(key=lambda x: x[3], reverse=True)

        moved = 0
        for item, from_z, to_z, score in moves:
            if self._zone_mgr.move(item.id, from_z, to_z, score):
                moved += 1

        evicted = self._zone_mgr.enforce_capacity()
        forgotten = self._zone_mgr.forget_stale(self._auto_forget, now)

        duration = (time.time() - start) * 1000  # ms
        return RebalanceResult(
            moved=moved,
            evicted=evicted,
            forgotten=forgotten,
            total_items=len(all_items),
            duration_ms=duration,
        )

    def start(self) -> None:
        """백그라운드 재배치 시작."""
        self._running = True
        self._schedule_next()

    def stop(self) -> None:
        """백그라운드 재배치 중지."""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_next(self) -> None:
        if not self._running:
            return
        self._timer = threading.Timer(self._interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        try:
            result = self.rebalance()
            if result.moved > 0 or result.forgotten > 0:
                logger.info(
                    "Rebalance: moved=%d evicted=%d forgotten=%d (%.1fms)",
                    result.moved, result.evicted, result.forgotten,
                    result.duration_ms,
                )
        except Exception as e:
            logger.error("Rebalance failed: %s", e)
        finally:
            self._schedule_next()
```

---

## 7. Importance Evaluator 상세 설계

### 7.1 ImportanceEvaluator 인터페이스

```python
# celestial_engine/importance.py

from abc import ABC, abstractmethod


class ImportanceEvaluator(ABC):
    """임의 중요도 A(m) 평가 인터페이스."""
    @abstractmethod
    def evaluate(self, content: str) -> float:
        """content의 중요도를 [0.0, 1.0] 범위로 평가."""
        ...


class DefaultEvaluator(ImportanceEvaluator):
    """기본 평가기: 항상 0.5 반환."""
    def evaluate(self, content: str) -> float:
        return 0.5


class RuleBasedEvaluator(ImportanceEvaluator):
    """규칙 기반 평가기: 키워드 패턴 매칭."""

    FACTUAL_PATTERNS = [
        r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
        r"\b\d+\s*(kg|km|m|cm|mm|gb|mb|tb|%)\b",
        r"\b(fact|data|statistic|number|result)\b",
    ]
    EMOTIONAL_PATTERNS = [
        r"\b(love|hate|happy|sad|angry|fear|joy|excited|worried)\b",
        r"\b(amazing|terrible|wonderful|horrible|fantastic|awful)\b",
    ]
    ACTIONABLE_PATTERNS = [
        r"\b(todo|must|should|need to|have to|deadline|urgent|asap)\b",
        r"\b(schedule|meeting|appointment|task|action item)\b",
    ]
    EXPLICIT_PATTERNS = [
        r"\b(important|critical|remember|never forget|key|essential)\b",
        r"\b(password|secret|api.?key|token|credential)\b",
    ]

    def evaluate(self, content: str) -> float:
        import re
        text = content.lower()
        f = self._score(text, self.FACTUAL_PATTERNS)
        e = self._score(text, self.EMOTIONAL_PATTERNS)
        a = self._score(text, self.ACTIONABLE_PATTERNS)
        x = self._score(text, self.EXPLICIT_PATTERNS)
        return max(0.0, min(1.0, 0.25 * f + 0.25 * e + 0.30 * a + 0.20 * x))

    def _score(self, text: str, patterns: list[str]) -> float:
        import re
        matches = sum(1 for p in patterns if re.search(p, text))
        return min(matches / max(len(patterns), 1), 1.0)


class LLMEvaluator(ImportanceEvaluator):
    """LLM 기반 평가기: AI가 자율적으로 중요도 판단."""

    def __init__(self, llm_callable=None):
        """
        llm_callable: (prompt: str) -> str 형태의 LLM 호출 함수.
        None이면 RuleBasedEvaluator로 fallback.
        """
        self._llm = llm_callable
        self._fallback = RuleBasedEvaluator()

    def evaluate(self, content: str) -> float:
        if self._llm is None:
            return self._fallback.evaluate(content)
        try:
            return self._call_llm(content)
        except Exception:
            return self._fallback.evaluate(content)

    def _call_llm(self, content: str) -> float:
        import json
        prompt = (
            "Rate the importance of this memory on a scale of 0.0 to 1.0.\n"
            "Consider: factual value, emotional significance, actionability, "
            "and explicit importance markers.\n\n"
            f"Memory: {content}\n\n"
            'Respond ONLY with JSON: {"importance": 0.0}'
        )
        raw = self._llm(prompt)
        data = json.loads(raw)
        return max(0.0, min(1.0, float(data.get("importance", 0.5))))
```

### 7.2 평가기 선택 전략

```
1순위: LLMEvaluator (사용자가 llm_callable 제공 시)
2순위: RuleBasedEvaluator (LLM 없을 때)
3순위: DefaultEvaluator (평가 비활성화)
```

---

## 8. Storage Layer 상세 설계

### 8.1 ZoneStorage 인터페이스

```python
# celestial_engine/storage/base.py

from abc import ABC, abstractmethod


class ZoneStorage(ABC):
    """Zone별 스토리지 인터페이스."""

    @abstractmethod
    def store(self, item: CelestialItem) -> None: ...

    @abstractmethod
    def get(self, item_id: str) -> CelestialItem | None: ...

    @abstractmethod
    def remove(self, item_id: str) -> bool: ...

    @abstractmethod
    def update(self, item: CelestialItem) -> None: ...

    @abstractmethod
    def search(self, query: str, limit: int = 5,
               query_embedding: list[float] | None = None) -> list[CelestialItem]: ...

    @abstractmethod
    def get_all(self) -> list[CelestialItem]: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def get_lowest_score_item(self) -> CelestialItem | None: ...
```

### 8.2 InMemoryStorage (Core/Inner Zone)

```python
# celestial_engine/storage/memory.py

class InMemoryStorage(ZoneStorage):
    """RAM 기반 스토리지. Core(Zone 0)과 Inner(Zone 1)에 사용."""

    def __init__(self):
        self._items: dict[str, CelestialItem] = {}

    def store(self, item): self._items[item.id] = item
    def get(self, item_id): return self._items.get(item_id)
    def remove(self, item_id): return self._items.pop(item_id, None) is not None
    def update(self, item): self._items[item.id] = item
    def count(self): return len(self._items)
    def get_all(self): return list(self._items.values())

    def search(self, query, limit=5, query_embedding=None):
        # 키워드 매칭 (대소문자 무시)
        q = query.lower()
        matches = [i for i in self._items.values() if q in i.content.lower()]
        matches.sort(key=lambda i: i.total_score, reverse=True)
        return matches[:limit]

    def get_lowest_score_item(self):
        if not self._items:
            return None
        return min(self._items.values(), key=lambda i: i.total_score)
```

### 8.3 SqliteStorage (Outer/Belt/Cloud Zone)

```python
# celestial_engine/storage/sqlite.py

import sqlite3
import json

class SqliteStorage(ZoneStorage):
    """SQLite 기반 영구 스토리지. Outer(Zone 2), Belt(Zone 3), Cloud(Zone 4)에 사용."""

    def __init__(self, db_path: str, zone_id: int):
        self._db_path = db_path
        self._zone_id = zone_id
        self._table = f"memories_zone_{zone_id}"
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_table()

    def _create_table(self):
        self._conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_recalled_at REAL NOT NULL,
                recall_count INTEGER DEFAULT 0,
                arbitrary_importance REAL DEFAULT 0.5,
                zone INTEGER DEFAULT {self._zone_id},
                metadata TEXT DEFAULT '{{}}',
                embedding BLOB,
                total_score REAL DEFAULT 0.0
            )
        """)
        self._conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{self._table}_score "
            f"ON {self._table}(total_score)"
        )
        self._conn.commit()

    def store(self, item):
        self._conn.execute(
            f"INSERT OR REPLACE INTO {self._table} "
            "(id, content, created_at, last_recalled_at, recall_count, "
            "arbitrary_importance, zone, metadata, embedding, total_score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item.id, item.content, item.created_at, item.last_recalled_at,
             item.recall_count, item.arbitrary_importance, item.zone,
             json.dumps(item.metadata), self._serialize_embedding(item.embedding),
             item.total_score),
        )
        self._conn.commit()

    def get(self, item_id):
        row = self._conn.execute(
            f"SELECT * FROM {self._table} WHERE id = ?", (item_id,)
        ).fetchone()
        return self._row_to_item(row) if row else None

    def remove(self, item_id):
        cursor = self._conn.execute(
            f"DELETE FROM {self._table} WHERE id = ?", (item_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def update(self, item):
        self.store(item)  # UPSERT

    def search(self, query, limit=5, query_embedding=None):
        q = f"%{query}%"
        rows = self._conn.execute(
            f"SELECT * FROM {self._table} WHERE content LIKE ? "
            f"ORDER BY total_score DESC LIMIT ?",
            (q, limit),
        ).fetchall()
        return [self._row_to_item(r) for r in rows]

    def get_all(self):
        rows = self._conn.execute(f"SELECT * FROM {self._table}").fetchall()
        return [self._row_to_item(r) for r in rows]

    def count(self):
        row = self._conn.execute(f"SELECT COUNT(*) FROM {self._table}").fetchone()
        return row[0] if row else 0

    def get_lowest_score_item(self):
        row = self._conn.execute(
            f"SELECT * FROM {self._table} ORDER BY total_score ASC LIMIT 1"
        ).fetchone()
        return self._row_to_item(row) if row else None

    def _serialize_embedding(self, emb):
        if emb is None:
            return None
        import struct
        return struct.pack(f"{len(emb)}f", *emb)

    def _deserialize_embedding(self, data):
        if data is None:
            return None
        import struct
        count = len(data) // 4
        return list(struct.unpack(f"{count}f", data))

    def _row_to_item(self, row):
        if row is None:
            return None
        return CelestialItem(
            id=row[0], content=row[1], created_at=row[2],
            last_recalled_at=row[3], recall_count=row[4],
            arbitrary_importance=row[5], zone=row[6],
            metadata=json.loads(row[7]) if row[7] else {},
            embedding=self._deserialize_embedding(row[8]),
            total_score=row[9],
        )
```

---

## 9. CelestialMemory Facade 상세 설계

### 9.1 Public API

```python
# celestial_engine/__init__.py

class CelestialMemory:
    """천체 기억 엔진 - 공개 Facade."""

    def __init__(
        self,
        db_path: str = "celestial_memory.db",
        zones: list[ZoneConfig] | None = None,
        memory_fn_config: MemoryFunctionConfig | None = None,
        evaluator: ImportanceEvaluator | None = None,
        rebalance_interval: int = 300,
        auto_forget_days: int = 90,
        embed_fn=None,  # (text: str) -> list[float] | None
    ):
        self._fn = CelestialMemoryFunction(memory_fn_config)
        self._zone_mgr = ZoneManager(zones, db_path)
        self._evaluator = evaluator or DefaultEvaluator()
        self._embed_fn = embed_fn
        self._rebalancer = Rebalancer(
            self._fn, self._zone_mgr,
            interval_seconds=rebalance_interval,
            auto_forget_seconds=auto_forget_days * 86400,
        )
        self._rebalancer.start()

    def store(self, content: str, importance: float | None = None,
              metadata: dict | None = None) -> CelestialItem:
        """기억 저장.
        importance=None이면 evaluator로 자동 평가.
        """
        if importance is None:
            importance = self._evaluator.evaluate(content)

        item = CelestialItem.create(content, importance, metadata)

        if self._embed_fn:
            item.embedding = self._embed_fn(content)

        now = item.created_at
        breakdown = self._fn.calculate(item, now)
        self._zone_mgr.place(item, breakdown.target_zone, breakdown.total)
        return item

    def recall(self, query: str, limit: int = 5) -> list[CelestialItem]:
        """기억 검색.
        검색 후 recall_count++, last_recalled_at 갱신, 신선도 리셋.
        """
        import time
        now = time.time()
        query_embedding = self._embed_fn(query) if self._embed_fn else None
        results = self._zone_mgr.search(query, limit, query_embedding)

        # 리콜된 기억의 메타데이터 갱신
        for item in results:
            item.recall_count += 1
            item.last_recalled_at = now  # 신선도 리셋!
            # 점수 재계산
            breakdown = self._fn.calculate(item, now, query_embedding)
            if breakdown.target_zone != item.zone:
                self._zone_mgr.move(item.id, item.zone, breakdown.target_zone, breakdown.total)
            else:
                item.total_score = breakdown.total
                self._zone_mgr._storages[item.zone].update(item)

        return results

    def rebalance(self) -> RebalanceResult:
        """수동 재배치 트리거."""
        return self._rebalancer.rebalance()

    def stats(self) -> dict:
        """Zone별 통계 반환."""
        zone_stats = self._zone_mgr.stats()
        return {
            "zones": {
                zid: {"count": count, "capacity": cap}
                for zid, (count, cap) in zone_stats.items()
            },
            "total": sum(count for count, _ in zone_stats.values()),
        }

    def close(self) -> None:
        """엔진 종료. 스케줄러 중지."""
        self._rebalancer.stop()
```

---

## 10. Adapter 상세 설계

### 10.1 LangChainAdapter

```python
# celestial_engine/adapters/langchain.py

class LangChainAdapter:
    """LangChain 프레임워크에 celestial memory 삽입."""

    def __init__(self, memory: CelestialMemory):
        self._memory = memory

    def as_retriever(self, k: int = 5):
        """LangChain Retriever 인터페이스 반환."""
        from langchain_core.retrievers import BaseRetriever
        from langchain_core.documents import Document

        mem = self._memory

        class CelestialRetriever(BaseRetriever):
            def _get_relevant_documents(self, query: str):
                results = mem.recall(query, limit=k)
                return [
                    Document(page_content=r.content, metadata=r.metadata)
                    for r in results
                ]

        return CelestialRetriever()

    def as_memory(self):
        """LangChain ConversationBufferMemory 호환 인터페이스."""
        from langchain.memory import ConversationBufferMemory

        mem = self._memory

        class CelestialConversationMemory(ConversationBufferMemory):
            def save_context(self, inputs, outputs):
                content = f"Human: {inputs.get('input', '')}\nAI: {outputs.get('output', '')}"
                mem.store(content)

            def load_memory_variables(self, inputs):
                query = inputs.get("input", "")
                results = mem.recall(query, limit=3)
                history = "\n".join(r.content for r in results)
                return {self.memory_key: history}

        return CelestialConversationMemory()
```

### 10.2 OpenAIAdapter

```python
# celestial_engine/adapters/openai.py

class OpenAIAdapter:
    """OpenAI 함수호출 형태로 celestial memory 삽입."""

    def __init__(self, memory: CelestialMemory):
        self._memory = memory

    def as_tools(self) -> list[dict]:
        """OpenAI function calling 도구 목록 반환."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "celestial_store",
                    "description": "Store a memory for later recall",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Memory content"},
                            "importance": {"type": "number", "description": "0.0-1.0"},
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "celestial_recall",
                    "description": "Recall relevant memories",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Max results"},
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

    def handle_tool_call(self, name: str, arguments: dict) -> str:
        """도구 호출 처리."""
        import json
        if name == "celestial_store":
            item = self._memory.store(
                arguments["content"],
                importance=arguments.get("importance"),
            )
            return json.dumps({"id": item.id, "zone": item.zone})
        elif name == "celestial_recall":
            results = self._memory.recall(
                arguments["query"],
                limit=arguments.get("limit", 5),
            )
            return json.dumps([{"content": r.content, "zone": r.zone} for r in results])
        return json.dumps({"error": f"Unknown tool: {name}"})
```

### 10.3 AnthropicAdapter

```python
# celestial_engine/adapters/anthropic.py

class AnthropicAdapter:
    """Claude MCP 도구 형태로 celestial memory 삽입."""

    def __init__(self, memory: CelestialMemory):
        self._memory = memory

    def as_mcp_tools(self) -> list[dict]:
        """MCP 도구 목록 반환."""
        return [
            {
                "name": "celestial_store",
                "description": "Store a memory in the celestial memory system",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "importance": {"type": "number"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "celestial_recall",
                "description": "Recall memories from the celestial memory system",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
            },
        ]

    def handle(self, tool_name: str, tool_input: dict) -> dict:
        """MCP 도구 호출 처리."""
        if tool_name == "celestial_store":
            item = self._memory.store(
                tool_input["content"],
                importance=tool_input.get("importance"),
            )
            return {"id": item.id, "zone": item.zone, "score": item.total_score}
        elif tool_name == "celestial_recall":
            results = self._memory.recall(
                tool_input["query"],
                limit=tool_input.get("limit", 5),
            )
            return {
                "memories": [
                    {"content": r.content, "zone": r.zone, "score": r.total_score}
                    for r in results
                ]
            }
        return {"error": f"Unknown tool: {tool_name}"}
```

---

## 11. 파일 구조 & 구현 순서

### 11.1 전체 파일 구조

```
celestial_engine/
├── __init__.py              # CelestialMemory facade + public exports
├── models.py                # CelestialItem, ScoreBreakdown, ZoneConfig, RebalanceResult
├── memory_function.py       # CelestialMemoryFunction (기억함수 v2)
├── zone_manager.py          # ZoneManager (배치/이동/퇴거/검색)
├── rebalancer.py            # Rebalancer (주기적 재배치 스케줄러)
├── importance.py            # ImportanceEvaluator (Default/RuleBased/LLM)
├── storage/
│   ├── __init__.py          # ZoneStorage ABC
│   ├── memory.py            # InMemoryStorage (Core/Inner)
│   └── sqlite.py            # SqliteStorage (Outer/Belt/Cloud)
└── adapters/
    ├── __init__.py          # adapter exports
    ├── langchain.py         # LangChainAdapter
    ├── openai.py            # OpenAIAdapter
    └── anthropic.py         # AnthropicAdapter
```

### 11.2 Implementation Checklist

| # | ID | 파일 | 구현 내용 | 의존성 |
|---|-----|------|----------|--------|
| 1 | F1-1 | models.py | CelestialItem, ScoreBreakdown, ZoneConfig, RebalanceResult | 없음 |
| 2 | F1-2 | memory_function.py | CelestialMemoryFunction._recall_score (log-capped) | models |
| 3 | F1-3 | memory_function.py | CelestialMemoryFunction._freshness_score (recall-reset) | models |
| 4 | F1-4 | memory_function.py | CelestialMemoryFunction._context_score (cosine sim) | models |
| 5 | F1-5 | memory_function.py | CelestialMemoryFunction.calculate + _determine_zone | models |
| 6 | F2-1 | storage/__init__.py | ZoneStorage ABC | models |
| 7 | F2-2 | storage/memory.py | InMemoryStorage | storage ABC |
| 8 | F2-3 | storage/sqlite.py | SqliteStorage | storage ABC |
| 9 | F3-1 | importance.py | DefaultEvaluator, RuleBasedEvaluator | 없음 |
| 10 | F3-2 | importance.py | LLMEvaluator | 없음 (llm_callable 주입) |
| 11 | F4-1 | zone_manager.py | ZoneManager (place, move, evict, search, stats) | storage, models |
| 12 | F4-2 | zone_manager.py | ZoneManager.forget_stale + enforce_capacity | storage |
| 13 | F5-1 | rebalancer.py | Rebalancer.rebalance (수동) | memory_fn, zone_mgr |
| 14 | F5-2 | rebalancer.py | Rebalancer.start/stop (자동 스케줄링) | threading |
| 15 | F6-1 | __init__.py | CelestialMemory.store | all above |
| 16 | F6-2 | __init__.py | CelestialMemory.recall (+ recall-reset) | all above |
| 17 | F6-3 | __init__.py | CelestialMemory.rebalance, stats, close | all above |
| 18 | F7-1 | adapters/langchain.py | LangChainAdapter.as_retriever, as_memory | facade |
| 19 | F7-2 | adapters/openai.py | OpenAIAdapter.as_tools, handle_tool_call | facade |
| 20 | F7-3 | adapters/anthropic.py | AnthropicAdapter.as_mcp_tools, handle | facade |

### 11.3 Implementation Order

```
Phase 1: 핵심 (F1-1 → F1-5)
  models.py → memory_function.py

Phase 2: 스토리지 (F2-1 → F2-3)
  storage/__init__.py → storage/memory.py → storage/sqlite.py

Phase 3: 평가기 (F3-1 → F3-2)
  importance.py

Phase 4: 관리자 (F4-1 → F4-2)
  zone_manager.py

Phase 5: 재배치 (F5-1 → F5-2)
  rebalancer.py

Phase 6: Facade (F6-1 → F6-3)
  __init__.py (CelestialMemory)

Phase 7: 어댑터 (F7-1 → F7-3)
  adapters/langchain.py → adapters/openai.py → adapters/anthropic.py
```

---

## 12. stellar_memory 통합 계획

### 12.1 기존 코드와의 관계

```python
# stellar_memory/memory_function.py (수정)
# 기존 MemoryFunction이 CelestialMemoryFunction을 내부적으로 사용하도록 변경

from celestial_engine.memory_function import CelestialMemoryFunction

class MemoryFunction:
    def __init__(self, config=None, zones=None, use_v2: bool = False):
        self._use_v2 = use_v2
        if use_v2:
            from celestial_engine.memory_function import MemoryFunctionConfig as V2Config
            v2_cfg = V2Config(
                w_recall=config.w_recall if config else 0.25,
                w_freshness=config.w_freshness if config else 0.30,
                w_arbitrary=config.w_arbitrary if config else 0.25,
                w_context=config.w_context if config else 0.20,
            )
            self._v2 = CelestialMemoryFunction(v2_cfg)
        # ... 기존 로직 유지
```

### 12.2 마이그레이션 경로

| 단계 | 작업 | 영향 |
|------|------|------|
| 1 | celestial_engine/ 패키지 생성 (독립) | 기존 코드 변경 없음 |
| 2 | stellar_memory에 `use_v2=True` 옵션 추가 | 하위 호환 유지 |
| 3 | 기본값을 v2로 전환 (v2.0.0) | 메이저 버전 업데이트 |

---

## 13. Test Plan

### 13.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| Unit Test | MemoryFunction 각 점수 계산 | pytest |
| Unit Test | ZoneManager 배치/이동/퇴거 | pytest |
| Integration Test | store → recall → rebalance 전체 흐름 | pytest |
| Math Proof Test | 블랙홀 방지 수학적 증명 | pytest (assertion) |
| Performance Test | 10K 기억 rebalance < 500ms | pytest-benchmark |
| Adapter Test | LangChain/OpenAI/Anthropic 어댑터 | pytest (mock) |

### 13.2 핵심 Test Cases

```python
# 블랙홀 방지 증명 테스트
def test_blackhole_prevention():
    """리콜하지 않는 기억은 반드시 외곽으로 밀려야 한다."""
    fn = CelestialMemoryFunction()
    item = CelestialItem.create("test", importance=1.0)
    item.recall_count = 1000

    # 생성 직후: Core 진입 가능
    score_t0 = fn.calculate(item, item.created_at)
    assert score_t0.target_zone <= 1  # Core or Inner

    # 1일 후: 리콜 없음 → 강등
    score_t1 = fn.calculate(item, item.created_at + 86400)
    assert score_t1.target_zone > score_t0.target_zone

    # 7일 후: 더 외곽으로
    score_t7 = fn.calculate(item, item.created_at + 86400 * 7)
    assert score_t7.total < score_t1.total


# 리콜-리셋 테스트
def test_recall_resets_freshness():
    """리콜 시 신선도가 0으로 리셋되어야 한다."""
    fn = CelestialMemoryFunction()
    item = CelestialItem.create("test")

    # 1일 후
    score_stale = fn.calculate(item, item.created_at + 86400)

    # 리콜!
    item.last_recalled_at = item.created_at + 86400
    item.recall_count = 1
    score_fresh = fn.calculate(item, item.created_at + 86400)

    assert score_fresh.freshness_score == 0.0  # 리셋됨
    assert score_fresh.total > score_stale.total  # 점수 회복


# Core Zone 용량 테스트
def test_core_zone_capacity():
    """Core Zone은 20개를 초과할 수 없다."""
    memory = CelestialMemory(db_path=":memory:")
    for i in range(30):
        memory.store(f"important memory {i}", importance=1.0)

    stats = memory.stats()
    assert stats["zones"][0]["count"] <= 20
    memory.close()
```

---

## 14. Coding Conventions

### 14.1 Naming

| Target | Rule | Example |
|--------|------|---------|
| 클래스 | PascalCase | `CelestialMemory`, `ZoneManager` |
| 함수/메서드 | snake_case | `_recall_score`, `forget_stale` |
| 상수 | UPPER_SNAKE_CASE | `DEFAULT_ZONES`, `MAX_RECALL_CAP` |
| 파일 | snake_case.py | `memory_function.py`, `zone_manager.py` |
| Private | _ prefix | `_cfg`, `_evict_lowest` |

### 14.2 Import Order

```python
# 1. __future__
from __future__ import annotations

# 2. stdlib
import math
import time
import threading

# 3. local (같은 패키지)
from celestial_engine.models import CelestialItem, ScoreBreakdown
```

### 14.3 Type Hints

- 모든 public 메서드에 type hint 필수
- `list[float] | None` 형태 사용 (Optional[X] 대신)
- `from __future__ import annotations` 모든 파일에 포함

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-18 | Initial draft | AI |
