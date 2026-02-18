# Design: Monetization Phase 1

> **Feature**: monetization-phase1
> **Plan Reference**: `docs/01-plan/features/monetization-phase1.plan.md`
> **Created**: 2026-02-18
> **Status**: Draft

---

## 1. Architecture Overview

```
landing/index.html
├── ... (existing sections) ...
├── #integrations section (line ~1768)
├── NEW: #pricing section          ← F1: Pricing Cards
├── <footer> (line ~1860)
└── ...

stellar_memory/
├── mcp_server.py (existing)       ← F2: MCP tools already implemented
└── cli.py (init-mcp command)      ← F2: IDE config generator exists

NEW FILES:
├── smithery.yaml                  ← F2-1: Smithery MCP registry
└── .cursor/mcp.json              ← F2-2: Cursor MCP config
```

## 2. F1: Pricing Section Design

### 2.1 Position in Page

Pricing 섹션은 `#integrations` 섹션과 `<footer>` 사이에 삽입.

```
#integrations → NEW #pricing → <footer>
```

### 2.2 HTML Structure

```html
<section id="pricing">
  <div class="container">
    <div class="section-label">Pricing</div>
    <h2 class="section-title">Simple, transparent pricing</h2>
    <p class="section-sub">
      Start free. Scale when you need to.
    </p>

    <div class="pricing-grid">
      <!-- Free Card -->
      <div class="pricing-card">
        <div class="pricing-tier">Free</div>
        <div class="pricing-price">$0<span>/mo</span></div>
        <div class="pricing-desc">For personal projects</div>
        <ul class="pricing-features">
          <li class="included">5,000 memories</li>
          <li class="included">1 agent</li>
          <li class="included">SQLite storage</li>
          <li class="included">Local MCP server</li>
          <li class="included">CLI interface</li>
          <li class="excluded">Cloud sync</li>
          <li class="excluded">Web dashboard</li>
        </ul>
        <a href="https://pypi.org/project/stellar-memory/" class="pricing-cta">
          Get Started
        </a>
      </div>

      <!-- Pro Card (highlighted) -->
      <div class="pricing-card pricing-popular">
        <div class="pricing-badge">Most Popular</div>
        <div class="pricing-tier">Pro</div>
        <div class="pricing-price">$29<span>/mo</span></div>
        <div class="pricing-desc">For serious builders</div>
        <ul class="pricing-features">
          <li class="included">50,000 memories</li>
          <li class="included">5 agents</li>
          <li class="included">PostgreSQL + pgvector</li>
          <li class="included">Cloud MCP endpoint</li>
          <li class="included">Web dashboard</li>
          <li class="included">Email support</li>
          <li class="excluded">Team sync</li>
        </ul>
        <a href="#" class="pricing-cta pricing-cta-primary">
          Coming Soon
        </a>
      </div>

      <!-- Team Card -->
      <div class="pricing-card">
        <div class="pricing-tier">Team</div>
        <div class="pricing-price">$99<span>/mo</span></div>
        <div class="pricing-desc">For growing teams</div>
        <ul class="pricing-features">
          <li class="included">500,000 memories</li>
          <li class="included">20 agents</li>
          <li class="included">Everything in Pro</li>
          <li class="included">CRDT team sync</li>
          <li class="included">RBAC + audit logs</li>
          <li class="included">Priority support</li>
          <li class="included">SSO</li>
        </ul>
        <a href="#" class="pricing-cta">
          Coming Soon
        </a>
      </div>

      <!-- Enterprise Card -->
      <div class="pricing-card">
        <div class="pricing-tier">Enterprise</div>
        <div class="pricing-price">Custom</div>
        <div class="pricing-desc">For organizations</div>
        <ul class="pricing-features">
          <li class="included">Unlimited memories</li>
          <li class="included">Unlimited agents</li>
          <li class="included">Everything in Team</li>
          <li class="included">On-premise deployment</li>
          <li class="included">Dedicated support</li>
          <li class="included">SLA guarantee</li>
          <li class="included">Custom integrations</li>
        </ul>
        <a href="mailto:contact@stellar-memory.com" class="pricing-cta">
          Contact Us
        </a>
      </div>
    </div>
  </div>
</section>
```

### 2.3 CSS Design Specs

```css
/* Pricing Grid: 4-column on desktop, 2 on tablet, 1 on mobile */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  max-width: 1100px;
  margin: 48px auto 0;
}

/* Card Base */
.pricing-card {
  background: var(--bg-card);          /* #0f2044 */
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: transform 0.2s, border-color 0.2s;
}
.pricing-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255,255,255,0.12);
}

/* Popular Card (Pro) - Gold accent border + glow */
.pricing-popular {
  border-color: var(--accent-gold);   /* #f0b429 */
  box-shadow: 0 0 40px rgba(240,180,41,0.1);
}

/* "Most Popular" Badge */
.pricing-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--accent-gold);
  color: #000;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 4px 16px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Tier Name */
.pricing-tier {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-secondary);       /* #94a3b8 */
  margin-bottom: 8px;
}

/* Price */
.pricing-price {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--text-primary);         /* #f0f4ff */
  line-height: 1;
  margin-bottom: 4px;
}
.pricing-price span {
  font-size: 1rem;
  font-weight: 400;
  color: var(--text-muted);           /* #475569 */
}

/* Description */
.pricing-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 24px;
}

/* Feature List */
.pricing-features {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
  flex: 1;
}
.pricing-features li {
  font-size: 0.85rem;
  padding: 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.pricing-features li.included { color: var(--text-secondary); }
.pricing-features li.excluded { color: var(--text-muted); text-decoration: line-through; opacity: 0.5; }

/* included: gold checkmark, excluded: dim dash */
.pricing-features li.included::before {
  content: "";
  width: 16px; height: 16px;
  background: var(--accent-gold);
  mask: url("data:image/svg+xml,...checkmark...");  /* inline SVG checkmark */
  flex-shrink: 0;
}
.pricing-features li.excluded::before {
  content: "—";
  width: 16px;
  text-align: center;
  flex-shrink: 0;
}

/* CTA Button */
.pricing-cta {
  display: block;
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid rgba(255,255,255,0.15);
  color: var(--text-primary);
  transition: background 0.2s;
}
.pricing-cta:hover {
  background: rgba(255,255,255,0.05);
}

/* Primary CTA (Pro card) - Gold filled */
.pricing-cta-primary {
  background: var(--accent-gold);
  color: #000;
  border-color: var(--accent-gold);
}
.pricing-cta-primary:hover {
  background: var(--accent-glow);     /* #fcd34d */
}

/* Responsive */
@media (max-width: 900px) {
  .pricing-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .pricing-grid { grid-template-columns: 1fr; max-width: 360px; }
}
```

### 2.4 Schema.org SEO Markup

`<head>` 내 기존 JSON-LD에 `offers` 배열 추가:

```json
"offers": [
  {
    "@type": "Offer",
    "name": "Free",
    "price": "0",
    "priceCurrency": "USD",
    "description": "5,000 memories, 1 agent, SQLite, Local MCP"
  },
  {
    "@type": "Offer",
    "name": "Pro",
    "price": "29",
    "priceCurrency": "USD",
    "billingIncrement": "P1M",
    "description": "50,000 memories, 5 agents, PostgreSQL, Cloud MCP, Dashboard"
  },
  {
    "@type": "Offer",
    "name": "Team",
    "price": "99",
    "priceCurrency": "USD",
    "billingIncrement": "P1M",
    "description": "500,000 memories, 20 agents, Team Sync, RBAC, Audit Logs"
  }
]
```

### 2.5 Nav Link Addition

기존 네비게이션에 Pricing 링크 추가:

```html
<a href="#pricing">Pricing</a>
```

위치: Features, Quickstart, Integrations 다음, GitHub 앞.

## 3. F2: MCP Marketplace Registration

### 3.1 Smithery Registry (smithery.yaml)

프로젝트 루트에 `smithery.yaml` 생성:

```yaml
name: stellar-memory
description: "Celestial-structure-based AI memory management. Give any AI human-like memory with 5 orbital zones."
version: "1.0.0"
license: MIT
author: sangjun0000
homepage: https://stellar-memory.com
repository: https://github.com/sangjun0000/stellar-memory

server:
  command: stellar-memory
  args: ["serve-mcp"]

install:
  pip: stellar-memory[mcp]

tools:
  - name: stellar_store
    description: "Store a memory with importance scoring"
  - name: stellar_recall
    description: "Recall relevant memories using semantic search"
  - name: stellar_stats
    description: "Get memory statistics and zone distribution"
  - name: stellar_timeline
    description: "View memory timeline"
  - name: stellar_introspect
    description: "Analyze knowledge state and gaps"
  - name: stellar_reason
    description: "Memory-augmented reasoning"

tags:
  - ai-memory
  - llm
  - mcp
  - celestial
  - context-management

categories:
  - memory
  - ai
```

### 3.2 Cursor MCP Config (.cursor/mcp.json)

프로젝트에 Cursor 예시 설정 파일 생성:

```json
{
  "mcpServers": {
    "stellar-memory": {
      "command": "stellar-memory",
      "args": ["serve-mcp"],
      "env": {}
    }
  }
}
```

### 3.3 MCP Docs Page Update

`docs/mcp/claude-code.md` 및 `docs/mcp/cursor.md`에 설치 가이드 보강:
- pip install 명령어
- init-mcp 자동 설정 사용법
- 수동 설정 방법
- 도구 목록 및 사용 예제

## 4. Implementation Checklist

### F1: Pricing Section
- [ ] F1-1: CSS 스타일 작성 (`.pricing-*` 클래스들)
- [ ] F1-2: HTML 구조 작성 (4개 카드)
- [ ] F1-3: Nav에 Pricing 링크 추가
- [ ] F1-4: Schema.org offers 배열 업데이트
- [ ] F1-5: 반응형 테스트 (desktop/tablet/mobile)
- [ ] F1-6: gh-pages 배포

### F2: MCP Registration
- [ ] F2-1: `smithery.yaml` 생성 (프로젝트 루트)
- [ ] F2-2: `.cursor/mcp.json` 예시 파일 생성
- [ ] F2-3: Smithery 레지스트리에 등록 (smithery.ai)
- [ ] F2-4: MCP 문서 페이지 보강

## 5. File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `landing/index.html` | MODIFY | Pricing CSS + HTML 섹션 + Nav 링크 + Schema.org |
| `smithery.yaml` | CREATE | Smithery MCP 레지스트리 설정 |
| `.cursor/mcp.json` | CREATE | Cursor MCP 설정 예시 |
| `sitemap.xml` (gh-pages) | MODIFY | Pricing 앵커 추가 (optional) |

## 6. Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Pro/Team CTA | "Coming Soon" | Cloud SaaS가 아직 없으므로 |
| Enterprise CTA | "Contact Us" (mailto) | 초기에는 이메일 기반 영업 |
| Free CTA | "Get Started" → PyPI | 즉시 사용 가능한 경로 |
| Pricing 위치 | integrations 뒤, footer 앞 | 기능 소개 후 구매 유도 자연스러운 흐름 |
| 카드 highlight | Pro에 gold border + badge | 가장 높은 전환 기대 플랜 |
