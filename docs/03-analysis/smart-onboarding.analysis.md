# Gap Analysis: smart-onboarding

> Design vs Implementation comparison
> Date: 2026-02-20
> Design: `docs/02-design/features/smart-onboarding.design.md`

## Match Rate: 96%

## Component-Level Analysis

| Component | Design Items | Matched | Rate | Status |
|-----------|:----------:|:-------:|:----:|:------:|
| F1: scanner.py | 18 | 17 | 94% | PASS |
| F2: importer.py | 15 | 15 | 100% | PASS |
| F3: cli.py | 18 | 18 | 100% | PASS |
| F6: knowledge_base.py | 22 | 22 | 100% | PASS |
| F5: mcp_server.py | 7 | 6.5 | 93% | PASS |
| F4: viz.py | 24 | 21 | 88% | PASS |
| config.py | 15 | 15 | 100% | PASS |
| models.py | 4 | 4 | 100% | PASS |
| **Total** | **123** | **118.5** | **96%** | **PASS** |

---

## Detailed Checklist

### F1: LocalScanner (scanner.py) - 94%

- [x] ScanResult dataclass with path, category, size, preview, ai_tool, importable
- [x] ScanSummary dataclass with total_found, by_category, total_size_bytes, skipped_count, results
- [x] ScanCategory dataclass with name, search_paths, file_patterns, importance, recursive
- [x] 6 scan categories: documents, notes, ai-config, chat-history, code, bookmarks
- [x] MAX_FILE_SIZE = 102,400 (100KB)
- [x] MAX_DEPTH = 3
- [x] __init__(categories, exclude_paths)
- [x] scan(categories) -> ScanSummary
- [x] _scan_ai_configs() (design: scan_ai_configs public, impl: private - acceptable)
- [x] _scan_category(category) -> list[ScanResult]
- [x] _is_safe(path) -> bool
- [x] _get_preview(path) -> str (first 200 chars)
- [x] AI_CONFIG_FILES dict (CLAUDE.md, .cursorrules, .windsurfrules)
- [x] AI_CONFIG_SUBPATHS (.github/copilot-instructions.md)
- [x] CLAUDE_MEMORY_DIR scanning
- [ ] CLAUDE_PROJECTS_DIR constant/scanning (design line 199)
- [x] Platform-specific paths (Windows/macOS/Linux)
- [x] SKIP_DIRS + SENSITIVE_NAMES + SENSITIVE_EXTENSIONS

### F2: SmartImporter (importer.py) - 100%

- [x] CHUNK_SIZE = 500
- [x] DEDUP_THRESHOLD = 0.8
- [x] IMPORTANCE_BY_CATEGORY dict (6 categories)
- [x] __init__(memory)
- [x] import_scan_results(results, progress_callback) -> ImportResult
- [x] _import_file(scan_result) -> list[str]
- [x] _import_ai_config(scan_result) -> list[str]
- [x] _import_bookmarks(scan_result) -> list[str] (bonus: not in design)
- [x] _chunk_content(content, source) -> list[ChunkInfo]
- [x] _is_duplicate(content) -> bool (recall + Jaccard)
- [x] _jaccard_similarity(a, b) -> float
- [x] _build_metadata(scan_result, chunk) -> dict
- [x] _parse_markdown_rules(content) -> list[str]
- [x] AI config import: sections parsed with importance 0.9
- [x] Claude memory import: content as-is with importance 0.85

### F3: CLI Commands (cli.py) - 100%

- [x] `onboard` subcommand with help text
- [x] --categories/-c nargs="*"
- [x] --exclude nargs="*"
- [x] --yes/-y action="store_true"
- [x] --dry-run action="store_true"
- [x] Welcome banner
- [x] Interactive category selection
- [x] Scan execution with progress
- [x] Preview display (top 5 per category)
- [x] Confirmation prompt with Y/n
- [x] Import with progress_callback
- [x] Summary output (imported, skipped, zone distribution)
- [x] `viz` subcommand
- [x] --output/-o
- [x] --no-open
- [x] `sync-ai` subcommand
- [x] --tool choices
- [x] --path with auto-detect fallback

### F6: AIKnowledgeBase (knowledge_base.py) - 100%

- [x] TYPE_RULE = "ai-rule"
- [x] TYPE_CONTEXT = "ai-context"
- [x] TYPE_PREFERENCE = "ai-preference"
- [x] TYPE_GUIDE = "ai-guide"
- [x] TYPE_LEARNED = "ai-learned"
- [x] __init__(memory)
- [x] detect_project(project_path) -> dict
- [x] Returns: type, name, tech_stack, entry_points, structure, package_manager, test_framework
- [x] Python detection (pyproject.toml, setup.py, requirements.txt)
- [x] Node.js detection (package.json)
- [x] Go detection (go.mod)
- [x] Rust detection (Cargo.toml)
- [x] generate_project_context(project_path) -> str
- [x] get_context(project_path) -> str (auto-generate if missing)
- [x] get_rules() -> list[str]
- [x] learn_preference(key, value) -> str (with dedup/update)
- [x] get_preferences() -> dict[str, str]
- [x] sync_ai_config(tool, config_path) -> int
- [x] _detect_from_pyproject(path) -> dict
- [x] _detect_from_package_json(path) -> dict
- [x] _scan_structure(root) -> str
- [x] _parse_markdown_rules(content) -> list[str]

### F5: MCP Tools (mcp_server.py) - 93%

- [x] memory_get_context(project_path)
- [x] memory_get_rules()
- [x] memory_learn_preference(key, value)
- [x] memory_sync_ai_config(tool, config_path)
- [~] memory_visualize() - zones returned but no top_memories per zone
- [x] memory_topics(limit) - enhanced with stopword filtering
- [x] memory_onboard_status()

### F4: MemoryVisualizer (viz.py) - 88%

- [x] MemoryVisualizer class
- [x] __init__(memory)
- [x] generate_html() with DATA placeholder replacement
- [x] save_and_open(output_path, open_browser) -> str
- [x] _collect_data() -> dict with zones, edges, stats
- [x] _item_to_dict(item) -> dict
- [x] Dark theme #0d1117
- [x] 4 tabs: Solar System, Memory List, Graph, Stats
- [x] Solar System: 5 concentric rings (SVG)
- [x] Solar System: memory dots sized by importance, colored by zone
- [x] Solar System: click dot -> show detail panel
- [x] Solar System: zone labels with counts
- [x] Memory List: search input (real-time filter)
- [x] Memory List: zone filter dropdown
- [x] Memory List: source filter dropdown (bonus)
- [x] Memory List: sortable columns (content, zone, importance, score, recalls, date, source)
- [x] Memory List: click row -> showDetail
- [x] Graph: force-directed layout (spring simulation, 50 iterations)
- [x] Graph: nodes colored by zone
- [x] Graph: edges from graph relationships
- [x] Graph: click node -> showDetail
- [ ] Graph: drag to rearrange nodes
- [x] Stats: zone usage bar charts
- [x] Stats: import source breakdown
- [ ] Stats: score distribution histogram
- [ ] Stats: top 10 most-recalled memories

### Config (config.py) - 100%

- [x] OnboardConfig dataclass
- [x] enabled, max_file_size, max_scan_depth
- [x] default_categories, skip_patterns, sensitive_patterns
- [x] KnowledgeBaseConfig dataclass
- [x] enabled, auto_detect_project, auto_import_ai_configs
- [x] preference_importance=0.95, rule_importance=0.9, context_importance=0.85
- [x] Both added to StellarConfig

### Models (models.py) - 100%

- [x] ScanResult with all design fields
- [x] ScanSummary with all design fields
- [x] ImportResult with all design fields
- [x] ChunkInfo with all design fields

---

## Identified Gaps (4 items)

### Gap 1: viz.py - Score Distribution Histogram (Minor)
- **Design**: Stats view includes "Score distribution histogram"
- **Implementation**: Has type breakdown bars instead
- **Impact**: Low - type breakdown provides useful info
- **Fix**: Add histogram as additional stat card

### Gap 2: viz.py - Top 10 Most-Recalled Memories (Minor)
- **Design**: Stats view includes "Top 10 most-recalled memories"
- **Implementation**: Not present
- **Impact**: Low - data is available, just not displayed
- **Fix**: Add ranked list card to stats grid

### Gap 3: viz.py - Graph Drag to Rearrange (Minor)
- **Design**: "Drag to rearrange" graph nodes
- **Implementation**: Static layout after force simulation
- **Impact**: Low - graph is still readable
- **Fix**: Add mousedown/mousemove/mouseup handlers for dragging

### Gap 4: scanner.py - CLAUDE_PROJECTS_DIR (Minor)
- **Design**: `CLAUDE_PROJECTS_DIR = ".claude/projects"` for per-project memory scanning
- **Implementation**: Not implemented
- **Impact**: Low - CLAUDE_MEMORY_DIR covers main memory files
- **Fix**: Add constant and scan logic in _scan_ai_configs

---

## Enhancements Over Design

1. **importer.py**: Added `_import_bookmarks()` for Chrome-format JSON bookmark parsing
2. **importer.py**: Graph edges between chunks from same file (`derived_from`)
3. **viz.py**: Added `open_browser` parameter to `save_and_open()`
4. **viz.py**: Added source filter dropdown in Memory List
5. **viz.py**: Added Summary card with total count + edge count
6. **viz.py**: Added type breakdown bar chart
7. **mcp_server.py**: Enhanced `memory_topics` with stopword filtering
8. **mcp_server.py**: Added `limit` clamping (1-50) in memory_topics
9. **cli.py**: EOFError/KeyboardInterrupt handling in interactive prompts
10. **viz.py**: `_find_full_id()` helper for short-to-full ID resolution

---

## Verdict

**Match Rate: 96% >= 90% threshold. PASS.**

All 4 gaps are minor cosmetic/UI items in viz.py and scanner.py. The core functionality for all 6 features (F1-F6) is fully implemented. Multiple enhancements beyond the design were added, improving robustness and user experience.

Recommended next step: `/pdca report smart-onboarding`
