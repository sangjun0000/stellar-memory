# Plan: stellar-memory-p4 (Production Hardening & Persistence)

## 1. Background

### 1.1 Previous Versions
- **MVP (v0.1.0)**: 5-zone celestial memory, memory function I(m), blackhole prevention, reorbit scheduler
- **P1 (v0.2.0)**: Semantic search, LLM importance evaluator, weight tuner, LLM adapter
- **P2 (v0.3.0)**: Memory consolidation, session management, export/import, performance optimization
- **P3 (v0.4.0)**: MCP server, event hook system, namespace, memory graph, CLI

### 1.2 Current State
- 23 source files, 21 test files, 193 tests all passing
- MCP 서버를 통해 Claude Code에 연결 가능
- 이벤트 훅, 네임스페이스, 연상 그래프 구현 완료

### 1.3 Problem Statement
v0.4.0은 AI 통합이 완성되었지만, 실제 **프로덕션 환경**에서 사용하려면:
1. MemoryGraph가 **인메모리**여서 재시작 시 모든 연결 관계가 사라짐
2. 기억의 **자동 망각(decay)**이 없어서 오래된 기억이 영원히 남음
3. 이벤트 **로그 영속화**가 없어서 기억 활동 이력 추적 불가
4. MCP 서버의 **에러 처리, 검증, 로깅**이 최소 수준
5. 대규모 기억(1000+)에서의 **성능 최적화**가 부족 (`_auto_link`가 O(n) 전체 스캔)

## 2. Goals

**Target Version**: v0.5.0
**Theme**: Production Hardening & Persistence

안정적으로 장기 운영할 수 있는 프로덕션 품질의 시스템으로 강화한다.

## 3. Features

### F1: Graph Persistence (SQLite)
**Priority**: Critical
**Complexity**: Medium

MemoryGraph의 엣지를 SQLite에 영속화하여 재시작해도 연결 관계가 유지되도록 한다.

**Requirements**:
- 기존 `memory.db`에 `edges` 테이블 추가 (별도 DB 아닌 같은 DB)
- `MemoryGraph` → `PersistentMemoryGraph` 로 확장 (기존 인터페이스 유지)
- `add_edge`, `get_edges`, `remove_item` 모두 SQLite 통해 동작
- `get_related_ids` BFS는 메모리에서 처리 (성능)
- config로 in-memory / persistent 선택 가능

**Schema**:
```sql
CREATE TABLE IF NOT EXISTS edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL DEFAULT 'related_to',
    weight REAL NOT NULL DEFAULT 1.0,
    created_at REAL NOT NULL,
    PRIMARY KEY (source_id, target_id, edge_type)
);
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
```

### F2: Memory Decay (Auto-Forget)
**Priority**: High
**Complexity**: Medium

일정 기간 동안 리콜되지 않은 기억을 자동으로 더 먼 존으로 이동하거나 완전히 삭제하는 망각 시스템.

**Requirements**:
- `DecayConfig`: enabled, decay_days (기본 30일), auto_forget_days (기본 90일), min_zone_for_decay (기본 2)
- Reorbit 시 decay 검사: `last_recalled_at`이 decay_days 이상 지나면 1존 아래로 이동
- Cloud(zone 4)에서 auto_forget_days 경과 시 자동 삭제
- 이벤트: `on_decay` (존 이동), `on_auto_forget` (자동 삭제)
- Core/Inner zone(0, 1)의 기억은 decay 대상에서 제외 (min_zone_for_decay)

**Analogy**: 사람이 오래 떠올리지 않은 기억은 점점 흐려지다가 결국 잊어버리는 것과 같음

### F3: Event Logger (Persistent Audit Trail)
**Priority**: High
**Complexity**: Low

이벤트를 파일/SQLite에 영속적으로 기록하여 기억 활동의 감사 추적을 가능하게 한다.

**Requirements**:
- `EventLogger`: EventBus에 자동 등록되는 로거
- JSONL 형식으로 이벤트 기록 (한 줄 = 한 이벤트)
- 필드: timestamp, event_type, summary, item_id (해당 시)
- 로그 파일 경로: config에서 지정 (`event_log_path`)
- 로그 로테이션: 파일 크기 제한 (기본 10MB)
- CLI에 `stellar-memory logs` 명령 추가

### F4: Recall Boost (Graph-Enhanced Search)
**Priority**: Medium
**Complexity**: Medium

기억 검색(recall) 시 그래프 연결 관계를 활용하여 관련 기억에 보너스 점수를 부여한다.

**Requirements**:
- recall 결과에서 각 기억의 그래프 이웃도 후보에 포함
- 그래프 연결된 기억에 `graph_boost` 점수 가산 (기본 0.1)
- `RecallConfig`: graph_boost_enabled (기본 True), graph_boost_score (기본 0.1), graph_boost_depth (기본 1)
- 기존 recall 성능에 영향 최소화 (그래프 조회는 결과에 대해서만)

### F5: Health Check & Diagnostics
**Priority**: Medium
**Complexity**: Low

시스템 상태를 점검하고 진단 정보를 제공하는 헬스 체크 시스템.

**Requirements**:
- `health()` 메서드: 전체 시스템 상태 반환
- 체크 항목: DB 접속, 존 용량 사용률, 스케줄러 상태, 그래프 에지 수
- MCP 서버에 `memory_health` tool 추가
- CLI에 `stellar-memory health` 명령 추가
- 경고 조건: 존 용량 80% 이상, 스케줄러 미작동, DB 용량 과대

## 4. Feature Dependencies

```
F1 (Graph Persistence) ← 독립, F4에서 활용
F2 (Memory Decay)      ← 독립, reorbit 통합
F3 (Event Logger)      ← F2의 이벤트 기록에 활용
F4 (Recall Boost)      ← F1 활용 (영속 그래프)
F5 (Health Check)      ← 독립
```

**Implementation Order**:
1. F1 (Graph Persistence) - 그래프 영속화 기반
2. F2 (Memory Decay) - 망각 시스템
3. F3 (Event Logger) - 이벤트 영속 기록
4. F4 (Recall Boost) - 그래프 기반 검색 강화
5. F5 (Health Check) - 진단 도구

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQLite edges 테이블 마이그레이션 | 기존 DB와 호환성 | CREATE IF NOT EXISTS로 안전 추가 |
| Auto-forget 데이터 손실 | 중요 기억 삭제 가능 | min_zone_for_decay로 Core/Inner 보호 |
| Event Logger I/O 부하 | 높은 빈도 이벤트 시 성능 | 버퍼링 + 비동기 쓰기 고려 |
| Recall Boost 복잡도 | recall 성능 저하 가능 | 결과에 대해서만 그래프 조회 (전체 스캔 아님) |

## 6. Success Criteria

1. 그래프 엣지가 재시작 후에도 유지됨
2. 30일 미리콜 기억이 자동으로 외곽 존으로 이동
3. 모든 기억 활동이 JSONL 로그에 기록됨
4. 그래프 연결 기억이 recall 결과에서 우선 순위 향상
5. health 명령으로 시스템 상태 진단 가능
6. 기존 193개 테스트 + 새 테스트 모두 통과

## 7. Estimated Scope

| Category | Count |
|----------|-------|
| New files | 3 (persistent_graph.py, decay_manager.py, event_logger.py) |
| Modified files | 7 (stellar.py, config.py, models.py, mcp_server.py, cli.py, __init__.py, pyproject.toml) |
| New test files | 5 |
| Target test count | ~240+ |

## 8. Version Target

**v0.5.0** - Production Hardening Release
- 기존 API 100% 하위 호환
- 새 기능은 config로 on/off 가능 (default: enabled)
- MemoryGraph 인터페이스 유지 (PersistentMemoryGraph는 동일 인터페이스 구현)
