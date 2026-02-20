# Plan: celestial-engine-plugin

## 1. 개요

| 항목 | 내용 |
|------|------|
| Feature | celestial-engine-plugin |
| 목표 | 천체구조 기반 AI 기억 시스템을 독립 패키지로 정비 + 기존 AI에 쉽게 삽입할 수 있는 미들웨어 제공 |
| 핵심 컨셉 | 태양계 구조 모방: 중요한 기억 = 태양(단기기억), 덜 중요한 기억 = 외곽 궤도(장기기억) |
| 대상 | `celestial_engine/` 패키지 (기존 코드 정비 + 확장) |

## 2. 현재 상태 분석

### 2.1 이미 구현된 것 (celestial_engine/)

`celestial_engine/` 패키지에 사용자가 구상한 핵심 시스템이 **이미 구현되어 있음**:

| 구성 요소 | 파일 | 상태 |
|-----------|------|------|
| 기억 함수 (Memory Function) | `memory_function.py` | 구현됨 |
| 중요도 평가 (Importance Evaluator) | `importance.py` | 구현됨 |
| 5존 관리 (Zone Manager) | `zone_manager.py` | 구현됨 |
| 주기적 재배치 (Rebalancer) | `rebalancer.py` | 구현됨 |
| 데이터 모델 | `models.py` | 구현됨 |
| 저장소 (InMemory + SQLite) | `storage/` | 구현됨 |
| AI 어댑터 (OpenAI, Anthropic, LangChain) | `adapters/` | 구현됨 |

**기억 함수 공식** (이미 구현):
```
I(m) = w_r * R(m) + w_f * F(m) + w_a * A(m) + w_c * C(m)

R(m) = log(1 + count) / log(1 + MAX_CAP)    → 로그함수로 임계값 방지
F(m) = -alpha * (now - last_recall) / |floor| → 리콜 시 0 초기화, 미리콜 시 음수 감소
A(m) = AI가 판단하는 임의 중요도               → LLMEvaluator 구현
C(m) = 문맥 유사도 (코사인 유사도)             → 임베딩 기반
```

**블랙홀 방지** (이미 구현):
1. R(m): 로그함수로 1.0 초과 불가 (max_recall_cap=1000)
2. F(m): 리콜 없으면 -1.0까지 감소 → 총점 하락 → 외곽으로 밀려남
3. Zone 용량 제한: Core(20), Inner(100), Outer(1000) → 초과 시 퇴거

### 2.2 문제점 (해결해야 할 것)

| 문제 | 설명 |
|------|------|
| **패키징 누락** | `pyproject.toml`에 `celestial_engine`이 포함되지 않음. `stellar_memory*`만 배포됨 |
| **독립 사용 불가** | `celestial_engine`을 단독으로 pip install 할 수 없음 |
| **검색 성능** | SQLite LIKE 검색만 사용. 벡터 유사도 검색 미지원 |
| **자동 주입 없음** | 기억을 AI 프롬프트에 자동으로 주입하는 미들웨어 없음 |
| **대화 자동 저장 없음** | AI와의 대화를 자동으로 기억에 저장하는 기능 없음 |
| **버전 불일치** | pyproject.toml은 1.0.0, 랜딩 페이지는 2.0.0 |

## 3. 변경 계획

### F1. 패키지 정비 및 배포 준비

**목표**: `celestial_engine`을 `stellar-memory` 패키지의 핵심 모듈로 포함

| 항목 | 변경 내용 |
|------|----------|
| `pyproject.toml` | `celestial_engine*` 추가. 버전 2.0.0으로 업데이트 |
| `celestial_engine/__init__.py` | 공개 API 정리. 버전 상수 추가 |
| 의존성 | 핵심 기능은 zero-dependency 유지 |

```toml
# pyproject.toml 변경
[tool.setuptools.packages.find]
include = ["stellar_memory*", "celestial_engine*"]

[project]
version = "2.0.0"
```

### F2. AI 미들웨어 레이어 (핵심 신규 기능)

**목표**: 기존 AI에 기억 능력을 "삽입"하는 미들웨어

```python
# 사용자가 원하는 최종 모습
from celestial_engine import CelestialMemory
from celestial_engine.middleware import MemoryMiddleware

memory = CelestialMemory()
middleware = MemoryMiddleware(memory)

# OpenAI에 기억 삽입
response = middleware.wrap_openai(client).chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "내 이름 기억해?"}]
)

# Anthropic에 기억 삽입
response = middleware.wrap_anthropic(client).messages.create(
    model="claude-sonnet-4-5-20250514",
    messages=[{"role": "user", "content": "어제 뭐 얘기했지?"}]
)
```

**미들웨어 동작 원리**:
1. 사용자 메시지 수신
2. `recall(query)` → 관련 기억 검색
3. 시스템 프롬프트에 기억 컨텍스트 주입
4. AI 응답 수신
5. 대화 내용을 `store()` → 자동 기억 저장
6. 기억 함수가 중요도 계산 → 적절한 Zone에 배치

**새 파일**: `celestial_engine/middleware.py`

| 클래스 | 역할 |
|--------|------|
| `MemoryMiddleware` | 기억 주입/저장 미들웨어 코어 |
| `OpenAIWrapper` | OpenAI SDK 래퍼 |
| `AnthropicWrapper` | Anthropic SDK 래퍼 |
| `ContextBuilder` | 검색된 기억 → 시스템 프롬프트 포매팅 |

### F3. 벡터 검색 강화

**목표**: 텍스트 LIKE 검색 → 임베딩 기반 유사도 검색으로 업그레이드

| 항목 | 변경 내용 |
|------|----------|
| `storage/memory.py` | 코사인 유사도 검색 추가 |
| `storage/sqlite.py` | 임베딩 기반 검색 로직 추가 |
| `zone_manager.py` | 검색 시 임베딩 우선 사용 |

현재 `search()` 메서드는 `query_embedding` 파라미터를 받지만 **실제로 사용하지 않음**.
이를 실제 코사인 유사도 검색으로 구현:

```python
# storage/memory.py - 변경
def search(self, query, limit=5, query_embedding=None):
    if query_embedding:
        # 코사인 유사도로 검색 (벡터 기반)
        scored = [(item, cosine_sim(item.embedding, query_embedding))
                  for item in self._items.values() if item.embedding]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:limit]]
    else:
        # 기존 텍스트 검색 (폴백)
        ...
```

### F4. 대화 자동 기억 (Auto-Memory)

**목표**: AI와의 대화를 자동으로 분석하여 기억에 저장

```python
class AutoMemory:
    """대화에서 중요한 정보를 자동 추출하여 저장."""

    def process_turn(self, user_msg: str, ai_response: str):
        # 1. LLMEvaluator로 중요도 판단
        # 2. 중요한 사실 추출 (이름, 선호, 약속 등)
        # 3. 기존 기억과 중복 검사
        # 4. 새 기억 저장
```

**새 파일**: `celestial_engine/auto_memory.py`

### F5. 기억 함수 설정 편의성 개선

**목표**: 사용자가 기억 함수의 가중치를 쉽게 조정할 수 있도록

현재 `MemoryFunctionConfig`의 기본값:
```python
w_recall: float = 0.25      # 리콜 가중치
w_freshness: float = 0.30   # 신선도 가중치
w_arbitrary: float = 0.25   # 임의 중요도 가중치
w_context: float = 0.20     # 문맥 유사도 가중치
```

**프리셋 추가**:
```python
class MemoryPresets:
    CONVERSATIONAL = MemoryFunctionConfig(
        w_recall=0.20, w_freshness=0.35, w_arbitrary=0.25, w_context=0.20
    )  # 대화형: 신선도 중시

    FACTUAL = MemoryFunctionConfig(
        w_recall=0.30, w_freshness=0.15, w_arbitrary=0.35, w_context=0.20
    )  # 사실 기반: 중요도 중시

    RESEARCH = MemoryFunctionConfig(
        w_recall=0.15, w_freshness=0.20, w_arbitrary=0.25, w_context=0.40
    )  # 연구용: 문맥 유사도 중시
```

## 4. 구현 순서

| 순서 | 작업 | 예상 변경 파일 |
|:----:|------|---------------|
| 1 | F1: `pyproject.toml` 패키지 정비 (celestial_engine 포함 + 버전 2.0.0) | `pyproject.toml` |
| 2 | F3: 벡터 검색 구현 (InMemory + SQLite) | `storage/memory.py`, `storage/sqlite.py` |
| 3 | F5: 기억 함수 프리셋 추가 | `memory_function.py` |
| 4 | F2: MemoryMiddleware 코어 구현 | `middleware.py` (신규) |
| 5 | F2: OpenAI/Anthropic 래퍼 구현 | `middleware.py` |
| 6 | F4: AutoMemory 자동 기억 기능 | `auto_memory.py` (신규) |
| 7 | F2+F4 통합: 미들웨어에 자동 기억 연결 | `middleware.py` |
| 8 | 예제 코드 업데이트 | `examples/` |

## 5. 수정 대상 파일

| 파일 | 액션 |
|------|------|
| `pyproject.toml` | MODIFY (패키지 포함 + 버전 업데이트) |
| `celestial_engine/storage/memory.py` | MODIFY (벡터 검색 추가) |
| `celestial_engine/storage/sqlite.py` | MODIFY (벡터 검색 추가) |
| `celestial_engine/memory_function.py` | MODIFY (프리셋 추가) |
| `celestial_engine/middleware.py` | CREATE (미들웨어 레이어) |
| `celestial_engine/auto_memory.py` | CREATE (자동 기억 기능) |
| `celestial_engine/__init__.py` | MODIFY (공개 API 추가) |
| `examples/middleware_openai.py` | CREATE (사용 예제) |
| `examples/middleware_anthropic.py` | CREATE (사용 예제) |

## 6. 아키텍처 설계

```
사용자 AI 앱
    ↓
┌─────────────────────────────────────────┐
│          MemoryMiddleware               │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ ContextBuilder│  │  AutoMemory    │  │
│  │ (기억→프롬프트) │  │ (대화→기억저장) │  │
│  └──────┬──────┘  └───────┬─────────┘  │
│         └──────┬──────────┘            │
│                ↓                        │
│  ┌──────────────────────────────┐      │
│  │      CelestialMemory         │      │
│  │  ┌─────────────────────────┐│      │
│  │  │   Memory Function       ││      │
│  │  │  I = wR + wF + wA + wC ││      │
│  │  └─────────────────────────┘│      │
│  │  ┌─────────────────────────┐│      │
│  │  │   Zone Manager (5존)    ││      │
│  │  │ ☀Core→Inner→Outer→Belt→Cloud│   │
│  │  └─────────────────────────┘│      │
│  │  ┌─────────────────────────┐│      │
│  │  │   Rebalancer (주기적)   ││      │
│  │  └─────────────────────────┘│      │
│  └──────────────────────────────┘      │
└─────────────────────────────────────────┘
    ↓                    ↓
OpenAI API          Anthropic API
```

## 7. 기억 함수 수학적 설계 (현재 구현 확인)

### 7.1 리콜 점수 R(m) - 블랙홀 방지 #1
```
R(m) = log(1 + recall_count) / log(1 + MAX_CAP)

MAX_CAP = 1000
recall_count=1   → R = 0.10
recall_count=10  → R = 0.35
recall_count=100 → R = 0.67
recall_count=999 → R = 0.9996  (절대 1.0 도달 불가)
```

### 7.2 신선도 점수 F(m) - 블랙홀 방지 #2
```
리콜 직후:    F = 0.0 (리셋)
1시간 후:     F ≈ -0.04
1일 후:       F ≈ -1.0 (바닥)
리콜 없으면:  점점 음수 → 총점 하락 → 외곽으로 이동
```

### 7.3 임의 중요도 A(m) - AI 자율 판단
```
DefaultEvaluator:   항상 0.5 반환
RuleBasedEvaluator: 키워드 패턴 매칭 (사실/감정/행동/명시적 중요도)
LLMEvaluator:       AI가 직접 0.0~1.0 점수 판단 (JSON 응답)
```

### 7.4 총 중요도 계산 → 존 배치
```
I(m) = 0.25*R + 0.30*F + 0.25*A + 0.20*C

Zone 배치:
I ≥ 0.50  → Core (☀ 태양, 단기기억, 20슬롯)
I ≥ 0.30  → Inner (수성~금성, 100슬롯)
I ≥ 0.10  → Outer (지구~화성, 1000슬롯)
I ≥ -0.10 → Belt (소행성대, 무제한)
I < -0.10 → Cloud (오르트 구름, 90일 후 삭제)
```

## 8. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| OpenAI/Anthropic SDK 버전 호환성 | 래퍼는 선택적 의존성. 런타임 import로 처리 |
| 임베딩 연산 비용 | 배치 처리 + 캐싱. 임베딩 없이도 텍스트 검색 폴백 |
| 미들웨어 latency | 비동기 store (백그라운드), recall은 동기 (응답 전 필요) |
| 자동 기억 중복 | 유사도 임계값으로 중복 저장 방지 |
| 기존 stellar_memory와 충돌 | celestial_engine은 독립 모듈, stellar_memory에서 import 가능 |

## 9. 성공 기준

- [ ] `pip install stellar-memory`로 celestial_engine 포함 설치
- [ ] OpenAI 래퍼 3줄로 기억 삽입 가능
- [ ] Anthropic 래퍼 3줄로 기억 삽입 가능
- [ ] 벡터 유사도 검색 동작 (임베딩 제공 시)
- [ ] 대화 자동 기억 저장 동작
- [ ] 기억 함수 프리셋 3종 제공
- [ ] 기존 테스트 통과 유지
