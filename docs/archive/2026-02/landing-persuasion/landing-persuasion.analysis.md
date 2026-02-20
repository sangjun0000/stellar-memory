# landing-persuasion Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: stellar-memory
> **Analyst**: gap-detector
> **Date**: 2026-02-20
> **Design Doc**: [landing-persuasion.design.md](../02-design/features/landing-persuasion.design.md)
> **Implementation**: [landing/index.html](../../landing/index.html)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Verify that the landing page persuasion-focused redesign described in the design document has been fully implemented in `landing/index.html`. The design specifies 10 concrete requirements covering section reordering, new content, i18n, CSS, JavaScript cleanup, and navigation changes.

### 1.2 Analysis Scope

- **Design Document**: `docs/02-design/features/landing-persuasion.design.md`
- **Implementation Path**: `landing/index.html`
- **Analysis Date**: 2026-02-20

---

## 2. Gap Analysis (Design vs Implementation)

### 2.1 Section Order (Requirement 1)

| Design Order | Implementation | Line | Status |
|-------------|----------------|------|--------|
| 1. Hero | `<section id="hero">` | L1511 | Match |
| 2. Pain Point (new) | `<section id="pain-point">` | L1580 | Match |
| 3. Use Cases | `<section id="use-cases">` | L1626 | Match |
| 4. How It Works (replaced) | `<section id="how-it-works">` | L1673 | Match |
| 5. Features (moved) | `<section id="features">` | L1730 | Match |
| 6. Ecosystem | `<section id="ecosystem">` | L1795 | Match |
| 7. Get Started | `<section id="get-started">` | L1866 | Match |

**Result**: 7/7 sections in correct order. **Score: 10/10**

### 2.2 Pain Point Section (Requirement 2)

| Design Element | Implementation | Status |
|---------------|----------------|--------|
| `<section id="pain-point">` | Present at L1580 | Match |
| section-label `data-i18n="pain.label"` | Present at L1583 | Match |
| section-title `data-i18n="pain.title"` | Present at L1584 | Match |
| section-sub `data-i18n="pain.subtitle"` | Present at L1585 | Match |
| `.pain-grid` with 3 cards | Present at L1588 (3 `.pain-card` children) | Match |
| Card 1: repeat (icon, title, chat bubbles, label) | L1589-1597 -- all elements present | Match |
| Card 2: forget (icon, title, chat bubbles) | L1599-1606 -- all elements present | Match |
| Card 3: context (icon, title, chat bubbles, label) | L1608-1616 -- all elements present | Match |
| `.pain-solution` text | Present at L1619 | Match |

**Result**: All Pain Point elements implemented. **Score: 10/10**

### 2.3 How It Works Replacement (Requirement 3)

| Design Element | Implementation | Status |
|---------------|----------------|--------|
| 3-step visual layout `.how-steps-new` | Present at L1681 with 3 `.how-step-card` | Match |
| Step 1: Connect (num, visual, title, desc) | L1682-1689 | Match |
| Step 2: Auto-remember (num, visual, title, desc) | L1691-1698 | Match |
| Step 3: Next-chat (num, visual, title, desc) | L1700-1707 | Match |
| Before/After demo `.how-demo` | Present at L1710 | Match |
| `.how-demo-before` with chat bubbles | L1711-1717 | Match |
| `.how-demo-after` with chat bubbles | L1718-1722 | Match |
| Old code example HTML removed | No code example HTML found | Match |

**Result**: How It Works fully replaced. **Score: 10/10**

### 2.4 Features Section Position (Requirement 4)

| Design Spec | Implementation | Status |
|------------|----------------|--------|
| Features after How It Works | `#how-it-works` at L1673, `#features` at L1730 | Match |

**Result**: Features correctly positioned. **Score: 10/10**

### 2.5 Navigation Links (Requirement 5)

| Design Nav | Implementation | Line | Status |
|-----------|----------------|------|--------|
| "Why?" -> `#pain-point` | `<a href="#pain-point" data-i18n="nav.why">Why?</a>` | L1478 | Match |
| "Use Cases" -> `#use-cases` | `<a href="#use-cases" data-i18n="nav.usecases">Use Cases</a>` | L1479 | Match |
| "How It Works" -> `#how-it-works` | `<a href="#how-it-works" data-i18n="nav.howitworks">How It Works</a>` | L1480 | Match |
| "Get Started" -> `#get-started` | `<a href="#get-started" data-i18n="nav.getstarted">Get Started</a>` | L1481 | Match |

**Result**: All navigation links correct. **Score: 10/10**

### 2.6 Hero CTA Buttons (Requirement 6)

| Design Spec | Implementation | Line | Status |
|------------|----------------|------|--------|
| Primary: "How does it work?" -> `#how-it-works` | `<a href="#how-it-works" class="btn-primary">` with `data-i18n="hero.cta.start"` text "How does it work?" | L1526-1529 | Match |
| Secondary: "Get Started Free" -> `#get-started` | `<a href="#get-started" class="btn-secondary">` with `data-i18n="hero.cta.who"` text "Get Started Free" | L1530-1533 | Match |

**Result**: Hero CTAs correctly updated. **Score: 10/10**

### 2.7 i18n Keys (Requirement 7)

Design requires `pain.*` (15 keys) and `how.*` (9 keys) for 5 languages.

#### 2.7.1 Per-Language Status

| Language | pain.* (15 keys) | how.* (9 keys) | nav.why | nav.howitworks | hero.cta updated | Status |
|----------|:-----------------:|:---------------:|:-------:|:--------------:|:----------------:|--------|
| en | 15/15 | 9/9 | Present | Present | Correct | Full Match |
| ko | 15/15 | 9/9 | Present | Present | Correct | Full Match |
| zh | 15/15 | 9/9 | Present | Present | Correct | Full Match |
| **es** | **0/15** | **0/9** | Present | Present | Correct | **MISSING** |
| **ja** | 15/15 | 9/9 | **MISSING** | **MISSING** | **Swapped** | **PARTIAL** |

#### 2.7.2 Spanish (es) -- Critical Gap

The Spanish locale is **completely missing** all new `pain.*` and `how.*` keys. It still contains old keys from the previous design:

| Issue | Details | Lines |
|-------|---------|-------|
| Missing pain.* keys (all 15) | No `pain.label` through `pain.solution` in es | -- |
| Missing how.label | Not present in es | -- |
| Missing how.s1-s3 keys (6) | Not present in es | -- |
| Missing how.before.label, how.after.label | Not present in es | -- |
| Old keys still present: `how.store` | L2315 | Stale |
| Old keys still present: `how.store.desc` | L2316 | Stale |
| Old keys still present: `how.recall` | L2317 | Stale |
| Old keys still present: `how.recall.desc` | L2318 | Stale |
| Old keys still present: `how.title` (old text) | L2313 | Stale |
| Old keys still present: `how.subtitle` (old text) | L2314 | Stale |

**Total missing in es**: 24 keys (15 pain + 9 how)

#### 2.7.3 Japanese (ja) -- Partial Gap

| Issue | Details | Lines |
|-------|---------|-------|
| Missing `nav.why` | Not present in ja locale | -- |
| Missing `nav.howitworks` | Not present in ja locale | -- |
| Stale `nav.features` present | L2367 -- old nav key not in new design | Stale |
| `hero.cta.start` = wrong value | L2364: shows "Free to start" instead of "How does it work?" equivalent | Incorrect |
| `hero.cta.who` = wrong value | L2365: shows "Who is this for?" instead of "Get Started Free" equivalent | Incorrect |

#### 2.7.4 Additional i18n Keys (Added in Implementation, Not in Design)

The implementation adds Before/After demo bubble text keys not specified in the design document:

| Key | en | ko | zh | es | ja |
|-----|:--:|:--:|:--:|:--:|:--:|
| how.before.user1 | Present | Present | Missing | Missing | Missing |
| how.before.ai1 | Present | Present | Missing | Missing | Missing |
| how.before.user2 | Present | Present | Missing | Missing | Missing |
| how.after.user1 | Present | Present | Missing | Missing | Missing |
| how.after.ai1 | Present | Present | Missing | Missing | Missing |

These 5 extra keys are in HTML `data-i18n` attributes (L1713-1721) but were not listed in the design's i18n key inventory. They are present only for en and ko, falling back to English for zh/es/ja.

**i18n Score**: 3 of 5 languages fully complete = **6/10**

### 2.8 setStep() JS Function Removed (Requirement 8)

| Design Spec | Implementation | Status |
|------------|----------------|--------|
| Remove `setStep()` function | Dead code remains at L2527-2537 | **Not Removed** |

The code at L2525-2537 includes a comment "step switcher removed -- now static 3-step layout" but the JavaScript code block that queries `.how-step` elements and calls `setStep(i)` is still present. Since `.how-step` elements no longer exist in the HTML, this code is harmless dead code -- but the design explicitly calls for its removal.

```javascript
// Line 2525-2537 (dead code, should be removed)
document.querySelectorAll('.how-step').forEach(function(el, i) {
  el.addEventListener('click', function() {
    clearInterval(autoCycle);
    setStep(i);
    currentStep = i;
    autoCycle = setInterval(function() {
      currentStep = (currentStep + 1) % 2;
      setStep(currentStep);
    }, 4000);
  });
});
```

**Score: 5/10** (dead code, no functional impact but explicitly required cleanup not done)

### 2.9 New CSS Added (Requirement 9)

| CSS Class | Design Spec | Implementation | Line | Status |
|-----------|------------|----------------|------|--------|
| `.pain-grid` | 3-column grid, 24px gap | Present, matches design | L699-704 | Match |
| `.pain-card` | bg-card, border, radius, padding | Present, matches design | L705-711 | Match |
| `.pain-icon` | 2.5rem, 16px margin-bottom | Present, matches design | L712 | Match |
| `.pain-chat` | text-align left, 16px margin-top | Present, matches design | L714 | Match |
| `.chat-bubble` | 12px radius, 8px margin, 0.85rem | Present, matches design | L715-721 | Match |
| `.chat-bubble.user` | blue bg, white text | Present, matches design | L722-727 | Match |
| `.chat-bubble.ai` | surface bg, secondary text | Present, matches design | L728-733 | Match |
| `.chat-label` | center, muted, italic | Present, matches design | L734-740 | Match |
| `.pain-solution` | center, gold, 600 weight | Present, matches design | L741-747 | Match |
| `.how-steps-new` | 3-column grid, 32px gap | Present, matches design | L750-755 | Match |
| `.how-step-card` | center, 32px 24px padding | Present, matches design | L756-758 | Match |
| `.how-step-num` | 48px circle, gold bg | Present, matches design | L760-768 | Match |
| `.how-step-visual` | 80px height, flex center | Present, matches design | L770-776 | Match |
| `.how-demo` | 2-column grid, 800px max | Present, matches design | L781-789 | Match |
| `.how-demo-before` | card bg, 0.6 opacity | Present, matches design | L790-796 | Match |
| `.how-demo-after` | gold border, glow shadow | Present, matches design | L797-800 | Match |
| `.demo-label` | 600 weight, 16px margin | Present, matches design | L801-807 | Match |
| Responsive `.pain-grid` (mobile) | 1fr at 900px | L1309 | Match |
| Responsive `.how-steps-new` (mobile) | 1fr at 900px | L1310 | Match |
| Responsive `.how-demo` (mobile) | 1fr at 900px | L1311 | Match |

Note: Design specifies `@media (max-width: 768px)` for `.pain-grid` and `.how-steps-new`, but implementation uses `@media (max-width: 900px)`. This is a minor deviation -- the implementation applies the mobile layout at a wider breakpoint.

**Score: 9/10** (breakpoint 900px vs design's 768px -- minor, arguably better UX)

### 2.10 Old code-window/code-block CSS Removed (Requirement 10)

| Design Spec | Implementation | Status |
|------------|----------------|--------|
| Remove `.code-window` CSS | Not found anywhere in file | Match |
| Remove `.code-block` CSS | Not found anywhere in file | Match |

**Score: 10/10**

---

## 3. Match Rate Summary

### 3.1 Per-Requirement Scores

| # | Requirement | Score | Status |
|---|------------|:-----:|:------:|
| 1 | Section order | 10/10 | Match |
| 2 | Pain Point section (3 cards + bubbles + solution) | 10/10 | Match |
| 3 | How It Works replaced (3-step + before/after) | 10/10 | Match |
| 4 | Features section moved after How It Works | 10/10 | Match |
| 5 | Navigation links updated | 10/10 | Match |
| 6 | Hero CTA changed | 10/10 | Match |
| 7 | i18n keys added for all 5 languages | 6/10 | Partial |
| 8 | setStep() JS function removed | 5/10 | Not Done |
| 9 | New CSS added | 9/10 | Minor Deviation |
| 10 | Old code-window/code-block CSS removed | 10/10 | Match |
| **Total** | | **90/100** | |

### 3.2 Overall Match Rate

```
+---------------------------------------------+
|  Overall Match Rate: 90%                     |
+---------------------------------------------+
|  Match:          7 items (70%)               |
|  Partial:        2 items (20%)               |
|  Not Done:       1 item  (10%)               |
+---------------------------------------------+
```

---

## 4. Differences Found

### 4.1 Missing Features (Design O, Implementation X)

| Item | Design Location | Description | Severity |
|------|-----------------|-------------|----------|
| Spanish (es) pain.* i18n keys | design.md Section 4, L388-400 | All 15 `pain.*` keys missing from es locale | High |
| Spanish (es) how.* i18n keys | design.md Section 4, L396-398 | All 9 new `how.*` keys missing from es locale (old store/recall keys remain) | High |
| Japanese (ja) nav.why key | design.md Section 2, L38-43 | `nav.why` not present in ja locale | Medium |
| Japanese (ja) nav.howitworks key | design.md Section 2, L38-43 | `nav.howitworks` not present in ja locale | Medium |
| setStep() removal | design.md Section 6, L423 | Dead code at L2527-2537 not removed | Low |

### 4.2 Added Features (Design X, Implementation O)

| Item | Implementation Location | Description | Impact |
|------|------------------------|-------------|--------|
| Before/After demo bubble i18n keys | L1713-1716, L1720-1721 | `how.before.user1`, `how.before.ai1`, `how.before.user2`, `how.after.user1`, `how.after.ai1` added beyond design spec | Positive |
| SVG icons in How It Works steps | L1685, L1694, L1703 | Concrete SVG visuals where design had `<svg>...</svg>` placeholder | Positive |

### 4.3 Changed Features (Design != Implementation)

| Item | Design | Implementation | Impact |
|------|--------|----------------|--------|
| Responsive breakpoint for pain-grid/how-steps-new | 768px | 900px (L1309-1311) | Low -- wider breakpoint, arguably better |
| Japanese hero.cta.start | Should be "How does it work?" equivalent | "Free to start" (L2364) | Medium -- wrong CTA text |
| Japanese hero.cta.who | Should be "Get Started Free" equivalent | "Who is this for?" (L2365) | Medium -- wrong CTA text |
| Japanese nav still has `nav.features` | Should be removed | L2367 -- stale key | Low |
| Spanish how.title/how.subtitle | Should be new persuasion text | Old developer-focused text (L2313-2314) | Medium |

---

## 5. Recommended Actions

### 5.1 Immediate (High Priority)

| # | Action | File | Location | Details |
|---|--------|------|----------|---------|
| 1 | Add all `pain.*` keys to Spanish (es) locale | landing/index.html | es i18n block (~L2283) | 15 keys: pain.label through pain.solution |
| 2 | Replace old `how.*` keys with new keys in Spanish (es) locale | landing/index.html | L2313-2318 | Remove how.store/recall, add how.label, how.s1-s3, how.before/after.label (9 keys) |

### 5.2 Short-term (Medium Priority)

| # | Action | File | Location | Details |
|---|--------|------|----------|---------|
| 3 | Add `nav.why` and `nav.howitworks` to Japanese (ja) locale | landing/index.html | ja i18n block (~L2366) | Add missing nav keys, remove stale `nav.features` |
| 4 | Fix Japanese `hero.cta.start` and `hero.cta.who` values | landing/index.html | L2364-2365 | Swap values to match design intent |
| 5 | Remove dead `setStep()` code block | landing/index.html | L2527-2537 | Delete the `.how-step` event listener block |

### 5.3 Optional (Low Priority)

| # | Action | File | Details |
|---|--------|------|---------|
| 6 | Add demo bubble i18n keys to zh/es/ja | landing/index.html | `how.before.user1/ai1/user2`, `how.after.user1/ai1` for 3 languages |
| 7 | Update design document to include demo bubble keys | design.md Section 4 | Add `how.before.user1`, etc. to key inventory |
| 8 | Align responsive breakpoint with design (768px vs 900px) | landing/index.html | L1309-1311 -- or update design to reflect 900px choice |

---

## 6. Design Document Updates Needed

If implementation is accepted as-is for non-gap items:

- [ ] Add `how.before.user1`, `how.before.ai1`, `how.before.user2`, `how.after.user1`, `how.after.ai1` to the i18n key inventory in Section 4
- [ ] Update responsive breakpoint spec from 768px to 900px (if 900px is intentional)

---

## 7. Synchronization Summary

| Language | Action Required | Keys to Add | Keys to Fix | Keys to Remove |
|----------|----------------|:-----------:|:-----------:|:--------------:|
| en | None | 0 | 0 | 0 |
| ko | None | 0 | 0 | 0 |
| zh | Optional (demo bubbles) | 5 | 0 | 0 |
| **es** | **Critical** | **24** | **2** | **4** |
| **ja** | **Required** | **2** | **2** | **1** |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-20 | Initial gap analysis | gap-detector |
