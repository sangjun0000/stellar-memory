"""Tests for StellarBuilder (v3.0 SDK)."""

import pytest

from stellar_memory.builder import StellarBuilder, Preset


class TestPresets:
    def test_minimal_creates_3_zones(self):
        builder = StellarBuilder(Preset.MINIMAL)
        config = builder._config
        assert len(config.zones) == 3
        assert not config.graph.enabled
        assert not config.emotion.enabled

    def test_chat_enables_session_and_emotion(self):
        builder = StellarBuilder(Preset.CHAT)
        config = builder._config
        assert config.session.enabled
        assert config.emotion.enabled
        assert not config.graph.enabled

    def test_agent_enables_full_intelligence(self):
        builder = StellarBuilder(Preset.AGENT)
        config = builder._config
        assert config.session.enabled
        assert config.emotion.enabled
        assert config.graph.enabled
        assert config.reasoning.enabled
        assert config.metacognition.enabled
        assert config.self_learning.enabled

    def test_knowledge_enables_graph_consolidation(self):
        builder = StellarBuilder(Preset.KNOWLEDGE)
        config = builder._config
        assert config.graph.enabled
        assert config.consolidation.enabled
        assert config.summarization.enabled
        assert not config.reasoning.enabled

    def test_research_enables_vector_index(self):
        builder = StellarBuilder(Preset.RESEARCH)
        config = builder._config
        assert config.vector_index.enabled
        assert not config.graph.enabled


class TestFluentAPI:
    def test_with_sqlite_sets_path(self):
        builder = StellarBuilder().with_sqlite("/tmp/test.db")
        assert builder._config.db_path == "/tmp/test.db"

    def test_with_memory_sets_memory_mode(self):
        builder = StellarBuilder().with_memory()
        assert builder._config.db_path == ":memory:"

    def test_with_embeddings_enables(self):
        builder = StellarBuilder().with_embeddings()
        assert builder._config.embedder.enabled
        assert builder._config.embedder.provider == "sentence-transformers"

    def test_with_embeddings_custom_provider(self):
        builder = StellarBuilder().with_embeddings(provider="openai", model="text-embedding-3-small")
        assert builder._config.embedder.provider == "openai"
        assert builder._config.embedder.model_name == "text-embedding-3-small"

    def test_with_llm_enables(self):
        builder = StellarBuilder().with_llm()
        assert builder._config.llm.enabled
        assert builder._config.llm.provider == "anthropic"

    def test_with_emotions_enables(self):
        builder = StellarBuilder().with_emotions()
        assert builder._config.emotion.enabled

    def test_with_graph_enables(self):
        builder = StellarBuilder().with_graph()
        assert builder._config.graph.enabled
        assert builder._config.graph.auto_link

    def test_with_graph_custom_threshold(self):
        builder = StellarBuilder().with_graph(threshold=0.5)
        assert builder._config.graph.auto_link_threshold == 0.5

    def test_with_reasoning_enables(self):
        builder = StellarBuilder().with_reasoning()
        assert builder._config.reasoning.enabled

    def test_with_metacognition_enables(self):
        builder = StellarBuilder().with_metacognition()
        assert builder._config.metacognition.enabled

    def test_with_self_learning_enables(self):
        builder = StellarBuilder().with_self_learning()
        assert builder._config.self_learning.enabled

    def test_with_namespace(self):
        builder = StellarBuilder().with_namespace("test-ns")
        assert builder._namespace == "test-ns"

    def test_with_decay_sets_parameters(self):
        builder = StellarBuilder().with_decay(rate=0.01, decay_days=14)
        assert builder._config.memory_function.decay_alpha == 0.01
        assert builder._config.decay.decay_days == 14

    def test_with_zones_sets_capacities(self):
        builder = StellarBuilder().with_zones(core=10, inner=50)
        assert builder._config.zones[0].max_slots == 10
        assert builder._config.zones[1].max_slots == 50

    def test_chaining_returns_self(self):
        builder = StellarBuilder()
        result = (
            builder
            .with_sqlite(":memory:")
            .with_emotions()
            .with_graph()
        )
        assert result is builder


class TestBuild:
    def test_minimal_build(self):
        """StellarBuilder().with_memory().build() creates working instance."""
        memory = StellarBuilder().with_memory().build()
        assert memory is not None
        assert memory.config is not None
        memory.stop()

    def test_three_line_init(self):
        """The 3-line init from the SDK vision works."""
        memory = StellarBuilder(Preset.MINIMAL).with_memory().build()
        assert memory is not None
        memory.stop()

    def test_build_with_plugin(self):
        from stellar_memory.plugin import MemoryPlugin

        class TestPlugin(MemoryPlugin):
            name = "test"
            init_called = False
            def on_init(self, memory):
                TestPlugin.init_called = True

        plugin = TestPlugin()
        memory = StellarBuilder().with_memory().with_plugin(plugin).build()
        assert TestPlugin.init_called
        memory.stop()


class TestFromDict:
    def test_from_dict_basic(self):
        data = {
            "preset": "minimal",
            "db_path": ":memory:",
        }
        builder = StellarBuilder.from_dict(data)
        assert builder._config.db_path == ":memory:"
        assert builder._preset == Preset.MINIMAL

    def test_from_dict_with_features(self):
        data = {
            "preset": "minimal",
            "db_path": ":memory:",
            "emotions": True,
            "graph": {"auto_link": True, "threshold": 0.6},
        }
        builder = StellarBuilder.from_dict(data)
        assert builder._config.emotion.enabled
        assert builder._config.graph.enabled
        assert builder._config.graph.auto_link_threshold == 0.6

    def test_from_dict_invalid_preset_defaults_to_minimal(self):
        data = {"preset": "nonexistent"}
        builder = StellarBuilder.from_dict(data)
        assert builder._preset == Preset.MINIMAL
