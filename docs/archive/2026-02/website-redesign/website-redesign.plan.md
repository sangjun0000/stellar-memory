# Plan: website-redesign

## 1. 개요

| 항목 | 내용 |
|------|------|
| Feature | website-redesign |
| 목표 | 랜딩 페이지 간소화 + 다국어 지원 + 배포 프로세스 개선 |
| 대상 파일 | `landing/index.html` (단일 파일) |
| 배포 대상 | GitHub Pages (`gh-pages` 브랜치) |

## 2. 현재 문제

### 2.1 페이지가 복잡하다
현재 섹션 (9개):
```
Nav → Hero → Stats → Features(6카드) → How It Works(3단계+코드)
→ Architecture(5존 설명+태양계 다이어그램) → Quick Start(체크리스트+코드)
→ Integrations(5카드+Docker코드) → Pricing(4-tier+결제모달) → Footer
```

**사용자가 관심 없는 것들**:
- `Stats` 섹션: 603 테스트, 83 모듈, 97.2% 등 → 개발자 내부 지표, 사용자는 관심 없음
- `Architecture` 섹션: Core/Inner/Outer/Belt/Cloud 5존 상세 설명 → 너무 기술적
- `How It Works`의 Manage 단계: promote, link, consolidate 등 고급 기능 → 초기 사용자에게 불필요
- `Integrations`의 Docker 코드 블록: 서버 배포 세부사항 → Quick Start에서 충분
- `Features` 6카드 중 일부: Metacognition, Memory Reasoning → 사용자가 직접 쓰는 기능이 아님

### 2.2 다국어 미지원
- 현재 영어 단일 언어
- 글로벌 사용자 접근성 부족

### 2.3 배포 프로세스가 복잡
- 현재: main에서 수정 → stash → gh-pages 전환 → 임시파일 복사 → 커밋 → push → main 복귀 → stash pop
- 루트 `index.html`과 `landing/index.html` 이중 관리 문제
- **해결**: 배포 스크립트 1개로 자동화 + 루트/landing 동기화

## 3. 변경 계획

### F1. 페이지 간소화 (삭제/축소)

| 액션 | 섹션 | 이유 |
|------|------|------|
| **삭제** | `#stats` (통계 바) | 개발 내부 지표. 사용자에게 무의미 |
| **삭제** | `#architecture` (5존 상세 + 태양계 다이어그램) | 너무 기술적. Hero에서 한 줄로 충분 |
| **축소** | `#features` 6→3카드 | 5-Zone Orbit, Self-Learning, Multimodal만 유지. Emotion/Metacognition/Reasoning 삭제 |
| **축소** | `#how-it-works` 3→2단계 | Store/Recall만 유지. Manage 삭제 (고급 기능) |
| **축소** | `#integrations` Docker 코드 삭제 | 카드만 유지. Docker는 Quick Start에 이미 있음 |
| **축소** | `#quickstart` 코드 간소화 | 10줄 이내로 축소 (pip install + 3줄 사용법) |
| **축소** | `#pricing` 4→3 tier | Enterprise 삭제 (아직 없으므로). Free/Pro/Team만 |
| **축소** | Nav 메뉴 | 7→4개 (Features, Quick Start, Pricing, GitHub) |
| **축소** | Footer | 4컬럼 → 2컬럼 (Project + Docs만) |

**삭제 후 섹션 (6개)**:
```
Nav → Hero → Features(3카드) → How It Works(2단계+코드)
→ Quick Start(간소화) → Pricing(3-tier) → Footer
```

### F2. 다국어 지원 (i18n)

| 항목 | 내용 |
|------|------|
| 지원 언어 | English, 한국어, 中文, Español, 日本語 |
| 구현 방식 | 단일 HTML + JavaScript 기반 클라이언트 사이드 번역 |
| 저장 | `localStorage`에 선택 언어 저장 (재방문 시 유지) |
| UI | Nav 우측에 언어 드롭다운 (🌐 아이콘 + 언어 코드) |
| 기본값 | 브라우저 `navigator.language` 기반 자동 감지 → 미지원 시 영어 |

**구현 방식**:
```javascript
// HTML에 data-i18n 속성으로 키 지정
<h1 data-i18n="hero.title">Stellar Memory</h1>
<p data-i18n="hero.subtitle">Give any AI human-like memory</p>

// JS 번역 객체
const translations = {
  en: { "hero.title": "Stellar Memory", ... },
  ko: { "hero.title": "Stellar Memory", ... },
  zh: { "hero.title": "Stellar Memory", ... },
  es: { "hero.title": "Stellar Memory", ... },
  ja: { "hero.title": "Stellar Memory", ... },
};

// 언어 전환 함수
function setLang(lang) {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = translations[lang][el.dataset.i18n];
  });
  localStorage.setItem('lang', lang);
}
```

**번역 범위**:
- Hero 텍스트 (제목, 부제, 배지, CTA)
- Features 카드 (제목, 설명)
- How It Works 단계 (제목, 설명)
- Quick Start (텍스트 부분만, 코드는 영어 유지)
- Pricing (티어 설명, CTA)
- Footer (간단한 텍스트)
- **코드 블록은 번역하지 않음** (개발자 도구이므로)

### F3. 배포 자동화

**배포 스크립트** `deploy.sh` 생성:
```bash
#!/bin/bash
# 1줄 배포: ./deploy.sh "커밋 메시지"
# landing/index.html → gh-pages 루트 index.html + landing/index.html 동시 배포

MSG="${1:-Update landing page}"
SRC="landing/index.html"

# 임시 저장
cp "$SRC" /tmp/_landing_deploy.html

# gh-pages 전환 및 배포
git stash -q
git checkout gh-pages -q
cp /tmp/_landing_deploy.html index.html
cp /tmp/_landing_deploy.html landing/index.html
git add index.html landing/index.html
git commit -m "$MSG"
git push origin gh-pages
git checkout main -q
git stash pop -q 2>/dev/null

echo "Deployed to stellar-memory.com"
```

## 4. 구현 순서

| 순서 | 작업 | 예상 변경 |
|:----:|------|----------|
| 1 | F1: 섹션 삭제/축소 (HTML) | landing/index.html 수정 |
| 2 | F1: CSS 정리 (사용하지 않는 스타일 제거) | landing/index.html 내 style 수정 |
| 3 | F2: i18n 번역 객체 + 전환 함수 구현 | landing/index.html 내 script 추가 |
| 4 | F2: HTML에 data-i18n 속성 추가 | landing/index.html 수정 |
| 5 | F2: Nav에 언어 선택 드롭다운 추가 | landing/index.html 수정 |
| 6 | F3: deploy.sh 생성 | deploy.sh 신규 생성 |
| 7 | 배포 + 검증 | deploy.sh 실행 |

## 5. 수정 대상 파일

| 파일 | 액션 |
|------|------|
| `landing/index.html` | MODIFY (간소화 + i18n) |
| `deploy.sh` | CREATE (배포 자동화) |

## 6. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| 번역 품질 | 주요 마케팅 문구는 자연스러운 번역 (직역 지양) |
| SEO 영향 | `<html lang>` + `hreflang` 메타태그로 검색 엔진 대응 |
| 코드 블록 번역 | 코드는 절대 번역하지 않음 (영어 유지) |
| 기존 CSS/JS 깨짐 | 섹션 삭제 후 관련 CSS/JS도 함께 정리 |

## 7. 성공 기준

- [ ] 페이지 섹션 9개 → 6개 이하
- [ ] Nav 메뉴 7개 → 4개 이하
- [ ] 5개 언어 전환 동작 (EN/KO/ZH/ES/JA)
- [ ] 브라우저 언어 자동 감지
- [ ] `./deploy.sh` 1줄로 배포 완료
- [ ] stellar-memory.com에서 라이브 확인
