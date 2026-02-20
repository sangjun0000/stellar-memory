# landing-persuasion Design Document

> **Summary**: 랜딩 페이지를 설득 중심 흐름으로 재구성하는 상세 설계
>
> **Plan**: `docs/01-plan/features/landing-persuasion.plan.md`
> **Date**: 2026-02-20
> **Status**: Draft

---

## 1. 변경 범위

**파일**: `landing/index.html` (단일 파일)

**변경 유형**:
- HTML 섹션 순서 재배치
- 새 섹션 1개 추가 (Pain Point)
- How It Works 섹션 내용 교체
- i18n 키 추가 (5개 언어: en, ko, zh, es, ja)
- CSS 추가 (새 섹션 스타일)
- 네비게이션 링크 업데이트

**변경하지 않는 것**:
- 설치 위자드 JavaScript 로직
- 기존 CSS 변수/테마
- Footer
- 기존 섹션 CSS (use-cases, features 등)

---

## 2. 새 섹션 순서

```
현재:  Hero → Use Cases → Features → How It Works(코드) → Ecosystem → Get Started → Footer
변경:  Hero → Pain Point(신규) → Use Cases → How It Works(교체) → Features → Ecosystem → Get Started → Footer
```

### 네비게이션 링크 변경

```
현재: Use Cases | Features | Ecosystem | Get Started
변경: Why? | Use Cases | How It Works | Get Started
```

---

## 3. 섹션별 상세 설계

### 3.1 Hero (수정)

**변경사항**: CTA 버튼 텍스트 변경

현재:
- 버튼1: "Get Started Free" → `#get-started`
- 버튼2: "Who Is This For?" → `#use-cases`

변경:
- 버튼1: "어떻게 동작하나요?" → `#how-it-works` (스크롤 유도)
- 버튼2: "무료로 시작하기" → `#get-started` (보조 CTA)

**i18n 키 변경**:
```
hero.cta.start → "How does it work?" (기존: "Get Started Free")
hero.cta.who → "Get Started Free" (기존: "Who Is This For?")
```

### 3.2 Pain Point 섹션 (신규) — `#pain-point`

Hero 바로 아래, Use Cases 위에 삽입.

**HTML 구조**:
```html
<section id="pain-point">
  <div class="container">
    <div class="section-label" data-i18n="pain.label">The Problem</div>
    <h2 class="section-title" data-i18n="pain.title">
      AI에게 매번 같은 말을 반복하고 있지 않나요?
    </h2>
    <p class="section-sub" data-i18n="pain.subtitle">...</p>

    <div class="pain-grid">  <!-- 3열 그리드 -->
      <!-- Card 1: 매번 반복 -->
      <div class="pain-card">
        <div class="pain-icon">🔄</div>
        <h3 data-i18n="pain.repeat.title">매번 처음부터 설명</h3>
        <div class="pain-chat">
          <div class="chat-bubble user" data-i18n="pain.repeat.before">
            "나는 프론트엔드 개발자이고, React를 쓰고, TypeScript를 선호해..."
          </div>
          <div class="chat-bubble ai" data-i18n="pain.repeat.ai">
            "알겠습니다! 어떤 도움이 필요하신가요?"
          </div>
          <div class="chat-label" data-i18n="pain.repeat.label">...다음 대화에서 또 반복</div>
        </div>
      </div>

      <!-- Card 2: 대화 끊김 -->
      <div class="pain-card">
        <div class="pain-icon">💨</div>
        <h3 data-i18n="pain.forget.title">새 대화 = 백지 상태</h3>
        <div class="pain-chat">
          <div class="chat-bubble user" data-i18n="pain.forget.before">
            "지난번에 말한 프로젝트 구조 기억나?"
          </div>
          <div class="chat-bubble ai" data-i18n="pain.forget.ai">
            "죄송합니다, 이전 대화 내용을 확인할 수 없습니다."
          </div>
        </div>
      </div>

      <!-- Card 3: 맥락 없는 AI -->
      <div class="pain-card">
        <div class="pain-icon">🤷</div>
        <h3 data-i18n="pain.context.title">내가 누군지 모르는 AI</h3>
        <div class="pain-chat">
          <div class="chat-bubble user" data-i18n="pain.context.before">
            "코드 리뷰 해줘"
          </div>
          <div class="chat-bubble ai" data-i18n="pain.context.ai">
            "어떤 언어와 프레임워크를 사용하시나요?"
          </div>
          <div class="chat-label" data-i18n="pain.context.label">...이미 100번 말했는데</div>
        </div>
      </div>
    </div>

    <p class="pain-solution" data-i18n="pain.solution">
      Stellar Memory를 설치하면, AI가 이 모든 것을 기억합니다.
    </p>
  </div>
</section>
```

**CSS**:
```css
/* Pain Point Section */
.pain-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 48px;
}

@media (max-width: 768px) {
  .pain-grid { grid-template-columns: 1fr; }
}

.pain-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 32px 24px;
  text-align: center;
}

.pain-icon { font-size: 2.5rem; margin-bottom: 16px; }
.pain-card h3 { margin-bottom: 20px; font-size: 1.1rem; }

.pain-chat {
  text-align: left;
  margin-top: 16px;
}

.chat-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  margin-bottom: 8px;
  font-size: 0.85rem;
  line-height: 1.5;
}

.chat-bubble.user {
  background: var(--accent-blue);
  color: white;
  border-bottom-right-radius: 4px;
  margin-left: 20px;
}

.chat-bubble.ai {
  background: var(--bg-surface);
  color: var(--text-secondary);
  border-bottom-left-radius: 4px;
  margin-right: 20px;
}

.chat-label {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.8rem;
  font-style: italic;
  margin-top: 8px;
}

.pain-solution {
  text-align: center;
  margin-top: 48px;
  font-size: 1.2rem;
  color: var(--accent-gold);
  font-weight: 600;
}
```

### 3.3 Use Cases (소폭 수정)

**변경사항**: 각 카드 설명에 구체적 시나리오 추가 (i18n 텍스트 업데이트만)

| 페르소나 | 기존 | 변경 |
|----------|------|------|
| 학생 | "remembers what you studied..." | + "지난주 공부한 미적분을 이어서 설명해줍니다" |
| 작가 | "knows your writing style..." | + "캐릭터 설정을 매번 안 알려줘도 기억합니다" |
| 직장인 | "remembers your clients..." | + "프로젝트 맥락을 누적으로 파악합니다" |
| 개발자 | "3 lines of code..." | + "코드 컨벤션, 아키텍처를 AI가 학습합니다" |

### 3.4 How It Works (전면 교체) — `#how-it-works`

**현재**: 코드 예제 (store/recall API) — 개발자 전용
**변경**: 3단계 시각적 설명 — 일반인 대상

**HTML 구조**:
```html
<section id="how-it-works">
  <div class="container">
    <div class="section-label" data-i18n="how.label">How It Works</div>
    <h2 class="section-title" data-i18n="how.title">
      기존 AI에 기억력을 추가하는 플러그인
    </h2>
    <p class="section-sub" data-i18n="how.subtitle">
      AI를 바꿀 필요 없습니다. 지금 쓰는 AI에 연결만 하세요.
    </p>

    <div class="how-steps-new">
      <!-- Step 1: 연결 -->
      <div class="how-step-card">
        <div class="how-step-num">1</div>
        <div class="how-step-visual">
          <!-- AI 로고 아이콘들 + 플러그 연결 SVG -->
          <svg>...</svg>
        </div>
        <h3 data-i18n="how.s1.title">AI에 연결</h3>
        <p data-i18n="how.s1.desc">
          Claude, ChatGPT, Cursor 등 — 당신이 이미 사용하는 AI에
          Stellar Memory를 연결합니다. 30초면 됩니다.
        </p>
      </div>

      <!-- Step 2: 자동 기억 -->
      <div class="how-step-card">
        <div class="how-step-num">2</div>
        <div class="how-step-visual">
          <svg>...</svg>
        </div>
        <h3 data-i18n="how.s2.title">대화하면 자동으로 기억</h3>
        <p data-i18n="how.s2.desc">
          "기억해"라고 말하지 않아도 됩니다.
          AI가 대화 중 중요한 정보를 스스로 판단해서 기억합니다.
        </p>
      </div>

      <!-- Step 3: 기억 활용 -->
      <div class="how-step-card">
        <div class="how-step-num">3</div>
        <div class="how-step-visual">
          <svg>...</svg>
        </div>
        <h3 data-i18n="how.s3.title">다음 대화부터 달라집니다</h3>
        <p data-i18n="how.s3.desc">
          새 대화를 시작해도 AI가 당신을 이미 알고 있습니다.
          이름, 취향, 프로젝트 맥락 — 더 이상 반복할 필요 없습니다.
        </p>
      </div>
    </div>

    <!-- Before/After 데모 -->
    <div class="how-demo">
      <div class="how-demo-before">
        <div class="demo-label" data-i18n="how.before.label">Stellar Memory 없이</div>
        <div class="chat-bubble user">"나는 React 개발자인데..."</div>
        <div class="chat-bubble ai">"알겠습니다! 어떤 도움이 필요하신가요?"</div>
        <div class="chat-label">--- 새 대화 ---</div>
        <div class="chat-bubble user">"나는 React 개발자인데..."</div>
      </div>
      <div class="how-demo-after">
        <div class="demo-label" data-i18n="how.after.label">Stellar Memory 사용 시</div>
        <div class="chat-bubble user">"이 컴포넌트 리뷰해줘"</div>
        <div class="chat-bubble ai">"React + TypeScript 프로젝트시죠.
함수형 컴포넌트 선호하시니까 그 기준으로 리뷰할게요."</div>
      </div>
    </div>
  </div>
</section>
```

**CSS**:
```css
.how-steps-new {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  margin-top: 48px;
}

@media (max-width: 768px) {
  .how-steps-new { grid-template-columns: 1fr; }
}

.how-step-card {
  text-align: center;
  padding: 32px 24px;
}

.how-step-num {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: var(--accent-gold);
  color: var(--bg-void);
  font-weight: 700;
  font-size: 1.2rem;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 24px;
}

.how-step-visual {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.how-step-card h3 { margin-bottom: 12px; }
.how-step-card p { color: var(--text-secondary); font-size: 0.95rem; }

/* Before/After Demo */
.how-demo {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-top: 56px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

@media (max-width: 768px) {
  .how-demo { grid-template-columns: 1fr; }
}

.how-demo-before, .how-demo-after {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 24px;
}

.how-demo-before { opacity: 0.6; }

.how-demo-after {
  border-color: var(--accent-gold);
  box-shadow: 0 0 20px rgba(240,180,41,0.1);
}

.demo-label {
  font-weight: 600;
  margin-bottom: 16px;
  font-size: 0.9rem;
}

.how-demo-before .demo-label { color: var(--text-muted); }
.how-demo-after .demo-label { color: var(--accent-gold); }
```

### 3.5 Features (위치만 이동)

How It Works 아래로 이동. 내용 변경 없음.

### 3.6 Ecosystem (유지)

변경 없음.

### 3.7 Get Started (유지, 위치 최하단)

이미 최하단. 변경 없음.

---

## 4. i18n 추가 키

5개 언어(en, ko, zh, es, ja) 모두에 아래 키 추가:

```
pain.label, pain.title, pain.subtitle
pain.repeat.title, pain.repeat.before, pain.repeat.ai, pain.repeat.label
pain.forget.title, pain.forget.before, pain.forget.ai
pain.context.title, pain.context.before, pain.context.ai, pain.context.label
pain.solution
how.label, how.s1.title, how.s1.desc, how.s2.title, how.s2.desc, how.s3.title, how.s3.desc
how.before.label, how.after.label
```

총 약 20개 키 x 5개 언어 = 100개 번역 문자열 추가

---

## 5. 구현 순서

| 순서 | 작업 | 상세 |
|------|------|------|
| 1 | CSS 추가 | Pain Point, How It Works 새 스타일 |
| 2 | Pain Point 섹션 HTML 추가 | Hero 아래에 삽입 |
| 3 | How It Works 교체 | 코드 예제 → 3단계 설명 + Before/After |
| 4 | 섹션 순서 조정 | Features를 How It Works 뒤로 이동 |
| 5 | 네비게이션 업데이트 | 링크 텍스트/href 변경 |
| 6 | Hero CTA 변경 | 버튼 텍스트/링크 교체 |
| 7 | i18n 키 추가 | 5개 언어 번역 |

---

## 6. 삭제 대상

| 대상 | 이유 |
|------|------|
| How It Works 코드 예제 HTML | 일반인 대상 3단계 설명으로 교체 |
| `setStep()` JS 함수 | 코드 탭 전환 더 이상 불필요 |
| `.code-window`, `.code-block` 등 관련 CSS | 코드 창 더 이상 사용 안 함 |
| `how.store`, `how.recall` 등 기존 i18n 키 | 새 키로 대체 |
