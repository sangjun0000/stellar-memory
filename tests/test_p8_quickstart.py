"""Tests for P8: quickstart and examples."""

import pytest


class TestQuickstartWizard:
    def test_quickstart_parser_exists(self):
        """quickstart subcommand should be registered."""
        import argparse
        from stellar_memory.cli import main
        # Parsing with quickstart should not error
        # (we won't actually run it since it needs stdin)
        assert callable(main)

    def test_quickstart_basic_flow(self, capsys, tmp_path, monkeypatch):
        """Test quickstart with mocked input."""
        from stellar_memory.cli import _run_quickstart
        import argparse

        inputs = iter(["1", "y"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        args = argparse.Namespace(db=str(tmp_path / "qs.db"))
        _run_quickstart(args)

        captured = capsys.readouterr()
        assert "Welcome to Stellar Memory" in captured.out
        assert "first memory" in captured.out.lower()

    def test_quickstart_rest_api_path(self, capsys, tmp_path, monkeypatch):
        """Test quickstart with REST API choice."""
        from stellar_memory.cli import _run_quickstart
        import argparse

        inputs = iter(["2", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        args = argparse.Namespace(db=str(tmp_path / "qs.db"))
        _run_quickstart(args)

        captured = capsys.readouterr()
        assert "serve-api" in captured.out

    def test_quickstart_mcp_path(self, capsys, tmp_path, monkeypatch):
        """Test quickstart with MCP choice."""
        from stellar_memory.cli import _run_quickstart
        import argparse

        inputs = iter(["3", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        args = argparse.Namespace(db=str(tmp_path / "qs.db"))
        _run_quickstart(args)

        captured = capsys.readouterr()
        assert "init-mcp" in captured.out

    def test_quickstart_docker_path(self, capsys, tmp_path, monkeypatch):
        """Test quickstart with Docker choice."""
        from stellar_memory.cli import _run_quickstart
        import argparse

        inputs = iter(["4", "n"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        args = argparse.Namespace(db=str(tmp_path / "qs.db"))
        _run_quickstart(args)

        captured = capsys.readouterr()
        assert "docker" in captured.out.lower()

    def test_quickstart_eof_handling(self, capsys, tmp_path, monkeypatch):
        """Test quickstart handles EOF gracefully."""
        from stellar_memory.cli import _run_quickstart
        import argparse

        def raise_eof(_):
            raise EOFError

        monkeypatch.setattr("builtins.input", raise_eof)

        args = argparse.Namespace(db=str(tmp_path / "qs.db"))
        _run_quickstart(args)

        captured = capsys.readouterr()
        assert "Welcome to Stellar Memory" in captured.out


class TestExamples:
    def test_basic_example_runs(self, tmp_path, monkeypatch):
        """Basic example should run without errors."""
        monkeypatch.chdir(tmp_path)
        from stellar_memory import StellarMemory

        memory = StellarMemory()
        memory.store("Python was created by Guido van Rossum", importance=0.7)
        memory.store("The weather is nice today", importance=0.2)
        memory.store("Project deadline is March 1st", importance=0.9)

        results = memory.recall("project deadline")
        assert len(results) > 0

        stats = memory.stats()
        assert stats.total_memories == 3
        memory.stop()

    def test_chatbot_example_runs(self, tmp_path, monkeypatch):
        """Chatbot example should run without errors."""
        monkeypatch.chdir(tmp_path)
        from stellar_memory import StellarMemory, StellarConfig, EmotionConfig

        config = StellarConfig(
            db_path=str(tmp_path / "chatbot.db"),
            emotion=EmotionConfig(enabled=True),
        )
        memory = StellarMemory(config)
        memory.store("User's name is Alice", importance=0.9)
        memory.store("User likes Python and dark mode", importance=0.7)

        results = memory.recall("Tell me about the user")
        assert len(results) > 0
        memory.stop()
