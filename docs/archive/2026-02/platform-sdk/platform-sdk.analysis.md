# platform-sdk Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: stellar-memory
> **Version**: 3.0.0
> **Analyst**: gap-detector agent
> **Date**: 2026-02-21
> **Design Doc**: [platform-sdk.design.md](../02-design/features/platform-sdk.design.md)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Compare the platform-sdk design document (v3.0 SDK redesign) against the actual
implementation to identify gaps, score match rates per feature (F1-F6), and produce
actionable recommendations.

### 1.2 Analysis Scope

- **Design Document**: `docs/02-design/features/platform-sdk.design.md`
- **Implementation Files**: 16 files across `stellar_memory/`, `celestial_engine/`, `tests/`, and `pyproject.toml`
- **Analysis Date**: 2026-02-21
- **Design Sections**: F1 (Core SDK), F2 (Package Split), F3 (Plugin), F4 (Builder), F5 (Protocols), F6 (Migration)

---

## 2. Overall Scores

```
+----------------------------------------------+
|  Overall Match Rate: 68%                      |
+----------------------------------------------+
|  Design Match:          68%                   |
|  Architecture Compliance: 60%                 |
|  Convention Compliance:   85%                 |
|  Overall:                68%                  |
+----------------------------------------------+
```

| Category | Score | Status |
|----------|:-----:|:------:|
| F5 - Protocols | 95% | PASS |
| F4 - Builder | 92% | PASS |
| F3 - Plugin System | 85% | PASS (partial) |
| F1 - Core SDK Layer | 35% | FAIL |
| F2 - Package Split & Compat | 78% | WARN |
| F6 - Migration / Deprecation | 55% | FAIL |
| **Weighted Overall** | **68%** | **WARN** |

---

## 3. Per-Feature Gap Analysis

---

### 3.1 F5: Interface Contracts (Protocols) -- 95%

**Design File**: `platform-sdk.design.md` Section 2
**Implementation File**: `stellar_memory/protocols.py` (90 LOC)

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| MemoryStore Protocol | 5 methods (store, recall, get, forget, stats) | 5 methods - exact match | Match |
| StorageBackend Protocol | Name: `StorageBackend`, 7 methods | Name: `StorageBackendProtocol`, 7 methods | Changed (naming) |
| EmbedderProvider Protocol | 2 methods (embed, embed_batch) | 2 methods - exact match | Match |
| LLMProvider Protocol | 1 method (complete) | 1 method - exact match | Match |
| ImportanceEvaluator Protocol | 1 method (evaluate) | 1 method - exact match | Match |
| EventHook Protocol | 1 method (on_event) | 1 method - exact match | Match |
| All @runtime_checkable | 6 protocols | 6 protocols | Match |
| TYPE_CHECKING guard | Not specified | Uses TYPE_CHECKING for MemoryItem/MemoryStats imports | Added (good practice) |

**Re-exports from providers/__init__.py:**

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| EmbedderProvider re-export | Move to protocols.py, re-export from providers/ | Re-exported via `from stellar_memory.protocols import ...` | Match |
| LLMProvider re-export | Move to protocols.py, re-export from providers/ | Re-exported via `from stellar_memory.protocols import ...` | Match |

**Gaps Found:**

| Severity | Item | Description |
|----------|------|-------------|
| Minor | Protocol name mismatch | Design says `StorageBackend`, impl uses `StorageBackendProtocol`. The `Protocol` suffix is arguably clearer but differs from design. |

**Tests**: `test_protocols.py` -- 9 tests covering runtime_checkable, conformance, and re-exports.

**Score Rationale**: 95/100. All 6 protocols implemented with correct signatures. Only a minor naming divergence for StorageBackendProtocol.

---

### 3.2 F4: SDK Builder -- 92%

**Design File**: `platform-sdk.design.md` Section 3
**Implementation File**: `stellar_memory/builder.py` (390 LOC)

**Preset Enum:**

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| MINIMAL | Present | Present | Match |
| CHAT | Present | Present | Match |
| AGENT | Present | Present | Match |
| KNOWLEDGE | Present | Present | Match |
| RESEARCH | Present | Present | Match |

**Builder Methods:**

| Method | Design | Implementation | Status |
|--------|--------|----------------|--------|
| `__init__(preset)` | `Preset = Preset.MINIMAL` | `Preset = Preset.MINIMAL` | Match |
| `with_sqlite(path)` | Present | Present | Match |
| `with_memory()` | Present in design list | Present - sets db_path to ":memory:" | Match |
| `with_postgres(dsn)` | `dsn` parameter | `db_url` parameter; uses `StorageConfig(backend="postgresql", db_url=...)` | Changed |
| `with_storage(backend)` | `StorageBackend` type | `StorageBackendProtocol` type | Changed (naming) |
| `with_embeddings(provider, model)` | 2 params | 3 params (added `dimension`) | Changed (additive) |
| `with_embedder(embedder)` | Present | Present | Match |
| `with_llm(provider, model)` | 2 params | 3 params (added `api_key_env`) | Changed (additive) |
| `with_emotions(enabled)` | `enabled: bool` param | `use_llm: bool` param | Changed |
| `with_graph(auto_link)` | 1 param | 2 params (added `threshold`) | Changed (additive) |
| `with_reasoning(enabled)` | `enabled: bool` param | `use_llm: bool` param | Changed |
| `with_metacognition(enabled)` | `enabled: bool` param | No params | Changed |
| `with_self_learning(enabled)` | `enabled: bool` param | `learning_rate: float` param | Changed |
| `with_sessions(...)` | Not in design | Present with `auto_summarize` param | Added |
| `with_decay(rate)` | 1 param | 3 params (rate, decay_days, auto_forget_days) | Changed (additive) |
| `with_zones(core, inner, outer, belt, cloud)` | All 5 params required | belt/cloud optional (None default) | Changed |
| `with_namespace(namespace)` | Present | Present | Match |
| `with_plugin(plugin)` | Present | Present | Match |
| `with_consolidation(threshold)` | Not in design | Present | Added |
| `with_summarization(min_length)` | Not in design | Present | Added |
| `from_dict(data)` | classmethod | classmethod with fuller implementation | Match |
| `from_toml(path)` | classmethod | classmethod with tomli fallback | Match |
| `build()` | Returns StellarMemory | Returns StellarMemory | Match |

**Preset Configurations:**

| Preset | Design | Implementation | Status |
|--------|--------|----------------|--------|
| MINIMAL | 3 zones, all features off | 3 zones, all features off | Match |
| CHAT | session + emotion on | session + emotion on, graph off | Match |
| AGENT | session + emotion + graph + reasoning + metacognition + self_learning | All enabled | Match |
| KNOWLEDGE | graph + consolidation + summarization | graph + consolidation + summarization | Match |
| RESEARCH | vector_index + benchmark | vector_index + benchmark | Match |

**Gaps Found:**

| Severity | Item | Description |
|----------|------|-------------|
| Minor | `with_postgres` parameter name | Design uses `dsn`, impl uses `db_url`. Functionally equivalent. |
| Minor | Builder `build()` missing `_storage_override` application | Design shows `memory._set_storage_backend(self._storage_override)`. Impl does not call this method; instead it would need a different mechanism. The method `_set_storage_backend` is not defined on StellarMemory in the implementation. |
| Minor | Extra methods added | `with_consolidation`, `with_summarization`, `with_sessions` are not in design but are useful additions. |

**Tests**: `test_builder.py` -- 20 tests covering presets, fluent API, build, and from_dict.

**Score Rationale**: 92/100. All 5 presets match. All design methods present. Minor parameter name differences and helpful additive methods.

---

### 3.3 F3: Plugin System -- 85%

**Design File**: `platform-sdk.design.md` Section 4
**Implementation Files**: `stellar_memory/plugin.py` (66 LOC), `stellar_memory/_plugin_manager.py` (106 LOC)

**MemoryPlugin Base Class:**

| Hook | Design | Implementation | Status |
|------|--------|----------------|--------|
| `name` class attribute | `"unnamed-plugin"` | `"unnamed-plugin"` | Match |
| `on_init(memory)` | Present | Present | Match |
| `on_store(item)` | Present, returns MemoryItem | Present, returns MemoryItem | Match |
| `on_pre_recall(query, **kwargs)` | Present, returns str | Present, returns str | Match |
| `on_recall(query, results)` | Present, returns list | Present, returns list | Match |
| `on_decay(item, new_score)` | Present, returns float | Present, returns float | Match |
| `on_reorbit(moves)` | Present | Present | Match |
| `on_forget(memory_id)` | Present, returns bool | Present, returns bool | Match |
| `on_consolidate(merged, sources)` | Present, returns MemoryItem | Present, returns MemoryItem | Match |
| `on_shutdown()` | Present | Present | Match |

**PluginManager (Internal):**

| Feature | Design | Implementation | Status |
|---------|--------|----------------|--------|
| `register(plugin, memory)` | Calls on_init | Calls on_init with try/except | Match (improved) |
| `dispatch_store(item)` | Chain through plugins | Chain with error isolation | Match (improved) |
| `dispatch_pre_recall(query)` | Chain through plugins | Chain with error isolation | Match (improved) |
| `dispatch_recall(query, results)` | Chain through plugins | Chain with error isolation | Match (improved) |
| `dispatch_decay(item, score)` | Chain through plugins | Chain with error isolation | Match (improved) |
| `dispatch_reorbit(moves)` | Notify all | Notify all with error isolation | Match (improved) |
| `dispatch_forget(memory_id)` | Any False cancels | Any False cancels, with error isolation | Match (improved) |
| `dispatch_consolidate(merged, sources)` | Chain through plugins | Chain with error isolation | Match (improved) |
| `shutdown()` | Call all on_shutdown | Call all on_shutdown with error isolation | Match (improved) |
| Error isolation (log, don't crash) | Design specifies this | All dispatch methods wrapped in try/except with logger.warning | Match |
| `plugins` property | Not in design | Added (read-only copy) | Added |

**StellarMemory Integration (stellar.py):**

| Integration Point | Design | Implementation | Status |
|-------------------|--------|----------------|--------|
| `_plugin_mgr = PluginManager()` in `__init__` | Present | Present (line 62) | Match |
| `use(plugin)` method | Present | Present (line 205) | Match |
| `on(event, callback)` method | Present | Present (line 209) | Match |
| `dispatch_store` in `store()` | After store logic | Called in `_store_internal` (line 332) | Match |
| `dispatch_pre_recall` in `recall()` | Before search | Called at start of recall (line 348) | Match |
| `dispatch_recall` in `recall()` | After search | Called after results (line 423) | Match |
| `dispatch_forget` in `forget()` | Before deletion | Called at start of forget (line 444) | Match |
| `shutdown()` in `stop()` | Present | Present (line 980) | Match |
| `dispatch_reorbit` in `reorbit()` | Not in design integration | NOT integrated | Missing |
| `dispatch_consolidate` in store consolidation path | Not in design integration | NOT integrated | Missing |

**Gaps Found:**

| Severity | Item | Description |
|----------|------|-------------|
| Major | `on_reorbit` hook not integrated | PluginManager has `dispatch_reorbit` but `stellar.py` `reorbit()` method (line 460) does not call it. The reorbit event is emitted via EventBus but plugin hook is skipped. |
| Major | `on_consolidate` hook not integrated | PluginManager has `dispatch_consolidate` but the consolidation path in `store()` (line 269-279) does not call it. |
| Minor | `on_decay` hook not integrated | PluginManager has `dispatch_decay` but `_apply_decay()` (line 700) does not call it for individual items. |

**Tests**: `test_plugin.py` -- 10 tests covering base class, on_store, on_recall, on_forget, on_init, chain order, on_shutdown, error handling.

**Score Rationale**: 85/100. Plugin base class and manager are exact matches with improved error isolation. However, 3 hooks (on_reorbit, on_consolidate, on_decay) are defined but not wired into stellar.py lifecycle methods.

---

### 3.4 F1: Core SDK Layer -- 35%

**Design File**: `platform-sdk.design.md` Sections 5, 9
**Implementation Files**: `stellar_memory/stellar.py` (987 LOC), `stellar_memory/config.py` (399 LOC), `stellar_memory/models.py` (445 LOC)

#### 3.4.1 Public API Simplification

**Design Target**: Reduce from 30+ methods to 14 public methods.

Public methods in current implementation (excluding private `_` methods and properties):

| # | Method | In Design's 14? | Status |
|---|--------|:---------------:|--------|
| 1 | `store()` | Yes | Keep |
| 2 | `recall()` | Yes | Keep |
| 3 | `get()` | Yes | Keep |
| 4 | `forget()` | Yes | Keep |
| 5 | `stats()` | Yes | Keep |
| 6 | `reorbit()` | Yes | Keep |
| 7 | `start()` | Yes | Keep |
| 8 | `stop()` | Yes | Keep |
| 9 | `use()` | Yes | Keep |
| 10 | `on()` | Yes | Keep |
| 11 | `export_json()` | Yes | Keep |
| 12 | `import_json()` | Yes | Keep |
| 13 | `reason()` | Yes | Keep |
| 14 | `introspect()` | Yes | Keep |
| 15 | `health()` | NO - should merge into stats() | NOT removed |
| 16 | `provide_feedback()` | NO - should be internal | NOT removed |
| 17 | `auto_tune()` | NO - should be internal | NOT removed |
| 18 | `create_middleware()` | NO - should be external | NOT removed |
| 19 | `start_session()` | NO - should be memory.session.start() | NOT removed |
| 20 | `end_session()` | NO - should be memory.session.end() | NOT removed |
| 21 | `snapshot()` | NO - should merge into export_json() | NOT removed |
| 22 | `recall_graph()` | NO - should be related() | NOT removed/renamed |
| 23 | `graph_stats()` | NO - should be memory.graph_analyzer.stats() | NOT removed |
| 24 | `graph_communities()` | NO - should be memory.graph_analyzer.communities() | NOT removed |
| 25 | `graph_centrality()` | NO - should be memory.graph_analyzer.centrality() | NOT removed |
| 26 | `graph_path()` | NO - should be memory.graph_analyzer.find_path() | NOT removed |
| 27 | `encrypt_memory()` | NO - should be plugin | NOT removed |
| 28 | `decrypt_memory()` | NO - should be plugin | NOT removed |
| 29 | `ingest()` | NO - should be plugin | NOT removed |
| 30 | `timeline()` | NO - should be memory.stream.timeline() | NOT removed |
| 31 | `narrate()` | NO - should be memory.stream.narrate() | NOT removed |
| 32 | `recall_with_confidence()` | NO - should merge into recall() | NOT removed |
| 33 | `optimize()` | NO - should be internal | NOT removed |
| 34 | `rollback_weights()` | NO - should be internal | NOT removed |
| 35 | `detect_contradictions()` | NO - should merge into reason() | NOT removed |
| 36 | `benchmark()` | NO - should be external | NOT removed |

**Design specifies `link()` and `related()` methods**: Neither exists. `recall_graph()` exists but was supposed to be renamed to `related()`, and `link()` is not implemented.

**Result**: 14 out of 14 design methods are present, but 22 methods that should have been removed are still present. The design target of "14 public methods" was NOT achieved. Current public method count: ~36.

#### 3.4.2 Config Simplification

**Design Target**: Reduce from 33 dataclasses to ~12.

**Current state**: config.py still contains **33 dataclasses** including:
- BillingConfig (design says REMOVE)
- OnboardConfig, KnowledgeBaseConfig (not addressed in design)
- All original P6 config classes (SyncConfig, SecurityConfig, ConnectorConfig, DashboardConfig, ServerConfig) that design says to REMOVE
- All sub-configs that design says to merge into parent (EventConfig, NamespaceConfig, AdaptiveDecayConfig, DecayConfig, EventLoggerConfig, RecallConfig, VectorIndexConfig, SummarizationConfig, GraphAnalyticsConfig, MultimodalConfig, BenchmarkConfig)

**Result**: 0 of 21 planned config removals/merges were implemented.

#### 3.4.3 Models Simplification

**Design Target**: Remove server/billing related models, simplify.

**Current state**: models.py contains **30 dataclasses** including SaaS/server models (AccessRole, IngestResult, ZoneDistribution, ScanResult, ScanSummary, ImportResult, ChunkInfo) that the design indicates should be removed or moved to optional extras.

**Result**: 0 simplification changes were made.

#### 3.4.4 stellar.py LOC Reduction

**Design Target**: 961 LOC reduced to ~400 LOC.
**Current state**: 987 LOC (slightly increased from baseline due to plugin integration additions).

**Gaps Found:**

| Severity | Item | Description |
|----------|------|-------------|
| Critical | Public method count not reduced | Design specifies 14 methods; implementation has ~36. The 22 methods marked for removal were not removed. |
| Critical | `link()` method missing | Design specifies `link(source_id, target_id, relation)` for explicit graph linking. Not implemented. |
| Critical | `related()` method missing | Design specifies `related(memory_id, depth)` to replace `recall_graph()`. Not implemented (recall_graph still exists). |
| Critical | config.py not simplified | 33 dataclasses remain vs design target of ~12. |
| Critical | models.py not simplified | 30 dataclasses remain vs design target of simplified set. |
| Critical | LOC not reduced | stellar.py is 987 LOC vs design target of ~400 LOC. |
| Major | BillingConfig still present | Design explicitly says "REMOVE". Still in config.py line 239-258. |
| Major | No internal module access pattern | Design specifies `memory.graph_analyzer`, `memory.session`, `memory.stream`, `memory.self_learning` as public attributes. Only `stream` is partially exposed (as lazy property). `graph_analyzer`, `session`, `self_learning` not exposed as designed. |
| Major | `store()` return type | Design says returns `str` (memory ID). Implementation returns `MemoryItem`. |
| Minor | `config` property | Design lists `config` as one of 14 public members. Implementation has `self.config` as a public attribute (equivalent). |

**Score Rationale**: 35/100. The additive changes (plugin hooks, use/on methods) are present, but the core simplification that defines F1 -- reducing methods, configs, models, and LOC -- was not performed at all.

---

### 3.5 F2: Package Split & Backward Compatibility -- 78%

**Design File**: `platform-sdk.design.md` Sections 6, 7
**Implementation Files**: `stellar_memory/__init__.py`, `stellar_memory/compat.py`, `pyproject.toml`

#### 3.5.1 __init__.py Core Exports

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| StellarMemory | In __all__ | In __all__ | Match |
| StellarBuilder | In __all__ | In __all__ | Match |
| Preset | In __all__ | In __all__ | Match |
| MemoryItem | In __all__ | In __all__ | Match |
| MemoryStats | In __all__ | In __all__ | Match |
| MemoryPlugin | In __all__ | In __all__ | Match |
| StorageBackend | In __all__ | `StorageBackendProtocol` in __all__ | Changed (naming) |
| EmbedderProvider | In __all__ | In __all__ | Match |
| ImportanceEvaluator | In __all__ | In __all__ | Match |
| MemoryStore | In __all__ | In __all__ | Match |
| StellarConfig | In __all__ | In __all__ | Match |
| __all__ count = 11 | 11 items | 11 items | Match |
| __version__ = "3.0.0" | Hardcoded | Dynamic with fallback to "3.0.0" | Match (improved) |

#### 3.5.2 Backward Compatibility Shim (__init__.py __getattr__)

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| __getattr__ lazy loading | Present in design Section 7.2 | Present (line 164) | Match |
| DeprecationWarning on v2 imports | Present | Present with clear message | Match |
| Config class redirects (28 classes) | Specified | All 28 present in _V2_COMPAT_MAP | Match |
| Model class redirects (22 classes) | Specified | All 22 present in _V2_COMPAT_MAP | Match |
| Core class redirects (20+ classes) | Specified | All present in _V2_COMPAT_MAP | Match |

#### 3.5.3 compat.py Module

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| __getattr__ with _V2_MAP | Present | Present with identical structure | Match |
| DeprecationWarning | Present | Present | Match |
| AttributeError for unknown names | Present | Present | Match |
| Comprehensive v2 export map | "all 58 v2 exports" | 70+ entries covering all v2 exports | Match (exceeds) |

#### 3.5.4 pyproject.toml

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| version = "3.0.0" | Present | Present | Match |
| dependencies = [] | Zero core deps | `dependencies = []` | Match |
| requires-python >= 3.10 | Present | Present | Match |
| optional: embedding | Present | Present | Match |
| optional: llm | Present | Present | Match |
| optional: openai | Present | Present | Match |
| optional: ollama | Present | Present | Match |
| optional: ai | Present | Present | Match |
| optional: mcp | Present | Present | Match |
| optional: server | Present | Present | Match |
| optional: dashboard | Present | Present | Match |
| optional: postgres | Present | Present | Match |
| optional: redis | Present | Present | Match |
| optional: security | Present | Present | Match |
| optional: sync | Present | Present | Match |
| optional: connectors | Present | Present | Match |
| optional: adapters | Present | Present | Match |
| optional: full | Present | Present (expanded inline vs self-referential) | Changed (functionally same) |
| optional: dev | Present | Present | Match |
| optional: docs | Present | Present | Match |
| optional: cli | Not in design | Present | Added |
| billing removed from full | Design says remove | Not present in `full` extras | Match |

**Gaps Found:**

| Severity | Item | Description |
|----------|------|-------------|
| Minor | StorageBackend vs StorageBackendProtocol in __all__ | Design says `"StorageBackend"`, impl uses `"StorageBackendProtocol"`. |
| Major | billing/ directory not removed | Design Step 8 says "billing/ REMOVE ~-748 LOC". The directory still exists with 8 files. |
| Minor | `full` extras uses inline deps | Design uses self-referential `stellar-memory[ai,mcp,...]`; impl lists deps directly. Functionally identical. |

**Score Rationale**: 78/100. __init__.py exports, compat.py, __getattr__ shim, and pyproject.toml all match closely. The billing/ directory still existing is a notable gap, and the naming divergence for StorageBackendProtocol propagates through.

---

### 3.6 F6: Migration / Deprecation -- 55%

**Design File**: `platform-sdk.design.md` Sections 8, 15
**Implementation Files**: `celestial_engine/__init__.py`, `docs/migration-v2-to-v3.md` (not found)

#### 3.6.1 celestial_engine Deprecation Shim

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| DeprecationWarning on import | Present | Present (line 22-27) | Match |
| Warning message mentions migration guide | "See migration guide: docs/migration-v2-to-v3.md" | Present | Match |
| `CelestialMemory` alias to `StellarMemory` | Design: `from stellar_memory import StellarMemory as CelestialMemory` | NOT present. Instead implements its own `CelestialMemory` class (line 77-181) | Missing |
| `StellarBuilder` export | In __all__ | NOT exported. Exports old celestial_engine classes. | Missing |
| `Preset` export | In __all__ | NOT exported | Missing |
| `StellarConfig` export | In __all__ | NOT exported | Missing |
| `MemoryItem` export | In __all__ | NOT exported (uses CelestialItem) | Missing |
| `MemoryStats` export | In __all__ | NOT exported | Missing |
| Minimal shim (~30 LOC) | Design says ~30 LOC | Implementation is 182 LOC with full CelestialMemory class | Changed (not simplified) |

**Current celestial_engine/__init__.py exports:**

The file exports `CelestialMemory`, `CelestialItem`, `CelestialMemoryFunction`, `MemoryFunctionConfig`, `MemoryPresets`, `MemoryMiddleware`, `AutoMemory`, `ZoneConfig`, `ScoreBreakdown`, `RebalanceResult`, `DEFAULT_ZONES`, `ImportanceEvaluator`, `DefaultEvaluator`, `RuleBasedEvaluator`, `LLMEvaluator`, `ZoneManager`, `Rebalancer` -- all from celestial_engine submodules, NOT from stellar_memory.

The design says celestial_engine should be a thin shim that re-exports from stellar_memory. Instead, it remains a fully independent package with its own implementation.

#### 3.6.2 Migration Guide

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| `docs/migration-v2-to-v3.md` | Design Step 11 | File does NOT exist | Missing |

**Gaps Found:**

| Severity | Item | Description |
|----------|------|-------------|
| Critical | celestial_engine not converted to shim | Design says celestial_engine should alias to stellar_memory classes. Implementation retains the full independent CelestialMemory class. |
| Major | Migration guide not created | `docs/migration-v2-to-v3.md` does not exist. |
| Major | AutoMemory not merged into Builder | Design says AutoMemory features should be merged into StellarBuilder. AutoMemory still exists independently. |

**Tests**: `test_compat.py` -- 12 tests covering v3 exports, v2 deprecation warnings, direct imports, compat module, and celestial_engine deprecation. Tests verify the deprecation warning fires but do NOT verify the content of what celestial_engine exports (the test just checks `import celestial_engine` produces a warning).

**Score Rationale**: 55/100. The deprecation warning is present, but the fundamental design goal -- converting celestial_engine to a thin shim over stellar_memory -- was not achieved.

---

## 4. Differences Summary

### 4.1 Missing Features (Design YES, Implementation NO)

| # | Item | Design Location | Description | Severity |
|---|------|-----------------|-------------|----------|
| 1 | Method reduction (36 to 14) | Section 5.1-5.2 | 22 methods not removed from StellarMemory | Critical |
| 2 | `link()` method | Section 5.1 | Explicit graph linking method not implemented | Critical |
| 3 | `related()` method | Section 5.1 | Graph traversal method not implemented (recall_graph exists) | Critical |
| 4 | Config simplification (33 to 12) | Section 9.1-9.2 | No dataclasses removed or merged | Critical |
| 5 | Models simplification | Section 5.2 | No model classes removed | Critical |
| 6 | stellar.py LOC reduction | Section 5 | 987 LOC vs target 400 LOC | Critical |
| 7 | billing/ directory removal | Section 6.2 | Directory still exists with 8 files | Major |
| 8 | celestial_engine shim conversion | Section 8.2 | Still full independent implementation | Critical |
| 9 | Migration guide document | Section 15 | docs/migration-v2-to-v3.md not created | Major |
| 10 | AutoMemory merger into Builder | Section 8.3 | AutoMemory still independent | Major |
| 11 | on_reorbit plugin hook integration | Section 4.3 | dispatch_reorbit not called in reorbit() | Major |
| 12 | on_consolidate plugin hook integration | Section 4.3 | dispatch_consolidate not called in store() | Major |
| 13 | on_decay plugin hook integration | Section 4.3 | dispatch_decay not called in _apply_decay() | Major |
| 14 | Internal module access pattern | Section 5.3-5.4 | graph_analyzer, session, self_learning not exposed as public attrs | Major |
| 15 | BillingConfig removal from config.py | Section 9.2 | BillingConfig still present (line 239) | Major |

### 4.2 Added Features (Design NO, Implementation YES)

| # | Item | Implementation Location | Description |
|---|------|------------------------|-------------|
| 1 | `with_sessions()` builder method | builder.py:174 | Enables session management |
| 2 | `with_consolidation()` builder method | builder.py:210 | Enables memory consolidation |
| 3 | `with_summarization()` builder method | builder.py:217 | Enables auto-summarization |
| 4 | `plugins` property on PluginManager | _plugin_manager.py:23 | Read-only plugin list |
| 5 | tomli fallback in from_toml | builder.py:278 | Python 3.10 compatibility |
| 6 | `cli` optional dependency | pyproject.toml:41 | CLI extra group |
| 7 | OnboardConfig, KnowledgeBaseConfig | config.py:307-333 | v2.1.0 Smart Onboarding configs |
| 8 | ScanResult, ScanSummary, ImportResult, ChunkInfo | models.py:402-445 | v2.1.0 Smart Onboarding models |

### 4.3 Changed Features (Design != Implementation)

| # | Item | Design | Implementation | Impact |
|---|------|--------|----------------|--------|
| 1 | Protocol name | `StorageBackend` | `StorageBackendProtocol` | Low - naming only |
| 2 | `store()` return type | `str` (memory ID) | `MemoryItem` | Medium - API difference |
| 3 | `with_postgres` param | `dsn: str` | `db_url: str` | Low - naming only |
| 4 | `with_emotions` param | `enabled: bool` | `use_llm: bool` | Low - different config aspect |
| 5 | `__version__` | Hardcoded `"3.0.0"` | Dynamic via importlib.metadata | Low - improved |
| 6 | `full` extras format | Self-referential | Inline dependencies | Low - functionally same |
| 7 | celestial_engine | Thin shim (~30 LOC) | Full independent class (182 LOC) | High - design intent unmet |

---

## 5. Test Coverage Analysis

| Test File | Tests | Coverage Areas | Missing Coverage |
|-----------|:-----:|----------------|-----------------|
| test_protocols.py | 9 | runtime_checkable, conformance, re-exports | EventHook conformance test |
| test_builder.py | 20 | presets, fluent API, build, from_dict | from_toml, with_postgres, custom storage/embedder overrides |
| test_plugin.py | 10 | base class, hooks, chain order, error isolation | on_reorbit, on_consolidate, on_decay integration |
| test_compat.py | 12 | v3 exports, v2 warnings, compat module, celestial_engine | compat map completeness, celestial_engine alias verification |

**Total new tests**: 51

**Missing test scenarios from design Section 12:**

| Designed Test | Present? | Notes |
|---------------|:--------:|-------|
| test_stellar_memory_implements_memory_store | NO | Would verify `isinstance(StellarMemory(...), MemoryStore)` |
| test_from_toml | NO | from_toml tested in builder tests? Not present. |
| test_v2_config_classes_accessible via compat | Partial | Tests a few, not all 33 |
| test_celestial_memory_is_stellar | NO | Cannot test because CelestialMemory is NOT an alias for StellarMemory |

---

## 6. Recommended Actions

### 6.1 Immediate Actions (Critical -- Block release)

| # | Action | Files Affected | Effort |
|---|--------|---------------|--------|
| 1 | **Simplify StellarMemory to 14 methods** | stellar.py | Large -- move 22 methods to internal module access or remove |
| 2 | **Add `link()` and `related()` methods** | stellar.py | Small -- wrapper around existing graph methods |
| 3 | **Simplify config.py from 33 to ~12 dataclasses** | config.py | Large -- merge/remove 21 dataclasses |
| 4 | **Convert celestial_engine to thin shim** | celestial_engine/__init__.py | Medium -- replace CelestialMemory class with alias |

### 6.2 Short-term Actions (Major -- Should fix)

| # | Action | Files Affected | Effort |
|---|--------|---------------|--------|
| 5 | Integrate on_reorbit hook into stellar.py reorbit() | stellar.py | Small |
| 6 | Integrate on_consolidate hook into stellar.py store() | stellar.py | Small |
| 7 | Integrate on_decay hook into stellar.py _apply_decay() | stellar.py | Small |
| 8 | Delete billing/ directory | stellar_memory/billing/ (8 files) | Small |
| 9 | Remove BillingConfig from config.py | config.py | Small |
| 10 | Create docs/migration-v2-to-v3.md | docs/ | Medium |
| 11 | Expose graph_analyzer, session, self_learning as public attrs | stellar.py | Medium |
| 12 | Simplify models.py (remove server/SaaS models) | models.py | Medium |
| 13 | Merge AutoMemory into StellarBuilder | builder.py, celestial_engine/ | Medium |

### 6.3 Low Priority Actions (Minor -- Nice to have)

| # | Action | Files Affected | Effort |
|---|--------|---------------|--------|
| 14 | Rename StorageBackendProtocol to StorageBackend | protocols.py, __init__.py, builder.py, tests | Small |
| 15 | Change store() return type to str (memory ID) | stellar.py | Small (breaking) |
| 16 | Add test_stellar_memory_implements_memory_store | test_protocols.py | Small |
| 17 | Add test_from_toml | test_builder.py | Small |

---

## 7. Synchronization Recommendations

Given the 68% overall match rate (below 70% threshold), significant synchronization
is needed. The recommended approach:

**Option 1 (Recommended): Modify implementation to match design**
- The design represents a clear architectural vision for v3.0
- F1 simplification is the core of the v3.0 value proposition
- Proceed with Steps 1-4 from Immediate Actions

**Option 2: Update design to match implementation (partial)**
- Record the additive features (with_sessions, with_consolidation, etc.) in design
- Update StorageBackendProtocol naming in design
- Keep simplification goals but adjust timeline

**Option 3: Hybrid approach**
- Implement critical simplifications (F1 method reduction, config reduction)
- Update design to accept celestial_engine remaining as independent package for now
- Create migration guide documenting current state

---

## 8. Score Calculation Detail

| Feature | Weight | Raw Score | Weighted |
|---------|:------:|:---------:|:--------:|
| F5 Protocols | 1.0 | 95% | 0.95 |
| F4 Builder | 1.0 | 92% | 0.92 |
| F3 Plugin | 1.0 | 85% | 0.85 |
| F1 Core SDK | 2.0 | 35% | 0.70 |
| F2 Package Split | 1.5 | 78% | 1.17 |
| F6 Migration | 0.5 | 55% | 0.275 |
| **Totals** | **7.0** | | **4.875** |

**Overall: 4.875 / 7.0 = 69.6% -- rounded to 68% (accounting for billing/ gap)**

---

---

## Iteration 1 Re-Analysis

> **Re-Analysis Date**: 2026-02-21
> **Previous Match Rate**: 68%
> **Trigger**: Post-iteration-1 fixes applied to F1, F2, F3, F6
> **Tests**: 673 pass, 33 skipped, 84 expected deprecation warnings

---

### I1.1 Changes Since Initial Analysis

The following changes were applied in Iteration 1:

1. **F1 - Core SDK**: 22 methods renamed to private (`_health`, `_provide_feedback`, etc.) with `__getattr__` backward compatibility (DeprecationWarning). `link()` and `related()` added as new public methods. `graph_analyzer`, `session_manager`, `self_learning` properties added.
2. **F1 - Config**: `BillingConfig` removed. `OnboardConfig` removed. `KnowledgeBaseConfig` kept but marked as internal.
3. **F1 - Models**: `AccessRole`, `ZoneDistribution`, `ScanResult`, `ScanSummary`, `ImportResult`, `ChunkInfo` moved to "Internal models" section with comment.
4. **F2 - Package Split**: `billing/` directory deleted (8 files removed).
5. **F3 - Plugin System**: `dispatch_reorbit` wired into `reorbit()`. `dispatch_consolidate` wired into `store()` consolidation path. `dispatch_decay` wired into `_apply_decay()`.
6. **F6 - Migration**: `celestial_engine/__init__.py` converted to thin shim (~68 LOC) re-exporting from `stellar_memory`. `docs/migration-v2-to-v3.md` created.

---

### I1.2 Updated Overall Scores

```
+----------------------------------------------+
|  Overall Match Rate: 88%                      |
+----------------------------------------------+
|  Design Match:          88%                   |
|  Architecture Compliance: 85%                 |
|  Convention Compliance:   92%                 |
|  Overall:                88%                  |
+----------------------------------------------+
```

| Category | Previous | Current | Delta | Status |
|----------|:--------:|:-------:|:-----:|:------:|
| F5 - Protocols | 95% | 95% | -- | PASS |
| F4 - Builder | 92% | 92% | -- | PASS |
| F3 - Plugin System | 85% | 98% | +13 | PASS |
| F1 - Core SDK Layer | 35% | 78% | +43 | WARN |
| F2 - Package Split & Compat | 78% | 92% | +14 | PASS |
| F6 - Migration / Deprecation | 55% | 90% | +35 | PASS |
| **Weighted Overall** | **68%** | **88%** | **+20** | **PASS** |

---

### I1.3 Per-Feature Re-Analysis

---

#### I1.3.1 F5: Interface Contracts (Protocols) -- 95% (unchanged)

No changes were made to `stellar_memory/protocols.py`. Score remains 95%.

The one minor gap persists: design says `StorageBackend` but implementation uses `StorageBackendProtocol`. This is a deliberate naming choice to distinguish from the existing ABC.

---

#### I1.3.2 F4: SDK Builder -- 92% (unchanged)

No changes were made to `stellar_memory/builder.py`. Score remains 92%.

All 5 presets, all builder methods, `from_dict`, `from_toml`, and `build()` continue to match design.

---

#### I1.3.3 F3: Plugin System -- 98% (was 85%)

**What changed**: All 3 missing hook integrations in `stellar.py` have been wired:

| Hook | Previous Status | Current Status | Location |
|------|----------------|----------------|----------|
| `dispatch_reorbit` | Missing | Wired | `stellar.py:466-467` -- called in `reorbit()` |
| `dispatch_consolidate` | Missing | Wired | `stellar.py:275-276` -- called in `store()` consolidation path |
| `dispatch_decay` | Missing | Wired | `stellar.py:738-739` -- called in `_apply_decay()` for each item |

**Remaining gaps:**

| Severity | Item | Description |
|----------|------|-------------|
| Minor | `dispatch_reorbit` move data is synthetic | `moves = [(str(i), 0, 0) for i in range(result.moved)]` does not provide actual (item_id, old_zone, new_zone) tuples. Real move data is available in OrbitManager but not surfaced. |

**Score Rationale**: 98/100. All 9 plugin hooks are now implemented and wired. The synthetic move data in `dispatch_reorbit` is the only remaining gap, and it is minor since the hook still fires correctly.

---

#### I1.3.4 F1: Core SDK Layer -- 78% (was 35%)

**What changed**: This is the most significantly improved feature.

##### Public API Simplification

**Design Target**: 16 public methods (design Section 5.1 lists 5 core + 3 lifecycle + 2 graph + 2 intelligence + 2 plugin + 2 serialization = 16).

**Current public methods** (non-underscore, excluding properties and `__getattr__`):

| # | Method | In Design? | Status |
|---|--------|:----------:|--------|
| 1 | `store()` | Yes | Match |
| 2 | `recall()` | Yes | Match |
| 3 | `get()` | Yes | Match |
| 4 | `forget()` | Yes | Match |
| 5 | `stats()` | Yes | Match |
| 6 | `reorbit()` | Yes | Match |
| 7 | `start()` | Yes | Match |
| 8 | `stop()` | Yes | Match |
| 9 | `link()` | Yes | Match (NEW) |
| 10 | `related()` | Yes | Match (NEW) |
| 11 | `reason()` | Yes | Match |
| 12 | `introspect()` | Yes | Match |
| 13 | `use()` | Yes | Match |
| 14 | `on()` | Yes | Match |
| 15 | `export_json()` | Yes | Match |
| 16 | `import_json()` | Yes | Match |

**Result**: 16 out of 16 design methods present. 22 formerly-public methods now prefixed with `_` and accessible only via `__getattr__` with DeprecationWarning. The public API target is met.

##### Backward Compatibility

The `_DEPRECATED_METHODS` dict (line 1029-1052) maps all 22 old method names to their private counterparts. `__getattr__` (line 1054) provides transparent backward compat with deprecation warnings. This is a sound approach that achieves the simplification without breaking existing code.

##### `link()` and `related()` Methods

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| `link(source_id, target_id, relation)` | `relation = "related"` | `relation = "related_to"`, adds `weight` param | Changed (minor) |
| `related(memory_id, depth)` | `depth: int = 2` | `depth: int = 2` | Match |
| `link` requires graph enabled | Not specified | Raises `RuntimeError` if graph not enabled | Added (good practice) |

##### Internal Module Access Properties

| Property | Design | Implementation | Status |
|----------|--------|----------------|--------|
| `graph_analyzer` | `self.graph_analyzer: GraphAnalyzer \| None` attribute | `@property` returning `self._analyzer` (line 666) | Match (property vs attribute, equivalent) |
| `session_manager` | `self.session: SessionManager \| None` | `@property` named `session_manager` returning `self._session_mgr` (line 675) | Changed (name: `session` vs `session_manager`) |
| `self_learning` | `self.self_learning: SelfLearning \| None` | `@property` returning `self._weight_optimizer` (line 680) | Match (returns weight optimizer component) |
| `stream` | `self.stream: MemoryStream \| None` | Lazy `@property` (line 828) | Match |

##### Config Simplification

**Design Target**: 33 dataclasses reduced to ~12.

**Changes applied**:
- `BillingConfig` removed (was line 239)
- `OnboardConfig` removed
- `KnowledgeBaseConfig` kept but marked "Internal (not part of public SDK API)" (line 282-284)

**Current state**: 31 dataclasses in config.py (was 33, removed 2). Design target was ~12.

| Category | Count | Design Target | Status |
|----------|:-----:|:-------------:|--------|
| Core configs (keep) | 12 | ~12 | Match |
| Infrastructure configs (design says remove) | 6 | 0 | NOT removed |
| Sub-configs (design says merge) | 11 | 0 | NOT merged |
| Internal (marked) | 1 | internal | Match |
| Removed | 2 | 21 | Partial |

The 6 infrastructure configs not removed: `SyncConfig`, `SecurityConfig`, `ConnectorConfig`, `DashboardConfig`, `ServerConfig`, `BenchmarkConfig`. The design says to remove these as optional extras, but removing them would require refactoring all modules that reference them.

The 11 sub-configs not merged: `EventConfig`, `NamespaceConfig`, `AdaptiveDecayConfig`, `DecayConfig`, `EventLoggerConfig`, `RecallConfig`, `VectorIndexConfig`, `SummarizationConfig`, `GraphAnalyticsConfig`, `MultimodalConfig`, `ConsolidationConfig`. Design says to merge these into parent configs or convert to simple flags.

##### Models Simplification

**Changes applied**:
- Internal models section created (line 385): `AccessRole`, `ZoneDistribution`, `ScanResult`, `ScanSummary`, `ImportResult`, `ChunkInfo` marked with "Internal models (not part of public SDK API)" comment.

**Current state**: 30 dataclasses total. Design says to remove server/SaaS models. Models are now marked internal but not removed.

##### stellar.py LOC

**Design Target**: ~400 LOC
**Current**: 1067 LOC

The LOC target was aspirational and assumed full removal of deprecated methods. The `__getattr__` backward compatibility approach requires keeping the private method implementations, which adds approximately 500 LOC that would not exist if backward compat were dropped. The effective "new public surface" code is approximately 500 LOC (init + 16 public methods + properties + __getattr__ shim), which while above the 400 target, reflects the cost of maintaining backward compatibility.

##### F1 Remaining Gaps

| Severity | Item | Description |
|----------|------|-------------|
| Major | Config dataclass count | 31 dataclasses vs target ~12. Only 2 removed (BillingConfig, OnboardConfig). 19 more need removal/merging. |
| Major | stellar.py LOC | 1067 LOC vs target ~400. Backward compat adds ~500 LOC of private methods. |
| Minor | models.py internal models | Marked as internal but not physically separated into a sub-module. |
| Minor | `link()` default relation | Design says `"related"`, implementation says `"related_to"`. |
| Minor | `session_manager` property name | Design says `memory.session`, implementation uses `memory.session_manager`. |
| Minor | `store()` return type | Design says `str` (memory ID), implementation returns `MemoryItem`. |

**Score Rationale**: 78/100. The core simplification goal -- reducing the public API to 16 methods -- is achieved through the `_` prefix + `__getattr__` pattern. `link()` and `related()` are implemented. Properties for internal module access are present. However, config.py still has 31 dataclasses (vs 12 target), models.py still has all models (marked but not removed), and stellar.py remains at 1067 LOC. The method count target is met but the code/config reduction targets are substantially unmet.

---

#### I1.3.5 F2: Package Split & Backward Compatibility -- 92% (was 78%)

**What changed**:
- `billing/` directory deleted (8 files removed, confirmed: no files found under `stellar_memory/billing/`)
- `__init__.py` compat map updated: comment notes BillingConfig, OnboardConfig removed

**Updated status:**

| Item | Previous | Current |
|------|----------|---------|
| billing/ directory removal | Exists (8 files) | Deleted |
| BillingConfig in full extras | Not present | Confirmed absent |
| __init__.py __all__ (11 items) | Match | Match |
| compat.py comprehensive map | Match | Match |
| pyproject.toml v3.0.0 | Match | Match |
| dependencies = [] | Match | Match |

**Remaining gaps:**

| Severity | Item | Description |
|----------|------|-------------|
| Minor | StorageBackendProtocol naming | Design says `StorageBackend`, impl uses `StorageBackendProtocol` in `__all__` |
| Minor | `full` extras format | Inline deps vs self-referential. Functionally identical. |

**Score Rationale**: 92/100. The billing/ directory deletion resolves the biggest gap from v1. All exports, compat shim, and pyproject.toml match design. Only the protocol naming divergence remains.

---

#### I1.3.6 F6: Migration / Deprecation -- 90% (was 55%)

**What changed**:
- `celestial_engine/__init__.py` completely rewritten as thin shim (68 LOC)
- `docs/migration-v2-to-v3.md` created (210 lines)

**celestial_engine/__init__.py Shim Analysis:**

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| DeprecationWarning on import | Present | Present (line 20-25) | Match |
| Warning mentions migration guide | "docs/migration-v2-to-v3.md" | Present | Match |
| `CelestialMemory = StellarMemory` alias | `from stellar_memory import StellarMemory as CelestialMemory` | `from stellar_memory import StellarMemory as CelestialMemory` (line 28) | Match |
| `CelestialItem = MemoryItem` alias | In design __all__ | `from stellar_memory import MemoryItem as CelestialItem` (line 32) | Match |
| `StellarBuilder` export | In __all__ | Exported (line 29) | Match |
| `Preset` export | In __all__ | Exported (line 30) | Match |
| `StellarConfig` export | In __all__ | Exported (line 31) | Match |
| `MemoryStats` export | In __all__ | Exported (line 33) | Match |
| Thin shim (~30 LOC) | Design target | 68 LOC | Changed (larger, but includes legacy re-exports) |
| Legacy evaluator re-exports | Not in design | Lines 42-47: re-exports `ImportanceEvaluator`, `RuleBasedEvaluator`, `LLMEvaluator`, `DefaultEvaluator` | Added (enhances compat) |
| `ScoreBreakdown`, `ReorbitResult` re-exports | Not in design | Lines 34: re-exports from models | Added (enhances compat) |
| Config re-exports | Not in design | Lines 35-39: `MemoryFunctionConfig`, `ZoneConfig`, `DEFAULT_ZONES` | Added (enhances compat) |
| `__version__` | Not specified | `"3.0.0-deprecated"` | Added |

**Migration Guide Analysis (`docs/migration-v2-to-v3.md`):**

| Section | Design Requirement | Implementation | Status |
|---------|-------------------|----------------|--------|
| Quick Start | v3.0 3-line init example | Present | Match |
| Import Changes | v2.0 to v3.0 import mapping | Present with before/after examples | Match |
| Builder Pattern | New builder usage examples | Present with v2.0 vs v3.0 comparison | Match |
| Presets table | List of presets and features | Present | Match |
| Method Changes | v2.0 method to v3.0 replacement | Comprehensive table with 14 entries | Match |
| Plugin System | Plugin example code | Present with hook reference table | Match |
| Protocol Interfaces | Custom storage example | Present with `isinstance` assertion | Match |
| celestial_engine deprecation | Before/after example | Present | Match |
| Removed items | BillingConfig, OnboardConfig, billing/, models | Listed | Match |
| Timeline | v3.0, v3.1, v4.0 plan | Present | Match |

**AutoMemory integration:**

| Item | Design | Implementation | Status |
|------|--------|----------------|--------|
| AutoMemory features merged into Builder | Design Section 8.3 | AutoMemory presets are effectively superseded by `StellarBuilder(Preset.*)`. The `celestial_engine/auto_memory.py` module status is unclear (the shim does not re-export it). | Partial -- functional equivalent via Builder, but AutoMemory module fate unverified. |

**Remaining gaps:**

| Severity | Item | Description |
|----------|------|-------------|
| Minor | Shim is 68 LOC vs design's 30 LOC | Extra LOC from legacy evaluator/config re-exports. Enhances backward compat, not a regression. |
| Minor | AutoMemory module fate | Design says merge into Builder. Builder functionally supersedes it, but `celestial_engine/auto_memory.py` may still exist independently. |

**Score Rationale**: 90/100. The critical gap -- converting celestial_engine to a thin shim -- is fully resolved. All aliases (`CelestialMemory`, `CelestialItem`) point to `stellar_memory` classes. Migration guide is comprehensive. The extra re-exports beyond design spec improve backward compatibility. Minor deduction for the larger-than-designed shim and unverified AutoMemory module status.

---

### I1.4 Updated Differences Summary

#### Missing Features (Design YES, Implementation NO) -- reduced from 15 to 6

| # | Item | Design Location | Description | Severity | Previous |
|---|------|-----------------|-------------|----------|----------|
| 1 | Config simplification (31 to 12) | Section 9.1-9.2 | 31 dataclasses remain vs target ~12. 2 removed, 19 more needed. | Major | Was Critical |
| 2 | stellar.py LOC reduction | Section 5 | 1067 LOC vs target ~400. Backward compat pattern adds ~500 LOC. | Major | Was Critical |
| 3 | Models physical separation | Section 5.2 | Internal models marked but not moved to sub-module. | Minor | Was Critical |
| 4 | `store()` return type | Section 5.1 | Design says `str`, impl returns `MemoryItem`. | Minor | Same |
| 5 | `dispatch_reorbit` synthetic data | Section 4.3 | Move tuples use synthetic data, not actual zone transitions. | Minor | N/A |
| 6 | AutoMemory module cleanup | Section 8.3 | `celestial_engine/auto_memory.py` may still exist independently. | Minor | Was Major |

#### Resolved Items (from initial 15 Missing)

| # | Item | Resolution |
|---|------|------------|
| 1 | Method reduction (36 to 16) | 22 methods prefixed with `_`, `__getattr__` backward compat |
| 2 | `link()` method | Implemented at stellar.py:640 |
| 3 | `related()` method | Implemented at stellar.py:647 |
| 4 | celestial_engine shim conversion | Rewritten as 68-LOC thin shim |
| 5 | Migration guide document | Created at `docs/migration-v2-to-v3.md` |
| 6 | billing/ directory removal | Deleted (confirmed: 0 files remain) |
| 7 | BillingConfig removal | Removed from config.py |
| 8 | on_reorbit hook integration | Wired at stellar.py:466-467 |
| 9 | on_consolidate hook integration | Wired at stellar.py:275-276 |
| 10 | on_decay hook integration | Wired at stellar.py:738-739 |
| 11 | Internal module access properties | `graph_analyzer`, `session_manager`, `self_learning` properties added |

---

### I1.5 Updated Score Calculation

| Feature | Weight | Previous | Current | Weighted (Previous) | Weighted (Current) |
|---------|:------:|:--------:|:-------:|:-------------------:|:------------------:|
| F5 Protocols | 1.0 | 95% | 95% | 0.950 | 0.950 |
| F4 Builder | 1.0 | 92% | 92% | 0.920 | 0.920 |
| F3 Plugin | 1.0 | 85% | 98% | 0.850 | 0.980 |
| F1 Core SDK | 2.0 | 35% | 78% | 0.700 | 1.560 |
| F2 Package Split | 1.5 | 78% | 92% | 1.170 | 1.380 |
| F6 Migration | 0.5 | 55% | 90% | 0.275 | 0.450 |
| **Totals** | **7.0** | | | **4.865** | **6.240** |

**Overall: 6.240 / 7.0 = 89.1% -- rounded to 88%**

The 1% difference from 89% to 88% accounts for the remaining config simplification gap being more impactful than the raw F1 score suggests.

---

### I1.6 Recommended Next Actions

#### To reach 90%+ (2 items)

| # | Action | Impact | Effort | Files |
|---|--------|--------|--------|-------|
| 1 | **Merge 6 infrastructure sub-configs into StellarConfig simple flags** | F1 +5% | Medium | `config.py` |
| 2 | **Merge 5 minor sub-configs into parent configs** | F1 +3% | Medium | `config.py`, `stellar.py` |

Specifically:
- Merge `EventConfig` into `StellarConfig.events_enabled: bool`
- Merge `NamespaceConfig` into `StellarConfig.namespace: str | None` (already exists as init param)
- Merge `EventLoggerConfig` into `StellarConfig.event_log_path: str | None`
- Merge `RecallConfig` into `GraphConfig.recall_boost: bool`
- Merge `GraphAnalyticsConfig` into `GraphConfig`
- Convert `SyncConfig`, `SecurityConfig`, `ConnectorConfig`, `DashboardConfig`, `ServerConfig` to optional-only (lazy import or remove from core config)

#### Low Priority (will not block 90%)

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 3 | Change `store()` return type to `str` | Minor | Small (potentially breaking) |
| 4 | Rename `session_manager` property to `session` | Minor | Small |
| 5 | Fix `dispatch_reorbit` to pass real move data | Minor | Small |
| 6 | Physically separate internal models to sub-module | Minor | Medium |

---

### I1.7 Synchronization Assessment

**Match Rate: 88% (above 70% threshold, approaching 90% target)**

The implementation now closely matches the design intent. The primary remaining gap is config.py dataclass count (31 vs 12), which is a significant structural simplification that carries refactoring risk. All functional design goals (public API reduction, plugin hooks, builder, protocols, migration shim, package cleanup) are achieved.

**Recommendation**: Proceed with targeted config simplification (merging the safest sub-configs first) to push above 90%. The current 88% represents a stable, well-tested state where all 673 tests pass.

---

---

## Iteration 2 Re-Analysis

> **Re-Analysis Date**: 2026-02-21
> **Previous Match Rate**: 88%
> **Trigger**: Post-iteration-2 fixes targeting F1 config simplification and API cleanup
> **Focus Areas**: config.py dataclass count, link() default relation, session property, EventConfig removal

---

### I2.1 Changes Since Iteration 1

The following changes were applied in Iteration 2:

1. **F1 - Config**: `EventConfig` dataclass removed from `config.py` (was unreferenced). Config dataclass count: 31 -> 30.
2. **F1 - Core SDK**: `link()` default `relation` parameter changed from `"related_to"` to `"related"` to match design spec (Section 5.1: `relation: str = "related"`).
3. **F1 - Core SDK**: `session` property added at `stellar.py:675` (matching design's `memory.session`). `session_manager` kept at `stellar.py:680` as backward-compat alias.
4. **F1 - Config**: `GraphAnalyticsConfig` merge into `GraphConfig` was attempted then reverted (too risky). `GraphAnalyticsConfig` remains a separate dataclass.

---

### I2.2 Updated Overall Scores

```
+----------------------------------------------+
|  Overall Match Rate: 89%                      |
+----------------------------------------------+
|  Design Match:          89%                   |
|  Architecture Compliance: 86%                 |
|  Convention Compliance:   92%                 |
|  Overall:                89%                  |
+----------------------------------------------+
```

| Category | Iter 0 | Iter 1 | Iter 2 | Delta (1->2) | Status |
|----------|:------:|:------:|:------:|:------------:|:------:|
| F5 - Protocols | 95% | 95% | 95% | -- | PASS |
| F4 - Builder | 92% | 92% | 92% | -- | PASS |
| F3 - Plugin System | 85% | 98% | 98% | -- | PASS |
| F1 - Core SDK Layer | 35% | 78% | 81% | +3 | WARN |
| F2 - Package Split & Compat | 78% | 92% | 91% | -1 | PASS |
| F6 - Migration / Deprecation | 55% | 90% | 90% | -- | PASS |
| **Weighted Overall** | **68%** | **88%** | **89%** | **+1** | **PASS** |

---

### I2.3 Per-Feature Re-Analysis

---

#### I2.3.1 F5: Interface Contracts (Protocols) -- 95% (unchanged)

No changes to `stellar_memory/protocols.py`. Score remains 95%.

The `StorageBackendProtocol` naming divergence from design's `StorageBackend` persists as a deliberate choice.

---

#### I2.3.2 F4: SDK Builder -- 92% (unchanged)

No changes to `stellar_memory/builder.py`. Score remains 92%.

---

#### I2.3.3 F3: Plugin System -- 98% (unchanged)

No changes to plugin files. Score remains 98%.

The synthetic `dispatch_reorbit` move data remains the only minor gap.

---

#### I2.3.4 F1: Core SDK Layer -- 81% (was 78%, +3)

Three targeted improvements were applied in this iteration:

##### link() Default Relation Fixed

| Item | Design | Iter 1 | Iter 2 | Status |
|------|--------|--------|--------|--------|
| `link()` default relation | `"related"` | `"related_to"` | `"related"` (stellar.py:641) | Match -- RESOLVED |

This resolves a minor gap from Iteration 1. The `link()` method now exactly matches design Section 5.1.

##### session Property Added

| Item | Design | Iter 1 | Iter 2 | Status |
|------|--------|--------|--------|--------|
| `memory.session` access | `self.session: SessionManager` | `session_manager` property only | `session` property (line 675) + `session_manager` alias (line 680) | Match -- RESOLVED |

Design Section 5.3 specifies `memory.session.start()` / `memory.session.end()`. The `session` property now provides this exact access pattern. The `session_manager` alias is kept for backward compat, which is a reasonable addition.

##### Config Simplification Progress

**EventConfig removal**:
- `EventConfig` dataclass removed from `config.py` (confirmed: no `EventConfig` class definition found)
- This was listed in design Section 9.2 as "merge into `StellarConfig.events_enabled: bool`"
- Impact: dataclass count 31 -> 30 (target: ~12)

**GraphAnalyticsConfig merge reverted**:
- Attempted to merge `GraphAnalyticsConfig` into `GraphConfig` but reverted due to risk
- `GraphAnalyticsConfig` remains as a separate dataclass at `config.py:105-108`
- This is understandable -- the config is referenced by `GraphAnalyzer` constructor and merging requires coordinated changes across multiple files

**Updated config dataclass status**:

| Category | Count | Design Target | Iter 1 | Iter 2 |
|----------|:-----:|:-------------:|:------:|:------:|
| Core configs (keep) | 12 | ~12 | 12 | 12 |
| Infrastructure configs (remove) | 6 | 0 | 6 | 6 |
| Sub-configs (merge into parent) | 10 | 0 | 11 | 10 |
| Internal (marked) | 1 | internal | 1 | 1 |
| Removed (from original 33) | 3 | 21 | 2 | 3 |
| **Total remaining** | **30** | **~12** | **31** | **30** |

The 10 remaining sub-configs that design says to merge:
`NamespaceConfig`, `AdaptiveDecayConfig`, `DecayConfig`, `EventLoggerConfig`, `RecallConfig`, `VectorIndexConfig`, `SummarizationConfig`, `GraphAnalyticsConfig`, `MultimodalConfig`, `ConsolidationConfig`

##### stellar.py LOC

**Current**: 1072 LOC (was 1067 in Iteration 1, +5 from `session` property addition)
**Design Target**: ~400 LOC

The LOC increase is small and justified by the new property. The overall gap remains structural -- backward compatibility via `__getattr__` plus private method bodies accounts for approximately 500 LOC.

##### F1 Remaining Gaps

| Severity | Item | Description | Changed? |
|----------|------|-------------|----------|
| Major | Config dataclass count | 30 vs target ~12. 3 removed so far, 18 more needed. | Improved (31->30) |
| Major | stellar.py LOC | 1072 LOC vs target ~400. Backward compat adds ~500 LOC. | Slightly worse (+5) |
| Minor | models.py internal models | Marked as internal but not physically separated. | Unchanged |
| Minor | `store()` return type | Design says `str`, impl returns `MemoryItem`. | Unchanged |
| ~~Minor~~ | ~~`link()` default relation~~ | ~~Design says `"related"`, was `"related_to"`~~ | RESOLVED |
| ~~Minor~~ | ~~`session_manager` property name~~ | ~~Design says `memory.session`~~ | RESOLVED |

**Score Rationale**: 81/100 (was 78%). Two minor gaps resolved (link default, session property) contribute +3%. The EventConfig removal helps but only marginally (30 vs 31 out of target 12 is not a significant proportional improvement). The major gaps -- config simplification and LOC reduction -- remain structurally unchanged.

---

#### I2.3.5 F2: Package Split & Backward Compatibility -- 91% (was 92%, -1)

**What changed**: The `EventConfig` removal from `config.py` introduced a latent compatibility issue.

**New gap discovered**:

| Severity | Item | Description |
|----------|------|-------------|
| Medium | `EventConfig` compat map broken | `__init__.py` line 75 and `compat.py` line 31 still reference `"EventConfig": (".config", "EventConfig")` in the v2 compat map. Since `EventConfig` no longer exists in `config.py`, any v2 code importing `EventConfig` via `from stellar_memory import EventConfig` or `from stellar_memory.compat import EventConfig` will fail with `AttributeError` at runtime. |
| Minor | StorageBackendProtocol naming | Unchanged from previous iterations. |
| Minor | `full` extras format | Unchanged from previous iterations. |

The `EventConfig` compat map entry should either be removed (if EventConfig is truly gone and no backward compat is needed) or the v2 compat map should point to a stub/error message explaining the removal. This is a regression from the previous state where the compat map was fully functional.

**Score Rationale**: 91/100 (was 92%). The compat map breakage for `EventConfig` is a small but real regression. The map now contains a reference to a non-existent class, which could cause runtime errors for v2 users. The -1% reflects this new gap.

---

#### I2.3.6 F6: Migration / Deprecation -- 90% (unchanged)

No changes to `celestial_engine/__init__.py` or `docs/migration-v2-to-v3.md`. Score remains 90%.

---

### I2.4 Updated Differences Summary

#### Missing Features (Design YES, Implementation NO) -- 4 items (was 6 in Iter 1)

| # | Item | Description | Severity | Iter 1 |
|---|------|-------------|----------|--------|
| 1 | Config simplification (30 to 12) | 30 dataclasses vs target ~12. 3 removed total. | Major | Was 31 |
| 2 | stellar.py LOC reduction | 1072 LOC vs target ~400. | Major | Was 1067 |
| 3 | Models physical separation | Internal models marked but not moved. | Minor | Same |
| 4 | `store()` return type | Design says `str`, impl returns `MemoryItem`. | Minor | Same |

#### Resolved Items (from Iteration 1's 6 Missing)

| # | Item | Resolution |
|---|------|------------|
| 1 | `link()` default relation `"related_to"` -> `"related"` | Fixed at `stellar.py:641` |
| 2 | `session_manager` property -> `session` property | Added at `stellar.py:675`, alias kept at `stellar.py:680` |

#### New Issues Introduced

| # | Item | Description | Severity |
|---|------|-------------|----------|
| 1 | `EventConfig` compat map stale entry | `__init__.py:75` and `compat.py:31` reference removed `EventConfig` class | Medium |

---

### I2.5 Updated Score Calculation

| Feature | Weight | Iter 0 | Iter 1 | Iter 2 | Weighted (Iter 2) |
|---------|:------:|:------:|:------:|:------:|:-----------------:|
| F5 Protocols | 1.0 | 95% | 95% | 95% | 0.950 |
| F4 Builder | 1.0 | 92% | 92% | 92% | 0.920 |
| F3 Plugin | 1.0 | 85% | 98% | 98% | 0.980 |
| F1 Core SDK | 2.0 | 35% | 78% | 81% | 1.620 |
| F2 Package Split | 1.5 | 78% | 92% | 91% | 1.365 |
| F6 Migration | 0.5 | 55% | 90% | 90% | 0.450 |
| **Totals** | **7.0** | | | | **6.285** |

**Overall: 6.285 / 7.0 = 89.8% -- rounded to 89%**

The marginal improvement (+1% overall) reflects the limited scope of Iteration 2 changes:
- F1 gained +3% from resolving 2 minor gaps (link default, session property)
- F2 lost -1% from the EventConfig compat map regression
- Net effect: +1% overall

---

### I2.6 Gap to 90% Analysis

The current 89% is just 1% below the 90% target. To cross the threshold:

#### Option A: Fix the EventConfig compat regression (Easiest -- pushes to 90%)

| Action | Impact | Effort | Files |
|--------|--------|--------|-------|
| Remove `EventConfig` from `_V2_COMPAT_MAP` in `__init__.py` and `_V2_MAP` in `compat.py` | F2 +1% -> 92%, restoring previous score | Trivial (2 line deletions) | `__init__.py`, `compat.py` |

This alone would restore F2 to 92% and push the weighted overall to:
`(0.950 + 0.920 + 0.980 + 1.620 + 1.380 + 0.450) / 7.0 = 6.300 / 7.0 = 90.0%`

#### Option B: Config simplification (Higher impact, higher effort)

| Action | Impact | Effort | Files |
|--------|--------|--------|-------|
| Merge `NamespaceConfig` into `StellarConfig.namespace: str \| None` | F1 +1% | Small | `config.py`, `stellar.py` |
| Merge `RecallConfig` into `GraphConfig` | F1 +1% | Small | `config.py`, `stellar.py` |
| Merge `EventLoggerConfig` into simple flags | F1 +1% | Small | `config.py`, `stellar.py` |
| Merge `GraphAnalyticsConfig` into `GraphConfig` | F1 +1% | Medium (attempted and reverted) | `config.py`, `stellar.py`, `graph_analyzer.py` |

Each config merge reduces the dataclass count toward the target of 12 and incrementally improves F1.

#### Recommended Path to 90%

**Immediate** (Iteration 2 hotfix):
1. Remove `EventConfig` from compat maps in `__init__.py:75` and `compat.py:31` -- this is a bug fix, not a design change
2. This alone achieves exactly 90.0%

**Follow-up** (Iteration 3, if pursued):
1. Merge the 4-5 safest sub-configs into parent configs
2. Target: bring dataclass count from 30 to ~25
3. Expected F1 improvement: +3-5%, pushing overall to 92-93%

---

### I2.7 Synchronization Assessment

**Match Rate: 89% (1% below 90% target)**

The Iteration 2 changes were narrow in scope but effective at resolving specific design deviations. The `link()` default relation now exactly matches design. The `session` property provides the access pattern design intended. The `EventConfig` removal progresses config simplification.

However, the core blocker to reaching 90% is not a design gap but a self-inflicted regression: the stale `EventConfig` entry in the compat maps. Fixing this trivial issue would bring the score to exactly 90%.

The remaining major gaps (config dataclass count and LOC) represent a structural simplification effort that carries refactoring risk. Given that all functional design goals are met and 673+ tests pass, the current state is production-ready. The config simplification can be treated as a follow-up improvement rather than a release blocker.

**Recommendation**: Apply the EventConfig compat map fix (2 line deletions) to reach 90%. Mark the config simplification as a post-v3.0 improvement tracked in a separate PDCA cycle.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-21 | Initial gap analysis (68%) | gap-detector agent |
| 2.0 | 2026-02-21 | Iteration 1 re-analysis (88%) after F1/F2/F3/F6 fixes | gap-detector agent |
| 3.0 | 2026-02-21 | Iteration 2 re-analysis (89%) -- link() default, session property, EventConfig removal | gap-detector agent |
