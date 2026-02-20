# Plan: smart-onboarding

> Stellar Memory v2.1.0 - Smart Onboarding (Auto-Import + AI Knowledge Base + Visualization)

## Background

Currently, Stellar Memory starts empty after installation. Users must manually store memories one-by-one through AI conversation or CLI. This creates a "cold start" problem - the AI has no context about the user until enough memories accumulate organically.

Additionally, AI tools each maintain their own fragmented configuration systems - Claude uses `CLAUDE.md` + `.claude/memory/`, Cursor uses `.cursorrules`, Copilot uses `.github/copilot-instructions.md`, Windsurf uses `.windsurfrules`. Users must duplicate instructions across tools, and none of these systems share knowledge with each other.

Users also have no intuitive way to see what Stellar Memory has stored or how their memories are organized.

## Problem

1. **Cold Start**: New users see no immediate value. Stellar Memory is only useful after accumulating memories over time.
2. **No Personalization Without Effort**: Users must explicitly tell the AI things for it to remember.
3. **Fragmented AI Memory**: Each AI tool has its own siloed config/memory. Skills, rules, and guides don't transfer between tools.
4. **Opaque Storage**: Users cannot easily see what's stored, how memories are scored, or how the zone structure works.

## Vision

Stellar Memory becomes the **universal brain** for all AI tools. Instead of each AI maintaining separate memory files, they all read from and write to Stellar Memory via MCP. One memory, every AI.

## Proposal

### F1: Local Data Scanner (`LocalScanner`)

A permission-based scanner that discovers importable data on the user's computer.

**Scan Targets** (with user opt-in per category):

| Category | Locations | File Types |
|----------|-----------|------------|
| Documents | `~/Documents`, `~/Desktop` | `.txt`, `.md`, `.rst` |
| Notes | `~/Obsidian`, `~/Notes`, `~/.logseq` | `.md` |
| AI Configs | `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.windsurfrules`, `.claude/memory/` | `.md`, `.json` |
| AI Chat History | Claude Desktop logs, ChatGPT exports | `.json`, `.jsonl` |
| Code Projects | `~/Projects`, `~/repos`, `~/dev` | `README.md`, `.env.example` |
| Bookmarks | Browser bookmark files | `.json`, `.html` |

**AI Config Discovery** (special handling):
- Scan current directory + home directory + recent git repos for AI config files
- Parse `CLAUDE.md` → extract coding conventions, project rules, preferences
- Parse `.cursorrules` → extract editor-specific instructions
- Parse `.claude/memory/*.md` → extract learned patterns
- Parse `.github/copilot-instructions.md` → extract Copilot guidelines
- Tag all as `{category: "ai-config", tool: "claude|cursor|copilot|windsurf"}`
- High importance (0.9) - these are active instructions the AI needs

**Privacy Rules**:
- Never scan without explicit user consent (interactive prompt)
- Show exactly what will be scanned before proceeding
- Skip binary files, images, videos
- Skip files > 100KB (likely not personal notes)
- Skip hidden directories (`.git`, `node_modules`, `__pycache__`)
- Never read `.env`, credentials, SSH keys, or password files
- User can exclude paths via `--exclude` flag

**Output**: List of `ScanResult(path, category, size, preview)` for user review before import.

### F2: Smart Importer (`SmartImporter`)

Processes scanned files into Stellar Memory with intelligent categorization.

**Pipeline**:
1. Read file content (respecting size limit)
2. Split large documents into chunks (max 500 chars per memory)
3. Auto-evaluate importance using `RuleBasedEvaluator`
4. Auto-detect content type via `multimodal.detect_content_type()`
5. Tag with metadata: `{source: "auto-import", file: path, category: category}`
6. Store via `memory.store()` with `auto_evaluate=True`
7. Build graph edges between memories from same file (`derived_from`)

**Smart Features**:
- Deduplication: skip content already stored (Jaccard similarity > 0.8)
- Category-based importance: personal notes = 0.7, code READMEs = 0.5, bookmarks = 0.3
- Progress reporting: show import count, skipped count, errors

### F3: Interactive Onboarding Wizard (`stellar-memory onboard`)

CLI command that guides first-time users through the entire process.

**Flow**:
```
Step 1: Welcome + explain what will happen
Step 2: Show scan categories with checkboxes (user selects which to scan)
Step 3: Scan selected categories, show found items count
Step 4: Show preview of what will be imported (top 10 items per category)
Step 5: User confirms → import begins with progress bar
Step 6: Show summary (imported X memories across Y zones)
Step 7: Suggest "Try asking your AI about [topic from imported data]"
```

### F4: Memory Visualization (`stellar-memory viz`)

A single-file HTML visualization that opens in the user's browser.

**Views**:

| View | Description |
|------|-------------|
| Solar System | Zone rings with memory dots (enhanced from dashboard), click to see content |
| Memory List | Searchable, filterable table of all memories with zone/score/date |
| Graph View | Interactive node-link diagram showing memory relationships |
| Timeline | Chronological view of when memories were created/recalled |
| Stats | Zone usage bars, score distribution histogram, top topics |

**Implementation**:
- CLI command `stellar-memory viz` generates a self-contained HTML file and opens it
- No server needed - reads from SQLite DB directly, embeds data as JSON in HTML
- Uses vanilla JS + SVG (no framework dependencies)
- Dark theme matching landing page aesthetic
- Export as PNG/SVG option for sharing

### F5: MCP Tools for Visualization

New MCP tools so AI assistants can help users explore their memories.

| Tool | Description |
|------|-------------|
| `memory_visualize()` | Returns zone summary + top memories per zone as formatted text |
| `memory_topics()` | Clusters memories by topic, returns topic list with counts |
| `memory_timeline(days)` | Returns activity timeline for last N days |
| `memory_suggest_import()` | Suggests files to import based on conversation context |

### F6: AI Knowledge Base (`AIKnowledgeBase`)

Pre-built knowledge packs that make Stellar Memory immediately useful for AI tools - replacing the need for per-tool configuration files.

**Concept**: Instead of users writing `CLAUDE.md` or `.cursorrules`, Stellar Memory ships with built-in knowledge that any AI can query via MCP.

**Built-in Knowledge Packs**:

| Pack | Contents | Replaces |
|------|----------|----------|
| `coding-conventions` | Common coding standards (naming, formatting, patterns) | `CLAUDE.md` coding rules |
| `project-context` | Auto-detected project structure, tech stack, dependencies | `CLAUDE.md` project overview |
| `tool-guides` | How to use common dev tools (git, npm, docker, etc.) | Agent skills/documentation |
| `user-preferences` | Learned user preferences (language, style, workflow) | `.claude/memory/`, `.cursorrules` |
| `mcp-guide` | MCP protocol usage patterns, available tools reference | MCP documentation |

**How It Works**:
1. On first run, detect project type (Python/Node/Go/etc.) from files present
2. Generate `project-context` pack automatically (read `package.json`, `pyproject.toml`, directory structure)
3. Load `coding-conventions` pack matching detected language
4. Import any existing AI config files found by F1 Scanner
5. Store all as high-importance memories (Zone 0-1) with `{type: "ai-knowledge", pack: "..."}`
6. AI tools query these via `memory_recall("coding conventions")` or dedicated MCP tool

**Sync Mechanism** (AI Config → Stellar Memory → All AI Tools):
```
CLAUDE.md ──┐
.cursorrules ──┤
copilot.md ──┤──→ Stellar Memory ──→ Any AI via MCP
.windsurfrules ──┤
user preferences ──┘
```

**New MCP Tools**:

| Tool | Description |
|------|-------------|
| `memory_get_context(project_path)` | Returns project context: tech stack, structure, conventions |
| `memory_get_rules()` | Returns all active coding rules/preferences for current project |
| `memory_learn_preference(key, value)` | Store a user preference (e.g., "always use TypeScript") |
| `memory_sync_ai_config(tool, config_path)` | Import an AI config file into Stellar Memory |

**User Preference Learning**:
- When AI stores a preference via `memory_learn_preference`, it's available to ALL AI tools
- Example: User tells Claude "always use snake_case" → stored in Stellar Memory → Cursor also follows it
- Preferences are Zone 0 (Core) memories with highest importance

## Feature Summary

| ID | Feature | Priority | Complexity | New Files |
|----|---------|----------|------------|-----------|
| F1 | Local Data Scanner | High | Medium | `scanner.py` |
| F2 | Smart Importer | High | Medium | `importer.py` |
| F3 | Onboarding Wizard | High | Low | CLI additions |
| F4 | Memory Visualization | Medium | High | `viz.py`, `viz_template.html` |
| F5 | MCP Viz Tools | Medium | Low | MCP additions |
| F6 | AI Knowledge Base | **Critical** | Medium | `knowledge_base.py`, MCP additions |

## Implementation Order

```
F6 (AI Knowledge Base) → F1 (Scanner) → F2 (Importer) → F3 (Wizard CLI) → F5 (MCP Tools) → F4 (Visualization)
```

F6 is the highest-value feature: makes Stellar Memory the universal AI brain.
F1-F3 solve cold start by importing user's existing data.
F4-F5 provide visibility into what was imported.

## Constraints

- Zero new mandatory dependencies (all features work with stdlib)
- File scanning must be opt-in with clear consent UX
- Import must be idempotent (running twice doesn't create duplicates)
- Visualization HTML must be self-contained (no CDN dependencies)
- All features must work offline (no network required)

## Success Criteria

- First-time user can go from `pip install` to 50+ imported memories in under 2 minutes
- AI tools can query project context and coding rules via MCP without any config file
- User preference set in one AI tool is automatically available in all other AI tools
- User can visualize all stored memories with a single command
- No data is accessed without explicit user consent
- Import is idempotent and safe to run multiple times
- Stellar Memory fully replaces `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`

## Risks

| Risk | Mitigation |
|------|------------|
| Privacy concerns | Strict opt-in, preview before import, skip sensitive files |
| Large file scanning takes too long | Size limits, directory depth limits, async scanning |
| Duplicate imports | Jaccard dedup + source metadata tracking |
| Cross-platform path differences | Use `pathlib.Path.home()`, platform-specific path constants |
| AI config format differences | Normalize all configs to plain-text rules before storing |
| Knowledge pack outdated | Version tag on packs, auto-refresh on project structure change |
