# Landing Page Chrome Extension 소개 — Planning Document

> **Summary**: Stellar Memory 랜딩 페이지에 Chrome Extension 소개 섹션 추가 및 설치 가이드 통합
>
> **Project**: stellar-memory
> **Feature**: landing-chrome-extension
> **Author**: Claude (AI)
> **Date**: 2026-02-21
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

Stellar Memory Chrome Extension이 완성되었으므로, 랜딩 페이지(stellar-memory.com)에 Extension 소개, 기능 설명, 설치 가이드를 추가하여 일반 사용자의 접근성을 극대화한다.

### 1.2 Background

현재 랜딩 페이지는 **개발자 중심**(MCP, pip install, Python SDK)으로 구성되어 있다. Chrome Extension은 **코드 없이 클릭 한 번**으로 설치 가능한 소비자 제품이므로, 비개발자도 쉽게 이해하고 설치할 수 있도록 사이트를 업데이트해야 한다.

### 1.3 현재 랜딩 페이지 구조

```
1. NAVIGATION — 링크: Why?, Use Cases, How It Works, Get Started, GitHub
2. HERO — 제목, 설명, CTA 2개
3. PAIN POINT — 3개 문제 카드 (반복/백지/모르는AI)
4. USE CASES — 4개 페르소나 카드 (학생/작가/비즈니스/개발자)
5. HOW IT WORKS — 3단계 + Before/After 데모
6. FEATURES — 3개 카드 (5-Zone, 자율학습, 멀티모달)
7. ECOSYSTEM — Homunculus + Community 카드
8. GET STARTED — AI 선택 위저드 (Claude/Cursor/ChatGPT/Other)
9. FOOTER — 프로젝트 링크 + 문서 링크 + 배지
10. JAVASCRIPT — i18n (5개 언어: EN/KO/ZH/ES/JA) + 위저드 로직
```

### 1.4 핵심 변경 사항

Chrome Extension을 랜딩 페이지의 **제1 CTA**로 격상:
- 비개발자에게 가장 쉬운 진입점
- "설치만 하면 AI가 나를 기억한다"는 메시지
- Chrome Web Store 링크 (또는 Coming Soon)

---

## 2. Feature Requirements

### FR-01: Chrome Extension 전용 소개 섹션

**위치**: HOW IT WORKS 섹션 바로 다음 (FEATURES 앞)

새로운 `#chrome-extension` 섹션 추가:
- 섹션 제목: "Chrome Extension — Install once, every AI remembers you"
- 3개 AI 로고/아이콘 (ChatGPT, Claude, Gemini) 가로 배치
- 핵심 기능 4개 카드:
  1. **Auto-Capture**: 대화를 자동으로 저장 (MutationObserver)
  2. **Auto-Inject**: 관련 기억을 자동 주입 (submit 가로채기)
  3. **Cross-Platform Memory**: ChatGPT에서 한 대화를 Claude에서 기억
  4. **Privacy-First**: 모든 데이터 로컬 저장, 서버 전송 없음
- Before/After 데모 (채팅 버블 스타일):
  - Before: "내가 좋아하는 게 뭐야?" → "죄송합니다, 기억하지 못합니다"
  - After: "내가 좋아하는 게 뭐야?" → "커피를 좋아하신다고 하셨죠!"
- CTA 버튼: "Install Chrome Extension" (Chrome Web Store 링크)

### FR-02: Hero 섹션 업데이트

- Hero 설명문에 Chrome Extension 언급 추가
- CTA 버튼 추가 또는 기존 CTA 수정:
  - 기존: "How does it work?" + "Get Started Free"
  - 변경: "Get Chrome Extension" (primary) + "Developer SDK" (secondary)

### FR-03: Get Started 위저드에 Chrome Extension 옵션 추가

현재 AI 선택지: Claude Desktop / Cursor / ChatGPT / Other
- **새로운 1번 선택지 추가**: "Chrome Extension" (가장 쉬운 방법)
- 선택 시 표시되는 안내:
  1. "Install from Chrome Web Store" (링크 버튼)
  2. "Visit any AI site (ChatGPT, Claude, or Gemini)"
  3. "Start chatting — Stellar Memory handles the rest!"
- OS 선택 단계 스킵 (브라우저 확장이므로 OS 무관)

### FR-04: Ecosystem 섹션에 Chrome Extension 카드 추가

- Homunculus 카드와 나란히 Chrome Extension 카드 추가
- 아이콘: 크롬 + 확장 프로그램 SVG
- 태그: Chrome Extension, ChatGPT, Claude, Gemini, TypeScript
- CTA: "Install" + "View on GitHub"

### FR-05: Navigation 업데이트

- 네비게이션에 "Extension" 링크 추가 (#chrome-extension 앵커)

### FR-06: Footer 업데이트

- Footer 배지에 "Chrome Extension" 배지 추가
- Footer 링크에 Chrome Web Store 링크 추가

### FR-07: i18n 번역 추가 (5개 언어)

모든 새 텍스트에 대해 EN/KO/ZH/ES/JA 번역 추가:
- `ext.label`, `ext.title`, `ext.subtitle`
- `ext.feat1.title`, `ext.feat1.desc` ~ `ext.feat4.title`, `ext.feat4.desc`
- `ext.before.label`, `ext.before.user`, `ext.before.ai`
- `ext.after.label`, `ext.after.user`, `ext.after.ai`
- `ext.cta`, `ext.cta.install`, `ext.cta.github`
- `nav.extension`
- `setup.ai.extension`, `setup.ext.s1`, `setup.ext.s2`, `setup.ext.s3`

총 약 25~30개 새로운 i18n 키 × 5개 언어 = 125~150개 번역 항목

### FR-08: CSS 스타일 추가

- Chrome Extension 섹션 전용 CSS
- 기능 카드 4개 그리드 레이아웃
- Before/After 데모 스타일
- AI 로고 아이콘 스타일
- 반응형 (모바일/태블릿/데스크톱)
- 기존 디자인 시스템과 일관성 유지 (dark theme, CSS 변수)

---

## 3. Non-Functional Requirements

### NFR-01: 성능
- 이미지 추가 없음 (SVG 아이콘만 사용)
- CSS inline 유지 (현재 구조 유지)
- 추가 외부 리소스 로드 없음

### NFR-02: 접근성
- 모든 아이콘에 aria-label
- 키보드 네비게이션 지원
- 시맨틱 HTML

### NFR-03: SEO
- Schema.org 메타데이터에 Chrome Extension 추가
- meta keywords에 "chrome extension, browser extension" 추가

---

## 4. Technical Approach

### 4.1 수정 파일

| 파일 | 변경 내용 |
|------|-----------|
| `landing/index.html` | 유일한 수정 대상 (단일 HTML 파일) |

### 4.2 변경 영역

1. **`<head>`**: meta keywords, Schema.org 업데이트
2. **Navigation**: Extension 링크 추가
3. **Hero**: 설명문 + CTA 업데이트
4. **새 섹션**: `#chrome-extension` (HOW IT WORKS 다음)
5. **Ecosystem**: Chrome Extension 카드 추가
6. **Get Started**: 위저드에 Extension 옵션 추가
7. **Footer**: 배지 + 링크 추가
8. **CSS**: 새 섹션 스타일
9. **i18n**: 5개 언어 번역 키 추가
10. **JS**: 위저드에 extension 선택 로직 추가

### 4.3 구현 순서

```
Step 1: CSS 스타일 추가 (chrome-extension 섹션용)
Step 2: HTML 섹션 추가 (#chrome-extension)
Step 3: Hero + Navigation 업데이트
Step 4: Get Started 위저드 업데이트
Step 5: Ecosystem + Footer 업데이트
Step 6: i18n 번역 추가 (EN/KO/ZH/ES/JA)
Step 7: JavaScript 위저드 로직 업데이트
Step 8: meta/SEO 업데이트
```

---

## 5. Acceptance Criteria

- [ ] Chrome Extension 소개 섹션이 랜딩 페이지에 표시됨
- [ ] 4개 기능 카드 (Auto-Capture, Auto-Inject, Cross-Platform, Privacy)
- [ ] Before/After 데모 (채팅 버블)
- [ ] Hero에서 Chrome Extension CTA 접근 가능
- [ ] Get Started 위저드에서 "Chrome Extension" 선택 가능
- [ ] Ecosystem에 Chrome Extension 카드 표시
- [ ] 5개 언어 모두 번역 완료
- [ ] 모바일 반응형 정상 동작
- [ ] 기존 스타일과 일관성 유지

---

## 6. Risks & Mitigations

| 리스크 | 완화 전략 |
|--------|-----------|
| Chrome Web Store 미등록 | CTA를 "Coming Soon" + GitHub 릴리스 링크로 대체 |
| HTML 파일 크기 증가 | i18n 키 최적화, 불필요한 중복 제거 |
| 기존 섹션 레이아웃 깨짐 | 기존 CSS 변수/클래스 패턴 준수 |

---

## 7. Level Assessment

- **Project Level**: Starter (단일 HTML 파일 수정)
- **Estimated Scope**: ~500 줄 추가 (HTML + CSS + i18n)
- **Risk**: Low
