# CLAUDE.md

## Project Overview

Stellar Memory는 천체 구조(태양계) 기반 AI 기억 관리 플랫폼입니다. 현재 버전 v3.0.0.

**핵심 아이디어**: 기억을 태양계 5존(Core/Inner/Outer/Belt/Cloud)에 배치하고, 중요도에 따라 자동 승격/강등/삭제합니다. 기억 함수 `I(m) = w1*R + w2*F + w3*A + w4*C + w5*E`로 점수를 계산하며, 로그-캡으로 블랙홀(모든 기억이 Core로 몰림) 방지. CE v2에서 리콜-리셋 신선도(리콜하면 F=0 리셋) 도입.

**제품 3종**:
- **Stellar Memory SDK** (Python): MCP 서버, REST API, CLI 제공. `pip install stellar-memory`
- **Celestial Engine v2**: 독립 플러그인 모듈. 3줄로 어떤 AI에든 삽입. Zero dependencies.
- **Chrome Extension**: ChatGPT/Claude/Gemini 웹에서 대화 자동 기억. Manifest V3.

**Homunculus** (별도 레포 `sangjun0000/homunculus`): Stellar Memory를 두뇌로 사용하는 자율 AI 에이전트. 풀스크린 TUI 인터페이스. Python.

## Tech Stack

- **코어**: Python 3.10+, SQLite WAL, 외부 의존성 0 (optional: PostgreSQL, Redis, FAISS)
- **서버**: FastAPI, Pydantic, SSE
- **Chrome Extension**: TypeScript, React 18, Vite, @crxjs/vite-plugin, Tailwind CSS, Vitest
- **인프라**: Docker, Fly.io, GitHub Actions CI/CD
- **문서**: MkDocs Material
- **랜딩**: 단일 HTML (landing/index.html), 인라인 CSS/JS, i18n 5개 언어 (EN/KO/ZH/ES/JA)

## Project Structure

```
stellar_memory/          # 코어 SDK (60개 파일)
├── stellar.py           # StellarMemory 메인 클래스
├── memory_function.py   # 기억 함수 I(m) 계산
├── mcp_server.py        # MCP 서버 (17개 도구)
├── server.py            # REST API (15개 엔드포인트)
├── cli.py               # CLI (20개 명령)
├── emotion.py           # 감정 분석 (6차원)
├── billing/             # 결제 시스템 (Stripe/Lemon Squeezy/Toss)
├── storage/             # SQLite, PostgreSQL, Redis
├── security/            # AES-256-GCM, RBAC
├── sync/                # CRDT + WebSocket
└── adapters/            # LangChain, OpenAI

celestial_engine/        # 독립 기억 엔진 v2 (13개 파일)
├── memory_function.py   # 기억함수 v2 (리콜-리셋)
├── zone_manager.py      # 5존 관리
└── adapters/            # LangChain, OpenAI, Anthropic MCP

stellar-chrome/          # Chrome Extension (TypeScript + React)
├── src/content/         # Content Scripts (ChatGPT/Claude/Gemini)
├── src/popup/           # Popup UI (React)
├── src/sidepanel/       # Side Panel UI (React)
├── src/background/      # Service Worker
└── tests/               # Vitest 48개 테스트

landing/index.html       # 랜딩 페이지 (단일 파일, ~3300줄)
tests/                   # Python 테스트 603개
docs/                    # MkDocs 문서 + PDCA 아카이브
```

## Key Numbers

- 총 테스트: 651개 (603 Python + 48 Extension)
- PDCA 사이클: 15개 완료, 평균 설계 일치율 97.1%
- 가격 티어: Free/Pro($29)/Team($99)/Enterprise
- 배포: PyPI, Docker, Fly.io, GitHub Pages (랜딩)

## Common Commands

- Python 테스트: `pytest tests/ -v`
- Extension 빌드: `cd stellar-chrome && npm run build`
- Extension 테스트: `cd stellar-chrome && npm test`
- MCP 서버: `stellar-memory serve`
- REST API: `stellar-memory server`
- 문서 서버: `mkdocs serve`
- 랜딩 배포: `git checkout gh-pages && cp landing/index.html index.html`

## Coding Conventions

- Python: snake_case, dataclass 선호, NullProvider 패턴 (LLM 없이도 동작)
- TypeScript: react-jsx transform (import React 불필요), strict mode
- 랜딩 i18n: `const T = { en: {...}, ko: {...}, zh: {...}, es: {...}, ja: {...} }` + `data-i18n` 속성
- 모든 기능 opt-in: `enabled=False` 기본값, 하위 호환 100%

## Important Notes

- 랜딩 페이지는 단일 HTML 파일. CSS/JS/i18n 모두 인라인. 수정 시 줄 번호 주의.
- gh-pages 브랜치에서 랜딩 서빙. main 수정 후 gh-pages에도 복사 필요.
- Chrome Extension 다운로드: GitHub Release `chrome-ext-v1.0.0` 태그의 .zip 직접 다운로드 링크 사용.
- PDCA 문서: `docs/archive/2026-02/` 에 아카이브됨.
- `.pdca-status.json`이 hook에 의해 초기화될 수 있음 — 수동 복원 필요할 수 있음.
- GitHub: `sangjun0000/stellar-memory` (메인 레포), `sangjun0000/homunculus` (에이전트 레포)
