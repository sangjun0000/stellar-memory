# free-access-overhaul Design Document

> **Summary**: 수익화 비활성화, 1클릭 설치, 클라우드 모드, 랜딩 페이지/문서 개편으로 비개발자 접근성 대폭 개선
>
> **Project**: stellar-memory
> **Version**: 2.0.0
> **Author**: sangjun0000
> **Date**: 2026-02-20
> **Status**: Draft
> **Planning Doc**: [free-access-overhaul.plan.md](../../01-plan/features/free-access-overhaul.plan.md)

---

## 1. Overview

### 1.1 Design Goals

1. 모든 기능 제한 해제 (무제한 무료)
2. 프로그래밍 지식 없이도 설치/사용 가능한 환경 구축
3. 로컬/클라우드 2가지 선택지 명확 제공
4. 랜딩 페이지에서 가격표 제거, "무료 & 오픈소스" 강조
5. 결제 코드는 보존 (추후 재활용)

### 1.2 Design Principles

- **비파괴적 비활성화**: 빌링 코드 삭제하지 않고 설정값만 변경
- **비개발자 우선**: 모든 UI/문서는 프로그래밍 용어 최소화
- **점진적 복잡도**: 간단한 것부터 보여주고, 개발자 옵션은 하단에 배치

---

## 2. Feature Specifications

### F1. 수익화 시스템 비활성화

#### F1-01. tiers.py — 제한값 무제한 변경

**파일**: `stellar_memory/billing/tiers.py`
**액션**: MODIFY

```python
# BEFORE (lines 5-24)
TIER_LIMITS: dict[str, dict] = {
    "free": {
        "max_memories": 1_000,
        "max_agents": 1,
        "rate_limit": 60,  # per minute
        "max_api_keys": 1,
    },
    "pro": {
        "max_memories": 50_000,
        "max_agents": 5,
        "rate_limit": 300,
        "max_api_keys": 5,
    },
    "promax": {
        "max_memories": 500_000,
        "max_agents": -1,  # unlimited
        "rate_limit": 1_000,
        "max_api_keys": 20,
    },
}

# AFTER
TIER_LIMITS: dict[str, dict] = {
    "free": {
        "max_memories": -1,   # unlimited
        "max_agents": -1,     # unlimited
        "rate_limit": 120,    # per minute (server protection only)
        "max_api_keys": -1,   # unlimited
    },
    "pro": {
        "max_memories": -1,
        "max_agents": -1,
        "rate_limit": 120,
        "max_api_keys": -1,
    },
    "promax": {
        "max_memories": -1,
        "max_agents": -1,
        "rate_limit": 120,
        "max_api_keys": -1,
    },
}
```

**변경 사항 (4개)**:
- `free.max_memories`: 1,000 → -1 (무제한)
- `free.max_agents`: 1 → -1 (무제한)
- `free.max_api_keys`: 1 → -1 (무제한)
- 모든 티어 `rate_limit`: 동일하게 120으로 통일 (서버 보호용)
- `_TIER_ORDER`, `get_tier_limits()`, `next_tier()` 함수는 그대로 유지 (빌링 코드 보존)

#### F1-02. fly.toml — 빌링 비활성화

**파일**: `fly.toml`
**액션**: MODIFY (line 11)

```toml
# BEFORE
STELLAR_BILLING_ENABLED = "true"

# AFTER
STELLAR_BILLING_ENABLED = "false"
```

#### F1-03. Schema.org JSON-LD — 무료 단일 Offer

**파일**: `landing/index.html`
**액션**: MODIFY (lines 27-31)

```json
// BEFORE
"offers": [
  {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD", "description": "1,000 memories, 1 agent, SQLite, Local MCP"},
  {"@type": "Offer", "name": "Pro", "price": "15", "priceCurrency": "USD", "billingIncrement": "P1M", "description": "50,000 memories, 5 agents, PostgreSQL, Cloud MCP, Dashboard"},
  {"@type": "Offer", "name": "Pro Max", "price": "29", "priceCurrency": "USD", "billingIncrement": "P1M", "description": "500,000 memories, Unlimited agents, Team Sync, RBAC, Audit Logs"}
],

// AFTER
"offers": [
  {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "USD", "description": "Unlimited memories, unlimited agents, all features included. 100% free & open source."}
],
```

#### F1-04. config.py — BillingConfig 확인

**파일**: `stellar_memory/config.py`
**액션**: VERIFY (변경 불필요)

`BillingConfig.enabled: bool = False`는 이미 기본값이 `False`이므로 코드 변경 불필요. `fly.toml`의 환경변수 `STELLAR_BILLING_ENABLED`만 `false`로 변경하면 됨.

---

### F2. 로컬 모드 간소화 (1클릭 설치)

#### F2-01. Windows 설치 스크립트

**파일**: `stellar-memory-setup.bat`
**액션**: CREATE (프로젝트 루트)

```batch
@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   Stellar Memory - Setup
echo   AI Memory System Installer
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed.
    echo     Download from: https://www.python.org/downloads/
    echo     Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/3] Installing Stellar Memory...
pip install stellar-memory[mcp] --quiet
if %errorlevel% neq 0 (
    echo [!] Installation failed. Check your internet connection.
    pause
    exit /b 1
)

echo [2/3] Setting up MCP for AI IDE...
stellar-memory setup --yes
if %errorlevel% neq 0 (
    echo [!] MCP setup had issues, but Stellar Memory is installed.
    echo     You can run "stellar-memory setup" later.
)

echo [3/3] Done!
echo.
echo ============================================
echo   Installation complete!
echo.
echo   If you use Claude Desktop or Cursor,
echo   restart the app to activate AI memory.
echo.
echo   Try telling your AI: "Remember my name"
echo ============================================
pause
```

#### F2-02. macOS/Linux 설치 스크립트

**파일**: `stellar-memory-setup.sh`
**액션**: CREATE (프로젝트 루트)

```bash
#!/usr/bin/env bash
set -e

echo "============================================"
echo "  Stellar Memory - Setup"
echo "  AI Memory System Installer"
echo "============================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is not installed."
    echo "    macOS: brew install python3"
    echo "    Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "    Other: https://www.python.org/downloads/"
    exit 1
fi

echo "[1/3] Installing Stellar Memory..."
pip3 install stellar-memory[mcp] --quiet

echo "[2/3] Setting up MCP for AI IDE..."
stellar-memory setup --yes || echo "[!] MCP setup had issues. Run 'stellar-memory setup' later."

echo "[3/3] Done!"
echo
echo "============================================"
echo "  Installation complete!"
echo
echo "  If you use Claude Desktop or Cursor,"
echo "  restart the app to activate AI memory."
echo
echo "  Try telling your AI: \"Remember my name\""
echo "============================================"
```

파일 권한: `chmod +x stellar-memory-setup.sh` (릴리즈 시 설정)

#### F2-03. CLI setup 명령 추가

**파일**: `stellar_memory/cli.py`
**액션**: MODIFY

**추가할 subcommand 등록** (line 122 이후에 추가):

```python
# setup (one-click)
p_setup = subparsers.add_parser("setup", help="Auto-setup: install MCP for your AI IDE")
p_setup.add_argument("--yes", "-y", action="store_true",
                     help="Skip confirmation prompts")

# start
subparsers.add_parser("start", help="Start MCP server (auto-detect transport)")

# status (alias for health with friendly output)
# Note: 'stats' already exists for memory stats, so we use 'status' for system status
p_status = subparsers.add_parser("status", help="Check system status")
```

**추가할 command handler** (line 323 이전, serve-api handler 이후):

```python
elif args.command == "setup":
    _run_setup(args)

elif args.command == "start":
    from stellar_memory.mcp_server import run_server
    run_server(config, namespace=args.namespace, transport="stdio")

elif args.command == "status":
    h = memory.health()
    status_str = "OK" if h.healthy else "PROBLEM"
    print(f"Stellar Memory: {status_str}")
    print(f"Memories stored: {h.total_memories}")
    if not h.healthy:
        for w in h.warnings:
            print(f"  Warning: {w}")
```

**추가할 _run_setup 함수** (cli.py 하단):

```python
def _run_setup(args) -> None:
    """One-click setup: detect IDE and configure MCP."""
    import platform
    from pathlib import Path

    print("Stellar Memory - Auto Setup")
    print("=" * 40)
    print()

    # Detect available IDEs
    claude_path = Path(_claude_config_path())
    cursor_path = Path(_cursor_config_path())

    claude_exists = claude_path.parent.exists()
    cursor_exists = cursor_path.parent.exists()

    if not claude_exists and not cursor_exists:
        print("No AI IDE detected (Claude Desktop or Cursor).")
        print()
        print("Install one of these:")
        print("  - Claude Desktop: https://claude.ai/download")
        print("  - Cursor: https://cursor.sh")
        print()
        print("After installing, run this command again.")
        return

    targets = []
    if claude_exists:
        targets.append(("Claude Desktop", "claude"))
    if cursor_exists:
        targets.append(("Cursor", "cursor"))

    print(f"Detected: {', '.join(name for name, _ in targets)}")

    if not args.yes:
        try:
            confirm = input(f"\nSet up MCP for {', '.join(name for name, _ in targets)}? [Y/n]: ").strip().lower()
            if confirm == 'n':
                print("Setup cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            return

    db_path = str(Path("~/.stellar/memory.db").expanduser())
    config_content = {
        "mcpServers": {
            "stellar-memory": {
                "command": "stellar-memory",
                "args": ["serve", "--transport", "stdio"],
                "env": {
                    "STELLAR_DB_PATH": db_path,
                },
            }
        }
    }

    for name, ide in targets:
        config_path = _get_mcp_config_path(ide)
        _merge_mcp_config(config_path, config_content)
        print(f"  {name}: configured")

    print()
    print("Setup complete!")
    print(f"Database: {db_path}")
    print()
    print("Restart your AI IDE to activate Stellar Memory.")
    print('Try saying: "Remember my name is ___"')
```

#### F2-04. quickstart 명령 간소화

**파일**: `stellar_memory/cli.py`
**액션**: MODIFY (`_run_quickstart` 함수 교체)

```python
def _run_quickstart(args) -> None:
    """Interactive quickstart wizard — simplified for non-developers."""
    print("=" * 50)
    print("  Stellar Memory")
    print("  Give your AI the ability to remember")
    print("=" * 50)
    print()
    print("Choose how to use Stellar Memory:")
    print()
    print("  1. With AI IDE (Claude Desktop / Cursor)")
    print("     → Your AI will automatically remember things")
    print()
    print("  2. As a Python library (for developers)")
    print("     → Use in your own code")
    print()

    try:
        choice = input("Select [1-2, default=1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice == "1":
        # Run setup directly
        class SetupArgs:
            yes = False
            db = args.db
        _run_setup(SetupArgs())
    else:
        db_path = args.db
        from stellar_memory import StellarMemory, StellarConfig
        config = StellarConfig(db_path=db_path)
        mem = StellarMemory(config)
        item = mem.store("Hello, Stellar Memory! This is my first memory.", importance=0.9)

        print(f"\nYour first memory is stored!")
        print(f"  ID:   {item.id[:8]}...")
        print(f"  Zone: {item.zone}")
        print()
        print("Try recalling:")
        print(f'  stellar-memory recall "hello" --db {db_path}')
        mem.stop()
```

---

### F3. 클라우드 모드 안내

#### F3-01. 클라우드 정보 (현재 인프라 기반)

클라우드 모드는 이미 구축된 Fly.io 서버 + REST API를 활용. 별도 새 인프라 구축 없이 기존 `serve-api` 엔드포인트를 안내.

**현재 클라우드 인프라**:
- Fly.io: `stellar-memory-api` 앱 (Tokyo region)
- REST API: `/api/v1/*` 엔드포인트
- 인증: API Key 기반

**랜딩 페이지에서의 안내 방식**:
클라우드 카드에서 "Coming Soon" 또는 REST API 문서 링크로 연결. 실제 웹 대시보드 구축은 이 Design scope 외 (별도 프로젝트).

#### F3-02. 클라우드 카드 CTA

**로컬 카드**: 설치 스크립트 다운로드 링크 (GitHub Releases)
**클라우드 카드**: REST API 문서 링크 + "Web Dashboard Coming Soon" 표시

---

### F4. 랜딩 페이지 개편

#### F4-01. Meta 태그 변경

**파일**: `landing/index.html`
**액션**: MODIFY (lines 6-14)

```html
<!-- BEFORE -->
<meta name="description" content="Give any AI human-like memory. Celestial-structure-based memory system with 5 orbital zones, self-learning, and multimodal support." />
<meta property="og:title" content="Stellar Memory — Give any AI human-like memory" />
<meta property="og:description" content="Celestial-structure-based AI memory management system. 5 orbital zones, self-learning, multimodal, and MCP integration." />

<!-- AFTER -->
<meta name="description" content="Free &amp; open-source AI memory system. Give any AI the ability to remember — install in 30 seconds or use in the cloud." />
<meta property="og:title" content="Stellar Memory — Free AI Memory for Everyone" />
<meta property="og:description" content="100% free, open-source AI memory. Install locally in 30 seconds or use our cloud service. No programming required." />
```

```html
<!-- BEFORE -->
<meta name="twitter:title" content="Stellar Memory — Give any AI human-like memory" />
<meta name="twitter:description" content="Celestial-structure-based AI memory management. 5 orbital zones, self-learning, and multimodal." />

<!-- AFTER -->
<meta name="twitter:title" content="Stellar Memory — Free AI Memory for Everyone" />
<meta name="twitter:description" content="100% free, open-source AI memory. No programming required. Install in 30 seconds." />
```

#### F4-02. Page title 변경

**파일**: `landing/index.html`
**액션**: MODIFY (line 45)

```html
<!-- BEFORE -->
<title>Stellar Memory — Give any AI human-like memory</title>

<!-- AFTER -->
<title>Stellar Memory — Free AI Memory for Everyone</title>
```

#### F4-03. Nav 링크 변경

**파일**: `landing/index.html`
**액션**: MODIFY (line 1137)

```html
<!-- BEFORE -->
<li><a href="#pricing" data-i18n="nav.pricing">Pricing</a></li>

<!-- AFTER -->
<li><a href="#get-started" data-i18n="nav.getstarted">Get Started</a></li>
```

#### F4-04. Hero 섹션 변경

**파일**: `landing/index.html`
**액션**: MODIFY (lines 1172-1200)

```html
<!-- BEFORE -->
<div class="hero-badge">
  <span class="hero-badge-dot"></span>
  <span data-i18n="hero.badge">v2.0.0 — Now Available on PyPI</span>
</div>
<h1 class="hero-title">
  <span class="hero-title-gradient" data-i18n="hero.title">Stellar Memory</span>
</h1>
<p class="hero-tagline" data-i18n="hero.subtitle">Give any AI human-like memory</p>
<p class="hero-desc" data-i18n="hero.desc">A celestial-structure-based memory system that organizes, prioritizes, and evolves memories across five orbital zones — just like the cosmos.</p>
<div class="hero-actions">
  <a href="#quickstart" class="btn-primary">
    <svg ...>...</svg>
    Get Started
  </a>
  <a href="https://github.com/sangjun0000/stellar-memory" target="_blank" rel="noopener" class="btn-secondary">
    <svg ...>...</svg>
    View on GitHub
  </a>
</div>
<div class="hero-install">
  <span class="install-prefix">$</span>
  <span class="install-cmd" id="install-text">pip install stellar-memory</span>
  <button class="copy-btn" onclick="copyInstall()" ...>...</button>
</div>

<!-- AFTER -->
<div class="hero-badge">
  <span class="hero-badge-dot"></span>
  <span data-i18n="hero.badge">100% Free &amp; Open Source</span>
</div>
<h1 class="hero-title">
  <span class="hero-title-gradient" data-i18n="hero.title">Stellar Memory</span>
</h1>
<p class="hero-tagline" data-i18n="hero.subtitle">AI remembers you</p>
<p class="hero-desc" data-i18n="hero.desc">Give any AI the ability to remember. Free forever, no programming required. Install on your computer in 30 seconds, or use our cloud service.</p>
<div class="hero-actions">
  <a href="#get-started" class="btn-primary">
    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
    <span data-i18n="hero.cta.start">Get Started Free</span>
  </a>
  <a href="https://github.com/sangjun0000/stellar-memory" target="_blank" rel="noopener" class="btn-secondary">
    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.868-.013-1.703-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0 1 12 6.836a9.59 9.59 0 0 1 2.504.337c1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.741 0 .267.18.579.688.481C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z"/></svg>
    View on GitHub
  </a>
</div>
<!-- Remove pip install bar — non-developers don't use terminal -->
```

#### F4-05. Pricing 섹션 → Get Started 섹션 교체

**파일**: `landing/index.html`
**액션**: REPLACE (lines 1451-1516)

Pricing 섹션 전체를 제거하고 아래 "Get Started" 섹션으로 교체:

```html
<!-- ============================================================
     GET STARTED (Local vs Cloud - replaces Pricing)
============================================================ -->
<section id="get-started">
  <div class="container">
    <div style="text-align:center;">
      <div class="section-label" data-i18n="start.label">Get Started</div>
      <h2 class="section-title" data-i18n="start.title">Choose how to use Stellar Memory</h2>
      <p class="section-sub" style="margin:0 auto;" data-i18n="start.subtitle">Both options are 100% free. Choose what works best for you.</p>
    </div>

    <div class="pricing-grid">
      <!-- Local -->
      <div class="pricing-card pricing-popular">
        <div class="pricing-badge" data-i18n="start.local.badge">Recommended</div>
        <div class="pricing-tier" data-i18n="start.local.title">On Your Computer</div>
        <div class="pricing-price" data-i18n="start.local.price">Free<span></span></div>
        <div class="pricing-desc" data-i18n="start.local.desc">Install and run locally</div>
        <ul class="pricing-features">
          <li class="incl" data-i18n="start.local.f1">100% private — data stays on your PC</li>
          <li class="incl" data-i18n="start.local.f2">Works offline — no internet needed</li>
          <li class="incl" data-i18n="start.local.f3">Unlimited memories &amp; agents</li>
          <li class="incl" data-i18n="start.local.f4">Auto-connects to Claude &amp; Cursor</li>
          <li class="incl" data-i18n="start.local.f5">30-second setup</li>
        </ul>
        <a href="https://github.com/sangjun0000/stellar-memory/releases" target="_blank" rel="noopener" class="pricing-cta pricing-cta-gold" data-i18n="start.local.cta">Download Installer</a>
      </div>

      <!-- Cloud -->
      <div class="pricing-card">
        <div class="pricing-tier" data-i18n="start.cloud.title">In the Cloud</div>
        <div class="pricing-price" data-i18n="start.cloud.price">Free<span></span></div>
        <div class="pricing-desc" data-i18n="start.cloud.desc">Use from any browser</div>
        <ul class="pricing-features">
          <li class="incl" data-i18n="start.cloud.f1">No installation needed</li>
          <li class="incl" data-i18n="start.cloud.f2">Access from any device</li>
          <li class="incl" data-i18n="start.cloud.f3">Automatic backups</li>
          <li class="incl" data-i18n="start.cloud.f4">REST API for developers</li>
          <li class="incl" data-i18n="start.cloud.f5">Remote MCP endpoint</li>
        </ul>
        <a href="https://stellar-memory.com/docs/cloud/" target="_blank" rel="noopener" class="pricing-cta" data-i18n="start.cloud.cta">Coming Soon</a>
      </div>
    </div>
  </div>
</section>
```

CSS 변경 사항: 기존 `.pricing-*` 클래스를 그대로 재활용하므로 CSS 수정 불필요.

#### F4-06. i18n 번역 업데이트

**파일**: `landing/index.html`
**액션**: MODIFY (JavaScript T 객체, lines 1572-1752)

각 언어에서 삭제할 키:
```
"nav.pricing"
"pricing.title"
"pricing.subtitle"
"pricing.free.desc"
"pricing.pro.desc"
"pricing.promax.desc"
"pricing.cta.free"
"pricing.cta.subscribe"
```

각 언어에 추가할 키:

**English (en)**:
```javascript
"nav.getstarted": "Get Started",
"hero.badge": "100% Free & Open Source",
"hero.subtitle": "AI remembers you",
"hero.desc": "Give any AI the ability to remember. Free forever, no programming required. Install on your computer in 30 seconds, or use our cloud service.",
"hero.cta.start": "Get Started Free",
"start.label": "Get Started",
"start.title": "Choose how to use Stellar Memory",
"start.subtitle": "Both options are 100% free. Choose what works best for you.",
"start.local.badge": "Recommended",
"start.local.title": "On Your Computer",
"start.local.price": "Free",
"start.local.desc": "Install and run locally",
"start.local.f1": "100% private — data stays on your PC",
"start.local.f2": "Works offline — no internet needed",
"start.local.f3": "Unlimited memories & agents",
"start.local.f4": "Auto-connects to Claude & Cursor",
"start.local.f5": "30-second setup",
"start.local.cta": "Download Installer",
"start.cloud.title": "In the Cloud",
"start.cloud.price": "Free",
"start.cloud.desc": "Use from any browser",
"start.cloud.f1": "No installation needed",
"start.cloud.f2": "Access from any device",
"start.cloud.f3": "Automatic backups",
"start.cloud.f4": "REST API for developers",
"start.cloud.f5": "Remote MCP endpoint",
"start.cloud.cta": "Coming Soon",
```

**Korean (ko)**:
```javascript
"nav.getstarted": "시작하기",
"hero.badge": "100% 무료 & 오픈소스",
"hero.subtitle": "AI가 당신을 기억합니다",
"hero.desc": "어떤 AI에든 기억 능력을 부여하세요. 영구 무료, 프로그래밍 불필요. 30초 설치 또는 클라우드에서 바로 사용.",
"hero.cta.start": "무료로 시작하기",
"start.label": "시작하기",
"start.title": "사용 방법을 선택하세요",
"start.subtitle": "두 가지 모두 100% 무료입니다. 원하는 방법을 선택하세요.",
"start.local.badge": "추천",
"start.local.title": "내 컴퓨터에서",
"start.local.price": "무료",
"start.local.desc": "로컬에서 설치하고 실행",
"start.local.f1": "100% 프라이버시 — 데이터가 내 PC에 저장",
"start.local.f2": "오프라인 사용 가능 — 인터넷 불필요",
"start.local.f3": "무제한 기억 & 에이전트",
"start.local.f4": "Claude & Cursor 자동 연결",
"start.local.f5": "30초 설정",
"start.local.cta": "설치 파일 다운로드",
"start.cloud.title": "클라우드에서",
"start.cloud.price": "무료",
"start.cloud.desc": "브라우저에서 바로 사용",
"start.cloud.f1": "설치 불필요",
"start.cloud.f2": "어디서든 접근 가능",
"start.cloud.f3": "자동 백업",
"start.cloud.f4": "개발자용 REST API",
"start.cloud.f5": "원격 MCP 엔드포인트",
"start.cloud.cta": "준비 중",
```

**Chinese (zh)**:
```javascript
"nav.getstarted": "开始使用",
"hero.badge": "100% 免费 & 开源",
"hero.subtitle": "AI记住你",
"hero.desc": "赋予任何AI记忆能力。永久免费，无需编程。30秒安装到电脑，或使用云服务。",
"hero.cta.start": "免费开始",
"start.label": "开始使用",
"start.title": "选择使用方式",
"start.subtitle": "两种方式都是100%免费。选择最适合您的。",
"start.local.badge": "推荐",
"start.local.title": "在你的电脑上",
"start.local.price": "免费",
"start.local.desc": "本地安装运行",
"start.local.f1": "100%隐私 — 数据存储在你的电脑",
"start.local.f2": "离线使用 — 无需网络",
"start.local.f3": "无限记忆和代理",
"start.local.f4": "自动连接Claude和Cursor",
"start.local.f5": "30秒安装",
"start.local.cta": "下载安装程序",
"start.cloud.title": "在云端",
"start.cloud.price": "免费",
"start.cloud.desc": "从任何浏览器使用",
"start.cloud.f1": "无需安装",
"start.cloud.f2": "任何设备都能访问",
"start.cloud.f3": "自动备份",
"start.cloud.f4": "开发者REST API",
"start.cloud.f5": "远程MCP端点",
"start.cloud.cta": "即将推出",
```

**Spanish (es)**:
```javascript
"nav.getstarted": "Empezar",
"hero.badge": "100% Gratis y Open Source",
"hero.subtitle": "La IA te recuerda",
"hero.desc": "Dale a cualquier IA la capacidad de recordar. Gratis para siempre, sin programación. Instala en 30 segundos o usa nuestro servicio en la nube.",
"hero.cta.start": "Empezar Gratis",
"start.label": "Empezar",
"start.title": "Elige cómo usar Stellar Memory",
"start.subtitle": "Ambas opciones son 100% gratuitas. Elige lo que funcione mejor para ti.",
"start.local.badge": "Recomendado",
"start.local.title": "En tu computadora",
"start.local.price": "Gratis",
"start.local.desc": "Instalar y ejecutar localmente",
"start.local.f1": "100% privado — datos en tu PC",
"start.local.f2": "Funciona sin internet",
"start.local.f3": "Memorias y agentes ilimitados",
"start.local.f4": "Auto-conecta con Claude y Cursor",
"start.local.f5": "Configuración en 30 segundos",
"start.local.cta": "Descargar Instalador",
"start.cloud.title": "En la nube",
"start.cloud.price": "Gratis",
"start.cloud.desc": "Usar desde cualquier navegador",
"start.cloud.f1": "Sin instalación",
"start.cloud.f2": "Acceso desde cualquier dispositivo",
"start.cloud.f3": "Copias de seguridad automáticas",
"start.cloud.f4": "REST API para desarrolladores",
"start.cloud.f5": "Endpoint MCP remoto",
"start.cloud.cta": "Próximamente",
```

**Japanese (ja)**:
```javascript
"nav.getstarted": "はじめる",
"hero.badge": "100% 無料 & オープンソース",
"hero.subtitle": "AIがあなたを覚えます",
"hero.desc": "あらゆるAIに記憶能力を。永久無料、プログラミング不要。30秒でインストール、またはクラウドで利用。",
"hero.cta.start": "無料で始める",
"start.label": "はじめる",
"start.title": "使い方を選んでください",
"start.subtitle": "どちらも100%無料です。最適な方法をお選びください。",
"start.local.badge": "おすすめ",
"start.local.title": "あなたのPCで",
"start.local.price": "無料",
"start.local.desc": "ローカルにインストールして実行",
"start.local.f1": "100%プライバシー — データはPCに保存",
"start.local.f2": "オフライン動作 — ネット不要",
"start.local.f3": "無制限のメモリ＆エージェント",
"start.local.f4": "Claude＆Cursorに自動接続",
"start.local.f5": "30秒セットアップ",
"start.local.cta": "インストーラーをダウンロード",
"start.cloud.title": "クラウドで",
"start.cloud.price": "無料",
"start.cloud.desc": "ブラウザから利用",
"start.cloud.f1": "インストール不要",
"start.cloud.f2": "どのデバイスからもアクセス",
"start.cloud.f3": "自動バックアップ",
"start.cloud.f4": "開発者向けREST API",
"start.cloud.f5": "リモートMCPエンドポイント",
"start.cloud.cta": "近日公開",
```

---

### F5. README 및 문서 개편

#### F5-01. README.md 전면 재작성

**파일**: `README.md`
**액션**: REWRITE

```markdown
# Stellar Memory

> Give your AI the ability to remember. Free & open-source.

[![PyPI](https://img.shields.io/pypi/v/stellar-memory)](https://pypi.org/project/stellar-memory/)
[![Tests](https://img.shields.io/github/actions/workflow/status/sangjun0000/stellar-memory/ci.yml?label=tests)](https://github.com/sangjun0000/stellar-memory/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What is Stellar Memory?

Stellar Memory gives any AI the ability to remember things across conversations.
Once your AI learns something about you, it remembers it next time — just like a person.

**No programming required.** Works with Claude Desktop, Cursor, and any MCP-compatible AI.

## Get Started (2 options)

### Option 1: Install on your computer (Recommended)

**Windows:**
1. Download [`stellar-memory-setup.bat`](https://github.com/sangjun0000/stellar-memory/releases/latest)
2. Double-click to run
3. Restart Claude Desktop or Cursor
4. Done! Try saying: "Remember my name is ___"

**macOS / Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/sangjun0000/stellar-memory/main/stellar-memory-setup.sh | bash
```

**Or if you have Python:**
```bash
pip install stellar-memory[mcp]
stellar-memory setup
```

### Option 2: Use in the cloud

Cloud service coming soon. You'll be able to use Stellar Memory from any browser without installing anything.

For now, developers can use the REST API — see [API docs](https://stellar-memory.com/docs/api-reference/).

## How it works

```
You: "My favorite color is blue. Remember that."
AI:  "Got it! I'll remember that your favorite color is blue."

... next conversation ...

You: "What's my favorite color?"
AI:  "Your favorite color is blue!"
```

Stellar Memory organizes memories like a solar system:
- **Core** — Most important, always remembered
- **Inner** — Important, frequently accessed
- **Outer** — Regular memories
- **Belt** — Less important
- **Cloud** — Rarely accessed, may fade

## For Developers

<details>
<summary>Click to expand developer documentation</summary>

### Python Library

```python
from stellar_memory import StellarMemory

memory = StellarMemory()
memory.store("User prefers dark mode", importance=0.8)
results = memory.recall("user preferences")
memory.stop()
```

### Installation Options

```bash
pip install stellar-memory          # Core library
pip install stellar-memory[mcp]     # With MCP server
pip install stellar-memory[server]  # With REST API
pip install stellar-memory[full]    # Everything
```

### Key Features

- **5-Zone Hierarchy** — Core, Inner, Outer, Belt, Cloud
- **Adaptive Decay** — Memories naturally fade like human memory
- **Emotion Engine** — 6-dimensional emotion vectors
- **Self-Learning** — Optimizes based on usage patterns
- **MCP Server** — Claude Code, Cursor integration
- **REST API** — Full HTTP API with Swagger docs
- **Vector Search** — Semantic similarity matching

### Requirements

Python 3.10+

### Documentation

- [Full Documentation](https://stellar-memory.com/docs/)
- [API Reference](https://stellar-memory.com/docs/api-reference/)
- [Examples](https://github.com/sangjun0000/stellar-memory/tree/main/examples)

</details>

## License

MIT License — free to use, modify, and distribute.
```

#### F5-02. smithery.yaml 업데이트

**파일**: `smithery.yaml`
**액션**: MODIFY (line 2)

```yaml
# BEFORE
description: "Celestial-structure-based AI memory management. Give any AI human-like memory with 5 orbital zones, emotion engine, and adaptive decay."

# AFTER
description: "Free AI memory system. Give any AI the ability to remember across conversations. 100% free, open-source, no programming required."
```

`tags`에 추가:
```yaml
tags:
  - ai-memory
  - llm
  - mcp
  - celestial
  - context-management
  - emotion-ai
  - memory-management
  - free        # 추가
  - open-source # 추가
```

---

## 3. File Change Summary

| # | File | Action | Feature | Changes |
|---|------|--------|---------|---------|
| 1 | `stellar_memory/billing/tiers.py` | MODIFY | F1 | 모든 티어 제한 무제한으로 변경 |
| 2 | `fly.toml` | MODIFY | F1 | BILLING_ENABLED=false |
| 3 | `landing/index.html` | MODIFY | F1,F4 | Schema.org, meta, nav, hero, pricing→get-started, i18n |
| 4 | `stellar-memory-setup.bat` | CREATE | F2 | Windows 1클릭 설치 스크립트 |
| 5 | `stellar-memory-setup.sh` | CREATE | F2 | macOS/Linux 1클릭 설치 스크립트 |
| 6 | `stellar_memory/cli.py` | MODIFY | F2 | setup/start/status 명령 추가, quickstart 간소화 |
| 7 | `README.md` | REWRITE | F5 | 비개발자 친화적 재작성 |
| 8 | `smithery.yaml` | MODIFY | F5 | description 업데이트, 태그 추가 |

**총 변경**: 5 파일 수정 + 2 파일 신규 + 1 파일 재작성 = 8 파일

---

## 4. Implementation Order

| 순서 | 작업 | 파일 | 의존성 |
|:----:|------|------|--------|
| 1 | F1: tiers.py 무제한 변경 | `billing/tiers.py` | 없음 |
| 2 | F1: fly.toml 빌링 비활성화 | `fly.toml` | 없음 |
| 3 | F4: landing page 개편 (meta, nav, hero, pricing→get-started, Schema.org, i18n) | `landing/index.html` | F1 완료 |
| 4 | F2: 설치 스크립트 생성 | `setup.bat`, `setup.sh` | 없음 |
| 5 | F2: CLI setup/start 명령 추가 + quickstart 간소화 | `cli.py` | 없음 |
| 6 | F5: README 재작성 | `README.md` | F2 완료 (설치 방법 확정 후) |
| 7 | F5: smithery.yaml 업데이트 | `smithery.yaml` | 없음 |

---

## 5. Design Checklist (Gap Analysis 기준)

### F1. 수익화 비활성화 (7 items)
- [ ] F1-01: tiers.py free.max_memories = -1
- [ ] F1-01: tiers.py free.max_agents = -1
- [ ] F1-01: tiers.py free.max_api_keys = -1
- [ ] F1-01: tiers.py 전 티어 rate_limit 통일 (120)
- [ ] F1-02: fly.toml BILLING_ENABLED = false
- [ ] F1-03: Schema.org offers → 단일 Free Offer
- [ ] F1-04: config.py BillingConfig.enabled = False 확인 (변경 불필요)

### F2. 로컬 모드 간소화 (8 items)
- [ ] F2-01: stellar-memory-setup.bat 생성
- [ ] F2-01: bat - Python 확인 로직
- [ ] F2-01: bat - pip install 실행
- [ ] F2-01: bat - stellar-memory setup 호출
- [ ] F2-02: stellar-memory-setup.sh 생성
- [ ] F2-03: cli.py setup 명령 추가
- [ ] F2-03: cli.py start 명령 추가
- [ ] F2-04: quickstart 간소화 (2개 선택지)

### F3. 클라우드 모드 안내 (2 items)
- [ ] F3-01: 클라우드 카드에 "Coming Soon" CTA
- [ ] F3-02: 클라우드 카드 기능 목록 (5개)

### F4. 랜딩 페이지 개편 (13 items)
- [ ] F4-01: meta description 변경
- [ ] F4-01: og:title 변경
- [ ] F4-01: og:description 변경
- [ ] F4-01: twitter:title 변경
- [ ] F4-01: twitter:description 변경
- [ ] F4-02: page title 변경
- [ ] F4-03: nav "Pricing" → "Get Started" 변경
- [ ] F4-04: hero badge 텍스트 변경
- [ ] F4-04: hero subtitle 변경
- [ ] F4-04: hero desc 변경
- [ ] F4-04: hero CTA 버튼 변경 (Get Started Free)
- [ ] F4-04: pip install 바 제거
- [ ] F4-05: pricing 섹션 → get-started 섹션 교체 (로컬/클라우드 2카드)

### F4-06. i18n (25 items — 5 languages x 5 key groups)
- [ ] en: nav + hero + start 키 업데이트
- [ ] ko: nav + hero + start 키 업데이트
- [ ] zh: nav + hero + start 키 업데이트
- [ ] es: nav + hero + start 키 업데이트
- [ ] ja: nav + hero + start 키 업데이트

### F5. 문서 개편 (3 items)
- [ ] F5-01: README.md 비개발자 친화적 재작성
- [ ] F5-02: smithery.yaml description 업데이트
- [ ] F5-02: smithery.yaml tags에 free, open-source 추가

**Total Design Items: 58**

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-20 | Initial draft | sangjun0000 |
