# celestial-engine-plugin Design Document

> **Summary**: celestial_engine 패키지 정비 + AI 미들웨어 + 벡터 검색 + 자동 기억 기능 설계
>
> **Project**: stellar-memory
> **Version**: v1.1.0 -> v2.0.0
> **Author**: Claude
> **Date**: 2026-02-20
> **Status**: Draft
> **Planning Doc**: [celestial-engine-plugin.plan.md](../../01-plan/features/celestial-engine-plugin.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. `celestial_engine`을 `stellar-memory` PyPI 패키지에 포함하여 `pip install stellar-memory`로 사용 가능하게
2. OpenAI/Anthropic SDK를 래핑하는 `MemoryMiddleware`로 3줄 코드 기억 삽입
3. 기존 `search()`에 벡터 유사도 검색을 실제 구현하여 RAG 품질 향상
4. 대화에서 중요 정보를 자동 추출/저장하는 `AutoMemory` 제공
5. 용도별 기억 함수 프리셋 (Conversational, Factual, Research)

### 1.2 Design Principles

- **Zero-dependency core**: `celestial_engine` 핵심은 표준 라이브러리만 사용
- **Optional integration**: OpenAI/Anthropic SDK는 런타임 import (선택적 의존성)
- **Backward compatibility**: 기존 API (`store`, `recall`, `rebalance`, `stats`, `close`) 유지
- **Layered extension**: 미들웨어는 `CelestialMemory` 위에 쌓이는 별도 레이어

---

## 2. Architecture

### 2.1 Component Diagram

```
사용자 AI 애플리케이션
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                  MemoryMiddleware                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ OpenAIWrapper │  │AnthropicWrap │  │ContextBuild│ │
│  │ .chat.compl() │  │ .messages()  │  │ er(memories │ │
│  │              │  │              │  │  →prompt)   │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         └────────┬────────┘                │        │
│                  ▼                         │        │
│  ┌──────────────────────────────────────┐  │        │
│  │           AutoMemory                  │◄─┘        │
│  │ process_turn(user_msg, ai_response)  │           │
│  │ → extract facts → dedup → store      │           │
│  └──────────────┬───────────────────────┘           │
│                  ▼                                   │
│  ┌──────────────────────────────────────┐           │
│  │         CelestialMemory              │           │
│  │  store() / recall() / rebalance()    │           │
│  │  ┌────────────────────────────────┐  │           │
│  │  │  MemoryFunction (I=wR+wF+wA+wC)│  │           │
│  │  │  MemoryPresets                  │  │           │
│  │  └────────────────────────────────┘  │           │
│  │  ┌────────────────────────────────┐  │           │
│  │  │  ZoneManager (5-zone system)   │  │           │
│  │  │  ☀Core→Inner→Outer→Belt→Cloud │  │           │
│  │  └────────────────────────────────┘  │           │
│  │  ┌────────────────────────────────┐  │           │
│  │  │  Storage (InMemory / SQLite)   │  │           │
│  │  │  + Vector cosine search        │  │           │
│  │  └────────────────────────────────┘  │           │
│  └──────────────────────────────────────┘           │
└──────────────────────────────────────────────────────┘
    │                     │
    ▼                     ▼
 OpenAI API          Anthropic API
```

### 2.2 Data Flow

#### Middleware Wrap Flow (사용자 메시지 → AI 응답)
```
1. user message → MemoryMiddleware
2. MemoryMiddleware → CelestialMemory.recall(user_message)
3. recalled memories → ContextBuilder.build(memories)
4. system_prompt + memory_context → AI API call
5. AI response received
6. AutoMemory.process_turn(user_message, ai_response)
7. extracted facts → CelestialMemory.store() (각각 중요도 평가)
8. response → 사용자에게 반환
```

#### Vector Search Flow (recall 시)
```
1. query → embed_fn(query) → query_embedding
2. storage.search(query, limit, query_embedding)
3. if query_embedding exists:
   → cosine_similarity(item.embedding, query_embedding) for each item
   → sort by similarity DESC
   → return top-limit
4. else:
   → fallback to text substring search
   → sort by total_score DESC
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| `MemoryMiddleware` | `CelestialMemory`, `AutoMemory`, `ContextBuilder` | 미들웨어 코어 |
| `OpenAIWrapper` | `MemoryMiddleware`, `openai` (optional) | OpenAI SDK 래핑 |
| `AnthropicWrapper` | `MemoryMiddleware`, `anthropic` (optional) | Anthropic SDK 래핑 |
| `AutoMemory` | `CelestialMemory`, `ImportanceEvaluator` | 대화 자동 기억 |
| `ContextBuilder` | `CelestialItem` | 기억 → 프롬프트 변환 |
| `MemoryPresets` | `MemoryFunctionConfig` | 프리셋 설정 |
| Vector search | `math` (stdlib) | 코사인 유사도 계산 |

---

## 3. Data Model

### 3.1 기존 모델 (변경 없음)

```python
# celestial_engine/models.py - 변경 없음
@dataclass
class CelestialItem:
    id: str
    content: str
    created_at: float
    last_recalled_at: float
    recall_count: int = 0
    arbitrary_importance: float = 0.5
    zone: int = -1
    metadata: dict
    embedding: list[float] | None = None
    total_score: float = 0.0
```

### 3.2 AutoMemory 추출 결과 (신규)

```python
# celestial_engine/auto_memory.py
@dataclass
class ExtractedFact:
    content: str           # 추출된 사실
    importance: float      # 중요도 (0.0~1.0)
    category: str          # "personal" | "factual" | "preference" | "event"
```

---

## 4. Feature Specifications

### 4.1 F1: 패키지 정비 및 배포 준비

#### 4.1.1 pyproject.toml 변경

```toml
# 변경 항목
[project]
version = "2.0.0"

[tool.setuptools.packages.find]
include = ["stellar_memory*", "celestial_engine*"]
```

**변경 파일**: `pyproject.toml`
- `version` 필드: `"1.0.0"` → `"2.0.0"`
- `packages.find.include`에 `"celestial_engine*"` 추가

#### 4.1.2 __init__.py 공개 API 정리

```python
# celestial_engine/__init__.py - 추가할 export
from .middleware import MemoryMiddleware      # F2 신규
from .auto_memory import AutoMemory           # F4 신규
from .memory_function import MemoryPresets    # F5 신규

__version__ = "2.0.0"
```

**변경 파일**: `celestial_engine/__init__.py`
- `MemoryMiddleware`, `AutoMemory`, `MemoryPresets` export 추가
- `__version__` 상수 추가

---

### 4.2 F2: AI 미들웨어 레이어

**신규 파일**: `celestial_engine/middleware.py`

#### 4.2.1 ContextBuilder 클래스

```python
class ContextBuilder:
    """검색된 기억을 시스템 프롬프트용 텍스트로 포매팅"""

    DEFAULT_TEMPLATE = (
        "You have the following memories from previous conversations:\n"
        "{memories}\n"
        "Use these memories naturally when relevant."
    )

    def __init__(self, template: str | None = None, max_memories: int = 5):
        self.template = template or self.DEFAULT_TEMPLATE
        self.max_memories = max_memories

    def build(self, memories: list[CelestialItem]) -> str:
        """기억 리스트를 시스템 프롬프트 문자열로 변환"""
        if not memories:
            return ""
        items = memories[:self.max_memories]
        lines = []
        for i, mem in enumerate(items, 1):
            zone_label = ["Core", "Inner", "Outer", "Belt", "Cloud"][mem.zone] if 0 <= mem.zone <= 4 else "Unknown"
            lines.append(f"- [{zone_label}] {mem.content}")
        memory_text = "\n".join(lines)
        return self.template.format(memories=memory_text)
```

**메서드 시그니처**: `build(memories: list[CelestialItem]) -> str`
**파라미터**: `template: str | None`, `max_memories: int = 5`

#### 4.2.2 MemoryMiddleware 클래스

```python
class MemoryMiddleware:
    """AI SDK에 기억 능력을 주입하는 미들웨어"""

    def __init__(
        self,
        memory: CelestialMemory,
        auto_memory: AutoMemory | None = None,
        context_builder: ContextBuilder | None = None,
        recall_limit: int = 5,
    ):
        self.memory = memory
        self.auto_memory = auto_memory or AutoMemory(memory)
        self.context_builder = context_builder or ContextBuilder()
        self.recall_limit = recall_limit

    def recall_context(self, query: str) -> str:
        """쿼리로 기억 검색 → 시스템 프롬프트 텍스트 반환"""
        memories = self.memory.recall(query, limit=self.recall_limit)
        return self.context_builder.build(memories)

    def save_interaction(self, user_msg: str, ai_response: str) -> list[CelestialItem]:
        """대화 턴을 분석하여 중요한 사실을 기억에 저장"""
        return self.auto_memory.process_turn(user_msg, ai_response)

    def wrap_openai(self, client) -> "OpenAIWrapper":
        """OpenAI 클라이언트를 기억 미들웨어로 래핑"""
        return OpenAIWrapper(client, self)

    def wrap_anthropic(self, client) -> "AnthropicWrapper":
        """Anthropic 클라이언트를 기억 미들웨어로 래핑"""
        return AnthropicWrapper(client, self)
```

**메서드 시그니처**:
- `recall_context(query: str) -> str`
- `save_interaction(user_msg: str, ai_response: str) -> list[CelestialItem]`
- `wrap_openai(client) -> OpenAIWrapper`
- `wrap_anthropic(client) -> AnthropicWrapper`

#### 4.2.3 OpenAIWrapper 클래스

```python
class OpenAIWrapper:
    """OpenAI 클라이언트 래퍼 - chat.completions.create() 가로채기"""

    def __init__(self, client, middleware: MemoryMiddleware):
        self._client = client
        self._middleware = middleware
        self.chat = _OpenAIChatProxy(client, middleware)

class _OpenAIChatProxy:
    def __init__(self, client, middleware: MemoryMiddleware):
        self._client = client
        self._middleware = middleware
        self.completions = _OpenAICompletionsProxy(client, middleware)

class _OpenAICompletionsProxy:
    def __init__(self, client, middleware: MemoryMiddleware):
        self._client = client
        self._middleware = middleware

    def create(self, **kwargs):
        """chat.completions.create()를 가로채서 기억 주입"""
        messages = list(kwargs.get("messages", []))

        # 1. 마지막 user 메시지에서 쿼리 추출
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_msg = msg.get("content", "")
                break

        # 2. 기억 검색 → 시스템 프롬프트 주입
        if user_msg:
            memory_context = self._middleware.recall_context(user_msg)
            if memory_context:
                # 기존 system 메시지에 추가 또는 새로 생성
                if messages and messages[0].get("role") == "system":
                    messages[0] = {
                        "role": "system",
                        "content": messages[0]["content"] + "\n\n" + memory_context,
                    }
                else:
                    messages.insert(0, {"role": "system", "content": memory_context})

        # 3. 원본 API 호출
        kwargs["messages"] = messages
        response = self._client.chat.completions.create(**kwargs)

        # 4. 대화 저장 (비동기적이지 않으나, 간단함 우선)
        if user_msg and response.choices:
            ai_response = response.choices[0].message.content or ""
            self._middleware.save_interaction(user_msg, ai_response)

        return response
```

**핵심 동작**:
1. `messages`에서 마지막 `user` 메시지 추출
2. `recall_context(user_msg)` → 관련 기억 검색
3. 시스템 프롬프트에 기억 컨텍스트 주입 (기존 system 메시지에 append, 없으면 insert)
4. 원본 `client.chat.completions.create(**kwargs)` 호출
5. 응답 수신 후 `save_interaction(user_msg, ai_response)` → 자동 기억 저장

#### 4.2.4 AnthropicWrapper 클래스

```python
class AnthropicWrapper:
    """Anthropic 클라이언트 래퍼 - messages.create() 가로채기"""

    def __init__(self, client, middleware: MemoryMiddleware):
        self._client = client
        self._middleware = middleware
        self.messages = _AnthropicMessagesProxy(client, middleware)

class _AnthropicMessagesProxy:
    def __init__(self, client, middleware: MemoryMiddleware):
        self._client = client
        self._middleware = middleware

    def create(self, **kwargs):
        """messages.create()를 가로채서 기억 주입"""
        messages = list(kwargs.get("messages", []))
        system = kwargs.get("system", "")

        # 1. 마지막 user 메시지에서 쿼리 추출
        user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    # content block 형태인 경우
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            user_msg = block.get("text", "")
                            break
                else:
                    user_msg = content
                break

        # 2. 기억 검색 → system 프롬프트에 주입
        if user_msg:
            memory_context = self._middleware.recall_context(user_msg)
            if memory_context:
                if system:
                    system = system + "\n\n" + memory_context
                else:
                    system = memory_context
                kwargs["system"] = system

        # 3. 원본 API 호출
        kwargs["messages"] = messages
        response = self._client.messages.create(**kwargs)

        # 4. 대화 저장
        if user_msg and response.content:
            ai_text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    ai_text_parts.append(block.text)
            ai_response = "\n".join(ai_text_parts)
            self._middleware.save_interaction(user_msg, ai_response)

        return response
```

**Anthropic 특이사항**:
- `system` 파라미터가 `messages`와 분리됨 (OpenAI와 다른 구조)
- `content`가 `list[ContentBlock]` 형태일 수 있음 → 텍스트 블록 추출 필요
- 응답 `content`도 `list[ContentBlock]` → `.text` 추출

---

### 4.3 F3: 벡터 검색 강화

#### 4.3.1 InMemoryStorage 벡터 검색

**변경 파일**: `celestial_engine/storage/memory.py`

`search()` 메서드 변경:

```python
def search(self, query: str, limit: int = 5,
           query_embedding: list[float] | None = None) -> list[CelestialItem]:
    if query_embedding:
        # 벡터 유사도 검색
        scored = []
        for item in self._items.values():
            if item.embedding:
                sim = _cosine_similarity(item.embedding, query_embedding)
                scored.append((item, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:limit]]
    else:
        # 기존 텍스트 검색 (폴백)
        matched = [item for item in self._items.values()
                   if query.lower() in item.content.lower()]
        matched.sort(key=lambda x: x.total_score, reverse=True)
        return matched[:limit]
```

**모듈 레벨 헬퍼 함수 추가**:

```python
import math

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도 계산"""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

#### 4.3.2 SqliteStorage 벡터 검색

**변경 파일**: `celestial_engine/storage/sqlite.py`

`search()` 메서드 변경:

```python
def search(self, query: str, limit: int = 5,
           query_embedding: list[float] | None = None) -> list[CelestialItem]:
    with self._lock:
        if query_embedding:
            # 모든 아이템 로드 후 벡터 유사도 계산
            cursor = self._conn.execute(
                f"SELECT * FROM {self._table} WHERE embedding IS NOT NULL"
            )
            rows = cursor.fetchall()
            scored = []
            for row in rows:
                item = self._row_to_item(row)
                if item and item.embedding:
                    sim = _cosine_similarity(item.embedding, query_embedding)
                    scored.append((item, sim))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [item for item, _ in scored[:limit]]
        else:
            # 기존 LIKE 검색 (폴백)
            cursor = self._conn.execute(
                f"SELECT * FROM {self._table} WHERE content LIKE ? "
                f"ORDER BY total_score DESC LIMIT ?",
                (f"%{query}%", limit),
            )
            return [self._row_to_item(row) for row in cursor.fetchall()
                    if self._row_to_item(row)]
```

**모듈 레벨 헬퍼 함수 추가** (memory.py와 동일):

```python
import math

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

> **설계 결정**: `_cosine_similarity`를 각 storage 파일에 중복 정의하는 이유:
> - 표준 라이브러리(`math`)만 사용하므로 2-3줄 함수
> - storage 모듈이 다른 모듈에 의존하지 않도록 독립성 유지
> - `memory_function.py`의 `_context_score()`에도 동일 로직이 있지만, 레이어 간 의존성 최소화 원칙

---

### 4.4 F4: 대화 자동 기억 (AutoMemory)

**신규 파일**: `celestial_engine/auto_memory.py`

#### 4.4.1 ExtractedFact 모델

```python
@dataclass
class ExtractedFact:
    content: str
    importance: float
    category: str  # "personal" | "factual" | "preference" | "event"
```

#### 4.4.2 AutoMemory 클래스

```python
class AutoMemory:
    """대화에서 중요한 정보를 자동 추출하여 저장"""

    # 카테고리별 키워드 패턴
    PERSONAL_PATTERNS = [
        r"(?:my |i am |i'm |i have |내 |제 |나는 )",
        r"(?:name is |이름은 |called )",
    ]
    PREFERENCE_PATTERNS = [
        r"(?:i (?:like|love|prefer|hate|dislike) )",
        r"(?:좋아하|싫어하|선호하)",
        r"(?:favorite |favourite )",
    ]
    EVENT_PATTERNS = [
        r"(?:tomorrow |next |on \w+day |deadline |meeting )",
        r"(?:내일 |다음 |마감 |회의 |약속 )",
    ]

    SIMILARITY_THRESHOLD = 0.85  # 중복 판단 임계값

    def __init__(
        self,
        memory: "CelestialMemory",
        evaluator: ImportanceEvaluator | None = None,
        min_importance: float = 0.3,
    ):
        self._memory = memory
        self._evaluator = evaluator or RuleBasedEvaluator()
        self._min_importance = min_importance

    def process_turn(
        self, user_msg: str, ai_response: str
    ) -> list[CelestialItem]:
        """대화 턴을 분석하여 중요한 사실을 추출 및 저장"""
        # 1. 사실 추출
        facts = self._extract_facts(user_msg, ai_response)

        # 2. 중요도 필터링
        facts = [f for f in facts if f.importance >= self._min_importance]

        # 3. 중복 검사 및 저장
        stored = []
        for fact in facts:
            if not self._is_duplicate(fact.content):
                item = self._memory.store(
                    content=fact.content,
                    importance=fact.importance,
                    metadata={"category": fact.category, "auto": True},
                )
                stored.append(item)

        return stored

    def _extract_facts(
        self, user_msg: str, ai_response: str
    ) -> list[ExtractedFact]:
        """대화에서 저장할 사실 추출"""
        facts = []
        combined = f"{user_msg} {ai_response}"

        # 문장 단위 분석
        sentences = re.split(r"[.!?\n]+", user_msg)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            category = self._categorize(sentence)
            importance = self._evaluator.evaluate(sentence)

            if importance >= self._min_importance:
                facts.append(ExtractedFact(
                    content=sentence,
                    importance=importance,
                    category=category,
                ))

        return facts

    def _categorize(self, text: str) -> str:
        """텍스트를 카테고리로 분류"""
        text_lower = text.lower()
        for pattern in self.PERSONAL_PATTERNS:
            if re.search(pattern, text_lower):
                return "personal"
        for pattern in self.PREFERENCE_PATTERNS:
            if re.search(pattern, text_lower):
                return "preference"
        for pattern in self.EVENT_PATTERNS:
            if re.search(pattern, text_lower):
                return "event"
        return "factual"

    def _is_duplicate(self, content: str) -> bool:
        """기존 기억과 유사도 비교하여 중복 판단"""
        existing = self._memory.recall(content, limit=3)
        for item in existing:
            # 임베딩 기반 유사도가 있으면 사용
            if item.embedding and self._memory._embed_fn:
                query_emb = self._memory._embed_fn(content)
                sim = _text_similarity(content, item.content)
                if sim >= self.SIMILARITY_THRESHOLD:
                    return True
            else:
                # 텍스트 기반 유사도 폴백
                sim = _text_similarity(content, item.content)
                if sim >= self.SIMILARITY_THRESHOLD:
                    return True
        return False
```

**모듈 레벨 헬퍼**:

```python
def _text_similarity(a: str, b: str) -> float:
    """간단한 문자열 유사도 (Jaccard similarity on words)"""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)
```

---

### 4.5 F5: 기억 함수 프리셋

**변경 파일**: `celestial_engine/memory_function.py`

```python
class MemoryPresets:
    """용도별 기억 함수 가중치 프리셋"""

    CONVERSATIONAL = MemoryFunctionConfig(
        w_recall=0.20,
        w_freshness=0.35,
        w_arbitrary=0.25,
        w_context=0.20,
    )
    """대화형: 최근 대화 중시, 오래된 기억은 빠르게 잊음"""

    FACTUAL = MemoryFunctionConfig(
        w_recall=0.30,
        w_freshness=0.15,
        w_arbitrary=0.35,
        w_context=0.20,
    )
    """사실 기반: 자주 참조되고 중요한 정보 우선, 시간 덜 민감"""

    RESEARCH = MemoryFunctionConfig(
        w_recall=0.15,
        w_freshness=0.20,
        w_arbitrary=0.25,
        w_context=0.40,
    )
    """연구용: 문맥 유사도 최우선, 관련 정보 클러스터링에 유리"""
```

**가중치 합계 검증**: 모든 프리셋은 `w_recall + w_freshness + w_arbitrary + w_context = 1.0`

---

## 5. Design Decisions

### 5.1 Key Decisions

| Decision | Selected | Alternatives | Rationale |
|----------|----------|-------------|-----------|
| 미들웨어 패턴 | Proxy wrapper (SDK 메서드 가로채기) | Callback hook, Decorator | OpenAI/Anthropic 공식 SDK와 동일한 호출 방식 유지 |
| 벡터 검색 | Python 코사인 유사도 (stdlib math) | numpy, faiss, annoy | Zero-dependency 원칙 유지. 소규모 데이터셋에 충분 |
| 자동 기억 추출 | 규칙 기반 패턴 매칭 | LLM 기반 추출, NER | 외부 의존성 없음. LLM evaluator와 결합하여 확장 가능 |
| 중복 감지 | Jaccard similarity (단어 기반) | 임베딩 코사인, MinHash | 간단하고 빠름. 임베딩 있으면 더 정확한 방법 사용 |
| 프리셋 구현 | 클래스 변수 (class-level constants) | JSON 파일, 팩토리 함수 | 가장 간단, IDE 자동완성 지원 |
| `_cosine_similarity` 위치 | 각 storage 파일에 중복 정의 | 공용 utils 모듈 | 레이어 독립성 유지, 함수가 매우 짧음 (5줄) |

### 5.2 Proxy Wrapper 구조 (F2 상세)

OpenAI SDK의 `client.chat.completions.create()`를 가로채기 위해 3단 프록시 구조:

```
OpenAIWrapper                  → client 대체
  └─ .chat                     → _OpenAIChatProxy
       └─ .completions         → _OpenAICompletionsProxy
            └─ .create(**kw)   → 기억 주입 + 원본 호출 + 대화 저장
```

Anthropic은 더 단순:
```
AnthropicWrapper               → client 대체
  └─ .messages                 → _AnthropicMessagesProxy
       └─ .create(**kw)        → 기억 주입 + 원본 호출 + 대화 저장
```

### 5.3 인터페이스 변경 규칙

- `ZoneStorage.search()`: 시그니처 변경 없음 (`query_embedding` 파라미터 이미 존재)
- `CelestialMemory.__init__()`: 변경 없음
- `CelestialMemory.store()` / `recall()`: 변경 없음
- `MemoryFunctionConfig`: 변경 없음 (프리셋은 기존 클래스의 인스턴스)
- 모든 변경은 **기존 코드에 추가**이며, 기존 API 파괴 없음

---

## 6. Error Handling

### 6.1 미들웨어 에러 전략

| 상황 | 처리 | 사용자 영향 |
|------|------|------------|
| `recall()` 실패 (DB 에러) | 빈 기억으로 진행 (no injection) | 기억 없이 응답, 기능 저하 허용 |
| `store()` 실패 (저장 에러) | 로깅만, 응답은 정상 반환 | 이번 대화 기억 안 됨 |
| OpenAI/Anthropic SDK 미설치 | `wrap_openai()` 호출 시 `ImportError` 발생 | 명확한 에러 메시지 |
| 임베딩 함수 실패 | `embed_fn` 결과 None → 텍스트 검색 폴백 | 검색 품질 저하 |
| AutoMemory 추출 실패 | 빈 리스트 반환, 저장 스킵 | 이번 턴 자동 기억 안 됨 |

### 6.2 래퍼 SDK Import 패턴

```python
# middleware.py 상단
# OpenAI/Anthropic은 런타임에만 import (선택적 의존성)

class OpenAIWrapper:
    def __init__(self, client, middleware):
        try:
            import openai  # noqa: F401 - 존재 확인만
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAI integration. "
                "Install with: pip install stellar-memory[openai]"
            )
        self._client = client
        ...
```

---

## 7. Security Considerations

- [x] 사용자 API 키가 미들웨어를 통과하지만 저장/로깅하지 않음
- [x] `AutoMemory`가 AI 응답 내용을 저장하므로, 민감 정보 필터링은 사용자 책임으로 문서화
- [x] SQLite 검색에서 SQL Injection 없음 (파라미터 바인딩 사용 중)
- [x] `_cosine_similarity` 연산에 DoS 위험 없음 (벡터 크기 제한은 사용자 임베딩 함수에 의존)

---

## 8. Test Plan

### 8.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| Unit Test | `_cosine_similarity`, `ContextBuilder`, `MemoryPresets` | pytest |
| Unit Test | `AutoMemory._extract_facts()`, `_categorize()`, `_is_duplicate()` | pytest |
| Integration Test | `MemoryMiddleware` + `CelestialMemory` 조합 | pytest |
| Mock Test | `OpenAIWrapper`, `AnthropicWrapper` (SDK mock) | pytest + unittest.mock |

### 8.2 Test Cases (Key)

- [ ] `_cosine_similarity([1,0], [1,0])` == 1.0
- [ ] `_cosine_similarity([1,0], [0,1])` == 0.0
- [ ] `_cosine_similarity([], [])` == 0.0
- [ ] `ContextBuilder.build([])` == `""`
- [ ] `ContextBuilder.build([item])` includes item.content
- [ ] `MemoryPresets.CONVERSATIONAL` weights sum to 1.0
- [ ] `MemoryPresets.FACTUAL` weights sum to 1.0
- [ ] `MemoryPresets.RESEARCH` weights sum to 1.0
- [ ] `AutoMemory._categorize("My name is Alice")` == `"personal"`
- [ ] `AutoMemory._categorize("I like Python")` == `"preference"`
- [ ] `AutoMemory._categorize("Meeting tomorrow")` == `"event"`
- [ ] `AutoMemory._is_duplicate()` returns True for identical content
- [ ] `InMemoryStorage.search()` with `query_embedding` uses cosine similarity
- [ ] `SqliteStorage.search()` with `query_embedding` uses cosine similarity
- [ ] `InMemoryStorage.search()` without embedding falls back to text search
- [ ] `OpenAIWrapper.chat.completions.create()` injects memory context
- [ ] `AnthropicWrapper.messages.create()` injects memory context
- [ ] Middleware saves interaction after response

---

## 9. Implementation Guide

### 9.1 File Structure

```
celestial_engine/
├── __init__.py              # MODIFY: exports 추가, __version__
├── models.py                # (변경 없음)
├── memory_function.py       # MODIFY: MemoryPresets 클래스 추가
├── zone_manager.py          # (변경 없음)
├── importance.py            # (변경 없음)
├── rebalancer.py            # (변경 없음)
├── middleware.py             # CREATE: 미들웨어 레이어 전체
├── auto_memory.py            # CREATE: 자동 기억 기능
├── storage/
│   ├── __init__.py          # (변경 없음)
│   ├── memory.py            # MODIFY: 벡터 검색 추가
│   └── sqlite.py            # MODIFY: 벡터 검색 추가
├── adapters/                # (변경 없음)
│   ├── __init__.py
│   ├── langchain.py
│   ├── openai.py
│   └── anthropic.py
│
pyproject.toml                # MODIFY: 패키지 포함 + 버전 2.0.0
examples/
├── middleware_openai.py      # CREATE: OpenAI 래퍼 사용 예제
└── middleware_anthropic.py   # CREATE: Anthropic 래퍼 사용 예제
```

### 9.2 Implementation Order

| Step | Feature | Files | Depends On |
|:----:|---------|-------|-----------|
| 1 | F1: pyproject.toml 패키지 정비 | `pyproject.toml` | - |
| 2 | F3: InMemoryStorage 벡터 검색 | `storage/memory.py` | - |
| 3 | F3: SqliteStorage 벡터 검색 | `storage/sqlite.py` | - |
| 4 | F5: MemoryPresets 추가 | `memory_function.py` | - |
| 5 | F4: AutoMemory 구현 | `auto_memory.py` (CREATE) | - |
| 6 | F2: MemoryMiddleware + ContextBuilder | `middleware.py` (CREATE) | Step 5 |
| 7 | F2: OpenAIWrapper 구현 | `middleware.py` | Step 6 |
| 8 | F2: AnthropicWrapper 구현 | `middleware.py` | Step 6 |
| 9 | F1: __init__.py 공개 API 정리 | `__init__.py` | Steps 4-8 |
| 10 | 예제 코드 작성 | `examples/` (CREATE) | Step 9 |

### 9.3 Implementation Notes

- Steps 1-5는 독립적이므로 병렬 구현 가능
- Step 6은 Step 5 (AutoMemory) 완료 후 진행
- Step 9 (__init__.py)는 모든 신규 모듈 완료 후 마지막에 진행
- 기존 테스트가 깨지지 않도록 주의: 모든 변경은 추가적(additive)

---

## 10. Coding Convention

### 10.1 Python Conventions

| Target | Rule | Example |
|--------|------|---------|
| Classes | PascalCase | `MemoryMiddleware`, `AutoMemory` |
| Functions/Methods | snake_case | `recall_context()`, `process_turn()` |
| Private methods | `_` prefix | `_extract_facts()`, `_is_duplicate()` |
| Constants | UPPER_SNAKE_CASE | `SIMILARITY_THRESHOLD`, `DEFAULT_TEMPLATE` |
| Type hints | PEP 604 union (`X | Y`) | `str | None`, `list[float] | None` |
| Docstrings | 한글 (프로젝트 관례) | `"""검색된 기억을 시스템 프롬프트로 포매팅"""` |

### 10.2 Import Order

```python
# 1. Standard library
import math
import re
from dataclasses import dataclass

# 2. Internal (celestial_engine)
from .models import CelestialItem
from .importance import RuleBasedEvaluator, ImportanceEvaluator

# 3. Optional external (runtime import)
# import openai  → inside method body only

# 4. Type checking only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import CelestialMemory
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-20 | Initial draft | Claude |
