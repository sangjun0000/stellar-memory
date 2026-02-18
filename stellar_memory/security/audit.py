"""Security audit logging for Stellar Memory."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityAudit:
    """Append-only audit log for security-relevant events."""

    def __init__(self, log_path: str = "stellar_audit.jsonl",
                 enabled: bool = True):
        self._log_path = Path(log_path)
        self._enabled = enabled

    def attach(self, event_bus) -> None:
        """Attach to an EventBus to log security-relevant events."""
        event_bus.on("on_store", lambda item: self.log(
            "store", item_id=item.id,
            details=f"encrypted={item.encrypted}"))
        event_bus.on("on_forget", lambda item_id: self.log(
            "forget", item_id=item_id))
        event_bus.on("on_recall", lambda items, query: self.log(
            "recall", details=f"query={query[:50]}, results={len(items)}"))

    def log(self, event_type: str, user_id: str = "",
            item_id: str = "", details: str = "") -> None:
        if not self._enabled:
            return
        entry = {
            "ts": time.time(),
            "event": event_type,
            "user": user_id,
            "item": item_id,
            "details": details,
        }
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning("Audit log write failed: %s", e)

    def log_access(self, user_id: str, item_id: str,
                   action: str) -> None:
        self.log("access", user_id=user_id, item_id=item_id,
                 details=action)

    def log_encrypt(self, item_id: str) -> None:
        self.log("encrypt", item_id=item_id)

    def log_decrypt(self, item_id: str) -> None:
        self.log("decrypt", item_id=item_id)

    def log_permission_denied(self, user_id: str,
                              permission: str) -> None:
        self.log("permission_denied", user_id=user_id,
                 details=permission)

    def get_entries(self, limit: int = 100) -> list[dict]:
        """Read last N audit entries."""
        if not self._log_path.exists():
            return []
        entries: list[dict] = []
        try:
            with open(self._log_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except Exception:
            pass
        return entries[-limit:]
