"""Tests for P6 security module: encryption, RBAC, audit."""

import os
import tempfile
import pytest

try:
    import cryptography
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

from stellar_memory.security.encryption import EncryptionManager
from stellar_memory.security.access_control import AccessControl, DEFAULT_ROLES
from stellar_memory.security.audit import SecurityAudit
from stellar_memory.config import SecurityConfig


# ---------- EncryptionManager ----------

class TestEncryptionManager:
    def test_disabled_without_key(self):
        mgr = EncryptionManager(key=None, key_env="NONEXISTENT_KEY_12345")
        assert not mgr.enabled

    def test_enabled_with_key(self):
        key = EncryptionManager.generate_key()
        mgr = EncryptionManager(key=key)
        assert mgr.enabled

    @pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography not installed")
    def test_encrypt_decrypt_roundtrip(self):
        key = EncryptionManager.generate_key()
        mgr = EncryptionManager(key=key)
        plaintext = "This is a secret memory about the universe."
        encrypted = mgr.encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = mgr.decrypt(encrypted)
        assert decrypted == plaintext

    @pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography not installed")
    def test_different_nonces(self):
        key = EncryptionManager.generate_key()
        mgr = EncryptionManager(key=key)
        e1 = mgr.encrypt("same text")
        e2 = mgr.encrypt("same text")
        assert e1 != e2  # different nonces

    @pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography not installed")
    def test_decrypt_wrong_key_fails(self):
        key1 = EncryptionManager.generate_key()
        key2 = EncryptionManager.generate_key()
        mgr1 = EncryptionManager(key=key1)
        mgr2 = EncryptionManager(key=key2)
        encrypted = mgr1.encrypt("secret")
        with pytest.raises(Exception):
            mgr2.decrypt(encrypted)

    def test_encrypt_raises_if_no_key(self):
        mgr = EncryptionManager(key=None, key_env="NONEXISTENT_12345")
        with pytest.raises(RuntimeError, match="key not set"):
            mgr.encrypt("hello")

    def test_decrypt_raises_if_no_key(self):
        mgr = EncryptionManager(key=None, key_env="NONEXISTENT_12345")
        with pytest.raises(RuntimeError, match="key not set"):
            mgr.decrypt("dummytoken")

    def test_key_from_env(self):
        key = EncryptionManager.generate_key()
        os.environ["TEST_STELLAR_KEY"] = key.decode("latin-1")
        try:
            mgr = EncryptionManager(key_env="TEST_STELLAR_KEY")
            assert mgr.enabled
        finally:
            del os.environ["TEST_STELLAR_KEY"]

    def test_normalize_short_key(self):
        short = b"shortkey"
        normalized = EncryptionManager._normalize_key(short)
        assert len(normalized) == 32

    def test_normalize_long_key(self):
        long_key = b"a" * 64
        normalized = EncryptionManager._normalize_key(long_key)
        assert len(normalized) == 32

    def test_generate_key(self):
        key = EncryptionManager.generate_key()
        assert len(key) == 32
        assert isinstance(key, bytes)

    @pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography not installed")
    def test_unicode_content(self):
        key = EncryptionManager.generate_key()
        mgr = EncryptionManager(key=key)
        text = "한국어 테스트 메모리 암호화 🌟"
        encrypted = mgr.encrypt(text)
        assert mgr.decrypt(encrypted) == text

    @pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography not installed")
    def test_empty_string(self):
        key = EncryptionManager.generate_key()
        mgr = EncryptionManager(key=key)
        encrypted = mgr.encrypt("")
        assert mgr.decrypt(encrypted) == ""

    @pytest.mark.skipif(not HAS_CRYPTOGRAPHY, reason="cryptography not installed")
    def test_large_content(self):
        key = EncryptionManager.generate_key()
        mgr = EncryptionManager(key=key)
        text = "x" * 100_000
        encrypted = mgr.encrypt(text)
        assert mgr.decrypt(encrypted) == text


# ---------- AccessControl ----------

class TestAccessControl:
    def test_default_roles(self):
        ac = AccessControl()
        roles = ac.list_roles()
        assert "admin" in roles
        assert "writer" in roles
        assert "reader" in roles
        assert "write" in roles["admin"]
        assert "write" not in roles["reader"]

    def test_default_role_is_writer(self):
        ac = AccessControl()
        assert ac.get_role("unknown_user") == "writer"

    def test_assign_and_check(self):
        ac = AccessControl()
        ac.assign_role("alice", "admin")
        assert ac.get_role("alice") == "admin"
        assert ac.check_permission("alice", "manage_roles")
        assert ac.check_permission("alice", "read")

    def test_reader_cannot_write(self):
        ac = AccessControl()
        ac.assign_role("bob", "reader")
        assert ac.check_permission("bob", "read")
        assert not ac.check_permission("bob", "write")

    def test_require_permission_raises(self):
        ac = AccessControl()
        ac.assign_role("bob", "reader")
        with pytest.raises(PermissionError):
            ac.require_permission("bob", "write")

    def test_require_permission_passes(self):
        ac = AccessControl()
        ac.assign_role("admin_user", "admin")
        ac.require_permission("admin_user", "delete")

    def test_assign_unknown_role_raises(self):
        ac = AccessControl()
        with pytest.raises(ValueError, match="Unknown role"):
            ac.assign_role("user", "superadmin")

    def test_custom_config(self):
        cfg = SecurityConfig(
            enabled=True,
            default_role="reader",
            roles={"viewer": ["read"]},
        )
        ac = AccessControl(cfg)
        assert ac.get_role("anyone") == "reader"
        assert "viewer" in ac.list_roles()

    def test_add_role(self):
        ac = AccessControl()
        ac.add_role("editor", ["read", "write"])
        ac.assign_role("ed", "editor")
        assert ac.check_permission("ed", "write")
        assert not ac.check_permission("ed", "delete")


# ---------- SecurityAudit ----------

class TestSecurityAudit:
    def test_log_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            audit = SecurityAudit(log_path=path)
            audit.log("test_event", user_id="u1", item_id="m1")
            entries = audit.get_entries()
            assert len(entries) == 1
            assert entries[0]["event"] == "test_event"
            assert entries[0]["user"] == "u1"
        finally:
            os.unlink(path)

    def test_log_access(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            audit = SecurityAudit(log_path=path)
            audit.log_access("alice", "mem-1", "read")
            entries = audit.get_entries()
            assert entries[0]["event"] == "access"
            assert entries[0]["details"] == "read"
        finally:
            os.unlink(path)

    def test_log_encrypt_decrypt(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            audit = SecurityAudit(log_path=path)
            audit.log_encrypt("mem-1")
            audit.log_decrypt("mem-1")
            entries = audit.get_entries()
            assert len(entries) == 2
            assert entries[0]["event"] == "encrypt"
            assert entries[1]["event"] == "decrypt"
        finally:
            os.unlink(path)

    def test_disabled(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            audit = SecurityAudit(log_path=path, enabled=False)
            audit.log("should_not_appear")
            entries = audit.get_entries()
            assert len(entries) == 0
        finally:
            os.unlink(path)

    def test_permission_denied_log(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            audit = SecurityAudit(log_path=path)
            audit.log_permission_denied("bob", "delete")
            entries = audit.get_entries()
            assert entries[0]["event"] == "permission_denied"
        finally:
            os.unlink(path)

    def test_get_entries_limit(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            audit = SecurityAudit(log_path=path)
            for i in range(20):
                audit.log(f"event_{i}")
            entries = audit.get_entries(limit=5)
            assert len(entries) == 5
            assert entries[0]["event"] == "event_15"
        finally:
            os.unlink(path)

    def test_attach_to_event_bus(self):
        """SecurityAudit.attach() registers event bus listeners."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            from stellar_memory.event_bus import EventBus
            bus = EventBus()
            audit = SecurityAudit(log_path=path)
            audit.attach(bus)
            # Verify listeners registered (on_store, on_forget, on_recall)
            assert len(bus._handlers.get("on_store", [])) >= 1
            assert len(bus._handlers.get("on_forget", [])) >= 1
            assert len(bus._handlers.get("on_recall", [])) >= 1
        finally:
            os.unlink(path)


class TestAccessControlDomainPermissions:
    """Test store/recall/forget domain-specific permission names."""

    def test_admin_has_store_recall_forget(self):
        ac = AccessControl()
        ac.assign_role("admin_user", "admin")
        assert ac.check_permission("admin_user", "store")
        assert ac.check_permission("admin_user", "recall")
        assert ac.check_permission("admin_user", "forget")

    def test_writer_has_store_recall_forget(self):
        ac = AccessControl()
        ac.assign_role("writer_user", "writer")
        assert ac.check_permission("writer_user", "store")
        assert ac.check_permission("writer_user", "recall")
        assert ac.check_permission("writer_user", "forget")

    def test_reader_has_recall_only(self):
        ac = AccessControl()
        ac.assign_role("reader_user", "reader")
        assert ac.check_permission("reader_user", "recall")
        assert not ac.check_permission("reader_user", "store")
        assert not ac.check_permission("reader_user", "forget")
