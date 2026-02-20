# Plan: Monetization Phase 2

> **Feature**: monetization-phase2
> **Created**: 2026-02-18
> **Status**: Draft
> **Depends On**: monetization-phase1 (archived, 94%)

---

## 1. Background

### 1.1 Phase 1 완료 현황
- Landing page Pricing section (Free/Pro/Team/Enterprise) 배포 완료
- MCP marketplace 파일 생성 (smithery.yaml, .cursor/mcp.json)
- Pro/Team CTA: "Coming Soon" 상태 → Phase 2에서 실제 결제로 전환 필요

### 1.2 기존 기술 스택 (이미 구현됨)
- **REST API 서버**: FastAPI (stellar_memory/server.py)
- **API Key 인증**: 환경변수 기반 단일 키 (STELLAR_API_KEY)
- **Rate Limiting**: IP당 60 req/min
- **PostgreSQL + pgvector**: 분산 스토리지 지원
- **Docker**: Dockerfile + docker-compose.yml
- **CRDT 동기화**: LWW + Vector Clock
- **RBAC + Audit**: 역할 기반 접근 제어

### 1.3 Phase 2 목표
수익화 전략 문서의 "Phase 2: 첫 수익" 달성:
- **목표 MRR**: $5,000
- **목표 유료 사용자**: 200명 Pro

---

## 2. Feature Scope

### F1: 결제 연동 (Lemon Squeezy + Stripe + 토스페이먼츠)
**목적**: Pro/Team 구독 결제 처리 (3개 결제 제공자)

| Provider | 대상 | 특징 |
|----------|------|------|
| Lemon Squeezy | 글로벌 (기본) | MoR(Merchant of Record) - VAT/세금 자동 처리, 가장 간단 |
| Stripe | 글로벌 (대안) | 직접 결제 처리, 더 많은 커스터마이징 |
| 토스페이먼츠 | 국내 사용자 | 카드/계좌이체/가상계좌, 한국 결제 최적화 |

| 항목 | 상세 |
|------|------|
| 구독 플랜 | Pro ($29/₩39,000), Team ($99/₩129,000) |
| Webhook 처리 | LS: subscription_created 등 / Stripe: checkout.session.completed / Toss: PAYMENT_STATUS_CHANGED |
| 구독 관리 | LS Customer Portal + Stripe Portal + Toss 관리 API |
| 결제 페이지 | Landing page "Coming Soon" → Provider 선택 결제 |

### F2: 사용자 계정 & API Key 시스템
**목적**: 사용자별 API Key 발급 및 tier 기반 접근 제어

| 항목 | 상세 |
|------|------|
| 사용자 등록 | 이메일 + 결제 Provider (Stripe/Toss) Customer ID 연동 |
| API Key 생성 | 사용자별 고유 API Key 발급 (sk-stellar-xxxxx) |
| Tier 연동 | API Key에 Free/Pro/Team tier 매핑 |
| Key 관리 | 생성, 조회, 폐기, 재발급 API |

### F3: Tier 기반 제한 (Usage Enforcement)
**목적**: 플랜별 기억 수, 에이전트 수, Rate Limit 적용

| Tier | 기억 수 | 에이전트 | Rate Limit |
|------|:-------:|:--------:|:----------:|
| Free | 5,000 | 1 | 60/min |
| Pro | 50,000 | 5 | 300/min |
| Team | 500,000 | 20 | 1,000/min |

### F4: Cloud 배포
**목적**: 클라우드에서 실제 서비스 운영

| 항목 | 상세 |
|------|------|
| 배포 플랫폼 | Fly.io (Docker 기반, 글로벌 엣지, 저렴) |
| 데이터베이스 | Neon PostgreSQL (서버리스, pgvector 지원, 무료 티어) |
| 도메인 | api.stellar-memory.com |
| SSL | Fly.io 자동 인증서 |
| 모니터링 | Health check + 기본 로깅 |

---

## 3. Out of Scope (Phase 3+)

| 항목 | 이유 |
|------|------|
| Web Dashboard UI | Phase 3에서 별도 프론트엔드 프로젝트 |
| Team CRDT 실시간 동기화 | Cloud infra 안정화 후 |
| Enterprise 온프레미스 | 엔터프라이즈 고객 확보 후 |
| 사용량 기반 과금 (API 호출당) | Phase 3 API as a Service |
| 소셜 로그인 (GitHub/Google) | Phase 3 UX 개선 |
| 다국어 SDK (JS/Go/Rust) | Phase 4 생태계 확장 |

---

## 4. Technical Architecture

```
사용자 브라우저
  │
  ├── stellar-memory.com (gh-pages)
  │     └── Pricing "Subscribe" → Stripe Checkout
  │
  ├── Stripe
  │     ├── Checkout Session
  │     ├── Customer Portal
  │     └── Webhook → api.stellar-memory.com/webhook/stripe
  │
  └── api.stellar-memory.com (Fly.io)
        ├── POST /auth/register (이메일 등록)
        ├── POST /auth/api-keys (Key 생성)
        ├── GET  /auth/api-keys (Key 목록)
        ├── DELETE /auth/api-keys/{id} (Key 폐기)
        ├── GET  /auth/usage (사용량 조회)
        │
        ├── POST /api/v1/store (기존 API + tier 제한)
        ├── POST /api/v1/recall
        ├── GET  /api/v1/stats
        │     ... (기존 API 엔드포인트들)
        │
        └── Neon PostgreSQL (pgvector)
              ├── users 테이블
              ├── api_keys 테이블
              ├── usage_logs 테이블
              └── memories 테이블 (기존)
```

---

## 5. Implementation Order

### Phase 2-A: 백엔드 (2-3일)
1. F2-1: DB 스키마 (users, api_keys, usage_logs 테이블)
2. F2-2: 사용자 등록 API (/auth/register)
3. F2-3: API Key CRUD API (/auth/api-keys)
4. F3-1: Tier 기반 Rate Limiting 리팩토링
5. F3-2: 기억 수 제한 enforcement

### Phase 2-B: Stripe 연동 (2-3일)
6. F1-1: Stripe 초기 설정 (Product/Price 생성)
7. F1-2: Checkout Session API (/billing/checkout)
8. F1-3: Webhook 처리 (/webhook/stripe)
9. F1-4: Customer Portal 연동 (/billing/portal)

### Phase 2-C: Cloud 배포 (1-2일)
10. F4-1: Fly.io 설정 (fly.toml)
11. F4-2: Neon PostgreSQL 연결
12. F4-3: 환경변수 설정 (Secrets)
13. F4-4: api.stellar-memory.com 도메인 연결

### Phase 2-D: Landing Page 연동 (0.5일)
14. F1-5: "Coming Soon" → Stripe Checkout 링크 전환
15. F1-6: 가격 페이지 FAQ 추가 (optional)

---

## 6. Success Criteria

| 기준 | 목표 |
|------|------|
| Stripe Checkout 작동 | Pro/Team 구독 결제 성공 |
| API Key 발급 | 등록 → Key 발급 → API 호출 성공 |
| Tier 제한 동작 | Free: 5K 기억, Pro: 50K 기억 제한 확인 |
| Cloud 서비스 가동 | api.stellar-memory.com 200 OK |
| 응답 시간 | < 200ms (p95) |
| Landing Page 전환 | "Coming Soon" → "Subscribe" 동작 |

---

## 7. Risks

| 리스크 | 확률 | 영향 | 완화 |
|--------|:----:|:----:|------|
| Stripe 설정 복잡도 | 중간 | 중간 | Stripe Checkout (hosted) 사용으로 복잡도 최소화 |
| Fly.io 냉시작 지연 | 낮음 | 낮음 | min_machines_running=1 설정 |
| DB 마이그레이션 | 낮음 | 중간 | Alembic 또는 수동 SQL migration |
| Webhook 보안 | 중간 | 높음 | Stripe signature 검증 필수 |
| 비용 초과 | 낮음 | 중간 | Fly.io free tier + Neon free tier 활용 |

---

## 8. Dependencies

| 의존성 | 버전 | 용도 |
|--------|------|------|
| stripe (Python) | ^7.0 | Stripe API 연동 |
| python-jose | ^3.3 | JWT 토큰 (optional) |
| passlib | ^1.7 | 비밀번호 해싱 |
| alembic | ^1.13 | DB 마이그레이션 (optional) |
| asyncpg | ^0.29 | PostgreSQL 비동기 드라이버 |

---

## 9. File Change Summary (예상)

| File | Action | Description |
|------|--------|-------------|
| stellar_memory/server.py | MODIFY | 인증/빌링 라우터 추가, tier 기반 제한 |
| stellar_memory/auth.py | CREATE | 사용자 등록, API Key 관리 |
| stellar_memory/billing.py | CREATE | Stripe Checkout, Webhook, Portal |
| stellar_memory/models.py | CREATE | DB 스키마 (users, api_keys, usage) |
| stellar_memory/config.py | MODIFY | Stripe/Cloud 설정 추가 |
| fly.toml | CREATE | Fly.io 배포 설정 |
| landing/index.html | MODIFY | "Coming Soon" → Stripe Checkout |
| pyproject.toml | MODIFY | stripe 의존성 추가 |
| docker-compose.yml | MODIFY | 환경변수 추가 |

---

## 10. Estimated Effort

| Phase | 예상 시간 |
|-------|----------|
| 2-A: 백엔드 | 2-3일 |
| 2-B: Stripe | 2-3일 |
| 2-C: Cloud | 1-2일 |
| 2-D: Landing | 0.5일 |
| **합계** | **~7일** |
