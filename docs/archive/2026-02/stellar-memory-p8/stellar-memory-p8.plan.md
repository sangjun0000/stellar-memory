# stellar-memory-p8 Planning Document

> **Summary**: 상용화 런칭 & 개발자 생태계 구축 - "AI 메모리의 표준을 만든다"
>
> **Project**: Stellar Memory
> **Version**: v0.8.0 → v0.9.0
> **Author**: Stellar Memory Team
> **Date**: 2026-02-17
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

P7까지 기술적 완성도를 확보했으나, **실제 사용자가 0명**인 상태입니다. 세계 최고의 기억 엔진도 아무도 쓰지 않으면 의미가 없습니다.

P8의 목적은 단 하나: **"첫 1,000명의 개발자가 `pip install stellar-memory`를 실행하게 만드는 것"**

수익화 전략 Phase 1(인지도 확보)과 Phase 2(첫 수익)의 기술적 기반을 모두 이번 단계에서 구축합니다.

### 1.2 Background

**수익화 전략 분석 결과**:

수익화 전략 문서에서 5가지 수익 모델(SaaS Cloud, MCP 마켓플레이스, API as a Service, 엔터프라이즈 라이선스, 교육/컨설팅)을 제안했으며, 추천 전략은 **오픈 코어 + SaaS**입니다.

그러나 전략 문서에서 한 가지 수정이 필요합니다:

> **수정 사항**: 전략 문서는 v0.7.0 기준으로 작성되었으나, P7에서 이미 REST API 서버, Docker, PyPI 패키징, LangChain/OpenAI 어댑터가 구현 완료되었습니다. 따라서 "Quick Win" 항목의 상당 부분은 이미 기술적으로 준비되어 있으며, P8은 **실제 배포와 사용자 획득**에 집중해야 합니다.

**현재 준비 상태**:

| 수익화 전략 항목 | 기술 구현 상태 | P8에서 필요한 작업 |
|-----------------|:------------:|-------------------|
| PyPI 배포 | pyproject.toml 완성 | 실제 빌드/업로드 + 의존성 검증 |
| Docker 이미지 | Dockerfile 완성 | Docker Hub 푸시 + 태그 관리 |
| REST API | server.py 완성 | API 문서(OpenAPI) + 인증 강화 |
| MCP 서버 | mcp_server.py 완성 | 설정 가이드 + 마켓플레이스 등록 준비 |
| LangChain 어댑터 | adapters/ 완성 | 사용 예제 + 통합 가이드 |
| 대시보드 | dashboard/ 완성 | 데모 페이지 준비 |
| README | **없음** | 제품 수준 README 작성 필수 |
| 랜딩 페이지 | 없음 | stellarmemory.io 준비 |
| 사용 가이드 | 없음 | 빠른 시작 ~ 고급 사용법 문서 |
| Cloud SaaS | 없음 | Free 티어 인프라 (P9 범위) |

### 1.3 Related Documents

- 수익화 전략: `docs/stellar-memory-수익화전략.md`
- 종합 보고서: `docs/stellar-memory-종합보고서.md`
- P7 아카이브: `docs/archive/2026-02/stellar-memory-p7/`

---

## 2. Scope

### 2.1 In Scope

- [ ] F1: 제품 README & 문서화 - 개발자가 3분 안에 시작할 수 있는 문서
- [ ] F2: PyPI/Docker 배포 파이프라인 - 실제 배포 가능한 CI/CD
- [ ] F3: OpenAPI 문서 & 인터랙티브 API 탐색기 - Swagger/ReDoc 자동 생성
- [ ] F4: MCP 통합 가이드 & 설정 자동화 - Claude Code/Cursor 원클릭 연결
- [ ] F5: 사용자 온보딩 & 데모 시스템 - 랜딩 페이지 + 라이브 데모 + 퀵스타트

### 2.2 Out of Scope

- Cloud SaaS 인프라 구축 (P9 범위 - AWS/GCP 배포)
- 결제 시스템 (Stripe 통합 등 - P9 범위)
- 다국어 SDK (JavaScript/Go/Rust - P10 범위)
- 메타인지/자율학습 등 고급 인지 기능 (기술 로드맵 별도 관리)
- 마케팅 캠페인 집행 (기술 기반 준비만 수행)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|:--------:|:------:|
| **F1: 제품 README & 문서화** | | | |
| FR-01 | 제품 수준 README.md 작성 (프로젝트 소개, 빠른 시작, 기능 목록, 아키텍처 다이어그램) | Critical | Pending |
| FR-02 | Getting Started 가이드 (설치 → 첫 기억 저장 → 리콜 → 존 시각화까지 5분 내 완료) | Critical | Pending |
| FR-03 | API 레퍼런스 문서 (StellarMemory 클래스 전체 메서드, Config 옵션, 이벤트 목록) | High | Pending |
| FR-04 | 사용 시나리오별 가이드 (AI 챗봇, 개인 비서, 코드 어시스턴트, 지식 관리) | Medium | Pending |
| FR-05 | CHANGELOG.md 작성 (MVP ~ P7 전체 변경 이력) | Medium | Pending |
| **F2: 배포 파이프라인** | | | |
| FR-06 | PyPI 빌드 검증 (`python -m build` + 로컬 설치 테스트) | Critical | Pending |
| FR-07 | Docker Hub 이미지 빌드/태그 자동화 (stellar-memory:latest, :0.9.0) | High | Pending |
| FR-08 | GitHub Actions CI/CD (테스트 → 빌드 → PyPI 배포 → Docker 빌드) | High | Pending |
| FR-09 | 버전 관리 자동화 (git tag → 버전 동기화) | Medium | Pending |
| **F3: OpenAPI 문서** | | | |
| FR-10 | FastAPI 자동 생성 OpenAPI 스키마 + Swagger UI (/docs) | High | Pending |
| FR-11 | ReDoc 인터랙티브 문서 (/redoc) | Medium | Pending |
| FR-12 | API 요청/응답 예제 (cURL, Python, JavaScript) | High | Pending |
| FR-13 | Rate Limit 헤더 문서화 (X-RateLimit-Limit, Remaining, Reset) | Medium | Pending |
| **F4: MCP 통합 가이드** | | | |
| FR-14 | Claude Code MCP 설정 가이드 (claude_desktop_config.json 예제) | Critical | Pending |
| FR-15 | Cursor MCP 설정 가이드 | High | Pending |
| FR-16 | MCP 도구 카탈로그 (12개 도구 설명, 파라미터, 사용 예제) | High | Pending |
| FR-17 | `stellar-memory init-mcp` CLI 명령 - MCP 설정 파일 자동 생성 | Medium | Pending |
| **F5: 온보딩 & 데모** | | | |
| FR-18 | 인터랙티브 퀵스타트 CLI (`stellar-memory quickstart` - 대화형 설정 마법사) | High | Pending |
| FR-19 | 라이브 데모 페이지 (태양계 시각화 + 기억 저장/검색 체험) | Medium | Pending |
| FR-20 | 예제 프로젝트 3종 (챗봇, 개인 비서, 코드 어시스턴트) | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| 문서 품질 | README에서 설치 → 첫 사용까지 5분 이내 | 실제 시간 측정 |
| 패키지 크기 | 코어 패키지 < 500KB (의존성 제외) | `pip install --dry-run` |
| Docker 이미지 | 이미지 크기 < 200MB (slim 기반) | `docker images` |
| API 응답 | Swagger UI 로드 < 2초 | 브라우저 측정 |
| 호환성 | Python 3.10, 3.11, 3.12 전부 지원 | GitHub Actions 매트릭스 |
| 보안 | API 키 유출 방지 (.env 패턴, secrets 관리) | 코드 리뷰 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] README.md가 GitHub "awesome" 프로젝트 수준의 완성도
- [ ] `pip install stellar-memory` 후 10줄 이내 코드로 기억 저장/검색 가능
- [ ] `docker run stellar-memory` 로 REST API 즉시 사용 가능
- [ ] Claude Code에서 MCP 연결 가이드대로 3분 내 설정 가능
- [ ] `/docs` 엔드포인트에서 Swagger UI로 모든 API 시험 가능
- [ ] GitHub Actions로 push 시 자동 테스트 + 배포 파이프라인 동작
- [ ] 전체 테스트 530+ 통과 (기존 485 + 신규 45+)

### 4.2 Quality Criteria

- [ ] 테스트 커버리지 80% 이상 (신규 코드)
- [ ] 문서 내 모든 코드 예제가 실제 실행 가능
- [ ] Zero lint errors
- [ ] 빌드 성공 (PyPI + Docker)

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|:------:|:----------:|------------|
| PyPI 패키지 이름 충돌 | High | Low | `stellar-memory` 이름 사전 확인, 대안명 `stellar-mem` 준비 |
| 의존성 충돌 (사용자 환경) | High | Medium | 코어 zero-dependency 유지, 선택적 의존성만 extras로 분리 |
| Docker 이미지 보안 취약점 | Medium | Medium | python:3.11-slim 기반, 불필요 패키지 제거, non-root 유저 |
| MCP 프로토콜 변경 | Medium | Low | MCP SDK 버전 고정 + 호환성 레이어 |
| README 가독성 부족 | High | Medium | A/B 테스트 - 3명의 개발자에게 읽히기 테스트 |
| 대형 업체(OpenAI) 자체 메모리 강화 | High | High | 오픈소스 + 벤더 독립 포지셔닝, 독자 알고리즘(블랙홀 방지) 강조 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites | ☐ |
| **Dynamic** | Feature-based modules, BaaS | Web apps, SaaS | ☐ |
| **Enterprise** | Strict layer separation, DI | High-traffic systems | ☑ |

기존 Stellar Memory는 Enterprise 레벨 아키텍처(모듈별 분리, 플러그인 시스템, 분산 스토리지)를 유지합니다.

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 문서 호스팅 | ReadTheDocs / MkDocs / Docusaurus | MkDocs Material | Python 프로젝트 표준, 자동 API 레퍼런스 생성 |
| CI/CD | GitHub Actions / GitLab CI / CircleCI | GitHub Actions | 오픈소스 무료, PyPI/Docker 통합 우수 |
| API 문서 | Swagger / ReDoc / Postman | Swagger + ReDoc (내장) | FastAPI 기본 제공, 추가 구현 불필요 |
| 데모 배포 | Vercel / Fly.io / Railway | 코드만 준비 (배포는 P9) | P8은 기술 준비, 실제 호스팅은 P9 |
| 패키지 빌드 | setuptools / hatchling / flit | setuptools | 기존 pyproject.toml 호환, 안정성 |

### 6.3 파일 구조 변경 예상

```
stellar_memory/                    # 기존 유지
├── (기존 55개 파일 유지)
├── __version__.py                 # 버전 단일 소스 (신규)
└── _openapi.py                    # OpenAPI 스키마 보강 (신규)

docs/                              # 문서 대폭 확장
├── index.md                       # 문서 홈 (신규)
├── getting-started.md             # 빠른 시작 가이드 (신규)
├── api-reference.md               # API 레퍼런스 (신규)
├── guides/                        # 시나리오별 가이드 (신규)
│   ├── chatbot.md
│   ├── personal-assistant.md
│   ├── code-assistant.md
│   └── knowledge-management.md
├── mcp/                           # MCP 통합 가이드 (신규)
│   ├── claude-code.md
│   ├── cursor.md
│   └── tool-catalog.md
└── examples/                      # 예제 프로젝트 (신규)
    ├── basic/
    ├── chatbot/
    └── mcp-agent/

.github/                           # CI/CD (신규)
├── workflows/
│   ├── ci.yml                     # 테스트 + 린트
│   ├── release.yml                # PyPI + Docker 배포
│   └── docs.yml                   # 문서 빌드
└── ISSUE_TEMPLATE/                # 이슈 템플릿

README.md                          # 제품 수준 README (신규)
CHANGELOG.md                       # 전체 변경 이력 (신규)
CONTRIBUTING.md                    # 기여 가이드 (신규)
mkdocs.yml                         # MkDocs 설정 (신규)
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `CLAUDE.md` 존재 (기본 구조)
- [ ] `docs/01-plan/conventions.md` - 미존재
- [ ] `CONVENTIONS.md` - 미존재
- [x] pytest 설정 (pyproject.toml)
- [x] MIT 라이선스

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|:------------:|-----------|:--------:|
| **Naming** | 존재 (snake_case) | 문서화에 명시 | Medium |
| **Folder structure** | 존재 (모듈별) | CONTRIBUTING.md에 정리 | Medium |
| **Docstring** | 부분적 | Google 스타일 통일 | High |
| **Commit convention** | 없음 | Conventional Commits 도입 | High |
| **Version** | pyproject.toml 수동 | 단일 소스 버전 관리 | High |

### 7.3 Environment Variables

| Variable | Purpose | Scope | To Be Created |
|----------|---------|:-----:|:-------------:|
| `STELLAR_DB_PATH` | SQLite DB 경로 | Runtime | 존재 |
| `STELLAR_HOST` | API 서버 호스트 | Runtime | 존재 |
| `STELLAR_PORT` | API 서버 포트 | Runtime | 존재 |
| `STELLAR_API_KEY` | API 인증 키 | Runtime | 문서화 필요 |
| `STELLAR_LOG_LEVEL` | 로그 레벨 | Runtime | 추가 |
| `PYPI_API_TOKEN` | PyPI 배포 토큰 | CI/CD | ☑ |
| `DOCKER_USERNAME` | Docker Hub 사용자 | CI/CD | ☑ |
| `DOCKER_PASSWORD` | Docker Hub 토큰 | CI/CD | ☑ |

---

## 8. Feature Details

### F1: 제품 README & 문서화

**목표**: 개발자가 README를 보고 3분 안에 "이거 써봐야겠다"고 결심하게 만드는 문서.

**README.md 구조**:
```markdown
# Stellar Memory
> AI가 드디어 기억합니다. 천체 구조로 설계된 AI 메모리 시스템.

[태양계 시각화 GIF/이미지]

## Why Stellar Memory?
- 기존 AI: 대화 끝나면 모든 것을 잊음
- Stellar Memory: 중요한 건 Core에, 덜 중요한 건 멀리 - 사람처럼

## Quick Start (3분)
pip install stellar-memory → 5줄 코드 예제

## Features
- 천체 구조 5존 기억 계층
- 블랙홀 방지 알고리즘
- 감성 기억 (P7)
- MCP/REST API/LangChain/OpenAI 통합
- 분산 멀티 에이전트 동기화

## Architecture (태양계 다이어그램)
## Installation Options (pip, Docker, MCP)
## Documentation Links
## Contributing
## License
```

**문서 사이트 (MkDocs Material)**:
- Getting Started → API Reference → Guides → Examples 흐름
- 코드 하이라이팅 + 복사 버튼 + 검색

### F2: 배포 파이프라인

**GitHub Actions CI/CD**:
```yaml
# ci.yml: PR마다 실행
- Python 3.10/3.11/3.12 매트릭스 테스트
- 린트 검사 (ruff)
- 패키지 빌드 검증

# release.yml: 태그 푸시 시 실행
- PyPI 배포 (twine upload)
- Docker 빌드 + Docker Hub 푸시
- GitHub Release 생성 + CHANGELOG 첨부
```

**버전 관리**: `stellar_memory/__version__.py` → pyproject.toml dynamic 참조

### F3: OpenAPI 문서

**현재 상태**: `server.py`에 FastAPI 앱이 있지만, 스키마 설명/예제 부족.

**보강 항목**:
- 각 엔드포인트에 `summary`, `description`, `response_model`, `examples` 추가
- Pydantic 모델에 `Field(description=..., example=...)` 보강
- `/docs` (Swagger UI) + `/redoc` (ReDoc) 자동 활성화
- API 키 인증 스키마 (OpenAPI Security Scheme)

### F4: MCP 통합 가이드

**Claude Code 설정 (원클릭)**:
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "stellar-memory": {
      "command": "stellar-memory",
      "args": ["serve", "--mcp"],
      "env": { "STELLAR_DB_PATH": "~/.stellar/memory.db" }
    }
  }
}
```

**`stellar-memory init-mcp` 명령**: 위 설정 파일을 자동으로 올바른 위치에 생성.

### F5: 온보딩 & 데모

**`stellar-memory quickstart` 대화형 마법사**:
```
$ stellar-memory quickstart
Welcome to Stellar Memory!

? How will you use Stellar Memory?
  > AI Chatbot (LangChain / OpenAI)
  > Personal Knowledge Base (CLI)
  > MCP Server (Claude Code / Cursor)
  > REST API Server

? Where to store memories?
  > Local SQLite (default)
  > PostgreSQL
  > In-Memory (testing)

Setting up... Done!
Your first memory is stored: "Hello, Stellar Memory!"
Try: stellar-memory recall "hello"
```

**예제 프로젝트 3종**:
1. `examples/basic/` - 기본 저장/검색/존 이동 (10줄)
2. `examples/chatbot/` - LangChain 챗봇 + 기억 유지
3. `examples/mcp-agent/` - Claude Code MCP 연결 에이전트

---

## 9. Implementation Priority & Order

```
Week 1: F1 (README + 핵심 문서) + F6 (수익화 전략 업데이트)
Week 2: F2 (CI/CD 파이프라인) + F3 (OpenAPI 보강)
Week 3: F4 (MCP 가이드) + F5 (퀵스타트 CLI + 예제)
Week 4: 통합 테스트 + 최종 검증 + 배포 리허설
```

**의존 관계**:
```
F1 (README) ← 다른 모든 기능의 기반
  ↓
F3 (OpenAPI) ← F2 (CI/CD)에서 빌드 검증
  ↓
F4 (MCP 가이드) ← F1 문서 구조 활용
  ↓
F5 (온보딩) ← F1 + F3 + F4 완성 후
  ↓
F2 (CI/CD) ← 모든 코드 안정화 후 최종 파이프라인
```

---

## 10. Success Metrics (수익화 전략 연계)

| 지표 | P8 완료 시 목표 | 수익화 Phase 1 목표 (3개월) |
|------|:--------------:|:-------------------------:|
| README 완성도 | A급 (awesome-list 등재 가능) | GitHub Stars 1,000+ |
| PyPI 배포 | 빌드/배포 성공 | 월 다운로드 5,000+ |
| Docker 이미지 | Hub에 게시 | Pull 1,000+ |
| API 문서 | Swagger UI 완성 | API 호출 수 측정 가능 |
| MCP 가이드 | 3분 내 설정 가능 | Claude/Cursor 사용자 100+ |
| 예제 프로젝트 | 3종 동작 확인 | GitHub 포크 100+ |
| 총 테스트 | 530+ (100% 통과) | 품질 신뢰 유지 |

---

## 11. Next Steps

1. [ ] 이 Plan 문서 리뷰 및 승인
2. [ ] Design 문서 작성 (`/pdca design stellar-memory-p8`)
3. [ ] 구현 시작 (`/pdca do stellar-memory-p8`)
4. [ ] Gap 분석 → Report → Archive

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | 초안 - 수익화 전략 기반 P8 Plan | Stellar Memory Team |
