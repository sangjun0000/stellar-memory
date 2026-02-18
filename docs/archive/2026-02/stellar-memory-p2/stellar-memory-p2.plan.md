# Plan: stellar-memory-p2 (Production Readiness & Memory Intelligence)

## 1. Background

### Current State (v0.2.0)
- MVP: 5-zone celestial memory system with reorbit scheduler
- P1: Embedding, importance evaluator, LLM middleware, weight tuner
- 99 tests, 2,388 lines, 96% match rate

### P1 Gaps to Resolve
1. SqliteStorage semantic search loads ALL rows (performance)
2. WeightTuner not integrated into StellarMemory (convenience)

### Core Problem
v0.2.0은 기능적으로 완전하지만, 실제 사용에서는 다음 문제가 발생함:
- 비슷한 기억이 중복 저장됨 (예: "오늘 회의 3시" + "회의는 3시에 시작")
- 대화 세션 구분이 없어 모든 기억이 뒤섞임
- 기억 데이터 백업/복원 방법이 없음
- 기억 상태를 모니터링할 수 없음

## 2. Features

### F1: Memory Consolidation (기억 통합)
유사한 기억들을 자동으로 병합하여 중복 방지.

**동작 원리:**
- 새 기억 저장 시, 기존 기억들과 코사인 유사도 비교
- 유사도 > threshold(0.85)이면 기존 기억을 업데이트 (병합)
- 병합 시: content 합침, recall_count 합산, importance는 max 취함
- 주기적 consolidation도 reorbit과 함께 실행 가능

**기대 효과:** Core/Inner 존의 슬롯 낭비 방지, 더 풍부한 단일 기억

### F2: Session Context Manager (세션 관리)
대화 세션별로 기억을 구분하고 관리.

**동작 원리:**
- 각 기억에 `session_id` 메타데이터 자동 부여
- 세션별 recall scope 제한 가능 (현재 세션 우선, 전체 fallback)
- 세션 요약 (session summary) 자동 생성 - 세션 종료 시 핵심 기억만 추출
- StellarMemory에 `start_session()`, `end_session()` 메서드 추가

**기대 효과:** 대화 맥락 분리, 세션 종료 시 기억 정리

### F3: Export/Import & Snapshot (백업/복원)
기억 데이터의 직렬화/역직렬화.

**동작 원리:**
- `export_json()`: 전체 기억을 JSON으로 내보내기
- `import_json()`: JSON에서 기억 복원
- `snapshot()`: 특정 시점의 스냅샷 생성 (zone 분포 포함)
- 임베딩은 base64 인코딩으로 직렬화

**기대 효과:** 백업/복원, 기억 마이그레이션, 디버깅 지원

### F4: WeightTuner Integration + Feedback API (P1 Gap 해결)
WeightTuner를 StellarMemory에 직접 통합하고 피드백 API 제공.

**동작 원리:**
- `StellarMemory.provide_feedback(query, used_ids)`: 피드백 기록
- `StellarMemory.auto_tune()`: 가중치 자동 조정
- recall 결과에 result_ids 자동 추적
- reorbit 시 auto_tune 옵션

**기대 효과:** P1 Gap #2 해결, 사용자 피드백 루프 완성

### F5: Performance Optimization (성능 최적화)
SqliteStorage 시맨틱 검색 성능 개선.

**동작 원리:**
- Pre-filter: 키워드 매칭으로 후보군 축소 후 시맨틱 re-rank
- 캐시: 최근 쿼리 임베딩 LRU 캐시 (동일 쿼리 반복 방지)
- Batch reorbit: 대량 아이템 reorbit 시 batch 처리
- InMemoryStorage에 간단한 임베딩 인덱스 (정규화된 벡터의 내적 = 코사인)

**기대 효과:** P1 Gap #1 해결, 대규모 데이터셋에서의 검색 속도 향상

## 3. Priority & Dependencies

| Feature | Priority | Complexity | Dependencies |
|---------|----------|------------|--------------|
| F4: WeightTuner Integration | P0 (P1 Gap) | Low | None |
| F5: Performance Optimization | P0 (P1 Gap) | Medium | None |
| F1: Memory Consolidation | P1 | Medium | F5 (pre-filter 활용) |
| F2: Session Context Manager | P1 | Medium | None |
| F3: Export/Import | P2 | Low | None |

## 4. Implementation Order

```
Step 1: F4 - WeightTuner Integration (stellar.py + models.py)
Step 2: F5 - Performance Optimization (sqlite_storage.py + in_memory.py)
Step 3: F1 - Memory Consolidation (consolidator.py + stellar.py)
Step 4: F2 - Session Context Manager (session.py + stellar.py + llm_adapter.py)
Step 5: F3 - Export/Import (serializer.py + stellar.py)
Step 6: Tests (5 test files + existing test updates)
Step 7: pyproject.toml version bump to v0.3.0
```

## 5. Success Criteria

- [ ] 기존 99개 테스트 전부 통과 (하위 호환)
- [ ] P2 신규 테스트 40개 이상 추가
- [ ] SqliteStorage 시맨틱 검색: 1000개 아이템에서 < 100ms
- [ ] 중복 기억 병합률 > 80% (유사도 > 0.85인 쌍 기준)
- [ ] Export -> Import 라운드트립 데이터 무결성 100%
- [ ] Gap Analysis Match Rate >= 90%

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Consolidation이 의미적으로 다른 기억을 병합 | High | 유사도 threshold을 높게 설정 (0.85+), dry-run 모드 제공 |
| Session 종료 시 중요한 기억 손실 | Medium | 세션 요약은 별도 저장, 원본은 zone 이동만 |
| Export 파일이 너무 클 수 있음 | Low | 임베딩 제외 옵션, 존별 선택적 export |
| Pre-filter가 관련 결과를 누락 | Medium | 키워드 후보 수를 충분히 확보 (limit * 5) |

## 7. Non-Goals (P2 범위 외)

- 벡터 데이터베이스 연동 (ChromaDB, Pinecone 등) → P3
- REST API / CLI 인터페이스 → P3
- 멀티 유저 지원 → P3
- 기억 시각화 대시보드 → P3
- 다른 LLM 프로바이더 (OpenAI, Ollama) → P3

## 8. Version Target

**v0.3.0** - Production Readiness & Memory Intelligence
