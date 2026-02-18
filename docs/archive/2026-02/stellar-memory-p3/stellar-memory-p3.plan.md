# Plan: stellar-memory-p3 (AI Integration & Real-World Deployment)

## 1. Background

### 1.1 Previous Versions
- **MVP (v0.1.0)**: 5-zone celestial memory, memory function I(m), blackhole prevention, reorbit scheduler
- **P1 (v0.2.0)**: Semantic search, LLM importance evaluator, weight tuner, LLM adapter
- **P2 (v0.3.0)**: Memory consolidation, session management, export/import, performance optimization

### 1.2 Current State
- 18 source files, 16 test files, 147 tests all passing
- Core memory system is functionally complete but **not yet integrated into any AI system**
- The original goal was: "기존의 AI에 삽입해 보려고해" (insert into existing AI)

### 1.3 Problem Statement
v0.3.0은 라이브러리로서 기능은 완성되었지만, 실제 AI 시스템에서 사용하려면:
1. AI 도구(Claude Code, ChatGPT 등)가 직접 호출할 수 있는 **표준 인터페이스**가 없음
2. 여러 사용자/프로젝트를 구분하는 **격리된 메모리 공간**이 없음
3. 실시간 모니터링/디버깅을 위한 **이벤트 시스템**이 없음
4. 기억 간의 **연결 관계**를 추적할 수 없음 (사람의 연상 기억 부재)
5. 명령줄에서 기억을 관리할 수 있는 **CLI 도구**가 없음

## 2. Goals

**Target Version**: v0.4.0
**Theme**: AI Integration & Real-World Deployment

실제 AI에 stellar-memory를 연결하여, AI가 대화하면서 스스로 기억하고 활용하는 시스템을 완성한다.

## 3. Features

### F1: MCP Server (Model Context Protocol)
**Priority**: Critical
**Complexity**: High

MCP(Model Context Protocol) 서버를 구현하여, Claude Code 등의 AI 도구가 stellar-memory를 tool로 직접 사용할 수 있게 한다.

**MCP Tools to expose**:
| Tool | Description |
|------|-------------|
| `memory_store` | 새 기억 저장 (content, importance, metadata) |
| `memory_recall` | 질의 기반 기억 검색 |
| `memory_get` | ID로 특정 기억 조회 |
| `memory_forget` | 특정 기억 삭제 |
| `memory_stats` | 존별 통계 조회 |
| `memory_export` | 전체 기억 JSON 내보내기 |
| `memory_import` | JSON에서 기억 가져오기 |
| `session_start` | 세션 시작 |
| `session_end` | 세션 종료 (+ 자동 요약) |

**MCP Resources**:
| Resource | Description |
|----------|-------------|
| `memory://stats` | 실시간 통계 |
| `memory://zones` | 존 구성 정보 |

**Expected Outcome**: Claude Code에서 `stellar-memory` MCP 서버를 연결하면, AI가 대화 중 기억을 저장/검색/관리할 수 있음.

### F2: Event Hook System
**Priority**: High
**Complexity**: Medium

확장 가능한 이벤트/훅 시스템을 구현하여 기억 생명주기의 주요 이벤트에 콜백을 등록할 수 있게 한다.

**Events**:
| Event | Trigger | Payload |
|-------|---------|---------|
| `on_store` | 기억 저장 후 | MemoryItem |
| `on_recall` | 기억 검색 후 | list[MemoryItem], query |
| `on_forget` | 기억 삭제 후 | item_id |
| `on_reorbit` | 재배치 완료 후 | ReorbitResult |
| `on_consolidate` | 기억 병합 후 | existing, new_item |
| `on_zone_change` | 존 이동 시 | item, from_zone, to_zone |

**Use Cases**:
- 로깅/모니터링: 모든 이벤트를 JSON으로 기록
- 알림: Core zone 가득 찰 때 경고
- 분석: 기억 패턴 추적

### F3: Memory Namespace (Multi-tenant)
**Priority**: High
**Complexity**: Medium

여러 사용자/프로젝트의 기억을 독립적으로 관리할 수 있는 네임스페이스 시스템.

**Requirements**:
- 네임스페이스별 독립 DB 또는 테이블 프리픽스
- StellarMemory 인스턴스에 namespace 파라미터 추가
- MCP 서버에서 namespace를 tool 파라미터로 지원
- 네임스페이스 간 기억 이동(migration) 지원

**Examples**:
```python
# 프로젝트별 독립 기억 공간
work_memory = StellarMemory(config, namespace="work-project-a")
personal_memory = StellarMemory(config, namespace="personal")
```

### F4: Memory Graph (Associative Memory)
**Priority**: Medium
**Complexity**: Medium

기억 간 연결 관계를 추적하여 사람처럼 연상 기억(associative recall)을 구현한다.

**Edge Types**:
| Type | Description | Example |
|------|-------------|---------|
| `related_to` | 의미적 연관 | "Python" ↔ "Django" |
| `derived_from` | 파생 관계 | 요약 → 원본 |
| `contradicts` | 모순 관계 | 이전 정보 ↔ 업데이트된 정보 |
| `sequence` | 시간적 순서 | 대화 흐름 |

**Features**:
- 저장 시 자동 관계 탐지 (cosine similarity 기반)
- `recall_graph(item_id, depth=2)`: 연결된 기억 네트워크 탐색
- 관계 기반 보너스 점수: recall 시 연결된 기억에 가산점

### F5: CLI Tool
**Priority**: Medium
**Complexity**: Low

명령줄에서 stellar-memory를 관리할 수 있는 CLI 도구.

**Commands**:
```bash
stellar-memory store "오늘 회의에서 중요한 결정 사항"
stellar-memory recall "회의 결정"
stellar-memory stats
stellar-memory export --output memories.json
stellar-memory import --input memories.json
stellar-memory reorbit          # 수동 재배치
stellar-memory forget <id>
stellar-memory serve             # MCP 서버 시작
```

**Implementation**: Python `click` or `argparse`, entry_point in pyproject.toml

## 4. Feature Dependencies

```
F2 (Event Hook) ← 독립, 다른 기능의 기반
F3 (Namespace)  ← 독립, F1에서 활용
F1 (MCP Server) ← F2, F3 활용 (선택적)
F4 (Memory Graph) ← 독립
F5 (CLI)        ← F1 활용 (serve 명령)
```

**Implementation Order**:
1. F2 (Event Hook) - 다른 기능들의 확장성 기반
2. F3 (Namespace) - MCP 서버에서 필요
3. F1 (MCP Server) - 핵심 목표
4. F4 (Memory Graph) - 독립 기능
5. F5 (CLI) - MCP serve 포함

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| MCP SDK 의존성 추가 | 설치 복잡도 증가 | optional dependency로 관리 |
| Multi-tenant DB 성능 | 대규모 네임스페이스에서 느려질 수 있음 | 네임스페이스별 별도 DB 파일 옵션 |
| Memory Graph 복잡도 | 관계 폭발 가능 | max_edges_per_item 제한 |
| MCP 프로토콜 변경 | API 호환성 깨짐 | mcp SDK 버전 고정 |

## 6. Success Criteria

1. Claude Code에서 MCP 서버를 연결하여 기억 저장/검색이 실제로 동작
2. 이벤트 훅을 통해 모든 기억 활동을 모니터링 가능
3. 네임스페이스로 프로젝트별 독립 기억 관리 가능
4. 기억 간 연상 관계를 활용한 확장 검색 동작
5. CLI로 기본 관리 작업 수행 가능
6. 기존 147개 테스트 + 새 테스트 모두 통과

## 7. Estimated Scope

| Category | Count |
|----------|-------|
| New files | 5 (mcp_server.py, event_bus.py, namespace.py, memory_graph.py, cli.py) |
| Modified files | 5 (stellar.py, config.py, models.py, __init__.py, pyproject.toml) |
| New test files | 5 |
| Target test count | ~200+ |

## 8. Version Target

**v0.4.0** - AI Integration Release
- 기존 API 100% 하위 호환
- 새 optional dependencies: `mcp` (MCP server), `cli` (click)
- pyproject.toml `[project.scripts]` entry for CLI
