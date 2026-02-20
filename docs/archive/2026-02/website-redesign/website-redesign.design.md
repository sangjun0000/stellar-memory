# Design: website-redesign

**Plan 참조**: `docs/01-plan/features/website-redesign.plan.md`

## 1. 현재 구조 → 목표 구조

### 현재 (2,335 lines, 9개 섹션)
```
Nav(7메뉴) → Hero → Stats → Features(6카드) → How It Works(3단계+3코드)
→ Architecture(5존+태양계SVG) → Quick Start(체크리스트+코드) → Integrations(5카드+Docker)
→ Pricing(4-tier+결제모달) → Footer(4컬럼)
```

### 목표 (~1,400 lines 예상, 6개 섹션)
```
Nav(4메뉴+언어선택) → Hero → Features(3카드) → How It Works(2단계+2코드)
→ Quick Start(간소화) → Pricing(3-tier+결제모달) → Footer(2컬럼)
```

## 2. F1: HTML 삭제/축소 상세 설계

### 2.1 삭제 대상

| ID | 대상 | 라인 범위 | 삭제 이유 |
|----|------|----------|----------|
| F1-1 | `<section id="stats">` 전체 | L1451~L1485 | 개발 내부 지표 (603테스트, 83모듈 등) — 사용자 무관 |
| F1-2 | `<section id="architecture">` 전체 | L1704~L1795 | 5존 상세 설명 + 태양계 다이어그램 — 너무 기술적 |
| F1-3 | CSS 중 `.stat-*` 관련 | `<style>` 내 | stats 섹션 CSS 제거 |
| F1-4 | CSS 중 `.arch-*` 관련 | `<style>` 내 | architecture 섹션 CSS 제거 |
| F1-5 | JS 중 `.stat-item` fade 타겟 | L2299 | stats 요소 참조 제거 |
| F1-6 | JS 중 `.arch-zone` fade 타겟 | L2297 | architecture 요소 참조 제거 |

### 2.2 축소 대상

| ID | 대상 | 변경 내용 |
|----|------|----------|
| F1-7 | Nav 메뉴 | 7→4개: Features, Quick Start, Pricing, GitHub. (How It Works, Architecture, Integrations 삭제) |
| F1-8 | Features 카드 | 6→3개 유지: **5-Zone Orbit**, **Self-Learning**, **Multimodal Memory**. 삭제: Emotion Engine, Metacognition, Memory Reasoning |
| F1-9 | How It Works | 3단계→2단계: **Store**(step-0), **Recall**(step-2) 유지. Manage(step-1) 삭제. JS auto-cycle `% 3` → `% 2` |
| F1-10 | Integrations Docker 코드 | Docker 코드 블록(L1958~L1979) 삭제. 통합 카드 5개는 유지 |
| F1-11 | Pricing | 4-tier→3-tier: **Free, Pro, Team** 유지. Enterprise 카드 삭제 |
| F1-12 | Footer | 4컬럼→2컬럼: **Project** + **Docs** 유지. Community 컬럼 삭제 |
| F1-13 | Quick Start 코드 | 현재 30줄→10줄 이내로 축소. pip install + 3줄 기본 사용법만 |

### 2.3 Nav 목표 구조

```html
<ul class="nav-links">
  <li><a href="#features" data-i18n="nav.features">Features</a></li>
  <li><a href="#quickstart" data-i18n="nav.quickstart">Quick Start</a></li>
  <li><a href="#pricing" data-i18n="nav.pricing">Pricing</a></li>
  <li><a href="https://github.com/sangjun0000/stellar-memory" target="_blank" rel="noopener" class="nav-cta">GitHub</a></li>
  <!-- 언어 선택 드롭다운 (F2에서 추가) -->
</ul>
```

### 2.4 Features 3카드 유지 목록

```
Card 1: 5-Zone Orbit System  (--card-accent: gold)
Card 2: Self-Learning         (--card-accent: emerald)
Card 3: Multimodal Memory     (--card-accent: cyan)
```

### 2.5 How It Works 2단계 구조

```
Step 0 (Store): 기존 코드 유지
Step 1 (Recall): 기존 step-2 코드를 step-1로 re-index
```

JS 변경:
```javascript
// Before
for (let i = 0; i < 3; i++) { ... }
currentStep = (currentStep + 1) % 3;

// After
for (let i = 0; i < 2; i++) { ... }
currentStep = (currentStep + 1) % 2;
```

### 2.6 Quick Start 간소화 코드

```python
# pip install stellar-memory

from stellar_memory import StellarMemory

memory = StellarMemory()
memory.store("User prefers dark mode")
results = memory.recall("user preferences")

for mem in results:
    print(f"[{mem.zone}] {mem.content}")
```

## 3. F2: 다국어 (i18n) 상세 설계

### 3.1 구현 방식

**클라이언트 사이드 JS 기반** (서버 불필요, 단일 HTML 유지)

```
번역 흐름:
1. 페이지 로드 → localStorage('lang') 확인
2. 없으면 → navigator.language 기반 자동 감지
3. 미지원 언어면 → 'en' 기본값
4. translations[lang] 객체로 DOM 업데이트
```

### 3.2 언어 코드 매핑

| 코드 | 언어 | navigator.language 패턴 |
|------|------|------------------------|
| `en` | English | `en`, `en-US`, `en-GB` |
| `ko` | 한국어 | `ko`, `ko-KR` |
| `zh` | 中文 | `zh`, `zh-CN`, `zh-TW` |
| `es` | Español | `es`, `es-ES`, `es-MX` |
| `ja` | 日本語 | `ja`, `ja-JP` |

### 3.3 Nav 언어 선택기 HTML

```html
<li class="lang-selector">
  <button class="lang-btn" onclick="toggleLangMenu()">
    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10"/>
      <line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
    <span id="current-lang">EN</span>
  </button>
  <ul class="lang-menu" id="lang-menu">
    <li onclick="setLang('en')">English</li>
    <li onclick="setLang('ko')">한국어</li>
    <li onclick="setLang('zh')">中文</li>
    <li onclick="setLang('es')">Español</li>
    <li onclick="setLang('ja')">日本語</li>
  </ul>
</li>
```

### 3.4 CSS 디자인

```css
.lang-selector { position: relative; }
.lang-btn {
  display: flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px; padding: 6px 12px; color: var(--text-secondary);
  cursor: pointer; font-size: 0.8rem; font-weight: 600;
}
.lang-btn:hover { background: rgba(255,255,255,0.1); color: var(--text-primary); }
.lang-menu {
  display: none; position: absolute; top: 100%; right: 0; margin-top: 8px;
  background: rgba(3,7,18,0.95); backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;
  padding: 8px 0; min-width: 140px; z-index: 100;
  list-style: none;
}
.lang-menu.open { display: block; }
.lang-menu li {
  padding: 8px 16px; cursor: pointer; font-size: 0.85rem;
  color: var(--text-secondary);
}
.lang-menu li:hover { background: rgba(255,255,255,0.06); color: var(--text-primary); }
```

### 3.5 번역 키 목록 (data-i18n)

| 키 | EN | KO | ZH | ES | JA |
|----|----|----|----|----|-----|
| `hero.badge` | v2.0.0 — Now Available on PyPI | v2.0.0 — PyPI 출시 | v2.0.0 — 已在PyPI发布 | v2.0.0 — Disponible en PyPI | v2.0.0 — PyPIで公開中 |
| `hero.title` | Stellar Memory | Stellar Memory | Stellar Memory | Stellar Memory | Stellar Memory |
| `hero.subtitle` | Give any AI human-like memory | 어떤 AI에든 사람처럼 기억하는 능력을 | 赋予任何AI类人记忆能力 | Dale a cualquier IA memoria humana | あらゆるAIに人間のような記憶を |
| `hero.desc` | A celestial-structure-based memory system... | 천체 구조 기반의 기억 시스템... | 基于天体结构的记忆系统... | Un sistema de memoria basado en estructuras celestiales... | 天体構造に基づく記憶システム... |
| `nav.features` | Features | 기능 | 功能 | Características | 機能 |
| `nav.quickstart` | Quick Start | 빠른 시작 | 快速开始 | Inicio Rápido | クイックスタート |
| `nav.pricing` | Pricing | 가격 | 价格 | Precios | 料金 |
| `features.title` | Everything a memory system needs | 기억 시스템에 필요한 모든 것 | 记忆系统所需的一切 | Todo lo que necesita un sistema de memoria | 記憶システムに必要なすべて |
| `features.subtitle` | Designed from first principles... | 인간의 기억 원리를 모방하여 설계... | 从第一原理出发设计... | Diseñado desde los principios fundamentales... | 第一原理から設計された... |
| `feat.zones.title` | 5-Zone Orbit System | 5-Zone 궤도 시스템 | 5区域轨道系统 | Sistema Orbital de 5 Zonas | 5ゾーン軌道システム |
| `feat.zones.desc` | Memories organized across five concentric zones... | 기억이 5개 동심원 궤도에 배치... | 记忆分布在五个同心区域... | Memorias organizadas en cinco zonas concéntricas... | 5つの同心円ゾーンに記憶を配置... |
| `feat.learn.title` | Self-Learning | 자율 학습 | 自主学习 | Autoaprendizaje | 自律学習 |
| `feat.learn.desc` | Continuously refines its own memory organization... | 사용 패턴을 분석하여 기억을 자동 재배치... | 根据使用模式持续优化记忆组织... | Refina continuamente su organización de memoria... | 使用パターンに基づき記憶を自動再編成... |
| `feat.multi.title` | Multimodal Memory | 멀티모달 기억 | 多模态记忆 | Memoria Multimodal | マルチモーダル記憶 |
| `feat.multi.desc` | Store and recall text, code, structured data... | 텍스트, 코드, 구조화 데이터를 저장하고 검색... | 存储和检索文本、代码、结构化数据... | Almacena y recupera texto, código, datos estructurados... | テキスト、コード、構造化データを保存・検索... |
| `how.title` | Simple by design, powerful in practice | 설계는 단순하게, 실행은 강력하게 | 设计简洁，功能强大 | Simple por diseño, potente en práctica | シンプルな設計、強力な実践 |
| `how.subtitle` | Two operations. Infinite memory depth. | 두 가지 동작으로 무한한 기억 | 两步操作，无限记忆深度 | Dos operaciones. Profundidad de memoria infinita. | 2つの操作で無限の記憶 |
| `how.store` | Store | 저장 | 存储 | Almacenar | 保存 |
| `how.store.desc` | Feed any memory into the orbital system... | 기억을 궤도 시스템에 입력하면 자동 분류... | 将任何记忆输入轨道系统... | Alimenta cualquier memoria al sistema orbital... | 記憶を軌道システムに入力すると自動分類... |
| `how.recall` | Recall | 검색 | 检索 | Recordar | 検索 |
| `how.recall.desc` | Query with natural language... | 자연어로 질의하면 관련 기억을 검색... | 使用自然语言查询... | Consulta con lenguaje natural... | 自然言語で問い合わせると関連記憶を検索... |
| `qs.title` | Up and running in minutes | 몇 분 만에 시작 | 几分钟即可启动 | Listo en minutos | 数分で起動 |
| `qs.subtitle` | Install from PyPI and give your AI persistent memory. | PyPI에서 설치하면 AI에 영구 기억을 부여합니다. | 从PyPI安装，赋予AI持久记忆。 | Instala desde PyPI y dale a tu IA memoria persistente. | PyPIからインストールしてAIに永続的な記憶を。 |
| `qs.check1` | No external database required | 외부 데이터베이스 불필요 | 无需外部数据库 | No requiere base de datos externa | 外部データベース不要 |
| `qs.check2` | Compatible with OpenAI, Anthropic, LangChain | OpenAI, Anthropic, LangChain 호환 | 兼容OpenAI、Anthropic、LangChain | Compatible con OpenAI, Anthropic, LangChain | OpenAI、Anthropic、LangChain対応 |
| `qs.check3` | MCP server for Claude Code and Cursor | Claude Code, Cursor용 MCP 서버 | Claude Code和Cursor的MCP服务器 | Servidor MCP para Claude Code y Cursor | Claude Code/Cursor用MCPサーバー |
| `pricing.title` | Simple, transparent pricing | 간단하고 투명한 가격 | 简单透明的定价 | Precios simples y transparentes | シンプルで透明な料金 |
| `pricing.subtitle` | Start free. Scale when you need to. | 무료로 시작. 필요할 때 업그레이드. | 免费开始，按需扩展。 | Empieza gratis. Escala cuando lo necesites. | 無料で開始。必要に応じて拡張。 |
| `pricing.free.desc` | For personal projects | 개인 프로젝트용 | 个人项目 | Para proyectos personales | 個人プロジェクト向け |
| `pricing.pro.desc` | For production apps | 프로덕션 앱용 | 生产应用 | Para apps en producción | 本番アプリ向け |
| `pricing.team.desc` | For growing teams | 성장하는 팀용 | 成长型团队 | Para equipos en crecimiento | 成長するチーム向け |
| `pricing.cta.free` | Get Started | 시작하기 | 开始使用 | Comenzar | 始める |
| `pricing.cta.subscribe` | Subscribe | 구독하기 | 订阅 | Suscribirse | 購読する |
| `footer.desc` | An intelligent AI memory system inspired by celestial structures. | 천체 구조에서 영감을 받은 지능형 AI 기억 시스템. | 受天体结构启发的智能AI记忆系统。 | Un sistema de memoria AI inteligente inspirado en estructuras celestiales. | 天体構造にインスパイアされた知的AI記憶システム。 |

### 3.6 i18n JavaScript 함수

```javascript
const T = {
  en: { /* 위 테이블의 EN 값들 */ },
  ko: { /* KO 값들 */ },
  zh: { /* ZH 값들 */ },
  es: { /* ES 값들 */ },
  ja: { /* JA 값들 */ },
};

const LANG_LABELS = { en:'EN', ko:'KO', zh:'ZH', es:'ES', ja:'JA' };

function detectLang() {
  const saved = localStorage.getItem('lang');
  if (saved && T[saved]) return saved;
  const browser = (navigator.language || 'en').slice(0, 2).toLowerCase();
  return T[browser] ? browser : 'en';
}

function setLang(lang) {
  if (!T[lang]) lang = 'en';
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (T[lang][key]) el.textContent = T[lang][key];
  });
  document.getElementById('current-lang').textContent = LANG_LABELS[lang];
  document.documentElement.lang = lang;
  localStorage.setItem('lang', lang);
  closeLangMenu();
}

function toggleLangMenu() {
  document.getElementById('lang-menu').classList.toggle('open');
}

function closeLangMenu() {
  document.getElementById('lang-menu').classList.remove('open');
}

// 페이지 외부 클릭 시 메뉴 닫기
document.addEventListener('click', (e) => {
  if (!e.target.closest('.lang-selector')) closeLangMenu();
});

// 초기화
setLang(detectLang());
```

### 3.7 번역하지 않는 영역

- 코드 블록 (`<pre><code>` 내부)
- 브랜드명 "Stellar Memory"
- GitHub, PyPI 등 외부 링크 텍스트
- 가격 숫자 ($0, $29, $99)
- 기술 용어 (SQLite, PostgreSQL, MCP, API 등)

## 4. F3: 배포 스크립트 설계

### 4.1 `deploy.sh`

```bash
#!/bin/bash
set -e

MSG="${1:-Update landing page}"
SRC="landing/index.html"
TMP="/tmp/_stellar_deploy.html"

echo "Deploying landing page..."

# 현재 파일 임시 복사
cp "$SRC" "$TMP"

# 작업중인 변경사항 임시 저장
git stash -q 2>/dev/null || true

# gh-pages 브랜치로 전환
git checkout gh-pages -q

# 루트 + landing 모두 업데이트
cp "$TMP" index.html
cp "$TMP" landing/index.html

# 커밋 & 푸시
git add index.html landing/index.html
git commit -m "$MSG" -q
git push origin gh-pages -q

# main 브랜치 복귀
git checkout main -q
git stash pop -q 2>/dev/null || true

# 임시 파일 정리
rm -f "$TMP"

echo "Deployed to https://stellar-memory.com"
```

### 4.2 사용법

```bash
# 기본 메시지로 배포
./deploy.sh

# 커스텀 메시지로 배포
./deploy.sh "feat: add i18n support"
```

## 5. 구현 체크리스트

### F1: 간소화
- [ ] F1-1: `#stats` 섹션 HTML 삭제 (L1451~L1485)
- [ ] F1-2: `#architecture` 섹션 HTML 삭제 (L1704~L1795)
- [ ] F1-3: `.stat-*` CSS 삭제
- [ ] F1-4: `.arch-*`, `.planet-orbit` CSS 삭제
- [ ] F1-5: JS fadeTargets에서 `.stat-item` 제거
- [ ] F1-6: JS fadeTargets에서 `.arch-zone` 제거
- [ ] F1-7: Nav 메뉴 7→4개 축소
- [ ] F1-8: Features 카드 6→3개 (Emotion, Metacognition, Reasoning 삭제)
- [ ] F1-9: How It Works 3→2단계 (Manage 삭제, step 인덱스 수정)
- [ ] F1-10: Integrations Docker 코드 블록 삭제
- [ ] F1-11: Pricing Enterprise 카드 삭제
- [ ] F1-12: Footer 4→2컬럼 (Community 삭제)
- [ ] F1-13: Quick Start 코드 10줄 이내로 축소

### F2: i18n
- [ ] F2-1: Nav에 언어 선택 드롭다운 HTML 추가
- [ ] F2-2: `.lang-selector` CSS 추가
- [ ] F2-3: 번역 객체 T (5개 언어) 작성
- [ ] F2-4: `setLang()`, `detectLang()`, `toggleLangMenu()` JS 구현
- [ ] F2-5: 모든 번역 대상 요소에 `data-i18n` 속성 추가
- [ ] F2-6: `<html lang>` 동적 변경
- [ ] F2-7: localStorage 저장/복원 동작 확인

### F3: 배포
- [ ] F3-1: `deploy.sh` 파일 생성
- [ ] F3-2: 실행 권한 부여 (`chmod +x`)
- [ ] F3-3: 배포 실행 + stellar-memory.com 반영 확인

## 6. 수정 대상 파일

| 파일 | 액션 | 변경 내용 |
|------|------|----------|
| `landing/index.html` | MODIFY | F1(간소화) + F2(i18n) 전체 반영 |
| `deploy.sh` | CREATE | 1줄 배포 스크립트 |
