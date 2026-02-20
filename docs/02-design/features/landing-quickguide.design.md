# landing-quickguide Design Document

> **Summary**: Detailed design for landing page UX overhaul — "Who Is This For?" section, in-page setup wizard with AI tool selector, OS auto-detect, and 5-language i18n
>
> **Project**: stellar-memory
> **Version**: 2.0.0
> **Author**: sangjun0000
> **Date**: 2026-02-20
> **Status**: Draft
> **Planning Doc**: [landing-quickguide.plan.md](../01-plan/features/landing-quickguide.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. Non-programmers can set up Stellar Memory without leaving the landing page or visiting GitHub
2. The page clearly communicates WHO benefits from AI memory and WHY
3. The setup wizard auto-detects the user's OS and provides tailored instructions per AI tool
4. All changes fit within the existing single-HTML-file architecture (vanilla CSS + JS, no build step)

### 1.2 Design Principles

- **Zero-redirect**: All critical user flows complete within the page itself
- **Progressive disclosure**: Simple first, details on demand (wizard steps)
- **Inclusive language**: No jargon (no "PyPI", "pip", "MCP" in user-facing copy for non-devs)
- **Consistent styling**: Reuse existing CSS variables, card patterns, and i18n system

---

## 2. Architecture

### 2.1 Page Section Flow (Before → After)

**Before (current):**
```
Nav → Hero → Features → How It Works → Quick Start → Get Started → Footer
```

**After (proposed):**
```
Nav → Hero → Who Is This For? (NEW) → Features → How It Works → Setup Wizard (REPLACED) → Footer
```

Changes:
- **Add** `#use-cases` section after Hero, before Features
- **Remove** `#quickstart` section (Python code block — irrelevant for non-programmers)
- **Replace** `#get-started` section with interactive setup wizard (same `id`, new content)
- **Nav** links update: remove "Quick Start", keep "Get Started"

### 2.2 Component Diagram

```
landing/index.html (single file)
├── CSS: new styles for #use-cases, wizard UI
├── HTML: #use-cases section, rewritten #get-started section
└── JS:
    ├── detectOS()          — auto-detect Windows/macOS/Linux
    ├── selectAI(tool)      — handle AI tool button click
    ├── selectOS(os)        — handle manual OS override
    ├── renderInstructions() — show tailored setup steps
    └── i18n additions      — ~40 new keys × 5 languages
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| Setup wizard JS | Existing i18n system (`T`, `setLang()`) | All wizard text must be translatable |
| OS detection | `navigator.userAgentData` / `navigator.platform` | Auto-select correct OS tab |
| Download links | GitHub Releases URLs | Actual file download source (hidden from user) |

---

## 3. Detailed Design

### 3.1 F1: "Who Is This For?" Section (`#use-cases`)

**Position**: After Hero, before Features.

**Layout**: 4 cards in a responsive grid (2×2 on mobile, 4×1 on desktop).

Each card has:
- Icon (SVG, matching existing style)
- Persona title (e.g., "Students & Learners")
- One-sentence value proposition
- Short description of how AI memory helps them

**HTML Structure:**
```html
<section id="use-cases">
  <div class="container">
    <div class="section-label" data-i18n="uc.label">Who Is This For?</div>
    <h2 class="section-title" data-i18n="uc.title">AI memory for everyone</h2>
    <p class="section-sub" data-i18n="uc.subtitle">
      Not just for developers — anyone who uses AI can benefit from persistent memory.
    </p>
    <div class="use-cases-grid">
      <!-- 4 cards: student, writer, business, developer -->
    </div>
  </div>
</section>
```

**Card Content (EN):**

| Persona | Icon | Title | Description |
|---------|------|-------|-------------|
| Student | GraduationCap | Students & Learners | "Your AI tutor remembers what you studied, where you struggled, and adapts to your learning pace." |
| Writer | Pen | Writers & Creators | "Your AI assistant knows your writing style, your characters, your world — across every session." |
| Business | Briefcase | Business Professionals | "Your AI remembers your clients, projects, and meeting notes — like a personal assistant that never forgets." |
| Developer | Code | Developers | "Add persistent memory to any LLM in 3 lines of code. MCP, REST API, and Python SDK included." |

**CSS** — Reuse `.feature-card` pattern with custom accent colors:
```css
.use-cases-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-top: 48px;
}
.use-case-card {
  /* Same base as .feature-card */
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 28px 24px;
  transition: transform 0.2s, border-color 0.2s;
}
.use-case-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255,255,255,0.15);
}
/* Mobile: 2×2 grid */
@media (max-width: 768px) {
  .use-cases-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .use-cases-grid { grid-template-columns: 1fr; }
}
```

### 3.2 F2+F3+F4: Setup Wizard (`#get-started` replacement)

**Replaces**: Current `#get-started` section (Local vs Cloud cards with GitHub link).

**Layout**: Single centered panel with 3 progressive steps.

#### Step 1: AI Tool Selector

4 clickable cards in a row. Clicking one highlights it and advances to Step 2.

| Tool | Icon | Label |
|------|------|-------|
| Claude Desktop | Anthropic logo (SVG) | Claude Desktop |
| Cursor | Cursor logo (SVG) | Cursor |
| ChatGPT | OpenAI logo (SVG) | ChatGPT |
| Other / Developer | Terminal icon | Other / Developer |

**Behavior**: `selectAI('claude')` → sets `selectedAI` state, shows Step 2.

#### Step 2: OS Selector (auto-detected)

3 pill buttons. The detected OS is pre-selected.

```
[Windows ●] [macOS ○] [Linux ○]
```

**OS Detection Logic:**
```javascript
function detectOS() {
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes('win')) return 'windows';
  if (ua.includes('mac')) return 'macos';
  return 'linux';
}
```

**Behavior**: Auto-runs on page load. User can override by clicking a different pill.

#### Step 3: Tailored Instructions

Content changes dynamically based on (AI tool × OS) selection.

**Instruction Matrix (6 combinations + fallback):**

| AI Tool | OS | Step 1 | Step 2 | Step 3 |
|---------|-----|--------|--------|--------|
| **Claude Desktop** | Windows | Download `stellar-memory-setup.bat` | Double-click the downloaded file | Restart Claude Desktop — done! |
| **Claude Desktop** | macOS/Linux | Open Terminal, paste one command: `curl -sL https://raw.githubusercontent.com/sangjun0000/stellar-memory/main/stellar-memory-setup.sh \| bash` | Restart Claude Desktop — done! | — |
| **Cursor** | Any | Open Cursor Settings (Ctrl+Shift+J) | Go to MCP section, click "+ Add" | Paste server config (shown in copyable box) |
| **ChatGPT** | Any | Install: `pip install stellar-memory` | Add middleware to your code (copyable snippet) | ChatGPT now has persistent memory |
| **Other** | Any | Install: `pip install stellar-memory` | Run MCP server: `stellar-memory serve` | Connect your AI tool to `http://localhost:5464` |

**Instruction Panel HTML:**
```html
<div class="wizard-instructions" id="wizard-instructions">
  <div class="wizard-step-card">
    <div class="wizard-step-num">1</div>
    <div class="wizard-step-content">
      <p id="wizard-s1-title"></p>
      <div id="wizard-s1-action"></div>  <!-- download button OR copyable command -->
    </div>
  </div>
  <div class="wizard-step-card">
    <div class="wizard-step-num">2</div>
    <div class="wizard-step-content">
      <p id="wizard-s2-title"></p>
      <div id="wizard-s2-action"></div>
    </div>
  </div>
  <div class="wizard-step-card" id="wizard-step-3">
    <div class="wizard-step-num">3</div>
    <div class="wizard-step-content">
      <p id="wizard-s3-title"></p>
    </div>
  </div>
</div>
```

**Copyable Command Box** — Reuse existing `.code-window` pattern with copy button:
```html
<div class="copy-box">
  <code id="copy-cmd">curl -sL ... | bash</code>
  <button class="copy-btn" onclick="copyCmd()">
    <svg>...</svg>
  </button>
</div>
```

**MCP Config JSON for Cursor:**
```json
{
  "mcpServers": {
    "stellar-memory": {
      "command": "uvx",
      "args": ["stellar-memory"]
    }
  }
}
```

#### Wizard CSS

```css
/* AI tool selector */
.ai-selector {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 32px 0;
}
.ai-card {
  background: var(--bg-card);
  border: 2px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 20px 16px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, transform 0.2s;
}
.ai-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.2); }
.ai-card.selected { border-color: var(--accent-gold); box-shadow: var(--shadow-glow); }
.ai-card-icon { width: 40px; height: 40px; margin: 0 auto 12px; }
.ai-card-label { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); }

/* OS selector */
.os-selector {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin: 16px 0 32px;
}
.os-pill {
  padding: 8px 20px;
  border-radius: 20px;
  border: 1px solid var(--border-card);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}
.os-pill:hover { border-color: rgba(255,255,255,0.2); }
.os-pill.selected {
  background: var(--accent-gold);
  color: #000;
  border-color: var(--accent-gold);
  font-weight: 600;
}

/* Instruction steps */
.wizard-instructions { margin-top: 32px; }
.wizard-step-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  margin-bottom: 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}
.wizard-step-num {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: var(--accent-gold);
  color: #000;
  font-weight: 700;
  font-size: 0.85rem;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.wizard-step-content { flex: 1; }
.wizard-step-content p { font-size: 0.9rem; color: var(--text-primary); margin-bottom: 8px; }

/* Copy box */
.copy-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-void);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--accent-glow);
  overflow-x: auto;
}
.copy-box code { flex: 1; white-space: nowrap; }

/* Responsive */
@media (max-width: 768px) {
  .ai-selector { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .ai-selector { grid-template-columns: 1fr; }
}
```

### 3.3 F5: Nav Changes

**Before:**
```html
<li><a href="#features">Features</a></li>
<li><a href="#quickstart">Quick Start</a></li>
<li><a href="#get-started">Get Started</a></li>
```

**After:**
```html
<li><a href="#use-cases" data-i18n="nav.usecases">Use Cases</a></li>
<li><a href="#features" data-i18n="nav.features">Features</a></li>
<li><a href="#get-started" data-i18n="nav.getstarted">Get Started</a></li>
```

### 3.4 F6: Hero CTA Update

**Before:**
```html
<a href="#get-started" class="btn-primary">Get Started Free</a>
<a href="https://github.com/..." class="btn-secondary">View on GitHub</a>
```

**After:**
```html
<a href="#get-started" class="btn-primary">Get Started Free</a>
<a href="#use-cases" class="btn-secondary">Who Is This For?</a>
```

GitHub link moved to footer only (already there).

---

## 4. JavaScript Specification

### 4.1 State Management

```javascript
// Wizard state (module-level variables)
let selectedAI = null;   // 'claude' | 'cursor' | 'chatgpt' | 'other'
let selectedOS = null;   // 'windows' | 'macos' | 'linux'
```

### 4.2 Core Functions

```javascript
// Auto-detect OS on page load
function detectOS() {
  const ua = navigator.userAgent.toLowerCase();
  if (ua.includes('win')) return 'windows';
  if (ua.includes('mac')) return 'macos';
  return 'linux';
}

// Handle AI tool selection
function selectAI(tool) {
  selectedAI = tool;
  // Update UI: highlight selected card, dim others
  document.querySelectorAll('.ai-card').forEach(c => c.classList.remove('selected'));
  document.querySelector(`[data-ai="${tool}"]`).classList.add('selected');
  // Show OS selector + instructions
  document.getElementById('wizard-step2').style.display = 'block';
  document.getElementById('wizard-step3').style.display = 'block';
  renderInstructions();
}

// Handle OS selection
function selectOS(os) {
  selectedOS = os;
  document.querySelectorAll('.os-pill').forEach(p => p.classList.remove('selected'));
  document.querySelector(`[data-os="${os}"]`).classList.add('selected');
  renderInstructions();
}

// Render tailored instructions based on selectedAI + selectedOS
function renderInstructions() {
  const lang = currentLang || 'en';
  const key = `${selectedAI}-${selectedOS}`;
  const instructions = getInstructions(key, lang);
  // Update DOM: wizard-s1-title, wizard-s1-action, etc.
}
```

### 4.3 Instruction Data Structure

```javascript
const INSTRUCTIONS = {
  'claude-windows': {
    steps: [
      {
        titleKey: 'setup.claude.win.s1',
        action: 'download',
        url: 'https://raw.githubusercontent.com/sangjun0000/stellar-memory/main/stellar-memory-setup.bat',
        filename: 'stellar-memory-setup.bat'
      },
      {
        titleKey: 'setup.claude.win.s2',
        action: 'text'
      },
      {
        titleKey: 'setup.claude.win.s3',
        action: 'text'
      }
    ]
  },
  'claude-macos': {
    steps: [
      {
        titleKey: 'setup.claude.mac.s1',
        action: 'copy',
        command: 'curl -sL https://raw.githubusercontent.com/sangjun0000/stellar-memory/main/stellar-memory-setup.sh | bash'
      },
      {
        titleKey: 'setup.claude.mac.s2',
        action: 'text'
      }
    ]
  },
  'claude-linux': { /* same as macos */ },
  'cursor-windows': {
    steps: [
      {
        titleKey: 'setup.cursor.s1',
        action: 'text'
      },
      {
        titleKey: 'setup.cursor.s2',
        action: 'copy',
        command: '{\n  "mcpServers": {\n    "stellar-memory": {\n      "command": "uvx",\n      "args": ["stellar-memory"]\n    }\n  }\n}'
      },
      {
        titleKey: 'setup.cursor.s3',
        action: 'text'
      }
    ]
  },
  'chatgpt-*': {
    steps: [
      {
        titleKey: 'setup.chatgpt.s1',
        action: 'copy',
        command: 'pip install stellar-memory'
      },
      {
        titleKey: 'setup.chatgpt.s2',
        action: 'copy',
        command: 'from stellar_memory.middleware import ChatGPTMiddleware\nmiddleware = ChatGPTMiddleware()\n# Wrap your ChatGPT calls with middleware'
      },
      {
        titleKey: 'setup.chatgpt.s3',
        action: 'text'
      }
    ]
  },
  'other-*': {
    steps: [
      {
        titleKey: 'setup.other.s1',
        action: 'copy',
        command: 'pip install stellar-memory'
      },
      {
        titleKey: 'setup.other.s2',
        action: 'copy',
        command: 'stellar-memory serve'
      },
      {
        titleKey: 'setup.other.s3',
        action: 'text'
      }
    ]
  }
};
```

### 4.4 Download Button Behavior

For `action: 'download'`, render a gold button that directly downloads the file:
```html
<a href="{url}" download="{filename}" class="btn-primary" style="font-size:0.85rem;">
  Download {filename}
</a>
```

This uses GitHub raw URL to download directly — no GitHub UI involved.

---

## 5. i18n Specification

### 5.1 New Keys — English (EN)

```javascript
// Nav
"nav.usecases": "Use Cases",

// Who Is This For?
"uc.label": "Who Is This For?",
"uc.title": "AI memory for everyone",
"uc.subtitle": "Not just for developers — anyone who uses AI can benefit from persistent memory.",
"uc.student.title": "Students & Learners",
"uc.student.desc": "Your AI tutor remembers what you studied, where you struggled, and adapts to your learning pace.",
"uc.writer.title": "Writers & Creators",
"uc.writer.desc": "Your AI assistant knows your writing style, your characters, your world — across every session.",
"uc.business.title": "Business Professionals",
"uc.business.desc": "Your AI remembers your clients, projects, and meeting notes — like a personal assistant that never forgets.",
"uc.dev.title": "Developers",
"uc.dev.desc": "Add persistent memory to any LLM in 3 lines of code. MCP, REST API, and Python SDK included.",

// Setup Wizard
"setup.label": "Get Started",
"setup.title": "Set up in 3 easy steps",
"setup.subtitle": "Choose your AI tool, and we'll guide you through the rest. No coding required.",
"setup.step1": "Which AI do you use?",
"setup.step2": "Your system",
"setup.step2.auto": "auto-detected",
"setup.step3": "Follow these steps",
"setup.ai.claude": "Claude Desktop",
"setup.ai.cursor": "Cursor",
"setup.ai.chatgpt": "ChatGPT",
"setup.ai.other": "Other / Developer",

// Claude Desktop instructions
"setup.claude.win.s1": "Download the installer",
"setup.claude.win.s2": "Double-click the downloaded file to install",
"setup.claude.win.s3": "Restart Claude Desktop — done! Stellar Memory is now connected.",
"setup.claude.mac.s1": "Open Terminal and paste this command",
"setup.claude.mac.s2": "Restart Claude Desktop — done! Stellar Memory is now connected.",

// Cursor instructions
"setup.cursor.s1": "Open Cursor Settings → MCP section",
"setup.cursor.s2": "Click '+ Add Server' and paste this config",
"setup.cursor.s3": "Save and restart Cursor — done!",

// ChatGPT instructions
"setup.chatgpt.s1": "Install the library",
"setup.chatgpt.s2": "Add this middleware to your code",
"setup.chatgpt.s3": "ChatGPT now has persistent memory across sessions.",

// Other instructions
"setup.other.s1": "Install Stellar Memory",
"setup.other.s2": "Start the MCP server",
"setup.other.s3": "Connect your AI tool to http://localhost:5464",

// Footer link
"setup.advanced": "Advanced: View on GitHub"
```

### 5.2 New Keys — Korean (KO)

```javascript
"nav.usecases": "활용 사례",
"uc.label": "누구를 위한 건가요?",
"uc.title": "모두를 위한 AI 기억",
"uc.subtitle": "개발자만을 위한 것이 아닙니다 — AI를 사용하는 모든 사람이 영구 기억의 혜택을 받을 수 있습니다.",
"uc.student.title": "학생 & 학습자",
"uc.student.desc": "AI 튜터가 공부한 내용, 어려웠던 부분을 기억하고 학습 속도에 맞춰 도와줍니다.",
"uc.writer.title": "작가 & 크리에이터",
"uc.writer.desc": "AI 어시스턴트가 당신의 글쓰기 스타일, 캐릭터, 세계관을 모든 세션에서 기억합니다.",
"uc.business.title": "비즈니스 전문가",
"uc.business.desc": "AI가 고객, 프로젝트, 회의 노트를 기억합니다 — 절대 잊지 않는 개인 비서처럼.",
"uc.dev.title": "개발자",
"uc.dev.desc": "코드 3줄로 모든 LLM에 영구 기억을 추가하세요. MCP, REST API, Python SDK 포함.",
"setup.label": "시작하기",
"setup.title": "3단계로 간편 설정",
"setup.subtitle": "사용하는 AI 도구를 선택하면 나머지는 안내해 드립니다. 코딩이 필요 없습니다.",
"setup.step1": "어떤 AI를 사용하시나요?",
"setup.step2": "운영체제",
"setup.step2.auto": "자동 감지",
"setup.step3": "아래 단계를 따라하세요",
"setup.ai.claude": "Claude Desktop",
"setup.ai.cursor": "Cursor",
"setup.ai.chatgpt": "ChatGPT",
"setup.ai.other": "기타 / 개발자",
"setup.claude.win.s1": "설치 파일을 다운로드하세요",
"setup.claude.win.s2": "다운로드한 파일을 더블클릭하여 설치",
"setup.claude.win.s3": "Claude Desktop을 재시작하면 완료! Stellar Memory가 연결되었습니다.",
"setup.claude.mac.s1": "터미널을 열고 이 명령어를 붙여넣으세요",
"setup.claude.mac.s2": "Claude Desktop을 재시작하면 완료! Stellar Memory가 연결되었습니다.",
"setup.cursor.s1": "Cursor 설정 → MCP 섹션을 여세요",
"setup.cursor.s2": "'+ 서버 추가'를 클릭하고 이 설정을 붙여넣으세요",
"setup.cursor.s3": "저장하고 Cursor를 재시작하면 완료!",
"setup.chatgpt.s1": "라이브러리를 설치하세요",
"setup.chatgpt.s2": "이 미들웨어를 코드에 추가하세요",
"setup.chatgpt.s3": "이제 ChatGPT가 세션 간 영구 기억을 가집니다.",
"setup.other.s1": "Stellar Memory를 설치하세요",
"setup.other.s2": "MCP 서버를 시작하세요",
"setup.other.s3": "AI 도구를 http://localhost:5464에 연결하세요",
"setup.advanced": "고급: GitHub에서 보기"
```

### 5.3 New Keys — Chinese (ZH)

```javascript
"nav.usecases": "使用场景",
"uc.label": "适合谁？",
"uc.title": "人人可用的AI记忆",
"uc.subtitle": "不仅适用于开发者 — 任何使用AI的人都能从持久记忆中受益。",
"uc.student.title": "学生和学习者",
"uc.student.desc": "AI导师记住你学过什么、哪里遇到困难，并根据你的学习节奏进行调整。",
"uc.writer.title": "作家和创作者",
"uc.writer.desc": "AI助手了解你的写作风格、角色和世界观 — 贯穿每一次对话。",
"uc.business.title": "商务人士",
"uc.business.desc": "AI记住你的客户、项目和会议笔记 — 就像一个永不遗忘的私人助理。",
"uc.dev.title": "开发者",
"uc.dev.desc": "3行代码为任何LLM添加持久记忆。包含MCP、REST API和Python SDK。",
"setup.label": "开始使用",
"setup.title": "3步轻松设置",
"setup.subtitle": "选择你的AI工具，我们将引导你完成其余步骤。无需编程。",
"setup.step1": "你使用哪个AI？",
"setup.step2": "你的系统",
"setup.step2.auto": "自动检测",
"setup.step3": "按照以下步骤操作",
"setup.ai.claude": "Claude Desktop",
"setup.ai.cursor": "Cursor",
"setup.ai.chatgpt": "ChatGPT",
"setup.ai.other": "其他 / 开发者",
"setup.claude.win.s1": "下载安装程序",
"setup.claude.win.s2": "双击下载的文件进行安装",
"setup.claude.win.s3": "重启Claude Desktop — 完成！Stellar Memory已连接。",
"setup.claude.mac.s1": "打开终端并粘贴此命令",
"setup.claude.mac.s2": "重启Claude Desktop — 完成！Stellar Memory已连接。",
"setup.cursor.s1": "打开Cursor设置 → MCP部分",
"setup.cursor.s2": "点击'+ 添加服务器'并粘贴此配置",
"setup.cursor.s3": "保存并重启Cursor — 完成！",
"setup.chatgpt.s1": "安装库",
"setup.chatgpt.s2": "将此中间件添加到你的代码中",
"setup.chatgpt.s3": "ChatGPT现在拥有跨会话的持久记忆。",
"setup.other.s1": "安装Stellar Memory",
"setup.other.s2": "启动MCP服务器",
"setup.other.s3": "将你的AI工具连接到 http://localhost:5464",
"setup.advanced": "高级：在GitHub上查看"
```

### 5.4 New Keys — Spanish (ES)

```javascript
"nav.usecases": "Casos de Uso",
"uc.label": "Para quién es?",
"uc.title": "Memoria AI para todos",
"uc.subtitle": "No solo para desarrolladores — cualquiera que use IA puede beneficiarse de la memoria persistente.",
"uc.student.title": "Estudiantes",
"uc.student.desc": "Tu tutor IA recuerda lo que estudiaste, dónde tuviste dificultades, y se adapta a tu ritmo de aprendizaje.",
"uc.writer.title": "Escritores y Creadores",
"uc.writer.desc": "Tu asistente IA conoce tu estilo de escritura, tus personajes, tu mundo — en cada sesión.",
"uc.business.title": "Profesionales",
"uc.business.desc": "Tu IA recuerda tus clientes, proyectos y notas de reuniones — como un asistente personal que nunca olvida.",
"uc.dev.title": "Desarrolladores",
"uc.dev.desc": "Agrega memoria persistente a cualquier LLM en 3 líneas de código. MCP, REST API y Python SDK incluidos.",
"setup.label": "Comenzar",
"setup.title": "Configura en 3 pasos fáciles",
"setup.subtitle": "Elige tu herramienta de IA y te guiaremos en el resto. Sin necesidad de programar.",
"setup.step1": "Qué IA usas?",
"setup.step2": "Tu sistema",
"setup.step2.auto": "auto-detectado",
"setup.step3": "Sigue estos pasos",
"setup.ai.claude": "Claude Desktop",
"setup.ai.cursor": "Cursor",
"setup.ai.chatgpt": "ChatGPT",
"setup.ai.other": "Otro / Desarrollador",
"setup.claude.win.s1": "Descarga el instalador",
"setup.claude.win.s2": "Haz doble clic en el archivo descargado para instalar",
"setup.claude.win.s3": "Reinicia Claude Desktop — listo! Stellar Memory está conectado.",
"setup.claude.mac.s1": "Abre Terminal y pega este comando",
"setup.claude.mac.s2": "Reinicia Claude Desktop — listo! Stellar Memory está conectado.",
"setup.cursor.s1": "Abre Configuración de Cursor → sección MCP",
"setup.cursor.s2": "Haz clic en '+ Agregar Servidor' y pega esta configuración",
"setup.cursor.s3": "Guarda y reinicia Cursor — listo!",
"setup.chatgpt.s1": "Instala la biblioteca",
"setup.chatgpt.s2": "Agrega este middleware a tu código",
"setup.chatgpt.s3": "ChatGPT ahora tiene memoria persistente entre sesiones.",
"setup.other.s1": "Instala Stellar Memory",
"setup.other.s2": "Inicia el servidor MCP",
"setup.other.s3": "Conecta tu herramienta de IA a http://localhost:5464",
"setup.advanced": "Avanzado: Ver en GitHub"
```

### 5.5 New Keys — Japanese (JA)

```javascript
"nav.usecases": "活用例",
"uc.label": "誰のため？",
"uc.title": "みんなのためのAI記憶",
"uc.subtitle": "開発者だけのものではありません — AIを使う全ての人が永続メモリの恩恵を受けられます。",
"uc.student.title": "学生・学習者",
"uc.student.desc": "AIチューターがあなたの学習内容、苦手な箇所を覚え、学習ペースに合わせてサポートします。",
"uc.writer.title": "作家・クリエイター",
"uc.writer.desc": "AIアシスタントがあなたの文体、キャラクター、世界観を全セッションで記憶します。",
"uc.business.title": "ビジネスプロフェッショナル",
"uc.business.desc": "AIがクライアント、プロジェクト、会議メモを記憶 — 忘れない個人秘書のように。",
"uc.dev.title": "開発者",
"uc.dev.desc": "3行のコードで任意のLLMに永続メモリを追加。MCP、REST API、Python SDK付属。",
"setup.label": "始める",
"setup.title": "3つの簡単ステップで設定",
"setup.subtitle": "AIツールを選ぶだけ。あとはガイドします。プログラミング不要。",
"setup.step1": "どのAIを使っていますか？",
"setup.step2": "お使いのシステム",
"setup.step2.auto": "自動検出",
"setup.step3": "以下の手順に従ってください",
"setup.ai.claude": "Claude Desktop",
"setup.ai.cursor": "Cursor",
"setup.ai.chatgpt": "ChatGPT",
"setup.ai.other": "その他 / 開発者",
"setup.claude.win.s1": "インストーラーをダウンロード",
"setup.claude.win.s2": "ダウンロードしたファイルをダブルクリックしてインストール",
"setup.claude.win.s3": "Claude Desktopを再起動 — 完了！Stellar Memoryが接続されました。",
"setup.claude.mac.s1": "ターミナルを開いてこのコマンドを貼り付け",
"setup.claude.mac.s2": "Claude Desktopを再起動 — 完了！Stellar Memoryが接続されました。",
"setup.cursor.s1": "Cursor設定 → MCPセクションを開く",
"setup.cursor.s2": "'+ サーバー追加'をクリックしてこの設定を貼り付け",
"setup.cursor.s3": "保存してCursorを再起動 — 完了！",
"setup.chatgpt.s1": "ライブラリをインストール",
"setup.chatgpt.s2": "このミドルウェアをコードに追加",
"setup.chatgpt.s3": "ChatGPTにセッション間の永続メモリが追加されました。",
"setup.other.s1": "Stellar Memoryをインストール",
"setup.other.s2": "MCPサーバーを起動",
"setup.other.s3": "AIツールをhttp://localhost:5464に接続",
"setup.advanced": "上級者向け：GitHubで見る"
```

---

## 6. Sections to Remove

### 6.1 Remove `#quickstart` Section (lines ~1377-1437)

The current Quick Start section shows `quickstart.py` Python code which is developer-only content. Remove entirely. The "How It Works" section (Store/Recall) already explains the concept visually.

### 6.2 Remove Nav "Quick Start" Link

Remove `<li><a href="#quickstart">Quick Start</a></li>` from nav.

---

## 7. Test Plan

### 7.1 Test Scenarios

| # | Scenario | Expected Result |
|---|----------|-----------------|
| 1 | Page loads on Windows | OS auto-detected as "Windows", pill pre-selected |
| 2 | Page loads on macOS | OS auto-detected as "macOS", pill pre-selected |
| 3 | Click "Claude Desktop" + Windows | Shows .bat download button + 3 steps |
| 4 | Click "Claude Desktop" + macOS | Shows curl command + 2 steps |
| 5 | Click "Cursor" + any OS | Shows MCP config JSON + 3 steps |
| 6 | Click "ChatGPT" + any OS | Shows pip install + middleware snippet |
| 7 | Click "Other" + any OS | Shows pip install + MCP serve command |
| 8 | Switch language to KO | All wizard text changes to Korean |
| 9 | Mobile (375px) | AI cards stack to 1 column, wizard remains usable |
| 10 | Use Cases section visible | 4 persona cards render correctly |

### 7.2 Verification Method

- Manual browser testing (Chrome, Firefox, Safari)
- Mobile simulation via Chrome DevTools
- i18n: switch all 5 languages, verify no missing keys
- Gap analysis via `/pdca analyze`

---

## 8. Implementation Order

1. [ ] Add CSS for `#use-cases` section and wizard components
2. [ ] Add `#use-cases` HTML section (4 persona cards)
3. [ ] Rewrite `#get-started` HTML section (wizard with 3 steps)
4. [ ] Remove `#quickstart` section and its nav link
5. [ ] Update nav links (add Use Cases, remove Quick Start)
6. [ ] Update Hero CTA (secondary button → Use Cases instead of GitHub)
7. [ ] Add JavaScript: `detectOS()`, `selectAI()`, `selectOS()`, `renderInstructions()`
8. [ ] Add `INSTRUCTIONS` data object with all AI×OS combinations
9. [ ] Add i18n keys for all 5 languages (~40 keys × 5 = 200 translations)
10. [ ] Test all wizard paths + responsive + i18n
11. [ ] Deploy via `deploy.sh`

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-20 | Initial draft | sangjun0000 |
