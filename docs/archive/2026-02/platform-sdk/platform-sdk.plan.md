# Platform SDK Planning Document

> **Summary**: Stellar Memory v3.0 - AI Memory Platform SDK for Derivative Products
>
> **Project**: stellar-memory
> **Version**: 2.0.0 -> 3.0.0
> **Date**: 2026-02-21
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

Stellar Memory를 **AI 메모리 플랫폼**으로 재구성한다. 현재 모놀리식 패키지(9,400+ LOC, 65+ exports)를 정리하여 **핵심 메모리 엔진**과 **확장 레이어**를 분리하고, Homunculus 같은 파생 제품이 쉽게 구축할 수 있는 깨끗한 SDK를 제공한다.

### 1.2 Background

**현재 상태 (v2.0.0)**:
- Stellar Memory는 메모리 저장/회상부터 결제(billing), 대시보드, REST API, 인증까지 모든 것이 하나의 패키지에 들어있음
- `__init__.py`에서 65개 이상의 클래스/함수를 export
- 30개 이상의 Config 클래스
- 파생 제품인 Homunculus는 `stellar-memory>=2.0.0` 전체를 의존성으로 가져야 하며, 실제로 사용하는 것은 메모리 엔진의 핵심 기능뿐

**비전**:
```
Stellar Memory = AI의 뇌 (The Brain)
    ├── Homunculus = 자율 에이전트 (몸 + 행동)
    ├── [Future] AI 비서 = 대화형 메모리 에이전트
    ├── [Future] 지식 관리 시스템 = 조직 메모리
    ├── [Future] AI 튜터 = 학습 메모리
    └── [Future] ...무한한 파생 제품
```

파생 제품이 쉽게 만들어지려면 Stellar Memory는 **"뇌" 역할에만 집중**해야 한다. 결제, UI, 서버 등 "몸"에 해당하는 기능은 별도로 분리해야 한다.

### 1.3 Related Documents

- Homunculus 프로젝트: `C:\Users\USER\Homunculus\`
- Archive Index: `docs/archive/2026-02/_INDEX.md` (18개 PDCA 사이클 완료)

---

## 2. Scope

### 2.1 In Scope

- [x] F1: Core SDK Layer - 핵심 메모리 API 정리 및 최소화
- [x] F2: Package Split - 모놀리식 패키지를 역할별로 분리
- [x] F3: Plugin System - 파생 제품이 확장할 수 있는 플러그인 아키텍처
- [x] F4: SDK Builder - 간편한 초기화를 위한 Builder 패턴
- [x] F5: Interface Contracts - 파생 제품이 의존할 명확한 Protocol/Interface
- [x] F6: Migration Guide - v2.0 → v3.0 마이그레이션 가이드

### 2.2 Out of Scope

- 새로운 메모리 알고리즘 개발 (기존 알고리즘 유지)
- Homunculus 코드 수정 (Homunculus는 별도 PDCA로)
- 새로운 AI provider 추가
- Landing page 업데이트

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 핵심 메모리 엔진을 `stellar-memory-core`로 분리 (Zero Dependencies) | Critical | Pending |
| FR-02 | 현재 65+ exports를 10개 이하의 핵심 public API로 축소 | Critical | Pending |
| FR-03 | 플러그인 시스템으로 Storage/Provider/Evaluator 확장 가능하게 | High | Pending |
| FR-04 | Builder 패턴으로 3줄 이내 초기화 가능 | High | Pending |
| FR-05 | 파생 제품이 의존할 Protocol 인터페이스 정의 | High | Pending |
| FR-06 | 응용 레이어(billing, dashboard, auth, server)를 별도 패키지로 분리 | High | Pending |
| FR-07 | 이벤트 훅 시스템으로 파생 제품이 메모리 라이프사이클에 개입 가능 | Medium | Pending |
| FR-08 | v2.0 → v3.0 마이그레이션 가이드 작성 | Medium | Pending |
| FR-09 | `celestial_engine`을 `stellar-memory-core`에 통합 (중복 제거) | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | Core SDK import time < 100ms | Python timeit |
| Size | Core package < 2,000 LOC (현재 9,400+) | wc -l |
| Dependencies | Core package: Zero external dependencies | pip show |
| API Surface | Public exports <= 10 classes | `__init__.py` 검사 |
| Backward Compat | v2.0 코드가 shim 패키지로 동작 | 기존 테스트 통과 |

---

## 4. Architecture: 현재 vs 목표

### 4.1 현재 구조 (v2.0 - 모놀리식)

```
stellar-memory (하나의 패키지)
├── Core: memory_function, orbit_manager, memory_graph, decay, vector_index
├── Intelligence: emotion, reasoning, metacognition, self_learning, multimodal
├── Infrastructure: storage/, providers/, security/, sync/
├── Application: billing/, dashboard/, connectors/, auth
├── Interface: cli, server, mcp_server
└── Onboarding: scanner, importer, viz, knowledge_base
```

**문제점**:
1. Homunculus가 `pip install stellar-memory`하면 billing, dashboard 코드도 딸려옴
2. 65개 export 중 파생 제품이 실제로 쓰는 건 5-6개
3. Config 클래스가 30개 이상 - 뭘 설정해야 하는지 파악하기 어려움
4. `celestial_engine`이 `stellar_memory`의 경량 복제 - 중복 코드

### 4.2 목표 구조 (v3.0 - Platform SDK)

```
stellar-memory (Core SDK) ← 파생 제품이 의존하는 유일한 패키지
├── StellarMemory          # 메인 클래스 (Facade)
├── MemoryItem             # 핵심 데이터 모델
├── StellarConfig          # 통합 설정 (간소화)
├── MemoryPlugin           # 플러그인 베이스 클래스
├── StorageBackend         # 스토리지 Protocol
├── EmbedderProvider       # 임베딩 Protocol
├── ImportanceEvaluator    # 중요도 평가 Protocol
├── EventHook              # 이벤트 훅 Protocol
└── StellarBuilder         # Builder 패턴

stellar-memory[mcp]        # MCP 서버 (Claude/AI 도구 연동)
stellar-memory[server]     # REST API 서버 (FastAPI)
stellar-memory[ai]         # AI 기능 (embeddings, LLM)
stellar-memory[postgres]   # PostgreSQL 스토리지
stellar-memory[full]       # 모든 것 포함
```

### 4.3 파생 제품 통합 예시

**Before (v2.0 - Homunculus)**:
```python
from stellar_memory import (
    StellarMemory, StellarConfig, MemoryFunctionConfig,
    EmbedderConfig, LLMConfig, ZoneConfig, EmotionConfig,
    GraphConfig, MetacognitionConfig, SelfLearningConfig,
    ReasoningConfig, StorageConfig, EventConfig,
    MemoryItem, EmotionVector, ...
)

config = StellarConfig(
    memory_function=MemoryFunctionConfig(...),
    embedder=EmbedderConfig(...),
    llm=LLMConfig(...),
    zones=[ZoneConfig(...), ZoneConfig(...), ...],
    emotion=EmotionConfig(...),
    graph=GraphConfig(...),
    metacognition=MetacognitionConfig(...),
    # ... 20줄 이상의 설정
)
memory = StellarMemory(config)
```

**After (v3.0 - Homunculus)**:
```python
from stellar_memory import StellarMemory, StellarBuilder

memory = (
    StellarBuilder()
    .with_sqlite("~/.homunculus/brain.db")
    .with_emotions()
    .with_graph()
    .with_reasoning()
    .build()
)

# 저장
memory.store("사용자는 Python을 선호한다", importance=0.9)

# 회상
results = memory.recall("프로그래밍 선호도", limit=5)

# 이벤트 훅
memory.on("store", lambda item: print(f"New memory: {item.content}"))
```

---

## 5. Feature Details

### F1: Core SDK Layer (핵심 API 정리)

**유지할 기능** (Core - 뇌의 본질):

| Component | File | Lines | Reason |
|-----------|------|------:|--------|
| StellarMemory (Facade) | stellar.py | 961 | 메인 클래스 - 대폭 간소화 |
| MemoryFunction (Scoring) | memory_function.py | 79 | 핵심 점수 계산 알고리즘 |
| OrbitManager (Zones) | orbit_manager.py | 140 | 존 관리 - 뇌의 구조 |
| MemoryGraph | memory_graph.py | 62 | 기억 간 연결 |
| PersistentGraph | persistent_graph.py | 118 | 그래프 영속화 |
| DecayManager | decay_manager.py | 73 | 망각 메커니즘 |
| AdaptiveDecay | adaptive_decay.py | 57 | 적응형 망각 |
| EventBus | event_bus.py | 57 | 이벤트 시스템 |
| VectorIndex | vector_index.py | 233 | 시맨틱 검색 |
| Models | models.py | 444 | 데이터 모델 (간소화) |
| Config | config.py | 398 | 설정 (간소화) |
| Storage (Abstract) | storage/__init__.py | 99 | 스토리지 인터페이스 |
| SQLite Storage | storage/sqlite.py | 192 | 기본 스토리지 |
| InMemory Storage | storage/in_memory.py | 61 | 테스트/경량 스토리지 |
| Embedder (Interface) | embedder.py | 79 | 임베딩 인터페이스 |
| ImportanceEvaluator | importance_evaluator.py | 194 | 중요도 평가 |
| Namespace | namespace.py | 47 | 네임스페이스 격리 |
| Session | session.py | 44 | 세션 관리 |

**Core 총계**: ~2,400 LOC (현재 9,400+에서 **74% 감소**)

### F2: Package Split (패키지 분리)

**분리할 기능** (응용 레이어 - "몸"에 해당):

| Component | Current Location | Target | Reason |
|-----------|-----------------|--------|--------|
| Billing | billing/ (748 LOC) | 제거 | SaaS 서버 관심사 |
| Dashboard | dashboard/ (260 LOC) | `stellar-memory[dashboard]` | UI 관심사 |
| REST Server | server.py (1,032 LOC) | `stellar-memory[server]` | 이미 optional |
| Auth | auth.py (288 LOC) | `stellar-memory[server]` | 서버 관심사 |
| MCP Server | mcp_server.py (501 LOC) | `stellar-memory[mcp]` | 이미 optional |
| CLI (기본) | cli.py (748 LOC) | 유지 (간소화) | 진입점 |
| Sync | sync/ (337 LOC) | `stellar-memory[sync]` | 분산 관심사 |
| Connectors | connectors/ (218 LOC) | `stellar-memory[connectors]` | 데이터 수집 |
| Security | security/ (220 LOC) | `stellar-memory[security]` | 암호화/접근제어 |
| PostgreSQL | storage/postgres.py (382 LOC) | `stellar-memory[postgres]` | 이미 optional |
| Redis | storage/redis_cache.py (138 LOC) | `stellar-memory[redis]` | 이미 optional |
| Onboarding | scanner/importer/viz/kb (1,400 LOC) | `stellar-memory[onboard]` | 온보딩 관심사 |

**Intelligence 기능** (뇌의 고급 기능 - Core에 유지):

| Component | Lines | Decision | Reason |
|-----------|------:|----------|--------|
| Emotion | 111 | Core 유지 | 메모리 점수에 영향 |
| Reasoning | 293 | Core 유지 | 메모리 기반 추론 |
| Metacognition | 153 | Core 유지 | 자기 인식 |
| Self-Learning | 341 | Core 유지 | 가중치 최적화 |
| Multimodal | 167 | Core 유지 | 콘텐츠 타입 처리 |
| Stream | 117 | Core 유지 | 메모리 스트림 |
| Graph Analyzer | 225 | Core 유지 | 그래프 분석 |
| Consolidator | 72 | Core 유지 | 메모리 병합 |
| Summarizer | 49 | Core 유지 | 메모리 요약 |

### F3: Plugin System

파생 제품이 Stellar Memory를 확장할 수 있는 플러그인 아키텍처:

```python
from stellar_memory import MemoryPlugin, StellarMemory

class HomuculusPlugin(MemoryPlugin):
    """Homunculus-specific memory behaviors."""

    def on_store(self, item):
        """기억 저장 시 경험으로 변환."""
        item.metadata["experience_type"] = self.classify(item.content)

    def on_recall(self, query, results):
        """회상 시 컨텍스트 보강."""
        return self.add_emotional_context(results)

    def on_decay(self, item, new_score):
        """망각 시 중요 기억 보호."""
        if item.metadata.get("core_identity"):
            return max(new_score, 0.5)  # 정체성 기억은 보호
        return new_score

# 플러그인 등록
memory = StellarMemory(config)
memory.use(HomuculusPlugin())
```

**Plugin Hooks**:

| Hook | Timing | Purpose |
|------|--------|---------|
| `on_store(item)` | 저장 직후 | 메타데이터 추가, 변환 |
| `on_pre_recall(query)` | 회상 직전 | 쿼리 보강 |
| `on_recall(query, results)` | 회상 직후 | 결과 필터링/보강 |
| `on_decay(item, score)` | 망각 계산 시 | 점수 조정 |
| `on_reorbit(moves)` | 리오빗 후 | 존 이동 추적 |
| `on_consolidate(merged)` | 병합 후 | 병합 결과 처리 |

### F4: SDK Builder

간편한 초기화를 위한 Builder 패턴과 Preset:

```python
from stellar_memory import StellarBuilder, Preset

# 1. 최소 구성 (3줄)
memory = StellarBuilder().build()

# 2. Preset 사용
memory = StellarBuilder(Preset.AGENT).build()      # 에이전트용 (Homunculus)
memory = StellarBuilder(Preset.CHAT).build()        # 대화형
memory = StellarBuilder(Preset.KNOWLEDGE).build()   # 지식 관리용
memory = StellarBuilder(Preset.RESEARCH).build()    # 연구용

# 3. 커스텀 구성
memory = (
    StellarBuilder()
    .with_sqlite("./memory.db")           # 스토리지
    .with_embeddings("openai")            # 시맨틱 검색
    .with_emotions()                      # 감정 분석
    .with_graph(auto_link=True)           # 그래프 연결
    .with_reasoning()                     # 추론 엔진
    .with_decay(rate=0.01)                # 망각 속도
    .with_zones(core=20, inner=100)       # 존 크기
    .with_namespace("homunculus")         # 네임스페이스
    .with_plugin(MyPlugin())              # 플러그인
    .build()
)

# 4. 딕셔너리/TOML에서 구성
memory = StellarBuilder.from_dict({...}).build()
memory = StellarBuilder.from_toml("stellar.toml").build()
```

**Presets**:

| Preset | Zones | Features | Use Case |
|--------|-------|----------|----------|
| `MINIMAL` | 3 zones | Store/Recall only | 가장 가벼운 사용 |
| `CHAT` | 5 zones | + Session, Emotion | 대화형 AI |
| `AGENT` | 5 zones | + Graph, Reasoning, Metacognition, Self-learning | 자율 에이전트 (Homunculus) |
| `KNOWLEDGE` | 5 zones | + Graph, Consolidation, Summarization | 지식 관리 |
| `RESEARCH` | 5 zones | + Vector, Benchmark | 연구/실험 |

### F5: Interface Contracts (Protocol 정의)

파생 제품이 의존할 안정적인 인터페이스:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class MemoryStore(Protocol):
    """핵심 메모리 인터페이스 - 파생 제품은 이것만 의존."""

    def store(self, content: str, *, importance: float = 0.5,
              metadata: dict | None = None) -> str:
        """기억 저장. ID 반환."""
        ...

    def recall(self, query: str, *, limit: int = 5,
               min_score: float = 0.0) -> list[MemoryItem]:
        """기억 회상."""
        ...

    def get(self, memory_id: str) -> MemoryItem | None:
        """ID로 기억 조회."""
        ...

    def forget(self, memory_id: str) -> bool:
        """기억 삭제."""
        ...

    def stats(self) -> MemoryStats:
        """메모리 통계."""
        ...

@runtime_checkable
class StorageBackend(Protocol):
    """스토리지 확장 인터페이스."""
    def store(self, item: MemoryItem) -> None: ...
    def get(self, item_id: str) -> MemoryItem | None: ...
    def update(self, item: MemoryItem) -> None: ...
    def remove(self, item_id: str) -> bool: ...
    def search(self, query: str, limit: int) -> list[MemoryItem]: ...

@runtime_checkable
class EmbedderProvider(Protocol):
    """임베딩 확장 인터페이스."""
    def embed(self, text: str) -> list[float] | None: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

@runtime_checkable
class ImportanceEvaluator(Protocol):
    """중요도 평가 확장 인터페이스."""
    def evaluate(self, content: str, metadata: dict) -> float: ...
```

### F6: celestial_engine 통합

`celestial_engine`(1,102 LOC)은 `stellar_memory`의 경량 복제:
- `CelestialMemory` ≈ `StellarMemory` (간소화 버전)
- `CelestialMemoryFunction` ≈ `MemoryFunction` (동일 알고리즘)
- `ZoneManager` ≈ `OrbitManager` (유사 로직)
- AI 미들웨어, AutoMemory, Presets → 이들은 유용하므로 Core로 통합

**계획**:
1. `celestial_engine`의 고유 기능 (Middleware, AutoMemory, Presets)을 `stellar_memory`로 통합
2. `CelestialMemory`를 `StellarMemory`의 alias로 유지 (하위 호환)
3. `celestial_engine` 패키지를 deprecated 처리

---

## 6. 제거 대상 상세

### 6.1 완전 제거

| Component | Lines | Reason |
|-----------|------:|--------|
| billing/ | 748 | SaaS 서버 관심사. Stellar Memory는 라이브러리이지 SaaS가 아님 |
| auth.py | 288 | API 키/사용자 인증은 서버 관심사 |
| tiers.py | 43 | 과금 티어 - 제거 |

**Reason**: Stellar Memory는 **라이브러리**다. 결제, 인증은 이 라이브러리를 사용하는 **애플리케이션**(SaaS 서버)의 관심사이지 라이브러리의 관심사가 아니다.

### 6.2 Optional Extras로 분리

| Component | Extra | Dependency |
|-----------|-------|------------|
| mcp_server.py | `[mcp]` | mcp[cli] |
| server.py | `[server]` | fastapi, uvicorn |
| dashboard/ | `[dashboard]` | fastapi, uvicorn |
| storage/postgres.py | `[postgres]` | asyncpg |
| storage/redis_cache.py | `[redis]` | redis |
| sync/ | `[sync]` | websockets |
| security/ | `[security]` | cryptography |
| connectors/ | `[connectors]` | httpx |
| providers/openai_provider.py | `[openai]` | openai |
| providers/ollama_provider.py | `[ollama]` | requests |
| scanner.py, importer.py, viz.py, knowledge_base.py | `[onboard]` | (stdlib only) |

### 6.3 유지하되 간소화

| Component | Current | Target | Changes |
|-----------|--------:|-------:|---------|
| stellar.py | 961 | ~400 | 서버/보안/대시보드 메서드 제거, 핵심만 유지 |
| models.py | 444 | ~200 | 서버/빌링 관련 모델 제거 |
| config.py | 398 | ~150 | 30개 Config → 5개로 통합 |
| cli.py | 748 | ~300 | 서버 명령 분리, 핵심 명령만 |
| __init__.py | 164 | ~30 | 65+ exports → 10개 이하 |

---

## 7. 새로운 Public API (v3.0)

### 7.1 Core Exports (10개 이하)

```python
# stellar_memory/__init__.py (v3.0)

# 1. Main Class
from .stellar import StellarMemory

# 2. Builder
from .builder import StellarBuilder, Preset

# 3. Core Models
from .models import MemoryItem, MemoryStats

# 4. Plugin Interface
from .plugin import MemoryPlugin

# 5. Extension Protocols
from .protocols import StorageBackend, EmbedderProvider, ImportanceEvaluator

# 6. Config
from .config import StellarConfig
```

### 7.2 StellarMemory Public Methods (v3.0)

```python
class StellarMemory:
    # === Core Operations (5) ===
    def store(content, *, importance, metadata) -> str
    def recall(query, *, limit, min_score, emotion, zone) -> list[MemoryItem]
    def get(memory_id) -> MemoryItem | None
    def forget(memory_id) -> bool
    def stats() -> MemoryStats

    # === Lifecycle (3) ===
    def reorbit() -> ReorbitResult
    def start() -> None
    def stop() -> None

    # === Graph (2) ===
    def link(source_id, target_id, relation) -> None
    def related(memory_id, depth) -> list[MemoryItem]

    # === Intelligence (optional, enabled by Builder) ===
    def reason(query) -> ReasoningResult          # with_reasoning()
    def introspect(topic) -> IntrospectionResult  # with_metacognition()

    # === Plugin (2) ===
    def use(plugin: MemoryPlugin) -> None
    def on(event, callback) -> None

    # === Serialization (2) ===
    def export_json(path) -> str
    def import_json(path) -> int
```

**v2.0 대비 제거되는 public methods**:
- `encrypt_memory()`, `decrypt_memory()` → `[security]` 플러그인으로
- `ingest()` → `[connectors]` 플러그인으로
- `create_middleware()` → `[adapters]` 플러그인으로
- `narrate()`, `timeline()` → `stream` 모듈 직접 접근
- `benchmark()` → `[dev]` 유틸리티로
- `provide_feedback()`, `auto_tune()` → 내부 self-learning으로 자동화
- `graph_stats()`, `graph_communities()`, `graph_centrality()`, `graph_path()` → `graph_analyzer` 직접 접근
- `recall_with_confidence()` → `recall()`에 통합 (confidence 필드)
- `detect_contradictions()` → `reason()`에 통합
- `optimize()`, `snapshot()` → 내부 관리

---

## 8. 파생 제품 개발 가이드

### 8.1 Homunculus 통합 (예시)

```python
# homunculus/memory/bridge.py (v3.0)
from stellar_memory import StellarBuilder, Preset, MemoryPlugin

class HomuculusMemoryPlugin(MemoryPlugin):
    """Homunculus-specific memory behaviors."""

    def on_store(self, item):
        # 경험 분류
        item.metadata["experience_type"] = self._classify(item.content)

    def on_recall(self, query, results):
        # 성격에 맞는 기억 우선순위
        return sorted(results, key=lambda r: self._personality_relevance(r))

class MemoryBridge:
    def __init__(self, db_path: str):
        self.memory = (
            StellarBuilder(Preset.AGENT)
            .with_sqlite(db_path)
            .with_plugin(HomuculusMemoryPlugin())
            .build()
        )

    def remember(self, experience: str, importance: float = 0.5):
        return self.memory.store(experience, importance=importance)

    def recall_context(self, situation: str, limit: int = 10):
        return self.memory.recall(situation, limit=limit)
```

### 8.2 새 파생 제품 만들기 (최소 3단계)

```bash
# Step 1: 설치
pip install stellar-memory

# Step 2: 초기화
from stellar_memory import StellarBuilder, Preset
memory = StellarBuilder(Preset.CHAT).with_sqlite("./memory.db").build()

# Step 3: 사용
memory.store("사용자 이름은 김철수입니다", importance=0.9)
results = memory.recall("사용자 이름")
```

---

## 9. Implementation Order

```
F5 (Protocols) → F4 (Builder) → F3 (Plugin) → F1 (Core SDK) → F2 (Package Split) → F6 (Migration)
```

| Step | Feature | Description | Estimated LOC |
|-----:|---------|-------------|-----:|
| 1 | F5 | Protocol 인터페이스 정의 | ~100 |
| 2 | F4 | StellarBuilder + Preset 구현 | ~200 |
| 3 | F3 | MemoryPlugin 베이스 클래스 + 훅 시스템 | ~150 |
| 4 | F1 | StellarMemory facade 간소화, __init__.py 정리 | ~-500 (삭제) |
| 5 | F2 | 패키지 분리, pyproject.toml 정리 | ~100 |
| 6 | F6 | celestial_engine 통합, 마이그레이션 가이드 | ~200 |
| 7 | - | Config 간소화 (30개 → 5개) | ~-250 (삭제) |
| 8 | - | 테스트 업데이트 | ~300 |

**Net change**: ~-1,500 LOC (코드 감소가 목표)

---

## 10. Success Criteria

### 10.1 Definition of Done

- [ ] `pip install stellar-memory`로 Core SDK만 설치됨 (billing, dashboard 없음)
- [ ] 파생 제품 3줄 초기화: `StellarBuilder(Preset.AGENT).with_sqlite(path).build()`
- [ ] Public exports 10개 이하
- [ ] Core import time < 100ms
- [ ] Homunculus가 v3.0 SDK로 동작 확인
- [ ] 기존 테스트 90% 이상 통과 (분리된 기능 제외)
- [ ] Zero external dependencies for core

### 10.2 Quality Criteria

- [ ] 모든 Protocol에 docstring 포함
- [ ] Builder 패턴 타입 안전성 (mypy 통과)
- [ ] Plugin 시스템 테스트 커버리지 > 80%

---

## 11. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| v2.0 호환성 깨짐 | High | High | Shim 패키지 + 마이그레이션 가이드 |
| Billing 제거 시 SaaS 서버 동작 불가 | Medium | Medium | 서버는 별도 배포, billing은 서버 레포로 이동 |
| celestial_engine 통합 시 기존 사용자 혼란 | Low | Medium | Deprecated warning + alias 유지 |
| Plugin 시스템이 복잡해질 수 있음 | Medium | Low | 단순한 훅 기반 설계, 과도한 추상화 지양 |
| Core가 너무 작아져서 유용성 감소 | Medium | Low | Intelligence 기능(emotion, reasoning 등)은 Core에 유지 |

---

## 12. Next Steps

1. [ ] 이 Plan 검토 및 승인
2. [ ] Design 문서 작성 (`/pdca design platform-sdk`)
3. [ ] 구현 시작

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-21 | Initial draft | Claude |
