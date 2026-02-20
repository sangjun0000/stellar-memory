"""MCP Server for Stellar Memory - enables AI tools to use memory as tools."""

from __future__ import annotations

import json
import logging

from stellar_memory.config import StellarConfig
from stellar_memory.stellar import StellarMemory

logger = logging.getLogger(__name__)


def create_mcp_server(config: StellarConfig | None = None,
                      namespace: str | None = None):
    """Create and configure the MCP server with all memory tools."""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("stellar-memory")
    memory = StellarMemory(config or StellarConfig(), namespace=namespace)

    @mcp.tool()
    def memory_store(content: str, importance: float = 0.5,
                     metadata_json: str = "{}") -> str:
        """Store a new memory. Returns the memory ID.

        Args:
            content: The content to remember
            importance: Importance score from 0.0 to 1.0
            metadata_json: Optional JSON string of metadata
        """
        metadata = json.loads(metadata_json) if metadata_json else {}
        item = memory.store(content, importance=importance,
                           metadata=metadata, auto_evaluate=True)
        return json.dumps({
            "id": item.id,
            "zone": item.zone,
            "total_score": item.total_score,
        })

    @mcp.tool()
    def memory_recall(query: str, limit: int = 5) -> str:
        """Search memories by query. Returns matching memories.

        Args:
            query: Search query text
            limit: Maximum number of results (1-20)
        """
        limit = max(1, min(20, limit))
        results = memory.recall(query, limit=limit)
        return json.dumps([{
            "id": item.id,
            "content": item.content,
            "zone": item.zone,
            "importance": item.arbitrary_importance,
            "recall_count": item.recall_count,
        } for item in results])

    @mcp.tool()
    def memory_get(memory_id: str) -> str:
        """Get a specific memory by ID.

        Args:
            memory_id: The UUID of the memory to retrieve
        """
        item = memory.get(memory_id)
        if item is None:
            return json.dumps({"error": "Memory not found"})
        return json.dumps({
            "id": item.id,
            "content": item.content,
            "zone": item.zone,
            "importance": item.arbitrary_importance,
            "recall_count": item.recall_count,
            "created_at": item.created_at,
            "metadata": item.metadata,
        })

    @mcp.tool()
    def memory_forget(memory_id: str) -> str:
        """Delete a specific memory by ID.

        Args:
            memory_id: The UUID of the memory to delete
        """
        removed = memory.forget(memory_id)
        return json.dumps({"removed": removed})

    @mcp.tool()
    def memory_stats() -> str:
        """Get memory statistics including zone counts and capacities."""
        stats = memory.stats()
        return json.dumps({
            "total_memories": stats.total_memories,
            "zone_counts": {str(k): v for k, v in stats.zone_counts.items()},
            "zone_capacities": {
                str(k): v for k, v in stats.zone_capacities.items()
            },
        })

    @mcp.tool()
    def memory_export(include_embeddings: bool = False) -> str:
        """Export all memories as JSON.

        Args:
            include_embeddings: Whether to include embedding vectors
        """
        return memory.export_json(include_embeddings=include_embeddings)

    @mcp.tool()
    def memory_import(json_data: str) -> str:
        """Import memories from JSON data.

        Args:
            json_data: JSON string containing memories to import
        """
        count = memory.import_json(json_data)
        return json.dumps({"imported": count})

    @mcp.tool()
    def session_start() -> str:
        """Start a new memory session for context grouping."""
        session = memory.start_session()
        return json.dumps({
            "session_id": session.session_id,
            "started_at": session.started_at,
        })

    @mcp.tool()
    def session_end() -> str:
        """End the current session and optionally create a summary."""
        session = memory.end_session()
        if session is None:
            return json.dumps({"error": "No active session"})
        return json.dumps({
            "session_id": session.session_id,
            "ended_at": session.ended_at,
            "memory_count": session.memory_count,
            "summary": session.summary,
        })

    @mcp.tool()
    def memory_health() -> str:
        """Run health diagnostics on the memory system."""
        h = memory.health()
        return json.dumps({
            "healthy": h.healthy,
            "db_accessible": h.db_accessible,
            "scheduler_running": h.scheduler_running,
            "total_memories": h.total_memories,
            "graph_edges": h.graph_edges,
            "zone_usage": {str(k): v for k, v in h.zone_usage.items()},
            "warnings": h.warnings,
        })

    @mcp.tool()
    def memory_summarize(memory_id: str) -> str:
        """Manually summarize an existing memory.

        Args:
            memory_id: The UUID of the memory to summarize
        """
        item = memory.get(memory_id)
        if item is None:
            return json.dumps({"error": "Memory not found"})
        if memory._summarizer is None:
            return json.dumps({"error": "Summarization not configured"})
        summary = memory._summarizer.summarize(item.content)
        if summary is None:
            return json.dumps({"error": "Summarization failed"})
        summary_item = memory.store(
            content=f"[Summary] {summary}",
            importance=min(1.0, item.arbitrary_importance + 0.1),
            metadata={"type": "summary", "source_id": item.id},
            skip_summarize=True,
        )
        if memory.config.graph.enabled:
            memory._graph.add_edge(summary_item.id, item.id, "derived_from")
        return json.dumps({
            "summary_id": summary_item.id,
            "summary": summary,
            "original_id": item.id,
        })

    @mcp.tool()
    def memory_graph_analyze(action: str, source_id: str = "",
                             target_id: str = "", top_k: int = 10) -> str:
        """Analyze the memory graph structure.

        Args:
            action: One of "stats", "communities", "centrality", "path"
            source_id: Required for "path" action - start node
            target_id: Required for "path" action - end node
            top_k: For "centrality" - number of top nodes to return
        """
        if memory._analyzer is None:
            return json.dumps({"error": "Graph analytics not enabled"})

        if action == "stats":
            s = memory._analyzer.stats()
            return json.dumps({
                "total_nodes": s.total_nodes,
                "total_edges": s.total_edges,
                "avg_degree": round(s.avg_degree, 2),
                "density": round(s.density, 4),
                "connected_components": s.connected_components,
            })
        elif action == "communities":
            comms = memory._analyzer.communities()
            return json.dumps({
                "count": len(comms),
                "communities": [{"size": len(c), "members": c[:5]} for c in comms],
            })
        elif action == "centrality":
            results = memory._analyzer.centrality(top_k)
            return json.dumps([{
                "id": r.item_id[:8],
                "degree": r.degree,
                "score": round(r.score, 3),
            } for r in results])
        elif action == "path":
            if not source_id or not target_id:
                return json.dumps({"error": "source_id and target_id required"})
            p = memory._analyzer.path(source_id, target_id)
            if p is None:
                return json.dumps({"path": None, "message": "No path found"})
            return json.dumps({"path": p, "length": len(p) - 1})
        else:
            return json.dumps({"error": f"Unknown action: {action}"})

    # --- P9 Tools ---

    @mcp.tool()
    def memory_introspect(topic: str, depth: int = 1) -> str:
        """Analyze knowledge state for a given topic.

        Args:
            topic: The topic to introspect about
            depth: Graph traversal depth for gap detection (1-3)
        """
        depth = max(1, min(3, depth))
        result = memory.introspect(topic, depth=depth)
        return json.dumps({
            "topic": result.topic,
            "confidence": result.confidence,
            "coverage": result.coverage,
            "gaps": result.gaps,
            "memory_count": result.memory_count,
            "avg_freshness": round(result.avg_freshness, 3),
            "zone_distribution": {str(k): v for k, v in result.zone_distribution.items()},
        })

    @mcp.tool()
    def memory_recall_confident(query: str, limit: int = 5,
                                threshold: float = 0.0) -> str:
        """Search memories with confidence scoring.

        Args:
            query: Search query text
            limit: Maximum number of results (1-20)
            threshold: Minimum confidence score (0.0-1.0)
        """
        limit = max(1, min(20, limit))
        result = memory.recall_with_confidence(query, top_k=limit)
        if threshold > 0 and result.confidence < threshold:
            return json.dumps({
                "confidence": result.confidence,
                "below_threshold": True,
                "memories": [],
                "warning": f"Confidence {result.confidence:.3f} below threshold {threshold}",
            })
        return json.dumps({
            "confidence": result.confidence,
            "below_threshold": False,
            "warning": result.warning,
            "memories": [{
                "id": item.id,
                "content": item.content,
                "zone": item.zone,
                "importance": item.arbitrary_importance,
            } for item in result.memories],
        })

    @mcp.tool()
    def memory_optimize(min_logs: int = 0) -> str:
        """Optimize memory function weights from recall patterns.

        Args:
            min_logs: Minimum number of recall logs required (0 = use default)
        """
        try:
            report = memory.optimize(min_logs=min_logs if min_logs > 0 else None)
            return json.dumps({
                "before_weights": report.before_weights,
                "after_weights": report.after_weights,
                "improvement": report.improvement,
                "pattern": report.pattern,
                "simulation_score": report.simulation_score,
                "rolled_back": report.rolled_back,
            })
        except ValueError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def memory_reason(query: str, max_sources: int = 5) -> str:
        """Derive insights by reasoning over related memories.

        Args:
            query: The question or topic to reason about
            max_sources: Maximum number of source memories to use
        """
        max_sources = max(1, min(20, max_sources))
        result = memory.reason(query, max_sources=max_sources)
        return json.dumps({
            "query": result.query,
            "insights": result.insights,
            "confidence": result.confidence,
            "reasoning_chain": result.reasoning_chain,
            "source_count": len(result.source_memories),
            "contradictions": result.contradictions,
        })

    @mcp.tool()
    def memory_benchmark(queries: int = 100, dataset: str = "standard",
                         seed: int = 42) -> str:
        """Run comprehensive memory system benchmark.

        Args:
            queries: Number of queries to run
            dataset: Dataset size - "small", "standard", or "large"
            seed: Random seed for reproducibility
        """
        if dataset not in ("small", "standard", "large"):
            dataset = "standard"
        report = memory.benchmark(queries=queries, dataset=dataset, seed=seed)
        return json.dumps(report.to_dict())

    # --- Smart Onboarding Tools (v2.1.0) ---

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
        Returns rules sorted by importance. Use this to understand
        the user's coding conventions across all AI tools.
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
        Once stored, any AI tool using Stellar Memory will know this preference.

        Args:
            key: Preference key (e.g., "naming_style", "language", "framework")
            value: Preference value (e.g., "snake_case", "Korean", "FastAPI")
        """
        from stellar_memory.knowledge_base import AIKnowledgeBase
        kb = AIKnowledgeBase(memory)
        mid = kb.learn_preference(key, value)
        return json.dumps({
            "stored": True, "memory_id": mid,
            "key": key, "value": value,
        })

    @mcp.tool()
    def memory_sync_ai_config(tool: str, config_path: str) -> str:
        """Import an AI configuration file into Stellar Memory.
        This makes rules from one AI tool available to all others.

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
        """Get a formatted summary of all memory zones and top memories per zone."""
        stats = memory.stats()
        zones_info = []
        for zone_id in sorted(stats.zone_counts.keys()):
            count = stats.zone_counts[zone_id]
            cap = stats.zone_capacities.get(zone_id)
            usage = f"{count}/{cap}" if cap else f"{count}/unlimited"
            zones_info.append({
                "zone": zone_id,
                "count": count,
                "capacity": cap,
                "usage": usage,
            })
        return json.dumps({
            "total_memories": stats.total_memories,
            "zones": zones_info,
        })

    @mcp.tool()
    def memory_topics(limit: int = 10) -> str:
        """Cluster memories by keyword and return topic list with counts.

        Args:
            limit: Maximum number of topics to return (1-50)
        """
        from collections import Counter
        limit = max(1, min(50, limit))
        results = memory.recall("", limit=200)
        word_counts: Counter = Counter()
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on",
                      "at", "to", "for", "of", "and", "or", "not", "this", "that",
                      "with", "from", "by", "as", "it", "be", "has", "had", "have"}
        for item in results:
            words = set(item.content.lower().split())
            words = {w for w in words if len(w) > 2 and w not in stopwords}
            word_counts.update(words)
        topics = [{"topic": word, "count": count}
                  for word, count in word_counts.most_common(limit)]
        return json.dumps({"topics": topics, "total_memories": len(results)})

    @mcp.tool()
    def memory_onboard_status() -> str:
        """Check onboarding status - what has been imported and what's available."""
        from collections import Counter
        stats = memory.stats()
        results = memory.recall("", limit=500)
        source_counts: Counter = Counter()
        type_counts: Counter = Counter()
        for item in results:
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

    @mcp.resource("memory://stats")
    def resource_stats() -> str:
        """Real-time memory statistics."""
        stats = memory.stats()
        return json.dumps({
            "total_memories": stats.total_memories,
            "zone_counts": {str(k): v for k, v in stats.zone_counts.items()},
        })

    @mcp.resource("memory://zones")
    def resource_zones() -> str:
        """Zone configuration information."""
        zones = []
        for z in memory.config.zones:
            zones.append({
                "zone_id": z.zone_id,
                "name": z.name,
                "max_slots": z.max_slots,
                "importance_range": [z.importance_min, z.importance_max],
            })
        return json.dumps(zones)

    return mcp, memory


def run_server(config: StellarConfig | None = None,
               namespace: str | None = None,
               transport: str = "stdio") -> None:
    """Run the MCP server."""
    mcp, memory = create_mcp_server(config, namespace)
    memory.start()
    try:
        mcp.run(transport=transport)
    finally:
        memory.stop()


if __name__ == "__main__":
    run_server()
