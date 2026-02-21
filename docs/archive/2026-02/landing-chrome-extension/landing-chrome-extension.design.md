# Landing Page Chrome Extension 소개 — Design Document

> **Summary**: Stellar Memory 랜딩 페이지에 Chrome Extension 소개 섹션, 설치 가이드, i18n 번역 추가
>
> **Project**: stellar-memory
> **Feature**: landing-chrome-extension
> **Plan Reference**: `docs/01-plan/features/landing-chrome-extension.plan.md`
> **Author**: Claude (AI)
> **Date**: 2026-02-21
> **Status**: Design

---

## 1. Architecture Overview

### 1.1 수정 대상

단일 파일: `landing/index.html`

### 1.2 변경 후 페이지 구조

```
1. NAVIGATION — Why? | Use Cases | Extension | How It Works | Get Started | GitHub   ← FR-05 추가
2. HERO — 제목 + 설명 (Extension 언급) + CTA 변경                                     ← FR-02 변경
3. PAIN POINT — (변경 없음)
4. USE CASES — (변경 없음)
5. HOW IT WORKS — (변경 없음)
6. ★ CHROME EXTENSION — 새 섹션 (기능 4카드 + Before/After + CTA)                     ← FR-01 신규
7. FEATURES — (변경 없음)
8. ECOSYSTEM — Homunculus + Chrome Extension + Community 카드                          ← FR-04 추가
9. GET STARTED — Extension + Claude + Cursor + ChatGPT + Other 위저드                  ← FR-03 추가
10. FOOTER — 배지 + 링크 추가                                                          ← FR-06 변경
11. JAVASCRIPT — i18n 5언어 + 위저드 로직 확장                                          ← FR-07/FR-08
```

---

## 2. Feature Specifications

### F1: Chrome Extension 전용 섹션 (FR-01)

**HTML 위치**: `<!-- HOW IT WORKS -->` 섹션 종료 후, `<!-- FEATURES -->` 섹션 시작 전

```html
<!-- ============================================================
     CHROME EXTENSION
============================================================ -->
<section id="chrome-extension" style="padding:100px 0;">
  <div class="container">
    <!-- Header -->
    <div style="text-align:center; margin-bottom:16px;">
      <div class="section-label" data-i18n="ext.label">Chrome Extension</div>
      <h2 class="section-title" data-i18n="ext.title">Install once, every AI remembers you</h2>
      <p class="section-sub" style="margin:0 auto;" data-i18n="ext.subtitle">
        No coding required. Just install and chat — works with ChatGPT, Claude, and Gemini.
      </p>
    </div>

    <!-- Supported AI logos row -->
    <div class="ext-ai-logos">
      <div class="ext-ai-logo">
        <svg ...ChatGPT icon>
        <span>ChatGPT</span>
      </div>
      <div class="ext-ai-logo">
        <svg ...Claude icon>
        <span>Claude</span>
      </div>
      <div class="ext-ai-logo">
        <svg ...Gemini icon>
        <span>Gemini</span>
      </div>
    </div>

    <!-- 4 Feature cards -->
    <div class="ext-features-grid">
      <!-- Card 1: Auto-Capture -->
      <div class="ext-feat-card">
        <div class="ext-feat-icon" style="background:rgba(16,185,129,0.1);">
          <svg stroke="var(--accent-emerald)"> <!-- eye icon --> </svg>
        </div>
        <h3 data-i18n="ext.f1.title">Auto-Capture</h3>
        <p data-i18n="ext.f1.desc">Your conversations are automatically saved as you chat. No buttons to click, nothing to remember.</p>
      </div>

      <!-- Card 2: Auto-Inject -->
      <div class="ext-feat-card">
        <div class="ext-feat-icon" style="background:rgba(240,180,41,0.1);">
          <svg stroke="var(--accent-gold)"> <!-- zap icon --> </svg>
        </div>
        <h3 data-i18n="ext.f2.title">Auto-Inject</h3>
        <p data-i18n="ext.f2.desc">When you start a new chat, relevant memories are automatically included. Your AI already knows the context.</p>
      </div>

      <!-- Card 3: Cross-Platform -->
      <div class="ext-feat-card">
        <div class="ext-feat-icon" style="background:rgba(59,130,246,0.1);">
          <svg stroke="var(--accent-blue)"> <!-- shuffle icon --> </svg>
        </div>
        <h3 data-i18n="ext.f3.title">Cross-Platform Memory</h3>
        <p data-i18n="ext.f3.desc">Tell ChatGPT you love coffee — Claude remembers it too. Your memory follows you across every AI.</p>
      </div>

      <!-- Card 4: Privacy-First -->
      <div class="ext-feat-card">
        <div class="ext-feat-icon" style="background:rgba(139,92,246,0.1);">
          <svg stroke="var(--accent-violet)"> <!-- shield icon --> </svg>
        </div>
        <h3 data-i18n="ext.f4.title">Privacy-First</h3>
        <p data-i18n="ext.f4.desc">All data stays on your computer. Nothing is sent to external servers. Your memories are yours alone.</p>
      </div>
    </div>

    <!-- Before/After Demo -->
    <div class="ext-demo">
      <div class="ext-demo-before">
        <div class="demo-label" data-i18n="ext.before.label">Without Extension</div>
        <div class="chat-bubble user" data-i18n="ext.before.user">"What's my favorite drink?"</div>
        <div class="chat-bubble ai" data-i18n="ext.before.ai">"I'm sorry, I don't have any information about your preferences."</div>
      </div>
      <div class="ext-demo-after">
        <div class="demo-label" data-i18n="ext.after.label">With Extension</div>
        <div class="chat-bubble user" data-i18n="ext.after.user">"What's my favorite drink?"</div>
        <div class="chat-bubble ai" data-i18n="ext.after.ai">"You mentioned you love coffee — especially iced americano!"</div>
      </div>
    </div>

    <!-- CTA -->
    <div style="text-align:center; margin-top:48px;">
      <a href="#get-started" class="btn-primary" style="font-size:1.05rem; padding:14px 32px;">
        <svg ...chrome icon></svg>
        <span data-i18n="ext.cta">Get Chrome Extension</span>
      </a>
      <p style="margin-top:12px; color:var(--text-muted); font-size:0.85rem;" data-i18n="ext.cta.sub">Free & open source — works on any Chromium browser</p>
    </div>
  </div>
</section>
```

### F2: Hero 섹션 업데이트 (FR-02)

**변경 1**: `hero.desc` 텍스트 업데이트 (Chrome Extension 언급)

```
Before: "Give any AI the ability to remember. Free forever, no programming required. Install on your computer in 30 seconds, or use our cloud service."
After:  "Give any AI the ability to remember. Install our Chrome Extension for ChatGPT, Claude & Gemini — or connect via MCP for developer tools. Free forever."
```

**변경 2**: Hero CTA 버튼 변경

```html
<!-- Before -->
<a href="#how-it-works" class="btn-primary">How does it work?</a>
<a href="#get-started" class="btn-secondary">Get Started Free</a>

<!-- After -->
<a href="#chrome-extension" class="btn-primary">
  <svg ...chrome-ext icon></svg>
  <span data-i18n="hero.cta.ext">Get Chrome Extension</span>
</a>
<a href="#get-started" class="btn-secondary">
  <svg ...code icon></svg>
  <span data-i18n="hero.cta.dev">Developer SDK</span>
</a>
```

### F3: Get Started 위저드 업데이트 (FR-03)

**변경**: AI 선택지 맨 앞에 "Chrome Extension" 카드 추가

```html
<!-- New first card -->
<div class="ai-card ai-card-featured" data-ai="extension" onclick="selectAI('extension')">
  <div class="ai-card-icon">
    <svg ...puzzle-piece icon, accent-rose></svg>
  </div>
  <div class="ai-card-label" data-i18n="setup.ai.extension">Chrome Extension</div>
  <div class="ai-card-badge" data-i18n="setup.ai.ext.badge">Easiest</div>
</div>
```

**위저드 instructions 추가**:

```javascript
// JS: WIZARD_INSTRUCTIONS에 추가 (OS 무관, 동일 내용)
'extension-windows': [
  { titleKey: 'setup.ext.s1', action: 'link', url: '#', label: 'Chrome Web Store' },
  { titleKey: 'setup.ext.s2', action: 'text' },
  { titleKey: 'setup.ext.s3', action: 'text' }
],
'extension-macos': [ /* 동일 */ ],
'extension-linux': [ /* 동일 */ ]
```

**위저드 CSS**: ai-card-featured에 특별 스타일 (rose 강조 테두리)

```css
.ai-card-featured {
  border-color: rgba(244,63,94,0.3);
  background: rgba(244,63,94,0.05);
}
.ai-card-featured:hover {
  border-color: rgba(244,63,94,0.5);
}
.ai-card-badge {
  font-size: 0.65rem;
  color: var(--accent-rose);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 4px;
}
```

### F4: Ecosystem 카드 추가 (FR-04)

**위치**: Homunculus 카드와 Community 카드 사이

```html
<!-- Chrome Extension Card -->
<div class="product-card product-featured">
  <div class="product-icon" style="background:rgba(244,63,94,0.1);">
    <svg ...puzzle piece icon, accent-rose></svg>
  </div>
  <h3 class="product-name">Chrome Extension</h3>
  <p class="product-tagline" data-i18n="eco.ext.tagline">AI Memory for ChatGPT, Claude & Gemini</p>
  <p class="product-desc" data-i18n="eco.ext.desc">Install once and every AI remembers you. Automatically captures conversations and injects relevant memories.</p>
  <div class="product-tags">
    <span class="product-tag">Chrome Extension</span>
    <span class="product-tag">ChatGPT</span>
    <span class="product-tag">Claude</span>
    <span class="product-tag">Gemini</span>
    <span class="product-tag">TypeScript</span>
  </div>
  <div class="product-actions">
    <a href="#get-started" class="product-cta-primary" data-i18n="eco.ext.install">
      <svg ...download icon></svg>
      Install Extension
    </a>
    <a href="https://github.com/sangjun0000/stellar-memory/tree/main/stellar-chrome" target="_blank" rel="noopener" class="product-cta-secondary">
      <svg ...github icon></svg>
      <span data-i18n="eco.ext.github">View Source</span>
    </a>
  </div>
</div>
```

**Ecosystem grid**: 3-column grid (Homunculus | Chrome Extension | Community)

```css
.ecosystem-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);  /* was repeat(2, 1fr) */
  gap: 24px;
}
/* Mobile: 1fr stays same */
```

### F5: Navigation 업데이트 (FR-05)

`How It Works` 다음에 `Extension` 링크 추가:

```html
<li><a href="#chrome-extension" data-i18n="nav.extension">Extension</a></li>
```

### F6: Footer 업데이트 (FR-06)

**배지 추가**:
```html
<span class="badge"><span class="badge-dot" style="background:var(--accent-rose);"></span>Chrome Extension</span>
```

**링크 추가** (Project 컬럼):
```html
<li><a href="#get-started">Chrome Extension</a></li>
```

### F7: SEO/Meta 업데이트

**Keywords**:
```html
<meta name="keywords" content="AI memory, LLM memory, stellar memory, celestial memory, MCP, AI agent memory, Python AI library, memory management, chrome extension, browser extension, chatgpt memory, claude memory" />
```

**Schema.org**: applicationCategory에 "BrowserExtension" 추가

---

## 3. i18n Translations (FR-07)

### 3.1 i18n Key 목록

| Key | EN | Purpose |
|-----|-----|---------|
| `nav.extension` | Extension | 네비 링크 |
| `ext.label` | Chrome Extension | 섹션 라벨 |
| `ext.title` | Install once, every AI remembers you | 섹션 제목 |
| `ext.subtitle` | No coding required. Just install and chat — works with ChatGPT, Claude, and Gemini. | 섹션 부제 |
| `ext.f1.title` | Auto-Capture | 기능1 제목 |
| `ext.f1.desc` | Your conversations are automatically saved as you chat. No buttons to click, nothing to remember. | 기능1 설명 |
| `ext.f2.title` | Auto-Inject | 기능2 제목 |
| `ext.f2.desc` | When you start a new chat, relevant memories are automatically included. Your AI already knows the context. | 기능2 설명 |
| `ext.f3.title` | Cross-Platform Memory | 기능3 제목 |
| `ext.f3.desc` | Tell ChatGPT you love coffee — Claude remembers it too. Your memory follows you across every AI. | 기능3 설명 |
| `ext.f4.title` | Privacy-First | 기능4 제목 |
| `ext.f4.desc` | All data stays on your computer. Nothing is sent to external servers. Your memories are yours alone. | 기능4 설명 |
| `ext.before.label` | Without Extension | Before 라벨 |
| `ext.before.user` | "What's my favorite drink?" | Before 사용자 |
| `ext.before.ai` | "I'm sorry, I don't have any information about your preferences." | Before AI |
| `ext.after.label` | With Extension | After 라벨 |
| `ext.after.user` | "What's my favorite drink?" | After 사용자 |
| `ext.after.ai` | "You mentioned you love coffee — especially iced americano!" | After AI |
| `ext.cta` | Get Chrome Extension | CTA 메인 |
| `ext.cta.sub` | Free & open source — works on any Chromium browser | CTA 서브 |
| `hero.cta.ext` | Get Chrome Extension | Hero CTA |
| `hero.cta.dev` | Developer SDK | Hero CTA 2 |
| `setup.ai.extension` | Chrome Extension | 위저드 카드 |
| `setup.ai.ext.badge` | Easiest | 위저드 배지 |
| `setup.ext.s1` | Install from Chrome Web Store | 위저드 스텝1 |
| `setup.ext.s2` | Visit any AI site (ChatGPT, Claude, or Gemini) | 위저드 스텝2 |
| `setup.ext.s3` | Start chatting — Stellar Memory handles the rest! | 위저드 스텝3 |
| `eco.ext.tagline` | AI Memory for ChatGPT, Claude & Gemini | 에코 태그라인 |
| `eco.ext.desc` | Install once and every AI remembers you. Automatically captures conversations and injects relevant memories. | 에코 설명 |
| `eco.ext.install` | Install Extension | 에코 CTA |
| `eco.ext.github` | View Source | 에코 GitHub |

**총 31개 키**

### 3.2 번역 (KO)

```javascript
"nav.extension": "확장 프로그램",
"ext.label": "크롬 확장 프로그램",
"ext.title": "한 번 설치하면, 모든 AI가 나를 기억합니다",
"ext.subtitle": "코딩이 필요 없습니다. 설치하고 대화하세요 — ChatGPT, Claude, Gemini에서 작동합니다.",
"ext.f1.title": "자동 캡처",
"ext.f1.desc": "대화하면 자동으로 저장됩니다. 버튼을 누를 필요도, 기억할 필요도 없습니다.",
"ext.f2.title": "자동 주입",
"ext.f2.desc": "새 대화를 시작하면 관련 기억이 자동으로 포함됩니다. AI가 이미 맥락을 알고 있습니다.",
"ext.f3.title": "크로스 플랫폼 기억",
"ext.f3.desc": "ChatGPT에 커피를 좋아한다고 말하면 — Claude도 기억합니다. 기억이 모든 AI를 따라다닙니다.",
"ext.f4.title": "프라이버시 우선",
"ext.f4.desc": "모든 데이터는 내 컴퓨터에 저장됩니다. 외부 서버로 전송되지 않습니다. 내 기억은 오직 나만의 것.",
"ext.before.label": "확장 프로그램 없이",
"ext.before.user": "\"내가 좋아하는 음료가 뭐야?\"",
"ext.before.ai": "\"죄송합니다, 선호도에 대한 정보가 없습니다.\"",
"ext.after.label": "확장 프로그램 사용 시",
"ext.after.user": "\"내가 좋아하는 음료가 뭐야?\"",
"ext.after.ai": "\"커피를 좋아하신다고 하셨죠 — 특히 아이스 아메리카노요!\"",
"ext.cta": "크롬 확장 프로그램 설치",
"ext.cta.sub": "무료 & 오픈소스 — 모든 크로미움 브라우저에서 작동",
"hero.cta.ext": "크롬 확장 프로그램 설치",
"hero.cta.dev": "개발자 SDK",
"setup.ai.extension": "크롬 확장 프로그램",
"setup.ai.ext.badge": "가장 쉬움",
"setup.ext.s1": "Chrome 웹 스토어에서 설치하세요",
"setup.ext.s2": "아무 AI 사이트를 방문하세요 (ChatGPT, Claude, 또는 Gemini)",
"setup.ext.s3": "대화를 시작하세요 — Stellar Memory가 나머지를 처리합니다!",
"eco.ext.tagline": "ChatGPT, Claude & Gemini를 위한 AI 기억",
"eco.ext.desc": "한 번 설치하면 모든 AI가 나를 기억합니다. 대화를 자동으로 캡처하고 관련 기억을 주입합니다.",
"eco.ext.install": "확장 프로그램 설치",
"eco.ext.github": "소스 보기",
```

### 3.3 번역 (ZH)

```javascript
"nav.extension": "浏览器扩展",
"ext.label": "Chrome 扩展",
"ext.title": "安装一次，所有AI都记住你",
"ext.subtitle": "无需编程。安装后直接对话 — 支持 ChatGPT、Claude 和 Gemini。",
"ext.f1.title": "自动捕获",
"ext.f1.desc": "对话时自动保存。无需点击按钮，无需刻意记忆。",
"ext.f2.title": "自动注入",
"ext.f2.desc": "开始新对话时，相关记忆自动包含。AI已经了解上下文。",
"ext.f3.title": "跨平台记忆",
"ext.f3.desc": "告诉ChatGPT你喜欢咖啡 — Claude也会记住。你的记忆跟随你到每个AI。",
"ext.f4.title": "隐私优先",
"ext.f4.desc": "所有数据保存在你的电脑上。不会发送到外部服务器。你的记忆只属于你。",
"ext.before.label": "没有扩展",
"ext.before.user": "\"我最喜欢的饮料是什么？\"",
"ext.before.ai": "\"抱歉，我没有关于你偏好的信息。\"",
"ext.after.label": "使用扩展后",
"ext.after.user": "\"我最喜欢的饮料是什么？\"",
"ext.after.ai": "\"你说过你喜欢咖啡 — 特别是冰美式！\"",
"ext.cta": "获取 Chrome 扩展",
"ext.cta.sub": "免费开源 — 适用于所有 Chromium 浏览器",
"hero.cta.ext": "获取 Chrome 扩展",
"hero.cta.dev": "开发者 SDK",
"setup.ai.extension": "Chrome 扩展",
"setup.ai.ext.badge": "最简单",
"setup.ext.s1": "从 Chrome 网上应用店安装",
"setup.ext.s2": "访问任意AI网站（ChatGPT、Claude 或 Gemini）",
"setup.ext.s3": "开始对话 — Stellar Memory 处理其余一切！",
"eco.ext.tagline": "ChatGPT、Claude 和 Gemini 的 AI 记忆",
"eco.ext.desc": "安装一次，所有AI都记住你。自动捕获对话并注入相关记忆。",
"eco.ext.install": "安装扩展",
"eco.ext.github": "查看源码",
```

### 3.4 번역 (ES)

```javascript
"nav.extension": "Extensión",
"ext.label": "Extensión de Chrome",
"ext.title": "Instala una vez, toda IA te recuerda",
"ext.subtitle": "Sin programación. Solo instala y chatea — funciona con ChatGPT, Claude y Gemini.",
"ext.f1.title": "Captura Automática",
"ext.f1.desc": "Tus conversaciones se guardan automáticamente mientras chateas. Sin botones, sin complicaciones.",
"ext.f2.title": "Inyección Automática",
"ext.f2.desc": "Al iniciar un nuevo chat, los recuerdos relevantes se incluyen automáticamente. Tu IA ya conoce el contexto.",
"ext.f3.title": "Memoria Multiplataforma",
"ext.f3.desc": "Dile a ChatGPT que te encanta el café — Claude también lo recuerda. Tu memoria te sigue en cada IA.",
"ext.f4.title": "Privacidad Primero",
"ext.f4.desc": "Todos los datos permanecen en tu computadora. Nada se envía a servidores externos. Tus recuerdos son solo tuyos.",
"ext.before.label": "Sin Extensión",
"ext.before.user": "\"¿Cuál es mi bebida favorita?\"",
"ext.before.ai": "\"Lo siento, no tengo información sobre tus preferencias.\"",
"ext.after.label": "Con Extensión",
"ext.after.user": "\"¿Cuál es mi bebida favorita?\"",
"ext.after.ai": "\"¡Mencionaste que te encanta el café — especialmente el americano con hielo!\"",
"ext.cta": "Obtener Extensión de Chrome",
"ext.cta.sub": "Gratis y open source — funciona en cualquier navegador Chromium",
"hero.cta.ext": "Obtener Extensión de Chrome",
"hero.cta.dev": "SDK para Desarrolladores",
"setup.ai.extension": "Extensión de Chrome",
"setup.ai.ext.badge": "Más fácil",
"setup.ext.s1": "Instala desde Chrome Web Store",
"setup.ext.s2": "Visita cualquier sitio de IA (ChatGPT, Claude o Gemini)",
"setup.ext.s3": "Empieza a chatear — ¡Stellar Memory se encarga del resto!",
"eco.ext.tagline": "Memoria IA para ChatGPT, Claude y Gemini",
"eco.ext.desc": "Instala una vez y toda IA te recuerda. Captura conversaciones automáticamente e inyecta recuerdos relevantes.",
"eco.ext.install": "Instalar Extensión",
"eco.ext.github": "Ver Código",
```

### 3.5 번역 (JA)

```javascript
"nav.extension": "拡張機能",
"ext.label": "Chrome 拡張機能",
"ext.title": "一度インストールすれば、すべてのAIがあなたを覚えます",
"ext.subtitle": "プログラミング不要。インストールして会話するだけ — ChatGPT、Claude、Geminiで動作します。",
"ext.f1.title": "自動キャプチャ",
"ext.f1.desc": "会話中に自動保存されます。ボタンをクリックする必要も、覚える必要もありません。",
"ext.f2.title": "自動インジェクション",
"ext.f2.desc": "新しいチャットを始めると、関連する記憶が自動的に含まれます。AIはすでに文脈を理解しています。",
"ext.f3.title": "クロスプラットフォーム記憶",
"ext.f3.desc": "ChatGPTにコーヒーが好きだと言えば — Claudeも覚えています。記憶がすべてのAIについて回ります。",
"ext.f4.title": "プライバシーファースト",
"ext.f4.desc": "すべてのデータはあなたのパソコンに保存されます。外部サーバーには送信されません。記憶はあなただけのもの。",
"ext.before.label": "拡張機能なし",
"ext.before.user": "\"私の好きな飲み物は何？\"",
"ext.before.ai": "\"申し訳ありませんが、お好みに関する情報がありません。\"",
"ext.after.label": "拡張機能使用時",
"ext.after.user": "\"私の好きな飲み物は何？\"",
"ext.after.ai": "\"コーヒーがお好きだとおっしゃっていましたね — 特にアイスアメリカーノ！\"",
"ext.cta": "Chrome 拡張機能を入手",
"ext.cta.sub": "無料＆オープンソース — すべてのChromiumブラウザで動作",
"hero.cta.ext": "Chrome 拡張機能を入手",
"hero.cta.dev": "開発者 SDK",
"setup.ai.extension": "Chrome 拡張機能",
"setup.ai.ext.badge": "最も簡単",
"setup.ext.s1": "Chrome ウェブストアからインストール",
"setup.ext.s2": "AIサイトにアクセス（ChatGPT、Claude、またはGemini）",
"setup.ext.s3": "チャットを始めましょう — Stellar Memoryが残りを処理します！",
"eco.ext.tagline": "ChatGPT、Claude、Gemini用のAIメモリ",
"eco.ext.desc": "一度インストールすればすべてのAIがあなたを覚えます。会話を自動キャプチャし関連する記憶を注入します。",
"eco.ext.install": "拡張機能をインストール",
"eco.ext.github": "ソースを見る",
```

---

## 4. CSS Specifications (FR-08)

### 4.1 Chrome Extension 섹션 CSS

```css
/* ============================================================
   CHROME EXTENSION
============================================================ */
#chrome-extension {
  background: linear-gradient(180deg, transparent 0%, rgba(244,63,94,0.03) 50%, transparent 100%);
}

.ext-ai-logos {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin: 40px 0 48px;
}

.ext-ai-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.ext-ai-logo svg {
  width: 48px;
  height: 48px;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.ext-ai-logo:hover svg { opacity: 1; }

.ext-ai-logo span {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}

.ext-features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 48px;
}

.ext-feat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 28px 24px;
  transition: border-color 0.3s, transform 0.2s, box-shadow 0.3s;
}

.ext-feat-card:hover {
  border-color: rgba(148,163,184,0.2);
  transform: translateY(-4px);
  box-shadow: var(--shadow-card);
}

.ext-feat-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.ext-feat-card h3 {
  font-size: 0.95rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.ext-feat-card p {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Before/After Demo - reuse existing how-demo pattern */
.ext-demo {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.ext-demo-before,
.ext-demo-after {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 24px;
}

.ext-demo-after {
  border-color: rgba(240,180,41,0.2);
  background: rgba(240,180,41,0.02);
}
```

### 4.2 반응형 CSS

```css
@media (max-width: 768px) {
  .ext-features-grid { grid-template-columns: repeat(2, 1fr); }
  .ext-demo { grid-template-columns: 1fr; }
  .ext-ai-logos { gap: 32px; }
  .ecosystem-grid { grid-template-columns: 1fr; }
}

@media (max-width: 480px) {
  .ext-features-grid { grid-template-columns: 1fr; }
}
```

### 4.3 위저드 ai-card-featured CSS

```css
.ai-card-featured {
  border-color: rgba(244,63,94,0.3);
  background: rgba(244,63,94,0.05);
  position: relative;
}

.ai-card-featured:hover {
  border-color: rgba(244,63,94,0.5);
  background: rgba(244,63,94,0.08);
}

.ai-card-badge {
  font-size: 0.6rem;
  color: var(--accent-rose);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 4px;
}
```

---

## 5. JavaScript Changes

### 5.1 WIZARD_INSTRUCTIONS 추가

```javascript
'extension-windows': [
  { titleKey: 'setup.ext.s1', action: 'link', url: 'https://github.com/sangjun0000/stellar-memory/tree/main/stellar-chrome', label: 'GitHub — stellar-chrome' },
  { titleKey: 'setup.ext.s2', action: 'text' },
  { titleKey: 'setup.ext.s3', action: 'text' }
],
'extension-macos': [
  { titleKey: 'setup.ext.s1', action: 'link', url: 'https://github.com/sangjun0000/stellar-memory/tree/main/stellar-chrome', label: 'GitHub — stellar-chrome' },
  { titleKey: 'setup.ext.s2', action: 'text' },
  { titleKey: 'setup.ext.s3', action: 'text' }
],
'extension-linux': [
  { titleKey: 'setup.ext.s1', action: 'link', url: 'https://github.com/sangjun0000/stellar-memory/tree/main/stellar-chrome', label: 'GitHub — stellar-chrome' },
  { titleKey: 'setup.ext.s2', action: 'text' },
  { titleKey: 'setup.ext.s3', action: 'text' }
]
```

### 5.2 renderInstructions `link` 액션 추가

```javascript
// renderInstructions 함수에 'link' 액션 핸들러 추가
} else if (step.action === 'link') {
  html += '<a href="' + step.url + '" target="_blank" rel="noopener" class="wizard-download-btn">';
  html += '<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>';
  html += step.label + '</a>';
}
```

### 5.3 IntersectionObserver 업데이트

`#chrome-extension` 섹션을 fade-in 애니메이션 대상에 추가:

```javascript
// animatedSections 배열에 추가
var animatedSections = [
  // ... existing sections ...
  document.getElementById('chrome-extension'),
  // ... rest ...
];
```

---

## 6. Implementation Order

```
Step 1: CSS 추가 — #chrome-extension, .ext-*, .ai-card-featured, 반응형
Step 2: HTML #chrome-extension 섹션 추가 (HOW IT WORKS 다음)
Step 3: Hero CTA + desc 텍스트 변경
Step 4: Navigation에 Extension 링크 추가
Step 5: Get Started 위저드에 Extension ai-card 추가
Step 6: Ecosystem에 Chrome Extension 카드 추가
Step 7: Footer 배지 + 링크 추가
Step 8: i18n 번역 추가 (EN 31키 + KO 31키 + ZH 31키 + ES 31키 + JA 31키)
Step 9: JavaScript 위저드 로직 + IntersectionObserver 업데이트
Step 10: meta/SEO 업데이트
```

---

## 7. Verification Checklist

- [ ] Chrome Extension 섹션 표시 (4 기능 카드 + Before/After)
- [ ] AI 로고 3개 (ChatGPT, Claude, Gemini) 표시
- [ ] Hero CTA가 "Get Chrome Extension" + "Developer SDK"로 변경
- [ ] Navigation에 "Extension" 링크 존재
- [ ] Get Started 위저드 첫 번째 카드가 "Chrome Extension (Easiest)"
- [ ] Ecosystem에 3개 카드 (Homunculus, Chrome Extension, Community)
- [ ] Footer 배지에 "Chrome Extension" 포함
- [ ] 5개 언어 전환 시 모든 Extension 텍스트 정상 번역
- [ ] 모바일 (480px): 기능 1열, 데모 1열
- [ ] 태블릿 (768px): 기능 2열, 데모 1열
- [ ] 데스크톱: 기능 4열, 데모 2열
