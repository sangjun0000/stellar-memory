"""StellarMemory - main interface for the Stellar Memory system."""

from __future__ import annotations

import time

from stellar_memory._plugin_manager import PluginManager
from stellar_memory.config import StellarConfig
from stellar_memory.consolidator import MemoryConsolidator
from stellar_memory.decay_manager import DecayManager
from stellar_memory.embedder import create_embedder
from stellar_memory.event_bus import EventBus
from stellar_memory.importance_evaluator import create_evaluator
from stellar_memory.memory_function import MemoryFunction
from stellar_memory.memory_graph import MemoryGraph
from stellar_memory.models import (
    MemoryItem, MemoryStats, MemorySnapshot, ReorbitResult, FeedbackRecord,
    SessionInfo, DecayResult, HealthStatus, IngestResult,
    EmotionVector, TimelineEntry,
    IntrospectionResult, ConfidentRecall, OptimizationReport,
    ReasoningResult, Contradiction, BenchmarkReport,
)
from stellar_memory.namespace import NamespaceManager
from stellar_memory.orbit_manager import OrbitManager
from stellar_memory.plugin import MemoryPlugin
from stellar_memory.scheduler import ReorbitScheduler
from stellar_memory.serializer import MemorySerializer
from stellar_memory.session import SessionManager
from stellar_memory.storage import StorageFactory
from stellar_memory.utils import cosine_similarity
from stellar_memory.vector_index import create_vector_index
from stellar_memory.weight_tuner import create_tuner


class StellarMemory:
    def __init__(self, config: StellarConfig | None = None,
                 namespace: str | None = None):
        self.config = config or StellarConfig()

        # Namespace: override db_path if namespace is specified
        self._namespace = namespace
        if namespace and self.config.namespace.enabled:
            ns_mgr = NamespaceManager(self.config.namespace.base_path)
            self.config.db_path = ns_mgr.get_db_path(namespace)

        self._memory_fn = MemoryFunction(self.config.memory_function, self.config.zones)
        self._embedder = create_embedder(self.config.embedder)
        self._evaluator = create_evaluator(self.config.llm)
        self._tuner = create_tuner(self.config.tuner, self.config.memory_function)
        self._consolidator = MemoryConsolidator(self.config.consolidation, self._embedder)
        self._session_mgr = SessionManager(self.config.session)
        self._decay_mgr = DecayManager(
            self.config.decay,
            emotion_config=self.config.emotion if self.config.emotion.enabled else None,
        )
        factory = StorageFactory(self.config.db_path)
        self._orbit_mgr = OrbitManager(self.config.zones, factory)
        self._scheduler = ReorbitScheduler(
            self._orbit_mgr, self._memory_fn, self.config.reorbit_interval
        )
        self._event_bus = EventBus()
        self._plugin_mgr = PluginManager()

        # Graph: persistent or in-memory
        if (self.config.graph.persistent
                and self.config.db_path != ":memory:"):
            from stellar_memory.persistent_graph import PersistentMemoryGraph
            self._graph = PersistentMemoryGraph(
                self.config.db_path, self.config.graph.max_edges_per_item
            )
        else:
            self._graph = MemoryGraph(self.config.graph.max_edges_per_item)

        # Event logger
        self._event_logger = None
        if self.config.event_logger.enabled:
            from stellar_memory.event_logger import EventLogger
            self._event_logger = EventLogger(
                self.config.event_logger.log_path,
                self.config.event_logger.max_size_mb,
            )
            self._event_logger.attach(self._event_bus)

        # P5: Vector Index
        self._vector_index = create_vector_index(
            self.config.vector_index, self.config.embedder.dimension
        )

        # P5: Summarizer
        self._summarizer = None
        if self.config.summarization.enabled:
            try:
                from stellar_memory.summarizer import MemorySummarizer
                self._summarizer = MemorySummarizer(
                    self.config.summarization, self.config.llm
                )
            except Exception:
                pass

        # P5: Graph Analyzer
        self._analyzer = None
        if self.config.graph_analytics.enabled and self.config.graph.enabled:
            from stellar_memory.graph_analyzer import GraphAnalyzer
            self._analyzer = GraphAnalyzer(self._graph, self.config.graph_analytics)

        self._last_recall_ids: list[str] = []

        # P7: Emotion Analyzer
        self._emotion_analyzer = None
        if self.config.emotion.enabled:
            from stellar_memory.emotion import EmotionAnalyzer
            self._emotion_analyzer = EmotionAnalyzer(
                self.config.emotion, self.config.llm
            )
            if self.config.memory_function.w_emotion == 0.0:
                self.config.memory_function.w_emotion = 0.15
                self.config.memory_function.w_recall = 0.25
                self.config.memory_function.w_freshness = 0.25
                self.config.memory_function.w_arbitrary = 0.20
                self.config.memory_function.w_context = 0.15

        # P7: Memory Stream (lazy init)
        self._stream = None

        # P9: Metacognition
        self._introspector = None
        self._confidence_scorer = None
        if self.config.metacognition.enabled:
            from stellar_memory.metacognition import Introspector, ConfidenceScorer
            self._introspector = Introspector(self.config.metacognition)
            self._confidence_scorer = ConfidenceScorer(self.config.metacognition)

        # P9: Self-Learning
        self._pattern_collector = None
        self._weight_optimizer = None
        if self.config.self_learning.enabled:
            from stellar_memory.self_learning import PatternCollector, WeightOptimizer
            sl_db = self.config.db_path.replace(".db", "_learning.db")
            if self.config.db_path == ":memory:":
                sl_db = ":memory:"
            self._pattern_collector = PatternCollector(sl_db)
            self._weight_optimizer = WeightOptimizer(
                self.config.memory_function, self.config.self_learning, sl_db
            )

        # P9: Reasoning
        self._reasoner = None
        if self.config.reasoning.enabled:
            from stellar_memory.reasoning import MemoryReasoner
            llm = None
            if self.config.reasoning.use_llm:
                try:
                    from stellar_memory.llm_adapter import create_llm_adapter
                    llm = create_llm_adapter(self.config.llm)
                except Exception:
                    pass
            self._reasoner = MemoryReasoner(self.config.reasoning, llm)

        # P6: Security
        self._encryption = None
        self._access_control = None
        self._audit = None
        if self.config.security.enabled:
            from stellar_memory.security.encryption import EncryptionManager
            from stellar_memory.security.access_control import AccessControl
            from stellar_memory.security.audit import SecurityAudit
            self._encryption = EncryptionManager(
                key_env=self.config.security.encryption_key_env
            )
            self._access_control = AccessControl(self.config.security)
            if self.config.security.audit_enabled:
                self._audit = SecurityAudit()
                self._audit.attach(self._event_bus)

        # P6: Sync
        self._sync = None
        if self.config.sync.enabled and self.config.sync.agent_id:
            from stellar_memory.sync import MemorySyncManager
            self._sync = MemorySyncManager(self.config.sync.agent_id)
            if self.config.sync.auto_start_server:
                self._sync.start_server(
                    self.config.sync.ws_host, self.config.sync.ws_port
                )
            if self.config.sync.remote_url:
                self._sync.connect_remote(self.config.sync.remote_url)

        # P6: Redis cache
        self._redis_cache = None
        if self.config.storage.redis_url:
            try:
                from stellar_memory.storage.redis_cache import RedisCache
                self._redis_cache = RedisCache(
                    self.config.storage.redis_url,
                    self.config.storage.redis_ttl,
                    self.config.storage.redis_cached_zones,
                )
                self._redis_cache.connect()
            except Exception:
                pass

    @property
    def events(self) -> EventBus:
        return self._event_bus

    def use(self, plugin: MemoryPlugin) -> None:
        """Register a plugin."""
        self._plugin_mgr.register(plugin, self)

    def on(self, event: str, callback) -> None:
        """Register event callback (shorthand for EventBus)."""
        self._event_bus.subscribe(event, callback)

    def store(self, content: str, importance: float = 0.5,
              metadata: dict | None = None,
              auto_evaluate: bool = False,
              skip_summarize: bool = False,
              encrypted: bool = False,
              role: str | None = None,
              emotion: EmotionVector | None = None,
              content_type: str | None = None,
              user_id: str | None = None) -> MemoryItem:
        # P6: RBAC check
        if self._access_control and role:
            self._access_control.require_permission(role, "write")
            if self._audit:
                self._audit.log_access(role, "", "store")

        item = MemoryItem.create(content, importance, metadata, user_id=user_id)
        # P9: Content type detection/assignment
        if content_type is not None:
            item.content_type = content_type
        elif self.config.multimodal.enabled:
            from stellar_memory.multimodal import detect_content_type
            item.content_type = detect_content_type(content)
        self._session_mgr.tag_memory(item)
        if auto_evaluate:
            result = self._evaluator.evaluate(content)
            item.arbitrary_importance = result.importance
            item.metadata["evaluation"] = result.method

        # P6: Auto-encrypt by tag or explicit flag
        should_encrypt = encrypted
        if (not should_encrypt and self._encryption
                and self._encryption.enabled
                and self.config.security.auto_encrypt_tags):
            tags = (metadata or {}).get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                if tag in self.config.security.auto_encrypt_tags:
                    should_encrypt = True
                    break

        if should_encrypt and self._encryption and self._encryption.enabled:
            item.content = self._encryption.encrypt(content)
            item.encrypted = True
            if self._audit:
                self._audit.log_encrypt(item.id)

        # P7: Emotion analysis
        if emotion is not None:
            item.emotion = emotion
        elif self._emotion_analyzer is not None:
            item.emotion = self._emotion_analyzer.analyze(content)

        item.embedding = self._embedder.embed(content)

        # Consolidation: try to merge with similar existing memory
        if (self.config.consolidation.enabled
                and self.config.consolidation.on_store
                and item.embedding is not None):
            existing = self._find_similar_in_zones(item)
            if existing is not None:
                merged = self._consolidator.merge(existing, item)
                # Plugin hook: on_consolidate
                merged = self._plugin_mgr.dispatch_consolidate(merged, [existing, item])
                storage = self._orbit_mgr.get_storage(existing.zone)
                storage.update(merged)
                self._event_bus.emit("on_consolidate", existing, item)
                self._event_bus.emit("on_store", merged)
                return merged

        # P5: Summarization pipeline
        if (not skip_summarize
                and self._summarizer is not None
                and self._summarizer.should_summarize(content)):
            summary_text = self._summarizer.summarize(content)
            if summary_text:
                summary_importance = min(
                    1.0, importance + self.config.summarization.importance_boost
                )
                summary_item = self.store(
                    content=f"[Summary] {summary_text}",
                    importance=summary_importance,
                    metadata={
                        **(metadata or {}),
                        "type": "summary",
                        "original_length": len(content),
                    },
                    skip_summarize=True,
                )
                # Store original at given importance
                original_item = self._store_internal(
                    content, importance, metadata, auto_evaluate, item
                )
                # Link summary → original
                if self.config.graph.enabled:
                    self._graph.add_edge(
                        summary_item.id, original_item.id, "derived_from", weight=1.0
                    )
                self._event_bus.emit("on_summarize", summary_item, original_item)
                return summary_item

        return self._store_internal(content, importance, metadata, auto_evaluate, item)

    def _store_internal(self, content: str, importance: float,
                        metadata: dict | None, auto_evaluate: bool,
                        item: MemoryItem) -> MemoryItem:
        """Internal store: place item, auto-link, register in vector index."""
        now = time.time()
        breakdown = self._memory_fn.calculate(item, now)
        item.total_score = breakdown.total
        self._orbit_mgr.place(item, breakdown.target_zone, breakdown.total)

        # Register in vector index
        if item.embedding is not None:
            self._vector_index.add(item.id, item.embedding)

        # Graph: auto-link to similar memories
        if self.config.graph.enabled and self.config.graph.auto_link:
            self._auto_link(item)

        # Plugin hook: on_store
        item = self._plugin_mgr.dispatch_store(item)

        self._event_bus.emit("on_store", item)
        return item

    def recall(self, query: str, limit: int = 5,
               role: str | None = None,
               emotion: str | None = None,
               user_id: str | None = None) -> list[MemoryItem]:
        # P6: RBAC check
        if self._access_control and role:
            self._access_control.require_permission(role, "read")
            if self._audit:
                self._audit.log_access(role, "", "recall")

        # Plugin hook: pre_recall
        query = self._plugin_mgr.dispatch_pre_recall(query)

        query_embedding = self._embedder.embed(query)
        results: list[MemoryItem] = []
        session_id = self._session_mgr.current_session_id

        if session_id and self.config.session.scope_current_first:
            # Phase 1: current session items first
            for zone_id in sorted(self._orbit_mgr._zones.keys()):
                storage = self._orbit_mgr.get_storage(zone_id)
                matches = storage.search(query, limit, query_embedding=query_embedding)
                for m in matches:
                    if m.metadata.get("session_id") == session_id:
                        results.append(m)
            # Phase 2: fill remaining from all items
            if len(results) < limit:
                existing_ids = {r.id for r in results}
                for zone_id in sorted(self._orbit_mgr._zones.keys()):
                    if len(results) >= limit:
                        break
                    storage = self._orbit_mgr.get_storage(zone_id)
                    matches = storage.search(query, limit, query_embedding=query_embedding)
                    for m in matches:
                        if m.id not in existing_ids:
                            results.append(m)
                            existing_ids.add(m.id)
                            if len(results) >= limit:
                                break
        else:
            for zone_id in sorted(self._orbit_mgr._zones.keys()):
                if len(results) >= limit:
                    break
                storage = self._orbit_mgr.get_storage(zone_id)
                matches = storage.search(query, limit - len(results),
                                         query_embedding=query_embedding)
                results.extend(matches)

        now = time.time()
        for item in results:
            item.recall_count += 1
            item.last_recalled_at = now
            storage = self._orbit_mgr.get_storage(item.zone)
            storage.update(item)

        results = results[:limit]

        # Multi-tenant: filter by user_id if provided
        if user_id:
            results = [r for r in results if r.user_id is None or r.user_id == user_id]

        # Graph boost: enhance results with graph-connected memories
        if (self.config.recall_boost.graph_boost_enabled
                and self.config.graph.enabled
                and results):
            results = self._apply_graph_boost(results, query_embedding, limit)

        # P6: Auto-decrypt encrypted memories
        if self._encryption and self._encryption.enabled:
            for item in results:
                if item.encrypted:
                    try:
                        item.content = self._encryption.decrypt(item.content)
                        if self._audit:
                            self._audit.log_decrypt(item.id)
                    except Exception:
                        pass  # leave encrypted if decrypt fails

        # P7: Emotion filter
        if emotion is not None:
            results = [
                r for r in results
                if r.emotion is not None and r.emotion.dominant == emotion
            ]

        # Plugin hook: on_recall
        results = self._plugin_mgr.dispatch_recall(query, results)

        self._last_recall_ids = [item.id for item in results]

        # P9: Log recall for self-learning
        if self._pattern_collector is not None and results:
            try:
                self._pattern_collector.log_recall(
                    query, [item.id for item in results]
                )
            except Exception:
                pass

        self._event_bus.emit("on_recall", results, query)
        return results

    def get(self, memory_id: str) -> MemoryItem | None:
        return self._orbit_mgr.find_item(memory_id)

    def forget(self, memory_id: str, user_id: str | None = None) -> bool:
        # Plugin hook: on_forget (can cancel)
        if not self._plugin_mgr.dispatch_forget(memory_id):
            return False

        item = self._orbit_mgr.find_item(memory_id)
        if item is None:
            return False
        if user_id and item.user_id and item.user_id != user_id:
            return False
        storage = self._orbit_mgr.get_storage(item.zone)
        removed = storage.remove(memory_id)
        if removed:
            self._graph.remove_item(memory_id)
            self._vector_index.remove(memory_id)
            self._event_bus.emit("on_forget", memory_id)
        return removed

    def reorbit(self) -> ReorbitResult:
        result = self._orbit_mgr.reorbit_all(self._memory_fn, time.time())

        # Plugin hook: on_reorbit
        moves = [(str(i), 0, 0) for i in range(result.moved)]
        self._plugin_mgr.dispatch_reorbit(moves)

        self._event_bus.emit("on_reorbit", result)

        # Apply decay after reorbit
        if self.config.decay.enabled:
            self._apply_decay()

        return result

    def stats(self) -> MemoryStats:
        zone_counts: dict[int, int] = {}
        zone_capacities: dict[int, int | None] = {}
        total = 0
        for zone_id, zone_cfg in sorted(self._orbit_mgr._zones.items()):
            count = self._orbit_mgr.get_zone_count(zone_id)
            zone_counts[zone_id] = count
            zone_capacities[zone_id] = zone_cfg.max_slots
            total += count
        return MemoryStats(
            zone_counts=zone_counts,
            zone_capacities=zone_capacities,
            total_memories=total,
        )

    def _health(self) -> HealthStatus:
        """Run health diagnostics on the memory system."""
        status = HealthStatus()

        try:
            s = self.stats()
            status.db_accessible = True
            status.total_memories = s.total_memories

            for zone_id, count in s.zone_counts.items():
                cap = s.zone_capacities.get(zone_id)
                if cap:
                    pct = count / cap * 100
                    status.zone_usage[zone_id] = f"{count}/{cap} ({pct:.0f}%)"
                    if pct >= 80:
                        status.warnings.append(
                            f"Zone {zone_id} at {pct:.0f}% capacity"
                        )
                else:
                    status.zone_usage[zone_id] = f"{count}/unlimited"
        except Exception:
            status.db_accessible = False
            status.healthy = False
            status.warnings.append("Database is not accessible")

        status.scheduler_running = self._scheduler.running
        status.graph_edges = self._graph.count_edges()

        if not status.db_accessible:
            status.healthy = False

        return status

    # --- F4: WeightTuner Integration ---

    def _provide_feedback(self, query: str, used_ids: list[str]) -> None:
        record = FeedbackRecord(
            query=query,
            result_ids=self._last_recall_ids,
            used_ids=used_ids,
        )
        self._tuner.record_feedback(record)

    def _auto_tune(self) -> dict[str, float] | None:
        return self._tuner.tune()

    def _create_middleware(self, max_context: int = 5):
        """Create an LLM integration middleware."""
        from stellar_memory.llm_adapter import MemoryMiddleware
        return MemoryMiddleware(self, recall_limit=max_context)

    # --- F2: Session Management ---

    def _start_session(self) -> SessionInfo:
        return self._session_mgr.start_session()

    def _end_session(self, summarize: bool | None = None) -> SessionInfo | None:
        session = self._session_mgr.end_session()
        if session is None:
            return None
        should_summarize = (
            summarize if summarize is not None else self.config.session.auto_summarize
        )
        if should_summarize:
            session.summary = self._summarize_session(session.session_id)
            if session.summary:
                self.store(
                    content=f"[Session Summary] {session.summary}",
                    importance=0.7,
                    metadata={"type": "session_summary", "session_id": session.session_id},
                )
        return session

    def _summarize_session(self, session_id: str) -> str:
        items = self._get_session_items(session_id)
        items.sort(key=lambda x: x.arbitrary_importance, reverse=True)
        top = items[:self.config.session.summary_max_items]
        if not top:
            return ""
        return " | ".join(item.content[:100] for item in top)

    def _get_session_items(self, session_id: str) -> list[MemoryItem]:
        all_items = self._orbit_mgr.get_all_items()
        return [i for i in all_items if i.metadata.get("session_id") == session_id]

    # --- F1: Consolidation helper ---

    def _find_similar_in_zones(self, item: MemoryItem) -> MemoryItem | None:
        for zone_id in sorted(self._orbit_mgr._zones.keys()):
            storage = self._orbit_mgr.get_storage(zone_id)
            candidates = storage.get_all()
            match = self._consolidator.find_similar(item, candidates)
            if match is not None:
                return match
        return None

    # --- F3: Export/Import ---

    def export_json(self, include_embeddings: bool = True) -> str:
        items = self._orbit_mgr.get_all_items()
        serializer = MemorySerializer(self.config.embedder.dimension)
        return serializer.export_json(items, include_embeddings)

    def import_json(self, json_str: str) -> int:
        serializer = MemorySerializer(self.config.embedder.dimension)
        items = serializer.import_json(json_str)
        for item in items:
            if item.zone >= 0:
                self._orbit_mgr.place(item, item.zone, item.total_score)
            else:
                breakdown = self._memory_fn.calculate(item, time.time())
                self._orbit_mgr.place(item, breakdown.target_zone, breakdown.total)
            # Register in vector index
            if item.embedding is not None:
                self._vector_index.add(item.id, item.embedding)
        return len(items)

    def _snapshot(self) -> MemorySnapshot:
        items = self._orbit_mgr.get_all_items()
        serializer = MemorySerializer(self.config.embedder.dimension)
        return serializer.snapshot(items)

    # --- Memory Graph ---

    def _auto_link(self, item: MemoryItem) -> None:
        """Automatically create edges to similar memories using vector index."""
        if item.embedding is None:
            return
        threshold = self.config.graph.auto_link_threshold

        # Use vector index for O(log n) search
        if self._vector_index.size() > 1:
            candidates = self._vector_index.search(item.embedding, top_k=20)
            for other_id, sim in candidates:
                if other_id == item.id:
                    continue
                if sim >= threshold:
                    self._graph.add_edge(item.id, other_id, "related_to", weight=sim)
        else:
            # Fallback: brute force for very small datasets
            all_items = self._orbit_mgr.get_all_items()
            for other in all_items:
                if other.id == item.id or other.embedding is None:
                    continue
                sim = cosine_similarity(item.embedding, other.embedding)
                if sim >= threshold:
                    self._graph.add_edge(item.id, other.id, "related_to", weight=sim)

    def link(self, source_id: str, target_id: str,
             relation: str = "related", weight: float = 1.0) -> None:
        """Explicitly link two memories in the knowledge graph."""
        if not self.config.graph.enabled:
            raise RuntimeError("Graph is not enabled")
        self._graph.add_edge(source_id, target_id, relation, weight=weight)

    def related(self, memory_id: str, depth: int = 2) -> list[MemoryItem]:
        """Get memories related through the knowledge graph."""
        related_ids = self._graph.get_related_ids(memory_id, depth)
        items = []
        for rid in related_ids:
            item = self._orbit_mgr.find_item(rid)
            if item is not None:
                items.append(item)
        return items

    def _recall_graph(self, item_id: str, depth: int = 2) -> list[MemoryItem]:
        """Deprecated: Use related() instead."""
        return self.related(item_id, depth)

    @property
    def graph(self):
        return self._graph

    @property
    def graph_analyzer(self):
        """Public access to graph analytics module."""
        return self._analyzer

    @property
    def analyzer(self):
        return self._analyzer

    @property
    def session(self):
        """Public access to session management module."""
        return self._session_mgr

    @property
    def session_manager(self):
        """Alias for backward compat. Prefer `session`."""
        return self._session_mgr

    @property
    def self_learning(self):
        """Public access to self-learning module."""
        return self._weight_optimizer

    # --- P5: Graph Analytics ---

    def _graph_stats(self):
        if self._analyzer is None:
            raise RuntimeError("Graph analytics not enabled")
        return self._analyzer.stats()

    def _graph_communities(self) -> list[list[str]]:
        if self._analyzer is None:
            raise RuntimeError("Graph analytics not enabled")
        return self._analyzer.communities()

    def _graph_centrality(self, top_k: int = 10):
        if self._analyzer is None:
            raise RuntimeError("Graph analytics not enabled")
        return self._analyzer.centrality(top_k)

    def _graph_path(self, source_id: str, target_id: str) -> list[str] | None:
        if self._analyzer is None:
            raise RuntimeError("Graph analytics not enabled")
        return self._analyzer.path(source_id, target_id)

    # --- Recall Boost ---

    def _apply_graph_boost(self, results: list[MemoryItem],
                           query_embedding: list[float] | None,
                           limit: int) -> list[MemoryItem]:
        """Boost recall results using graph connections."""
        result_ids = {r.id for r in results}
        boosted: list[MemoryItem] = list(results)
        depth = self.config.recall_boost.graph_boost_depth
        boost_score = self.config.recall_boost.graph_boost_score

        neighbor_ids: set[str] = set()
        for item in results:
            related = self._graph.get_related_ids(item.id, depth=depth)
            neighbor_ids.update(related - result_ids)

        for nid in neighbor_ids:
            neighbor = self._orbit_mgr.find_item(nid)
            if neighbor is not None:
                neighbor.total_score += boost_score
                boosted.append(neighbor)

        boosted.sort(key=lambda x: x.total_score, reverse=True)
        return boosted[:limit]

    # --- Memory Decay ---

    def _apply_decay(self) -> DecayResult:
        """Apply memory decay: demote stale memories, forget ancient ones."""
        all_items = self._orbit_mgr.get_all_items()

        # Plugin hook: on_decay for each item
        for item in all_items:
            item.total_score = self._plugin_mgr.dispatch_decay(item, item.total_score)

        decay = self._decay_mgr.check_decay(all_items, time.time())

        for item_id in decay.to_forget:
            self.forget(item_id)
            self._event_bus.emit("on_auto_forget", item_id)
            decay.forgotten += 1

        for item_id, from_zone, to_zone in decay.to_demote:
            max_zone = max(self._orbit_mgr._zones.keys())
            if to_zone <= max_zone:
                item = self._orbit_mgr.find_item(item_id)
                if item is not None:
                    self._orbit_mgr.move(item.id, from_zone, to_zone, item.total_score)
                    self._event_bus.emit("on_zone_change", item, from_zone, to_zone)
                    decay.demoted += 1

        if decay.demoted > 0 or decay.forgotten > 0:
            self._event_bus.emit("on_decay", decay)

        return decay

    # --- P6: Security ---

    def _encrypt_memory(self, memory_id: str) -> bool:
        """Encrypt a memory's content in place."""
        if not self._encryption or not self._encryption.enabled:
            return False
        item = self.get(memory_id)
        if item is None or item.encrypted:
            return False
        item.content = self._encryption.encrypt(item.content)
        item.encrypted = True
        storage = self._orbit_mgr.get_storage(item.zone)
        storage.update(item)
        if self._audit:
            self._audit.log_encrypt(memory_id)
        return True

    def _decrypt_memory(self, memory_id: str) -> str | None:
        """Decrypt and return a memory's content (does not alter storage)."""
        if not self._encryption or not self._encryption.enabled:
            return None
        item = self.get(memory_id)
        if item is None or not item.encrypted:
            return item.content if item else None
        decrypted = self._encryption.decrypt(item.content)
        if self._audit:
            self._audit.log_decrypt(memory_id)
        return decrypted

    # --- P6: Knowledge Ingestion ---

    def _ingest(self, source: str, importance: float = 0.5,
                **kwargs) -> IngestResult:
        """Ingest external knowledge from web, file, or API."""
        if not self.config.connectors.enabled:
            raise RuntimeError("Connectors are not enabled")

        from stellar_memory.connectors.web_connector import WebConnector as _WC
        from stellar_memory.connectors.file_connector import FileConnector as _FC
        from stellar_memory.connectors.api_connector import ApiConnector as _AC

        connectors = []
        if self.config.connectors.web_enabled:
            connectors.append(_WC(summarizer=self._summarizer,
                                  consolidator=self._consolidator))
        if self.config.connectors.file_enabled:
            connectors.append(_FC(summarizer=self._summarizer))
        if self.config.connectors.api_enabled:
            connectors.append(_AC(summarizer=self._summarizer))

        for conn in connectors:
            if conn.can_handle(source):
                result = conn.ingest(source, **kwargs)
                item = self.store(
                    content=result.summary_text,
                    importance=importance,
                    metadata={"source_type": "ingested", "source_url": source},
                )
                result.memory_id = item.id
                return result

        raise ValueError(f"No connector can handle source: {source}")

    # --- P7: Memory Stream ---

    @property
    def stream(self):
        """Lazy-initialized MemoryStream."""
        if self._stream is None:
            from stellar_memory.stream import MemoryStream
            self._stream = MemoryStream(self)
        return self._stream

    def _timeline(self, start=None, end=None,
                  limit: int = 100,
                  user_id: str | None = None) -> list[TimelineEntry]:
        """Time-ordered memory timeline."""
        return self.stream.timeline(start, end, limit, user_id=user_id)

    def _narrate(self, topic: str, limit: int = 10,
                 user_id: str | None = None) -> str:
        """Generate narrative from memories about a topic."""
        return self.stream.narrate(topic, limit, user_id=user_id)

    # --- P9: Metacognition ---

    def introspect(self, topic: str, depth: int = 1) -> IntrospectionResult:
        """Analyze knowledge state for a given topic."""
        if self._introspector is None:
            from stellar_memory.metacognition import Introspector
            self._introspector = Introspector(self.config.metacognition)

        memories = self.recall(topic, limit=50)

        # Get graph neighbors for gap detection
        graph_neighbors = None
        if self.config.graph.enabled and memories:
            neighbor_ids: set[str] = set()
            for m in memories[:5]:
                related = self._graph.get_related_ids(m.id, depth=depth)
                neighbor_ids.update(related)
            neighbor_items = []
            for nid in neighbor_ids:
                item = self._orbit_mgr.find_item(nid)
                if item is not None:
                    neighbor_items.append(item)
            # Extract neighbor tags/keywords as gap candidates
            graph_neighbors = []
            for ni in neighbor_items:
                if ni.metadata and "tags" in ni.metadata:
                    graph_neighbors.extend(ni.metadata["tags"])
                words = ni.content.lower().split()
                for w in words:
                    cleaned = w.strip(".,!?;:'\"()[]{}").strip()
                    if len(cleaned) > 4 and cleaned.isalpha():
                        graph_neighbors.append(cleaned)
            graph_neighbors = list(set(graph_neighbors))

        result = self._introspector.introspect(
            topic, memories, graph_neighbors=graph_neighbors
        )
        self._event_bus.emit("introspect", {"topic": topic, "confidence": result.confidence})
        return result

    def _recall_with_confidence(self, query: str, top_k: int = 5,
                                threshold: float = 0.0) -> ConfidentRecall:
        """Recall memories with confidence scoring."""
        if self._confidence_scorer is None:
            from stellar_memory.metacognition import ConfidenceScorer
            self._confidence_scorer = ConfidenceScorer(self.config.metacognition)

        memories = self.recall(query, limit=top_k)
        result = self._confidence_scorer.score(memories, query)
        if threshold > 0 and result.confidence < threshold:
            result.warning = (
                f"Confidence {result.confidence:.3f} below threshold {threshold}"
            )
        return result

    # --- P9: Self-Learning ---

    def _optimize(self, min_logs: int | None = None) -> OptimizationReport:
        """Optimize memory function weights from recall patterns."""
        if self._pattern_collector is None or self._weight_optimizer is None:
            from stellar_memory.self_learning import PatternCollector, WeightOptimizer
            sl_db = self.config.db_path.replace(".db", "_learning.db")
            if self.config.db_path == ":memory:":
                sl_db = ":memory:"
            self._pattern_collector = PatternCollector(sl_db)
            self._weight_optimizer = WeightOptimizer(
                self.config.memory_function, self.config.self_learning, sl_db
            )

        effective_min = min_logs if min_logs is not None else self.config.self_learning.min_logs
        logs = self._pattern_collector.get_logs(limit=1000)
        if len(logs) < effective_min:
            raise ValueError(
                f"Need at least {effective_min} recall logs, got {len(logs)}"
            )

        patterns = self._pattern_collector.analyze_patterns(logs)
        report = self._weight_optimizer.optimize(patterns, logs)
        self._event_bus.emit("optimize", {
            "before": report.before_weights,
            "after": report.after_weights,
            "rolled_back": report.rolled_back,
        })
        return report

    def _rollback_weights(self) -> dict[str, float]:
        """Rollback to previous memory function weights."""
        if self._weight_optimizer is None:
            raise RuntimeError("Self-learning is not initialized")
        weights = self._weight_optimizer.rollback()
        self._event_bus.emit("optimize", {"action": "rollback", "weights": weights})
        return weights

    # --- P9: Reasoning ---

    def reason(self, query: str, max_sources: int | None = None) -> ReasoningResult:
        """Derive insights by reasoning over related memories."""
        if self._reasoner is None:
            from stellar_memory.reasoning import MemoryReasoner
            self._reasoner = MemoryReasoner(self.config.reasoning)

        effective_max = max_sources or self.config.reasoning.max_sources
        memories = self.recall(query, limit=effective_max)

        # Optionally include graph neighbors
        graph_neighbors = None
        if self.config.graph.enabled and memories:
            neighbor_ids: set[str] = set()
            seen = {m.id for m in memories}
            for m in memories[:3]:
                related = self._graph.get_related_ids(m.id, depth=1)
                neighbor_ids.update(related - seen)
            graph_neighbors = []
            for nid in list(neighbor_ids)[:5]:
                item = self._orbit_mgr.find_item(nid)
                if item is not None:
                    graph_neighbors.append(item)

        result = self._reasoner.reason(query, memories, graph_neighbors)
        self._event_bus.emit("reason", {
            "query": query, "insight_count": len(result.insights)
        })
        return result

    def _detect_contradictions(self, scope: str | None = None) -> list[Contradiction]:
        """Detect contradictions among memories."""
        from stellar_memory.reasoning import ContradictionDetector

        if scope:
            memories = self.recall(scope, limit=20)
        else:
            memories = self._orbit_mgr.get_all_items()[:50]

        llm = None
        if self.config.reasoning.use_llm:
            try:
                from stellar_memory.llm_adapter import create_llm_adapter
                llm = create_llm_adapter(self.config.llm)
            except Exception:
                pass

        detector = ContradictionDetector(self.config.reasoning, llm)
        contradictions = detector.detect(memories)

        for c in contradictions:
            self._event_bus.emit("contradiction_found", {
                "mem_a_id": c.memory_a_id,
                "mem_b_id": c.memory_b_id,
                "severity": c.severity,
            })
        return contradictions

    # --- P9: Benchmark ---

    def _benchmark(self, queries: int = 100, dataset: str = "standard",
                   seed: int = 42) -> BenchmarkReport:
        """Run comprehensive memory system benchmark."""
        from stellar_memory.benchmark import MemoryBenchmark
        bench = MemoryBenchmark(self)
        report = bench.run(queries=queries, dataset=dataset, seed=seed)
        self._event_bus.emit("benchmark_complete", {
            "recall_at_5": report.recall_at_5,
            "avg_latency": report.avg_recall_latency_ms,
        })
        return report

    # --- Lifecycle ---

    def start(self) -> None:
        self._scheduler.start()

    def stop(self) -> None:
        self._plugin_mgr.shutdown()
        self._scheduler.stop()
        self._tuner.close()
        if self._sync:
            self._sync.stop()
        if self._redis_cache:
            self._redis_cache.disconnect()

    # --- v3.0 Backward Compatibility ---
    # Methods moved to private API. Old names still work via __getattr__.

    _DEPRECATED_METHODS: dict[str, str] = {
        "health": "_health",
        "provide_feedback": "_provide_feedback",
        "auto_tune": "_auto_tune",
        "create_middleware": "_create_middleware",
        "start_session": "_start_session",
        "end_session": "_end_session",
        "snapshot": "_snapshot",
        "recall_graph": "_recall_graph",
        "graph_stats": "_graph_stats",
        "graph_communities": "_graph_communities",
        "graph_centrality": "_graph_centrality",
        "graph_path": "_graph_path",
        "encrypt_memory": "_encrypt_memory",
        "decrypt_memory": "_decrypt_memory",
        "ingest": "_ingest",
        "timeline": "_timeline",
        "narrate": "_narrate",
        "recall_with_confidence": "_recall_with_confidence",
        "optimize": "_optimize",
        "rollback_weights": "_rollback_weights",
        "detect_contradictions": "_detect_contradictions",
        "benchmark": "_benchmark",
    }

    def __getattr__(self, name: str):
        if name in StellarMemory._DEPRECATED_METHODS:
            import warnings
            warnings.warn(
                f"StellarMemory.{name}() is deprecated in v3.0. "
                f"Use the internal API or plugin system instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            return getattr(self, StellarMemory._DEPRECATED_METHODS[name])
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )
