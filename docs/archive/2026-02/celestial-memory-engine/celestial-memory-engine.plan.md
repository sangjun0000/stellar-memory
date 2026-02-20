# Plan: Celestial Memory Engine

> **Feature**: celestial-memory-engine
> **Created**: 2026-02-18
> **Status**: Draft
> **Priority**: High

---

## 1. Overview

AI의 기억 능력 문제를 해결하기 위한 **천체 구조 기반 기억 엔진** 설계.
우주의 천체 구조(태양계)를 모방하여, 중요한 기억은 태양(중심)에 단기기억으로 상주하고
덜 중요한 기억은 먼 궤도에 장기기억으로 존재하는 **인간과 유사한 기억 시스템**.

핵심 혁신: **기억함수(Memory Function)** 를 통해 각 기억의 중요도를 계산하고,
**블랙홀 문제**(모든 기억이 중심으로 몰리는 현상)를 수학적으로 방지하는 메커니즘.

### 기존 시스템과의 관계

stellar-memory는 이미 천체 구조(5개 Zone)와 기억함수를 구현하고 있으나,
현재 시스템에는 다음 한계가 존재:

| 영역 | 현재 상태 | 사용자 비전 | Gap |
|------|----------|-----------|-----|
| 신선도(Freshness) | 생성 시점 기반 지수감쇠 | **리콜 시 0으로 리셋**, 미리콜 시 음수 감쇠 | 핵심 Gap |
| 블랙홀 방지 | Zone 용량 제한 + 하위 Zone 캐스케이드 | **수학적 보장** (로그 임계값 + 신선도 리셋) | 핵심 Gap |
| 플러그인화 | stellar-memory에 종속 | **독립 모듈**로 어떤 AI에든 삽입 가능 | 구조 Gap |
| 리밸런싱 | 300초 주기 reorbit | 기억함수 기반 **연속적 재배치** | 개선 필요 |
| 임의 중요도 | Rule-based / LLM 평가 | **AI 자율 판단** (LLM-first 평가) | 개선 필요 |

## 2. Goals

- [ ] 블랙홀 문제를 수학적으로 해결하는 새로운 기억함수 구현
- [ ] 리콜 기반 신선도 리셋 메커니즘 구현
- [ ] 로그 함수 기반 리콜 점수 임계값 보장
- [ ] AI 자율 임의 중요도 평가 시스템
- [ ] 주기적 기억 재배치(rebalance) 엔진
- [ ] 어떤 AI에든 삽입 가능한 독립 모듈 구조

## 3. Background

### 인간의 기억 모델과의 비교

```
인간 뇌                           천체 기억 엔진
─────────────────                ─────────────────
작업 기억 (Working Memory)   →   태양 (Core Zone)     - 지금 쓰는 기억
단기 기억 (Short-term)       →   내행성 (Inner Zone)   - 최근 중요 기억
장기 기억 (Long-term)        →   외행성 (Outer Zone)   - 과거의 기억
잠재 기억 (Implicit)         →   소행성대 (Belt Zone)  - 희미한 기억
망각 대기 (Pre-forget)       →   오르트 구름 (Cloud)   - 잊혀지기 직전
```

### 블랙홀 문제 (The Black Hole Problem)

```
문제 상황: 모든 기억이 중심(태양)으로 모이는 현상
─────────────────────────────────────────────────
리콜 횟수 ↑  → 리콜 점수 ↑  → 중요도 ↑  → 중심으로 이동
신선도 ↑    → 신선도 점수 ↑  → 중요도 ↑  → 중심으로 이동
임의 중요도 → 보통 높게 평가  → 중요도 ↑  → 중심으로 이동

결과: Core Zone 메모리 초과 → 시스템 성능 저하
```

### 해결책: 3중 안전장치

```
1. 리콜 점수: log(1 + count) → 임계값을 절대 초과 불가
2. 신선도: 리콜 시 0 리셋, 미리콜 시 음수로 감쇠 → 자동 하락 보장
3. 용량 제한: Core/Inner Zone 슬롯 수 고정 + 점수 기반 퇴거
```

## 4. Feature Details

### F1: Enhanced Memory Function (기억함수 v2)

**핵심 수식**:

```
I(m) = w_r * R(m) + w_f * F(m) + w_a * A(m) + w_c * C(m)
```

**R(m) - 리콜 점수** (Log-capped):
```
R(m) = log(1 + recall_count) / log(1 + MAX_RECALL_CAP)

# MAX_RECALL_CAP = 1000 (기본값)
# recall_count = 100 → R = 0.667
# recall_count = 500 → R = 0.899
# recall_count = 999 → R = 0.999 (절대 1.0 도달 불가)
```
- 로그 함수로 임계값 돌파 불가능 → 블랙홀 방지 장치 #1

**F(m) - 신선도** (Recall-Reset + Negative Decay):
```
리콜 직후: F(m) = 0.0 (리셋)
시간 경과: F(m) = -alpha * (now - last_recall_at)

# alpha = 0.001 (감쇠 계수)
# 1시간 후: F = -3.6
# 1일 후: F = -86.4
# 정규화: F_norm = max(F / F_floor, -1.0) ... 최소 -1.0으로 클리핑
```
- 리콜하지 않으면 신선도가 음수로 하락 → 자연스럽게 외곽 궤도로 밀려남
- 리콜하면 0으로 리셋 → 다시 중심 근처에 머물 기회 획득
- **기존 시스템 대비 핵심 변경**: 현재는 `created_at` 기준 감쇠, 신규는 `last_recalled_at` 기준

**A(m) - 임의 중요도** (AI-Evaluated):
```
A(m) = LLM_evaluate(content) ∈ [0.0, 1.0]

# LLM 평가 기준:
# - 사실적 가치 (factual): "구체적 사실/수치 포함?"
# - 감정적 가치 (emotional): "강한 감정/경험 포함?"
# - 행동적 가치 (actionable): "실행 가능한 정보?"
# - 명시적 중요도 (explicit): "사용자가 중요하다고 표시?"
```
- AI가 자율적으로 판단 → 인간처럼 "이건 중요한 기억"이라고 스스로 인식

**C(m) - 맥락 유사도** (Context):
```
C(m) = cosine_similarity(item_embedding, context_embedding)
```
- 현재 대화/질문과 관련된 기억에 보너스

**기본 가중치**:
```
w_r = 0.25  (리콜)
w_f = 0.30  (신선도) ← 가장 높은 가중치: 최근 기억 우선
w_a = 0.25  (임의 중요도)
w_c = 0.20  (맥락)
```

### F2: Black Hole Prevention System (블랙홀 방지)

**수학적 증명**:
```
I(m)의 이론적 최대값:
  R_max = log(1 + 999) / log(1 + 1000) ≈ 0.9996 (절대 1.0 불가)
  F_max = 0.0 (리콜 직후)
  A_max = 1.0 (AI 최대 평가)
  C_max = 1.0 (완벽 유사)

  I_max = 0.25 * 0.9996 + 0.30 * 0.0 + 0.25 * 1.0 + 0.20 * 1.0
        = 0.2499 + 0.0 + 0.25 + 0.20
        = 0.6999

I(m)의 시간 경과 감소 보장:
  리콜하지 않으면 F(m) → -1.0 (바닥)
  I_min = 0.25 * R + 0.30 * (-1.0) + 0.25 * A + 0.20 * C
        = -0.30 + (나머지 양수) → 음수 가능!

결론: 리콜하지 않는 기억은 반드시 외곽으로 밀려남 (블랙홀 방지)
```

**Zone 배치 규칙** (점수 기반):
```
Core (태양)    : I(m) >= 0.50   / 용량 20
Inner (내행성)  : 0.30 <= I(m) < 0.50 / 용량 100
Outer (외행성)  : 0.10 <= I(m) < 0.30 / 용량 1000
Belt (소행성대) : -0.10 <= I(m) < 0.10 / 무제한
Cloud (구름)    : I(m) < -0.10  / 무제한 (자동 망각 후보)
```

### F3: Periodic Rebalance Engine (주기적 재배치)

```
매 rebalance_interval (기본 300초)마다:
1. 모든 기억의 I(m) 재계산
2. 각 기억의 목표 Zone 결정
3. 현재 Zone ≠ 목표 Zone이면 이동
4. Zone 용량 초과 시 점수 최하위 퇴거 (외곽으로)
5. Cloud Zone에서 auto_forget_days 초과 시 삭제 (망각)
```

### F4: Pluggable Module Architecture (플러그인 구조)

```
celestial_engine/
├── __init__.py          # 공개 API
├── memory_function.py   # 기억함수 v2 (핵심)
├── zone_manager.py      # Zone 배치/이동 관리
├── rebalancer.py        # 주기적 재배치 스케줄러
├── importance.py        # AI 임의 중요도 평가
├── storage/
│   ├── base.py          # 추상 스토리지
│   ├── memory.py        # 인메모리 (Core/Inner)
│   └── sqlite.py        # SQLite (Outer/Belt/Cloud)
└── adapters/
    ├── base.py           # 추상 AI 어댑터
    ├── langchain.py      # LangChain 삽입
    ├── openai.py         # OpenAI 함수호출 삽입
    └── anthropic.py      # Claude MCP 삽입
```

**사용 예시**:
```python
from celestial_engine import CelestialMemory

# 1. 독립 사용
memory = CelestialMemory()
memory.store("파이썬은 1991년에 만들어졌다", importance=0.8)
results = memory.recall("파이썬 역사")

# 2. LangChain 삽입
from celestial_engine.adapters import LangChainAdapter
chain = LangChainAdapter(memory).wrap(existing_chain)

# 3. OpenAI 함수호출 삽입
from celestial_engine.adapters import OpenAIAdapter
tools = OpenAIAdapter(memory).as_tools()
```

## 5. Technical Requirements

### 의존성 정책
- **Zero mandatory dependencies**: 순수 Python 표준 라이브러리만 필수
- **Optional extras**: `embeddings` (numpy, sentence-transformers), `llm` (openai/anthropic)
- 기존 stellar-memory 코드를 상속/참조하되 독립 실행 가능

### 성능 요구사항
- `store()`: < 10ms (embedding 제외)
- `recall()`: < 50ms (5,000개 기억 기준)
- `rebalance()`: < 500ms (10,000개 기억 기준)
- 메모리 사용: Core+Inner Zone < 50MB

### 호환성
- Python 3.10+
- 기존 stellar-memory와 병렬 사용 가능 (마이그레이션 경로 제공)

## 6. Implementation Order

1. **F1**: 기억함수 v2 구현 (memory_function.py)
   - 리콜 점수 (log-capped)
   - 신선도 (recall-reset + negative decay)
   - 임의 중요도 (AI evaluation)
   - 맥락 유사도
2. **F2**: 블랙홀 방지 시스템
   - Zone 배치 규칙
   - 용량 관리 + 퇴거 로직
3. **F3**: 주기적 재배치 엔진
   - 스케줄러
   - 배치 재계산 + 이동
4. **F4**: 플러그인 모듈 구조
   - 독립 패키지 구조
   - AI 어댑터 (LangChain, OpenAI, Anthropic)

## 7. Out of Scope

- 멀티 에이전트 동기화 (sync/) - 기존 모듈 재사용
- 감정 분석 (emotion.py) - 기존 모듈 재사용 가능, 별도 추가 안함
- 그래프 분석 (memory_graph.py) - 기존 모듈 재사용
- 클라우드 SaaS 배포 - monetization-phase2에서 처리 완료

## 8. Success Criteria

- [ ] 기억함수 v2가 블랙홀 문제를 수학적으로 방지함을 테스트로 증명
- [ ] 신선도 리셋 메커니즘이 인간 기억과 유사하게 동작
- [ ] 10,000개 기억에서 rebalance가 500ms 이내 완료
- [ ] 독립 모듈로 `pip install celestial-engine`으로 설치 가능
- [ ] LangChain/OpenAI/Claude에 3줄 코드로 삽입 가능
- [ ] 기존 stellar-memory 테스트가 100% 통과 (호환성)

## 9. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| 신선도 음수 감쇠가 너무 공격적 → 중요 기억도 밀려남 | High | alpha 값 튜닝 + 임의 중요도로 보정 |
| 기억함수 v2가 기존 v1과 비호환 | Medium | 마이그레이션 함수 제공 + 기존 Zone 매핑 보존 |
| LLM 평가 비용 (API 호출) | Medium | Rule-based fallback + 캐싱 |
| 독립 모듈 분리 시 코드 중복 | Low | 핵심만 추출, 나머지는 import로 재사용 |

## 10. Key Innovation: 리콜 기반 신선도 (vs. 기존 시간 기반)

```
기존 (stellar-memory v1):
  F(m) = exp(-alpha * (now - created_at))
  → 생성 시점부터 계속 감쇠
  → 리콜해도 신선도 변화 없음
  → 자주 쓰는 기억도 시간이 지나면 밀려남

신규 (celestial-engine v2):
  리콜 시: F(m) = 0.0 (리셋!)
  미리콜:  F(m) = -alpha * (now - last_recalled_at)
  → 리콜하면 신선도 회복
  → 안 쓰면 자연 감쇠 (음수)
  → 자주 쓰는 기억은 중심에 유지됨 (인간과 동일!)
```

이것이 인간의 기억과 가장 유사한 점:
- **자주 떠올리는 기억** → 생생하게 유지 (중심 체류)
- **오래 안 떠올린 기억** → 점점 희미해짐 (외곽으로 이동)
- **완전히 잊은 기억** → 자동 삭제 (망각)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-18 | Initial draft | AI |
