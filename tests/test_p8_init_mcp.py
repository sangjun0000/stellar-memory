"""Tests for P8: init-mcp CLI command."""

import json
import os
import tempfile

import pytest

from stellar_memory.cli import main, _merge_mcp_config, _claude_config_path, _cursor_config_path


class TestInitMCP:
    def test_dry_run_outputs_json(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "init-mcp", "--dry-run"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "mcpServers" in data
        assert "stellar-memory" in data["mcpServers"]

    def test_dry_run_has_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "init-mcp", "--dry-run"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        server = data["mcpServers"]["stellar-memory"]
        assert server["command"] == "stellar-memory"
        assert "serve" in server["args"]

    def test_dry_run_has_db_path(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "init-mcp", "--dry-run", "--db-path", "/custom/path.db"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        env = data["mcpServers"]["stellar-memory"]["env"]
        assert "STELLAR_DB_PATH" in env


class TestMergeConfig:
    def test_merge_creates_new_file(self, tmp_path):
        config_path = str(tmp_path / "mcp.json")
        new_config = {
            "mcpServers": {
                "stellar-memory": {"command": "stellar-memory"}
            }
        }
        _merge_mcp_config(config_path, new_config)
        with open(config_path) as f:
            data = json.load(f)
        assert "stellar-memory" in data["mcpServers"]

    def test_merge_preserves_existing(self, tmp_path):
        config_path = str(tmp_path / "mcp.json")
        # Write existing config
        existing = {
            "mcpServers": {
                "other-server": {"command": "other"}
            }
        }
        with open(config_path, "w") as f:
            json.dump(existing, f)

        # Merge new config
        new_config = {
            "mcpServers": {
                "stellar-memory": {"command": "stellar-memory"}
            }
        }
        _merge_mcp_config(config_path, new_config)

        with open(config_path) as f:
            data = json.load(f)
        assert "other-server" in data["mcpServers"]
        assert "stellar-memory" in data["mcpServers"]

    def test_merge_updates_existing_server(self, tmp_path):
        config_path = str(tmp_path / "mcp.json")
        existing = {
            "mcpServers": {
                "stellar-memory": {"command": "old-command"}
            }
        }
        with open(config_path, "w") as f:
            json.dump(existing, f)

        new_config = {
            "mcpServers": {
                "stellar-memory": {"command": "stellar-memory", "args": ["serve"]}
            }
        }
        _merge_mcp_config(config_path, new_config)

        with open(config_path) as f:
            data = json.load(f)
        assert data["mcpServers"]["stellar-memory"]["command"] == "stellar-memory"
        assert "args" in data["mcpServers"]["stellar-memory"]

    def test_merge_creates_parent_dirs(self, tmp_path):
        config_path = str(tmp_path / "deep" / "nested" / "mcp.json")
        new_config = {
            "mcpServers": {"test": {"command": "test"}}
        }
        _merge_mcp_config(config_path, new_config)
        assert os.path.exists(config_path)


class TestConfigPaths:
    def test_claude_config_path_returns_string(self):
        path = _claude_config_path()
        assert isinstance(path, str)
        assert "claude" in path.lower() or "Claude" in path

    def test_cursor_config_path_returns_string(self):
        path = _cursor_config_path()
        assert isinstance(path, str)
        assert "cursor" in path.lower() or ".cursor" in path

    def test_claude_config_path_ends_with_json(self):
        path = _claude_config_path()
        assert path.endswith(".json")

    def test_cursor_config_path_ends_with_json(self):
        path = _cursor_config_path()
        assert path.endswith(".json")
