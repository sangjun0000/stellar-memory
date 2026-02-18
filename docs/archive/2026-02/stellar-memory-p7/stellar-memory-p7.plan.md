# Plan: stellar-memory-p7

> **Feature**: AI 기억 플러그인 - 천체구조 기반 독립 기억 모듈 상용화
> **Version**: v0.8.0
> **Created**: 2026-02-17
> **Status**: Draft

---

## 1. 개요

### 1.1 배경

P1~P6을 통해 Stellar Memory는 420개 테스트, 47개 소스 파일, 평균 97% 설계 일치율을 달성한 엔터프라이즈급 기억 플랫폼이 되었습니다. 그러나 현재 구조는 **독립 라이브러리** 형태이며, 기존 AI(Claude, GPT, Gemini 등)에 **즉시 삽입(plug-in)** 하기에는 진입 장벽이 존재합니다.

P7의 핵심 목표는 **"기존 AI에 삽입할 수 있는 독립 기억 프로그램"** 을 만드는 것입니다.

### 1.2 핵심 철학

우주의 천체구조를 모방한 기억 시스템:

```
┌─────────────────────────────────────────────────────┐
│                   Oort Cloud (Cloud)                 │
│        ┌─────────────────────────────────┐           │
│        │       Asteroid Belt (Belt)       │           │
│        │    ┌───────────────────────┐     │           │
│        │    │    Outer Planets      │     │           │
│        │    │  ┌─────────────────┐  │     │           │
│        │    │  │  Inner Planets  │  │     │           │
│        │    │  │  ┌───────────┐  │  │     │           │
│        │    │  │  │   ☀ Sun   │  │  │     │           │
│        │    │  │  │  (Core)   │  │  │     │           │
│        │    │  │  │ 핵심 기억 │  │  │     │           │
│        │    │  │  └───────────┘  │  │     │           │
│        │    │  │  자주 쓰는 기억 │  │     │           │
│        │    │  └─────────────────┘  │     │           │
│        │    │    일반 기억          │     │           │
│        │    └───────────────────────┘     │           │
│        │       희미한 기억                │           │
│        └─────────────────────────────────┘           │
│                   잊혀지는 기억 → 자동 삭제           │
└─────────────────────────────────────────────────────┘
```

**기억 함수 (Memory Function)**:
```
I(m) = w₁·R(m) + w₂·F(m) + w₃·A(m) + w₄·C(m) + w₅·E(m)

R(m) = log(recall_count + 1) / log(max_recall + 1)
       → 로그 함수로 블랙홀 방지 (아무리 리콜해도 임계값 초과 불가)

F(m) = -α × (현재시간 - 마지막_리콜_시간)
       → 리콜 시 0으로 초기화, 이후 음수로 절대값 증가

A(m) = AI가 내용 분석하여 자동 판단 (0.0~1.0)
       → 임의 중요도: AI가 알아서 판단

C(m) = 현재 대화와의 관련성 (컨텍스트 점수)

E(m) = 감정 강도 (P7 신규) - 감정이 강한 기억은 더 오래 유지
```

**블랙홀 방지 메커니즘**:
- **리콜 점수**: `log` 함수 적용 → 아무리 자주 호출해도 임계값 불가
- **신선도**: 리콜 후 0 초기화, 미리콜 시 음수 증가 → 자연 망각
- **임의 중요도**: AI 자체 판단 → 과도한 집중 방지
- 결과: 주기적 재배치(reorbit)로 사람처럼 기억 관리

### 1.3 목표

| 목표 | 설명 |
|------|------|
| **AI 플러그인화** | 어떤 AI에든 3줄 코드로 기억 능력 부여 |
| **감성 기억** | 감정 차원 추가로 인간과 더 유사한 기억 |
| **상용화 패키징** | PyPI, Docker, REST API 서버 모드 |
| **SDK & 문서** | 개발자가 바로 쓸 수 있는 완전한 패키지 |
| **MCP 원클릭** | Claude Code 등 MCP 지원 AI에 즉시 연결 |

---

## 2. 기능 명세

### F1: 감성 기억 엔진 (Emotional Memory Engine)

**우선순위**: High | **복잡도**: Medium | **신규 파일**: 2개

감정이 기억의 수명과 중요도에 영향을 미치는 인간 유사 기억 시스템.

**요구사항**:
- `EmotionAnalyzer` 클래스: 텍스트에서 감정 벡터 추출
  - 6가지 기본 감정: joy, sadness, anger, fear, surprise, disgust
  - 감정 강도(intensity): 0.0~1.0 float
  - LLM 기반 분석 + 규칙 기반 fallback (LLM 없을 때)
- 기억 함수 확장: `I(m) += w₅·E(m)`
  - E(m) = max(emotion_vector) × emotion_intensity
  - 감정 가중치 w₅ 기본값: 0.15
- 감정 기반 검색: `recall(query, emotion="joy")`
  - 특정 감정 필터링, 감정 유사도 기반 정렬
- 감정 기반 Decay 조절:
  - 감정 강도 > 0.7 → decay_rate × 0.5 (천천히 잊음)
  - 감정 강도 < 0.3 → decay_rate × 1.5 (빨리 잊음)

**구현 파일**:
- `stellar_memory/emotion.py` (EmotionAnalyzer, EmotionVector)
- `stellar_memory/models.py` (EmotionData 모델 추가)
- `stellar_memory/memory_function.py` (E(m) 항 추가)
- `stellar_memory/config.py` (emotion 설정 추가)

**테스트**: 15+개
- 감정 분석 정확도, 감정 기반 검색, Decay 조절, 기억 함수 통합

---

### F2: 기억 스트림 & 타임라인 (Memory Stream)

**우선순위**: Medium | **복잡도**: Medium | **신규 파일**: 1개

시간순 기억 흐름과 내러티브 생성.

**요구사항**:
- `MemoryStream` 클래스:
  - `timeline(start, end)`: 시간 범위 내 기억 시간순 조회
  - `narrate(topic)`: LLM이 기억들을 엮어 스토리 형태로 정리
  - `summarize_period(start, end)`: 특정 기간 자동 요약
- 타임라인 포맷:
  ```python
  [
    {"time": "2026-02-01 10:00", "content": "...", "zone": "Core", "emotion": "joy"},
    {"time": "2026-02-01 14:30", "content": "...", "zone": "Inner", "emotion": "neutral"},
  ]
  ```
- 구간 자동 요약: 긴 타임라인은 LLM으로 구간별 요약 생성
- StellarMemory 메인 클래스에 `timeline()`, `narrate()` 메서드 추가

**구현 파일**:
- `stellar_memory/stream.py` (MemoryStream)
- `stellar_memory/stellar.py` (timeline/narrate 메서드 추가)

**테스트**: 12+개
- 시간 범위 조회, 정렬 정확도, 내러티브 생성, 빈 구간 처리

---

### F3: PyPI 패키지 & Docker 이미지

**우선순위**: Critical | **복잡도**: High | **신규 파일**: 4개

실제 사용자가 바로 설치/실행할 수 있는 패키징.

**요구사항**:
- PyPI 패키지:
  ```bash
  pip install stellar-memory                  # 코어만
  pip install stellar-memory[ai]              # + LLM 프로바이더
  pip install stellar-memory[postgres]        # + PostgreSQL
  pip install stellar-memory[full]            # 모든 기능
  pip install stellar-memory[server]          # + REST API 서버
  ```
- `pyproject.toml` 정리:
  - 의존성 그룹 정리 (core, ai, postgres, redis, security, sync, connectors, dashboard, server, full)
  - 진입점(entry_points): `stellar-memory` CLI, `stellar-memory-server` REST API
  - 메타데이터: 설명, 라이선스, 분류자, README
- Dockerfile:
  ```dockerfile
  # 코어 이미지
  FROM python:3.11-slim
  RUN pip install stellar-memory[server]
  CMD ["stellar-memory", "serve"]
  ```
  - Multi-stage build: 빌드/실행 분리
  - 환경변수로 설정: `STELLAR_DB_PATH`, `STELLAR_LLM_PROVIDER`, etc.
- docker-compose.yml: 풀스택 (stellar + postgres + redis)

**구현 파일**:
- `pyproject.toml` (수정 - 패키지 메타데이터 완성)
- `Dockerfile` (신규)
- `docker-compose.yml` (신규)
- `.dockerignore` (신규)
- `stellar_memory/__init__.py` (public API 정리)

**테스트**: 8+개
- 패키지 임포트, CLI 진입점, 환경변수 설정, public API 노출

---

### F4: REST API 서버 모드 (Standalone Server)

**우선순위**: High | **복잡도**: High | **신규 파일**: 2개

독립 실행 가능한 REST API 서버로, 어떤 AI/앱에서든 HTTP로 기억 접근.

**요구사항**:
- FastAPI 기반 REST API 서버:
  ```
  POST   /api/v1/store          기억 저장
  GET    /api/v1/recall          기억 검색 (query param)
  DELETE /api/v1/forget/{id}     기억 삭제
  GET    /api/v1/memories        전체 기억 목록 (페이지네이션)
  GET    /api/v1/timeline        타임라인 조회
  POST   /api/v1/narrate         내러티브 생성
  GET    /api/v1/stats           통계
  GET    /api/v1/health          헬스체크
  GET    /api/v1/events          SSE 실시간 이벤트
  ```
- API 키 인증: `X-API-Key` 헤더 또는 Bearer 토큰
- CORS 설정: 기본 허용, 설정으로 제한 가능
- OpenAPI(Swagger) 자동 문서 생성
- CLI 통합: `stellar-memory serve --host 0.0.0.0 --port 9000`
- Rate Limiting: 분당 요청 제한 (기본 60/분)

**구현 파일**:
- `stellar_memory/server.py` (FastAPI 앱, 라우트, 미들웨어)
- `stellar_memory/cli.py` (serve 커맨드 추가)
- `stellar_memory/config.py` (ServerConfig 추가)

**테스트**: 15+개
- 각 엔드포인트 CRUD, 인증, CORS, rate limit, SSE

---

### F5: AI 플러그인 SDK & 문서화

**우선순위**: High | **복잡도**: Medium | **신규 파일**: 3개

3줄 코드로 기존 AI에 기억 능력을 부여하는 SDK.

**요구사항**:
- **Quick Start SDK**:
  ```python
  from stellar_memory import StellarMemory

  # 3줄로 AI에 기억 부여
  memory = StellarMemory()
  memory.store("사용자가 Python을 선호한다고 말함")
  context = memory.recall("사용자의 프로그래밍 선호도")
  ```
- **AI 프레임워크 어댑터**:
  - `LangChainAdapter`: LangChain Memory 인터페이스 구현
  - `OpenAIPlugin`: OpenAI function calling 스키마 제공
  - `MCPAdapter`: MCP 프로토콜 표준 어댑터 (이미 구현, 정리)
- **Public API 정리**:
  - `__init__.py`에서 핵심 클래스만 export
  - 내부 모듈은 `_` prefix로 비공개 표시
  - `__all__` 리스트 관리
- **문서화**:
  - `README.md`: 프로젝트 소개, Quick Start, 설치 방법
  - `docs/guide/`: 사용자 가이드 (getting-started, configuration, api-reference)
  - docstring: 모든 public 메서드에 Google style docstring
  - 사용 예시 코드: `examples/` 디렉토리

**구현 파일**:
- `stellar_memory/adapters/langchain.py` (LangChain 어댑터)
- `stellar_memory/adapters/openai_plugin.py` (OpenAI 어댑터)
- `stellar_memory/adapters/__init__.py`
- `stellar_memory/__init__.py` (public API 정리)
- `README.md` (프로젝트 소개)
- `examples/quick_start.py`
- `examples/with_langchain.py`
- `examples/with_mcp.py`

**테스트**: 10+개
- 어댑터 인터페이스 호환, public API 노출, import 확인

---

## 3. 기술 스택

### 3.1 기존 기술 (유지)

| 카테고리 | 기술 |
|----------|------|
| 언어 | Python 3.10+ |
| 스토리지 | SQLite (기본), PostgreSQL+pgvector, Redis |
| AI | OpenAI, Ollama, Null (테스트) |
| 프로토콜 | MCP (Model Context Protocol) |
| 벡터 | FAISS, BallTree, BruteForce |
| 동기화 | CRDT LWW-Register, WebSocket |
| 보안 | AES-256-GCM, RBAC, 감사로그 |

### 3.2 P7 추가 기술

| 카테고리 | 기술 | 용도 |
|----------|------|------|
| 서버 | FastAPI + Uvicorn | REST API 서버 모드 |
| 패키징 | setuptools + pyproject.toml | PyPI 배포 |
| 컨테이너 | Docker + docker-compose | 원클릭 실행 |
| 감정 분석 | LLM 기반 + 규칙 fallback | EmotionAnalyzer |
| 문서 | mkdocs or pdoc | API 레퍼런스 자동 생성 |
| 어댑터 | LangChain, OpenAI schema | AI 프레임워크 통합 |

---

## 4. 구현 순서

```
F1 (감성 기억)  ─→  F2 (타임라인)  ─→  F4 (REST API)
                                           │
                    F3 (PyPI/Docker) ←──────┤
                                           │
                    F5 (SDK/문서화)  ←──────┘
```

| 순서 | 기능 | 의존성 | 예상 규모 |
|:----:|------|--------|-----------|
| 1 | F1: 감성 기억 | 없음 (코어 확장) | 신규 2파일, 수정 3파일 |
| 2 | F2: 타임라인 | F1 (감정 데이터 활용) | 신규 1파일, 수정 1파일 |
| 3 | F4: REST API | F1, F2 (전체 기능 노출) | 신규 1파일, 수정 2파일 |
| 4 | F3: PyPI/Docker | F4 (서버 모드 포함) | 신규 3파일, 수정 2파일 |
| 5 | F5: SDK/문서화 | F1~F4 (전체 완성 후) | 신규 6+파일, 수정 2파일 |

---

## 5. 하위 호환성

### 5.1 호환성 원칙 (P1~P6 전통 유지)

- 기존 420개 테스트 100% 통과 유지
- `StellarMemory` 기존 API 변경 없음 (추가만 허용)
- 감성 기억은 선택적 (기본 비활성, `config.emotion.enabled=True`로 활성화)
- REST API 서버는 별도 진입점 (`stellar-memory serve`)
- 모든 P7 기능은 기존 설치에 영향 없음

### 5.2 선택적 의존성 확장

```toml
[project.optional-dependencies]
# 기존 유지
postgres = ["asyncpg>=0.29"]
redis = ["redis>=5.0"]
security = ["cryptography>=41.0"]
sync = ["websockets>=12.0"]
connectors = ["aiohttp>=3.9", "watchdog>=3.0"]
dashboard = ["fastapi>=0.109", "uvicorn>=0.27"]

# P7 신규
ai = ["openai>=1.0"]
server = ["fastapi>=0.109", "uvicorn>=0.27", "python-multipart>=0.0.6"]
adapters = ["langchain-core>=0.1"]
full = ["stellar-memory[ai,postgres,redis,security,sync,connectors,dashboard,server,adapters]"]
```

---

## 6. 성공 기준

| 기준 | 목표 |
|------|------|
| 테스트 수 | 480+ (현재 420 + 60 신규) |
| 설계 일치율 | 90%+ |
| 기존 테스트 통과 | 420/420 (하위 호환) |
| PyPI 설치 가능 | `pip install stellar-memory` 성공 |
| Docker 실행 | `docker run` 으로 서버 기동 |
| REST API 동작 | store/recall/forget/timeline 엔드포인트 |
| 3줄 Quick Start | 코드 3줄로 기억 저장/검색 가능 |
| LangChain 호환 | LangChain Memory 인터페이스 구현 |
| 감정 기반 검색 | `recall(query, emotion="joy")` 동작 |

---

## 7. 리스크 및 완화

| 리스크 | 영향 | 완화 방안 |
|--------|------|-----------|
| 감정 분석 정확도 | Medium | LLM + 규칙 기반 이중 분석, fallback |
| PyPI 패키지 충돌 | Low | 선택적 의존성으로 최소 코어 유지 |
| REST API 보안 | High | API 키 인증, Rate Limiting, CORS |
| Docker 이미지 크기 | Low | Multi-stage build, slim 베이스 |
| LangChain 버전 호환 | Medium | langchain-core만 의존, 최소 인터페이스 |
| 기존 API 깨짐 | Critical | 420 테스트 회귀 방지, 추가만 허용 |

---

## 8. 예상 산출물

| 항목 | 수량 |
|------|------|
| 신규 소스 파일 | 8~10개 |
| 수정 소스 파일 | 6~8개 |
| 신규 테스트 | 60+개 |
| 목표 총 테스트 | 480+개 |
| 문서 파일 | 4+개 (README, 가이드, 예시) |
| 설정 파일 | 3개 (Dockerfile, docker-compose, .dockerignore) |
| 목표 버전 | v0.8.0 |
