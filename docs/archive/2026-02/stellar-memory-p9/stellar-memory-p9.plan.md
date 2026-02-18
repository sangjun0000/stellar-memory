# stellar-memory-p9 Planning Document

> **Summary**: 고급 인지 & 자율 학습 - "AI가 스스로 성장하는 기억 시스템" (v1.0.0 정식 릴리스)
>
> **Project**: Stellar Memory
> **Version**: v0.9.0 → v1.0.0
> **Author**: Stellar Memory Team
> **Date**: 2026-02-17
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

P8까지 Stellar Memory는 **상용화 완료된 지능형 기억 플랫폼**이 되었습니다(508개 테스트, CI/CD, MkDocs 문서, OpenAPI, 예제 3종). 그러나 현재 시스템은 여전히 **수동적(passive)**입니다 - 사용자가 저장하면 기억하고, 물어보면 답할 뿐입니다.

P9의 목적은 **AI가 능동적으로 자신의 기억을 관리하는 시스템**을 만드는 것입니다:

1. **메타인지**: "내가 뭘 알고 뭘 모르는지" 스스로 파악
2. **자율 학습**: 사용 패턴을 분석하여 기억 함수 파라미터를 자동 최적화
3. **멀티모달 기억**: 텍스트 외에 코드, JSON, 구조화 데이터 처리
4. **기억 추론**: 기존 기억을 조합하여 새로운 인사이트 도출
5. **벤치마크**: 기억 시스템의 정량적 성능 측정 도구

이 5가지 기능을 통해 **v1.0.0 정식 릴리스**를 달성합니다.

### 1.2 Background

**P1~P8 진화 경로**:

```
MVP → 기억 → 이해 → 안정 → 연결 → 영속 → 지능 → 협업 → 감성+상용화 → 문서+생태계
```

**현재까지 달성한 사람의 기억 능력**:

| 사람의 기억 | 구현 상태 | 단계 |
|------------|:---------:|:----:|
| 중요한 건 잘 기억 | OK | MVP |
| 연상 기억 | OK | P3 |
| 기억 망각 | OK | P4 |
| 차등 망각 | OK | P5 |
| 감정이 기억에 영향 | OK | P7 |
| **"내가 뭘 모르는지 아는 것"** | **미구현** | **P9** |
| **패턴 학습으로 기억력 향상** | **미구현** | **P9** |
| **다양한 형태의 정보 기억** | **미구현** | **P9** |
| **기억을 조합한 추론** | **미구현** | **P9** |

**메타인지(Metacognition)**는 인간 인지과학에서 가장 고급 기능 중 하나입니다. 아이와 어른의 핵심 차이가 바로 "자신이 뭘 모르는지 아는 능력"입니다. P9에서 이를 구현하면 Stellar Memory는 단순한 데이터 저장소에서 **자기 인식을 가진 지능 시스템**으로 도약합니다.

### 1.3 Related Documents

- 종합 보고서: `docs/stellar-memory-종합보고서.md`
- P8 아카이브: `docs/archive/2026-02/stellar-memory-p8/`
- 수익화 전략: `docs/stellar-memory-수익화전략.md`

---

## 2. Scope

### 2.1 In Scope

- [ ] F1: 메타인지 엔진 (Metacognition Engine) - 지식 상태 자기 인식 + 신뢰도 기반 응답
- [ ] F2: 자율 학습 & 가중치 최적화 (Self-Learning) - 사용 패턴 분석 + 파라미터 자동 튜닝
- [ ] F3: 멀티모달 기억 (Multimodal Memory) - 코드/JSON/구조화 데이터 타입별 처리
- [ ] F4: 기억 추론 (Memory Reasoning) - 기존 기억 조합 → 새로운 인사이트 도출
- [ ] F5: 벤치마크 & 성능 프로파일링 - 리콜 정확도/응답시간/메모리 사용량 정량 측정

### 2.2 Out of Scope

- Cloud SaaS 인프라 배포 (AWS/GCP - 별도 운영 로드맵)
- 결제 시스템 (Stripe 등 - 별도 비즈니스 로드맵)
- 다국어 SDK (JavaScript/Go/Rust - P10 범위)
- 실시간 학습 (온라인 러닝 - 연구 단계)
- GPU 가속 추론 (벡터 연산 최적화 - 성능 로드맵)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|:--------:|:------:|
| **F1: 메타인지 엔진** | | | |
| FR-01 | `introspect(topic)` - 주제별 지식 상태 분석 (confidence, coverage, gaps) | Critical | Pending |
| FR-02 | `recall_with_confidence(query)` - 신뢰도 점수 포함 리콜 (0.0~1.0) | Critical | Pending |
| FR-03 | 지식 커버리지 맵 - 주제별 기억 밀도 시각화 데이터 생성 | High | Pending |
| FR-04 | 자동 불확실성 경고 - 신뢰도 < 임계값 시 "확실하지 않음" 플래그 | High | Pending |
| FR-05 | 지식 갭 탐지 - 관련 기억이 부족한 영역 자동 식별 | Medium | Pending |
| **F2: 자율 학습** | | | |
| FR-06 | `optimize()` - 리콜 패턴 분석 → 기억 함수 가중치 자동 조정 | Critical | Pending |
| FR-07 | 사용 패턴 수집기 - 리콜 쿼리/결과/피드백 이력 추적 | High | Pending |
| FR-08 | 적응형 가중치 - 사용자 행동에 따라 w₁~w₅ 자동 업데이트 | High | Pending |
| FR-09 | 학습 보고서 - 최적화 전후 성능 비교 통계 | Medium | Pending |
| FR-10 | 롤백 메커니즘 - 최적화 결과가 나쁠 경우 이전 가중치 복원 | Medium | Pending |
| **F3: 멀티모달 기억** | | | |
| FR-11 | `content_type` 필드 추가 - "text", "code", "json", "structured" 타입 구분 | High | Pending |
| FR-12 | 코드 기억 처리 - 언어 감지, 구문 분석, 함수/클래스 단위 분리 | High | Pending |
| FR-13 | JSON/구조화 데이터 - 스키마 인식 저장 + 필드 기반 검색 | High | Pending |
| FR-14 | 타입별 임베딩 전략 - 코드는 코드 임베더, 텍스트는 텍스트 임베더 | Medium | Pending |
| **F4: 기억 추론** | | | |
| FR-15 | `reason(query)` - 관련 기억 조합 → 추론 결과 생성 (LLM 기반) | High | Pending |
| FR-16 | 모순 탐지 - 상충하는 기억 자동 식별 + 해결 제안 | High | Pending |
| FR-17 | 인사이트 생성 - 기억 간 패턴/트렌드 자동 발견 | Medium | Pending |
| FR-18 | 추론 체인 기록 - 어떤 기억에서 어떤 결론이 도출되었는지 추적 | Medium | Pending |
| **F5: 벤치마크** | | | |
| FR-19 | `benchmark(queries, dataset)` - 리콜 정확도 측정 (recall@k, precision@k) | Critical | Pending |
| FR-20 | 응답시간 프로파일링 - store/recall/reorbit 각 단계별 지연시간 측정 | High | Pending |
| FR-21 | 메모리 사용량 추적 - 기억 수/존별 분포/DB 크기 실시간 모니터링 | High | Pending |
| FR-22 | 벤치마크 보고서 - JSON/HTML 형식 결과 내보내기 | Medium | Pending |
| FR-23 | 표준 데이터셋 - 벤치마크용 기억 세트 내장 (100/1000/10000건) | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| 성능 | introspect() 응답 < 500ms (1000개 기억 기준) | benchmark 도구 |
| 성능 | reason() 응답 < 2초 (LLM 호출 포함) | benchmark 도구 |
| 성능 | optimize() 완료 < 10초 (5000개 리콜 이력 기준) | 실시간 측정 |
| 정확도 | recall_with_confidence 신뢰도와 실제 정확도 상관계수 > 0.7 | 벤치마크 검증 |
| 호환성 | 기존 508개 테스트 100% 통과 (하위 호환) | pytest |
| 안정성 | optimize() 실패 시 자동 롤백 (데이터 무손실) | 단위 테스트 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `memory.introspect("topic")` → confidence, coverage, gaps 반환
- [ ] `memory.recall_with_confidence("query")` → 결과 + 신뢰도 점수
- [ ] `memory.optimize()` → 가중치 자동 조정 + 전후 비교 보고서
- [ ] `memory.store(content, content_type="code")` → 코드 특화 저장/검색
- [ ] `memory.reason("query")` → 기억 조합 추론 결과 생성
- [ ] `memory.benchmark(queries=100)` → recall@5, avg_latency, memory_usage 보고서
- [ ] 전체 테스트 590+ 통과 (기존 508 + 신규 80+)
- [ ] 모든 신규 기능 기본 비활성화 (하위 호환 100%)

### 4.2 Quality Criteria

- [ ] 신규 코드 테스트 커버리지 80% 이상
- [ ] 기존 508개 테스트 변경 없이 통과
- [ ] Zero lint errors
- [ ] 빌드 성공 (PyPI + Docker)
- [ ] v1.0.0 릴리스 준비 완료

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|:------:|:----------:|------------|
| 메타인지 정확도 부족 | High | Medium | 점진적 개선 - 규칙 기반 → LLM 보강 2단계 접근 |
| 자율 학습 과최적화 | High | Medium | 롤백 메커니즘 필수, 보수적 학습률 적용 |
| LLM 의존성 증가 (추론) | Medium | High | NullLLM 패턴 유지 - LLM 없이도 규칙 기반 폴백 |
| 멀티모달 임베딩 불일치 | Medium | Medium | 타입별 임베딩 공간 분리 + 교차 검색 시 정규화 |
| 벤치마크 재현성 | Low | Medium | 시드 고정 + 표준 데이터셋 내장 |
| v1.0.0 릴리스 부담 | Medium | Low | 기능별 feature flag, GA 전 RC 버전 선행 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites | - |
| **Dynamic** | Feature-based modules, BaaS | Web apps, SaaS | - |
| **Enterprise** | Strict layer separation, DI | High-traffic systems | OK |

기존 Enterprise 레벨 아키텍처 유지. 신규 모듈은 기존 플러그인 패턴을 따름.

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 메타인지 구현 | 규칙 기반 / LLM 기반 / 하이브리드 | 하이브리드 | 기본 규칙 + LLM으로 정밀도 향상 |
| 자율 학습 알고리즘 | 단순 통계 / 경사하강법 / 베이지안 | 단순 통계 + 이동평균 | 외부 의존성 없이 순수 Python으로 구현 |
| 멀티모달 처리 | 단일 임베딩 / 타입별 분리 | 타입별 분리 | 코드/텍스트 임베딩 품질 차이 큼 |
| 추론 엔진 | 규칙 기반 / LLM 체인 | LLM 체인 (NullLLM 폴백) | 유연한 추론, LLM 없으면 키워드 연결 |
| 벤치마크 형식 | 자체 포맷 / 표준 포맷 | JSON + HTML 보고서 | 프로그래밍적 활용 + 시각적 확인 |
| 테스트 프레임워크 | pytest (기존) | pytest | 일관성 유지 |

### 6.3 파일 구조 변경 예상

```
stellar_memory/                    # 기존 55개 + 신규 ~8개
├── (기존 파일 유지)
│
├── metacognition.py               # P9-F1: 메타인지 엔진
│   ├── Introspector 클래스
│   ├── ConfidenceScorer 클래스
│   └── KnowledgeGapDetector 클래스
│
├── self_learning.py               # P9-F2: 자율 학습
│   ├── PatternCollector 클래스
│   ├── WeightOptimizer 클래스
│   └── LearningReport 클래스
│
├── multimodal.py                  # P9-F3: 멀티모달 기억
│   ├── ContentTypeHandler ABC
│   ├── CodeMemoryHandler 클래스
│   └── StructuredMemoryHandler 클래스
│
├── reasoning.py                   # P9-F4: 기억 추론
│   ├── MemoryReasoner 클래스
│   ├── ContradictionDetector 클래스
│   └── InsightGenerator 클래스
│
└── benchmark.py                   # P9-F5: 벤치마크
    ├── MemoryBenchmark 클래스
    ├── StandardDataset 클래스
    └── BenchmarkReport 클래스

tests/                             # 신규 테스트 ~80개
├── test_p9_metacognition.py       # ~20 tests
├── test_p9_self_learning.py       # ~15 tests
├── test_p9_multimodal.py          # ~15 tests
├── test_p9_reasoning.py           # ~15 tests
└── test_p9_benchmark.py           # ~15 tests
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `CLAUDE.md` 존재
- [x] `CONTRIBUTING.md` 존재 (P8)
- [x] pytest 설정 (pyproject.toml)
- [x] MIT 라이선스
- [x] GitHub Actions CI/CD (P8)
- [x] MkDocs 문서 사이트 (P8)

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|:------------:|-----------|:--------:|
| **Naming** | OK (snake_case) | P9 모듈명 확정 | Medium |
| **Folder structure** | OK (모듈별) | 신규 파일 위치 확정 | High |
| **NullProvider 패턴** | OK (기존) | 메타인지/추론에도 NullLLM 적용 | High |
| **Feature Flag** | 부분적 | 모든 P9 기능 기본 비활성화 | Critical |
| **Config 확장** | OK (dataclass) | MetacognitionConfig, BenchmarkConfig 추가 | High |

### 7.3 Environment Variables

| Variable | Purpose | Scope | To Be Created |
|----------|---------|:-----:|:-------------:|
| `STELLAR_DB_PATH` | SQLite DB 경로 | Runtime | 존재 |
| `STELLAR_METACOGNITION` | 메타인지 활성화 | Runtime | 신규 |
| `STELLAR_SELF_LEARNING` | 자율 학습 활성화 | Runtime | 신규 |
| `STELLAR_BENCHMARK_SEED` | 벤치마크 시드 | Testing | 신규 |

---

## 8. Feature Details

### F1: 메타인지 엔진 (Metacognition Engine)

**목표**: AI가 "내가 뭘 알고 뭘 모르는지" 스스로 파악하는 자기 인식 기억.

**핵심 API**:

```python
# 지식 상태 분석
state = memory.introspect("React 프레임워크")
# → IntrospectionResult(
#     confidence=0.85,
#     coverage=["hooks", "components", "state"],
#     gaps=["server components", "suspense"],
#     memory_count=12,
#     avg_freshness=-3.2
# )

# 신뢰도 포함 리콜
result = memory.recall_with_confidence("Next.js App Router")
# → ConfidentRecall(
#     memories=[...],
#     confidence=0.42,
#     warning="Low confidence - limited knowledge on this topic"
# )
```

**구현 방식**:
1. 주제 관련 기억 검색 → 기억 수, 신선도, 존 분포 분석
2. 커버리지 계산: 관련 키워드/태그 중 기억에 존재하는 비율
3. 갭 탐지: 관련 주제 그래프에서 기억이 없는 노드 식별
4. 신뢰도 공식: `conf = min(1.0, α*coverage + β*avg_freshness + γ*memory_density)`

### F2: 자율 학습 & 가중치 최적화 (Self-Learning)

**목표**: 사용자 행동 패턴을 분석하여 기억 함수 가중치를 자동 최적화.

**핵심 API**:

```python
# 사용 패턴 기반 자동 최적화
report = memory.optimize()
# → OptimizationReport(
#     before_weights={w_recall: 0.3, w_freshness: 0.25, ...},
#     after_weights={w_recall: 0.2, w_freshness: 0.35, ...},
#     improvement="+12% recall accuracy",
#     pattern="User prefers recent memories"
# )
```

**구현 방식**:
1. PatternCollector: 리콜 쿼리, 결과, 사용자 피드백(재검색=불만족) 이력 수집
2. 분석: "최근 기억 선호", "감정적 기억 선호" 등 패턴 탐지
3. WeightOptimizer: 이동평균 기반 가중치 미세 조정 (학습률 0.01~0.05)
4. 검증: 최근 100개 리콜에 대해 새 가중치로 시뮬레이션 → 개선 시만 적용
5. 롤백: 성능 저하 시 이전 가중치로 자동 복원

### F3: 멀티모달 기억 (Multimodal Memory)

**목표**: 텍스트 외에 코드, JSON, 구조화 데이터를 각 특성에 맞게 처리.

**핵심 API**:

```python
# 코드 기억
memory.store(
    content="def fibonacci(n): ...",
    content_type="code",
    metadata={"language": "python", "function": "fibonacci"}
)

# 구조화 데이터 기억
memory.store(
    content={"user": "kim", "action": "purchase", "amount": 50000},
    content_type="json",
    metadata={"schema": "user_event"}
)

# 타입별 검색
memories = memory.recall("fibonacci function", content_type="code")
```

**구현 방식**:
1. ContentTypeHandler ABC: 타입별 저장/검색/임베딩 전략 분리
2. CodeMemoryHandler: 언어 감지(정규식 기반), 함수/클래스 단위 분리
3. StructuredMemoryHandler: JSON 스키마 인식, 필드 기반 필터링
4. 기존 store/recall에 `content_type` 파라미터 추가 (기본값 "text" → 하위 호환)

### F4: 기억 추론 (Memory Reasoning)

**목표**: 기존 기억들을 조합하여 새로운 결론을 도출.

**핵심 API**:

```python
# 기억 조합 추론
insights = memory.reason("김 고객 상태")
# → ReasoningResult(
#     source_memories=[mem_a, mem_b, mem_c],
#     insights=["김 고객 이탈 위험 - 불만 제기 + 구독 만료 임박"],
#     contradictions=[],
#     confidence=0.78,
#     reasoning_chain=["mem_a → 불만", "mem_b → 만료", "combine → 이탈 위험"]
# )

# 모순 탐지
contradictions = memory.detect_contradictions()
# → [Contradiction(mem_a="오늘 비 옴", mem_b="오늘 맑음", severity=0.9)]
```

**구현 방식**:
1. 쿼리 관련 기억 수집 (recall + graph 이웃)
2. LLM에 기억 목록 전달 → 추론/인사이트 요청 (NullLLM 시 키워드 매칭 폴백)
3. 모순 탐지: 관련 기억 쌍을 LLM에 비교 요청 (NullLLM 시 부정어 패턴 탐지)
4. 추론 체인: 어떤 기억이 어떤 결론에 기여했는지 연결 기록

### F5: 벤치마크 & 성능 프로파일링

**목표**: 기억 시스템의 정량적 성능 측정.

**핵심 API**:

```python
# 종합 벤치마크
report = memory.benchmark(queries=1000, dataset="standard")
# → BenchmarkReport(
#     recall_at_5=0.92,
#     recall_at_10=0.97,
#     precision_at_5=0.85,
#     avg_store_latency_ms=5.2,
#     avg_recall_latency_ms=12.3,
#     avg_reorbit_latency_ms=8.1,
#     memory_usage_mb=45,
#     db_size_mb=12,
#     zone_distribution={0: 15, 1: 45, 2: 120, 3: 200, 4: 620}
# )

# CLI 벤치마크
# $ stellar-memory benchmark --queries 500 --output report.html
```

**구현 방식**:
1. StandardDataset: 내장 기억 세트 (small=100, medium=1000, large=10000)
2. store/recall/reorbit 각 단계 시간 측정 (time.perf_counter)
3. recall@k: 쿼리에 대해 상위 k개 결과 중 관련 기억 비율
4. HTML 보고서: 차트(존별 분포, 응답시간 히스토그램) 포함

---

## 9. Implementation Priority & Order

```
Phase 1: F5 (벤치마크) - 다른 기능 검증의 기반 도구
Phase 2: F1 (메타인지) - 핵심 혁신 기능
Phase 3: F3 (멀티모달) - 기억 데이터 모델 확장
Phase 4: F2 (자율 학습) - F5 벤치마크로 효과 측정 가능
Phase 5: F4 (추론) - F1 + F3 + 그래프 활용
Phase 6: 통합 테스트 + v1.0.0 릴리스 준비
```

**의존 관계**:

```
F5 (벤치마크) ← 모든 기능의 성능 측정 기반
  ↓
F1 (메타인지) ← 독립 구현 가능
  ↓
F3 (멀티모달) ← 기억 모델 확장
  ↓
F2 (자율 학습) ← F5 벤치마크로 효과 검증
  ↓
F4 (추론) ← F1 신뢰도 + F3 멀티모달 + 그래프 분석 활용
```

---

## 10. Success Metrics

| 지표 | P9 완료 시 목표 | 비고 |
|------|:--------------:|------|
| introspect 정확도 | 커버리지와 실제 기억 일치율 > 80% | 벤치마크 검증 |
| confidence와 정확도 상관 | 상관계수 > 0.7 | 통계 검증 |
| optimize 개선율 | recall@5 +5% 이상 향상 | 벤치마크 전후 비교 |
| 멀티모달 검색 정확도 | 코드/JSON 타입 필터 정확도 > 95% | 단위 테스트 |
| 추론 관련성 | 추론 결과의 소스 기억 관련도 > 70% | 수동 검증 |
| benchmark 재현성 | 동일 시드 → 동일 결과 | 반복 실행 검증 |
| 총 테스트 | 590+ (100% 통과) | pytest |
| 하위 호환 | 508개 기존 테스트 변경 없이 통과 | pytest |

---

## 11. v1.0.0 릴리스 체크리스트

P9 완료 시 v1.0.0 정식 릴리스를 위한 최종 점검:

- [ ] 모든 공개 API 안정화 (breaking change 없음 보장)
- [ ] CHANGELOG.md v1.0.0 섹션 작성
- [ ] README.md v1.0.0 배지 업데이트
- [ ] pyproject.toml version = "1.0.0"
- [ ] GitHub Release v1.0.0 태그
- [ ] PyPI 1.0.0 배포
- [ ] Docker 이미지 1.0.0 태그
- [ ] MkDocs 문서 v1.0.0 반영

---

## 12. Next Steps

1. [ ] 이 Plan 문서 리뷰 및 승인
2. [ ] Design 문서 작성 (`/pdca design stellar-memory-p9`)
3. [ ] 구현 시작 (`/pdca do stellar-memory-p9`)
4. [ ] Gap 분석 → Report → Archive

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-17 | 초안 - P9 고급 인지 & 자율 학습 Plan | Stellar Memory Team |
