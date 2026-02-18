# Design: stellar-memory-p7

> **Feature**: AI 기억 플러그인 - 천체구조 기반 독립 기억 모듈 상용화
> **Version**: v0.8.0
> **Created**: 2026-02-17
> **Plan Reference**: `docs/01-plan/features/stellar-memory-p7.plan.md`

---

## 1. 아키텍처 개요

### 1.1 현재 아키텍처 (v0.7.0)

```
stellar_memory/
├── stellar.py              ← StellarMemory 메인 클래스 (673줄)
├── config.py               ← 전체 설정 (266줄, 17개 Config 클래스)
├── models.py               ← 데이터 모델 (203줄, 16개 dataclass)
├── memory_function.py      ← 기억 함수 I(m) = w₁R + w₂F + w₃A + w₄C
├── importance_evaluator.py ← 중요도 평가 (Rule/LLM/Null)
├── orbit_manager.py        ← 존 배치 관리
├── storage/                ← SQLite, PostgreSQL, Redis
├── security/               ← 암호화, RBAC, 감사
├── sync/                   ← CRDT, WebSocket
├── connectors/             ← Web, File, API
├── dashboard/              ← FastAPI 대시보드
├── cli.py                  ← CLI (store/recall/stats/serve)
├── mcp_server.py           ← MCP 프로토콜 서버
└── __init__.py             ← Public API (106개 export)
```

### 1.2 P7 확장 아키텍처

```
stellar_memory/
├── emotion.py              ← [NEW] F1: EmotionAnalyzer + EmotionVector
├── stream.py               ← [NEW] F2: MemoryStream + Timeline
├── server.py               ← [NEW] F4: REST API 서버 (FastAPI)
├── adapters/               ← [NEW] F5: AI 프레임워크 어댑터
│   ├── __init__.py
│   ├── langchain.py        ← LangChain Memory 인터페이스
│   └── openai_plugin.py    ← OpenAI function calling 스키마
├── stellar.py              ← [MOD] timeline(), narrate(), emotion 통합
├── config.py               ← [MOD] EmotionConfig, ServerConfig 추가
├── models.py               ← [MOD] EmotionData, TimelineEntry 추가
├── memory_function.py      ← [MOD] E(m) 감정 항 추가
├── cli.py                  ← [MOD] serve-api 커맨드 추가
├── __init__.py             ← [MOD] Public API 정리
├── Dockerfile              ← [NEW] F3: Docker 이미지
├── docker-compose.yml      ← [NEW] F3: 풀스택 구성
├── .dockerignore           ← [NEW] F3
└── pyproject.toml          ← [MOD] F3: 메타데이터, entry_points 완성
```

---

## 2. F1: 감성 기억 엔진 (Emotional Memory Engine)

### 2.1 데이터 모델

```python
# models.py에 추가

@dataclass
class EmotionVector:
    """6가지 기본 감정 벡터."""
    joy: float = 0.0
    sadness: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    surprise: float = 0.0
    disgust: float = 0.0

    @property
    def intensity(self) -> float:
        """감정 강도 = 최대 감정값."""
        return max(self.joy, self.sadness, self.anger,
                   self.fear, self.surprise, self.disgust)

    @property
    def dominant(self) -> str:
        """지배적 감정 이름."""
        emotions = {
            "joy": self.joy, "sadness": self.sadness,
            "anger": self.anger, "fear": self.fear,
            "surprise": self.surprise, "disgust": self.disgust,
        }
        return max(emotions, key=emotions.get)

    def to_list(self) -> list[float]:
        return [self.joy, self.sadness, self.anger,
                self.fear, self.surprise, self.disgust]

    @classmethod
    def from_list(cls, values: list[float]) -> EmotionVector:
        names = ["joy", "sadness", "anger", "fear", "surprise", "disgust"]
        kwargs = {n: v for n, v in zip(names, values[:6])}
        return cls(**kwargs)

    def to_dict(self) -> dict[str, float]:
        return {
            "joy": self.joy, "sadness": self.sadness,
            "anger": self.anger, "fear": self.fear,
            "surprise": self.surprise, "disgust": self.disgust,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EmotionVector:
        return cls(**{k: float(data.get(k, 0.0)) for k in
                      ["joy", "sadness", "anger", "fear", "surprise", "disgust"]})


@dataclass
class TimelineEntry:
    """타임라인 항목."""
    timestamp: float
    memory_id: str
    content: str
    zone: int
    emotion: EmotionVector | None = None
    importance: float = 0.0
```

### 2.2 MemoryItem 확장

```python
# models.py - MemoryItem에 필드 추가
@dataclass
class MemoryItem:
    # ... 기존 필드 유지 ...
    # P7 fields
    emotion: EmotionVector | None = None  # 감정 벡터
```

### 2.3 EmotionAnalyzer 클래스

```python
# emotion.py (신규 파일)

"""Emotion analysis for memory items - rule-based with optional LLM."""

from __future__ import annotations
import re
import logging
from stellar_memory.models import EmotionVector
from stellar_memory.config import EmotionConfig, LLMConfig

logger = logging.getLogger(__name__)

# 규칙 기반 감정 키워드
EMOTION_KEYWORDS: dict[str, list[str]] = {
    "joy": [
        r"\b(happy|glad|delighted|excited|wonderful|great|amazing|love|enjoy|celebrate|success|win|perfect|fantastic)\b",
        r"\b(기쁘|행복|좋|즐거|축하|성공|완벽|대박|최고)\b",
        r"[!]{2,}",
        r"[😊😄🎉❤️👍🥳]",
    ],
    "sadness": [
        r"\b(sad|unhappy|depressed|disappointed|lonely|miss|lost|cry|grief|sorry|regret|fail)\b",
        r"\b(슬프|우울|실망|외로|그리|잃|아쉬|후회|실패)\b",
        r"[😢😭💔]",
    ],
    "anger": [
        r"\b(angry|furious|hate|rage|annoyed|frustrated|irritated|outraged|damn|hell)\b",
        r"\b(화나|분노|짜증|열받|싫|미치)\b",
        r"[😠😡🤬]",
    ],
    "fear": [
        r"\b(afraid|scared|terrified|worried|anxious|panic|nervous|threat|danger|risk)\b",
        r"\b(무서|걱정|불안|공포|위험|두려)\b",
        r"[😨😱😰]",
    ],
    "surprise": [
        r"\b(surprised|shocked|unexpected|wow|unbelievable|incredible|sudden|astonish)\b",
        r"\b(놀라|충격|예상 밖|갑자기|대단|헐)\b",
        r"[😮😲🤯]",
    ],
    "disgust": [
        r"\b(disgusting|gross|awful|terrible|horrible|revolting|nasty|creepy)\b",
        r"\b(역겨|끔찍|최악|혐오|지저분|구역질)\b",
        r"[🤮😷🤢]",
    ],
}


class EmotionAnalyzer:
    """텍스트에서 감정 벡터를 추출하는 분석기."""

    def __init__(self, config: EmotionConfig | None = None,
                 llm_config: LLMConfig | None = None):
        from stellar_memory.config import EmotionConfig as _EC
        self._config = config or _EC()
        self._llm_config = llm_config
        self._llm = None

        if self._config.use_llm and llm_config:
            try:
                from stellar_memory.providers import ProviderRegistry
                self._llm = ProviderRegistry.create_llm(llm_config)
            except Exception:
                logger.info("LLM not available for emotion analysis, using rules")

    def analyze(self, text: str) -> EmotionVector:
        """텍스트의 감정을 분석하여 EmotionVector 반환."""
        if not self._config.enabled:
            return EmotionVector()

        # LLM 분석 시도
        if self._llm is not None:
            try:
                return self._analyze_llm(text)
            except Exception:
                logger.debug("LLM emotion analysis failed, falling back to rules")

        # 규칙 기반 분석
        return self._analyze_rules(text)

    def _analyze_rules(self, text: str) -> EmotionVector:
        """규칙 기반(키워드 패턴) 감정 분석."""
        scores: dict[str, float] = {}
        text_lower = text.lower()

        for emotion, patterns in EMOTION_KEYWORDS.items():
            match_count = sum(
                1 for p in patterns if re.search(p, text_lower)
            )
            scores[emotion] = min(match_count / max(len(patterns), 1), 1.0)

        return EmotionVector(**scores)

    def _analyze_llm(self, text: str) -> EmotionVector:
        """LLM 기반 감정 분석."""
        import json

        prompt = (
            "Analyze the emotion of the following text. "
            "Rate each emotion from 0.0 to 1.0:\n"
            "- joy, sadness, anger, fear, surprise, disgust\n\n"
            f"Text: {text[:500]}\n\n"
            "Respond ONLY with JSON: "
            '{"joy": 0.0, "sadness": 0.0, "anger": 0.0, '
            '"fear": 0.0, "surprise": 0.0, "disgust": 0.0}'
        )

        raw = self._llm.complete(prompt, max_tokens=100)
        data = json.loads(raw)
        return EmotionVector.from_dict(data)
```

### 2.4 기억 함수 확장

```python
# memory_function.py 변경사항

class MemoryFunction:
    def calculate(self, item: MemoryItem, current_time: float,
                  context_embedding: list[float] | None = None) -> ScoreBreakdown:
        r = self._recall_score(item.recall_count)
        f = self._freshness_score(item.last_recalled_at, current_time)
        a = item.arbitrary_importance
        c = self._context_score(item.embedding, context_embedding)
        e = self._emotion_score(item)  # NEW

        total = (self._cfg.w_recall * r
                 + self._cfg.w_freshness * f
                 + self._cfg.w_arbitrary * a
                 + self._cfg.w_context * c
                 + self._cfg.w_emotion * e)  # NEW

        target_zone = self._determine_zone(total)
        return ScoreBreakdown(r, f, a, c, total, target_zone, e)  # e 추가

    def _emotion_score(self, item: MemoryItem) -> float:
        """E(m) = 감정 강도. 감정 없으면 0.0."""
        if item.emotion is None:
            return 0.0
        return item.emotion.intensity
```

### 2.5 ScoreBreakdown 확장

```python
# models.py
@dataclass
class ScoreBreakdown:
    recall_score: float
    freshness_score: float
    arbitrary_score: float
    context_score: float
    total: float
    target_zone: int
    emotion_score: float = 0.0  # NEW - 기본값으로 하위호환
```

### 2.6 EmotionConfig

```python
# config.py에 추가

@dataclass
class EmotionConfig:
    enabled: bool = False          # 기본 비활성 (하위호환)
    use_llm: bool = False          # LLM 분석 사용 여부
    decay_boost_threshold: float = 0.7   # 이 이상이면 느린 망각
    decay_boost_factor: float = 0.5      # 강한 감정 decay 배율
    decay_penalty_threshold: float = 0.3 # 이 이하이면 빠른 망각
    decay_penalty_factor: float = 1.5    # 약한 감정 decay 배율

# MemoryFunctionConfig에 추가:
@dataclass
class MemoryFunctionConfig:
    # ... 기존 필드 ...
    w_emotion: float = 0.0  # 기본 0.0 → EmotionConfig.enabled 시 0.15로 조정

# StellarConfig에 추가:
@dataclass
class StellarConfig:
    # ... 기존 필드 ...
    emotion: EmotionConfig = field(default_factory=EmotionConfig)  # P7
```

### 2.7 Decay 통합

```python
# adaptive_decay.py 또는 decay_manager.py 수정

# DecayManager.check_decay()에서 감정 강도에 따라 decay_rate 조절:
def _adjusted_decay_days(self, item: MemoryItem) -> int:
    """감정 강도에 따른 망각 속도 조절."""
    base = self._config.decay_days
    if item.emotion is None:
        return base
    intensity = item.emotion.intensity
    if intensity >= self._emotion_cfg.decay_boost_threshold:
        return int(base / self._emotion_cfg.decay_boost_factor)  # 느린 망각
    if intensity <= self._emotion_cfg.decay_penalty_threshold:
        return int(base * self._emotion_cfg.decay_penalty_factor)  # 빠른 망각
    return base
```

### 2.8 StellarMemory 통합

```python
# stellar.py 변경사항

class StellarMemory:
    def __init__(self, ...):
        # ... 기존 초기화 ...

        # P7: Emotion Analyzer
        self._emotion_analyzer = None
        if self.config.emotion.enabled:
            from stellar_memory.emotion import EmotionAnalyzer
            self._emotion_analyzer = EmotionAnalyzer(
                self.config.emotion, self.config.llm
            )
            # w_emotion 자동 활성화
            if self.config.memory_function.w_emotion == 0.0:
                self.config.memory_function.w_emotion = 0.15
                # 기존 가중치 재조정 (총합 ~1.0 유지)
                self.config.memory_function.w_recall = 0.25
                self.config.memory_function.w_freshness = 0.25
                self.config.memory_function.w_arbitrary = 0.20
                self.config.memory_function.w_context = 0.15

    def store(self, content: str, ..., emotion: EmotionVector | None = None) -> MemoryItem:
        # ... 기존 로직 ...
        # P7: 감정 분석
        if self._emotion_analyzer and emotion is None:
            item.emotion = self._emotion_analyzer.analyze(content)
        elif emotion is not None:
            item.emotion = emotion
        # ... 나머지 로직 ...

    def recall(self, query: str, ..., emotion: str | None = None) -> list[MemoryItem]:
        # ... 기존 로직 ...
        # P7: 감정 필터링
        if emotion is not None and results:
            results = [
                r for r in results
                if r.emotion and r.emotion.dominant == emotion
            ]
        # ...
```

---

## 3. F2: 기억 스트림 & 타임라인 (Memory Stream)

### 3.1 MemoryStream 클래스

```python
# stream.py (신규 파일)

"""Memory Stream - time-ordered memory retrieval and narrative generation."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.stellar import StellarMemory

from stellar_memory.models import TimelineEntry, EmotionVector


class MemoryStream:
    """시간순 기억 스트림과 내러티브 생성."""

    def __init__(self, memory: StellarMemory):
        self._memory = memory

    def timeline(self, start: float | str | None = None,
                 end: float | str | None = None,
                 limit: int = 100) -> list[TimelineEntry]:
        """시간 범위 내 기억을 시간순으로 조회.

        Args:
            start: 시작 시간 (Unix timestamp 또는 "YYYY-MM-DD" 문자열)
            end: 종료 시간
            limit: 최대 항목 수

        Returns:
            시간순 정렬된 TimelineEntry 리스트
        """
        start_ts = self._parse_time(start) if start else 0.0
        end_ts = self._parse_time(end) if end else time.time()

        all_items = self._memory._orbit_mgr.get_all_items()
        filtered = [
            item for item in all_items
            if start_ts <= item.created_at <= end_ts
        ]
        filtered.sort(key=lambda x: x.created_at)
        filtered = filtered[:limit]

        entries = []
        for item in filtered:
            entries.append(TimelineEntry(
                timestamp=item.created_at,
                memory_id=item.id,
                content=item.content[:200],
                zone=item.zone,
                emotion=item.emotion,
                importance=item.arbitrary_importance,
            ))
        return entries

    def narrate(self, topic: str, limit: int = 10) -> str:
        """LLM을 사용하여 관련 기억들을 스토리 형태로 정리.

        Args:
            topic: 내러티브 주제
            limit: 사용할 기억 수

        Returns:
            내러티브 텍스트 문자열
        """
        # 주제 관련 기억 검색
        results = self._memory.recall(topic, limit=limit)
        if not results:
            return ""

        # LLM이 없으면 단순 연결
        summarizer = self._memory._summarizer
        if summarizer is None:
            lines = []
            for item in results:
                lines.append(f"- {item.content[:150]}")
            return "\n".join(lines)

        # LLM 내러티브 생성
        memories_text = "\n".join(
            f"[{i+1}] {item.content[:200]}"
            for i, item in enumerate(results)
        )
        prompt = (
            f"Based on these memories about '{topic}', "
            f"create a brief narrative summary:\n\n{memories_text}\n\n"
            "Write a cohesive narrative in 2-3 sentences."
        )
        try:
            from stellar_memory.providers import ProviderRegistry
            llm = ProviderRegistry.create_llm(self._memory.config.llm)
            return llm.complete(prompt, max_tokens=200)
        except Exception:
            lines = [f"- {item.content[:150]}" for item in results]
            return "\n".join(lines)

    def summarize_period(self, start: float | str,
                         end: float | str) -> str:
        """특정 기간의 기억을 자동 요약.

        Args:
            start: 시작 시간
            end: 종료 시간

        Returns:
            요약 텍스트
        """
        entries = self.timeline(start, end)
        if not entries:
            return ""
        contents = [e.content for e in entries]
        combined = " | ".join(contents[:20])

        summarizer = self._memory._summarizer
        if summarizer and len(combined) > 100:
            return summarizer.summarize(combined) or combined[:200]
        return combined[:200]

    @staticmethod
    def _parse_time(value: float | str) -> float:
        """시간 값을 Unix timestamp로 변환."""
        if isinstance(value, (int, float)):
            return float(value)
        # "YYYY-MM-DD" 또는 "YYYY-MM-DD HH:MM" 형식
        import datetime
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.datetime.strptime(value, fmt)
                return dt.timestamp()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse time: {value}")
```

### 3.2 StellarMemory 통합

```python
# stellar.py에 추가

class StellarMemory:
    def __init__(self, ...):
        # ... 기존 초기화 ...
        # P7: Memory Stream
        self._stream = None  # lazy init

    @property
    def stream(self) -> MemoryStream:
        """Lazy-initialized MemoryStream."""
        if self._stream is None:
            from stellar_memory.stream import MemoryStream
            self._stream = MemoryStream(self)
        return self._stream

    def timeline(self, start=None, end=None, limit: int = 100) -> list[TimelineEntry]:
        """시간순 기억 타임라인."""
        return self.stream.timeline(start, end, limit)

    def narrate(self, topic: str, limit: int = 10) -> str:
        """주제에 대한 기억 내러티브 생성."""
        return self.stream.narrate(topic, limit)
```

---

## 4. F3: PyPI 패키지 & Docker 이미지

### 4.1 pyproject.toml 완성

```toml
[project]
name = "stellar-memory"
version = "0.8.0"
description = "A celestial-structure-based AI memory management system - Give any AI human-like memory"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Stellar Memory Contributors"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
keywords = ["ai", "memory", "llm", "mcp", "recall", "context"]
dependencies = []

[project.urls]
Homepage = "https://github.com/stellar-memory/stellar-memory"
Documentation = "https://stellar-memory.readthedocs.io"

[project.scripts]
stellar-memory = "stellar_memory.cli:main"

[project.optional-dependencies]
# Core AI features
ai = ["sentence-transformers>=2.2.0", "anthropic>=0.18.0"]
embedding = ["sentence-transformers>=2.2.0"]
llm = ["anthropic>=0.18.0"]
openai = ["openai>=1.0.0"]
ollama = ["requests>=2.28.0"]

# Infrastructure
postgres = ["asyncpg>=0.29.0"]
redis = ["redis>=5.0.0"]
security = ["cryptography>=42.0.0"]
sync = ["websockets>=12.0"]
connectors = ["httpx>=0.27.0"]

# Server & Dashboard
server = ["fastapi>=0.110.0", "uvicorn>=0.29.0"]
dashboard = ["fastapi>=0.110.0", "uvicorn>=0.29.0"]
mcp = ["mcp[cli]>=1.2.0"]

# Adapters
adapters = ["langchain-core>=0.1.0"]

# Full install
full = [
    "sentence-transformers>=2.2.0", "anthropic>=0.18.0", "openai>=1.0.0",
    "requests>=2.28.0", "mcp[cli]>=1.2.0",
    "asyncpg>=0.29.0", "redis>=5.0.0", "cryptography>=42.0.0",
    "websockets>=12.0", "httpx>=0.27.0",
    "fastapi>=0.110.0", "uvicorn>=0.29.0",
    "langchain-core>=0.1.0",
]

dev = ["pytest>=7.0", "pytest-cov>=4.0", "httpx>=0.27.0"]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 4.2 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy source
COPY pyproject.toml .
COPY stellar_memory/ stellar_memory/

# Install
RUN pip install --no-cache-dir .[server]

# Runtime config via env
ENV STELLAR_DB_PATH=/data/stellar_memory.db
ENV STELLAR_HOST=0.0.0.0
ENV STELLAR_PORT=9000

EXPOSE 9000

# Data volume
VOLUME /data

CMD ["stellar-memory", "serve-api", "--host", "0.0.0.0", "--port", "9000"]
```

### 4.3 docker-compose.yml

```yaml
# docker-compose.yml
version: "3.9"

services:
  stellar:
    build: .
    ports:
      - "9000:9000"
    environment:
      - STELLAR_DB_PATH=/data/stellar_memory.db
      - STELLAR_STORAGE_BACKEND=sqlite
    volumes:
      - stellar-data:/data

  # Optional: PostgreSQL + pgvector
  stellar-pg:
    build: .
    ports:
      - "9001:9000"
    environment:
      - STELLAR_STORAGE_BACKEND=postgresql
      - STELLAR_DB_URL=postgresql://stellar:stellar@postgres:5432/stellar
    depends_on:
      - postgres

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: stellar
      POSTGRES_PASSWORD: stellar
      POSTGRES_DB: stellar
    volumes:
      - pg-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  stellar-data:
  pg-data:
```

### 4.4 .dockerignore

```
__pycache__
*.pyc
.git
.pytest_cache
tests/
docs/
*.egg-info
.pdca-status.json
stellar_data/
*.db
```

---

## 5. F4: REST API 서버 모드

### 5.1 서버 설계

```python
# server.py (신규 파일)

"""Standalone REST API server for Stellar Memory."""

from __future__ import annotations

import json
import logging
import os
import time

logger = logging.getLogger(__name__)


def create_api_app(config=None, namespace: str | None = None):
    """Create FastAPI application for REST API server mode."""
    try:
        from fastapi import FastAPI, HTTPException, Depends, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel, Field
    except ImportError:
        raise ImportError(
            "fastapi is required. Install with: pip install stellar-memory[server]"
        )

    from stellar_memory.config import StellarConfig
    from stellar_memory.stellar import StellarMemory

    cfg = config or StellarConfig()
    memory = StellarMemory(cfg, namespace=namespace)

    app = FastAPI(
        title="Stellar Memory API",
        version="0.8.0",
        description="Celestial-structure-based AI memory management API",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Rate Limiting (simple in-memory) ---
    _rate_store: dict[str, list[float]] = {}
    RATE_LIMIT = int(os.environ.get("STELLAR_RATE_LIMIT", "60"))
    RATE_WINDOW = 60  # seconds

    async def check_rate_limit(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        times = _rate_store.get(client_ip, [])
        times = [t for t in times if now - t < RATE_WINDOW]
        if len(times) >= RATE_LIMIT:
            raise HTTPException(429, "Rate limit exceeded")
        times.append(now)
        _rate_store[client_ip] = times

    # --- API Key Auth (optional) ---
    API_KEY = os.environ.get("STELLAR_API_KEY")

    async def check_api_key(request: Request):
        if API_KEY is None:
            return  # No auth configured
        key = request.headers.get("X-API-Key") or ""
        if not key:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                key = auth[7:]
        if key != API_KEY:
            raise HTTPException(401, "Invalid API key")

    # --- Pydantic Models ---
    class StoreRequest(BaseModel):
        content: str
        importance: float = Field(0.5, ge=0.0, le=1.0)
        metadata: dict = Field(default_factory=dict)
        auto_evaluate: bool = False

    class RecallQuery(BaseModel):
        query: str
        limit: int = Field(5, ge=1, le=50)
        emotion: str | None = None

    class NarrateRequest(BaseModel):
        topic: str
        limit: int = Field(10, ge=1, le=50)

    # --- Routes ---
    @app.post("/api/v1/store",
              dependencies=[Depends(check_api_key), Depends(check_rate_limit)])
    async def store(req: StoreRequest):
        item = memory.store(
            req.content,
            importance=req.importance,
            metadata=req.metadata,
            auto_evaluate=req.auto_evaluate,
        )
        return {
            "id": item.id, "zone": item.zone,
            "score": round(item.total_score, 4),
        }

    @app.get("/api/v1/recall",
             dependencies=[Depends(check_api_key), Depends(check_rate_limit)])
    async def recall(q: str, limit: int = 5, emotion: str | None = None):
        results = memory.recall(q, limit=min(limit, 50), emotion=emotion)
        return [{
            "id": item.id,
            "content": item.content,
            "zone": item.zone,
            "importance": round(item.arbitrary_importance, 4),
            "recall_count": item.recall_count,
            "emotion": item.emotion.to_dict() if item.emotion else None,
        } for item in results]

    @app.delete("/api/v1/forget/{memory_id}",
                dependencies=[Depends(check_api_key), Depends(check_rate_limit)])
    async def forget(memory_id: str):
        removed = memory.forget(memory_id)
        if not removed:
            raise HTTPException(404, "Memory not found")
        return {"removed": True}

    @app.get("/api/v1/memories",
             dependencies=[Depends(check_api_key), Depends(check_rate_limit)])
    async def memories(zone: int | None = None, limit: int = 50,
                       offset: int = 0):
        all_items = memory._orbit_mgr.get_all_items()
        if zone is not None:
            all_items = [i for i in all_items if i.zone == zone]
        all_items.sort(key=lambda x: x.total_score, reverse=True)
        page = all_items[offset:offset + limit]
        return {
            "total": len(all_items),
            "items": [{
                "id": item.id,
                "content": item.content[:200],
                "zone": item.zone,
                "score": round(item.total_score, 4),
                "recall_count": item.recall_count,
                "importance": round(item.arbitrary_importance, 4),
                "created_at": item.created_at,
            } for item in page],
        }

    @app.get("/api/v1/timeline",
             dependencies=[Depends(check_api_key), Depends(check_rate_limit)])
    async def timeline(start: str | None = None, end: str | None = None,
                       limit: int = 100):
        entries = memory.timeline(start, end, limit)
        return [{
            "timestamp": e.timestamp,
            "memory_id": e.memory_id,
            "content": e.content,
            "zone": e.zone,
            "importance": round(e.importance, 4),
            "emotion": e.emotion.to_dict() if e.emotion else None,
        } for e in entries]

    @app.post("/api/v1/narrate",
              dependencies=[Depends(check_api_key), Depends(check_rate_limit)])
    async def narrate(req: NarrateRequest):
        text = memory.narrate(req.topic, req.limit)
        return {"narrative": text}

    @app.get("/api/v1/stats",
             dependencies=[Depends(check_api_key)])
    async def stats():
        s = memory.stats()
        return {
            "total_memories": s.total_memories,
            "zones": {str(k): v for k, v in s.zone_counts.items()},
            "capacities": {str(k): v for k, v in s.zone_capacities.items()},
        }

    @app.get("/api/v1/health")
    async def health():
        h = memory.health()
        return {
            "healthy": h.healthy,
            "total_memories": h.total_memories,
            "warnings": h.warnings,
        }

    @app.get("/api/v1/events",
             dependencies=[Depends(check_api_key)])
    async def events():
        """SSE endpoint - reuses dashboard SSE logic."""
        import asyncio
        from starlette.responses import StreamingResponse

        async def event_stream():
            q: asyncio.Queue = asyncio.Queue()
            bus = memory._event_bus

            def _push(event_name, *args):
                data = {"event": event_name, "ts": time.time()}
                try:
                    q.put_nowait(data)
                except asyncio.QueueFull:
                    pass

            for evt in ("on_store", "on_recall", "on_forget",
                        "on_reorbit", "on_decay"):
                bus.on(evt, lambda *a, en=evt: _push(en, *a))

            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'heartbeat'})}\n\n"

        return StreamingResponse(
            event_stream(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.on_event("startup")
    async def startup():
        memory.start()

    @app.on_event("shutdown")
    async def shutdown():
        memory.stop()

    return app, memory
```

### 5.2 CLI 통합

```python
# cli.py에 추가

# subparser 추가:
p_serve_api = subparsers.add_parser("serve-api", help="Start REST API server")
p_serve_api.add_argument("--host", default="0.0.0.0")
p_serve_api.add_argument("--port", type=int, default=9000)
p_serve_api.add_argument("--reload", action="store_true")

# handler:
elif args.command == "serve-api":
    from stellar_memory.server import create_api_app
    import uvicorn
    app, _ = create_api_app(config, namespace=args.namespace)
    uvicorn.run(app, host=args.host, port=args.port,
                reload=args.reload, log_level="info")
```

### 5.3 ServerConfig

```python
# config.py에 추가

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 9000
    api_key_env: str = "STELLAR_API_KEY"
    rate_limit: int = 60
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
```

---

## 6. F5: AI 플러그인 SDK & 문서화

### 6.1 LangChain 어댑터

```python
# adapters/langchain.py

"""LangChain Memory interface adapter for Stellar Memory."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.stellar import StellarMemory


class StellarLangChainMemory:
    """LangChain BaseMemory compatible adapter.

    Usage:
        from stellar_memory import StellarMemory
        from stellar_memory.adapters.langchain import StellarLangChainMemory

        memory = StellarMemory()
        lc_memory = StellarLangChainMemory(memory)

        # Use with LangChain
        from langchain.chains import ConversationChain
        chain = ConversationChain(memory=lc_memory, ...)
    """

    memory_key: str = "history"
    input_key: str = "input"
    output_key: str = "output"

    def __init__(self, stellar_memory: StellarMemory,
                 recall_limit: int = 5,
                 memory_key: str = "history"):
        self._memory = stellar_memory
        self._recall_limit = recall_limit
        self.memory_key = memory_key

    @property
    def memory_variables(self) -> list[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
        """Recall relevant memories based on input."""
        query = inputs.get(self.input_key, "")
        if not query:
            return {self.memory_key: ""}

        results = self._memory.recall(str(query), limit=self._recall_limit)
        if not results:
            return {self.memory_key: ""}

        context = "\n".join(
            f"- {item.content}" for item in results
        )
        return {self.memory_key: context}

    def save_context(self, inputs: dict[str, Any],
                     outputs: dict[str, str]) -> None:
        """Store the conversation exchange as a memory."""
        user_input = inputs.get(self.input_key, "")
        assistant_output = outputs.get(self.output_key, "")
        if user_input or assistant_output:
            content = f"User: {user_input}\nAssistant: {assistant_output}"
            self._memory.store(
                content=content,
                auto_evaluate=True,
                metadata={"source": "langchain"},
            )

    def clear(self) -> None:
        """Clear is a no-op for persistent memory."""
        pass
```

### 6.2 OpenAI Function Calling 어댑터

```python
# adapters/openai_plugin.py

"""OpenAI function calling schema for Stellar Memory."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.stellar import StellarMemory


# OpenAI function calling tools schema
STELLAR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "memory_store",
            "description": "Store a new memory for future recall",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Memory content to store"},
                    "importance": {"type": "number", "minimum": 0, "maximum": 1,
                                   "description": "Importance score 0.0-1.0"},
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_recall",
            "description": "Search memories by query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20,
                              "description": "Max results"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_forget",
            "description": "Delete a specific memory by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "Memory UUID"},
                },
                "required": ["memory_id"],
            },
        },
    },
]


class OpenAIMemoryPlugin:
    """Plugin that handles OpenAI function call dispatch.

    Usage:
        import openai
        from stellar_memory import StellarMemory
        from stellar_memory.adapters.openai_plugin import OpenAIMemoryPlugin, STELLAR_TOOLS

        memory = StellarMemory()
        plugin = OpenAIMemoryPlugin(memory)

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[...],
            tools=STELLAR_TOOLS,
        )

        # Handle function calls
        for call in response.choices[0].message.tool_calls:
            result = plugin.handle_call(call.function.name, call.function.arguments)
    """

    def __init__(self, stellar_memory: StellarMemory):
        self._memory = stellar_memory

    def get_tools(self) -> list[dict]:
        """Return OpenAI tools schema."""
        return STELLAR_TOOLS

    def handle_call(self, function_name: str, arguments: str) -> str:
        """Dispatch function call and return JSON result."""
        import json
        args = json.loads(arguments)

        if function_name == "memory_store":
            item = self._memory.store(
                content=args["content"],
                importance=args.get("importance", 0.5),
                auto_evaluate=True,
            )
            return json.dumps({"id": item.id, "zone": item.zone})

        elif function_name == "memory_recall":
            results = self._memory.recall(
                args["query"], limit=args.get("limit", 5)
            )
            return json.dumps([{
                "id": item.id, "content": item.content,
                "zone": item.zone, "importance": item.arbitrary_importance,
            } for item in results])

        elif function_name == "memory_forget":
            removed = self._memory.forget(args["memory_id"])
            return json.dumps({"removed": removed})

        else:
            return json.dumps({"error": f"Unknown function: {function_name}"})
```

### 6.3 Public API 정리

```python
# __init__.py 업데이트 방침

# 핵심 사용자 API만 상단에 노출
# 내부 모듈은 명시적 import 필요

__version__ = "0.8.0"

# Primary API - 3줄로 시작 가능
from stellar_memory.stellar import StellarMemory
from stellar_memory.config import StellarConfig
from stellar_memory.models import MemoryItem

# Config classes
from stellar_memory.config import (
    MemoryFunctionConfig, ZoneConfig, EmbedderConfig,
    LLMConfig, EmotionConfig, ServerConfig,
    # ... 기타 config ...
)

# P7 추가
from stellar_memory.models import EmotionVector, TimelineEntry

__all__ = [
    # Primary (3줄 Quick Start)
    "StellarMemory", "StellarConfig", "MemoryItem",
    # P7
    "EmotionVector", "TimelineEntry", "EmotionConfig", "ServerConfig",
    # ... 기존 exports 유지 ...
]
```

---

## 7. 테스트 설계

### 7.1 F1 테스트: 감성 기억

| # | 테스트명 | 검증 내용 |
|---|---------|-----------|
| 1 | test_emotion_vector_creation | EmotionVector 생성, intensity, dominant |
| 2 | test_emotion_vector_to_from_dict | 직렬화/역직렬화 |
| 3 | test_emotion_vector_to_from_list | list 변환 |
| 4 | test_rule_based_joy_detection | 기쁨 키워드 감지 |
| 5 | test_rule_based_sadness_detection | 슬픔 키워드 감지 |
| 6 | test_rule_based_anger_detection | 분노 키워드 감지 |
| 7 | test_rule_based_neutral | 중립 텍스트 → 낮은 강도 |
| 8 | test_analyzer_disabled | enabled=False → 빈 벡터 |
| 9 | test_emotion_score_in_memory_function | E(m) 계산 정확도 |
| 10 | test_store_with_auto_emotion | store() 시 자동 감정 분석 |
| 11 | test_store_with_explicit_emotion | 명시적 emotion 전달 |
| 12 | test_recall_emotion_filter | emotion="joy" 필터링 |
| 13 | test_emotion_decay_boost | 강한 감정 → 느린 망각 |
| 14 | test_emotion_decay_penalty | 약한 감정 → 빠른 망각 |
| 15 | test_score_breakdown_has_emotion | ScoreBreakdown.emotion_score |
| 16 | test_korean_emotion_keywords | 한국어 감정 키워드 |
| 17 | test_emoji_emotion_detection | 이모지 감정 감지 |

### 7.2 F2 테스트: 타임라인

| # | 테스트명 | 검증 내용 |
|---|---------|-----------|
| 1 | test_timeline_empty | 빈 메모리 → 빈 리스트 |
| 2 | test_timeline_time_range | 시간 범위 필터링 |
| 3 | test_timeline_sorted | 시간순 정렬 확인 |
| 4 | test_timeline_limit | limit 적용 |
| 5 | test_timeline_date_string | "YYYY-MM-DD" 문자열 파싱 |
| 6 | test_narrate_no_results | 결과 없을 때 빈 문자열 |
| 7 | test_narrate_without_llm | LLM 없이 단순 연결 |
| 8 | test_summarize_period | 기간 요약 |
| 9 | test_parse_time_float | float 입력 |
| 10 | test_parse_time_invalid | 잘못된 형식 → ValueError |
| 11 | test_timeline_entry_model | TimelineEntry 필드 확인 |
| 12 | test_stellar_timeline_method | StellarMemory.timeline() 호출 |

### 7.3 F3 테스트: 패키징

| # | 테스트명 | 검증 내용 |
|---|---------|-----------|
| 1 | test_import_stellar_memory | `import stellar_memory` 성공 |
| 2 | test_version | `__version__ == "0.8.0"` |
| 3 | test_quick_start_3lines | 3줄 코드 동작 확인 |
| 4 | test_public_api_exports | `__all__` 핵심 클래스 포함 |
| 5 | test_optional_import_no_crash | 선택적 의존성 없어도 코어 동작 |
| 6 | test_cli_entrypoint | `stellar-memory --help` 정상 |
| 7 | test_env_config | 환경변수로 설정 가능 |
| 8 | test_dockerfile_exists | Dockerfile 존재 확인 |

### 7.4 F4 테스트: REST API

| # | 테스트명 | 검증 내용 |
|---|---------|-----------|
| 1 | test_store_endpoint | POST /api/v1/store |
| 2 | test_recall_endpoint | GET /api/v1/recall?q= |
| 3 | test_forget_endpoint | DELETE /api/v1/forget/{id} |
| 4 | test_memories_list | GET /api/v1/memories |
| 5 | test_memories_zone_filter | zone 파라미터 필터링 |
| 6 | test_timeline_endpoint | GET /api/v1/timeline |
| 7 | test_narrate_endpoint | POST /api/v1/narrate |
| 8 | test_stats_endpoint | GET /api/v1/stats |
| 9 | test_health_endpoint | GET /api/v1/health (인증 불필요) |
| 10 | test_events_sse | GET /api/v1/events SSE |
| 11 | test_api_key_auth | X-API-Key 인증 |
| 12 | test_api_key_bearer | Bearer 토큰 인증 |
| 13 | test_unauthorized | 잘못된 키 → 401 |
| 14 | test_cors_headers | CORS 헤더 확인 |
| 15 | test_openapi_docs | /docs 접근 가능 |

### 7.5 F5 테스트: SDK & 어댑터

| # | 테스트명 | 검증 내용 |
|---|---------|-----------|
| 1 | test_langchain_memory_variables | memory_variables 프로퍼티 |
| 2 | test_langchain_load_memory | load_memory_variables() |
| 3 | test_langchain_save_context | save_context() |
| 4 | test_langchain_clear | clear() no-op |
| 5 | test_openai_tools_schema | STELLAR_TOOLS 스키마 유효성 |
| 6 | test_openai_handle_store | handle_call("memory_store") |
| 7 | test_openai_handle_recall | handle_call("memory_recall") |
| 8 | test_openai_handle_forget | handle_call("memory_forget") |
| 9 | test_openai_unknown_function | 알 수 없는 함수 → error |
| 10 | test_adapters_init_import | from stellar_memory.adapters import ... |

---

## 8. 구현 순서 (상세)

```
Phase 1: 코어 확장 (F1)
├── 8.1  EmotionVector, TimelineEntry 모델 추가 (models.py)
├── 8.2  EmotionConfig 추가 (config.py)
├── 8.3  ScoreBreakdown.emotion_score 추가 (models.py)
├── 8.4  MemoryFunctionConfig.w_emotion 추가 (config.py)
├── 8.5  MemoryFunction._emotion_score() 추가 (memory_function.py)
├── 8.6  EmotionAnalyzer 구현 (emotion.py)
├── 8.7  StellarMemory 감정 통합 (stellar.py)
├── 8.8  MemoryItem.emotion 필드 추가 (models.py)
└── 8.9  DecayManager 감정 연동 (decay_manager.py)

Phase 2: 타임라인 (F2)
├── 8.10 MemoryStream 구현 (stream.py)
├── 8.11 StellarMemory.timeline(), narrate() 추가 (stellar.py)
└── 8.12 stream 프로퍼티 추가 (stellar.py)

Phase 3: REST API (F4)
├── 8.13 server.py 구현
├── 8.14 ServerConfig 추가 (config.py)
├── 8.15 CLI serve-api 커맨드 추가 (cli.py)
└── 8.16 StellarConfig.server 추가 (config.py)

Phase 4: 패키징 (F3)
├── 8.17 pyproject.toml 업데이트
├── 8.18 Dockerfile 작성
├── 8.19 docker-compose.yml 작성
├── 8.20 .dockerignore 작성
└── 8.21 __init__.py Public API 정리

Phase 5: SDK (F5)
├── 8.22 adapters/__init__.py 작성
├── 8.23 adapters/langchain.py 구현
├── 8.24 adapters/openai_plugin.py 구현
└── 8.25 __init__.py 어댑터 export 추가
```

---

## 9. 하위 호환성 체크리스트

| # | 항목 | 방법 |
|---|------|------|
| 1 | MemoryItem 기존 필드 유지 | `emotion: EmotionVector | None = None` (기본 None) |
| 2 | ScoreBreakdown 기존 필드 유지 | `emotion_score: float = 0.0` (기본 0.0) |
| 3 | MemoryFunction.calculate() 시그니처 유지 | 반환값에 emotion_score 추가만 |
| 4 | MemoryFunctionConfig 기존 가중치 유지 | `w_emotion: float = 0.0` (비활성) |
| 5 | StellarMemory 기존 API 유지 | store()/recall() 시그니처에 선택적 파라미터만 추가 |
| 6 | 감정 기본 비활성 | `EmotionConfig(enabled=False)` |
| 7 | CLI 기존 명령어 유지 | serve-api만 추가 |
| 8 | 기존 420 테스트 통과 | 모든 기본값이 기존 동작과 동일 |
| 9 | __init__.py 기존 export 유지 | 추가만, 삭제 없음 |
| 10 | pyproject.toml 기존 의존성 유지 | 그룹 추가만 |

---

## 10. 파일 변경 요약

### 신규 파일 (8개)

| 파일 | 기능 | 예상 줄수 |
|------|------|----------|
| `stellar_memory/emotion.py` | EmotionAnalyzer | ~120줄 |
| `stellar_memory/stream.py` | MemoryStream | ~100줄 |
| `stellar_memory/server.py` | REST API 서버 | ~200줄 |
| `stellar_memory/adapters/__init__.py` | 어댑터 패키지 | ~10줄 |
| `stellar_memory/adapters/langchain.py` | LangChain 어댑터 | ~80줄 |
| `stellar_memory/adapters/openai_plugin.py` | OpenAI 어댑터 | ~100줄 |
| `Dockerfile` | Docker 이미지 | ~20줄 |
| `docker-compose.yml` | 풀스택 구성 | ~40줄 |

### 수정 파일 (7개)

| 파일 | 변경 내용 | 변경 규모 |
|------|-----------|----------|
| `stellar_memory/models.py` | EmotionVector, TimelineEntry, MemoryItem.emotion | +60줄 |
| `stellar_memory/config.py` | EmotionConfig, ServerConfig, w_emotion | +30줄 |
| `stellar_memory/memory_function.py` | _emotion_score(), calculate() 확장 | +15줄 |
| `stellar_memory/stellar.py` | 감정/타임라인/스트림 통합 | +40줄 |
| `stellar_memory/cli.py` | serve-api 커맨드 | +15줄 |
| `stellar_memory/__init__.py` | Public API 정리 | +10줄 |
| `pyproject.toml` | 메타데이터, 의존성 그룹 | +30줄 |

### 테스트 파일 (5개)

| 파일 | 테스트 수 |
|------|----------|
| `tests/test_emotion.py` (신규) | 17개 |
| `tests/test_stream.py` (신규) | 12개 |
| `tests/test_packaging.py` (신규) | 8개 |
| `tests/test_server.py` (신규) | 15개 |
| `tests/test_adapters.py` (신규) | 10개 |
| **합계** | **62개** |

### 총 예상

| 항목 | 수량 |
|------|------|
| 신규 소스 파일 | 8개 |
| 수정 소스 파일 | 7개 |
| 신규 테스트 파일 | 5개 |
| 신규 테스트 수 | 62개 |
| 목표 총 테스트 | 482개 (420 + 62) |
| 목표 버전 | v0.8.0 |
