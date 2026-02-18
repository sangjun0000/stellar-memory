"""Role-based access control for Stellar Memory."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stellar_memory.config import SecurityConfig

logger = logging.getLogger(__name__)

# Default role definitions
# Includes both generic (read/write/delete) and domain-specific
# (store/recall/forget) permission names for compatibility.
DEFAULT_ROLES: dict[str, list[str]] = {
    "admin": ["read", "write", "delete", "encrypt", "manage_roles", "audit",
              "store", "recall", "forget"],
    "writer": ["read", "write", "delete", "encrypt", "store", "recall", "forget"],
    "reader": ["read", "recall"],
}


class AccessControl:
    """RBAC access control for memory operations."""

    def __init__(self, config: SecurityConfig | None = None):
        self._roles: dict[str, list[str]] = dict(DEFAULT_ROLES)
        self._user_roles: dict[str, str] = {}  # user_id -> role_name
        self._default_role = "writer"
        if config:
            self._default_role = config.default_role
            if config.roles:
                self._roles.update(config.roles)

    def assign_role(self, user_id: str, role: str) -> None:
        if role not in self._roles:
            raise ValueError(f"Unknown role: {role}")
        self._user_roles[user_id] = role

    def get_role(self, user_id: str) -> str:
        return self._user_roles.get(user_id, self._default_role)

    def check_permission(self, user_id: str, permission: str) -> bool:
        role = self.get_role(user_id)
        return permission in self._roles.get(role, [])

    def require_permission(self, user_id: str, permission: str) -> None:
        if not self.check_permission(user_id, permission):
            raise PermissionError(
                f"User '{user_id}' (role={self.get_role(user_id)}) "
                f"lacks permission '{permission}'"
            )

    def list_roles(self) -> dict[str, list[str]]:
        return dict(self._roles)

    def add_role(self, name: str, permissions: list[str]) -> None:
        self._roles[name] = list(permissions)
