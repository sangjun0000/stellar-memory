"""CLI tool for Stellar Memory management."""

from __future__ import annotations

import argparse
import json
import sys

from stellar_memory.config import StellarConfig
from stellar_memory.stellar import StellarMemory


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="stellar-memory",
        description="Stellar Memory - AI memory management CLI",
    )
    parser.add_argument("--db", default="stellar_memory.db", help="Database path")
    parser.add_argument("--namespace", "-n", default=None, help="Memory namespace")

    subparsers = parser.add_subparsers(dest="command")

    # store
    p_store = subparsers.add_parser("store", help="Store a new memory")
    p_store.add_argument("content", help="Memory content")
    p_store.add_argument("--importance", "-i", type=float, default=0.5)

    # recall
    p_recall = subparsers.add_parser("recall", help="Search memories")
    p_recall.add_argument("query", help="Search query")
    p_recall.add_argument("--limit", "-l", type=int, default=5)
    p_recall.add_argument("--confident", action="store_true",
                         help="Include confidence scoring (P9)")
    p_recall.add_argument("--threshold", type=float, default=None,
                         help="Minimum confidence threshold (with --confident)")

    # stats
    subparsers.add_parser("stats", help="Show memory statistics")

    # export
    p_export = subparsers.add_parser("export", help="Export memories to JSON")
    p_export.add_argument("--output", "-o", default="-", help="Output file (- for stdout)")
    p_export.add_argument("--embeddings", action="store_true")

    # import
    p_import = subparsers.add_parser("import", help="Import memories from JSON")
    p_import.add_argument("input", help="Input JSON file")

    # forget
    p_forget = subparsers.add_parser("forget", help="Delete a memory")
    p_forget.add_argument("id", help="Memory ID to delete")

    # reorbit
    subparsers.add_parser("reorbit", help="Trigger manual reorbit")

    # health
    subparsers.add_parser("health", help="System health check")

    # logs
    p_logs = subparsers.add_parser("logs", help="Show event logs")
    p_logs.add_argument("--limit", "-l", type=int, default=20)

    # summarize (P5)
    p_summarize = subparsers.add_parser("summarize", help="Summarize a memory")
    p_summarize.add_argument("id", help="Memory ID to summarize")

    # graph (P5)
    p_graph = subparsers.add_parser("graph", help="Graph analysis commands")
    graph_sub = p_graph.add_subparsers(dest="graph_command")
    graph_sub.add_parser("stats", help="Graph statistics")
    graph_sub.add_parser("communities", help="Detect communities")
    p_gcent = graph_sub.add_parser("centrality", help="Node centrality")
    p_gcent.add_argument("--top", "-k", type=int, default=10)
    p_gpath = graph_sub.add_parser("path", help="Find path between memories")
    p_gpath.add_argument("source", help="Source memory ID")
    p_gpath.add_argument("target", help="Target memory ID")
    p_gexport = graph_sub.add_parser("export", help="Export graph")
    p_gexport.add_argument("--format", "-f", choices=["dot", "graphml"], default="dot")
    p_gexport.add_argument("--output", "-o", default="-")

    # introspect (P9)
    p_introspect = subparsers.add_parser("introspect", help="Analyze knowledge state for a topic")
    p_introspect.add_argument("topic", help="Topic to introspect")
    p_introspect.add_argument("--depth", "-d", type=int, default=1)

    # optimize (P9)
    p_optimize = subparsers.add_parser("optimize", help="Optimize memory function weights")
    p_optimize.add_argument("--min-logs", type=int, default=None,
                            help="Minimum recall logs required")

    # rollback-weights (P9)
    subparsers.add_parser("rollback-weights", help="Rollback to previous weights")

    # benchmark (P9)
    p_bench = subparsers.add_parser("benchmark", help="Run memory system benchmark")
    p_bench.add_argument("--queries", "-q", type=int, default=100)
    p_bench.add_argument("--dataset", choices=["small", "standard", "large"],
                         default="standard")
    p_bench.add_argument("--seed", type=int, default=42)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start MCP server")
    p_serve.add_argument("--transport", default="stdio",
                         choices=["stdio", "streamable-http"])

    # serve-api
    p_serve_api = subparsers.add_parser("serve-api", help="Start REST API server")
    p_serve_api.add_argument("--host", default="0.0.0.0")
    p_serve_api.add_argument("--port", type=int, default=9000)
    p_serve_api.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # init-mcp (P8)
    p_init_mcp = subparsers.add_parser("init-mcp", help="Generate MCP configuration for AI IDEs")
    p_init_mcp.add_argument("--ide", choices=["claude", "cursor", "auto"], default="auto",
                            help="Target IDE (default: auto-detect)")
    p_init_mcp.add_argument("--db-path", default="~/.stellar/memory.db",
                            help="Database path for MCP server")
    p_init_mcp.add_argument("--dry-run", action="store_true",
                            help="Print config without writing")

    # quickstart (P8)
    subparsers.add_parser("quickstart", help="Interactive setup wizard")

    # setup (one-click)
    p_setup = subparsers.add_parser("setup", help="Auto-setup: install MCP for your AI IDE")
    p_setup.add_argument("--yes", "-y", action="store_true",
                         help="Skip confirmation prompts")

    # start
    subparsers.add_parser("start", help="Start MCP server (auto-detect transport)")

    # status
    subparsers.add_parser("status", help="Check system status")

    # onboard (v2.1.0)
    p_onboard = subparsers.add_parser("onboard",
        help="Smart onboarding - scan and import your data")
    p_onboard.add_argument("--categories", "-c", nargs="*", default=None,
        help="Categories: documents, notes, ai-config, chat-history, code, bookmarks")
    p_onboard.add_argument("--exclude", nargs="*", default=None,
        help="Paths to exclude from scanning")
    p_onboard.add_argument("--yes", "-y", action="store_true",
        help="Skip confirmation prompts")
    p_onboard.add_argument("--dry-run", action="store_true",
        help="Scan only, don't import")

    # viz (v2.1.0)
    p_viz = subparsers.add_parser("viz", help="Visualize memories in browser")
    p_viz.add_argument("--output", "-o", default=None,
        help="Output HTML file path (default: temp file)")
    p_viz.add_argument("--no-open", action="store_true",
        help="Don't open in browser")

    # sync-ai (v2.1.0)
    p_sync = subparsers.add_parser("sync-ai",
        help="Import AI config files into Stellar Memory")
    p_sync.add_argument("--tool", choices=["claude", "cursor", "copilot", "windsurf"],
        default=None, help="AI tool (default: auto-detect)")
    p_sync.add_argument("--path", default=None, help="Config file path (default: auto-detect)")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return

    config = StellarConfig(db_path=args.db)
    memory = StellarMemory(config, namespace=args.namespace)

    if args.command == "store":
        item = memory.store(args.content, importance=args.importance)
        print(json.dumps({"id": item.id, "zone": item.zone}))

    elif args.command == "recall":
        if args.confident:
            result = memory.recall_with_confidence(args.query, top_k=args.limit)
            if args.threshold is not None and result.confidence < args.threshold:
                print(f"Confidence {result.confidence:.3f} below threshold {args.threshold}")
                return
            print(f"Confidence: {result.confidence:.3f}")
            if result.warning:
                print(f"Warning: {result.warning}")
            for item in result.memories:
                print(f"[{item.id[:8]}] (zone {item.zone}, score {item.total_score:.3f}) {item.content[:100]}")
            return
        results = memory.recall(args.query, limit=args.limit)
        for item in results:
            print(f"[{item.id[:8]}] (zone {item.zone}, score {item.total_score:.3f}) {item.content[:100]}")

    elif args.command == "stats":
        stats = memory.stats()
        print(f"Total memories: {stats.total_memories}")
        for zone_id, count in sorted(stats.zone_counts.items()):
            cap = stats.zone_capacities.get(zone_id)
            cap_str = str(cap) if cap else "unlimited"
            print(f"  Zone {zone_id}: {count}/{cap_str}")

    elif args.command == "export":
        data = memory.export_json(include_embeddings=args.embeddings)
        if args.output == "-":
            print(data)
        else:
            with open(args.output, "w") as f:
                f.write(data)
            print(f"Exported to {args.output}")

    elif args.command == "import":
        with open(args.input) as f:
            data = f.read()
        count = memory.import_json(data)
        print(f"Imported {count} memories")

    elif args.command == "forget":
        removed = memory.forget(args.id)
        print("Removed" if removed else "Not found")

    elif args.command == "reorbit":
        result = memory.reorbit()
        print(f"Moved: {result.moved}, Evicted: {result.evicted}, "
              f"Total: {result.total_items}, Duration: {result.duration:.3f}s")

    elif args.command == "health":
        h = memory.health()
        status_str = "HEALTHY" if h.healthy else "UNHEALTHY"
        print(f"Status: {status_str}")
        print(f"DB: {'OK' if h.db_accessible else 'FAIL'}")
        print(f"Scheduler: {'running' if h.scheduler_running else 'stopped'}")
        print(f"Memories: {h.total_memories}")
        print(f"Graph edges: {h.graph_edges}")
        for zone_id, usage in sorted(h.zone_usage.items()):
            print(f"  Zone {zone_id}: {usage}")
        if h.warnings:
            print("Warnings:")
            for w in h.warnings:
                print(f"  - {w}")

    elif args.command == "logs":
        from stellar_memory.event_logger import EventLogger
        el = EventLogger(log_path="stellar_events.jsonl")
        entries = el.read_logs(limit=args.limit)
        for entry in entries:
            ts = entry.get("timestamp", 0)
            event = entry.get("event", "?")
            detail = {k: v for k, v in entry.items()
                      if k not in ("timestamp", "event")}
            print(f"[{ts:.0f}] {event}: {json.dumps(detail)}")

    elif args.command == "summarize":
        item = memory.get(args.id)
        if item is None:
            print("Memory not found")
            return
        if memory._summarizer is None:
            print("Summarization not available (LLM not configured)")
            return
        summary = memory._summarizer.summarize(item.content)
        if summary:
            print(f"Summary: {summary}")
        else:
            print("Could not generate summary")

    elif args.command == "graph":
        if memory._analyzer is None:
            print("Graph analytics not enabled")
            return
        if args.graph_command == "stats":
            s = memory._analyzer.stats()
            print(f"Nodes: {s.total_nodes}")
            print(f"Edges: {s.total_edges}")
            print(f"Avg degree: {s.avg_degree:.2f}")
            print(f"Density: {s.density:.4f}")
            print(f"Components: {s.connected_components}")
        elif args.graph_command == "communities":
            comms = memory._analyzer.communities()
            print(f"Communities found: {len(comms)}")
            for i, c in enumerate(comms):
                print(f"  #{i+1}: {len(c)} members - {', '.join(id[:8] for id in c[:5])}")
        elif args.graph_command == "centrality":
            results = memory._analyzer.centrality(args.top)
            for r in results:
                print(f"  [{r.item_id[:8]}] degree={r.degree} score={r.score:.3f}")
        elif args.graph_command == "path":
            p = memory._analyzer.path(args.source, args.target)
            if p is None:
                print("No path found")
            else:
                print(f"Path (length {len(p)-1}): {' -> '.join(id[:8] for id in p)}")
        elif args.graph_command == "export":
            if args.format == "dot":
                data = memory._analyzer.export_dot(memory_getter=memory.get)
            else:
                data = memory._analyzer.export_graphml()
            if args.output == "-":
                print(data)
            else:
                with open(args.output, "w") as f:
                    f.write(data)
                print(f"Exported to {args.output}")
        else:
            p_graph.print_help()

    elif args.command == "introspect":
        result = memory.introspect(args.topic, depth=args.depth)
        print(f"Topic: {result.topic}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Memory count: {result.memory_count}")
        print(f"Avg freshness: {result.avg_freshness:.3f}")
        if result.coverage:
            print(f"Coverage: {', '.join(result.coverage[:10])}")
        if result.gaps:
            print(f"Gaps: {', '.join(result.gaps[:10])}")
        if result.zone_distribution:
            print("Zone distribution:")
            for z, c in sorted(result.zone_distribution.items()):
                print(f"  Zone {z}: {c}")

    elif args.command == "optimize":
        try:
            report = memory.optimize(min_logs=args.min_logs)
            print(f"Pattern: {report.pattern}")
            print(f"Result: {report.improvement}")
            print(f"Rolled back: {report.rolled_back}")
            print(f"Before: {json.dumps(report.before_weights)}")
            print(f"After:  {json.dumps(report.after_weights)}")
        except ValueError as e:
            print(f"Error: {e}")

    elif args.command == "rollback-weights":
        weights = memory.rollback_weights()
        print(f"Rolled back to: {json.dumps(weights)}")

    elif args.command == "benchmark":
        report = memory.benchmark(
            queries=args.queries, dataset=args.dataset, seed=args.seed
        )
        print(f"Dataset: {report.dataset_name} ({report.queries_run} queries)")
        print(f"Recall@5:  {report.recall_at_5:.3f}")
        print(f"Recall@10: {report.recall_at_10:.3f}")
        print(f"Precision@5: {report.precision_at_5:.3f}")
        print(f"Avg store latency:  {report.avg_store_latency_ms:.2f}ms")
        print(f"Avg recall latency: {report.avg_recall_latency_ms:.2f}ms")
        print(f"Reorbit latency:    {report.avg_reorbit_latency_ms:.2f}ms")
        print(f"Total memories: {report.total_memories}")
        print(f"DB size: {report.db_size_mb:.2f}MB")

    elif args.command == "serve":
        try:
            from stellar_memory.mcp_server import run_server
        except ImportError:
            print("Error: MCP module not installed.")
            print("Run:  pip install stellar-memory[mcp]")
            sys.exit(1)
        run_server(config, namespace=args.namespace, transport=args.transport)

    elif args.command == "serve-api":
        from stellar_memory.server import create_api_app
        import uvicorn
        app, _ = create_api_app(config, namespace=args.namespace)
        uvicorn.run(app, host=args.host, port=args.port,
                    reload=args.reload, log_level="info")

    elif args.command == "init-mcp":
        _run_init_mcp(args)

    elif args.command == "quickstart":
        _run_quickstart(args)

    elif args.command == "setup":
        _run_setup(args)

    elif args.command == "start":
        from stellar_memory.mcp_server import run_server
        run_server(config, namespace=args.namespace, transport="stdio")

    elif args.command == "status":
        h = memory.health()
        status_str = "OK" if h.healthy else "PROBLEM"
        print(f"Stellar Memory: {status_str}")
        print(f"Memories stored: {h.total_memories}")
        if not h.healthy:
            for w in h.warnings:
                print(f"  Warning: {w}")

    elif args.command == "onboard":
        _run_onboard(args, config)

    elif args.command == "viz":
        _run_viz(args, config)

    elif args.command == "sync-ai":
        _run_sync_ai(args, config)


def _run_onboard(args, config) -> None:
    """Interactive onboarding wizard."""
    from stellar_memory.scanner import LocalScanner, CATEGORIES
    from stellar_memory.importer import SmartImporter

    print("=" * 50)
    print("  Stellar Memory - Smart Onboarding")
    print("=" * 50)
    print()
    print("This wizard scans your computer for useful data")
    print("and imports it into Stellar Memory.")
    print("Nothing is accessed without your permission.")
    print()

    # Category selection
    all_cats = list(CATEGORIES.keys())
    categories = args.categories
    if categories is None and not args.yes:
        print("Select categories to scan:")
        for i, cat in enumerate(all_cats, 1):
            default = "*" if cat == "ai-config" else " "
            print(f"  [{default}] {i}. {cat}")
        print()
        try:
            selection = input("Enter numbers (e.g., 1,2,3) or 'all' [default: all]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not selection or selection.lower() == "all":
            categories = all_cats
        else:
            indices = [int(x.strip()) - 1 for x in selection.split(",")
                       if x.strip().isdigit()]
            categories = [all_cats[i] for i in indices if 0 <= i < len(all_cats)]
    elif categories is None:
        categories = all_cats

    # Scan
    scanner = LocalScanner(exclude_paths=args.exclude)
    print("\nScanning...")
    summary = scanner.scan(categories=categories)
    print(f"\nFound {summary.total_found} items:")
    for cat, count in summary.by_category.items():
        if count > 0:
            print(f"  {cat}: {count} files")

    if summary.total_found == 0:
        print("\nNo importable files found.")
        return

    # Preview
    if not args.yes:
        print("\nPreview (top 5 per category):")
        shown: dict[str, int] = {}
        for result in summary.results:
            cat = result.category
            shown[cat] = shown.get(cat, 0) + 1
            if shown[cat] > 5:
                continue
            label = f"[{cat}]"
            if result.ai_tool:
                label = f"[{cat}/{result.ai_tool}]"
            print(f"  {label} {result.path}")
            if result.preview:
                print(f"    {result.preview[:80]}...")
        print()

    # Confirm
    if args.dry_run:
        print("Dry run - no import performed.")
        return
    if not args.yes:
        try:
            answer = input("Import these items? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if answer and answer != "y":
            print("Cancelled.")
            return

    # Import
    memory = StellarMemory(config)
    memory.start()
    importer = SmartImporter(memory)
    result = importer.import_scan_results(
        summary.results,
        progress_callback=lambda done, total: print(
            f"\r  Importing... {done}/{total}", end="", flush=True),
    )
    print()

    # Summary
    print(f"\nImport complete!")
    print(f"  Imported: {result.imported}")
    print(f"  Skipped (duplicate): {result.skipped_duplicate}")
    if result.skipped_error:
        print(f"  Errors: {result.skipped_error}")
    stats = memory.stats()
    print(f"\nZone distribution:")
    for z, count in sorted(stats.zone_counts.items()):
        if count > 0:
            print(f"  Zone {z}: {count} memories")
    print(f"\nTotal: {stats.total_memories} memories")
    print("\nTry: stellar-memory viz")
    memory.stop()


def _run_viz(args, config) -> None:
    """Generate and open memory visualization."""
    from stellar_memory.viz import MemoryVisualizer

    memory = StellarMemory(config)
    viz = MemoryVisualizer(memory)

    output = args.output
    open_browser = not args.no_open

    path = viz.save_and_open(output_path=output, open_browser=open_browser)
    print(f"Visualization saved to: {path}")
    if open_browser:
        print("Opening in browser...")


def _run_sync_ai(args, config) -> None:
    """Import AI config files into Stellar Memory."""
    from pathlib import Path
    from stellar_memory.knowledge_base import AIKnowledgeBase
    from stellar_memory.scanner import AI_CONFIG_FILES, AI_CONFIG_SUBPATHS

    memory = StellarMemory(config)
    memory.start()
    kb = AIKnowledgeBase(memory)

    tool = args.tool
    config_path = args.path

    if config_path:
        # Explicit path provided
        if not tool:
            tool = "unknown"
        if not Path(config_path).exists():
            print(f"File not found: {config_path}")
            memory.stop()
            return
        count = kb.sync_ai_config(tool, config_path)
        print(f"Imported {count} rules from {config_path} ({tool})")
    else:
        # Auto-detect
        total = 0
        search_dirs = [Path.cwd(), Path.home()]
        for d in search_dirs:
            for filename, t in {**AI_CONFIG_FILES, **AI_CONFIG_SUBPATHS}.items():
                if tool and t != tool:
                    continue
                path = d / filename
                if path.exists():
                    count = kb.sync_ai_config(t, str(path))
                    if count > 0:
                        print(f"  {t}: {count} rules from {path}")
                    total += count
        if total == 0:
            print("No AI config files found.")
        else:
            print(f"\nTotal: {total} rules imported")

    memory.stop()


def _claude_config_path() -> str:
    """Get Claude Desktop config path by platform."""
    import platform
    from pathlib import Path
    system = platform.system()
    if system == "Windows":
        return str(Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json")
    elif system == "Darwin":
        return str(Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json")
    else:
        return str(Path.home() / ".config" / "claude" / "claude_desktop_config.json")


def _cursor_config_path() -> str:
    from pathlib import Path
    return str(Path.home() / ".cursor" / "mcp.json")


def _get_mcp_config_path(ide: str) -> str:
    if ide == "claude":
        return _claude_config_path()
    elif ide == "cursor":
        return _cursor_config_path()
    raise ValueError(f"Unknown IDE: {ide}")


def _merge_mcp_config(path: str, new_config: dict) -> None:
    """Merge new MCP config into existing config file."""
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if p.exists():
        with open(p) as f:
            existing = json.load(f)
    servers = existing.get("mcpServers", {})
    servers.update(new_config["mcpServers"])
    existing["mcpServers"] = servers
    with open(p, "w") as f:
        json.dump(existing, f, indent=2)


def _run_init_mcp(args) -> None:
    """Generate MCP configuration for AI IDEs."""
    from pathlib import Path

    ide = args.ide
    if ide == "auto":
        if Path(_claude_config_path()).parent.exists():
            ide = "claude"
        else:
            ide = "claude"

    db_path = str(Path(args.db_path).expanduser())
    config_content = {
        "mcpServers": {
            "stellar-memory": {
                "command": "stellar-memory",
                "args": ["serve", "--mcp"],
                "env": {
                    "STELLAR_DB_PATH": db_path,
                },
            }
        }
    }

    if args.dry_run:
        print(json.dumps(config_content, indent=2))
        return

    config_path = _get_mcp_config_path(ide)
    _merge_mcp_config(config_path, config_content)
    print(f"MCP configuration written to: {config_path}")
    print(f"Database path: {db_path}")
    print(f"\nRestart {ide.title()} to activate Stellar Memory tools.")


def _run_quickstart(args) -> None:
    """Interactive quickstart wizard — simplified for non-developers."""
    print("=" * 50)
    print("  Stellar Memory")
    print("  Give your AI the ability to remember")
    print("=" * 50)
    print()
    print("Choose how to use Stellar Memory:")
    print()
    print("  1. With AI IDE (Claude Desktop / Cursor)")
    print("     → Your AI will automatically remember things")
    print()
    print("  2. As a Python library (for developers)")
    print("     → Use in your own code")
    print()

    try:
        choice = input("Select [1-2, default=1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice == "1":
        class SetupArgs:
            yes = False
            db = args.db
        _run_setup(SetupArgs())
    else:
        db_path = args.db
        from stellar_memory import StellarMemory, StellarConfig
        config = StellarConfig(db_path=db_path)
        mem = StellarMemory(config)
        item = mem.store("Hello, Stellar Memory! This is my first memory.", importance=0.9)

        print(f"\nYour first memory is stored!")
        print(f"  ID:   {item.id[:8]}...")
        print(f"  Zone: {item.zone}")
        print()
        print("Try recalling:")
        print(f'  stellar-memory recall "hello" --db {db_path}')
        mem.stop()


def _run_setup(args) -> None:
    """One-click setup: detect IDE and configure MCP."""
    from pathlib import Path

    print("Stellar Memory - Auto Setup")
    print("=" * 40)
    print()

    # Detect available IDEs
    claude_path = Path(_claude_config_path())
    cursor_path = Path(_cursor_config_path())

    claude_exists = claude_path.parent.exists()
    cursor_exists = cursor_path.parent.exists()

    if not claude_exists and not cursor_exists:
        print("No AI IDE detected (Claude Desktop or Cursor).")
        print()
        print("Install one of these:")
        print("  - Claude Desktop: https://claude.ai/download")
        print("  - Cursor: https://cursor.sh")
        print()
        print("After installing, run this command again.")
        return

    targets = []
    if claude_exists:
        targets.append(("Claude Desktop", "claude"))
    if cursor_exists:
        targets.append(("Cursor", "cursor"))

    print(f"Detected: {', '.join(name for name, _ in targets)}")

    if not args.yes:
        try:
            confirm = input(f"\nSet up MCP for {', '.join(name for name, _ in targets)}? [Y/n]: ").strip().lower()
            if confirm == 'n':
                print("Setup cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            return

    db_path = str(Path("~/.stellar/memory.db").expanduser())
    config_content = {
        "mcpServers": {
            "stellar-memory": {
                "command": "stellar-memory",
                "args": ["serve", "--transport", "stdio"],
                "env": {
                    "STELLAR_DB_PATH": db_path,
                },
            }
        }
    }

    for name, ide in targets:
        config_path = _get_mcp_config_path(ide)
        _merge_mcp_config(config_path, config_content)
        print(f"  {name}: configured")

    print()
    print("Setup complete!")
    print(f"Database: {db_path}")
    print()
    print("Restart your AI IDE to activate Stellar Memory.")
    print('Try saying: "Remember my name is ___"')


if __name__ == "__main__":
    main()
