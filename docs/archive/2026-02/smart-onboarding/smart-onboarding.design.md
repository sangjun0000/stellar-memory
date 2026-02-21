# Design: smart-onboarding

> Stellar Memory v2.1.0 - Smart Onboarding (Auto-Import + AI Knowledge Base + Visualization)

## Reference

- Plan: `docs/01-plan/features/smart-onboarding.plan.md`

## Architecture Overview

```
                  ┌─────────────────────────────────────────────┐
                  │              CLI Commands                    │
                  │  onboard / viz / sync-ai-config              │
                  └──────┬──────────┬──────────┬────────────────┘
                         │          │          │
              ┌──────────▼──┐ ┌────▼─────┐ ┌──▼──────────────┐
              │ LocalScanner │ │ Importer │ │ AIKnowledgeBase │
              │  (scanner.py)│ │(importer │ │(knowledge_base  │
              │              │ │  .py)    │ │  .py)           │
              └──────────────┘ └──────────┘ └─────────────────┘
                         │          │          │
                         └──────────▼──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   StellarMemory      │
                         │   .store() / .recall()│
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────▼─────────────────────┐
              │               MCP Server                   │
              │  memory_get_context / memory_get_rules     │
              │  memory_learn_preference / memory_topics    │
              │  memory_visualize / memory_onboard_status   │
              └─────────────────────┬─────────────────────┘
                                    │
              ┌─────────────────────▼─────────────────────┐
              │          Any AI Tool (via MCP)              │
              │  Claude / Cursor / ChatGPT / Windsurf      │
              └───────────────────────────────────────────┘
```

## New Files

| File | Feature | Description |
|------|---------|-------------|
| `stellar_memory/scanner.py` | F1 | Local data scanner with category-based discovery |
| `stellar_memory/importer.py` | F2 | Smart import pipeline with dedup and chunking |
| `stellar_memory/knowledge_base.py` | F6 | AI Knowledge Base with project detection and packs |
| `stellar_memory/viz.py` | F4 | Visualization HTML generator |

## Modified Files

| File | Feature | Changes |
|------|---------|---------|
| `stellar_memory/cli.py` | F3 | Add `onboard`, `viz`, `sync-ai` subcommands |
| `stellar_memory/mcp_server.py` | F5/F6 | Add 7 new MCP tools |
| `stellar_memory/models.py` | F1/F2 | Add `ScanResult`, `ImportResult`, `OnboardReport` |
| `stellar_memory/config.py` | F6 | Add `OnboardConfig`, `KnowledgeBaseConfig` |

---

## F1: LocalScanner (`scanner.py`)

### Data Models (in `models.py`)

```python
@dataclass
class ScanResult:
    path: str               # absolute file path
    category: str           # "documents" | "notes" | "ai-config" | "chat-history" | "code" | "bookmarks"
    size: int               # file size in bytes
    preview: str            # first 200 chars of content
    ai_tool: str | None     # for ai-config: "claude" | "cursor" | "copilot" | "windsurf"
    importable: bool        # True if passes all filters

@dataclass
class ScanSummary:
    total_found: int
    by_category: dict[str, int]     # category → count
    total_size_bytes: int
    skipped_count: int
    results: list[ScanResult]
```

### Class Design

```python
# scanner.py

class LocalScanner:
    """Discovers importable files on the user's computer."""

    # Category → (search_paths, file_patterns)
    SCAN_TARGETS: dict[str, ScanCategory]

    # Files/dirs to always skip
    SKIP_PATTERNS: set[str]  # {".git", "node_modules", "__pycache__", ".env", ...}
    SENSITIVE_PATTERNS: set[str]  # {"id_rsa", ".ssh", "credentials", "password", ...}

    MAX_FILE_SIZE: int = 102_400  # 100KB
    MAX_DEPTH: int = 3            # directory recursion depth

    def __init__(self, categories: list[str] | None = None,
                 exclude_paths: list[str] | None = None):
        ...

    def scan(self, categories: list[str] | None = None) -> ScanSummary:
        """Scan selected categories. Returns results for user review."""

    def scan_ai_configs(self) -> list[ScanResult]:
        """Special scanner for AI configuration files."""

    def _scan_category(self, category: str) -> list[ScanResult]:
        """Scan a single category."""

    def _is_safe(self, path: Path) -> bool:
        """Check if file is safe to read (not sensitive, not binary, within size)."""

    def _get_preview(self, path: Path) -> str:
        """Read first 200 chars of file for preview."""
```

### Scan Category Definitions

```python
@dataclass
class ScanCategory:
    name: str
    search_paths: list[str]      # relative to home dir or absolute
    file_patterns: list[str]     # glob patterns
    importance: float            # default importance for this category
    recursive: bool = True

CATEGORIES = {
    "documents": ScanCategory(
        name="Documents",
        search_paths=["Documents", "Desktop"],
        file_patterns=["*.txt", "*.md", "*.rst"],
        importance=0.5,
    ),
    "notes": ScanCategory(
        name="Notes",
        search_paths=["Obsidian", "Notes", ".logseq", "Notion"],
        file_patterns=["*.md"],
        importance=0.7,
    ),
    "ai-config": ScanCategory(
        name="AI Configurations",
        search_paths=["."],  # current dir + home
        file_patterns=["CLAUDE.md", ".cursorrules", ".windsurfrules",
                       ".github/copilot-instructions.md"],
        importance=0.9,
    ),
    "chat-history": ScanCategory(
        name="AI Chat History",
        search_paths=[
            "AppData/Roaming/Claude/logs",       # Windows
            ".config/claude/logs",                # Linux
            "Library/Application Support/Claude", # macOS
        ],
        file_patterns=["*.json", "*.jsonl"],
        importance=0.6,
    ),
    "code": ScanCategory(
        name="Code Projects",
        search_paths=["Projects", "repos", "dev", "workspace"],
        file_patterns=["README.md"],
        importance=0.5,
        recursive=False,  # only top-level READMEs
    ),
    "bookmarks": ScanCategory(
        name="Browser Bookmarks",
        search_paths=[
            "AppData/Local/Google/Chrome/User Data/Default",
            "AppData/Local/BraveSoftware/Brave-Browser/User Data/Default",
            ".config/google-chrome/Default",
            "Library/Application Support/Google/Chrome/Default",
        ],
        file_patterns=["Bookmarks"],
        importance=0.3,
    ),
}
```

### AI Config Parsers

```python
# Inside scanner.py

AI_CONFIG_FILES = {
    "CLAUDE.md": "claude",
    ".cursorrules": "cursor",
    ".windsurfrules": "windsurf",
    ".github/copilot-instructions.md": "copilot",
}

CLAUDE_MEMORY_DIR = ".claude/memory"  # contains *.md files
CLAUDE_PROJECTS_DIR = ".claude/projects"  # contains per-project memory

def _detect_ai_configs(self, search_dirs: list[Path]) -> list[ScanResult]:
    """Find all AI config files in given directories."""
    results = []
    for d in search_dirs:
        for filename, tool in AI_CONFIG_FILES.items():
            path = d / filename
            if path.exists():
                results.append(ScanResult(
                    path=str(path),
                    category="ai-config",
                    size=path.stat().st_size,
                    preview=self._get_preview(path),
                    ai_tool=tool,
                    importable=True,
                ))
        # Claude memory directory
        memory_dir = d / CLAUDE_MEMORY_DIR
        if memory_dir.is_dir():
            for md_file in memory_dir.glob("*.md"):
                results.append(ScanResult(
                    path=str(md_file),
                    category="ai-config",
                    size=md_file.stat().st_size,
                    preview=self._get_preview(md_file),
                    ai_tool="claude-memory",
                    importable=True,
                ))
    return results
```

---

## F2: SmartImporter (`importer.py`)

### Data Models

```python
@dataclass
class ImportResult:
    total_processed: int
    imported: int
    skipped_duplicate: int
    skipped_error: int
    by_category: dict[str, int]     # category → imported count
    by_zone: dict[int, int]         # zone → count
    memory_ids: list[str]           # IDs of imported memories
    errors: list[str]

@dataclass
class ChunkInfo:
    content: str
    index: int          # chunk number within file
    total_chunks: int
    source_path: str
```

### Class Design

```python
# importer.py

class SmartImporter:
    """Processes scan results into Stellar Memory."""

    CHUNK_SIZE: int = 500          # max chars per memory
    DEDUP_THRESHOLD: float = 0.8   # Jaccard similarity threshold
    IMPORTANCE_BY_CATEGORY: dict[str, float] = {
        "ai-config": 0.9,
        "notes": 0.7,
        "chat-history": 0.6,
        "documents": 0.5,
        "code": 0.5,
        "bookmarks": 0.3,
    }

    def __init__(self, memory: StellarMemory):
        self._memory = memory

    def import_scan_results(self, results: list[ScanResult],
                            progress_callback=None) -> ImportResult:
        """Import all scan results into memory."""

    def import_file(self, scan_result: ScanResult) -> list[str]:
        """Import a single file. Returns list of created memory IDs."""

    def import_ai_config(self, scan_result: ScanResult) -> list[str]:
        """Special handler for AI config files. Parses into structured rules."""

    def _chunk_content(self, content: str, source: str) -> list[ChunkInfo]:
        """Split content into chunks at paragraph boundaries."""

    def _is_duplicate(self, content: str) -> bool:
        """Check if similar content already exists via recall + Jaccard."""

    def _jaccard_similarity(self, a: str, b: str) -> float:
        """Word-level Jaccard similarity."""

    def _build_metadata(self, scan_result: ScanResult,
                        chunk: ChunkInfo | None = None) -> dict:
        """Build metadata dict for a memory item."""
```

### AI Config Import Logic

```python
def import_ai_config(self, scan_result: ScanResult) -> list[str]:
    """Parse AI config files into individual rule memories."""
    content = Path(scan_result.path).read_text(encoding="utf-8", errors="replace")
    ids = []

    if scan_result.ai_tool in ("claude", "cursor", "copilot", "windsurf"):
        # Parse markdown sections into individual rules
        rules = self._parse_markdown_rules(content)
        for rule in rules:
            if self._is_duplicate(rule):
                continue
            item = self._memory.store(
                content=rule,
                importance=0.9,
                metadata={
                    "source": "auto-import",
                    "type": "ai-rule",
                    "ai_tool": scan_result.ai_tool,
                    "file": scan_result.path,
                    "category": "ai-config",
                },
                auto_evaluate=False,  # keep importance at 0.9
            )
            ids.append(item.id)
    elif scan_result.ai_tool == "claude-memory":
        # Import Claude memory files as-is
        item = self._memory.store(
            content=content,
            importance=0.85,
            metadata={
                "source": "auto-import",
                "type": "ai-learned",
                "ai_tool": "claude",
                "file": scan_result.path,
                "category": "ai-config",
            },
            auto_evaluate=False,
        )
        ids.append(item.id)
    return ids

def _parse_markdown_rules(self, content: str) -> list[str]:
    """Split markdown into section-level rules.
    Each H2/H3 section becomes a separate rule memory.
    """
    sections = []
    current = []
    for line in content.split("\n"):
        if line.startswith(("## ", "### ")) and current:
            text = "\n".join(current).strip()
            if len(text) > 20:  # skip tiny sections
                sections.append(text)
            current = [line]
        else:
            current.append(line)
    if current:
        text = "\n".join(current).strip()
        if len(text) > 20:
            sections.append(text)
    return sections
```

---

## F3: Onboarding Wizard (CLI additions in `cli.py`)

### New Subcommand: `stellar-memory onboard`

```python
# In cli.py subparser setup
p_onboard = subparsers.add_parser("onboard",
    help="Smart onboarding - scan and import your data")
p_onboard.add_argument("--categories", "-c", nargs="*",
    default=None,
    help="Categories to scan: documents, notes, ai-config, chat-history, code, bookmarks")
p_onboard.add_argument("--exclude", nargs="*", default=None,
    help="Paths to exclude from scanning")
p_onboard.add_argument("--yes", "-y", action="store_true",
    help="Skip confirmation prompts")
p_onboard.add_argument("--dry-run", action="store_true",
    help="Scan only, don't import")
```

### Wizard Flow

```python
def _cmd_onboard(args, config):
    """Interactive onboarding wizard."""
    from stellar_memory.scanner import LocalScanner
    from stellar_memory.importer import SmartImporter

    # Step 1: Welcome
    print("=" * 50)
    print("  Stellar Memory - Smart Onboarding")
    print("=" * 50)
    print()
    print("This wizard will scan your computer for useful data")
    print("and import it into Stellar Memory.")
    print("Nothing is accessed without your permission.")
    print()

    # Step 2: Category selection (if not specified via --categories)
    categories = args.categories
    if categories is None and not args.yes:
        categories = _interactive_category_select()

    # Step 3: Scan
    scanner = LocalScanner(exclude_paths=args.exclude)
    print("\nScanning...")
    summary = scanner.scan(categories=categories)
    print(f"\nFound {summary.total_found} items:")
    for cat, count in summary.by_category.items():
        print(f"  {cat}: {count} files")

    # Step 4: Preview
    if not args.yes:
        print("\nPreview (top 5 per category):")
        for result in summary.results[:20]:
            print(f"  [{result.category}] {result.path}")
            print(f"    {result.preview[:80]}...")
        print()

    # Step 5: Confirm
    if args.dry_run:
        print("Dry run - no import performed.")
        return
    if not args.yes:
        answer = input("Import these items? [Y/n]: ").strip().lower()
        if answer and answer != "y":
            print("Cancelled.")
            return

    # Step 6: Import
    memory = StellarMemory(config)
    memory.start()
    importer = SmartImporter(memory)
    result = importer.import_scan_results(
        summary.results,
        progress_callback=lambda done, total: print(f"\r  Importing... {done}/{total}", end=""),
    )
    print()

    # Step 7: Summary
    print(f"\nImport complete!")
    print(f"  Imported: {result.imported}")
    print(f"  Skipped (duplicate): {result.skipped_duplicate}")
    if result.skipped_error:
        print(f"  Errors: {result.skipped_error}")
    stats = memory.stats()
    print(f"\nZone distribution:")
    for z, count in sorted(stats.zone_counts.items()):
        print(f"  Zone {z}: {count} memories")
    print(f"\nTry: stellar-memory viz")
    memory.stop()


def _interactive_category_select() -> list[str]:
    """Show category checkboxes and return selected categories."""
    all_cats = ["ai-config", "documents", "notes", "chat-history", "code", "bookmarks"]
    print("Select categories to scan:")
    for i, cat in enumerate(all_cats, 1):
        default = "*" if cat == "ai-config" else " "
        print(f"  [{default}] {i}. {cat}")
    print()
    selection = input("Enter numbers (e.g., 1,2,3) or 'all' [default: 1]: ").strip()
    if not selection:
        return ["ai-config"]
    if selection.lower() == "all":
        return all_cats
    indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]
    return [all_cats[i] for i in indices if 0 <= i < len(all_cats)]
```

---

## F6: AI Knowledge Base (`knowledge_base.py`)

### Class Design

```python
# knowledge_base.py

class AIKnowledgeBase:
    """Universal AI knowledge store - replaces per-tool config files."""

    # Metadata type constants
    TYPE_RULE = "ai-rule"           # coding convention / project rule
    TYPE_CONTEXT = "ai-context"     # project structure / tech stack
    TYPE_PREFERENCE = "ai-preference"  # user preference (snake_case, etc.)
    TYPE_GUIDE = "ai-guide"         # tool usage guide
    TYPE_LEARNED = "ai-learned"     # imported from existing AI memory

    def __init__(self, memory: StellarMemory):
        self._memory = memory

    def detect_project(self, project_path: str | None = None) -> dict:
        """Auto-detect project type, tech stack, and structure.

        Returns:
            {
                "type": "python" | "node" | "go" | "rust" | "mixed",
                "name": "my-project",
                "tech_stack": ["python", "fastapi", "sqlite"],
                "entry_points": ["stellar_memory/cli.py"],
                "structure": "src/module or flat",
                "package_manager": "pip" | "npm" | "cargo",
                "test_framework": "pytest" | "jest" | "go test",
            }
        """

    def generate_project_context(self, project_path: str | None = None) -> str:
        """Generate and store project context memory.

        Reads pyproject.toml / package.json / go.mod / Cargo.toml,
        scans directory structure, identifies key files.
        Returns the stored memory ID.
        """

    def get_context(self, project_path: str | None = None) -> str:
        """Retrieve stored project context. If none exists, generate it."""

    def get_rules(self) -> list[str]:
        """Get all active coding rules/preferences.

        Queries memories with metadata type in (ai-rule, ai-preference).
        Returns list of rule strings sorted by importance.
        """

    def learn_preference(self, key: str, value: str) -> str:
        """Store a user preference. Returns memory ID.

        If a preference with same key exists, updates it (forget old, store new).
        """

    def sync_ai_config(self, tool: str, config_path: str) -> int:
        """Import an AI config file.

        Parses the file, stores each rule as a memory.
        Returns number of rules imported.
        """

    def get_preferences(self) -> dict[str, str]:
        """Get all stored preferences as key-value dict."""

    def _detect_from_pyproject(self, path: Path) -> dict:
        """Extract project info from pyproject.toml."""

    def _detect_from_package_json(self, path: Path) -> dict:
        """Extract project info from package.json."""

    def _scan_structure(self, path: Path) -> dict:
        """Scan directory structure (top 2 levels)."""
```

### Project Detection Logic

```python
def detect_project(self, project_path: str | None = None) -> dict:
    root = Path(project_path or ".").resolve()
    info = {"type": "unknown", "name": root.name, "tech_stack": [],
            "entry_points": [], "package_manager": None, "test_framework": None}

    # Python
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    requirements = root / "requirements.txt"
    if pyproject.exists() or setup_py.exists() or requirements.exists():
        info["type"] = "python"
        info["tech_stack"].append("python")
        info["package_manager"] = "pip"
        info["test_framework"] = "pytest"
        if pyproject.exists():
            info.update(self._detect_from_pyproject(pyproject))

    # Node.js
    pkg_json = root / "package.json"
    if pkg_json.exists():
        info["type"] = "node" if info["type"] == "unknown" else "mixed"
        info["tech_stack"].append("node")
        info["package_manager"] = "npm"
        info.update(self._detect_from_package_json(pkg_json))

    # Go
    go_mod = root / "go.mod"
    if go_mod.exists():
        info["type"] = "go" if info["type"] == "unknown" else "mixed"
        info["tech_stack"].append("go")
        info["test_framework"] = "go test"

    # Rust
    cargo = root / "Cargo.toml"
    if cargo.exists():
        info["type"] = "rust" if info["type"] == "unknown" else "mixed"
        info["tech_stack"].append("rust")
        info["package_manager"] = "cargo"

    # Structure scan
    info["structure"] = self._scan_structure(root)
    return info
```

### Context Generation

```python
def generate_project_context(self, project_path: str | None = None) -> str:
    info = self.detect_project(project_path)

    context_text = f"""## Project: {info['name']}
Type: {info['type']}
Tech Stack: {', '.join(info['tech_stack'])}
Package Manager: {info.get('package_manager', 'N/A')}
Test Framework: {info.get('test_framework', 'N/A')}

### Directory Structure
{info.get('structure', 'N/A')}

### Entry Points
{chr(10).join('- ' + e for e in info.get('entry_points', []))}
"""

    # Check for existing context and update
    existing = self._memory.recall("project context tech stack", limit=1)
    for item in existing:
        if (item.metadata or {}).get("type") == self.TYPE_CONTEXT:
            self._memory.forget(item.id)

    item = self._memory.store(
        content=context_text,
        importance=0.9,
        metadata={
            "type": self.TYPE_CONTEXT,
            "source": "auto-detect",
            "project_name": info["name"],
            "project_type": info["type"],
        },
        auto_evaluate=False,
    )
    return item.id
```

---

## F5: MCP Tools (additions to `mcp_server.py`)

### New MCP Tools

```python
# --- Smart Onboarding Tools ---

@mcp.tool()
def memory_get_context(project_path: str = "") -> str:
    """Get project context: tech stack, structure, conventions.
    Auto-detects if not previously generated.

    Args:
        project_path: Optional path to project root (default: current dir)
    """
    from stellar_memory.knowledge_base import AIKnowledgeBase
    kb = AIKnowledgeBase(memory)
    context = kb.get_context(project_path or None)
    return json.dumps({"context": context})

@mcp.tool()
def memory_get_rules() -> str:
    """Get all active coding rules and user preferences.
    Returns rules sorted by importance.
    """
    from stellar_memory.knowledge_base import AIKnowledgeBase
    kb = AIKnowledgeBase(memory)
    rules = kb.get_rules()
    preferences = kb.get_preferences()
    return json.dumps({
        "rules": rules,
        "preferences": preferences,
        "total": len(rules) + len(preferences),
    })

@mcp.tool()
def memory_learn_preference(key: str, value: str) -> str:
    """Store a user preference that applies across all AI tools.

    Args:
        key: Preference key (e.g., "naming_style", "language", "framework")
        value: Preference value (e.g., "snake_case", "Korean", "FastAPI")
    """
    from stellar_memory.knowledge_base import AIKnowledgeBase
    kb = AIKnowledgeBase(memory)
    mid = kb.learn_preference(key, value)
    return json.dumps({"stored": True, "memory_id": mid, "key": key, "value": value})

@mcp.tool()
def memory_sync_ai_config(tool: str, config_path: str) -> str:
    """Import an AI configuration file into Stellar Memory.

    Args:
        tool: AI tool name ("claude", "cursor", "copilot", "windsurf")
        config_path: Path to the config file
    """
    from stellar_memory.knowledge_base import AIKnowledgeBase
    kb = AIKnowledgeBase(memory)
    count = kb.sync_ai_config(tool, config_path)
    return json.dumps({"imported_rules": count, "tool": tool})

@mcp.tool()
def memory_visualize() -> str:
    """Get a formatted summary of all memory zones and top memories."""
    stats = memory.stats()
    result = {"zones": []}
    for zone_id in sorted(stats.zone_counts.keys()):
        count = stats.zone_counts[zone_id]
        cap = stats.zone_capacities.get(zone_id)
        zone_info = {
            "zone": zone_id,
            "count": count,
            "capacity": cap,
            "usage": f"{count}/{cap}" if cap else f"{count}/unlimited",
        }
        # Get top 3 memories per zone
        items = memory.recall("", limit=3)  # zone-filtered internally
        zone_info["top_memories"] = [
            {"id": item.id[:8], "content": item.content[:100],
             "importance": item.arbitrary_importance}
            for item in items if item.zone == zone_id
        ]
        result["zones"].append(zone_info)
    result["total"] = stats.total_memories
    return json.dumps(result)

@mcp.tool()
def memory_topics(limit: int = 10) -> str:
    """Cluster memories by topic and return topic list with counts.

    Args:
        limit: Maximum number of topics to return
    """
    # Simple keyword-based clustering
    all_items = []
    for z in range(5):
        items = memory.recall("", limit=100)
        all_items.extend([i for i in items if i.zone == z])

    # Extract keywords and cluster
    from collections import Counter
    word_counts = Counter()
    for item in all_items:
        words = set(item.content.lower().split())
        # Filter stopwords (basic)
        words = {w for w in words if len(w) > 3}
        word_counts.update(words)

    topics = [{"topic": word, "count": count}
              for word, count in word_counts.most_common(limit)]
    return json.dumps({"topics": topics, "total_memories": len(all_items)})

@mcp.tool()
def memory_onboard_status() -> str:
    """Check onboarding status - what has been imported and what's available."""
    stats = memory.stats()
    # Count by source type
    from collections import Counter
    source_counts = Counter()
    type_counts = Counter()
    all_items = memory.recall("", limit=1000)
    for item in all_items:
        meta = item.metadata or {}
        source_counts[meta.get("source", "manual")] += 1
        type_counts[meta.get("type", "general")] += 1

    return json.dumps({
        "total_memories": stats.total_memories,
        "by_source": dict(source_counts),
        "by_type": dict(type_counts),
        "has_ai_rules": type_counts.get("ai-rule", 0) > 0,
        "has_project_context": type_counts.get("ai-context", 0) > 0,
        "has_preferences": type_counts.get("ai-preference", 0) > 0,
    })
```

---

## F4: Memory Visualization (`viz.py`)

### CLI Command

```python
# In cli.py
p_viz = subparsers.add_parser("viz", help="Visualize memories in browser")
p_viz.add_argument("--output", "-o", default=None,
    help="Output HTML file path (default: temp file)")
p_viz.add_argument("--no-open", action="store_true",
    help="Don't open in browser")
```

### Class Design

```python
# viz.py

class MemoryVisualizer:
    """Generates self-contained HTML visualization of memory state."""

    def __init__(self, memory: StellarMemory):
        self._memory = memory

    def generate_html(self) -> str:
        """Generate complete HTML visualization page."""
        data = self._collect_data()
        return VIZ_TEMPLATE.replace("__DATA__", json.dumps(data))

    def save_and_open(self, output_path: str | None = None) -> str:
        """Save HTML to file and open in browser. Returns file path."""
        html = self.generate_html()
        if output_path is None:
            import tempfile
            fd, output_path = tempfile.mkstemp(suffix=".html", prefix="stellar-viz-")
            os.close(fd)
        Path(output_path).write_text(html, encoding="utf-8")
        import webbrowser
        webbrowser.open(f"file://{output_path}")
        return output_path

    def _collect_data(self) -> dict:
        """Collect all data needed for visualization."""
        stats = self._memory.stats()
        zones_data = []
        all_items = []
        for zone_id in range(5):
            items = self._get_zone_items(zone_id)
            zones_data.append({
                "id": zone_id,
                "name": self._memory.config.zones[zone_id].name,
                "count": stats.zone_counts.get(zone_id, 0),
                "capacity": stats.zone_capacities.get(zone_id),
                "items": [self._item_to_dict(i) for i in items],
            })
            all_items.extend(items)

        # Graph edges
        edges = []
        if hasattr(self._memory, '_graph') and self._memory._graph:
            for item in all_items:
                neighbors = self._memory._graph.get_edges(item.id)
                for edge in neighbors:
                    edges.append({
                        "source": edge.source_id[:8],
                        "target": edge.target_id[:8],
                        "type": edge.edge_type,
                    })

        return {
            "stats": {
                "total": stats.total_memories,
                "zones": {str(k): v for k, v in stats.zone_counts.items()},
            },
            "zones": zones_data,
            "edges": edges,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _item_to_dict(self, item: MemoryItem) -> dict:
        return {
            "id": item.id[:8],
            "content": item.content[:200],
            "zone": item.zone,
            "importance": round(item.arbitrary_importance, 2),
            "score": round(item.total_score, 3),
            "recall_count": item.recall_count,
            "created_at": time.strftime("%Y-%m-%d", time.localtime(item.created_at)),
            "category": (item.metadata or {}).get("category", ""),
            "type": (item.metadata or {}).get("type", "general"),
            "source": (item.metadata or {}).get("source", "manual"),
        }
```

### HTML Template Structure

```
VIZ_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Stellar Memory Visualization</title>
  <style>
    /* Dark theme: #0d1117 background */
    /* Tab navigation: Solar System | Memory List | Graph | Stats */
    /* Zone rings SVG with interactive dots */
    /* Responsive layout */
  </style>
</head>
<body>
  <nav> Tab buttons </nav>

  <!-- Tab 1: Solar System -->
  <div id="tab-solar">
    <svg id="solar-system"> <!-- Zone rings + memory dots --> </svg>
    <div id="memory-detail"> <!-- Click to show content --> </div>
  </div>

  <!-- Tab 2: Memory List -->
  <div id="tab-list">
    <input id="search" placeholder="Search memories...">
    <select id="filter-zone"> Zone filter </select>
    <select id="filter-type"> Type filter </select>
    <table id="memory-table"> <!-- Sortable columns --> </table>
  </div>

  <!-- Tab 3: Graph -->
  <div id="tab-graph">
    <svg id="graph-view"> <!-- Force-directed node-link diagram --> </svg>
  </div>

  <!-- Tab 4: Stats -->
  <div id="tab-stats">
    <div class="stat-cards"> <!-- Zone usage bars --> </div>
    <div class="score-histogram"> <!-- Score distribution --> </div>
    <div class="source-pie"> <!-- Import source breakdown --> </div>
  </div>

  <script>
    const DATA = __DATA__;
    // Tab switching
    // Solar system rendering (SVG)
    // Memory list with search/filter/sort
    // Force-directed graph (vanilla JS)
    // Stats charts (SVG bars)
  </script>
</body>
</html>"""
```

### Visualization Views Spec

**Solar System View**:
- 5 concentric ring circles (zones 0-4)
- Memory dots positioned on rings, size = importance, color = category
- Click dot → show content/metadata in side panel
- Zone labels with count/capacity

**Memory List View**:
- Searchable text input (filters in real-time)
- Filter by zone, category, type
- Sortable columns: content, zone, importance, score, recall count, date
- Click row → expand full content + metadata

**Graph View**:
- Force-directed layout using simple spring simulation
- Nodes = memories (color by zone)
- Edges = graph relationships (color by edge type)
- Hover node → show content preview
- Drag to rearrange

**Stats View**:
- Zone usage bar charts (filled / capacity)
- Import source pie chart (manual / auto-import / ai-config)
- Score distribution histogram
- Top 10 most-recalled memories

---

## Config Additions (`config.py`)

```python
@dataclass
class OnboardConfig:
    enabled: bool = True
    max_file_size: int = 102_400       # 100KB
    max_scan_depth: int = 3
    default_categories: list[str] = field(
        default_factory=lambda: ["ai-config", "documents", "notes"]
    )
    skip_patterns: list[str] = field(
        default_factory=lambda: [".git", "node_modules", "__pycache__",
                                 ".env", "venv", ".venv"]
    )
    sensitive_patterns: list[str] = field(
        default_factory=lambda: ["id_rsa", ".ssh", "credentials",
                                 "password", "secret", ".pem", ".key"]
    )

@dataclass
class KnowledgeBaseConfig:
    enabled: bool = True
    auto_detect_project: bool = True
    auto_import_ai_configs: bool = False  # requires explicit consent
    preference_importance: float = 0.95
    rule_importance: float = 0.9
    context_importance: float = 0.85

# Add to StellarConfig:
#     onboard: OnboardConfig = field(default_factory=OnboardConfig)
#     knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
```

---

## Implementation Order

```
1. F6: knowledge_base.py     (AIKnowledgeBase class + project detection)
2. F1: scanner.py            (LocalScanner class + category definitions)
3. F2: importer.py           (SmartImporter class + AI config parser)
4. F6+F5: mcp_server.py      (7 new MCP tools)
5. F3: cli.py                (onboard + sync-ai subcommands)
6. F4: viz.py                (MemoryVisualizer + HTML template)
7. F3: cli.py                (viz subcommand)
8. config.py + models.py     (new configs and data models)
```

Note: Step 8 (models/config) should be done first as other steps depend on it, but is listed last for logical grouping. Actual implementation starts with models/config.

## Actual Implementation Steps

```
Step 1: models.py       → Add ScanResult, ScanSummary, ImportResult, ChunkInfo
Step 2: config.py       → Add OnboardConfig, KnowledgeBaseConfig to StellarConfig
Step 3: knowledge_base.py → AIKnowledgeBase (detect_project, get_context, get_rules, learn_preference)
Step 4: scanner.py       → LocalScanner (scan, scan_ai_configs, category definitions)
Step 5: importer.py      → SmartImporter (import_scan_results, import_ai_config, chunking, dedup)
Step 6: cli.py           → Add onboard + viz + sync-ai subcommands
Step 7: mcp_server.py    → Add 7 new MCP tools
Step 8: viz.py           → MemoryVisualizer + full HTML template
```

## Dependencies

- Zero new mandatory dependencies
- All features use stdlib only: `pathlib`, `json`, `os`, `platform`, `webbrowser`, `tempfile`
- Existing `StellarMemory.store()` / `.recall()` / `.forget()` used for all storage

## Testing Strategy

| Test | Validates |
|------|-----------|
| `test_scanner_discovers_files` | F1: finds files in test directories |
| `test_scanner_skips_sensitive` | F1: never reads .env, SSH keys |
| `test_scanner_ai_configs` | F1: finds CLAUDE.md, .cursorrules |
| `test_importer_chunks` | F2: splits content at paragraph boundaries |
| `test_importer_dedup` | F2: skips duplicate content |
| `test_importer_ai_config_parse` | F2: parses markdown sections into rules |
| `test_knowledge_base_detect` | F6: detects Python/Node project type |
| `test_knowledge_base_context` | F6: generates project context memory |
| `test_knowledge_base_preferences` | F6: stores and retrieves preferences |
| `test_knowledge_base_rules` | F6: queries all rules by metadata type |
| `test_viz_generates_html` | F4: produces valid self-contained HTML |
| `test_mcp_get_context` | F5: MCP tool returns project context |
| `test_mcp_learn_preference` | F5: MCP tool stores preference |
| `test_mcp_get_rules` | F5: MCP tool returns rules list |
| `test_onboard_dry_run` | F3: scans without importing |
