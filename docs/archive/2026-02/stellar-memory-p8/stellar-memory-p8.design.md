# stellar-memory-p8 Design Document

> **Summary**: 상용화 런칭 & 개발자 생태계 구축 - 기술 설계서
>
> **Project**: Stellar Memory
> **Version**: v0.8.0 → v0.9.0
> **Author**: Stellar Memory Team
> **Date**: 2026-02-17
> **Status**: Draft
> **Planning Doc**: [stellar-memory-p8.plan.md](../01-plan/features/stellar-memory-p8.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **개발자 첫인상 최적화**: README → 설치 → 첫 사용까지 5분 이내
2. **자동화된 배포**: 코드 푸시 한 번으로 PyPI + Docker Hub 동시 배포
3. **자기 문서화 API**: 코드 내 타입/설명이 곧 API 문서 (별도 관리 불필요)
4. **원클릭 AI 연결**: MCP 설정 자동 생성으로 Claude Code/Cursor 즉시 연결
5. **점진적 온보딩**: 기본 사용 → MCP → REST API → 고급 기능 순서로 안내

### 1.2 Design Principles

- **Zero Config Start**: 설치 즉시 사용 가능, 모든 설정은 합리적 기본값
- **Self-Documenting**: Pydantic 모델의 `Field(description=...)` + FastAPI 자동 생성 = 별도 문서 불필요
- **DRY Version**: `__version__`을 단일 소스로 관리, pyproject.toml/Docker/API 자동 반영
- **기존 코드 최소 변경**: P7까지 485개 테스트 0 깨짐 유지

---

## 2. Architecture

### 2.1 P8 변경 범위 다이어그램

```
                        ┌──────────────────────────────────────┐
                        │         P8: 상용화 레이어              │
                        │                                      │
  ┌──────────┐         │  ┌────────┐  ┌────────┐  ┌────────┐ │
  │ README   │────────▶│  │OpenAPI │  │ MCP    │  │  CI/CD │ │
  │ Docs     │         │  │Swagger │  │ Guide  │  │Actions │ │
  │ Examples │         │  └───┬────┘  └───┬────┘  └───┬────┘ │
  └──────────┘         │      │           │           │      │
                        │      ▼           ▼           ▼      │
                        │  ┌──────────────────────────────┐   │
                        │  │   기존 Stellar Memory 코어     │   │
                        │  │   (55 파일, 485 테스트)         │   │
                        │  └──────────────────────────────┘   │
                        └──────────────────────────────────────┘
```

### 2.2 Data Flow: 개발자 온보딩 경로

```
[README] → pip install stellar-memory
             │
             ├─ 경로 A: Python 라이브러리 ─── from stellar_memory import StellarMemory
             │                                 memory = StellarMemory()
             │                                 memory.store("hello")
             │
             ├─ 경로 B: REST API ─────────── stellar-memory serve-api
             │                                 curl localhost:9000/docs  (Swagger UI)
             │                                 curl localhost:9000/api/v1/store
             │
             ├─ 경로 C: MCP 서버 ──────────── stellar-memory init-mcp
             │                                 → claude_desktop_config.json 자동 생성
             │                                 → Claude Code에서 기억 도구 바로 사용
             │
             └─ 경로 D: Docker ─────────────── docker run stellar-memory
                                               → REST API 즉시 사용
```

### 2.3 Dependencies (신규/수정)

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| F1: README.md | 없음 | 프로젝트 진입점 |
| F1: mkdocs.yml | mkdocs-material (dev 의존성) | 문서 사이트 빌드 |
| F2: ci.yml | GitHub Actions | 테스트/빌드 자동화 |
| F2: release.yml | PyPI token, Docker Hub creds | 배포 자동화 |
| F3: _openapi.py | server.py (기존) | OpenAPI 스키마 보강 |
| F4: init-mcp | cli.py (기존) | MCP 설정 자동 생성 |
| F5: quickstart | cli.py (기존) | 대화형 설정 마법사 |

---

## 3. Feature Designs

### 3.1 F1: 제품 README & 문서화

#### 3.1.1 README.md 구조

```markdown
# <logo> Stellar Memory

> Give any AI human-like memory. Built on a celestial structure.

<badges: PyPI, Tests, License, Python versions>

<solar-system-diagram.svg - ASCII or 이미지>

## Why Stellar Memory?

3줄 비교 테이블: 기존 AI vs Stellar Memory

## Quick Start

```python
from stellar_memory import StellarMemory

memory = StellarMemory()
memory.store("User prefers dark mode", importance=0.8)
results = memory.recall("user preference")
print(results[0].content)  # "User prefers dark mode"
```

## Installation

pip install stellar-memory
pip install stellar-memory[server]  # REST API
pip install stellar-memory[full]    # 모든 기능

## Key Features

- 5-Zone Memory Hierarchy (태양계 모델)
- Black Hole Prevention (로그 함수)
- Emotional Memory (6-dim 감정 벡터)
- MCP Server (Claude Code / Cursor)
- REST API (FastAPI + Swagger)
- Multi-Agent Sync (CRDT + WebSocket)
- Adaptive Decay (사람처럼 망각)
- LangChain / OpenAI Adapters

## Use Cases (링크)
## Architecture (5존 다이어그램)
## API Reference (링크)
## MCP Setup (링크)
## Docker (링크)
## Contributing
## License (MIT)
```

#### 3.1.2 문서 사이트 (MkDocs Material)

**`mkdocs.yml` 설정**:

```yaml
site_name: Stellar Memory
site_description: Celestial-structure-based AI memory management
repo_url: https://github.com/stellar-memory/stellar-memory
theme:
  name: material
  palette:
    primary: deep purple
    accent: amber
  features:
    - content.code.copy
    - navigation.sections
    - search.suggest

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - API Reference: api-reference.md
  - Guides:
    - AI Chatbot: guides/chatbot.md
    - Personal Assistant: guides/personal-assistant.md
    - Code Assistant: guides/code-assistant.md
    - Knowledge Management: guides/knowledge-management.md
  - MCP Integration:
    - Claude Code: mcp/claude-code.md
    - Cursor: mcp/cursor.md
    - Tool Catalog: mcp/tool-catalog.md
  - REST API: rest-api.md
  - Examples: examples.md
  - Changelog: changelog.md
```

#### 3.1.3 CHANGELOG.md 형식

```markdown
# Changelog

All notable changes to Stellar Memory.

## [0.8.0] - 2026-02-17 (P7)
### Added
- Emotional Memory Engine (6-dim emotion vector)
- Memory Stream / Timeline
- REST API Server (FastAPI)
- LangChain / OpenAI adapters
- PyPI packaging + Docker support

## [0.7.0] - 2026-02-17 (P6)
### Added
- Distributed Storage (PostgreSQL + pgvector)
...
```

#### 3.1.4 Getting Started 가이드 (`docs/getting-started.md`)

```markdown
# Getting Started

## Step 1: Install (30초)
pip install stellar-memory

## Step 2: First Memory (1분)
from stellar_memory import StellarMemory
memory = StellarMemory()
item = memory.store("Hello, Stellar Memory!")
print(f"Stored in Zone {item.zone}")

## Step 3: Recall (1분)
results = memory.recall("hello")
print(results[0].content)

## Step 4: Check Stats (30초)
stats = memory.stats()
print(f"Total: {stats.total_memories}")

## Step 5: Emotional Memory (1분)
from stellar_memory import StellarConfig, EmotionConfig
config = StellarConfig(emotion=EmotionConfig(enabled=True))
memory = StellarMemory(config)
item = memory.store("Got my first customer today!")
print(f"Joy: {item.emotion.joy}")

## Next Steps
- REST API: stellar-memory serve-api
- MCP Server: stellar-memory init-mcp
- Docker: docker-compose up
```

#### 3.1.5 API Reference (`docs/api-reference.md`)

자동 생성이 아닌 **수동 큐레이션** 방식:

```markdown
# API Reference

## StellarMemory

### Constructor
StellarMemory(config=None, namespace=None)

### Core Methods
| Method | Description | Returns |
|--------|-------------|---------|
| store(content, ...) | 기억 저장 | MemoryItem |
| recall(query, ...) | 기억 검색 | list[MemoryItem] |
| forget(memory_id) | 기억 삭제 | bool |
| reorbit() | 수동 재배치 | ReorbitResult |
| stats() | 통계 조회 | MemoryStats |
| health() | 상태 진단 | HealthStatus |

### Advanced Methods
| Method | Description | Since |
|--------|-------------|:-----:|
| timeline(...) | 시간순 타임라인 | P7 |
| narrate(topic, ...) | 내러티브 생성 | P7 |
| export_json(...) | JSON 내보내기 | P2 |
| import_json(data) | JSON 가져오기 | P2 |

### Configuration
StellarConfig 전체 옵션 테이블
```

---

### 3.2 F2: 배포 파이프라인

#### 3.2.1 GitHub Actions CI (`ci.yml`)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e .[dev]

      - name: Run tests
        run: pytest --tb=short -q

      - name: Build package
        run: python -m build

      - name: Verify package
        run: |
          pip install dist/*.whl
          python -c "import stellar_memory; print(stellar_memory.__version__)"
```

#### 3.2.2 GitHub Actions Release (`release.yml`)

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  pypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Build
        run: |
          pip install build twine
          python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*

  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: stellarmemory/stellar-memory
          tags: |
            type=semver,pattern={{version}}
            type=raw,value=latest
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}

  github-release:
    runs-on: ubuntu-latest
    needs: [pypi, docker]
    steps:
      - uses: actions/checkout@v4
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

#### 3.2.3 버전 관리

**현재**: `__init__.py`에 `__version__ = "0.8.0"` 하드코딩.

**변경**: pyproject.toml의 `version` 필드를 단일 소스로 유지하되, `__init__.py`에서 `importlib.metadata`로 읽기.

```python
# stellar_memory/__init__.py (변경)
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("stellar-memory")
except PackageNotFoundError:
    __version__ = "0.9.0-dev"
```

**server.py 반영**:
```python
from stellar_memory import __version__

app = FastAPI(
    title="Stellar Memory API",
    version=__version__,
    ...
)
```

#### 3.2.4 Docker 보안 강화

```dockerfile
# Dockerfile 수정
FROM python:3.11-slim AS base

# Non-root user
RUN groupadd -r stellar && useradd -r -g stellar stellar

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY stellar_memory/ stellar_memory/

RUN pip install --no-cache-dir .[server]

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/api/v1/health')"

ENV STELLAR_DB_PATH=/data/stellar_memory.db
ENV STELLAR_HOST=0.0.0.0
ENV STELLAR_PORT=9000

EXPOSE 9000
VOLUME /data

USER stellar
CMD ["stellar-memory", "serve-api", "--host", "0.0.0.0", "--port", "9000"]
```

---

### 3.3 F3: OpenAPI 문서 보강

#### 3.3.1 설계 원칙

FastAPI는 Pydantic 모델에서 OpenAPI 스키마를 자동 생성합니다. **별도 문서 파일을 관리하지 않고**, 코드 내 타입 힌트와 설명이 곧 문서가 되도록 설계합니다.

#### 3.3.2 Pydantic 모델 보강

**현재 `server.py`의 StoreRequest**:
```python
class StoreRequest(BaseModel):
    content: str
    importance: float = Field(0.5, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)
    auto_evaluate: bool = False
```

**보강 후**:
```python
class StoreRequest(BaseModel):
    """Store a new memory in Stellar Memory."""
    content: str = Field(
        ...,
        description="The text content to memorize",
        min_length=1,
        max_length=10000,
        json_schema_extra={"examples": ["User prefers dark mode"]}
    )
    importance: float = Field(
        0.5, ge=0.0, le=1.0,
        description="Manual importance score (0.0 = trivial, 1.0 = critical)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Optional key-value metadata",
        json_schema_extra={"examples": [{"source": "chat", "topic": "preferences"}]}
    )
    auto_evaluate: bool = Field(
        False,
        description="Use AI to automatically evaluate importance (requires LLM config)"
    )

class StoreResponse(BaseModel):
    """Response after storing a memory."""
    id: str = Field(description="Unique memory ID")
    zone: int = Field(description="Assigned zone (0=Core, 1=Inner, 2=Outer, 3=Belt, 4=Cloud)")
    score: float = Field(description="Calculated importance score")

class RecallItem(BaseModel):
    """A single recalled memory item."""
    id: str = Field(description="Memory ID")
    content: str = Field(description="Memory content")
    zone: int = Field(description="Current zone")
    importance: float = Field(description="Importance score")
    recall_count: int = Field(description="Times this memory was recalled")
    emotion: dict | None = Field(None, description="Emotion vector if available")

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(description="Error description")
```

#### 3.3.3 엔드포인트 보강

**현재**:
```python
@app.post("/api/v1/store", dependencies=[...])
async def store(req: StoreRequest):
```

**보강 후**:
```python
@app.post(
    "/api/v1/store",
    response_model=StoreResponse,
    summary="Store a memory",
    description="Store new content as a memory. It will be analyzed, scored, and placed in the appropriate zone.",
    responses={
        201: {"description": "Memory stored successfully"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    tags=["Memories"],
    dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
)
async def store(req: StoreRequest):
```

#### 3.3.4 FastAPI 앱 메타데이터 보강

```python
app = FastAPI(
    title="Stellar Memory API",
    version=__version__,
    description="""
# Stellar Memory API

Celestial-structure-based AI memory management system.

## Authentication
Set `X-API-Key` header or `Authorization: Bearer <key>`.
Configure via `STELLAR_API_KEY` environment variable.

## Rate Limiting
Default: 60 requests per minute per IP.
Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## Zones
| Zone | Name | Description |
|------|------|-------------|
| 0 | Core | Most important, always accessible |
| 1 | Inner | Important memories |
| 2 | Outer | Regular memories |
| 3 | Belt | Less important |
| 4 | Cloud | Near-forgotten, auto-deleted |
""",
    openapi_tags=[
        {"name": "Memories", "description": "Store, recall, and manage memories"},
        {"name": "Timeline", "description": "Time-based memory access"},
        {"name": "System", "description": "Health, stats, and events"},
    ],
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc
)
```

#### 3.3.5 Rate Limit 헤더

```python
from starlette.responses import Response

async def check_rate_limit(request: Request, response: Response):
    # ... 기존 로직 ...
    remaining = rate_limit - len(times)
    response.headers["X-RateLimit-Limit"] = str(rate_limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    response.headers["X-RateLimit-Reset"] = str(int(now + RATE_WINDOW))
```

---

### 3.4 F4: MCP 통합 가이드 & 자동 설정

#### 3.4.1 `stellar-memory init-mcp` 명령

**CLI 추가** (`cli.py`):

```python
# init-mcp 서브커맨드
p_init_mcp = subparsers.add_parser("init-mcp", help="Generate MCP configuration for AI IDEs")
p_init_mcp.add_argument("--ide", choices=["claude", "cursor", "auto"], default="auto",
                         help="Target IDE (default: auto-detect)")
p_init_mcp.add_argument("--db", default="~/.stellar/memory.db",
                         help="Database path for MCP server")
p_init_mcp.add_argument("--dry-run", action="store_true",
                         help="Print config without writing")
```

**동작 로직**:

```python
elif args.command == "init-mcp":
    import platform
    from pathlib import Path

    ide = args.ide
    if ide == "auto":
        # Auto-detect: Claude Desktop 설정 경로 존재 여부 확인
        if _claude_config_path().exists():
            ide = "claude"
        else:
            ide = "claude"  # default

    config_content = {
        "mcpServers": {
            "stellar-memory": {
                "command": "stellar-memory",
                "args": ["serve", "--mcp"],
                "env": {
                    "STELLAR_DB_PATH": str(Path(args.db).expanduser()),
                },
            }
        }
    }

    if args.dry_run:
        print(json.dumps(config_content, indent=2))
        return

    config_path = _get_mcp_config_path(ide)
    # 기존 설정 병합 (있으면 mcpServers에 추가, 없으면 새로 생성)
    _merge_mcp_config(config_path, config_content)
    print(f"MCP configuration written to: {config_path}")
    print(f"Database path: {args.db}")
    print(f"\nRestart {ide.title()} to activate Stellar Memory tools.")


def _claude_config_path() -> Path:
    """Get Claude Desktop config path by platform."""
    system = platform.system()
    if system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"


def _get_mcp_config_path(ide: str) -> Path:
    if ide == "claude":
        return _claude_config_path()
    elif ide == "cursor":
        return Path.home() / ".cursor" / "mcp.json"
    raise ValueError(f"Unknown IDE: {ide}")


def _merge_mcp_config(path: Path, new_config: dict):
    """Merge new MCP config into existing config file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        with open(path) as f:
            existing = json.load(f)
    servers = existing.get("mcpServers", {})
    servers.update(new_config["mcpServers"])
    existing["mcpServers"] = servers
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)
```

#### 3.4.2 MCP 도구 카탈로그 (`docs/mcp/tool-catalog.md`)

```markdown
# MCP Tool Catalog

Stellar Memory provides 12 MCP tools:

## Memory Operations
| Tool | Description | Parameters |
|------|-------------|------------|
| stellar_store | Store a memory | content, importance?, metadata? |
| stellar_recall | Search memories | query, limit?, emotion? |
| stellar_forget | Delete a memory | memory_id |
| stellar_get | Get specific memory | memory_id |

## Management
| Tool | Description | Parameters |
|------|-------------|------------|
| stellar_reorbit | Trigger zone rebalance | - |
| stellar_stats | Memory statistics | - |
| stellar_health | System health check | - |
| stellar_export | Export to JSON | include_embeddings? |
| stellar_import | Import from JSON | data |

## Graph
| Tool | Description | Parameters |
|------|-------------|------------|
| stellar_graph_neighbors | Related memories | memory_id, depth? |
| stellar_graph_communities | Memory clusters | - |
| stellar_graph_path | Path between memories | source, target |
```

#### 3.4.3 Claude Code 설정 가이드 (`docs/mcp/claude-code.md`)

```markdown
# Claude Code MCP Setup

## Quick Setup (Recommended)
stellar-memory init-mcp --ide claude
# Restart Claude Desktop

## Manual Setup
Edit: ~/Library/Application Support/Claude/claude_desktop_config.json

{
  "mcpServers": {
    "stellar-memory": {
      "command": "stellar-memory",
      "args": ["serve", "--mcp"],
      "env": {
        "STELLAR_DB_PATH": "~/.stellar/memory.db"
      }
    }
  }
}

## Verify
Claude에서 "현재 기억된 내용을 보여줘" 입력
→ stellar_stats 도구가 호출되면 성공

## Usage Examples
- "이 정보를 기억해: ..." → stellar_store
- "~에 대해 기억나는 것은?" → stellar_recall
- "기억 상태 확인" → stellar_health
```

---

### 3.5 F5: 온보딩 & 데모 시스템

#### 3.5.1 `stellar-memory quickstart` 대화형 마법사

**CLI 추가** (`cli.py`):

```python
p_quickstart = subparsers.add_parser("quickstart", help="Interactive setup wizard")
```

**동작 로직**:

```python
elif args.command == "quickstart":
    _run_quickstart(args)


def _run_quickstart(args):
    """Interactive quickstart wizard."""
    print("=" * 50)
    print("  Welcome to Stellar Memory!")
    print("  Celestial-structure AI memory system")
    print("=" * 50)
    print()

    # Step 1: 사용 목적
    print("How will you use Stellar Memory?")
    print("  1. Python library (import in your code)")
    print("  2. REST API server (HTTP endpoints)")
    print("  3. MCP server (Claude Code / Cursor)")
    print("  4. Docker container")
    choice = input("\nSelect [1-4, default=1]: ").strip() or "1"

    # Step 2: DB 경로
    db_path = input(f"\nDatabase path [default: stellar_memory.db]: ").strip()
    db_path = db_path or "stellar_memory.db"

    # Step 3: 감정 분석
    enable_emotion = input("Enable emotion analysis? [y/N]: ").strip().lower() == "y"

    # Step 4: 설정 생성 + 첫 기억 저장
    from stellar_memory import StellarMemory, StellarConfig, EmotionConfig
    config = StellarConfig(
        db_path=db_path,
        emotion=EmotionConfig(enabled=enable_emotion),
    )
    memory = StellarMemory(config)
    item = memory.store("Hello, Stellar Memory! This is my first memory.", importance=0.9)

    print(f"\nYour first memory is stored!")
    print(f"  ID:   {item.id[:8]}...")
    print(f"  Zone: {item.zone} ({'Core' if item.zone == 0 else 'Inner'})")
    if item.emotion:
        print(f"  Emotion: {item.emotion.dominant} ({item.emotion.intensity:.2f})")

    # Step 5: 다음 단계 안내
    if choice == "2":
        print(f"\nStart REST API server:")
        print(f"  stellar-memory serve-api --db {db_path}")
        print(f"  Open http://localhost:9000/docs for Swagger UI")
    elif choice == "3":
        print(f"\nSetup MCP for Claude Code:")
        print(f"  stellar-memory init-mcp --db {db_path}")
    elif choice == "4":
        print(f"\nRun with Docker:")
        print(f"  docker-compose up stellar")
    else:
        print(f"\nTry recalling your memory:")
        print(f'  stellar-memory recall "hello" --db {db_path}')

    print(f"\nDocumentation: https://stellar-memory.readthedocs.io")
    memory.stop()
```

#### 3.5.2 예제 프로젝트 3종

**`examples/basic/main.py`**:
```python
"""Basic Stellar Memory usage in 10 lines."""
from stellar_memory import StellarMemory

memory = StellarMemory()

# Store memories with different importance
memory.store("Python was created by Guido van Rossum", importance=0.7)
memory.store("The weather is nice today", importance=0.2)
memory.store("Project deadline is March 1st", importance=0.9)

# Recall relevant memories
results = memory.recall("project deadline")
for item in results:
    print(f"[Zone {item.zone}] {item.content}")

# Check stats
stats = memory.stats()
print(f"\nTotal: {stats.total_memories} memories across 5 zones")
memory.stop()
```

**`examples/chatbot/main.py`**:
```python
"""LangChain chatbot with persistent memory."""
from stellar_memory import StellarMemory, StellarConfig, EmotionConfig
from stellar_memory.adapters import StellarLangChainMemory

config = StellarConfig(
    db_path="chatbot_memory.db",
    emotion=EmotionConfig(enabled=True),
)
memory = StellarMemory(config)
lc_memory = StellarLangChainMemory(memory)

# Use with any LangChain chain
# chain = ConversationChain(llm=llm, memory=lc_memory)

# Manual demo
memory.store("User's name is Alice", importance=0.9)
memory.store("User likes Python and dark mode", importance=0.7)
memory.store("Had a great conversation about AI", importance=0.5)

# Recall for context building
context = lc_memory.load_memory_variables({"input": "Tell me about the user"})
print(context)
memory.stop()
```

**`examples/mcp-agent/README.md`**:
```markdown
# MCP Agent Example

## Setup
1. pip install stellar-memory
2. stellar-memory init-mcp
3. Restart Claude Desktop

## Usage
In Claude Code, try:
- "Remember that my favorite color is blue"
- "What's my favorite color?"
- "Show my memory stats"
```

---

## 4. File Changes Summary

### 4.1 New Files

| File | Feature | Description |
|------|:-------:|-------------|
| `README.md` | F1 | 제품 README |
| `CHANGELOG.md` | F1 | 전체 변경 이력 |
| `CONTRIBUTING.md` | F1 | 기여 가이드 |
| `mkdocs.yml` | F1 | 문서 사이트 설정 |
| `docs/index.md` | F1 | 문서 홈페이지 |
| `docs/getting-started.md` | F1 | 빠른 시작 가이드 |
| `docs/api-reference.md` | F1 | API 레퍼런스 |
| `docs/rest-api.md` | F1 | REST API 가이드 |
| `docs/changelog.md` | F1 | 변경 이력 (symlink) |
| `docs/guides/chatbot.md` | F1 | 챗봇 가이드 |
| `docs/guides/personal-assistant.md` | F1 | 개인 비서 가이드 |
| `docs/guides/code-assistant.md` | F1 | 코드 어시스턴트 가이드 |
| `docs/guides/knowledge-management.md` | F1 | 지식 관리 가이드 |
| `docs/mcp/claude-code.md` | F4 | Claude Code MCP 설정 |
| `docs/mcp/cursor.md` | F4 | Cursor MCP 설정 |
| `docs/mcp/tool-catalog.md` | F4 | MCP 도구 카탈로그 |
| `.github/workflows/ci.yml` | F2 | CI 파이프라인 |
| `.github/workflows/release.yml` | F2 | Release 파이프라인 |
| `examples/basic/main.py` | F5 | 기본 예제 |
| `examples/chatbot/main.py` | F5 | 챗봇 예제 |
| `examples/mcp-agent/README.md` | F5 | MCP 에이전트 예제 |

### 4.2 Modified Files

| File | Feature | Changes |
|------|:-------:|---------|
| `stellar_memory/__init__.py` | F2 | `__version__`을 importlib.metadata로 변경 |
| `stellar_memory/server.py` | F3 | Pydantic 모델 보강, OpenAPI 메타데이터, response_model, tags, Rate Limit 헤더 |
| `stellar_memory/cli.py` | F4, F5 | `init-mcp`, `quickstart` 서브커맨드 추가 |
| `Dockerfile` | F2 | non-root user, HEALTHCHECK 추가 |
| `pyproject.toml` | F2 | `build-system`, docs extras 추가 |

### 4.3 Unchanged Files (485 테스트 보호)

기존 55개 소스 파일 중 `__init__.py`, `server.py`, `cli.py` 3개만 수정. 나머지 52개는 **변경 없음**. 기존 485개 테스트 100% 통과 유지.

---

## 5. Test Plan

### 5.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| Unit Test | init-mcp 로직, quickstart 로직, Pydantic 모델 | pytest |
| Integration Test | CI workflow dry-run, Docker 빌드 | pytest + subprocess |
| Package Test | pip install → import → 기본 동작 | pytest |
| API Test | Swagger UI 렌더링, 응답 스키마 검증 | pytest + httpx |

### 5.2 Test Cases

#### F1: README & Docs
- [ ] mkdocs build 성공 (no warnings)
- [ ] 모든 문서 내 코드 예제 실행 가능

#### F2: CI/CD
- [ ] `python -m build` 성공
- [ ] `pip install dist/*.whl` 후 `import stellar_memory` 성공
- [ ] `__version__` 일치 (pyproject.toml == __init__.py)
- [ ] Docker build 성공
- [ ] Docker health check 통과

#### F3: OpenAPI
- [ ] `/docs` 접근 시 Swagger UI 렌더링
- [ ] `/redoc` 접근 시 ReDoc 렌더링
- [ ] `/openapi.json` 스키마에 모든 엔드포인트 포함
- [ ] 각 엔드포인트 description/examples 존재
- [ ] Rate Limit 헤더 (X-RateLimit-*) 반환
- [ ] ErrorResponse 모델 일관 사용

#### F4: MCP
- [ ] `stellar-memory init-mcp --dry-run` 유효한 JSON 출력
- [ ] `init-mcp --ide claude` 올바른 경로에 파일 생성
- [ ] `init-mcp --ide cursor` 올바른 경로에 파일 생성
- [ ] 기존 MCP 설정이 있을 때 병합 (덮어쓰기 아님)

#### F5: Quickstart & Examples
- [ ] `stellar-memory quickstart` 대화형 실행 + 첫 기억 저장
- [ ] `examples/basic/main.py` 실행 성공
- [ ] `examples/chatbot/main.py` 실행 성공 (어댑터 없이도)

### 5.3 예상 테스트 수

| Category | New Tests | Total |
|----------|:---------:|:-----:|
| 기존 | - | 485 |
| F2: 패키지 빌드/버전 | 5 | |
| F3: OpenAPI/API 스키마 | 15 | |
| F4: init-mcp | 10 | |
| F5: quickstart/examples | 8 | |
| F1: 문서 코드 검증 | 7 | |
| **합계** | **45** | **530** |

---

## 6. Implementation Order

```
Phase 1 (Day 1-2): 기반 작업
  1. __init__.py 버전 관리 변경 (importlib.metadata)
  2. Dockerfile 보안 강화 (non-root, healthcheck)
  3. pyproject.toml extras 업데이트
  4. .github/workflows/ci.yml 작성
  5. .github/workflows/release.yml 작성

Phase 2 (Day 3-4): API 문서화
  6. server.py Pydantic 모델 보강 (StoreResponse, RecallItem, ErrorResponse)
  7. server.py 엔드포인트 메타데이터 (summary, description, tags, responses)
  8. server.py Rate Limit 헤더 추가
  9. server.py FastAPI 앱 메타데이터 보강

Phase 3 (Day 5-6): CLI 확장
  10. cli.py init-mcp 서브커맨드 + 헬퍼 함수
  11. cli.py quickstart 서브커맨드

Phase 4 (Day 7-8): 문서 작성
  12. README.md
  13. CHANGELOG.md
  14. CONTRIBUTING.md
  15. docs/getting-started.md
  16. docs/api-reference.md
  17. docs/rest-api.md
  18. docs/mcp/ (claude-code.md, cursor.md, tool-catalog.md)
  19. docs/guides/ (4개 가이드)
  20. mkdocs.yml

Phase 5 (Day 9): 예제 & 마무리
  21. examples/ (basic, chatbot, mcp-agent)
  22. 테스트 작성 (45개)
  23. 전체 테스트 실행 (530개 목표)
  24. 빌드 검증 (PyPI + Docker)
```

---

## 7. Security Considerations

- [x] API 키 인증 (기존 구현)
- [x] Rate Limiting (기존 구현, 헤더 추가)
- [x] CORS 설정 (기존 구현)
- [ ] Docker non-root 유저 (P8 추가)
- [ ] Docker HEALTHCHECK (P8 추가)
- [ ] CI 시크릿 관리 (GitHub Secrets)
- [ ] .env 파일 .gitignore 확인
- [ ] 예제 코드에 API 키 하드코딩 금지

---

## 8. Backward Compatibility

| 항목 | 보장 |
|------|:----:|
| 기존 `from stellar_memory import *` | 100% |
| 기존 StellarConfig 기본값 | 100% |
| 기존 CLI 명령어 | 100% (신규 추가만) |
| 기존 REST API 엔드포인트 | 100% (보강만, 변경 없음) |
| 기존 MCP 도구 | 100% |
| 기존 485개 테스트 | 100% 통과 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | 초안 - P8 상용화 런칭 Design | Stellar Memory Team |
