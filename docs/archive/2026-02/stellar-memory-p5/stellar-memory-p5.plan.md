# Plan: stellar-memory-p5 (Advanced Intelligence & Scalability)

## 1. Background

### 1.1 Previous Versions
- **MVP (v0.1.0)**: 5-zone celestial memory, memory function I(m), blackhole prevention, reorbit scheduler
- **P1 (v0.2.0)**: Semantic search, LLM importance evaluator, weight tuner, LLM adapter
- **P2 (v0.3.0)**: Memory consolidation, session management, export/import, performance optimization
- **P3 (v0.4.0)**: MCP server, event hook system, namespace, memory graph, CLI
- **P4 (v0.5.0)**: Graph persistence, memory decay, event logger, recall boost, health check

### 1.2 Current State
- 26 source files, 26 test files, 237 tests all passing
- v0.5.0: 프로덕션 수준의 영속성, 자동 망각, 감사 로깅 완비
- MCP 서버 10개 도구 + CLI 10개 명령으로 AI/사용자 인터페이스 완성
- 설계 일치율 평균 98.2% (P1~P4)

### 1.3 Problem Statement
v0.5.0은 프로덕션 품질의 기억 관리 시스템이지만, **지능형 기억 시스템**으로 진화하려면:
1. 기억이 **텍스트 그대로** 저장됨 → AI가 요약/재구성하지 않아 저장 효율이 낮음
2. `auto_link`와 시맨틱 검색이 **O(n) 전체 스캔** → 1000+ 기억에서 성능 저하
3. 모든 기억이 **동일 속도로 망각** → 중요도에 따른 차등 망각 전략 없음
4. 기억 그래프가 쌓이지만 **분석/시각화 수단 없음** → 패턴 발견 불가
5. **Anthropic(Claude)만** 지원 → OpenAI/Ollama 등 대체 프로바이더 사용 불가

## 2. Goals

**Target Version**: v0.6.0
**Theme**: Advanced Intelligence & Scalability

기억의 질적 향상과 대규모 확장성을 확보하여, 단순 저장소에서 **지능형 기억 시스템**으로 진화한다.

### 2.1 Key Objectives
1. AI가 기억을 자동 요약하여 핵심만 빠르게 접근 가능하게 함
2. 벡터 인덱스로 O(n) → O(log n) 검색 성능 개선
3. 중요도 기반 차등 망각으로 사람의 기억에 더 가깝게 모사
4. 그래프 분석 도구로 기억 간 숨은 패턴 발견
5. 다중 LLM/Embedder 프로바이더 지원으로 유연한 배포

## 3. Features

### F1: Multi-Provider LLM/Embedder Support
**Priority**: Critical
**Complexity**: Medium
**Dependency**: None (기반 인프라, 다른 기능에서 활용)

Anthropic 외에 OpenAI, Ollama 등 다양한 LLM/임베딩 프로바이더를 지원한다.

**Requirements**:
- `ProviderConfig`: provider 이름, model, api_key_env, base_url 설정
- `ProviderRegistry`: 프로바이더별 어댑터 등록/조회 시스템
- `OpenAIAdapter`: GPT-4o 중요도 평가 + text-embedding-3-small 임베딩
- `OllamaAdapter`: 로컬 LLM으로 오프라인 운영 (llama3, nomic-embed-text)
- 기존 `LLMConfig.provider` 필드 활용하여 하위 호환 유지
- 기존 `EmbedderConfig`에 `provider` 필드 추가 (기본값 "sentence-transformers")
- 프로바이더별 optional dependency (openai, ollama 패키지)

**Interface**:
```python
# 기존 방식 (변경 없음)
config = StellarConfig(llm=LLMConfig(provider="anthropic"))

# 새로운 방식
config = StellarConfig(
    llm=LLMConfig(provider="openai", model="gpt-4o"),
    embedder=EmbedderConfig(provider="ollama", model="nomic-embed-text"),
)
```

**Files**:
- New: `stellar_memory/providers/__init__.py` - ProviderRegistry
- New: `stellar_memory/providers/openai_provider.py` - OpenAI LLM + Embedder
- New: `stellar_memory/providers/ollama_provider.py` - Ollama LLM + Embedder
- Modify: `stellar_memory/config.py` - EmbedderConfig에 provider 필드 추가
- Modify: `stellar_memory/llm_adapter.py` - ProviderRegistry 연동
- Modify: `stellar_memory/embedder.py` - ProviderRegistry 연동
- Modify: `stellar_memory/importance_evaluator.py` - 프로바이더 분기

### F2: Vector Index (Scalable Search)
**Priority**: High
**Complexity**: High
**Dependency**: None (독립, 하지만 F1과 병행 가능)

`auto_link`와 시맨틱 검색의 O(n) 전체 스캔을 벡터 인덱스로 최적화한다.

**Requirements**:
- `VectorIndexConfig`: 인덱스 방식 선택 (brute_force, ball_tree, faiss)
- `VectorIndex` 인터페이스: `add(id, vector)`, `remove(id)`, `search(vector, top_k) -> [(id, score)]`, `rebuild()`
- `BruteForceIndex`: 현재 방식 래핑 (하위 호환)
- `BallTreeIndex`: 내장 Ball-Tree (순수 Python, 외부 의존성 없음)
- `FaissIndex`: FAISS 기반 대규모(10만+) 인덱스 (optional dependency)
- `auto_link` 시 O(n) → O(log n) 개선
- recall 시맨틱 검색에도 인덱스 활용
- 인덱스 영속화: rebuild 시 전체 재구축 or 증분 업데이트
- config에서 `graph.auto_link_index` 설정 추가

**Performance Target**:
- 10,000개 기억에서 auto_link: < 100ms (현재 brute_force 대비 10x 개선)
- recall top-10 검색: < 50ms

**Files**:
- New: `stellar_memory/vector_index.py` - VectorIndex 인터페이스 + BruteForce + BallTree
- New: `stellar_memory/faiss_index.py` - FAISS 래퍼 (optional)
- Modify: `stellar_memory/config.py` - VectorIndexConfig 추가
- Modify: `stellar_memory/stellar.py` - VectorIndex 연동 (auto_link, recall)
- Modify: `stellar_memory/embedder.py` - 벡터 인덱스에 등록 연동

### F3: AI Memory Summarization
**Priority**: Critical
**Complexity**: Medium
**Dependency**: F1 (다중 프로바이더 LLM 활용)

기억을 저장할 때 AI가 자동으로 핵심만 추출하여 압축 저장한다.

**Requirements**:
- `SummarizationConfig`: enabled, min_length(100자 이상만 요약), model 선택
- `MemorySummarizer`: LLM을 사용하여 기억의 핵심 내용 추출
- 요약본은 별도 `MemoryItem`으로 Core/Inner에 저장
- 원본은 Outer 이하에 저장, `derived_from` 엣지로 자동 연결
- 요약 실패 시 원본 그대로 저장 (graceful degradation)
- LLM이 비활성화(NullAdapter)이면 요약 스킵
- MCP 도구 `memory_summarize`: 기존 기억의 수동 요약 요청
- CLI 명령 `summarize <id>`: 특정 기억 수동 요약
- 이벤트: `on_summarize` (요약 생성 시)

**Summarization Flow**:
```
store("오늘 오후 3시에 회의실B에서 프로젝트X 분기검토...")
  → 길이 >= min_length?
    → Yes: LLM에 요약 요청
      → 요약본 저장 (Core/Inner, importance=원본+0.1)
      → 원본 저장 (Outer, importance=원본)
      → derived_from 엣지 생성
    → No: 그대로 저장 (기존 동작)
```

**Files**:
- New: `stellar_memory/summarizer.py` - MemorySummarizer
- Modify: `stellar_memory/config.py` - SummarizationConfig 추가
- Modify: `stellar_memory/stellar.py` - store() 시 요약 파이프라인 연동
- Modify: `stellar_memory/mcp_server.py` - memory_summarize 도구 추가
- Modify: `stellar_memory/cli.py` - summarize 명령 추가
- Modify: `stellar_memory/event_bus.py` - on_summarize 이벤트 추가

### F4: Adaptive Decay (Importance-Based Forgetting)
**Priority**: High
**Complexity**: Low
**Dependency**: None (독립)

중요도에 따라 망각 속도를 차등 적용하여, 사람의 기억에 더 가깝게 모사한다.

**Requirements**:
- `AdaptiveDecayConfig`: enabled, decay_curve (linear, exponential, sigmoid), importance_weight (기본 1.0)
- 유효 망각일수 공식: `effective_days = base_decay_days * (0.5 + importance)`
  - 중요도 0.9 기억: 30 * 1.4 = 42일 후 강등
  - 중요도 0.3 기억: 30 * 0.8 = 24일 후 강등
  - 중요도 0.0 기억: 30 * 0.5 = 15일 후 강등
- 망각 곡선 옵션:
  - `linear`: 현재 방식 (시간에 비례)
  - `exponential`: 초기 빠른 망각, 후기 느린 망각
  - `sigmoid`: S자 곡선 (중간에 급격한 전환점)
- 존별 차등 망각률: 존이 가까울수록(Inner) 망각이 느림
- 망각 이력 추적: `decay_history` 테이블에 기록
- 이벤트: `on_adaptive_decay` (차등 망각 적용 시)
- 기존 `DecayConfig`와 하위 호환: `adaptive` 필드 추가

**Files**:
- New: `stellar_memory/adaptive_decay.py` - AdaptiveDecayManager
- Modify: `stellar_memory/config.py` - AdaptiveDecayConfig 추가, DecayConfig에 adaptive 필드
- Modify: `stellar_memory/decay_manager.py` - AdaptiveDecayManager 연동
- Modify: `stellar_memory/event_bus.py` - on_adaptive_decay 이벤트 추가
- Modify: `stellar_memory/event_logger.py` - adaptive_decay 이벤트 로깅

### F5: Graph Analytics
**Priority**: Medium
**Complexity**: Medium
**Dependency**: None (독립)

축적된 기억 그래프에서 패턴을 발견하고 분석하는 도구를 제공한다.

**Requirements**:
- `GraphAnalyzer` 클래스:
  - `communities()`: 커뮤니티 탐지 (Connected Components 기반, 순수 Python)
  - `centrality(top_k)`: 중심성 분석 (degree centrality)
  - `path(source_id, target_id)`: 최단 경로 탐색 (BFS)
  - `stats()`: 그래프 통계 (노드 수, 엣지 수, 평균 차수, 밀도)
  - `export_dot()`: DOT 형식 내보내기 (Graphviz 시각화)
  - `export_graphml()`: GraphML 형식 내보내기
- CLI 명령:
  - `graph stats`: 그래프 통계 출력
  - `graph communities`: 커뮤니티 목록 출력
  - `graph path <id1> <id2>`: 경로 탐색
  - `graph export [--format dot|graphml]`: 내보내기
- MCP 도구: `memory_graph_analyze` (stats, communities, centrality, path)
- `GraphAnalyticsConfig`: enabled, community_min_size (최소 커뮤니티 크기)

**Files**:
- New: `stellar_memory/graph_analyzer.py` - GraphAnalyzer
- Modify: `stellar_memory/config.py` - GraphAnalyticsConfig 추가
- Modify: `stellar_memory/stellar.py` - GraphAnalyzer 연동 (analyzer 속성)
- Modify: `stellar_memory/mcp_server.py` - memory_graph_analyze 도구 추가
- Modify: `stellar_memory/cli.py` - graph 서브커맨드 추가

## 4. Implementation Order

```
Step 1:  F1 Multi-Provider      (기반 인프라, F3에서 활용)
Step 2:  F2 Vector Index         (성능 기반, recall/auto_link에서 활용)
Step 3:  F3 AI Summarization     (F1 LLM + F2 인덱스 활용)
Step 4:  F4 Adaptive Decay       (독립, 기존 decay_manager 확장)
Step 5:  F5 Graph Analytics      (독립, 기존 graph 활용)
Step 6:  Integration + __init__.py + pyproject.toml version bump
Step 7:  Tests for F1 (10+ tests)
Step 8:  Tests for F2 (10+ tests)
Step 9:  Tests for F3 (10+ tests)
Step 10: Tests for F4 (8+ tests)
Step 11: Tests for F5 (10+ tests)
Step 12: MCP + CLI updates (F3 summarize, F5 graph commands)
Step 13: Full regression test (237 existing + 50+ new)
```

## 5. Files Overview

### 5.1 New Files (6~7)
| File | Feature | Description |
|------|---------|-------------|
| `stellar_memory/providers/__init__.py` | F1 | ProviderRegistry |
| `stellar_memory/providers/openai_provider.py` | F1 | OpenAI LLM + Embedder adapter |
| `stellar_memory/providers/ollama_provider.py` | F1 | Ollama LLM + Embedder adapter |
| `stellar_memory/vector_index.py` | F2 | VectorIndex + BruteForce + BallTree |
| `stellar_memory/summarizer.py` | F3 | MemorySummarizer |
| `stellar_memory/adaptive_decay.py` | F4 | AdaptiveDecayManager |
| `stellar_memory/graph_analyzer.py` | F5 | GraphAnalyzer |

### 5.2 Modified Files (8~10)
| File | Features | Changes |
|------|----------|---------|
| `config.py` | F1-F5 | 5개 Config 클래스 추가 |
| `stellar.py` | F1-F5 | provider, index, summarizer, adaptive decay, analyzer 통합 |
| `llm_adapter.py` | F1 | ProviderRegistry 연동 |
| `embedder.py` | F1, F2 | provider 필드 + VectorIndex 등록 |
| `importance_evaluator.py` | F1 | 프로바이더 분기 |
| `decay_manager.py` | F4 | AdaptiveDecayManager 연동 |
| `mcp_server.py` | F3, F5 | 2개 도구 추가 |
| `cli.py` | F3, F5 | summarize + graph 서브커맨드 |
| `event_bus.py` | F3, F4 | 2개 이벤트 추가 |
| `__init__.py` | All | 신규 export + version 0.6.0 |

### 5.3 New Test Files (5)
| File | Feature | Tests |
|------|---------|-------|
| `tests/test_providers.py` | F1 | 10+ |
| `tests/test_vector_index.py` | F2 | 10+ |
| `tests/test_summarizer.py` | F3 | 10+ |
| `tests/test_adaptive_decay.py` | F4 | 8+ |
| `tests/test_graph_analyzer.py` | F5 | 10+ |

## 6. Success Criteria

1. 다중 프로바이더: OpenAI + Ollama 어댑터 동작 (NullAdapter 폴백 포함)
2. 벡터 인덱스: 10,000개 기억에서 auto_link < 100ms
3. AI 요약: 100자 이상 기억의 자동 요약 생성 (LLM 활성 시)
4. 차등 망각: 중요도 0.9 기억의 존속 기간이 중요도 0.1 기억의 2배 이상
5. 그래프 분석: communities, centrality, path 기능 동작
6. 기존 237개 테스트 + 신규 50개 이상 모두 통과
7. 하위 호환성 100% 유지

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| FAISS 설치 어려움 (platform 이슈) | High | optional dependency + BallTree 기본 제공 |
| LLM 호출 비용 증가 (요약 시) | Medium | min_length 제한 + 요약 캐시 |
| OpenAI/Ollama API 변경 | Low | 어댑터 패턴으로 격리 |
| BallTree 순수 Python 성능 한계 | Medium | 10만+ 시 FAISS 권장 안내 |
| 요약 품질 불일치 (프로바이더별) | Low | 프롬프트 표준화 + 테스트 검증 |

## 8. Scope & Non-Scope

### In Scope
- 다중 LLM/Embedder 프로바이더 (OpenAI, Ollama)
- 벡터 인덱스 (BruteForce, BallTree, FAISS optional)
- AI 기반 기억 요약
- 중요도 기반 차등 망각
- 그래프 분석 도구 (communities, centrality, path, export)

### Out of Scope (P6 이후)
- 웹 UI / 대시보드
- 분산 스토리지 (Redis, PostgreSQL)
- 실시간 스트리밍 (WebSocket)
- 멀티모달 기억 (이미지, 오디오)
- 기억 암호화 / 접근 제어
