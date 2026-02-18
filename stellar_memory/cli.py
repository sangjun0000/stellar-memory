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
        from stellar_memory.mcp_server import run_server
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
    """Interactive quickstart wizard."""
    print("=" * 50)
    print("  Welcome to Stellar Memory!")
    print("  Celestial-structure AI memory system")
    print("=" * 50)
    print()
    print("How will you use Stellar Memory?")
    print("  1. Python library (import in your code)")
    print("  2. REST API server (HTTP endpoints)")
    print("  3. MCP server (Claude Code / Cursor)")
    print("  4. Docker container")

    try:
        choice = input("\nSelect [1-4, default=1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    db_path = args.db

    try:
        enable_emotion = input("Enable emotion analysis? [y/N]: ").strip().lower() == "y"
    except (EOFError, KeyboardInterrupt):
        enable_emotion = False

    from stellar_memory import StellarMemory, StellarConfig, EmotionConfig
    config = StellarConfig(
        db_path=db_path,
        emotion=EmotionConfig(enabled=enable_emotion),
    )
    mem = StellarMemory(config)
    item = mem.store("Hello, Stellar Memory! This is my first memory.", importance=0.9)

    print(f"\nYour first memory is stored!")
    print(f"  ID:   {item.id[:8]}...")
    print(f"  Zone: {item.zone} ({'Core' if item.zone == 0 else 'Inner' if item.zone == 1 else 'Outer'})")
    if item.emotion:
        print(f"  Emotion: {item.emotion.dominant} ({item.emotion.intensity:.2f})")

    if choice == "2":
        print(f"\nStart REST API server:")
        print(f"  stellar-memory serve-api --db {db_path}")
        print(f"  Open http://localhost:9000/docs for Swagger UI")
    elif choice == "3":
        print(f"\nSetup MCP for Claude Code:")
        print(f"  stellar-memory init-mcp --db-path {db_path}")
    elif choice == "4":
        print(f"\nRun with Docker:")
        print(f"  docker-compose up stellar")
    else:
        print(f"\nTry recalling your memory:")
        print(f'  stellar-memory recall "hello" --db {db_path}')

    mem.stop()


if __name__ == "__main__":
    main()
