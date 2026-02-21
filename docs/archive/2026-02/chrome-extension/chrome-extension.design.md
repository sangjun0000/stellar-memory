# Chrome Extension Design Document

> **Summary**: ChatGPT/Claude/Gemini에서 대화를 자동 기억하고 주입하는 크롬 확장 프로그램 상세 설계
>
> **Project**: stellar-memory
> **Version**: v3.0.0 → v3.1.0
> **Author**: Claude (AI)
> **Date**: 2026-02-21
> **Status**: Draft
> **Planning Doc**: [chrome-extension.plan.md](../01-plan/features/chrome-extension.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. **Zero-Config**: 설치 후 설정 없이 즉시 동작
2. **Privacy-First**: 모든 데이터 로컬 저장, 외부 전송 없음
3. **Non-Intrusive**: AI 사이트의 기존 UX를 방해하지 않음
4. **Resilient**: AI 사이트 DOM 변경에도 핵심 기능 유지
5. **Lightweight**: 메모리 < 50MB, 입력 지연 < 200ms

### 1.2 Design Principles

- **Selector 격리**: DOM selector를 config JSON으로 분리하여 사이트 변경 시 빠른 대응
- **Message-Based**: Content Script ↔ Background Worker 간 Chrome Message API로 통신
- **Graceful Degradation**: API 서버 미실행 시에도 Extension 크래시 없음 (기억 기능만 비활성)
- **Preset 활용**: 기존 SDK의 `Preset.CHAT`을 그대로 사용

---

## 2. Architecture

### 2.1 Component Diagram

```
┌────────────────────────── Chrome Extension ──────────────────────────┐
│                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐  │
│  │   Popup (UI)    │  │  Side Panel     │  │   Content Scripts    │  │
│  │   400×500px     │  │  (UI)           │  │                      │  │
│  │                 │  │                 │  │  chatgpt-cs.ts       │  │
│  │  MemoryList     │  │  RelatedPanel   │  │  claude-cs.ts        │  │
│  │  SearchBar      │  │                 │  │  gemini-cs.ts        │  │
│  │  SiteToggles    │  │                 │  │                      │  │
│  │  StatusBar      │  │                 │  │  shared/             │  │
│  └───────┬─────────┘  └───────┬─────────┘  │   observer.ts       │  │
│          │                    │             │   injector.ts        │  │
│          │                    │             │   extractor.ts       │  │
│          └────────┬───────────┘             └──────────┬───────────┘  │
│                   │                                    │              │
│          ┌────────▼────────────────────────────────────▼──────┐      │
│          │           Background Service Worker                 │      │
│          │           (background.ts)                           │      │
│          │                                                     │      │
│          │   ┌──────────┐ ┌──────────┐ ┌───────────────────┐  │      │
│          │   │ApiClient │ │ MsgRouter│ │ SettingsManager   │  │      │
│          │   └──────────┘ └──────────┘ └───────────────────┘  │      │
│          └─────────────────────┬───────────────────────────────┘      │
│                                │                                      │
└────────────────────────────────┼──────────────────────────────────────┘
                                 │ HTTP localhost:9000
                     ┌───────────▼───────────────┐
                     │  Stellar Memory REST API   │
                     │  (기존 Python 서버)          │
                     │                            │
                     │  /api/v1/store             │
                     │  /api/v1/recall            │
                     │  /api/v1/stats             │
                     │  /api/v1/forget/{id}       │
                     │  /api/v1/health            │
                     └────────────────────────────┘
```

### 2.2 Data Flow

**대화 캡처 흐름 (Store)**:
```
AI 사이트 DOM 변화
  → Content Script (MutationObserver) 감지
  → extractor.ts: 메시지 텍스트 + 메타데이터 추출
  → chrome.runtime.sendMessage({type: "STORE"})
  → Background Worker: ApiClient
  → POST /api/v1/store {content, importance, metadata}
  → Stellar Memory SQLite 저장
```

**기억 주입 흐름 (Recall + Inject)**:
```
사용자 입력창 포커스 or 전송 직전
  → Content Script: 입력 텍스트 감지
  → chrome.runtime.sendMessage({type: "RECALL", query})
  → Background Worker: ApiClient
  → GET /api/v1/recall?q={query}&limit=5
  → 관련 기억 수신
  → Content Script: injector.ts
  → 입력 텍스트 앞에 기억 컨텍스트 삽입
  → 사용자가 전송
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| Content Scripts | Background Worker | API 통신 중개 |
| Background Worker | REST API (localhost:9000) | 기억 저장/검색 |
| Popup UI | Background Worker | 상태 조회/설정 변경 |
| Side Panel | Background Worker | 관련 기억 표시 |
| REST API | Stellar Memory SDK | 기억 관리 엔진 |

---

## 3. Data Model

### 3.1 Chrome Storage Schema

```typescript
// chrome.storage.local에 저장되는 설정
interface StellarSettings {
  enabled: boolean;              // 전체 on/off
  sites: {
    chatgpt: boolean;            // ChatGPT on/off
    claude: boolean;             // Claude on/off
    gemini: boolean;             // Gemini on/off
  };
  injection: {
    mode: "auto" | "manual";     // 자동 주입 vs 사이드 패널만
    maxMemories: number;         // 주입할 최대 기억 수 (default: 5)
    minImportance: number;       // 최소 중요도 필터 (default: 0.3)
  };
  api: {
    baseUrl: string;             // default: "http://localhost:9000"
    connected: boolean;          // 서버 연결 상태
  };
  stats: {
    totalStored: number;         // 총 저장된 기억 수
    lastSync: string;            // 마지막 동기화 시간
  };
}
```

### 3.2 Message Protocol

Content Script ↔ Background Worker 간 메시지 규격:

```typescript
// Content Script → Background Worker
type CSMessage =
  | { type: "STORE"; payload: StorePayload }
  | { type: "RECALL"; payload: RecallPayload }
  | { type: "FORGET"; payload: { memoryId: string } }
  | { type: "GET_SETTINGS" }
  | { type: "GET_STATS" }
  | { type: "CHECK_CONNECTION" };

interface StorePayload {
  content: string;
  importance: number;
  metadata: {
    source: "chatgpt" | "claude" | "gemini";
    url: string;
    role: "user" | "assistant";
    conversationId?: string;
    timestamp: number;
  };
}

interface RecallPayload {
  query: string;
  limit: number;
  source?: "chatgpt" | "claude" | "gemini";
}

// Background Worker → Content Script
interface RecallResponse {
  memories: Array<{
    id: string;
    content: string;
    zone: number;
    importance: number;
    source: string;
    createdAt: string;
  }>;
}
```

### 3.3 REST API 사용 엔드포인트 (기존 서버)

| Method | Path | 용도 | 파라미터 |
|--------|------|------|----------|
| GET | `/api/v1/health` | 서버 연결 확인 | - |
| POST | `/api/v1/store` | 기억 저장 | content, importance, metadata |
| GET | `/api/v1/recall` | 기억 검색 | q, limit |
| DELETE | `/api/v1/forget/{id}` | 기억 삭제 | memory_id |
| GET | `/api/v1/stats` | 통계 조회 | - |

---

## 4. Feature Specification

### F1: Site Selectors Config

각 AI 사이트의 DOM selector를 JSON으로 분리하여, 사이트 UI 변경 시 코드 수정 없이 selector만 업데이트:

```typescript
// src/content/selectors.ts
interface SiteSelectors {
  // 메시지 영역
  messageContainer: string;     // 전체 메시지 목록 컨테이너
  userMessage: string;          // 사용자 메시지 요소
  assistantMessage: string;     // AI 응답 요소
  messageText: string;          // 메시지 내 텍스트 추출 대상

  // 입력 영역
  inputArea: string;            // 입력창
  submitButton: string;         // 전송 버튼
  formElement: string;          // form 요소 (submit 이벤트용)
}

const SELECTORS: Record<string, SiteSelectors> = {
  chatgpt: {
    messageContainer: "main .flex.flex-col",
    userMessage: "[data-message-author-role='user']",
    assistantMessage: "[data-message-author-role='assistant']",
    messageText: ".markdown",
    inputArea: "#prompt-textarea",
    submitButton: "[data-testid='send-button']",
    formElement: "form",
  },
  claude: {
    messageContainer: "[class*='conversation']",
    userMessage: "[data-testid='user-message']",
    assistantMessage: "[data-testid='ai-message']",
    messageText: "[class*='message-content']",
    inputArea: "[contenteditable='true']",
    submitButton: "button[aria-label='Send']",
    formElement: "form",
  },
  gemini: {
    messageContainer: ".conversation-container",
    userMessage: ".user-query",
    assistantMessage: ".model-response",
    messageText: ".message-content",
    inputArea: "rich-textarea .ql-editor",
    submitButton: "button.send-button",
    formElement: "form",
  },
};
```

### F2: Conversation Observer (observer.ts)

MutationObserver로 새 메시지 감지:

```typescript
// src/content/shared/observer.ts
export function createConversationObserver(
  selectors: SiteSelectors,
  onNewMessage: (msg: ExtractedMessage) => void
): MutationObserver {
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node instanceof HTMLElement) {
          const userMsg = node.querySelector(selectors.userMessage);
          const aiMsg = node.querySelector(selectors.assistantMessage);

          if (userMsg) {
            const text = extractText(userMsg, selectors.messageText);
            if (text) onNewMessage({ role: "user", content: text });
          }
          if (aiMsg) {
            const text = extractText(aiMsg, selectors.messageText);
            if (text) onNewMessage({ role: "assistant", content: text });
          }
        }
      }
    }
  });

  const container = document.querySelector(selectors.messageContainer);
  if (container) {
    observer.observe(container, { childList: true, subtree: true });
  }

  return observer;
}
```

**핵심 설계**:
- `childList: true, subtree: true`로 깊은 DOM 변화도 감지
- 새 메시지 추가 시에만 트리거 (속성 변화 무시)
- container가 없으면 1초 간격으로 재시도 (SPA 로딩 대기)
- debounce 300ms: AI 응답이 스트리밍으로 올 때 완성 후 캡처

### F3: Memory Injector (injector.ts)

기억을 사용자 메시지에 주입하는 모듈:

```typescript
// src/content/shared/injector.ts

const MEMORY_PREFIX = "[Stellar Memory — 이 사용자에 대해 기억하고 있는 것들]";
const MEMORY_SUFFIX = "[기억 끝 — 위 기억을 참고하여 대화해주세요]\n\n";

export function formatMemoryContext(memories: RecallResponse["memories"]): string {
  if (memories.length === 0) return "";

  const lines = memories.map((m) => {
    const age = getRelativeTime(m.createdAt);
    return `- ${m.content} (${age})`;
  });

  return `${MEMORY_PREFIX}\n${lines.join("\n")}\n${MEMORY_SUFFIX}`;
}

export function injectIntoInput(
  selectors: SiteSelectors,
  memoryContext: string,
  originalText: string
): void {
  const input = document.querySelector(selectors.inputArea);
  if (!input) return;

  const injected = memoryContext + originalText;

  if (input instanceof HTMLTextAreaElement) {
    // ChatGPT: textarea
    input.value = injected;
    input.dispatchEvent(new Event("input", { bubbles: true }));
  } else if (input.getAttribute("contenteditable")) {
    // Claude, Gemini: contenteditable div
    input.textContent = injected;
    input.dispatchEvent(new InputEvent("input", { bubbles: true }));
  }
}
```

**주입 타이밍**: 사용자가 전송 버튼 클릭 or Enter 키 누르기 **직전**에 가로채서 주입.

```typescript
// 전송 이벤트 가로채기
function interceptSubmit(selectors: SiteSelectors, onBeforeSubmit: (text: string) => Promise<string>) {
  const form = document.querySelector(selectors.formElement);
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const input = document.querySelector(selectors.inputArea);
    const originalText = getInputText(input);

    // 기억 검색 + 주입
    const injectedText = await onBeforeSubmit(originalText);
    setInputText(input, injectedText);

    // 원래 submit 실행
    form.requestSubmit();
  }, { capture: true, once: false });
}
```

### F4: Background Service Worker (background.ts)

```typescript
// src/background/background.ts

import { ApiClient } from "../lib/api-client";
import { SettingsManager } from "../lib/settings-manager";

const api = new ApiClient();
const settings = new SettingsManager();

chrome.runtime.onMessage.addListener((msg: CSMessage, sender, sendResponse) => {
  handleMessage(msg, sender).then(sendResponse);
  return true; // async response
});

async function handleMessage(msg: CSMessage, sender: chrome.runtime.MessageSender) {
  switch (msg.type) {
    case "STORE":
      return api.store(msg.payload);

    case "RECALL":
      return api.recall(msg.payload);

    case "FORGET":
      return api.forget(msg.payload.memoryId);

    case "GET_SETTINGS":
      return settings.getAll();

    case "GET_STATS":
      return api.getStats();

    case "CHECK_CONNECTION":
      return api.checkHealth();

    default:
      return { error: "Unknown message type" };
  }
}

// 서버 연결 상태 주기적 확인 (30초)
setInterval(async () => {
  const connected = await api.checkHealth();
  await settings.update({ api: { connected } });
}, 30000);
```

### F5: API Client (api-client.ts)

```typescript
// src/lib/api-client.ts

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl = "http://localhost:9000") {
    this.baseUrl = baseUrl;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/health`, {
        signal: AbortSignal.timeout(3000),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  async store(payload: StorePayload): Promise<StoreResult> {
    const res = await fetch(`${this.baseUrl}/api/v1/store`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: payload.content,
        importance: payload.importance,
        metadata: payload.metadata,
      }),
    });
    return res.json();
  }

  async recall(payload: RecallPayload): Promise<RecallResponse> {
    const params = new URLSearchParams({
      q: payload.query,
      limit: String(payload.limit),
    });
    const res = await fetch(`${this.baseUrl}/api/v1/recall?${params}`);
    return res.json();
  }

  async forget(memoryId: string): Promise<{ removed: boolean }> {
    const res = await fetch(`${this.baseUrl}/api/v1/forget/${memoryId}`, {
      method: "DELETE",
    });
    return res.json();
  }

  async getStats(): Promise<StatsResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/stats`);
    return res.json();
  }
}
```

### F6: Popup UI

```
┌─────────────────────────────────┐  400 × 500px
│  ☀️ Stellar Memory        ⚙️    │  Header
│─────────────────────────────────│
│  🔍 기억 검색...                 │  SearchBar
│─────────────────────────────────│
│  ● 서버 연결됨  |  127개 기억     │  StatusBar
│─────────────────────────────────│
│                                 │
│  ☀️ Core (5)                     │  MemoryList
│    "커피를 좋아함"        [🗑️]   │   - grouped by zone
│    "React 선호"          [🗑️]   │   - delete button
│                                 │
│  🪐 Inner (23)                   │
│    "한국어 선호"          [🗑️]   │
│    "다크모드 사용"        [🗑️]   │
│    ...                          │
│─────────────────────────────────│
│  사이트 설정                     │  SiteToggles
│  ChatGPT  [━━━●]  ON            │
│  Claude   [━━━●]  ON            │
│  Gemini   [●━━━]  OFF           │
│─────────────────────────────────│
│  기억 주입: ○ 자동  ● 수동       │  InjectionMode
└─────────────────────────────────┘
```

**React 컴포넌트 구조**:

| Component | File | Responsibility |
|-----------|------|----------------|
| `Popup` | `popup/Popup.tsx` | 메인 레이아웃 |
| `SearchBar` | `popup/SearchBar.tsx` | 기억 검색 입력 |
| `StatusBar` | `popup/StatusBar.tsx` | 서버 상태 + 기억 수 표시 |
| `MemoryList` | `popup/MemoryList.tsx` | 존별 기억 목록 + 삭제 |
| `MemoryItem` | `popup/MemoryItem.tsx` | 개별 기억 표시 |
| `SiteToggles` | `popup/SiteToggles.tsx` | 사이트별 on/off 토글 |
| `InjectionMode` | `popup/InjectionMode.tsx` | 자동/수동 주입 선택 |

### F7: Side Panel

```
┌──────────────────────────────┐  300px width
│  관련 기억                    │
│──────────────────────────────│
│                              │
│  📌 이 대화와 관련된 기억:     │
│                              │
│  ┌────────────────────────┐  │
│  │ ☀️ "커피를 좋아함"      │  │  MemoryCard
│  │ 2일 전 · ChatGPT       │  │
│  │ 중요도: ████████░░ 0.8  │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │ 🪐 "React 개발자"      │  │
│  │ 5일 전 · Claude        │  │
│  │ 중요도: ██████░░░░ 0.6  │  │
│  └────────────────────────┘  │
│                              │
│──────────────────────────────│
│  💡 기억이 자동 주입됩니다    │
│  [주입 끄기]                 │
└──────────────────────────────┘
```

Side Panel은 사용자가 현재 입력 중인 내용에 맞춰 실시간으로 관련 기억을 표시. 입력 변경 시 500ms debounce 후 recall 실행.

### F8: Content Script Entry Points

각 사이트별 Content Script는 공통 모듈을 조합:

```typescript
// src/content/chatgpt-cs.ts
import { SELECTORS } from "./selectors";
import { createConversationObserver } from "./shared/observer";
import { interceptSubmit, formatMemoryContext } from "./shared/injector";
import { sendToBackground } from "./shared/bridge";

const site = "chatgpt";
const sel = SELECTORS[site];

// 1. 대화 캡처 시작
createConversationObserver(sel, async (msg) => {
  await sendToBackground({
    type: "STORE",
    payload: {
      content: `[${msg.role}] ${msg.content}`,
      importance: msg.role === "user" ? 0.6 : 0.4,
      metadata: {
        source: site,
        url: window.location.href,
        role: msg.role,
        timestamp: Date.now(),
      },
    },
  });
});

// 2. 기억 주입 설정
interceptSubmit(sel, async (originalText) => {
  const settings = await sendToBackground({ type: "GET_SETTINGS" });
  if (!settings.enabled || !settings.sites[site]) return originalText;
  if (settings.injection.mode !== "auto") return originalText;

  const { memories } = await sendToBackground({
    type: "RECALL",
    payload: { query: originalText, limit: settings.injection.maxMemories },
  });

  if (memories.length === 0) return originalText;
  return formatMemoryContext(memories) + originalText;
});
```

Claude와 Gemini도 동일 패턴, selector만 다름.

---

## 5. Manifest V3 Configuration

```json
{
  "manifest_version": 3,
  "name": "Stellar Memory — AI가 나를 기억합니다",
  "version": "1.0.0",
  "description": "ChatGPT, Claude, Gemini에서 대화를 자동으로 기억합니다",

  "permissions": [
    "storage",
    "sidePanel",
    "contextMenus",
    "activeTab"
  ],

  "host_permissions": [
    "https://chat.openai.com/*",
    "https://chatgpt.com/*",
    "https://claude.ai/*",
    "https://gemini.google.com/*",
    "http://localhost:9000/*"
  ],

  "background": {
    "service_worker": "src/background/background.ts",
    "type": "module"
  },

  "content_scripts": [
    {
      "matches": ["https://chat.openai.com/*", "https://chatgpt.com/*"],
      "js": ["src/content/chatgpt-cs.ts"]
    },
    {
      "matches": ["https://claude.ai/*"],
      "js": ["src/content/claude-cs.ts"]
    },
    {
      "matches": ["https://gemini.google.com/*"],
      "js": ["src/content/gemini-cs.ts"]
    }
  ],

  "action": {
    "default_popup": "src/popup/index.html",
    "default_icon": {
      "16": "public/icons/icon-16.png",
      "32": "public/icons/icon-32.png",
      "48": "public/icons/icon-48.png",
      "128": "public/icons/icon-128.png"
    }
  },

  "side_panel": {
    "default_path": "src/sidepanel/index.html"
  },

  "icons": {
    "16": "public/icons/icon-16.png",
    "48": "public/icons/icon-48.png",
    "128": "public/icons/icon-128.png"
  },

  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

---

## 6. Error Handling

### 6.1 서버 미연결 시

```typescript
// ApiClient 내부
async store(payload: StorePayload): Promise<StoreResult> {
  try {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (err) {
    // 서버 미연결: 큐에 저장, 재연결 시 재전송
    await this.queue.push({ action: "store", payload });
    return { id: null, error: "offline", queued: true };
  }
}
```

### 6.2 DOM Selector 실패 시

```typescript
// 폴백: 알려진 패턴으로 재시도
function findInputArea(selectors: SiteSelectors): HTMLElement | null {
  // 1차: 지정된 selector
  let el = document.querySelector(selectors.inputArea);
  if (el) return el as HTMLElement;

  // 2차: 일반적인 패턴 시도
  el = document.querySelector("textarea[placeholder]")
    || document.querySelector("[contenteditable='true']");
  if (el) return el as HTMLElement;

  // 실패: 로그 남기고 null 반환 (기능 비활성)
  console.warn("[Stellar] Input area not found. Memory injection disabled.");
  return null;
}
```

### 6.3 에러 코드

| Code | Scenario | Handling |
|------|----------|----------|
| OFFLINE | 서버 미연결 | 오프라인 큐 + 상태바 표시 |
| SELECTOR_MISS | DOM selector 실패 | 폴백 시도 + 로그 |
| RATE_LIMITED | API 429 | 지수 백오프 재시도 |
| STORE_FAIL | 저장 실패 | 큐 + 재시도 |
| RECALL_FAIL | 검색 실패 | 빈 결과 반환 (주입 생략) |

---

## 7. Security Considerations

- [x] **로컬 전용**: 모든 데이터 localhost 통신, 외부 서버 없음
- [x] **최소 권한**: 필요한 사이트(3개) + localhost만 host_permissions
- [x] **CSP 준수**: Manifest V3 Content Security Policy
- [ ] **입력 검증**: store 시 content 길이 제한 (10,000자)
- [ ] **XSS 방지**: 기억 내용 표시 시 textContent 사용 (innerHTML 금지)
- [ ] **Rate Limit**: 초당 최대 2회 store 제한 (클라이언트 측)

---

## 8. Test Plan

### 8.1 Test Scope

| Type | Target | Tool |
|------|--------|------|
| Unit | ApiClient, observer, injector, extractor | Vitest |
| Component | Popup, SidePanel React 컴포넌트 | Vitest + Testing Library |
| E2E | ChatGPT에서 전체 흐름 | Playwright |
| Integration | Extension ↔ REST API 통신 | Vitest + MSW |

### 8.2 Key Test Cases

- [ ] ChatGPT에서 사용자 메시지 캡처 → store API 호출 확인
- [ ] ChatGPT에서 AI 응답 캡처 → store API 호출 확인
- [ ] 메시지 전송 시 관련 기억 자동 주입 확인
- [ ] 서버 미연결 시 Extension 크래시 없음
- [ ] Popup에서 기억 목록 표시 + 삭제 동작
- [ ] 사이트 토글 off → 해당 사이트 캡처 중단
- [ ] DOM selector 변경 시 폴백 동작
- [ ] Side Panel에서 관련 기억 실시간 업데이트

---

## 9. File Structure

```
stellar-chrome/
├── manifest.json                     # Chrome Manifest V3
├── package.json                      # 의존성
├── vite.config.ts                    # Vite + CRXJS
├── tsconfig.json                     # TypeScript
├── tailwind.config.js                # Tailwind CSS
│
├── src/
│   ├── background/
│   │   └── background.ts             # Service Worker (메시지 라우팅)
│   │
│   ├── content/
│   │   ├── selectors.ts              # 사이트별 DOM selector config
│   │   ├── chatgpt-cs.ts             # ChatGPT Content Script
│   │   ├── claude-cs.ts              # Claude Content Script
│   │   ├── gemini-cs.ts              # Gemini Content Script
│   │   └── shared/
│   │       ├── observer.ts           # MutationObserver 대화 감지
│   │       ├── injector.ts           # 기억 주입 + 전송 가로채기
│   │       ├── extractor.ts          # 메시지 텍스트 추출
│   │       └── bridge.ts             # chrome.runtime.sendMessage 래퍼
│   │
│   ├── popup/
│   │   ├── index.html                # Popup entry
│   │   ├── main.tsx                  # React mount
│   │   ├── Popup.tsx                 # 메인 레이아웃
│   │   ├── SearchBar.tsx             # 검색
│   │   ├── StatusBar.tsx             # 서버 상태 + 기억 수
│   │   ├── MemoryList.tsx            # 존별 기억 목록
│   │   ├── MemoryItem.tsx            # 개별 기억
│   │   ├── SiteToggles.tsx           # 사이트 on/off
│   │   └── InjectionMode.tsx         # 자동/수동 모드
│   │
│   ├── sidepanel/
│   │   ├── index.html                # Side Panel entry
│   │   ├── main.tsx                  # React mount
│   │   ├── SidePanel.tsx             # 메인
│   │   └── MemoryCard.tsx            # 개별 기억 카드
│   │
│   ├── lib/
│   │   ├── api-client.ts             # REST API 클라이언트
│   │   ├── settings-manager.ts       # chrome.storage 설정 관리
│   │   ├── offline-queue.ts          # 오프라인 큐 (서버 미연결 대비)
│   │   └── utils.ts                  # 유틸리티 (getRelativeTime 등)
│   │
│   ├── types/
│   │   └── index.ts                  # 공통 TypeScript 타입
│   │
│   └── styles/
│       └── global.css                # Tailwind + 글로벌 스타일
│
├── public/
│   ├── icons/
│   │   ├── icon-16.png
│   │   ├── icon-32.png
│   │   ├── icon-48.png
│   │   └── icon-128.png
│   └── onboarding.html               # 설치 후 안내 페이지
│
└── tests/
    ├── unit/
    │   ├── api-client.test.ts
    │   ├── observer.test.ts
    │   ├── injector.test.ts
    │   └── extractor.test.ts
    ├── component/
    │   ├── Popup.test.tsx
    │   └── SidePanel.test.tsx
    └── e2e/
        └── chatgpt-flow.test.ts
```

---

## 10. Implementation Order

| Step | Task | Files | Depends On |
|:----:|------|-------|:----------:|
| 1 | 프로젝트 셋업 (Vite + CRXJS + manifest.json) | package.json, vite.config.ts, manifest.json | - |
| 2 | Types + API Client + Settings Manager | types/, lib/ | Step 1 |
| 3 | Background Service Worker | background/background.ts | Step 2 |
| 4 | Shared Content Script 모듈 (observer, injector, extractor, bridge) | content/shared/ | Step 3 |
| 5 | ChatGPT Content Script + Selectors | content/chatgpt-cs.ts, selectors.ts | Step 4 |
| 6 | Popup UI (React 전체) | popup/ | Step 3 |
| 7 | Claude + Gemini Content Scripts | content/claude-cs.ts, gemini-cs.ts | Step 4 |
| 8 | Side Panel UI | sidepanel/ | Step 3 |
| 9 | 온보딩 페이지 | public/onboarding.html | Step 1 |
| 10 | 테스트 + Chrome Web Store 준비 | tests/, 아이콘, 스크린샷 | Step 1~9 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-21 | Initial design | Claude (AI) |
