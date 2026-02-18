# Design: stellar-memory-p5 (Advanced Intelligence & Scalability)

**Version**: v0.6.0
**Plan Reference**: `docs/01-plan/features/stellar-memory-p5.plan.md`
**Previous**: v0.5.0 (26 source files, 237 tests, 98% avg match rate)

---

## 1. Architecture Overview

### 1.1 New Component Diagram

```
StellarMemory (stellar.py)
├── ProviderRegistry (providers/)          ← F1: NEW
│   ├── AnthropicProvider (built-in)
│   ├── OpenAIProvider (optional)
│   └── OllamaProvider (optional)
├── VectorIndex (vector_index.py)          ← F2: NEW
│   ├── BruteForceIndex (default)
│   ├── BallTreeIndex (built-in)
│   └── FaissIndex (optional)
├── MemorySummarizer (summarizer.py)       ← F3: NEW
├── AdaptiveDecayManager (adaptive_decay.py) ← F4: NEW
├── GraphAnalyzer (graph_analyzer.py)      ← F5: NEW
│
├── MemoryFunction (memory_function.py)    ← existing
├── Embedder / NullEmbedder (embedder.py)  ← modified
├── LLMEvaluator (importance_evaluator.py) ← modified
├── OrbitManager (orbit_manager.py)        ← existing
├── PersistentGraph (persistent_graph.py)  ← existing
├── DecayManager (decay_manager.py)        ← modified
├── EventBus (event_bus.py)                ← modified
├── EventLogger (event_logger.py)          ← existing
├── SessionManager (session.py)            ← existing
├── Consolidator (consolidator.py)         ← existing
└── Scheduler (scheduler.py)              ← existing
```

### 1.2 Dependency Graph (P5 Features)

```
F1 Multi-Provider ──→ F3 AI Summarization (needs LLM)
                  ──→ importance_evaluator (OpenAI/Ollama support)
F2 Vector Index   ──→ stellar.py auto_link + recall (performance)
F4 Adaptive Decay ──→ decay_manager (extends existing)
F5 Graph Analytics ──→ persistent_graph / memory_graph (reads graph)
```

---

## 2. Feature Specifications

### F1: Multi-Provider LLM/Embedder Support

#### 2.1.1 Config Changes

```python
# config.py additions

@dataclass
class EmbedderConfig:
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    enabled: bool = True
    provider: str = "sentence-transformers"  # NEW: "sentence-transformers" | "openai" | "ollama"

@dataclass
class LLMConfig:
    provider: str = "anthropic"  # existing: "anthropic" | "openai" | "ollama"
    model: str = "claude-haiku-4-5-20251001"
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 256
    enabled: bool = True
    base_url: str | None = None  # NEW: for Ollama custom endpoint
```

#### 2.1.2 ProviderRegistry

```python
# providers/__init__.py

from typing import Protocol

class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    def complete(self, prompt: str, max_tokens: int = 256) -> str: ...

class EmbedderProvider(Protocol):
    """Protocol for embedding providers."""
    def embed(self, text: str) -> list[float]: ...
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

class ProviderRegistry:
    """Registry for LLM and Embedder providers."""

    _llm_factories: dict[str, Callable] = {}
    _embedder_factories: dict[str, Callable] = {}

    @classmethod
    def register_llm(cls, name: str, factory: Callable) -> None: ...

    @classmethod
    def register_embedder(cls, name: str, factory: Callable) -> None: ...

    @classmethod
    def create_llm(cls, config: LLMConfig) -> LLMProvider: ...

    @classmethod
    def create_embedder(cls, config: EmbedderConfig) -> EmbedderProvider: ...
```

Auto-register on import:
- `"anthropic"` → existing AnthropicProvider (from importance_evaluator.py logic)
- `"openai"` → OpenAIProvider (try import openai, fallback to NullProvider)
- `"ollama"` → OllamaProvider (try import ollama, fallback to NullProvider)
- `"sentence-transformers"` → existing Embedder class
- `"rule"` → existing RuleBasedEvaluator (no LLM needed)

#### 2.1.3 OpenAI Provider

```python
# providers/openai_provider.py

class OpenAILLMProvider:
    """OpenAI GPT-based LLM provider."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._client = None  # lazy init

    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        """Call OpenAI chat completions API."""
        import os
        from openai import OpenAI
        if self._client is None:
            api_key = os.environ.get(self._config.api_key_env, "")
            self._client = OpenAI(api_key=api_key)
        response = self._client.chat.completions.create(
            model=self._config.model or "gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content


class OpenAIEmbedderProvider:
    """OpenAI text-embedding provider."""

    def __init__(self, config: EmbedderConfig):
        self._config = config
        self._client = None

    def embed(self, text: str) -> list[float]:
        import os
        from openai import OpenAI
        if self._client is None:
            self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        response = self._client.embeddings.create(
            model=self._config.model_name or "text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import os
        from openai import OpenAI
        if self._client is None:
            self._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        response = self._client.embeddings.create(
            model=self._config.model_name or "text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in response.data]
```

#### 2.1.4 Ollama Provider

```python
# providers/ollama_provider.py

class OllamaLLMProvider:
    """Ollama local LLM provider."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._base_url = config.base_url or "http://localhost:11434"

    def complete(self, prompt: str, max_tokens: int = 256) -> str:
        """Call Ollama generate API."""
        import requests
        response = requests.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._config.model or "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens},
            },
        )
        response.raise_for_status()
        return response.json()["response"]


class OllamaEmbedderProvider:
    """Ollama local embedding provider."""

    def __init__(self, config: EmbedderConfig):
        self._config = config
        self._base_url = "http://localhost:11434"

    def embed(self, text: str) -> list[float]:
        import requests
        response = requests.post(
            f"{self._base_url}/api/embed",
            json={
                "model": self._config.model_name or "nomic-embed-text",
                "input": text,
            },
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
```

#### 2.1.5 Integration Points

**importance_evaluator.py** changes:
```python
# LLMEvaluator._call_llm() currently has:
#   if self._config.provider == "anthropic": ...
#   else: raise ValueError(...)
#
# Change to use ProviderRegistry:
def _call_llm(self, content: str) -> EvaluationResult:
    from stellar_memory.providers import ProviderRegistry
    llm = ProviderRegistry.create_llm(self._config)
    raw = llm.complete(prompt, self._config.max_tokens)
    # ... parse JSON response (same logic)
```

**create_evaluator()** changes:
```python
def create_evaluator(config: LLMConfig | None = None):
    cfg = config or LLMConfig()
    if not cfg.enabled:
        return NullEvaluator()
    # Try to create provider via registry
    try:
        from stellar_memory.providers import ProviderRegistry
        ProviderRegistry.create_llm(cfg)  # test if provider is available
        return LLMEvaluator(cfg)
    except Exception:
        return RuleBasedEvaluator()
```

**embedder.py** changes:
```python
def create_embedder(config: EmbedderConfig | None = None):
    cfg = config or EmbedderConfig()
    if not cfg.enabled:
        return NullEmbedder()
    if cfg.provider == "sentence-transformers":
        # existing logic
        try:
            import sentence_transformers
            return Embedder(cfg)
        except ImportError:
            return NullEmbedder()
    else:
        # Use ProviderRegistry for openai/ollama
        try:
            from stellar_memory.providers import ProviderRegistry
            return ProviderRegistry.create_embedder(cfg)
        except Exception:
            return NullEmbedder()
```

---

### F2: Vector Index (Scalable Search)

#### 2.2.1 Config

```python
# config.py addition

@dataclass
class VectorIndexConfig:
    enabled: bool = True
    backend: str = "brute_force"  # "brute_force" | "ball_tree" | "faiss"
    rebuild_on_start: bool = True
    ball_tree_leaf_size: int = 40
```

Add to StellarConfig:
```python
vector_index: VectorIndexConfig = field(default_factory=VectorIndexConfig)
```

#### 2.2.2 VectorIndex Interface

```python
# vector_index.py

from abc import ABC, abstractmethod

class VectorIndex(ABC):
    """Abstract base for vector search indices."""

    @abstractmethod
    def add(self, item_id: str, vector: list[float]) -> None: ...

    @abstractmethod
    def remove(self, item_id: str) -> None: ...

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        """Returns list of (item_id, similarity_score) sorted descending."""
        ...

    @abstractmethod
    def size(self) -> int: ...

    def rebuild(self, items: dict[str, list[float]]) -> None:
        """Rebuild index from scratch."""
        for item_id, vector in items.items():
            self.add(item_id, vector)
```

#### 2.2.3 BruteForceIndex

```python
class BruteForceIndex(VectorIndex):
    """O(n) brute force search - wraps existing cosine_similarity."""

    def __init__(self):
        self._vectors: dict[str, list[float]] = {}

    def add(self, item_id: str, vector: list[float]) -> None:
        self._vectors[item_id] = vector

    def remove(self, item_id: str) -> None:
        self._vectors.pop(item_id, None)

    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        from stellar_memory.utils import cosine_similarity
        scores = []
        for item_id, vec in self._vectors.items():
            sim = cosine_similarity(query_vector, vec)
            scores.append((item_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def size(self) -> int:
        return len(self._vectors)
```

#### 2.2.4 BallTreeIndex

```python
class BallTreeIndex(VectorIndex):
    """Ball-Tree based approximate nearest neighbor search.
    Pure Python implementation, no external dependencies.
    O(log n) average case search."""

    def __init__(self, leaf_size: int = 40):
        self._leaf_size = leaf_size
        self._vectors: dict[str, list[float]] = {}
        self._tree = None  # rebuilt lazily
        self._dirty = True

    def add(self, item_id: str, vector: list[float]) -> None:
        self._vectors[item_id] = vector
        self._dirty = True

    def remove(self, item_id: str) -> None:
        self._vectors.pop(item_id, None)
        self._dirty = True

    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        if self._dirty or self._tree is None:
            self._build_tree()
        return self._tree_search(query_vector, top_k)

    def _build_tree(self) -> None:
        """Build ball tree from current vectors."""
        # Implementation: recursive binary tree splitting by dimension
        # Each leaf node holds up to leaf_size vectors
        # Internal nodes hold centroid + radius for pruning
        ...
        self._dirty = False

    def _tree_search(self, query: list[float], top_k: int) -> list[tuple[str, float]]:
        """Search tree using branch-and-bound with cosine similarity."""
        ...

    def size(self) -> int:
        return len(self._vectors)

    def rebuild(self, items: dict[str, list[float]]) -> None:
        self._vectors = dict(items)
        self._dirty = True
```

**BallTree Node Structure**:
```python
@dataclass
class _BallTreeNode:
    centroid: list[float]
    radius: float
    item_ids: list[str] | None = None     # leaf node
    vectors: list[list[float]] | None = None  # leaf node
    left: _BallTreeNode | None = None      # internal
    right: _BallTreeNode | None = None     # internal
```

#### 2.2.5 FaissIndex (Optional)

```python
# faiss_index.py (separate file - optional dependency)

class FaissIndex(VectorIndex):
    """FAISS-based index for large-scale vector search (100k+)."""

    def __init__(self, dimension: int = 384):
        import faiss
        self._dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)  # inner product (cosine for normalized)
        self._id_map: list[str] = []

    def add(self, item_id: str, vector: list[float]) -> None: ...
    def remove(self, item_id: str) -> None: ...
    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]: ...
    def size(self) -> int: return self._index.ntotal
```

#### 2.2.6 Factory Function

```python
def create_vector_index(config: VectorIndexConfig,
                        dimension: int = 384) -> VectorIndex:
    if not config.enabled:
        return BruteForceIndex()  # minimal overhead when disabled
    if config.backend == "ball_tree":
        return BallTreeIndex(leaf_size=config.ball_tree_leaf_size)
    elif config.backend == "faiss":
        try:
            from stellar_memory.faiss_index import FaissIndex
            return FaissIndex(dimension=dimension)
        except ImportError:
            logger.warning("faiss not installed, falling back to BallTreeIndex")
            return BallTreeIndex(leaf_size=config.ball_tree_leaf_size)
    else:
        return BruteForceIndex()
```

#### 2.2.7 Integration into StellarMemory

```python
# stellar.py __init__ additions:
self._vector_index = create_vector_index(
    self.config.vector_index, self.config.embedder.dimension
)

# _auto_link() change:
def _auto_link(self, item: MemoryItem) -> None:
    if item.embedding is None:
        return
    # Register in vector index
    self._vector_index.add(item.id, item.embedding)

    threshold = self.config.graph.auto_link_threshold
    # Use index instead of O(n) scan
    candidates = self._vector_index.search(item.embedding, top_k=20)
    for other_id, sim in candidates:
        if other_id == item.id:
            continue
        if sim >= threshold:
            self._graph.add_edge(item.id, other_id, "related_to", weight=sim)

# store() addition: register embedding in index
# forget() addition: remove from index
# import_json() addition: rebuild index after import
```

---

### F3: AI Memory Summarization

#### 2.3.1 Config

```python
# config.py addition

@dataclass
class SummarizationConfig:
    enabled: bool = True
    min_length: int = 100       # minimum content length to trigger summarization
    max_summary_length: int = 200  # target summary length
    importance_boost: float = 0.1  # summary gets +0.1 importance vs original
```

Add to StellarConfig:
```python
summarization: SummarizationConfig = field(default_factory=SummarizationConfig)
```

#### 2.3.2 MemorySummarizer

```python
# summarizer.py

class MemorySummarizer:
    """AI-powered memory summarization."""

    PROMPT_TEMPLATE = (
        "Summarize the following text in one concise sentence "
        "(max {max_len} characters). Keep only the essential facts, "
        "dates, names, and action items.\n\n"
        "Text: {content}\n\n"
        "Summary:"
    )

    def __init__(self, config: SummarizationConfig, llm_config: LLMConfig):
        self._config = config
        self._llm_config = llm_config
        self._llm = None  # lazy init via ProviderRegistry

    def should_summarize(self, content: str) -> bool:
        """Check if content is long enough to warrant summarization."""
        return (self._config.enabled
                and len(content) >= self._config.min_length)

    def summarize(self, content: str) -> str | None:
        """Generate a summary of the content using LLM.
        Returns None if summarization fails or is disabled."""
        if not self.should_summarize(content):
            return None
        try:
            if self._llm is None:
                from stellar_memory.providers import ProviderRegistry
                self._llm = ProviderRegistry.create_llm(self._llm_config)
            prompt = self.PROMPT_TEMPLATE.format(
                max_len=self._config.max_summary_length,
                content=content,
            )
            result = self._llm.complete(prompt, max_tokens=self._config.max_summary_length)
            return result.strip()[:self._config.max_summary_length]
        except Exception:
            logger.warning("Summarization failed, storing original")
            return None
```

#### 2.3.3 StellarMemory.store() Integration

```python
def store(self, content: str, importance: float = 0.5,
          metadata: dict | None = None,
          auto_evaluate: bool = False,
          skip_summarize: bool = False) -> MemoryItem:
    # ... existing evaluation + embedding logic ...

    # NEW: Summarization pipeline
    if (not skip_summarize
            and self._summarizer is not None
            and self._summarizer.should_summarize(content)):
        summary_text = self._summarizer.summarize(content)
        if summary_text:
            # Store summary as a separate high-priority item
            summary_importance = min(1.0, importance + self.config.summarization.importance_boost)
            summary_item = self.store(
                content=f"[Summary] {summary_text}",
                importance=summary_importance,
                metadata={**(metadata or {}), "type": "summary", "original_length": len(content)},
                skip_summarize=True,  # prevent recursion
            )
            # Store original at lower zone
            item = self._store_internal(content, importance, metadata, auto_evaluate)
            # Link summary → original with derived_from edge
            if self.config.graph.enabled:
                self._graph.add_edge(summary_item.id, item.id, "derived_from", weight=1.0)
            self._event_bus.emit("on_summarize", summary_item, item)
            return summary_item  # return the summary as primary reference

    return self._store_internal(content, importance, metadata, auto_evaluate)
```

#### 2.3.4 New Events

```python
# event_bus.py EVENTS tuple addition:
"on_summarize",       # (summary_item, original_item)
```

#### 2.3.5 MCP Tool

```python
# mcp_server.py addition

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
```

#### 2.3.6 CLI Command

```python
# cli.py addition

# summarize subparser
p_summarize = subparsers.add_parser("summarize", help="Summarize a memory")
p_summarize.add_argument("id", help="Memory ID to summarize")

# handler
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
```

---

### F4: Adaptive Decay (Importance-Based Forgetting)

#### 2.4.1 Config

```python
# config.py addition

@dataclass
class AdaptiveDecayConfig:
    enabled: bool = False  # opt-in, disabled by default
    importance_weight: float = 1.0
    decay_curve: str = "linear"  # "linear" | "exponential" | "sigmoid"
    zone_factor: bool = True  # closer zones decay slower
```

Add to DecayConfig:
```python
@dataclass
class DecayConfig:
    enabled: bool = True
    decay_days: int = 30
    auto_forget_days: int = 90
    min_zone_for_decay: int = 2
    adaptive: AdaptiveDecayConfig = field(default_factory=AdaptiveDecayConfig)  # NEW
```

#### 2.4.2 AdaptiveDecayManager

```python
# adaptive_decay.py

import math
from stellar_memory.config import DecayConfig, AdaptiveDecayConfig
from stellar_memory.models import MemoryItem

SECONDS_PER_DAY = 86400


class AdaptiveDecayManager:
    """Importance-based differential decay rates."""

    def __init__(self, decay_config: DecayConfig):
        self._config = decay_config
        self._adaptive = decay_config.adaptive

    def effective_decay_days(self, item: MemoryItem) -> float:
        """Calculate effective decay days based on importance.

        Formula: base_days * (0.5 + importance * weight)
        - importance=0.9, weight=1.0 → 30 * 1.4 = 42 days
        - importance=0.3, weight=1.0 → 30 * 0.8 = 24 days
        - importance=0.0, weight=1.0 → 30 * 0.5 = 15 days
        """
        base = self._config.decay_days
        importance = item.arbitrary_importance
        weight = self._adaptive.importance_weight
        factor = 0.5 + importance * weight

        if self._adaptive.zone_factor and item.zone > 0:
            # Closer zones (smaller zone_id) decay slower
            # zone 2: * 1.5, zone 3: * 1.0, zone 4: * 0.75
            zone_multiplier = max(0.5, 2.0 - item.zone * 0.5)
            factor *= zone_multiplier

        return base * factor

    def effective_forget_days(self, item: MemoryItem) -> float:
        """Calculate effective auto-forget days."""
        base = self._config.auto_forget_days
        importance = item.arbitrary_importance
        return base * (0.5 + importance * self._adaptive.importance_weight)

    def apply_curve(self, elapsed_days: float, threshold_days: float) -> float:
        """Apply decay curve to determine decay severity.
        Returns 0.0 (no decay) to 1.0 (full decay)."""
        if elapsed_days < threshold_days:
            return 0.0
        ratio = elapsed_days / threshold_days

        if self._adaptive.decay_curve == "exponential":
            return 1.0 - math.exp(-(ratio - 1.0))
        elif self._adaptive.decay_curve == "sigmoid":
            x = (ratio - 1.0) * 5  # steepness factor
            return 1.0 / (1.0 + math.exp(-x))
        else:  # linear
            return min(1.0, ratio - 1.0)
```

#### 2.4.3 DecayManager Integration

```python
# decay_manager.py changes

class DecayManager:
    def __init__(self, config: DecayConfig):
        self._config = config
        self._adaptive = None
        if config.adaptive.enabled:
            from stellar_memory.adaptive_decay import AdaptiveDecayManager
            self._adaptive = AdaptiveDecayManager(config)

    def check_decay(self, items: list[MemoryItem],
                    current_time: float) -> DecayResult:
        result = DecayResult()
        if not self._config.enabled:
            return result

        for item in items:
            if item.zone < self._config.min_zone_for_decay:
                continue

            if self._adaptive:
                decay_days = self._adaptive.effective_decay_days(item)
                forget_days = self._adaptive.effective_forget_days(item)
            else:
                decay_days = self._config.decay_days
                forget_days = self._config.auto_forget_days

            decay_threshold = current_time - (decay_days * SECONDS_PER_DAY)
            forget_threshold = current_time - (forget_days * SECONDS_PER_DAY)

            if item.zone == 4 and item.last_recalled_at < forget_threshold:
                result.to_forget.append(item.id)
            elif item.last_recalled_at < decay_threshold:
                result.to_demote.append((item.id, item.zone, item.zone + 1))

        return result
```

#### 2.4.4 New Events

```python
# event_bus.py EVENTS addition:
"on_adaptive_decay",   # (item, effective_days, actual_elapsed_days)
```

---

### F5: Graph Analytics

#### 2.5.1 Config

```python
# config.py addition

@dataclass
class GraphAnalyticsConfig:
    enabled: bool = True
    community_min_size: int = 2  # minimum nodes for a community
```

Add to StellarConfig:
```python
graph_analytics: GraphAnalyticsConfig = field(default_factory=GraphAnalyticsConfig)
```

#### 2.5.2 GraphAnalyzer

```python
# graph_analyzer.py

from dataclasses import dataclass, field

@dataclass
class GraphStats:
    total_nodes: int = 0
    total_edges: int = 0
    avg_degree: float = 0.0
    density: float = 0.0
    connected_components: int = 0

@dataclass
class CentralityResult:
    item_id: str
    degree: int
    score: float  # normalized degree centrality

class GraphAnalyzer:
    """Analyzes memory graph structure and patterns."""

    def __init__(self, graph, config: GraphAnalyticsConfig):
        """
        Args:
            graph: MemoryGraph or PersistentMemoryGraph instance
            config: GraphAnalyticsConfig
        """
        self._graph = graph
        self._config = config

    def stats(self) -> GraphStats:
        """Compute graph-level statistics."""
        all_edges = self._get_all_edges()
        nodes = set()
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
        n = len(nodes)
        e = len(all_edges)
        avg_deg = (2 * e / n) if n > 0 else 0.0
        density = (2 * e / (n * (n - 1))) if n > 1 else 0.0
        components = self._count_components(nodes, all_edges)
        return GraphStats(
            total_nodes=n, total_edges=e,
            avg_degree=avg_deg, density=density,
            connected_components=components,
        )

    def centrality(self, top_k: int = 10) -> list[CentralityResult]:
        """Compute degree centrality for all nodes.
        Returns top-k nodes sorted by degree descending."""
        all_edges = self._get_all_edges()
        degree_map: dict[str, int] = defaultdict(int)
        for edge in all_edges:
            degree_map[edge.source_id] += 1
            degree_map[edge.target_id] += 1
        max_degree = max(degree_map.values()) if degree_map else 1
        results = [
            CentralityResult(
                item_id=item_id,
                degree=deg,
                score=deg / max_degree,
            )
            for item_id, deg in degree_map.items()
        ]
        results.sort(key=lambda x: x.degree, reverse=True)
        return results[:top_k]

    def communities(self) -> list[list[str]]:
        """Detect communities using connected components.
        Returns list of communities (each is a list of item IDs)."""
        all_edges = self._get_all_edges()
        nodes = set()
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)

        visited: set[str] = set()
        communities: list[list[str]] = []
        for node in nodes:
            if node in visited:
                continue
            component = self._bfs_component(node, adjacency, visited)
            if len(component) >= self._config.community_min_size:
                communities.append(sorted(component))

        communities.sort(key=len, reverse=True)
        return communities

    def path(self, source_id: str, target_id: str,
             max_depth: int = 10) -> list[str] | None:
        """Find shortest path between two memories using BFS.
        Returns list of IDs from source to target, or None if no path."""
        all_edges = self._get_all_edges()
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in all_edges:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)

        # BFS with parent tracking
        visited = {source_id}
        parent: dict[str, str | None] = {source_id: None}
        queue = [(source_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if current == target_id:
                # Reconstruct path
                path = []
                node = target_id
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return list(reversed(path))
            if depth >= max_depth:
                continue
            for neighbor in adjacency.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append((neighbor, depth + 1))
        return None

    def export_dot(self, memory_getter=None) -> str:
        """Export graph in DOT format for Graphviz visualization.

        Args:
            memory_getter: Optional callable(id) -> MemoryItem for labels
        """
        all_edges = self._get_all_edges()
        lines = ["digraph StellarMemory {"]
        lines.append('  rankdir=LR;')
        nodes = set()
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
        for node_id in sorted(nodes):
            label = node_id[:8]
            if memory_getter:
                item = memory_getter(node_id)
                if item:
                    label = item.content[:30].replace('"', '\\"')
            lines.append(f'  "{node_id[:8]}" [label="{label}"];')
        for edge in all_edges:
            lines.append(
                f'  "{edge.source_id[:8]}" -> "{edge.target_id[:8]}" '
                f'[label="{edge.edge_type}"];'
            )
        lines.append("}")
        return "\n".join(lines)

    def export_graphml(self) -> str:
        """Export graph in GraphML format."""
        all_edges = self._get_all_edges()
        nodes = set()
        for edge in all_edges:
            nodes.add(edge.source_id)
            nodes.add(edge.target_id)
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<graphml xmlns="http://graphml.graphstruct.org/graphml">')
        lines.append('  <graph id="stellar-memory" edgedefault="directed">')
        for node_id in sorted(nodes):
            lines.append(f'    <node id="{node_id}"/>')
        for i, edge in enumerate(all_edges):
            lines.append(
                f'    <edge id="e{i}" source="{edge.source_id}" '
                f'target="{edge.target_id}"/>'
            )
        lines.append('  </graph>')
        lines.append('</graphml>')
        return "\n".join(lines)

    # --- Internal helpers ---

    def _get_all_edges(self) -> list:
        """Get all edges from graph (works with both MemoryGraph and PersistentMemoryGraph)."""
        if hasattr(self._graph, '_edges'):
            # In-memory MemoryGraph
            edges = []
            for edge_list in self._graph._edges.values():
                edges.extend(edge_list)
            return edges
        elif hasattr(self._graph, '_get_conn'):
            # PersistentMemoryGraph
            conn = self._graph._get_conn()
            from stellar_memory.models import MemoryEdge
            cur = conn.execute(
                "SELECT source_id, target_id, edge_type, weight, created_at FROM edges"
            )
            return [
                MemoryEdge(source_id=r[0], target_id=r[1], edge_type=r[2],
                           weight=r[3], created_at=r[4])
                for r in cur.fetchall()
            ]
        return []

    def _count_components(self, nodes, edges) -> int:
        adjacency = defaultdict(set)
        for edge in edges:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
        visited = set()
        count = 0
        for node in nodes:
            if node not in visited:
                self._bfs_component(node, adjacency, visited)
                count += 1
        return count

    def _bfs_component(self, start, adjacency, visited) -> list[str]:
        component = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
        return component
```

#### 2.5.3 StellarMemory Integration

```python
# stellar.py additions

def __init__(self, ...):
    # ... existing init ...
    # Graph Analyzer
    self._analyzer = None
    if self.config.graph_analytics.enabled and self.config.graph.enabled:
        from stellar_memory.graph_analyzer import GraphAnalyzer
        self._analyzer = GraphAnalyzer(self._graph, self.config.graph_analytics)

@property
def analyzer(self) -> GraphAnalyzer | None:
    return self._analyzer

def graph_stats(self) -> GraphStats:
    if self._analyzer is None:
        raise RuntimeError("Graph analytics not enabled")
    return self._analyzer.stats()

def graph_communities(self) -> list[list[str]]:
    if self._analyzer is None:
        raise RuntimeError("Graph analytics not enabled")
    return self._analyzer.communities()

def graph_centrality(self, top_k: int = 10) -> list[CentralityResult]:
    if self._analyzer is None:
        raise RuntimeError("Graph analytics not enabled")
    return self._analyzer.centrality(top_k)

def graph_path(self, source_id: str, target_id: str) -> list[str] | None:
    if self._analyzer is None:
        raise RuntimeError("Graph analytics not enabled")
    return self._analyzer.path(source_id, target_id)
```

#### 2.5.4 MCP Tool

```python
# mcp_server.py addition

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
```

#### 2.5.5 CLI Commands

```python
# cli.py additions

# graph subparser with sub-subparsers
p_graph = subparsers.add_parser("graph", help="Graph analysis commands")
graph_sub = p_graph.add_subparsers(dest="graph_command")

graph_sub.add_parser("stats", help="Graph statistics")

p_gc = graph_sub.add_parser("communities", help="Detect communities")

p_gcent = graph_sub.add_parser("centrality", help="Node centrality")
p_gcent.add_argument("--top", "-k", type=int, default=10)

p_gpath = graph_sub.add_parser("path", help="Find path between memories")
p_gpath.add_argument("source", help="Source memory ID")
p_gpath.add_argument("target", help="Target memory ID")

p_gexport = graph_sub.add_parser("export", help="Export graph")
p_gexport.add_argument("--format", "-f", choices=["dot", "graphml"], default="dot")
p_gexport.add_argument("--output", "-o", default="-")

# handler
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
```

---

## 3. Models (New/Modified)

```python
# models.py additions

@dataclass
class SummarizationResult:
    original_id: str
    summary_id: str
    summary_text: str
    original_length: int
    summary_length: int
```

---

## 4. __init__.py Exports (v0.6.0)

```python
# New exports for P5
from stellar_memory.config import (
    ...,  # existing
    VectorIndexConfig,
    SummarizationConfig,
    AdaptiveDecayConfig,
    GraphAnalyticsConfig,
)
from stellar_memory.models import (
    ...,  # existing
    SummarizationResult,
)
from stellar_memory.vector_index import VectorIndex, BruteForceIndex, BallTreeIndex, create_vector_index
from stellar_memory.summarizer import MemorySummarizer
from stellar_memory.adaptive_decay import AdaptiveDecayManager
from stellar_memory.graph_analyzer import GraphAnalyzer, GraphStats, CentralityResult
from stellar_memory.providers import ProviderRegistry

__version__ = "0.6.0"
```

---

## 5. Implementation Order (Detailed Steps)

| Step | Feature | Files | Description |
|------|---------|-------|-------------|
| 1 | F1 | `providers/__init__.py` | ProviderRegistry + protocols |
| 2 | F1 | `providers/openai_provider.py` | OpenAI LLM + Embedder |
| 3 | F1 | `providers/ollama_provider.py` | Ollama LLM + Embedder |
| 4 | F1 | `config.py` | EmbedderConfig.provider + LLMConfig.base_url |
| 5 | F1 | `importance_evaluator.py` | ProviderRegistry 연동 |
| 6 | F1 | `embedder.py` | ProviderRegistry 연동 |
| 7 | F2 | `vector_index.py` | VectorIndex + BruteForce + BallTree |
| 8 | F2 | `config.py` | VectorIndexConfig |
| 9 | F2 | `stellar.py` | VectorIndex 연동 (auto_link, store, forget) |
| 10 | F3 | `summarizer.py` | MemorySummarizer |
| 11 | F3 | `config.py` | SummarizationConfig |
| 12 | F3 | `stellar.py` | store() 요약 파이프라인 |
| 13 | F3 | `event_bus.py` | on_summarize 이벤트 |
| 14 | F4 | `adaptive_decay.py` | AdaptiveDecayManager |
| 15 | F4 | `config.py` | AdaptiveDecayConfig, DecayConfig.adaptive |
| 16 | F4 | `decay_manager.py` | Adaptive 연동 |
| 17 | F4 | `event_bus.py` | on_adaptive_decay 이벤트 |
| 18 | F5 | `graph_analyzer.py` | GraphAnalyzer + GraphStats |
| 19 | F5 | `config.py` | GraphAnalyticsConfig |
| 20 | F5 | `stellar.py` | GraphAnalyzer 연동 |
| 21 | F5 | `models.py` | SummarizationResult |
| 22 | All | `mcp_server.py` | memory_summarize + memory_graph_analyze |
| 23 | All | `cli.py` | summarize + graph 서브커맨드 |
| 24 | All | `__init__.py` + `pyproject.toml` | exports + version 0.6.0 |
| 25 | F1 | `tests/test_providers.py` | 10+ tests |
| 26 | F2 | `tests/test_vector_index.py` | 10+ tests |
| 27 | F3 | `tests/test_summarizer.py` | 10+ tests |
| 28 | F4 | `tests/test_adaptive_decay.py` | 8+ tests |
| 29 | F5 | `tests/test_graph_analyzer.py` | 10+ tests |
| 30 | All | Full regression | 237 existing + 50+ new |

---

## 6. Backward Compatibility

| Component | Strategy |
|-----------|----------|
| EmbedderConfig | `provider` defaults to `"sentence-transformers"` (existing behavior) |
| LLMConfig | `base_url` defaults to `None` (existing behavior) |
| VectorIndexConfig | `backend` defaults to `"brute_force"` (same as O(n) scan) |
| SummarizationConfig | `enabled` defaults to `True` but requires LLM; no-op with NullAdapter |
| AdaptiveDecayConfig | `enabled` defaults to `False` (opt-in) |
| DecayConfig.adaptive | New field with default factory (no breaking change) |
| GraphAnalyticsConfig | `enabled` defaults to `True` (new feature, no conflict) |
| store() | New `skip_summarize` param defaults to `False` (backward compatible) |
| All 237 existing tests | Must pass without modification |

---

## 7. Test Strategy

### F1: test_providers.py (10+ tests)
1. `test_registry_register_llm` - register + create
2. `test_registry_register_embedder` - register + create
3. `test_anthropic_provider_registered` - default registration
4. `test_openai_provider_not_installed` - graceful fallback
5. `test_ollama_provider_not_installed` - graceful fallback
6. `test_create_evaluator_with_openai` - evaluator uses registry
7. `test_create_embedder_with_provider` - embedder uses registry
8. `test_null_provider_fallback` - NullProvider when nothing available
9. `test_provider_config_base_url` - base_url passed correctly
10. `test_provider_complete_returns_string` - protocol compliance

### F2: test_vector_index.py (10+ tests)
1. `test_brute_force_add_search` - basic add/search
2. `test_brute_force_remove` - remove from index
3. `test_ball_tree_add_search` - ball tree basic
4. `test_ball_tree_large_dataset` - 1000+ vectors
5. `test_ball_tree_rebuild` - rebuild from scratch
6. `test_ball_tree_accuracy_vs_brute` - results match brute force
7. `test_factory_brute_force` - factory creates correct type
8. `test_factory_ball_tree` - factory creates correct type
9. `test_factory_faiss_fallback` - FAISS not installed → BallTree
10. `test_stellar_auto_link_uses_index` - integration test
11. `test_index_size` - size tracking

### F3: test_summarizer.py (10+ tests)
1. `test_should_summarize_short` - under min_length → False
2. `test_should_summarize_long` - over min_length → True
3. `test_summarize_success` - mock LLM returns summary
4. `test_summarize_failure_returns_none` - LLM error → None
5. `test_summarize_disabled` - config.enabled=False
6. `test_store_with_summary_creates_two` - summary + original items
7. `test_store_with_summary_creates_edge` - derived_from edge
8. `test_store_short_no_summary` - short content stored normally
9. `test_summarize_event_emitted` - on_summarize event fired
10. `test_mcp_memory_summarize` - MCP tool integration
11. `test_cli_summarize` - CLI command integration

### F4: test_adaptive_decay.py (8+ tests)
1. `test_effective_days_high_importance` - importance 0.9 → longer
2. `test_effective_days_low_importance` - importance 0.1 → shorter
3. `test_effective_days_zero_importance` - importance 0.0 → minimum
4. `test_zone_factor_multiplier` - zone-based adjustment
5. `test_decay_curve_linear` - linear curve
6. `test_decay_curve_exponential` - exponential curve
7. `test_decay_curve_sigmoid` - sigmoid curve
8. `test_adaptive_integrated` - StellarMemory with adaptive decay
9. `test_adaptive_disabled_same_as_before` - backward compat

### F5: test_graph_analyzer.py (10+ tests)
1. `test_stats_empty_graph` - no edges → zero stats
2. `test_stats_with_edges` - correct node/edge count
3. `test_centrality_top_k` - returns correct top nodes
4. `test_communities_detection` - finds connected components
5. `test_communities_min_size` - filters small communities
6. `test_path_exists` - finds shortest path
7. `test_path_not_exists` - returns None
8. `test_path_direct` - direct connection
9. `test_export_dot` - valid DOT output
10. `test_export_graphml` - valid GraphML output
11. `test_stellar_integration` - via memory.analyzer

---

## 8. Performance Targets

| Metric | Current (v0.5.0) | Target (v0.6.0) |
|--------|:-----------------:|:----------------:|
| auto_link (1K memories) | ~50ms (O(n)) | ~5ms (O(log n)) |
| auto_link (10K memories) | ~500ms (O(n)) | ~50ms (O(log n)) |
| recall top-10 (10K) | ~100ms | ~50ms |
| store with summary | N/A | < 2s (LLM latency) |
| graph communities (1K nodes) | N/A | < 100ms |
| adaptive decay check (10K items) | ~1ms | ~2ms (minimal overhead) |
