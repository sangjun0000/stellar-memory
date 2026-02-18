# stellar-memory-p6 Planning Document

> **Summary**: 분산 지능 & 실시간 협업 - 다중 에이전트 기억 공유 플랫폼
>
> **Project**: Stellar Memory
> **Version**: v0.7.0 (목표)
> **Author**: User
> **Date**: 2026-02-17
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

P1~P5를 통해 Stellar Memory는 단일 AI 에이전트를 위한 **완전한 지능형 기억 시스템**을 구축했습니다. P6에서는 이를 **다중 에이전트가 안전하게 공유하는 분산 기억 플랫폼**으로 확장합니다.

핵심 문제:
- 현재 단일 SQLite 파일 기반으로 다중 인스턴스 동시 접근 불가
- 여러 AI 에이전트가 같은 기억을 실시간으로 공유하지 못함
- 민감 기억의 암호화/접근 제어 부재
- 외부 지식(웹, 파일, API)의 자동 수집 경로 없음

### 1.2 Background

P5(v0.6.0) 완료 현황:
- 총 318개 테스트 (100% 통과)
- 33개 소스 파일, 31개 테스트 파일
- P1~P5 평균 설계 일치율 97.9%
- 5존 천체 구조, AI 요약, 차등 망각, 그래프 분석, 다중 프로바이더 완비

실제 운영 환경에서는 여러 AI 에이전트(Claude, GPT, 로컬 모델)가 **같은 프로젝트의 기억을 공유**해야 하는 상황이 발생합니다. 또한 API 키, 인증 정보 같은 **민감 기억의 보안**이 필수적이고, 웹 문서나 회의록 같은 **외부 지식을 자동으로 기억화**하는 기능이 필요합니다.

### 1.3 Related Documents

- 종합 보고서: `docs/stellar-memory-종합보고서.md` (Section 7: P6 제안)
- P5 아카이브: `docs/archive/2026-02/stellar-memory-p5/`
- 현재 아키텍처: `stellar_memory/` (33개 파일)

---

## 2. Scope

### 2.1 In Scope

- [ ] F1: 분산 스토리지 백엔드 (PostgreSQL + pgvector, Redis 캐시)
- [ ] F2: 실시간 기억 동기화 (CRDT + WebSocket 브로드캐스트)
- [ ] F3: 기억 보안 & 접근 제어 (AES-256-GCM 암호화, RBAC)
- [ ] F4: 외부 지식 커넥터 (Web/File/API 자동 수집)
- [ ] F5: 기억 시각화 대시보드 (FastAPI + SSE + 태양계 모델 뷰)

### 2.2 Out of Scope

- 클라우드 호스팅/배포 (AWS, GCP 등의 인프라 설정)
- 모바일 클라이언트
- 자연어 쿼리 인터페이스 (SQL 변환 등)
- 멀티 언어 기억 자동 번역

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| **F1: 분산 스토리지** | | | |
| FR-01 | `StorageBackend` ABC로 스토리지 추상화 | Critical | Pending |
| FR-02 | PostgreSQL 어댑터 (pgvector 벡터 검색 통합) | Critical | Pending |
| FR-03 | Redis 어댑터 (Core/Inner 존 캐시 레이어) | High | Pending |
| FR-04 | 기존 SQLite 어댑터를 `StorageBackend` 인터페이스로 리팩토링 | Critical | Pending |
| FR-05 | Connection Pool 관리 (pool_size 설정) | High | Pending |
| **F2: 실시간 동기화** | | | |
| FR-06 | `MemorySyncManager`: 기억 변경 감지 + CRDT 기반 전파 | High | Pending |
| FR-07 | WebSocket 서버: 실시간 이벤트 브로드캐스트 | High | Pending |
| FR-08 | WebSocket 클라이언트: 원격 기억 변경 수신 + 로컬 반영 | High | Pending |
| FR-09 | 충돌 해결: Last-Write-Wins 기본 + 수동 머지 옵션 | Medium | Pending |
| FR-10 | MCP 도구 `memory_sync_status`: 동기화 상태 확인 | Medium | Pending |
| **F3: 기억 보안** | | | |
| FR-11 | `SecurityManager`: AES-256-GCM 암호화/복호화 | High | Pending |
| FR-12 | 역할 기반 접근 제어 (RBAC): admin, writer, reader | High | Pending |
| FR-13 | 민감 기억 태깅 (`encrypted=True`) + 자동 암호화 | High | Pending |
| FR-14 | 감사 로그 강화: 접근자, 시간, 대상 기억 추적 | Medium | Pending |
| FR-15 | `SecurityConfig`: encryption, access_control, roles 설정 | High | Pending |
| **F4: 외부 지식 커넥터** | | | |
| FR-16 | `KnowledgeConnector` ABC + Web/File/API 구현체 | Medium | Pending |
| FR-17 | URL 수집: 웹 페이지 → 자동 요약(P5 Summarizer) → 기억 저장 | Medium | Pending |
| FR-18 | 파일 감시: 디렉토리 변경 감지 → 자동 기억화 | Medium | Pending |
| FR-19 | API 구독: 주기적 API 호출 → 응답 기억화 | Low | Pending |
| FR-20 | 소스 추적 메타데이터 (`source_url`, `ingested_at`) | Medium | Pending |
| FR-21 | 중복 검사: P2 Consolidator 연동 | Medium | Pending |
| **F5: 시각화 대시보드** | | | |
| FR-22 | FastAPI REST API 서버 (대시보드 백엔드) | Medium | Pending |
| FR-23 | 태양계 모델 시각화 (존별 기억 분포) | Medium | Pending |
| FR-24 | 그래프 네트워크 시각화 (P5 GraphML 활용) | Medium | Pending |
| FR-25 | 실시간 이벤트 스트림 (SSE: Server-Sent Events) | Low | Pending |
| FR-26 | 기억 검색/편집/삭제 UI | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | PostgreSQL 읽기 응답 < 50ms (단일 기억) | pytest-benchmark |
| Performance | Redis 캐시 히트 시 < 5ms | 캐시 히트율 모니터링 |
| Performance | WebSocket 전파 지연 < 100ms | 타임스탬프 비교 |
| Security | AES-256-GCM 암호화 라운드트립 100% | 단위 테스트 |
| Security | RBAC 우회 0건 | 권한 없는 접근 시도 테스트 |
| Scalability | 10,000 기억 동시 접근 시 락 대기 < 1초 | 부하 테스트 |
| Compatibility | 기존 318개 테스트 100% 통과 (하위 호환) | pytest 전체 실행 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] 모든 Functional Requirements (FR-01 ~ FR-26) 구현 완료
- [ ] 단위 테스트 작성 및 통과 (신규 80개 이상)
- [ ] 기존 318개 테스트 하위 호환 100% 유지
- [ ] 설계 문서 대비 일치율 90% 이상
- [ ] `__init__.py` 공개 API 노출 완료
- [ ] `pyproject.toml` 버전 v0.7.0 업데이트

### 4.2 Quality Criteria

- [ ] 총 테스트 수 400개 이상
- [ ] PostgreSQL 백엔드에서 전체 테스트 통과
- [ ] 2개 에이전트 동시 읽기/쓰기 충돌 없이 동작
- [ ] 민감 기억 AES-256 암호화 + 복호화 라운드트립 검증
- [ ] 외부 URL 수집 → 자동 요약 → 기억 저장 파이프라인 동작
- [ ] 대시보드에서 존별 분포 + 그래프 시각화 렌더링

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| PostgreSQL/Redis 외부 의존성 증가 | Medium | High | optional dependency 분리, SQLite 폴백 기본 유지 |
| CRDT 구현 복잡도 | High | Medium | 단순 LWW-Register로 시작, 점진적 확장 |
| WebSocket 연결 안정성 | Medium | Medium | 재연결 로직 + 오프라인 큐 |
| 암호화 키 관리 | High | Low | 환경변수 기반 + 키 로테이션 가이드 문서화 |
| 대시보드 프론트엔드 복잡도 | Medium | Medium | 최소 기능(stats + graph view)로 시작 |
| 하위 호환성 깨짐 | High | Low | StorageBackend ABC가 기존 인터페이스 완전 포함 |

---

## 6. Architecture Considerations

### 6.1 Project Level

**Stellar Memory는 Python 라이브러리**이므로 웹 프레임워크 레벨 분류(Starter/Dynamic/Enterprise)와는 다릅니다. 그러나 아키텍처 복잡도는 **Enterprise 수준**:

- 추상화 계층 분리 (Storage ABC, Provider Protocol, Connector ABC)
- 플러그인 시스템 (ProviderRegistry, StorageBackend)
- 실시간 통신 (WebSocket)
- 보안 레이어 (RBAC + 암호화)

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 분산 DB | PostgreSQL / MongoDB / CockroachDB | PostgreSQL | pgvector로 벡터 검색 통합, SQL 호환 |
| 캐시 | Redis / Memcached / 인메모리 | Redis | pub/sub 지원 → F2 동기화에도 활용 가능 |
| 동기화 | CRDT / OT / 단순 락 | CRDT (LWW) | 오프라인 내성, 분산 환경 적합 |
| WebSocket | websockets / aiohttp / Socket.IO | websockets | 순수 Python, asyncio 네이티브 |
| 암호화 | AES-256-GCM / ChaCha20 / Fernet | AES-256-GCM | 산업 표준, Python cryptography 라이브러리 |
| 대시보드 | FastAPI / Flask / Django | FastAPI | async 지원, 자동 OpenAPI 문서 |
| 시각화 | D3.js / Plotly / Chart.js | 서버사이드 HTML + 최소 JS | 외부 프론트엔드 의존성 최소화 |

### 6.3 파일 구조 예상

```
stellar_memory/                    # 기존 33개 + 신규 ~10개 = ~43개
├── (기존 파일들 유지)
│
├── storage/                       # P6-F1: 분산 스토리지
│   ├── __init__.py                # StorageBackend ABC + 팩토리 (리팩토링)
│   ├── in_memory.py               # (기존)
│   ├── sqlite_storage.py          # (기존, StorageBackend 구현)
│   ├── postgres_storage.py        # PostgreSQL + pgvector 어댑터
│   └── redis_cache.py             # Redis 캐시 레이어
│
├── sync/                          # P6-F2: 실시간 동기화
│   ├── __init__.py
│   ├── sync_manager.py            # MemorySyncManager (CRDT)
│   ├── ws_server.py               # WebSocket 서버
│   └── ws_client.py               # WebSocket 클라이언트
│
├── security/                      # P6-F3: 보안
│   ├── __init__.py
│   ├── encryption.py              # AES-256-GCM 암호화
│   ├── access_control.py          # RBAC 역할 관리
│   └── audit.py                   # 보안 감사 로그
│
├── connectors/                    # P6-F4: 외부 지식 커넥터
│   ├── __init__.py                # KnowledgeConnector ABC
│   ├── web_connector.py           # URL → 기억
│   ├── file_connector.py          # 파일/디렉토리 → 기억
│   └── api_connector.py           # API 응답 → 기억
│
└── dashboard/                     # P6-F5: 시각화 대시보드
    ├── __init__.py
    ├── app.py                     # FastAPI 앱
    ├── routes.py                  # REST API 엔드포인트
    └── templates/                 # HTML 템플릿
        ├── index.html             # 메인 대시보드
        └── graph.html             # 그래프 시각화
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

기존 P1~P5에서 확립된 컨벤션:

- [x] Python 3.9+ 호환, `from __future__ import annotations`
- [x] `@dataclass` 기반 Config/Model 클래스
- [x] ABC/Protocol 기반 인터페이스 (Storage, Provider, Connector)
- [x] `Null*` 패턴으로 optional 기능 안전 처리
- [x] `pytest` 기반 테스트, 파일명 `test_{module}.py`
- [x] optional dependency 분리 (`extras_require`)

### 7.2 P6에서 추가될 컨벤션

| Category | Rule | Priority |
|----------|------|:--------:|
| Async | 분산 스토리지/WebSocket은 `async/await` 사용 | High |
| Async | 동기 API 유지 (기존 호환) + `async_` 접두사 비동기 메서드 | High |
| Security | 암호화 키는 환경변수로만 전달 (`STELLAR_ENCRYPTION_KEY`) | High |
| Security | 민감 데이터 로깅 금지 (content 필드 마스킹) | High |
| Testing | 외부 서비스 테스트는 mock 사용 (PostgreSQL, Redis, WebSocket) | High |
| Testing | `@pytest.mark.integration` 마커로 통합 테스트 분리 | Medium |

### 7.3 Environment Variables

| Variable | Purpose | Scope | Required |
|----------|---------|-------|:--------:|
| `STELLAR_DB_URL` | PostgreSQL 연결 문자열 | Server | Optional |
| `STELLAR_REDIS_URL` | Redis 연결 문자열 | Server | Optional |
| `STELLAR_ENCRYPTION_KEY` | AES-256 암호화 키 (32바이트 base64) | Server | Optional |
| `STELLAR_WS_HOST` | WebSocket 서버 호스트 | Server | Optional |
| `STELLAR_WS_PORT` | WebSocket 서버 포트 | Server | Optional |
| `STELLAR_DASHBOARD_PORT` | 대시보드 HTTP 포트 | Server | Optional |

---

## 8. Implementation Order

```
Phase 1: F1 분산 스토리지 (기반 인프라)
  Step 1: StorageBackend ABC 정의 + 기존 SQLite/InMemory 리팩토링
  Step 2: PostgreSQL 어댑터 (pgvector 벡터 검색)
  Step 3: Redis 캐시 레이어
  Step 4: StorageConfig + StellarConfig 확장
  Step 5: StellarMemory에 StorageBackend 통합

Phase 2: F3 기억 보안 (분산 환경 전제)
  Step 6: SecurityManager (AES-256-GCM 암호화/복호화)
  Step 7: RBAC 접근 제어 (admin/writer/reader)
  Step 8: 민감 기억 태깅 + 자동 암호화
  Step 9: SecurityConfig + StellarConfig 확장
  Step 10: StellarMemory에 SecurityManager 통합

Phase 3: F2 실시간 동기화 (F1 위에 구축)
  Step 11: MemorySyncManager (CRDT LWW-Register)
  Step 12: WebSocket 서버 (asyncio + websockets)
  Step 13: WebSocket 클라이언트 + 재연결 로직
  Step 14: SyncConfig + StellarConfig 확장
  Step 15: MCP 도구 memory_sync_status

Phase 4: F4 외부 지식 커넥터 (독립)
  Step 16: KnowledgeConnector ABC
  Step 17: WebConnector (URL → 요약 → 기억)
  Step 18: FileConnector (디렉토리 감시 → 기억)
  Step 19: ApiConnector (주기적 API → 기억)
  Step 20: ConnectorConfig + StellarConfig 확장

Phase 5: F5 시각화 대시보드 (독립, 통합 뷰)
  Step 21: FastAPI 앱 + REST API 엔드포인트
  Step 22: 태양계 모델 HTML 뷰 (존별 분포)
  Step 23: 그래프 네트워크 HTML 뷰
  Step 24: 실시간 SSE 이벤트 스트림

Phase 6: 마무리
  Step 25: __init__.py P6 exports + version 0.7.0
  Step 26: pyproject.toml 업데이트 (optional deps)
  Step 27-31: 테스트 파일 5개 작성
  Step 32: 전체 회귀 테스트
```

---

## 9. Dependencies (신규 외부 패키지)

| Package | Purpose | Required/Optional |
|---------|---------|:-----------------:|
| `asyncpg` | PostgreSQL async 드라이버 | Optional (postgres) |
| `pgvector` | PostgreSQL 벡터 확장 Python 바인딩 | Optional (postgres) |
| `redis` | Redis Python 클라이언트 | Optional (redis) |
| `websockets` | WebSocket 서버/클라이언트 | Optional (sync) |
| `cryptography` | AES-256-GCM 암호화 | Optional (security) |
| `fastapi` | 대시보드 웹 서버 | Optional (dashboard) |
| `uvicorn` | ASGI 서버 | Optional (dashboard) |
| `httpx` | 외부 URL/API 수집 | Optional (connectors) |
| `watchdog` | 파일 시스템 변경 감지 | Optional (connectors) |

---

## 10. Next Steps

1. [ ] Plan 검토 및 승인
2. [ ] Design 문서 작성 (`/pdca design stellar-memory-p6`)
3. [ ] 구현 시작 (`/pdca do stellar-memory-p6`)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | Initial draft | User |
