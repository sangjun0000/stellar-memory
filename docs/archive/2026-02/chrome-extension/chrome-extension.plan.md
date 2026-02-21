# Stellar Memory Chrome Extension — Planning Document

> **Summary**: ChatGPT, Claude, Gemini에서 "설치만 하면 AI가 나를 기억하는" 크롬 확장 프로그램
>
> **Project**: stellar-memory
> **Version**: v3.0.0 → v3.1.0
> **Author**: Claude (AI)
> **Date**: 2026-02-21
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

**"설치 한 번이면, 모든 AI가 나를 기억한다"**

일반 사용자가 크롬 확장 프로그램을 설치하면, ChatGPT/Claude/Gemini에서 하는 대화를 자동으로 기억하고, 다음 대화에서 관련 기억을 AI에게 자동으로 전달하는 소비자용 제품.

### 1.2 Background

현재 Stellar Memory는 **개발자용 SDK**로 완성되어 있음 (v3.0.0, 673 테스트). 그러나 일반 사용자가 접근할 수 있는 제품은 없음.

크롬 확장이 필요한 이유:
- ChatGPT 주간 활성 사용자 수억 명 — 가장 큰 시장
- "AI가 나를 기억하지 못한다"는 가장 흔한 불만
- 설치 한 번으로 해결 — 코드 작성 불필요
- 기존 SDK를 백엔드로 그대로 활용 가능

### 1.3 핵심 사용자 경험

```
[설치 전]
사용자: "나 커피 좋아해"
ChatGPT: "네, 좋은 취향이시네요!"
(다음 날)
사용자: "내가 좋아하는 거 뭐야?"
ChatGPT: "죄송합니다, 이전 대화를 기억하지 못합니다."

[설치 후]
사용자: "나 커피 좋아해"
ChatGPT: "네, 좋은 취향이시네요!"
  ← Stellar Memory가 자동 저장: "사용자는 커피를 좋아함" (importance: 0.8)
(다음 날)
사용자: "내가 좋아하는 거 뭐야?"
  ← Stellar Memory가 자동 주입: "[기억: 사용자는 커피를 좋아함]"
ChatGPT: "커피를 좋아하신다고 하셨죠!"
```

### 1.4 Related Documents

- SDK v3.0 Report: `docs/archive/2026-02/platform-sdk/platform-sdk.report.md`
- REST API: `stellar_memory/server.py` (15개 엔드포인트)
- MCP Server: `stellar_memory/mcp_server.py` (17개 도구)

---

## 2. Scope

### 2.1 In Scope

- [ ] Chrome Extension (Manifest V3)
- [ ] ChatGPT (chat.openai.com) 대화 자동 캡처 및 기억 주입
- [ ] Claude (claude.ai) 대화 자동 캡처 및 기억 주입
- [ ] Gemini (gemini.google.com) 대화 자동 캡처 및 기억 주입
- [ ] 로컬 Stellar Memory 백엔드 서버 (자동 시작)
- [ ] 팝업 UI (기억 목록, 설정, on/off)
- [ ] 사이드 패널 UI (현재 대화 관련 기억 표시)

### 2.2 Out of Scope

- 모바일 앱 (향후 별도 프로젝트)
- Firefox/Safari 확장 (향후 포트)
- 유료 결제/구독 (1차에서는 무료)
- 클라우드 서버 배포 (1차에서는 로컬 only)
- AI 자체 개발 (기존 SDK 활용)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|:--------:|--------|
| FR-01 | **대화 자동 캡처**: ChatGPT/Claude/Gemini의 사용자+AI 대화를 실시간 감지하여 저장 | High | Pending |
| FR-02 | **기억 자동 주입**: 사용자가 메시지 입력 시, 관련 기억을 프롬프트에 자동 추가 | High | Pending |
| FR-03 | **팝업 UI**: 확장 아이콘 클릭 시 기억 목록, 검색, on/off 토글 | High | Pending |
| FR-04 | **사이드 패널**: 현재 대화에 관련된 기억을 실시간 표시 | Medium | Pending |
| FR-05 | **로컬 백엔드**: Stellar Memory REST API 서버를 로컬에서 자동 실행 | High | Pending |
| FR-06 | **사이트별 on/off**: ChatGPT/Claude/Gemini 개별적으로 활성화/비활성화 | Medium | Pending |
| FR-07 | **기억 수동 저장**: 텍스트 선택 후 우클릭 → "기억하기" 컨텍스트 메뉴 | Medium | Pending |
| FR-08 | **기억 삭제**: 팝업/사이드 패널에서 개별 기억 삭제 | Medium | Pending |
| FR-09 | **대화 분리**: 각 AI 플랫폼별로 기억을 분리하거나 통합 선택 가능 | Low | Pending |
| FR-10 | **설치 온보딩**: 최초 설치 시 사용법 안내 페이지 표시 | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement |
|----------|----------|-------------|
| Performance | 기억 주입 시 입력 지연 < 200ms | 콘솔 타임스탬프 |
| Privacy | 모든 데이터 로컬 저장 (외부 전송 없음) | 네트워크 탭 검증 |
| Compatibility | Chrome 120+ (Manifest V3) | 크롬 버전 테스트 |
| UX | 설치 후 설정 없이 즉시 동작 | 사용자 테스트 |
| Stability | AI 사이트 UI 변경 시에도 핵심 기능 유지 | DOM selector 격리 |

---

## 4. Architecture

### 4.1 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                   Chrome Extension                   │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Popup UI │  │Side Panel│  │  Content Scripts   │  │
│  │ (React)  │  │ (React)  │  │ (per AI site)     │  │
│  └────┬─────┘  └────┬─────┘  │                   │  │
│       │              │        │ chatgpt.js        │  │
│       │              │        │ claude.js         │  │
│       │              │        │ gemini.js         │  │
│       │              │        └─────┬─────────────┘  │
│       └──────┬───────┘              │                │
│              │                      │                │
│         ┌────▼──────────────────────▼────┐           │
│         │     Background Service Worker   │           │
│         │     (stellar-bridge.js)         │           │
│         │                                 │           │
│         │  - Message routing              │           │
│         │  - API call queue               │           │
│         │  - Rate limit handling          │           │
│         └────────────┬────────────────────┘           │
│                      │                                │
└──────────────────────┼────────────────────────────────┘
                       │ HTTP (localhost:9000)
                       │
         ┌─────────────▼─────────────┐
         │  Stellar Memory REST API   │
         │  (Python, 로컬 실행)        │
         │                            │
         │  POST /api/v1/store        │
         │  GET  /api/v1/recall       │
         │  GET  /api/v1/stats        │
         │  DELETE /api/v1/forget     │
         └────────────────────────────┘
```

### 4.2 Content Script 동작 방식

각 AI 사이트별로 전용 Content Script가 동작:

```
[대화 캡처 흐름]
1. Content Script가 DOM 변화 감지 (MutationObserver)
2. 새 메시지(사용자/AI) 감지 시 텍스트 추출
3. Background Worker로 전달
4. Background Worker가 REST API /store 호출
5. 메타데이터 포함: {source: "chatgpt", url, timestamp, conversation_id}

[기억 주입 흐름]
1. 사용자가 입력창에 텍스트 작성
2. Content Script가 입력 이벤트 감지
3. Background Worker로 입력 텍스트 전달
4. REST API /recall 호출 → 관련 기억 수신
5. 두 가지 주입 방식 중 선택:
   a) 프롬프트 앞에 기억 컨텍스트 삽입 (자동)
   b) 사이드 패널에 기억 표시 (사용자가 수동 복사)
```

### 4.3 기억 주입 형식

```
[Stellar Memory — 이 사용자에 대한 기억]
- 사용자는 커피를 좋아함 (2일 전)
- 프론트엔드 개발자, React 사용 (5일 전)
- 한국어를 선호함 (1주 전)
[기억 끝]

사용자의 원래 메시지가 여기에 이어짐...
```

### 4.4 프로젝트 레벨

| Level | Characteristics | Selected |
|-------|-----------------|:--------:|
| **Starter** | Simple HTML/CSS/JS | |
| **Dynamic** | Feature-based, BaaS | **YES** |
| **Enterprise** | Microservices | |

Dynamic 레벨 선정 이유: 프론트엔드(Chrome Extension) + 백엔드(Stellar Memory API) 구조

### 4.5 기술 스택

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Extension Framework | Chrome Manifest V3 | 최신 표준, 보안 강화 |
| UI Framework | React + Vite | 빠른 빌드, 컴포넌트 기반 |
| UI Styling | Tailwind CSS | 확장 팝업/사이드 패널 경량 스타일 |
| 빌드 도구 | Vite + CRXJS | Chrome Extension 전용 Vite 플러그인 |
| 백엔드 | Stellar Memory REST API (Python) | 이미 완성됨 |
| 로컬 저장 | chrome.storage.local | 설정, API 키 저장 |
| 기억 저장 | SQLite (via Stellar Memory) | 기존 SDK 그대로 활용 |
| 테스트 | Vitest + Playwright | 유닛 + E2E |

---

## 5. Feature 상세

### F1: Content Scripts (대화 캡처 + 기억 주입)

각 AI 사이트별 DOM 구조에 맞는 Content Script:

| Site | 입력창 Selector | 메시지 Selector | 전송 버튼 |
|------|----------------|-----------------|-----------|
| ChatGPT | `#prompt-textarea` | `[data-message-author-role]` | form submit 이벤트 |
| Claude | `div[contenteditable]` | `[data-testid="chat-message"]` | form submit 이벤트 |
| Gemini | `rich-textarea` | `.message-content` | form submit 이벤트 |

**핵심 설계 원칙**: DOM selector가 변경되어도 핵심 로직은 유지되도록, selector를 config로 분리하여 빠르게 업데이트 가능하게 함.

### F2: Background Service Worker

```javascript
// 메시지 라우팅
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  switch (msg.type) {
    case 'STORE_MEMORY':    // 대화 내용 저장
    case 'RECALL_MEMORIES': // 관련 기억 검색
    case 'FORGET_MEMORY':   // 기억 삭제
    case 'GET_STATS':       // 통계 조회
    case 'TOGGLE_SITE':     // 사이트별 on/off
  }
});
```

### F3: Popup UI

```
┌─────────────────────────────┐
│  Stellar Memory        ⚙️   │
│─────────────────────────────│
│  🔍 기억 검색...            │
│─────────────────────────────│
│  📊 총 127개 기억            │
│  Core: 5 | Inner: 23        │
│  Outer: 67 | Belt: 32       │
│─────────────────────────────│
│  최근 기억:                  │
│  ☀️ 커피를 좋아함     [🗑️]  │
│  🪐 React 개발자      [🗑️]  │
│  🪐 한국어 선호       [🗑️]  │
│─────────────────────────────│
│  ChatGPT  [ON]  ●           │
│  Claude   [ON]  ●           │
│  Gemini   [OFF] ○           │
└─────────────────────────────┘
```

### F4: Side Panel

현재 대화에 관련된 기억을 실시간으로 보여주는 사이드 패널:

```
┌──────────────────────────┐
│  이 대화와 관련된 기억     │
│──────────────────────────│
│  📌 Core                  │
│  "커피를 좋아함"          │
│  2일 전 · ChatGPT        │
│                          │
│  📎 Inner                 │
│  "React 개발자"          │
│  5일 전 · Claude          │
│──────────────────────────│
│  💡 기억이 자동 주입됩니다  │
│  ○ 자동 주입  ● 수동 확인  │
└──────────────────────────┘
```

### F5: 로컬 백엔드 연동

Chrome Extension은 직접 Python을 실행할 수 없으므로, 사용자가 백엔드를 별도로 실행해야 함:

**방법 A: 사용자가 수동 실행** (1차 MVP)
```bash
pip install stellar-memory[server]
stellar-memory serve-api
```

**방법 B: Native Messaging Host** (2차)
- Chrome Native Messaging으로 Python 프로세스 자동 시작
- 설치 스크립트가 native host manifest 등록

**방법 C: WASM/IndexedDB** (3차, 장기)
- Python → WASM 변환 (Pyodide)
- 서버 없이 브라우저 내에서 직접 실행

**1차 MVP는 방법 A**로 진행. 설치 가이드로 안내.

---

## 6. Success Criteria

### 6.1 Definition of Done

- [ ] Chrome Web Store에 등록 가능한 상태
- [ ] ChatGPT에서 대화 캡처 및 기억 주입 동작
- [ ] Claude에서 대화 캡처 및 기억 주입 동작
- [ ] Gemini에서 대화 캡처 및 기억 주입 동작
- [ ] 팝업 UI에서 기억 목록 확인 및 삭제 가능
- [ ] 사이드 패널에서 관련 기억 실시간 표시
- [ ] 로컬 REST API 서버와 안정적 통신

### 6.2 Quality Criteria

- [ ] 입력 지연 < 200ms
- [ ] 메모리 사용 < 50MB
- [ ] 모든 데이터 로컬 저장 (외부 전송 없음)
- [ ] 각 사이트별 E2E 테스트 통과
- [ ] Manifest V3 규격 준수

---

## 7. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|:------:|:----------:|------------|
| AI 사이트 DOM 구조 변경 | High | High | Selector config 분리, 자동 감지 폴백, 빠른 업데이트 파이프라인 |
| 사용자가 백엔드 서버 실행을 어려워함 | High | High | 1차: 상세 가이드, 2차: Native Messaging 자동 실행 |
| 기억 주입 시 AI가 기억 컨텍스트를 무시 | Medium | Medium | 프롬프트 형식 최적화, A/B 테스트 |
| Chrome Web Store 심사 거부 | Medium | Low | Manifest V3 준수, 권한 최소화, 개인정보 정책 명시 |
| 기억 주입으로 토큰 낭비 | Medium | Medium | 기억 수 제한 (최대 5개), 중요도 기반 필터링 |
| 대화 캡처 정확도 | Medium | Medium | AI 응답 완료 대기 후 캡처, debounce 적용 |

---

## 8. 파일 구조 (예상)

```
stellar-chrome/                     # 새 디렉토리 (모노레포 또는 별도 repo)
├── manifest.json                   # Chrome Extension Manifest V3
├── package.json                    # Node.js 의존성
├── vite.config.ts                  # Vite + CRXJS 빌드 설정
├── tailwind.config.js              # Tailwind CSS
│
├── src/
│   ├── background/
│   │   └── service-worker.ts       # Background Service Worker
│   │
│   ├── content/
│   │   ├── common.ts               # 공통 DOM 유틸리티
│   │   ├── chatgpt.ts              # ChatGPT Content Script
│   │   ├── claude.ts               # Claude Content Script
│   │   ├── gemini.ts               # Gemini Content Script
│   │   └── selectors.json          # DOM Selector 설정 (빠른 업데이트용)
│   │
│   ├── popup/
│   │   ├── Popup.tsx               # 팝업 메인 컴포넌트
│   │   ├── MemoryList.tsx          # 기억 목록
│   │   ├── SearchBar.tsx           # 검색
│   │   └── SiteToggle.tsx          # 사이트별 on/off
│   │
│   ├── sidepanel/
│   │   ├── SidePanel.tsx           # 사이드 패널 메인
│   │   └── RelatedMemories.tsx     # 관련 기억 표시
│   │
│   ├── lib/
│   │   ├── api-client.ts           # Stellar Memory REST API 클라이언트
│   │   ├── memory-injector.ts      # 기억 주입 로직
│   │   └── conversation-parser.ts  # 대화 파싱 공통 로직
│   │
│   └── types/
│       └── index.ts                # TypeScript 타입 정의
│
├── public/
│   ├── icons/                      # 확장 아이콘 (16, 32, 48, 128px)
│   └── onboarding.html             # 최초 설치 시 안내 페이지
│
└── tests/
    ├── unit/                       # Vitest 유닛 테스트
    └── e2e/                        # Playwright E2E 테스트
```

---

## 9. 구현 순서

| Phase | 내용 | 예상 산출물 |
|:-----:|------|-----------|
| **1** | 프로젝트 셋업 + Background Worker + API Client | 기본 골격 |
| **2** | ChatGPT Content Script (캡처 + 주입) | ChatGPT 동작 |
| **3** | Popup UI (기억 목록 + 검색 + 토글) | 기본 UI |
| **4** | Claude + Gemini Content Scripts | 3개 사이트 지원 |
| **5** | Side Panel + 온보딩 페이지 | 완성 UX |
| **6** | 테스트 + Chrome Web Store 등록 준비 | 배포 가능 |

---

## 10. Next Steps

1. [ ] Design 문서 작성 (`/pdca design chrome-extension`)
2. [ ] 프로젝트 셋업 (stellar-chrome/ 디렉토리)
3. [ ] ChatGPT Content Script 프로토타입
4. [ ] 구현 시작

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-21 | Initial draft | Claude (AI) |
