# landing-quickguide Planning Document

> **Summary**: Landing page UX overhaul — replace GitHub-redirect download with in-page quick guide, add "Who is this for?" section, and provide AI auto-connect wizard
>
> **Project**: stellar-memory
> **Version**: 2.0.0
> **Author**: sangjun0000
> **Date**: 2026-02-20
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

The current landing page has three critical UX problems for non-programmers:

1. **"Download Installer" links to GitHub Releases** — Users click the golden CTA and land on a GitHub releases page full of `.bat`/`.sh` files and commit hashes. Non-technical users don't know what to do.
2. **No explanation of WHO needs Stellar Memory or WHY** — The site explains features (5-zone orbit, self-learning, multimodal) but never answers "Is this for me?" in plain language.
3. **Quick Start section shows Python code** — The `quickstart.py` code block is meaningless to anyone who doesn't code. There is no guided flow that takes users from "I'm interested" to "my AI now has memory" without touching GitHub or a terminal.

### 1.2 Background

Stellar Memory targets **all AI users**, not just developers. The site says "No programming required" but every actionable path (Download, Quick Start, PyPI) requires programming knowledge. This disconnect loses the majority of potential users at the first click.

### 1.3 Related Documents

- Previous feature: `docs/archive/2026-02/free-access-overhaul/`
- Previous feature: `docs/archive/2026-02/website-redesign/`
- Landing page: `landing/index.html`

---

## 2. Scope

### 2.1 In Scope

- [ ] F1: **"Who Is This For?" section** — Persona-based use cases explaining why different people need AI memory
- [ ] F2: **In-page Quick Guide** — Step-by-step interactive wizard (no GitHub redirect) that guides users to install and connect to their AI
- [ ] F3: **AI Auto-Connect selector** — User picks their AI tool (Claude, ChatGPT, Cursor, etc.) and gets tailored setup instructions
- [ ] F4: **Remove/replace GitHub-dependent CTAs** — "Download Installer" should trigger in-page guide, not link to GitHub Releases
- [ ] F5: **i18n updates** — All new text translated to 5 languages (EN/KO/ZH/ES/JA)

### 2.2 Out of Scope

- Backend/server changes (this is a static landing page update)
- Actual auto-installer download hosting (keep using GitHub Releases as the underlying source, but wrap it in a guided experience)
- Cloud service implementation (still "Coming Soon")

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | Add "Who Is This For?" section with 3-4 persona cards (e.g., "Students", "Professionals", "Creators", "Developers") each explaining the benefit in one sentence | High | Pending |
| FR-02 | Replace "Download Installer" CTA with in-page guided setup wizard that opens on click | High | Pending |
| FR-03 | Add AI tool selector (Step 1 of wizard): Claude Desktop, Cursor, ChatGPT, Other — each showing tailored instructions | High | Pending |
| FR-04 | Add OS auto-detect (Step 2): detect Windows/macOS/Linux and show the correct install command or download link | High | Pending |
| FR-05 | Show copy-pasteable setup commands in the guide (not Python code — just terminal/config steps) | High | Pending |
| FR-06 | Replace quickstart.py code with a visual "How It Works" that non-programmers can understand | Medium | Pending |
| FR-07 | Add all new i18n keys for 5 languages | Medium | Pending |
| FR-08 | Keep "View on GitHub" as secondary link for developers, but remove it as primary path | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Accessibility | All new elements keyboard-navigable | Manual testing |
| Performance | No additional JS libraries; vanilla JS only | Code review |
| Mobile | Wizard works on mobile viewports | Responsive testing |
| i18n | All visible text has data-i18n attributes | Grep audit |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] A non-programmer can go from landing page to "AI has memory" without visiting GitHub
- [ ] The page clearly explains who needs Stellar Memory and why
- [ ] AI tool selector shows correct setup for at least 3 AI tools (Claude, Cursor, ChatGPT)
- [ ] OS auto-detect shows correct installer/command
- [ ] All text translated to 5 languages
- [ ] Deployed to gh-pages

### 4.2 Quality Criteria

- [ ] Zero broken links
- [ ] Responsive on mobile (375px+)
- [ ] Page load time unaffected (no new external dependencies)

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Wizard UX too complex for single HTML page | Medium | Medium | Keep to max 3 steps; use show/hide, no multi-page |
| OS detection unreliable | Low | Low | Provide manual OS selection as fallback |
| i18n key explosion | Medium | Medium | Reuse existing pattern; group by section |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure (`components/`, `lib/`, `types/`) | Static sites, portfolios, landing pages | **Yes** |
| Dynamic | Feature-based modules, BaaS integration | Web apps with backend | |
| Enterprise | Strict layer separation, DI, microservices | High-traffic systems | |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| Framework | Single HTML file (current) | Single HTML file | Matches existing architecture; no build step |
| JS approach | Vanilla JS / React / Alpine | Vanilla JS | No external deps; current pattern |
| Wizard pattern | Modal / Inline accordion / Multi-step | Inline accordion in get-started section | Least disruptive; mobile-friendly |
| OS detection | `navigator.platform` / `navigator.userAgentData` | `navigator.userAgentData` with fallback | Modern API with legacy fallback |

---

## 7. Detailed Design Preview

### 7.1 New Section: "Who Is This For?" (after Features, before How It Works)

```
┌─────────────────────────────────────────────────────────┐
│  WHO IS THIS FOR?                                       │
│  "AI memory isn't just for engineers."                  │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Student  │ │  Writer  │ │ Business │ │Developer │   │
│  │          │ │          │ │          │ │          │   │
│  │ "Your AI │ │ "Your AI │ │ "Your AI │ │ "Add     │   │
│  │  tutor   │ │  knows   │ │  remembers│ │  memory  │   │
│  │  remembers│ │  your    │ │  your    │ │  to any  │   │
│  │  what you│ │  writing │ │  clients │ │  LLM in  │   │
│  │  studied"│ │  style"  │ │  & deals"│ │  3 lines"│   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 7.2 New Get Started: In-Page Quick Guide with AI Selector

Replace current "Download Installer → GitHub" with an interactive 3-step wizard:

```
┌─────────────────────────────────────────────────────────┐
│  GET STARTED                                            │
│                                                         │
│  Step 1: Which AI do you use?                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Claude  │ │  Cursor  │ │ ChatGPT  │ │  Other   │   │
│  │ Desktop  │ │          │ │          │ │          │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                         │
│  Step 2: Your system (auto-detected: Windows)          │
│  [Windows ●] [macOS ○] [Linux ○]                       │
│                                                         │
│  Step 3: Follow these 2 steps                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1. Download & run the installer:                │   │
│  │    [Download stellar-memory-setup.bat]  (button) │   │
│  │                                                  │   │
│  │ 2. Restart Claude Desktop — done!               │   │
│  │    Stellar Memory is now connected.             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [Advanced: View on GitHub →]                          │
└─────────────────────────────────────────────────────────┘
```

The instructions in Step 3 change dynamically based on selections:
- **Claude Desktop + Windows** → Download .bat, restart Claude
- **Claude Desktop + macOS/Linux** → Download .sh, restart Claude
- **Cursor + any OS** → Show MCP config JSON to paste
- **ChatGPT + any OS** → Show Python middleware snippet
- **Other** → Show generic pip install + MCP instructions

---

## 8. Next Steps

1. [ ] Write design document (`landing-quickguide.design.md`)
2. [ ] Implement changes in `landing/index.html`
3. [ ] Deploy via `deploy.sh`

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-20 | Initial draft | sangjun0000 |
