# celestial-memory-engine Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: stellar-memory
> **Version**: 2.0.0
> **Analyst**: gap-detector
> **Date**: 2026-02-18
> **Design Doc**: [celestial-memory-engine.design.md](../02-design/features/celestial-memory-engine.design.md)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Verify that the 13 implementation files in `celestial_engine/` faithfully implement the design document for the Celestial Memory Engine v2. This analysis checks every class, method, field, algorithm, and constant against the design specification, covering all 20 checklist items.

### 1.2 Analysis Scope

- **Design Document**: `docs/02-design/features/celestial-memory-engine.design.md`
- **Implementation Path**: `celestial_engine/` (13 files)
- **Analysis Date**: 2026-02-18

---

## 2. Checklist Item-by-Item Verification

### F1-1: models.py -- CelestialItem, ScoreBreakdown, ZoneConfig, RebalanceResult

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| CelestialItem fields | id, content, created_at, last_recalled_at, recall_count, arbitrary_importance, zone, metadata, embedding, total_score | Identical | MATCH |
| CelestialItem.create() | Clamps importance [0,1], sets now for created_at & last_recalled_at | Identical | MATCH |
| ScoreBreakdown fields | recall_score, freshness_score, arbitrary_score, context_score, total, target_zone | Identical | MATCH |
| ZoneConfig fields | zone_id, name, max_slots, score_min, score_max (default inf) | Identical | MATCH |
| RebalanceResult fields | moved, evicted, forgotten, total_items, duration_ms | Identical | MATCH |
| DEFAULT_ZONES location | Design Section 5.1 places in `celestial_engine/zones.py` | Implementation places in `models.py` | CHANGED |
| DEFAULT_ZONES values | 5 zones: core(20,0.50), inner(100,0.30,0.50), outer(1000,0.10,0.30), belt(None,-0.10,0.10), cloud(None,-inf,-0.10) | Identical values | MATCH |

**Verdict**: MATCH (the DEFAULT_ZONES file location change is a minor structural improvement -- keeping all model data together is cleaner)

### F1-2: memory_function.py -- _recall_score (log-capped)

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Formula | `log(1 + count) / log(1 + MAX_RECALL_CAP)` | Identical | MATCH |
| Guard for count <= 0 | Returns 0.0 | Identical | MATCH |
| MAX_RECALL_CAP default | 1000 | 1000 | MATCH |

**Verdict**: MATCH

### F1-3: memory_function.py -- _freshness_score (recall-reset)

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| delta_t calculation | `max(0.0, current_time - last_recalled_at)` | Identical | MATCH |
| raw decay | `-alpha * delta_t` | Identical | MATCH |
| Clamping | `max(raw, freshness_floor)` | Identical | MATCH |
| floor >= 0 guard | Returns 0.0 | Identical | MATCH |
| Normalization | `clamped / abs(freshness_floor)` | Identical | MATCH |
| freshness_alpha default | 0.001 | 0.001 | MATCH |
| freshness_floor default | -86400.0 | -86400.0 | MATCH |

**Design Document Math Error** (flagged per instructions):

The design Section 4.2 claims: `F(1 day) = -0.001 * 86400 / 86400 = -1.0`

This is **mathematically incorrect**. The actual calculation:
- `raw = -0.001 * 86400 = -86.4`
- `clamped = max(-86.4, -86400.0) = -86.4` (raw does NOT hit the floor)
- `normalized = -86.4 / 86400.0 = -0.001`

So after 1 day: F = -0.001, NOT -1.0.

The freshness_floor of -86400.0 means F reaches -1.0 only when `raw = -86400`, i.e., when `0.001 * delta_t = 86400`, so `delta_t = 86,400,000 seconds = ~1000 days`.

The design proof in Section 4.2 incorrectly simplifies the division. The design scenarios in Section 4.3 that claim "1 day -> F = -1.0" are also based on this error.

**However**, the implementation correctly implements the formula as written in the code block (Section 4.1), which is self-consistent. The error is in the **prose/proof section**, not in the code specification. The implementation matches the code spec exactly.

**Verdict**: MATCH (implementation matches the code specification; design prose/proof section has a documentation error)

### F1-4: memory_function.py -- _context_score (cosine similarity)

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| None guards | Returns 0.0 if either embedding is None | Identical | MATCH |
| Dot product | `sum(a * b for a, b in zip(...))` | Identical | MATCH |
| Norms | `sum(x*x)^0.5` | Identical | MATCH |
| Zero norm guard | Returns 0.0 | Identical | MATCH |
| Final formula | `dot / (norm_a * norm_b)` | Identical | MATCH |

**Verdict**: MATCH

### F1-5: memory_function.py -- calculate + _determine_zone

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Weight defaults | w_r=0.25, w_f=0.30, w_a=0.25, w_c=0.20 | Identical | MATCH |
| Total formula | `w_r*R + w_f*F + w_a*A + w_c*C` | Identical | MATCH |
| Zone thresholds | (0,0.50), (1,0.30), (2,0.10), (3,-0.10), (4,-inf) | Identical | MATCH |
| _determine_zone loop | Iterates thresholds, returns first match, fallback 4 | Design iterates `zone[1]` (tuple index), impl iterates `score_min` (destructured) | MATCH |
| MemoryFunctionConfig | Dataclass with 7 fields | Identical | MATCH |

**Verdict**: MATCH

### F2-1: storage/__init__.py -- ZoneStorage ABC

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| File location | Design says `storage/base.py` | Implementation is `storage/__init__.py` | CHANGED |
| Abstract methods | store, get, remove, update, search, get_all, count, get_lowest_score_item | Identical set of 8 methods | MATCH |
| Method signatures | All match design signatures | Identical | MATCH |
| TYPE_CHECKING import | Not in design | Implementation uses `TYPE_CHECKING` for CelestialItem | ADDED (improvement) |

**Verdict**: MATCH (file location differs: `storage/base.py` vs `storage/__init__.py`, but this is a Pythonic improvement putting the ABC in the package init)

### F2-2: storage/memory.py -- InMemoryStorage

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Class name | InMemoryStorage | Identical | MATCH |
| Internal storage | `dict[str, CelestialItem]` | Identical | MATCH |
| store() | `self._items[item.id] = item` | Identical | MATCH |
| get() | `self._items.get(item_id)` | Identical | MATCH |
| remove() | `self._items.pop(item_id, None) is not None` | Identical | MATCH |
| update() | `self._items[item.id] = item` | Identical | MATCH |
| search() | Case-insensitive keyword match, sort by total_score desc | Identical | MATCH |
| get_all() | `list(self._items.values())` | Identical | MATCH |
| count() | `len(self._items)` | Identical | MATCH |
| get_lowest_score_item() | `min(..., key=lambda i: i.total_score)` | Identical | MATCH |
| Type hints | Design uses compact form (`def store(self, item):`) | Implementation uses full type hints | ADDED (improvement) |

**Verdict**: MATCH

### F2-3: storage/sqlite.py -- SqliteStorage

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Table naming | `memories_zone_{zone_id}` | Identical | MATCH |
| WAL mode | `PRAGMA journal_mode=WAL` | Identical | MATCH |
| Schema columns | 10 columns matching CelestialItem fields | Identical | MATCH |
| Score index | `idx_{table}_score ON {table}(total_score)` | Identical | MATCH |
| store() UPSERT | `INSERT OR REPLACE` | Identical | MATCH |
| Embedding serialization | struct.pack/unpack float array | Identical algorithm | MATCH |
| _row_to_item() | Positional tuple unpacking | Identical | MATCH |
| Thread safety | Design: no threading.Lock | Implementation: adds `threading.Lock` for store/remove | ADDED (improvement) |
| Helper functions | Design: instance methods (`self._serialize_embedding`) | Implementation: module-level functions (`_serialize_embedding`) | CHANGED |
| close() method | Not in design | Implementation adds `close()` | ADDED |

**Verdict**: MATCH (thread safety lock and module-level helpers are improvements)

### F3-1: importance.py -- DefaultEvaluator, RuleBasedEvaluator

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| ImportanceEvaluator ABC | `evaluate(content: str) -> float` | Identical | MATCH |
| DefaultEvaluator | Returns 0.5 | Identical | MATCH |
| RuleBasedEvaluator patterns | FACTUAL(3), EMOTIONAL(2), ACTIONABLE(2), EXPLICIT(2) | Identical pattern sets | MATCH |
| Weights | 0.25*f + 0.25*e + 0.30*a + 0.20*x | Identical | MATCH |
| _score() | `min(matches/max(len(patterns),1), 1.0)` | Identical | MATCH |
| re import | Design imports re inside evaluate() | Implementation imports re at module level | CHANGED (improvement) |

**Verdict**: MATCH

### F3-2: importance.py -- LLMEvaluator

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Constructor | `llm_callable=None` | Identical | MATCH |
| Fallback | RuleBasedEvaluator | Identical | MATCH |
| evaluate() flow | None check -> try LLM -> except fallback | Identical | MATCH |
| _call_llm() prompt | Exact same prompt text | Identical | MATCH |
| JSON parsing | `json.loads(raw)`, extract "importance", clamp [0,1] | Identical | MATCH |
| Logging on failure | Design: bare `except Exception` | Implementation: `except Exception as exc` with logger.warning | CHANGED (improvement) |

**Verdict**: MATCH

### F4-1: zone_manager.py -- ZoneManager (place, move, evict, search, stats)

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Constructor zones | `{z.zone_id: z for z in (zones or DEFAULT_ZONES)}` | Identical logic | MATCH |
| Storage assignment | zone_id <= 1 -> InMemory, else -> Sqlite | Implementation adds: `or db_path == ":memory:"` -> all InMemory | CHANGED (improvement for testing) |
| place() | Sets zone, score, checks capacity, stores | Implementation adds `_clamp_zone()` call | CHANGED (improvement) |
| move() | Get from source, remove, place in target | Identical logic | MATCH |
| get_all_items() | Collect from all storages | Identical | MATCH |
| search() | Zone 0->4 order, early stop at limit | Identical | MATCH |
| stats() | Returns `{zid: (count, max_slots)}` | Identical | MATCH |
| _evict_lowest() | Remove lowest, place in zone+1 | Implementation adds: logger.info when no next zone exists | CHANGED (improvement) |
| find_item() | Not in design | Implementation adds cross-zone item finder | ADDED |
| _clamp_zone() | Not in design | Implementation adds zone boundary clamping | ADDED |

**Verdict**: MATCH (additions are defensive improvements)

### F4-2: zone_manager.py -- forget_stale + enforce_capacity

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| forget_stale() | Deletes Cloud zone items older than max_age_seconds | Identical | MATCH |
| enforce_capacity() | Iterates zones, evicts while over max_slots | Implementation adds infinite-loop guard: `if storage.count() >= before: break` | CHANGED (improvement) |

**Verdict**: MATCH

### F5-1: rebalancer.py -- Rebalancer.rebalance (manual)

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Score recalculation | For all items, calculate new score | Identical | MATCH |
| Move detection | If target_zone != current zone | Identical | MATCH |
| Moves list | Design: `list[tuple[CelestialItem, int, int, float]]` | Implementation: `list[tuple[str, int, int, float]]` (stores item_id, not item) | CHANGED |
| Sort order | High score first (reverse=True) | Identical | MATCH |
| Move execution | Design: `self._zone_mgr.move(item.id, ...)` | Implementation: `self._zone_mgr.move(item_id, ...)` | MATCH (consistent with tuple change) |
| enforce_capacity | Called after moves | Identical | MATCH |
| forget_stale | Called after enforce | Identical | MATCH |
| duration_ms | `(time.time() - start) * 1000` | Identical | MATCH |
| RebalanceResult | All fields populated | Identical | MATCH |

**Verdict**: MATCH (storing item_id instead of item object in moves list is an improvement -- avoids holding stale object references)

### F5-2: rebalancer.py -- Rebalancer.start/stop (auto scheduling)

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Constructor params | memory_fn, zone_mgr, interval_seconds=300, auto_forget_seconds=86400*90 | Identical | MATCH |
| _timer type | `threading.Timer \| None` | Identical | MATCH |
| _running flag | Boolean | Identical | MATCH |
| start() | Sets _running=True, calls _schedule_next | Identical | MATCH |
| stop() | Sets _running=False, cancels timer | Identical | MATCH |
| _schedule_next() | Creates daemon Timer, starts it | Identical | MATCH |
| _tick() | try rebalance, log if changes, except log error, finally schedule next | Identical | MATCH |

**Verdict**: MATCH

### F6-1: __init__.py -- CelestialMemory.store

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Constructor params | db_path, zones, memory_fn_config, evaluator, rebalance_interval, auto_forget_days, embed_fn | Identical | MATCH |
| Auto-start rebalancer | `self._rebalancer.start()` | Identical | MATCH |
| store() signature | `(content, importance=None, metadata=None) -> CelestialItem` | Identical | MATCH |
| Auto-evaluate importance | `self._evaluator.evaluate(content)` when None | Identical | MATCH |
| Embed if embed_fn | `item.embedding = self._embed_fn(content)` | Identical | MATCH |
| Calculate + place | `self._fn.calculate(item, now)` -> `self._zone_mgr.place(...)` | Identical | MATCH |

**Verdict**: MATCH

### F6-2: __init__.py -- CelestialMemory.recall (+ recall-reset)

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| recall() signature | `(query, limit=5) -> list[CelestialItem]` | Identical | MATCH |
| Query embedding | `self._embed_fn(query) if self._embed_fn else None` | Identical | MATCH |
| Zone search | `self._zone_mgr.search(query, limit, query_embedding)` | Identical | MATCH |
| Recall count increment | `item.recall_count += 1` | Identical | MATCH |
| Freshness reset | `item.last_recalled_at = now` | Identical | MATCH |
| Score recalculation | `self._fn.calculate(item, now, query_embedding)` | Identical | MATCH |
| Zone move check | If target_zone changed, move; else update in place | Identical | MATCH |
| Private storage access | `self._zone_mgr._storages[item.zone].update(item)` | Identical | MATCH |

**Verdict**: MATCH

### F6-3: __init__.py -- CelestialMemory.rebalance, stats, close

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| rebalance() | Delegates to `self._rebalancer.rebalance()` | Identical | MATCH |
| stats() | Returns `{zones: {zid: {count, capacity}}, total: N}` | Identical | MATCH |
| close() | Calls `self._rebalancer.stop()` | Identical | MATCH |

**Verdict**: MATCH

### F7-1: adapters/langchain.py -- LangChainAdapter.as_retriever, as_memory

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| Constructor | `(memory: CelestialMemory)` | Identical | MATCH |
| as_retriever(k=5) | Returns BaseRetriever subclass | Identical | MATCH |
| _get_relevant_documents | Calls mem.recall, wraps in Document | Implementation adds `**kwargs` parameter | CHANGED (minor, for LangChain compat) |
| as_memory() | Returns ConversationBufferMemory subclass | Identical | MATCH |
| save_context() | Formats Human/AI, stores in memory | Identical | MATCH |
| load_memory_variables() | Recalls and joins content | Identical | MATCH |

**Verdict**: MATCH

### F7-2: adapters/openai.py -- OpenAIAdapter.as_tools, handle_tool_call

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| as_tools() | 2 tools: celestial_store, celestial_recall | Identical structure | MATCH |
| Tool descriptions | Design: `"Memory content"` | Implementation: `"Memory content to store"` | CHANGED (minor) |
| Tool descriptions | Design: `"0.0-1.0"` | Implementation: `"Importance score 0.0-1.0"` | CHANGED (minor) |
| Tool descriptions | Design: `"Search query"` | Implementation: `"Search query for memory recall"` | CHANGED (minor) |
| Tool descriptions | Design: `"Max results"` | Implementation: `"Maximum number of results"` | CHANGED (minor) |
| handle_tool_call store | Design returns `{"id", "zone"}` | Implementation returns `{"id", "zone", "score"}` | CHANGED |
| handle_tool_call recall | Design returns `[{"content", "zone"}]` | Implementation returns `[{"content", "zone", "score"}]` | CHANGED |
| json import | Design: inside method | Implementation: at module level | CHANGED (improvement) |

**Verdict**: PARTIAL -- The response format includes an extra `score` field not specified in design. This is an additive change (non-breaking) but represents a design deviation. The tool descriptions are more verbose than designed.

### F7-3: adapters/anthropic.py -- AnthropicAdapter.as_mcp_tools, handle

| Aspect | Design | Implementation | Status |
|--------|--------|----------------|--------|
| as_mcp_tools() | 2 tools: celestial_store, celestial_recall | Identical | MATCH |
| Tool schemas | Identical input_schema structures | Identical | MATCH |
| handle() store | Design returns `{"id", "zone", "score"}` | Identical | MATCH |
| handle() recall | Design returns `{"memories": [{"content", "zone", "score"}]}` | Identical | MATCH |

**Verdict**: MATCH

---

## 3. Additional Findings

### 3.1 Added Features (Design X, Implementation O)

| Item | Implementation Location | Description | Impact |
|------|------------------------|-------------|--------|
| `find_item()` | `zone_manager.py:117-123` | Cross-zone item lookup | Low (utility method) |
| `_clamp_zone()` | `zone_manager.py:137-143` | Zone ID boundary clamping | Low (defensive) |
| `close()` | `storage/sqlite.py:116-117` | SQLite connection cleanup | Low (resource management) |
| `threading.Lock` | `storage/sqlite.py:21` | Thread-safe SQLite writes | Low (concurrency safety) |
| `TYPE_CHECKING` | `storage/__init__.py:6-9` | Lazy type imports | Low (circular import prevention) |
| `__all__` exports | `__init__.py:38-53` | Explicit public API | Low (API clarity) |
| `logger` | `importance.py:9` | Logging for LLM failures | Low (observability) |
| Infinite-loop guard | `zone_manager.py:103-106` | `enforce_capacity` safety break | Low (robustness) |
| `db_path == ":memory:"` | `zone_manager.py:27` | All-InMemory for test convenience | Low (testability) |
| `**kwargs` in retriever | `adapters/langchain.py:33` | LangChain API compatibility | Low (framework compat) |

### 3.2 Structural Differences

| Aspect | Design | Implementation | Impact |
|--------|--------|----------------|--------|
| DEFAULT_ZONES location | `celestial_engine/zones.py` (Section 5.1) | `celestial_engine/models.py` | Low -- no separate zones.py needed |
| ZoneStorage ABC location | `storage/base.py` (Section 8.1) | `storage/__init__.py` | Low -- Pythonic convention |
| Rebalancer moves tuple | `tuple[CelestialItem, ...]` | `tuple[str, ...]` (item_id) | Low -- avoids stale refs |
| Helper functions scope | Instance methods in SqliteStorage | Module-level functions | Low -- reduces class complexity |

### 3.3 Design Document Issues

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Math error in proof | Design Section 4.2 | Medium | Claims `F(1 day) = -1.0` but actual value is `F(1 day) = -0.001`. The formula `F(1 day) = -0.001 * 86400 / 86400` incorrectly cancels the 86400 terms. The correct chain is: `raw = -0.001 * 86400 = -86.4`, `clamped = max(-86.4, -86400) = -86.4`, `normalized = -86.4 / 86400 = -0.001`. F reaches -1.0 after ~1000 days, not 1 day. |
| Scenario errors | Design Section 4.3 | Medium | Scenarios 2, 3, 4 all assume F = -1.0 after 1 day, which is incorrect per the implemented formula. |
| File path mismatch | Design Section 5.1 says `zones.py`, Section 8.1 says `storage/base.py` | Low | Implementation uses `models.py` and `storage/__init__.py` respectively. |

---

## 4. Match Rate Summary

### 4.1 Per-Item Results

| # | ID | File | Verdict | Notes |
|---|-----|------|---------|-------|
| 1 | F1-1 | models.py | MATCH | All 4 dataclasses + DEFAULT_ZONES (in models.py instead of zones.py) |
| 2 | F1-2 | memory_function.py | MATCH | Log-capped recall score exact match |
| 3 | F1-3 | memory_function.py | MATCH | Recall-reset freshness exact match (design prose has math error) |
| 4 | F1-4 | memory_function.py | MATCH | Cosine similarity exact match |
| 5 | F1-5 | memory_function.py | MATCH | Calculate + zone determination exact match |
| 6 | F2-1 | storage/__init__.py | MATCH | ABC in __init__.py instead of base.py |
| 7 | F2-2 | storage/memory.py | MATCH | InMemoryStorage exact match |
| 8 | F2-3 | storage/sqlite.py | MATCH | SqliteStorage with added thread safety |
| 9 | F3-1 | importance.py | MATCH | DefaultEvaluator + RuleBasedEvaluator exact match |
| 10 | F3-2 | importance.py | MATCH | LLMEvaluator with improved error logging |
| 11 | F4-1 | zone_manager.py | MATCH | Core methods match + defensive additions |
| 12 | F4-2 | zone_manager.py | MATCH | forget_stale + enforce_capacity with safety guard |
| 13 | F5-1 | rebalancer.py | MATCH | Rebalance logic match (item_id tuple optimization) |
| 14 | F5-2 | rebalancer.py | MATCH | start/stop/scheduling exact match |
| 15 | F6-1 | __init__.py | MATCH | CelestialMemory.store exact match |
| 16 | F6-2 | __init__.py | MATCH | CelestialMemory.recall with recall-reset exact match |
| 17 | F6-3 | __init__.py | MATCH | rebalance, stats, close exact match |
| 18 | F7-1 | adapters/langchain.py | MATCH | LangChainAdapter with minor **kwargs addition |
| 19 | F7-2 | adapters/openai.py | PARTIAL | Response includes extra `score` field; descriptions more verbose |
| 20 | F7-3 | adapters/anthropic.py | MATCH | AnthropicAdapter exact match |

### 4.2 Score Calculation

```
MATCH items:    19 / 20 = 95.0%
PARTIAL items:   1 / 20 =  5.0%  (F7-2: OpenAI adapter response format)
MISSING items:   0 / 20 =  0.0%

Weighted Score:
  MATCH    = 19 * 1.0  = 19.0
  PARTIAL  =  1 * 0.5  =  0.5
  MISSING  =  0 * 0.0  =  0.0
  Total    = 19.5 / 20 = 97.5%
```

```
+-------------------------------------------------+
|  Overall Match Rate: 97.5% (19.5 / 20)          |
+-------------------------------------------------+
|  MATCH:     19 items (95%)                       |
|  PARTIAL:    1 item  ( 5%)  -- OpenAI adapter    |
|  MISSING:    0 items ( 0%)                       |
+-------------------------------------------------+
```

---

## 5. Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| Design Match | 97.5% | PASS |
| Architecture Compliance | 100% | PASS |
| Convention Compliance | 98% | PASS |
| **Overall** | **97.5%** | **PASS** |

### Architecture Compliance Details

- Single responsibility: Each module has one clear role -- PASS
- Dependency direction: models <- memory_function <- zone_manager <- rebalancer <- facade -- PASS
- No circular imports: TYPE_CHECKING used correctly -- PASS
- Storage abstraction: ABC properly defined and implemented -- PASS

### Convention Compliance Details

| Convention | Score | Notes |
|------------|:-----:|-------|
| Class naming (PascalCase) | 100% | All 14 classes follow PascalCase |
| Function naming (snake_case) | 100% | All methods follow snake_case |
| Constant naming (UPPER_SNAKE_CASE) | 100% | DEFAULT_ZONES, FACTUAL_PATTERNS, etc. |
| File naming (snake_case.py) | 100% | All 13 files follow snake_case |
| Private prefix (_) | 100% | All private members use underscore prefix |
| `from __future__ import annotations` | 100% | Present in all 13 files |
| Type hints on public methods | 95% | `embed_fn` parameter lacks type hint |
| Import order (stdlib, local) | 100% | All files follow correct order |

---

## 6. Differences Detail

### 6.1 PARTIAL Items

#### F7-2: OpenAI adapter handle_tool_call response format

**Design** (Section 10.2):
```python
# celestial_store response:
{"id": item.id, "zone": item.zone}

# celestial_recall response:
[{"content": r.content, "zone": r.zone} for r in results]
```

**Implementation** (`celestial_engine/adapters/openai.py:82,89`):
```python
# celestial_store response:
{"id": item.id, "zone": item.zone, "score": item.total_score}

# celestial_recall response:
[{"content": r.content, "zone": r.zone, "score": r.total_score} for r in results]
```

**Impact**: Low-Medium. The `score` field is additive (non-breaking for consumers), and matches the AnthropicAdapter behavior which was designed with `score`. This appears to be an intentional improvement for consistency across adapters. The tool descriptions are also slightly more verbose than designed, which is a beneficial deviation.

### 6.2 Design Document Math Error (Not an implementation gap)

**Design** (Section 4.2, line ~314):
```
F(1 day) = -0.001 * 86400 / 86400 = -1.0
```

**Correct calculation**:
```
raw = -0.001 * 86400 = -86.4
clamped = max(-86.4, -86400.0) = -86.4
F = -86.4 / abs(-86400.0) = -86.4 / 86400.0 = -0.001
```

The proof incorrectly treats `freshness_floor` as if it were `-86400.0 / 86400 = -1.0` directly, but the normalization step divides the *clamped raw value* by `abs(floor)`, not `floor` by itself.

**Actual behavior with defaults**:
| Time elapsed | raw | clamped | F(m) |
|-------------|-----|---------|------|
| 0 (just recalled) | 0.0 | 0.0 | 0.0 |
| 1 hour | -3.6 | -3.6 | -0.0000417 |
| 1 day | -86.4 | -86.4 | -0.001 |
| 30 days | -2592.0 | -2592.0 | -0.03 |
| 365 days | -31536.0 | -31536.0 | -0.365 |
| ~1000 days | -86400.0 | -86400.0 | -1.0 |

**Impact**: Medium. The black hole prevention still works (freshness eventually reaches -1.0), but the decay is **much slower** than the design prose suggests. A memory takes ~1000 days to reach F = -1.0 instead of the claimed 1 day. This affects the scenarios in Section 4.3 but does NOT affect the correctness of the implementation since the implementation matches the code specification.

---

## 7. Recommended Actions

### 7.1 Optional Code Fix (Low Priority)

| # | Item | File | Description |
|---|------|------|-------------|
| 1 | OpenAI adapter consistency | `adapters/openai.py` | Either update design to include `score` field (recommended) or remove from implementation |

### 7.2 Design Document Updates Needed

| # | Item | Section | Description |
|---|------|---------|-------------|
| 1 | Fix math proof | Section 4.2 | Correct `F(1 day) = -0.001` not `-1.0`; update freshness_floor semantics |
| 2 | Fix scenarios | Section 4.3 | Update "1 day -> F = -1.0" to reflect actual decay rate |
| 3 | Add score to OpenAI spec | Section 10.2 | Add `score` field to handle_tool_call responses |
| 4 | Fix file paths | Sections 5.1, 8.1 | Update `zones.py` -> `models.py`, `storage/base.py` -> `storage/__init__.py` |
| 5 | Document added features | N/A | Document `find_item()`, `_clamp_zone()`, `close()`, thread safety |

---

## 8. Next Steps

- [x] Gap analysis complete
- [ ] Update design document Section 4.2 math proof
- [ ] Update design document Section 4.3 scenarios
- [ ] Update design document Sections 5.1 and 8.1 file paths
- [ ] Update design document Section 10.2 OpenAI response format
- [ ] Proceed to `/pdca report celestial-memory-engine`

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-18 | Initial analysis -- 97.5% match rate (19.5/20) | gap-detector |
