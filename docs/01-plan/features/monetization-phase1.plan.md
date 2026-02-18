# Plan: Monetization Phase 1

> **Feature**: monetization-phase1
> **Created**: 2026-02-18
> **Status**: Draft
> **Priority**: High

---

## 1. Overview

Stellar Memory의 수익화 Phase 1: 랜딩페이지 Pricing 섹션 추가 및 MCP 마켓플레이스 등록.
현재 "무료 오픈소스 프로젝트" 상태에서 "수익화 준비 상태"로 전환하는 첫 단계.

## 2. Goals

- [ ] 랜딩페이지에 Pricing 섹션 추가 (Free / Pro / Team / Enterprise 4단계)
- [ ] MCP 마켓플레이스에 Stellar Memory 등록 (Claude Code + Cursor)

## 3. Background

### 수익화 전략 (docs/stellar-memory-수익화전략.md 참조)
- 추천 모델: 오픈 코어 + SaaS
- Phase 1 목표: 인지도 확보 + 가격 정책 공개
- 가격 체계: Free ($0) / Pro ($29) / Team ($99) / Enterprise ($499+)

### 현재 상태
- 기술 구현: 100% (코어 엔진, API, MCP, Docker)
- 배포/인프라: 80% (PyPI, GitHub, 도메인, SSL, SEO)
- 수익화 기능: 10% (가격 페이지 없음, 결제 없음)

## 4. Feature Details

### F1: Landing Page Pricing Section

**목표**: stellar-memory.com 랜딩페이지에 가격 정책 섹션 추가

**수정 파일**: `landing/index.html`

**Pricing 테이블 구성**:

| Plan | Price | Memories | Agents | Features |
|------|-------|----------|--------|----------|
| Free | $0/mo | 5,000 | 1 | SQLite, Basic CLI, Local MCP |
| Pro | $29/mo | 50,000 | 5 | PostgreSQL, Web Dashboard, Cloud MCP |
| Team | $99/mo | 500,000 | 20 | + Team Sync, RBAC, Audit Logs |
| Enterprise | Custom | Unlimited | Unlimited | + SLA, Dedicated Support, On-premise |

**UI 요구사항**:
- 기존 랜딩페이지 디자인과 일관된 다크 테마
- 4컬럼 카드 레이아웃 (모바일에서는 1컬럼)
- Pro 플랜에 "Most Popular" 배지
- Enterprise는 "Contact Us" CTA
- Free/Pro는 "Get Started" CTA (현재는 PyPI/GitHub 링크)
- 별 + 궤도 테마 유지 (우주 느낌)

**위치**: "Five Orbital Zones" 섹션과 Footer 사이

### F2: MCP Marketplace Registration

**목표**: Claude Code 및 Cursor MCP 마켓플레이스에 Stellar Memory 등록

**F2-1: Claude Code MCP 등록**
- mcp.json 또는 smithery.yaml 설정 파일 작성
- Claude MCP 레지스트리 등록 (smithery.ai 또는 mcp.run)
- 설치 가이드: `stellar-memory init-mcp --ide claude`

**F2-2: Cursor MCP 등록**
- Cursor MCP 설정 파일 작성
- 설치 가이드: `stellar-memory init-mcp --ide cursor`

**MCP 도구 목록** (이미 구현됨):
- `stellar_store` - 기억 저장
- `stellar_recall` - 기억 검색
- `stellar_stats` - 통계 조회
- `stellar_timeline` - 타임라인
- `stellar_introspect` - 내성 분석
- `stellar_reason` - 추론

## 5. Technical Requirements

### F1 기술 요구사항
- HTML/CSS only (JS 최소화)
- 반응형 디자인 (모바일 대응)
- 기존 CSS 변수 활용 (--accent-amber, --accent-blue 등)
- Schema.org PriceSpecification 마크업 추가 (SEO)

### F2 기술 요구사항
- smithery.yaml (Smithery MCP 레지스트리)
- .cursor/mcp.json (Cursor 설정)
- CLI `init-mcp` 명령어 이미 구현됨 → 가이드 문서만 추가

## 6. Implementation Order

1. **F1**: Pricing 섹션 HTML/CSS 작성 → landing/index.html에 추가
2. **F1**: gh-pages에 배포 및 확인
3. **F2-1**: Smithery MCP 레지스트리 설정 파일 작성
4. **F2-2**: Cursor MCP 설정 가이드 작성
5. **F2**: MCP 등록 절차 진행

## 7. Out of Scope (Phase 2+)

- Stripe 결제 연동
- Cloud SaaS 인프라 구축
- API 키 발급 / 인증 시스템
- 사용량 추적 / 과금 시스템
- Free 티어 기억 제한 (5,000개) 코드 구현

## 8. Success Criteria

- [ ] stellar-memory.com에 Pricing 섹션이 표시됨
- [ ] 4개 플랜 (Free/Pro/Team/Enterprise)이 명확히 구분됨
- [ ] 모바일에서도 Pricing이 정상 표시됨
- [ ] MCP 레지스트리에 stellar-memory가 검색 가능
- [ ] `stellar-memory init-mcp` 가이드가 문서에 포함됨

## 9. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Pricing이 너무 높으면 개발자 이탈 | Medium | Free 티어로 충분한 무료 사용 보장 |
| MCP 마켓플레이스 심사 지연 | Low | 자체 문서로 설치 가이드 제공 |
| Cloud 서비스 없이 Pro 가격 공개 | Medium | "Coming Soon" 배지 + Waitlist 폼 |
