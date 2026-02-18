# stellar-memory-p9 Design Document

> **Summary**: 고급 인지 & 자율 학습 - 기술 설계서 (v1.0.0 정식 릴리스)
>
> **Project**: Stellar Memory
> **Version**: v0.9.0 → v1.0.0
> **Author**: Stellar Memory Team
> **Date**: 2026-02-17
> **Status**: Draft
> **Planning Doc**: [stellar-memory-p9.plan.md](../../01-plan/features/stellar-memory-p9.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **자기 인식 기억**: AI가 자신의 지식 범위와 확신도를 정량적으로 파악
2. **자동 최적화**: 사용 패턴 분석 → 기억 함수 가중치 자동 조정 (외부 의존성 없이)
3. **멀티 타입 처리**: text/code/json/structured 타입별 최적 저장/검색 전략
4. **추론 능력**: 기존 기억을 조합하여 새로운 인사이트 도출 + 모순 탐지
5. **정량적 측정**: 리콜 정확도, 응답시간, 메모리 사용량 벤치마크 도구
6. **100% 하위 호환**: 기존 508개 테스트 0 깨짐, 모든 신규 기능 기본 비활성화

### 1.2 Design Principles

- **NullProvider 패턴 유지**: LLM 없어도 규칙 기반 폴백으로 모든 기능 동작
- **Opt-in Activation**: `MetacognitionConfig(enabled=True)` 등 명시적 활성화만 동작
- **Pure Python**: 신규 기능에 외부 의존성 추가하지 않음 (기존 선택적 의존성만 활용)
- **기존 아키텍처 준수**: dataclass Config, MemoryItem 확장, EventBus 연동

---

## 2. Architecture

### 2.1 P9 변경 범위 다이어그램

```
                    ┌─────────────────────────────────────────────┐
                    │            P9: 고급 인지 레이어                │
                    │                                             │
  ┌──────────┐     │  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
  │ User     │────▶│  │Metacog-   │  │Self-      │  │Benchmark│ │
  │ API      │     │  │nition     │  │Learning   │  │Engine   │ │
  │ Calls    │     │  │Engine     │  │Optimizer  │  │         │ │
  │          │     │  └─────┬─────┘  └─────┬─────┘  └────┬────┘ │
  └──────────┘     │        │              │              │      │
                    │        ▼              ▼              ▼      │
                    │  ┌─────────────────────────────────────┐   │
                    │  │         기존 Stellar Memory 코어       │   │
                    │  │                                     │   │
                    │  │  MemoryFunction  OrbitManager       │   │
                    │  │  Embedder        Graph              │   │
                    │  │  Storage         EventBus           │   │
                    │  │  (55 파일, 508 테스트)                │   │
                    │  └─────────────────────────────────────┘   │
                    │        ▲              ▲                     │
                    │  ┌─────┴─────┐  ┌────┴──────┐             │
                    │  │Multimodal │  │Reasoning  │             │
                    │  │Memory     │  │Engine     │             │
                    │  │Handler    │  │           │             │
                    │  └───────────┘  └───────────┘             │
                    └─────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
[메타인지] introspect(topic)
  → recall(topic) → 기억 목록 수집
  → 커버리지 분석 (태그/키워드 vs 기억 존재 여부)
  → 신뢰도 계산 (기억 수, 신선도, 존 분포)
  → IntrospectionResult 반환

[자율 학습] optimize()
  → PatternCollector에서 리콜 이력 로드
  → 패턴 분석 (최근성 선호, 감정 선호 등)
  → WeightOptimizer가 가중치 미세 조정
  → 시뮬레이션 검증 → 개선 시만 적용 / 롤백

[멀티모달] store(content, content_type="code")
  → ContentTypeHandler.preprocess(content)
  → 타입별 임베딩 (코드→코드 임베더, 텍스트→텍스트 임베더)
  → MemoryItem에 content_type 필드 저장
  → recall 시 content_type 필터링

[추론] reason(query)
  → 관련 기억 수집 (recall + graph neighbors)
  → LLM에 기억 목록 + 질문 전달 → 추론 결과
  → 모순 탐지 (기억 쌍 비교)
  → ReasoningResult 반환 (인사이트 + 소스 추적)

[벤치마크] benchmark(queries=1000)
  → StandardDataset 로드 (또는 사용자 데이터셋)
  → store/recall/reorbit 각 단계 시간 측정
  → recall@k 정확도 계산
  → BenchmarkReport 생성 (JSON + HTML)
```

### 2.3 Dependencies

| 신규 모듈 | 의존 대상 | 목적 |
|-----------|----------|------|
| metacognition.py | stellar.py, memory_function.py, graph | 기억 검색 + 그래프 분석으로 지식 상태 파악 |
| self_learning.py | memory_function.py, config.py | 기억 함수 가중치 읽기/수정 |
| multimodal.py | models.py, embedder.py, storage | MemoryItem 확장, 타입별 임베딩 |
| reasoning.py | stellar.py, graph, llm_adapter.py | 기억 검색 + LLM 추론 |
| benchmark.py | stellar.py, time module | store/recall 성능 측정 |

---

## 3. Data Model

### 3.1 신규/확장 모델 (models.py 추가)

```python
# ── F1: 메타인지 결과 ──

@dataclass
class IntrospectionResult:
    """introspect() 결과."""
    topic: str                          # 분석 주제
    confidence: float                   # 종합 신뢰도 (0.0~1.0)
    coverage: list[str]                 # 커버하는 하위 주제 목록
    gaps: list[str]                     # 기억이 부족한 영역
    memory_count: int                   # 관련 기억 수
    avg_freshness: float                # 평균 신선도 (0.0~1.0)
    zone_distribution: dict[int, int]   # 존별 분포 {0: 3, 1: 5, ...}

@dataclass
class ConfidentRecall:
    """recall_with_confidence() 결과."""
    memories: list[MemoryItem]          # 리콜된 기억 목록
    confidence: float                   # 종합 신뢰도 (0.0~1.0)
    warning: str | None                 # 낮은 신뢰도 시 경고 메시지


# ── F2: 자율 학습 결과 ──

@dataclass
class RecallLog:
    """리콜 이력 단일 항목."""
    query: str                          # 검색 쿼리
    result_ids: list[str]               # 반환된 기억 ID들
    timestamp: float                    # 리콜 시간
    feedback: str = "none"              # "positive" | "negative" | "none"

@dataclass
class OptimizationReport:
    """optimize() 결과."""
    before_weights: dict[str, float]    # 최적화 전 가중치
    after_weights: dict[str, float]     # 최적화 후 가중치
    improvement: str                    # 개선 설명
    pattern: str                        # 탐지된 패턴
    simulation_score: float             # 시뮬레이션 점수 변화
    rolled_back: bool                   # 롤백 여부


# ── F4: 추론 결과 ──

@dataclass
class ReasoningResult:
    """reason() 결과."""
    query: str                          # 추론 질문
    source_memories: list[MemoryItem]   # 소스 기억 목록
    insights: list[str]                 # 도출된 인사이트
    contradictions: list[dict]          # 모순 목록 [{mem_a, mem_b, description}]
    confidence: float                   # 추론 신뢰도
    reasoning_chain: list[str]          # 추론 체인 설명

@dataclass
class Contradiction:
    """모순 탐지 결과."""
    memory_a_id: str
    memory_b_id: str
    description: str
    severity: float                     # 모순 심각도 (0.0~1.0)


# ── F5: 벤치마크 결과 ──

@dataclass
class BenchmarkReport:
    """benchmark() 결과."""
    recall_at_5: float                  # Top-5 리콜 정확도
    recall_at_10: float                 # Top-10 리콜 정확도
    precision_at_5: float               # Top-5 정밀도
    avg_store_latency_ms: float         # 평균 store 지연시간
    avg_recall_latency_ms: float        # 평균 recall 지연시간
    avg_reorbit_latency_ms: float       # 평균 reorbit 지연시간
    memory_usage_mb: float              # 메모리 사용량
    db_size_mb: float                   # DB 파일 크기
    total_memories: int                 # 총 기억 수
    zone_distribution: dict[int, int]   # 존별 분포
    dataset_name: str                   # 데이터셋 이름
    queries_run: int                    # 실행한 쿼리 수

    def to_dict(self) -> dict:
        """JSON 직렬화용."""
        ...

    def to_html(self) -> str:
        """HTML 보고서 생성."""
        ...
```

### 3.2 MemoryItem 확장

```python
@dataclass
class MemoryItem:
    # 기존 필드 (변경 없음)
    id: str
    content: str
    created_at: float
    last_recalled_at: float
    recall_count: int = 0
    arbitrary_importance: float = 0.5
    zone: int = -1
    metadata: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    emotion: EmotionVector | None = None

    # P9 신규 필드 (하위 호환: 기본값 제공)
    content_type: str = "text"          # "text" | "code" | "json" | "structured"
```

### 3.3 SQLite 스키마 변경

```sql
-- 기존 memories 테이블에 컬럼 추가 (ALTER TABLE)
ALTER TABLE memories ADD COLUMN content_type TEXT DEFAULT 'text';

-- 새 테이블: 리콜 이력 (자율 학습용)
CREATE TABLE IF NOT EXISTS recall_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    result_ids TEXT NOT NULL,         -- JSON array of memory IDs
    timestamp REAL NOT NULL,
    feedback TEXT DEFAULT 'none'      -- 'positive' | 'negative' | 'none'
);

-- 새 테이블: 가중치 이력 (롤백용)
CREATE TABLE IF NOT EXISTS weight_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weights TEXT NOT NULL,            -- JSON: {w_recall, w_freshness, ...}
    timestamp REAL NOT NULL,
    reason TEXT DEFAULT ''            -- 'optimize' | 'rollback' | 'manual'
);
```

---

## 4. API Specification

### 4.1 Python API (StellarMemory 클래스 확장)

#### F1: 메타인지 메서드

```python
def introspect(self, topic: str, depth: int = 1) -> IntrospectionResult:
    """주제별 지식 상태 분석.

    Args:
        topic: 분석할 주제 (예: "React 프레임워크")
        depth: 그래프 탐색 깊이 (기본 1홉)

    Returns:
        IntrospectionResult: confidence, coverage, gaps, memory_count, ...
    """

def recall_with_confidence(self, query: str, top_k: int = 5,
                           threshold: float = 0.3) -> ConfidentRecall:
    """신뢰도 점수 포함 리콜.

    Args:
        query: 검색 쿼리
        top_k: 반환할 최대 기억 수
        threshold: 신뢰도 경고 임계값 (이하 시 warning 포함)

    Returns:
        ConfidentRecall: memories, confidence, warning
    """
```

#### F2: 자율 학습 메서드

```python
def optimize(self, min_logs: int = 50) -> OptimizationReport:
    """리콜 패턴 분석 → 가중치 자동 최적화.

    Args:
        min_logs: 최적화에 필요한 최소 리콜 로그 수

    Returns:
        OptimizationReport: before/after weights, improvement, pattern

    Raises:
        ValueError: 리콜 로그가 min_logs 미만일 때
    """

def rollback_weights(self) -> dict[str, float]:
    """마지막 가중치 최적화를 롤백.

    Returns:
        dict: 복원된 가중치
    """
```

#### F3: 멀티모달 store 확장

```python
def store(self, content: str | dict, tags: list[str] | None = None,
          importance: float | None = None, source: str | None = None,
          session_id: str | None = None,
          content_type: str = "text",             # P9 신규
          metadata: dict | None = None) -> str:
    """기억 저장 (content_type 파라미터 추가).

    Args:
        content: 저장할 내용 (str 또는 dict for JSON)
        content_type: "text" | "code" | "json" | "structured"
        metadata: 추가 메타데이터 (code일 때 language 등)
    """
```

#### F4: 추론 메서드

```python
def reason(self, query: str, max_sources: int = 10) -> ReasoningResult:
    """기억 조합 추론.

    Args:
        query: 추론 질문
        max_sources: 소스 기억 최대 수

    Returns:
        ReasoningResult: insights, contradictions, reasoning_chain
    """

def detect_contradictions(self, scope: str | None = None) -> list[Contradiction]:
    """모순 기억 탐지.

    Args:
        scope: 검색 범위 (태그/주제, None이면 전체)

    Returns:
        list[Contradiction]: 발견된 모순 목록
    """
```

#### F5: 벤치마크 메서드

```python
def benchmark(self, queries: int = 100,
              dataset: str = "standard") -> BenchmarkReport:
    """종합 벤치마크 실행.

    Args:
        queries: 실행할 쿼리 수
        dataset: "standard" | "small" | "large" | 사용자 정의 경로

    Returns:
        BenchmarkReport: recall@k, latency, memory usage
    """
```

### 4.2 REST API 확장 (server.py)

| Method | Path | Description | Auth |
|--------|------|-------------|:----:|
| GET | /api/introspect?topic={topic} | 주제별 지식 상태 | Yes |
| GET | /api/recall/confident?query={q} | 신뢰도 포함 리콜 | Yes |
| POST | /api/optimize | 가중치 자동 최적화 | Yes |
| POST | /api/rollback-weights | 가중치 롤백 | Yes |
| POST | /api/reason | 기억 조합 추론 | Yes |
| GET | /api/contradictions | 모순 탐지 | Yes |
| POST | /api/benchmark | 벤치마크 실행 | Yes |

### 4.3 CLI 확장 (cli.py)

```bash
# 메타인지
stellar-memory introspect "React"
stellar-memory recall --confident "Next.js"

# 자율 학습
stellar-memory optimize
stellar-memory rollback-weights

# 벤치마크
stellar-memory benchmark --queries 500 --output report.html
stellar-memory benchmark --dataset large --seed 42
```

### 4.4 MCP 도구 확장 (mcp_server.py)

| 도구 | 설명 |
|------|------|
| `memory_introspect` | 주제별 지식 상태 분석 |
| `memory_recall_confident` | 신뢰도 포함 리콜 |
| `memory_optimize` | 가중치 자동 최적화 |
| `memory_reason` | 기억 추론 |
| `memory_benchmark` | 벤치마크 실행 |

---

## 5. Module Design

### 5.1 F1: metacognition.py

```python
class Introspector:
    """지식 상태 분석기."""

    def __init__(self, stellar: StellarMemory):
        self._stellar = stellar

    def introspect(self, topic: str, depth: int = 1) -> IntrospectionResult:
        """1. topic으로 recall
        2. 결과 기억들의 태그/키워드 수집 → coverage
        3. 그래프에서 관련 노드 중 기억 없는 것 → gaps
        4. confidence 계산"""

    def _calculate_confidence(self, memories, topic) -> float:
        """confidence = α*coverage_ratio + β*avg_freshness + γ*memory_density

        α=0.4, β=0.3, γ=0.3 (기본값)
        coverage_ratio: 관련 태그 중 기억에 존재하는 비율
        avg_freshness: 관련 기억의 평균 신선도 (0~1)
        memory_density: min(memory_count / 10, 1.0)
        """


class ConfidenceScorer:
    """리콜 결과 신뢰도 평가."""

    def score(self, memories: list[MemoryItem], query: str) -> float:
        """리콜 결과의 신뢰도 계산.

        factors:
        - 결과 수 (많을수록 높음, 10개에서 포화)
        - 최고 유사도 (시맨틱 검색 시)
        - 평균 존 번호 (낮을수록 Core에 가까워 신뢰도 높음)
        - 평균 신선도 (높을수록 신뢰도 높음)
        """


class KnowledgeGapDetector:
    """지식 갭 탐지기."""

    def detect_gaps(self, topic: str, coverage: list[str]) -> list[str]:
        """그래프에서 topic 관련 노드 중 기억이 없는 영역 탐지.

        1. topic 키워드로 그래프 이웃 노드 수집
        2. 이웃 노드의 태그/키워드 중 coverage에 없는 것 → gaps
        3. LLM 사용 가능 시: 주제 관련 일반적 하위 주제 생성 → 비교
        """
```

### 5.2 F2: self_learning.py

```python
class PatternCollector:
    """리콜 패턴 수집기."""

    def __init__(self, db_path: str):
        self._db_path = db_path  # recall_logs 테이블 사용

    def log_recall(self, query: str, result_ids: list[str]):
        """리콜 이력 기록."""

    def get_logs(self, limit: int = 1000) -> list[RecallLog]:
        """최근 리콜 이력 조회."""

    def analyze_patterns(self, logs: list[RecallLog]) -> dict:
        """패턴 분석.

        Returns:
            {
                "freshness_preference": float,  # 최근 기억 선호 정도
                "emotion_preference": float,    # 감정적 기억 선호 정도
                "recall_frequency": float,      # 리콜 빈도 (높으면 w_recall 중요)
                "topic_diversity": float,       # 주제 다양성
            }
        """


class WeightOptimizer:
    """기억 함수 가중치 최적화기."""

    def __init__(self, config: MemoryFunctionConfig, db_path: str):
        self._config = config
        self._db_path = db_path  # weight_history 테이블 사용
        self._learning_rate = 0.03  # 보수적 학습률

    def optimize(self, patterns: dict, logs: list[RecallLog]) -> OptimizationReport:
        """패턴 기반 가중치 조정.

        1. 현재 가중치 저장 (weight_history)
        2. 패턴에 따라 가중치 미세 조정:
           - freshness_preference 높음 → w_freshness += learning_rate
           - emotion_preference 높음 → w_emotion += learning_rate
           - 등등
        3. 가중치 합 = 1.0 정규화
        4. 시뮬레이션: 최근 100개 리콜에 대해 새 가중치로 점수 재계산
        5. 개선 시 적용, 아닐 경우 롤백
        """

    def rollback(self) -> dict[str, float]:
        """weight_history에서 이전 가중치 복원."""

    def _simulate(self, weights: dict, logs: list[RecallLog]) -> float:
        """새 가중치로 시뮬레이션 → 평균 순위 점수 반환."""

    def _normalize_weights(self, weights: dict) -> dict:
        """가중치 합 = 1.0으로 정규화."""
```

### 5.3 F3: multimodal.py

```python
from abc import ABC, abstractmethod

class ContentTypeHandler(ABC):
    """콘텐츠 타입 핸들러 추상 클래스."""

    @abstractmethod
    def preprocess(self, content: str | dict) -> str:
        """저장 전 전처리 → 텍스트 변환."""

    @abstractmethod
    def get_metadata(self, content: str | dict) -> dict:
        """타입별 메타데이터 추출."""

    @abstractmethod
    def matches_filter(self, item: MemoryItem, filter_params: dict) -> bool:
        """필터 조건 일치 여부."""


class TextHandler(ContentTypeHandler):
    """기본 텍스트 핸들러 (기존 동작과 동일)."""

    def preprocess(self, content):
        return str(content)

    def get_metadata(self, content):
        return {"word_count": len(str(content).split())}

    def matches_filter(self, item, filter_params):
        return True


class CodeHandler(ContentTypeHandler):
    """코드 기억 핸들러."""

    LANGUAGE_PATTERNS = {
        "python": r"(def |class |import |from .+ import)",
        "javascript": r"(function |const |let |var |=>|require\()",
        "typescript": r"(interface |type |: string|: number)",
        # ... 기타 언어
    }

    def preprocess(self, content):
        return str(content)

    def get_metadata(self, content):
        """언어 감지 + 함수/클래스 이름 추출."""
        language = self._detect_language(str(content))
        return {
            "language": language,
            "functions": self._extract_functions(str(content), language),
            "line_count": len(str(content).splitlines()),
        }

    def _detect_language(self, code: str) -> str:
        """정규식 기반 언어 감지."""

    def _extract_functions(self, code: str, language: str) -> list[str]:
        """함수/클래스 이름 추출."""


class JsonHandler(ContentTypeHandler):
    """JSON/구조화 데이터 핸들러."""

    def preprocess(self, content):
        if isinstance(content, dict):
            import json
            return json.dumps(content, ensure_ascii=False, indent=2)
        return str(content)

    def get_metadata(self, content):
        """스키마 정보 추출."""
        if isinstance(content, dict):
            return {
                "keys": list(content.keys()),
                "types": {k: type(v).__name__ for k, v in content.items()},
            }
        return {}

    def matches_filter(self, item, filter_params):
        """필드 기반 필터링."""


# 핸들러 레지스트리
CONTENT_TYPE_HANDLERS: dict[str, ContentTypeHandler] = {
    "text": TextHandler(),
    "code": CodeHandler(),
    "json": JsonHandler(),
    "structured": JsonHandler(),  # JSON과 동일한 핸들러 재사용
}

def get_handler(content_type: str) -> ContentTypeHandler:
    return CONTENT_TYPE_HANDLERS.get(content_type, TextHandler())
```

### 5.4 F4: reasoning.py

```python
class MemoryReasoner:
    """기억 조합 추론 엔진."""

    def __init__(self, stellar: StellarMemory):
        self._stellar = stellar

    def reason(self, query: str, max_sources: int = 10) -> ReasoningResult:
        """1. recall(query) + graph neighbors → 소스 기억 수집
        2. LLM에 기억 목록 + 질문 전달 → 추론 결과
        3. NullLLM 폴백: 키워드 오버랩 기반 연결
        """

    def _reason_with_llm(self, query: str, memories: list[MemoryItem]) -> list[str]:
        """LLM 기반 추론.

        프롬프트: "다음 기억들을 종합하여 '{query}'에 대한 인사이트를 도출하세요:
        1. {memory_1.content}
        2. {memory_2.content}
        ..."
        """

    def _reason_without_llm(self, query: str, memories: list[MemoryItem]) -> list[str]:
        """규칙 기반 폴백.

        기억 간 공통 키워드 탐지 → "A와 B는 '{keyword}'로 연결됨" 형태
        """


class ContradictionDetector:
    """모순 탐지기."""

    def detect(self, memories: list[MemoryItem]) -> list[Contradiction]:
        """기억 쌍 비교 → 모순 탐지.

        LLM 모드: 기억 쌍을 LLM에 비교 요청
        규칙 모드: 부정어 패턴 탐지 (not, 아닌, 없는 등)
        """

    def _detect_with_llm(self, mem_a: MemoryItem, mem_b: MemoryItem) -> Contradiction | None:
        """LLM 기반 모순 탐지."""

    def _detect_with_rules(self, mem_a: MemoryItem, mem_b: MemoryItem) -> Contradiction | None:
        """규칙 기반 모순 탐지.

        패턴: 동일 주어 + 상반 술어
        예: "A는 B이다" vs "A는 B가 아니다"
        """
```

### 5.5 F5: benchmark.py

```python
class StandardDataset:
    """벤치마크용 표준 데이터셋."""

    DATASETS = {
        "small": 100,    # 100개 기억 + 20개 쿼리
        "standard": 1000, # 1000개 기억 + 100개 쿼리
        "large": 10000,   # 10000개 기억 + 500개 쿼리
    }

    def __init__(self, name: str = "standard", seed: int = 42):
        self._name = name
        self._seed = seed

    def generate_memories(self) -> list[dict]:
        """시드 기반 재현 가능한 기억 생성.

        카테고리: 일상, 업무, 기술, 감정, 코드 (각 20%)
        """

    def generate_queries(self) -> list[dict]:
        """쿼리 + 정답 기억 ID 쌍 생성."""


class MemoryBenchmark:
    """종합 벤치마크 엔진."""

    def __init__(self, stellar: StellarMemory):
        self._stellar = stellar

    def run(self, queries: int = 100, dataset: str = "standard",
            seed: int = 42) -> BenchmarkReport:
        """벤치마크 실행.

        1. StandardDataset 생성 → 기억 저장 (store latency 측정)
        2. 쿼리 실행 → recall latency 측정
        3. recall@k 계산: 상위 k개 결과 중 정답 비율
        4. reorbit 실행 → latency 측정
        5. 메모리/DB 크기 측정
        6. BenchmarkReport 반환
        """

    def _measure_store(self, memories: list[dict]) -> float:
        """store 평균 지연시간 (ms)."""

    def _measure_recall(self, queries: list[dict], k: int) -> tuple[float, float]:
        """(avg_latency_ms, recall_at_k)."""

    def _measure_reorbit(self) -> float:
        """reorbit 평균 지연시간 (ms)."""

    def _get_memory_stats(self) -> dict:
        """메모리/DB 크기, 존별 분포."""
```

---

## 6. Config 확장 (config.py)

```python
# ── P9 Config classes ──

@dataclass
class MetacognitionConfig:
    enabled: bool = False               # 기본 비활성화
    confidence_alpha: float = 0.4       # 커버리지 가중치
    confidence_beta: float = 0.3        # 신선도 가중치
    confidence_gamma: float = 0.3       # 밀도 가중치
    low_confidence_threshold: float = 0.3  # 경고 임계값
    use_llm_for_gaps: bool = False      # LLM으로 갭 분석 (선택)

@dataclass
class SelfLearningConfig:
    enabled: bool = False               # 기본 비활성화
    learning_rate: float = 0.03         # 보수적 학습률
    min_logs: int = 50                  # 최적화 시작 최소 로그 수
    max_delta: float = 0.1             # 가중치 최대 변화량
    auto_optimize: bool = False         # 자동 최적화 (False=수동만)
    auto_optimize_interval: int = 1000  # 자동 최적화 주기 (리콜 횟수)

@dataclass
class MultimodalConfig:
    enabled: bool = False               # 기본 비활성화
    code_language_detect: bool = True   # 코드 언어 자동 감지
    json_schema_extract: bool = True    # JSON 스키마 추출

@dataclass
class ReasoningConfig:
    enabled: bool = False               # 기본 비활성화
    max_sources: int = 10               # 추론 시 최대 소스 기억 수
    use_llm: bool = True                # LLM 추론 (False면 규칙 기반만)
    contradiction_check: bool = True    # 모순 탐지 활성화

@dataclass
class BenchmarkConfig:
    default_queries: int = 100          # 기본 쿼리 수
    default_dataset: str = "standard"   # 기본 데이터셋
    default_seed: int = 42              # 기본 시드
    output_format: str = "json"         # "json" | "html" | "both"


# StellarConfig 확장
@dataclass
class StellarConfig:
    # ... 기존 필드 유지 ...

    # P9 fields
    metacognition: MetacognitionConfig = field(default_factory=MetacognitionConfig)
    self_learning: SelfLearningConfig = field(default_factory=SelfLearningConfig)
    multimodal: MultimodalConfig = field(default_factory=MultimodalConfig)
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)
```

---

## 7. Error Handling

### 7.1 에러 유형

| 에러 | 원인 | 처리 |
|------|------|------|
| `InsufficientDataError` | optimize() 호출 시 리콜 로그 < min_logs | ValueError 발생, 최소 로그 수 안내 |
| 메타인지 빈 결과 | introspect 주제에 관련 기억 없음 | confidence=0.0, gaps=[topic] 반환 |
| 추론 LLM 실패 | LLM API 호출 실패 | 규칙 기반 폴백 자동 전환 |
| 벤치마크 타임아웃 | 대규모 데이터셋 + 느린 임베딩 | 진행률 콜백 + 부분 결과 반환 |
| 가중치 범위 초과 | optimize 후 가중치 < 0.01 또는 > 0.8 | 자동 클램핑 + 경고 |
| content_type 미인식 | 지원하지 않는 content_type | TextHandler 폴백 + 경고 로그 |

### 7.2 롤백 안전성

```python
# optimize() 내부 흐름
def optimize(self):
    # 1. 현재 가중치를 weight_history에 저장
    self._save_weights(self._config, reason="pre_optimize")

    try:
        # 2. 새 가중치 계산
        new_weights = self._calculate_new_weights(patterns)

        # 3. 시뮬레이션
        old_score = self._simulate(current_weights, logs)
        new_score = self._simulate(new_weights, logs)

        if new_score > old_score:
            # 4a. 개선됨 → 적용
            self._apply_weights(new_weights)
            return OptimizationReport(rolled_back=False, ...)
        else:
            # 4b. 개선 안됨 → 적용하지 않음
            return OptimizationReport(rolled_back=True, ...)

    except Exception:
        # 5. 에러 → 이전 가중치 복원
        self._rollback()
        raise
```

---

## 8. Test Plan

### 8.1 Test Scope

| Type | Target | Tool | 예상 수 |
|------|--------|------|:-------:|
| Unit Test | metacognition.py | pytest | ~20 |
| Unit Test | self_learning.py | pytest | ~15 |
| Unit Test | multimodal.py | pytest | ~15 |
| Unit Test | reasoning.py | pytest | ~15 |
| Unit Test | benchmark.py | pytest | ~15 |
| Integration | StellarMemory P9 API | pytest | ~10 |

### 8.2 Test Cases (Key)

**F1: 메타인지**
- [ ] introspect 빈 DB → confidence=0.0, gaps=[topic]
- [ ] introspect 관련 기억 있음 → confidence > 0, coverage 비어있지 않음
- [ ] recall_with_confidence 낮은 신뢰도 → warning 포함
- [ ] recall_with_confidence 높은 신뢰도 → warning=None
- [ ] coverage 정확성 (태그와 일치)
- [ ] zone_distribution 정확성

**F2: 자율 학습**
- [ ] PatternCollector log_recall + get_logs 왕복
- [ ] analyze_patterns → freshness/emotion preference 계산
- [ ] optimize 성공 → 가중치 변경 + 정규화 합=1.0
- [ ] optimize 실패 → 롤백 + rolled_back=True
- [ ] min_logs 미달 → ValueError
- [ ] rollback_weights → weight_history에서 복원
- [ ] 가중치 범위 클램핑 (0.01~0.8)

**F3: 멀티모달**
- [ ] store(content_type="text") → 기존과 동일
- [ ] store(content_type="code") → 언어 감지 메타데이터
- [ ] store(content_type="json", content=dict) → JSON 직렬화
- [ ] recall(content_type="code") → 코드 타입만 필터
- [ ] 미지원 content_type → TextHandler 폴백

**F4: 추론**
- [ ] reason 기본 동작 → insights 비어있지 않음
- [ ] reason LLM 없음 → 규칙 기반 폴백
- [ ] detect_contradictions 모순 없음 → 빈 리스트
- [ ] detect_contradictions 모순 있음 → Contradiction 반환
- [ ] reasoning_chain 소스 추적 정확성

**F5: 벤치마크**
- [ ] benchmark("small") → BenchmarkReport 모든 필드
- [ ] 동일 시드 → 동일 결과 (재현성)
- [ ] recall_at_5 범위 0.0~1.0
- [ ] latency > 0
- [ ] to_dict() JSON 직렬화 가능
- [ ] zone_distribution 합 = total_memories

---

## 9. Implementation Guide

### 9.1 File Structure

```
stellar_memory/                    # 기존 유지 + 신규 5파일
├── metacognition.py               # P9-F1: 메타인지 엔진 (신규)
├── self_learning.py               # P9-F2: 자율 학습 (신규)
├── multimodal.py                  # P9-F3: 멀티모달 핸들러 (신규)
├── reasoning.py                   # P9-F4: 추론 엔진 (신규)
├── benchmark.py                   # P9-F5: 벤치마크 (신규)
├── config.py                      # 수정: P9 Config 5개 추가
├── models.py                      # 수정: P9 모델 7개 추가
├── stellar.py                     # 수정: P9 메서드 7개 추가
├── server.py                      # 수정: P9 엔드포인트 7개 추가
├── cli.py                         # 수정: P9 명령 5개 추가
└── mcp_server.py                  # 수정: P9 도구 5개 추가

tests/
├── test_p9_metacognition.py       # ~20 tests (신규)
├── test_p9_self_learning.py       # ~15 tests (신규)
├── test_p9_multimodal.py          # ~15 tests (신규)
├── test_p9_reasoning.py           # ~15 tests (신규)
└── test_p9_benchmark.py           # ~15 tests (신규)
```

### 9.2 Implementation Order

```
Phase 1: 기반 작업
  1. [ ] config.py - P9 Config 5개 추가
  2. [ ] models.py - P9 모델 7개 추가
  3. [ ] MemoryItem에 content_type 필드 추가
  4. [ ] SQLite 스키마 마이그레이션 (recall_logs, weight_history)

Phase 2: F5 벤치마크 (다른 기능 검증 도구)
  5. [ ] benchmark.py - StandardDataset + MemoryBenchmark
  6. [ ] stellar.py - benchmark() 메서드 추가
  7. [ ] tests/test_p9_benchmark.py

Phase 3: F1 메타인지
  8. [ ] metacognition.py - Introspector + ConfidenceScorer + GapDetector
  9. [ ] stellar.py - introspect() + recall_with_confidence() 추가
  10. [ ] tests/test_p9_metacognition.py

Phase 4: F3 멀티모달
  11. [ ] multimodal.py - ContentTypeHandler + Code/Json/Text Handler
  12. [ ] stellar.py - store() content_type 파라미터 연동
  13. [ ] tests/test_p9_multimodal.py

Phase 5: F2 자율 학습
  14. [ ] self_learning.py - PatternCollector + WeightOptimizer
  15. [ ] stellar.py - optimize() + rollback_weights() + recall 로깅 연동
  16. [ ] tests/test_p9_self_learning.py

Phase 6: F4 추론
  17. [ ] reasoning.py - MemoryReasoner + ContradictionDetector
  18. [ ] stellar.py - reason() + detect_contradictions() 추가
  19. [ ] tests/test_p9_reasoning.py

Phase 7: 통합 + API 확장
  20. [ ] server.py - P9 REST API 7개 엔드포인트
  21. [ ] cli.py - P9 CLI 5개 명령
  22. [ ] mcp_server.py - P9 MCP 도구 5개
  23. [ ] 통합 테스트 + 하위 호환성 검증
```

---

## 10. EventBus 연동

P9 기능별 발행할 이벤트:

| 이벤트 | 발행 시점 | 데이터 |
|--------|----------|--------|
| `introspect` | introspect() 호출 시 | {topic, confidence} |
| `optimize` | optimize() 완료 시 | {before, after, rolled_back} |
| `reason` | reason() 완료 시 | {query, insight_count} |
| `contradiction_found` | 모순 탐지 시 | {mem_a_id, mem_b_id, severity} |
| `benchmark_complete` | benchmark() 완료 시 | {recall_at_5, avg_latency} |

---

## 11. 하위 호환성 보장

| 항목 | 전략 |
|------|------|
| MemoryItem.content_type | 기본값 "text" → 기존 코드 영향 없음 |
| StellarConfig.metacognition | enabled=False 기본 → 비활성 상태 |
| StellarConfig.self_learning | enabled=False 기본 → 비활성 상태 |
| StellarConfig.multimodal | enabled=False 기본 → 비활성 상태 |
| StellarConfig.reasoning | enabled=False 기본 → 비활성 상태 |
| store() content_type 파라미터 | 기본값 "text" → 기존 호출 변경 불필요 |
| recall_logs 테이블 | IF NOT EXISTS → 기존 DB에 안전하게 추가 |
| weight_history 테이블 | IF NOT EXISTS → 기존 DB에 안전하게 추가 |
| 신규 메서드 | 기존 메서드와 이름 충돌 없음 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | 초안 - P9 고급 인지 & 자율 학습 Design | Stellar Memory Team |
