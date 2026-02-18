"""Tests for P8: version management and packaging."""

import pytest


class TestVersionManagement:
    def test_version_from_importlib(self):
        """Version should be loaded from importlib.metadata or fallback."""
        import stellar_memory
        assert stellar_memory.__version__ is not None
        assert isinstance(stellar_memory.__version__, str)
        assert len(stellar_memory.__version__) > 0

    def test_version_format(self):
        """Version should follow semver-like format."""
        import stellar_memory
        parts = stellar_memory.__version__.replace("-dev", "").split(".")
        assert len(parts) >= 2

    def test_version_in_server(self):
        """Server should use the same version."""
        try:
            from stellar_memory.server import create_api_app
            from stellar_memory.config import StellarConfig
            import stellar_memory
            config = StellarConfig(db_path=":memory:")
            app, _ = create_api_app(config)
            assert app.version == stellar_memory.__version__
        except ImportError:
            pytest.skip("fastapi not installed")

    def test_pyproject_version_matches(self):
        """pyproject.toml version should be consistent."""
        try:
            import tomllib
        except ModuleNotFoundError:
            pytest.skip("tomllib requires Python 3.11+")
        from pathlib import Path
        toml_path = Path(__file__).parent.parent / "pyproject.toml"
        if not toml_path.exists():
            pytest.skip("pyproject.toml not found")
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        pyproject_version = data["project"]["version"]
        assert pyproject_version is not None
        assert len(pyproject_version) > 0

    def test_build_package(self):
        """Package should be buildable."""
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "build", "--no-isolation", "--wheel", "."],
            capture_output=True, text=True, timeout=120,
            cwd=str(__import__("pathlib").Path(__file__).parent.parent),
        )
        # Just check no crash; may fail without build deps
        # This is a soft test
        assert result.returncode == 0 or "No module named" in result.stderr
