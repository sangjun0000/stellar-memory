"""AES-256-GCM encryption for sensitive memories."""

from __future__ import annotations

import base64
import logging
import os

logger = logging.getLogger(__name__)

_NONCE_SIZE = 12
_TAG_SIZE = 16


class EncryptionManager:
    """Encrypts / decrypts memory content with AES-256-GCM."""

    def __init__(self, key: bytes | None = None,
                 key_env: str = "STELLAR_ENCRYPTION_KEY"):
        self._key: bytes | None = None
        if key:
            self._key = self._normalize_key(key)
        else:
            env_val = os.environ.get(key_env)
            if env_val:
                self._key = self._normalize_key(env_val.encode())
        if self._key is None:
            logger.warning(
                "No encryption key provided – EncryptionManager disabled."
            )

    @property
    def enabled(self) -> bool:
        return self._key is not None

    # ------------------------------------------------------------------
    def encrypt(self, plaintext: str) -> str:
        """Return base64-encoded  nonce || ciphertext || tag."""
        if not self._key:
            raise RuntimeError("Encryption key not set")
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ImportError(
                "cryptography is required for encryption. "
                "Install with: pip install stellar-memory[security]"
            )
        nonce = os.urandom(_NONCE_SIZE)
        aes = AESGCM(self._key)
        ct = aes.encrypt(nonce, plaintext.encode(), None)
        # ct already includes the 16-byte tag appended by AESGCM
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, token: str) -> str:
        """Decode base64 token and decrypt."""
        if not self._key:
            raise RuntimeError("Encryption key not set")
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ImportError(
                "cryptography is required for encryption. "
                "Install with: pip install stellar-memory[security]"
            )
        raw = base64.b64decode(token)
        nonce = raw[:_NONCE_SIZE]
        ct = raw[_NONCE_SIZE:]
        aes = AESGCM(self._key)
        return aes.decrypt(nonce, ct, None).decode()

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_key(raw: bytes) -> bytes:
        """Ensure the key is exactly 32 bytes (AES-256)."""
        if len(raw) == 32:
            return raw
        if len(raw) > 32:
            return raw[:32]
        return raw.ljust(32, b"\x00")

    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 32-byte key."""
        return os.urandom(32)
