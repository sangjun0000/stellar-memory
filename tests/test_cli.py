"""Tests for CLI tool."""

import json
import os
import tempfile

import pytest

from stellar_memory.cli import main


class TestCLI:
    def test_store_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "hello world"])
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "id" in result
        assert "zone" in result

    def test_recall_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "python programming"])
        main(["--db", db, "recall", "python"])
        captured = capsys.readouterr()
        assert "python" in captured.out.lower()

    def test_stats_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "stats test"])
        main(["--db", db, "stats"])
        captured = capsys.readouterr()
        assert "Total memories" in captured.out

    def test_export_stdout(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "export test"])
        main(["--db", db, "export"])
        captured = capsys.readouterr()
        # Last output should be valid JSON
        lines = captured.out.strip().split("\n")
        # Find the JSON part (after the store output)
        json_part = "\n".join(lines[1:])
        parsed = json.loads(json_part)
        assert "items" in parsed

    def test_export_to_file(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        out_file = str(tmp_path / "out.json")
        main(["--db", db, "store", "export file test"])
        main(["--db", db, "export", "--output", out_file])
        assert os.path.exists(out_file)
        with open(out_file) as f:
            parsed = json.loads(f.read())
        assert "items" in parsed

    def test_import_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "import source"])
        main(["--db", db, "export", "--output", str(tmp_path / "data.json")])
        # Import into a new db
        db2 = str(tmp_path / "test2.db")
        main(["--db", db2, "import", str(tmp_path / "data.json")])
        captured = capsys.readouterr()
        assert "Imported" in captured.out

    def test_forget_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "to forget"])
        captured = capsys.readouterr()
        result = json.loads(captured.out.strip().split("\n")[0])
        item_id = result["id"]
        main(["--db", db, "forget", item_id])
        captured = capsys.readouterr()
        assert "Removed" in captured.out

    def test_reorbit_command(self, capsys, tmp_path):
        db = str(tmp_path / "test.db")
        main(["--db", db, "store", "reorbit test"])
        main(["--db", db, "reorbit"])
        captured = capsys.readouterr()
        assert "Moved:" in captured.out
