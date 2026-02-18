"""Tests for NamespaceManager and StellarMemory namespace support."""

import os
import tempfile

import pytest

from stellar_memory.namespace import NamespaceManager
from stellar_memory.config import StellarConfig, NamespaceConfig
from stellar_memory.stellar import StellarMemory


class TestNamespaceManager:
    def test_get_db_path_creates_directory(self, tmp_path):
        mgr = NamespaceManager(str(tmp_path / "data"))
        path = mgr.get_db_path("project-a")
        assert path.endswith("memory.db")
        assert os.path.isdir(os.path.dirname(path))

    def test_list_namespaces_empty(self, tmp_path):
        mgr = NamespaceManager(str(tmp_path / "data"))
        assert mgr.list_namespaces() == []

    def test_list_namespaces_with_data(self, tmp_path):
        mgr = NamespaceManager(str(tmp_path / "data"))
        # Create namespace by getting db path and creating db file
        path = mgr.get_db_path("ns1")
        with open(path, "w") as f:
            f.write("")
        path2 = mgr.get_db_path("ns2")
        with open(path2, "w") as f:
            f.write("")
        namespaces = mgr.list_namespaces()
        assert sorted(namespaces) == ["ns1", "ns2"]

    def test_delete_namespace(self, tmp_path):
        mgr = NamespaceManager(str(tmp_path / "data"))
        mgr.get_db_path("to-delete")
        assert mgr.delete_namespace("to-delete") is True
        assert not os.path.exists(tmp_path / "data" / "to-delete")

    def test_delete_nonexistent_namespace(self, tmp_path):
        mgr = NamespaceManager(str(tmp_path / "data"))
        assert mgr.delete_namespace("nonexistent") is False

    def test_sanitize_special_characters(self, tmp_path):
        mgr = NamespaceManager(str(tmp_path / "data"))
        assert mgr._sanitize("my project!@#") == "my_project___"
        assert mgr._sanitize("safe-name_123") == "safe-name_123"

    def test_stellar_memory_with_namespace(self, tmp_path):
        config = StellarConfig(
            namespace=NamespaceConfig(enabled=True, base_path=str(tmp_path / "data"))
        )
        mem = StellarMemory(config, namespace="test-ns")
        item = mem.store("namespaced content")
        assert item.id is not None
        found = mem.get(item.id)
        assert found is not None
        assert found.content == "namespaced content"

    def test_separate_namespaces_are_isolated(self, tmp_path):
        ns_config = NamespaceConfig(enabled=True, base_path=str(tmp_path / "data"))
        config1 = StellarConfig(namespace=ns_config)
        config2 = StellarConfig(namespace=ns_config)
        mem1 = StellarMemory(config1, namespace="ns-a")
        mem2 = StellarMemory(config2, namespace="ns-b")

        item = mem1.store("only in ns-a")
        assert mem1.get(item.id) is not None
        assert mem2.get(item.id) is None
