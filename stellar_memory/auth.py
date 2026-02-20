"""User authentication and API key management."""

from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "sk-stellar-"


@dataclass
class UserInfo:
    id: str
    email: str
    tier: str


def generate_api_key() -> str:
    """Generate a new API key: sk-stellar-{32 hex chars}."""
    return f"{API_KEY_PREFIX}{secrets.token_hex(16)}"


def hash_api_key(key: str) -> str:
    """SHA-256 hash of an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def key_prefix(key: str) -> str:
    """Extract display prefix: sk-stellar-a1b2..."""
    return key[:16] + "..."


class AuthManager:
    """Manages users and API keys via asyncpg connection pool."""

    def __init__(self, pool):
        self._pool = pool

    async def init_schema(self):
        """Create tables if they don't exist."""
        from stellar_memory.billing.db_models import SCHEMA_SQL

        async with self._pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)

    async def register_user(self, email: str) -> tuple[dict, str]:
        """Register a new user and generate their first API key.

        Returns (user_dict, raw_api_key). The raw key is shown only once.
        """
        async with self._pool.acquire() as conn:
            # Check if user already exists
            existing = await conn.fetchrow(
                "SELECT id, tier FROM users WHERE email = $1", email
            )
            if existing:
                # User exists - generate new key for them
                user_id = str(existing["id"])
                tier = existing["tier"]
            else:
                # Create new user
                row = await conn.fetchrow(
                    "INSERT INTO users (email) VALUES ($1) RETURNING id, tier",
                    email,
                )
                user_id = str(row["id"])
                tier = row["tier"]

            # Generate API key
            raw_key = generate_api_key()
            k_hash = hash_api_key(raw_key)
            k_prefix = key_prefix(raw_key)

            await conn.execute(
                """INSERT INTO api_keys (user_id, key_hash, key_prefix, name)
                   VALUES ($1, $2, $3, $4)""",
                user_id,
                k_hash,
                k_prefix,
                "Default",
            )

            return {
                "user_id": user_id,
                "email": email,
                "tier": tier,
            }, raw_key

    async def get_user_by_api_key(self, key_hash: str) -> UserInfo | None:
        """Look up user by hashed API key."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT u.id, u.email, u.tier
                   FROM users u
                   JOIN api_keys ak ON ak.user_id = u.id
                   WHERE ak.key_hash = $1 AND ak.is_active = TRUE""",
                key_hash,
            )
            if row:
                # Update last_used_at
                await conn.execute(
                    "UPDATE api_keys SET last_used_at = NOW() WHERE key_hash = $1",
                    key_hash,
                )
                return UserInfo(
                    id=str(row["id"]),
                    email=row["email"],
                    tier=row["tier"],
                )
        return None

    async def list_api_keys(self, user_id: str) -> list[dict]:
        """List all API keys for a user (prefix only, no raw keys)."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, key_prefix, name, is_active, last_used_at, created_at
                   FROM api_keys WHERE user_id = $1 ORDER BY created_at DESC""",
                user_id,
            )
            return [
                {
                    "id": str(r["id"]),
                    "prefix": r["key_prefix"],
                    "name": r["name"],
                    "is_active": r["is_active"],
                    "last_used_at": r["last_used_at"].isoformat()
                    if r["last_used_at"]
                    else None,
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows
            ]

    async def create_api_key(self, user_id: str, name: str = "Unnamed") -> tuple[dict, str]:
        """Create a new API key for a user. Returns (key_info, raw_key)."""
        from stellar_memory.billing.tiers import get_tier_limits

        async with self._pool.acquire() as conn:
            # Check key count limit
            user = await conn.fetchrow(
                "SELECT tier FROM users WHERE id = $1", user_id
            )
            if not user:
                raise ValueError("User not found")

            limits = get_tier_limits(user["tier"])
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM api_keys WHERE user_id = $1 AND is_active = TRUE",
                user_id,
            )
            if count >= limits["max_api_keys"]:
                raise ValueError(
                    f"API key limit reached ({count}/{limits['max_api_keys']})"
                )

            raw_key = generate_api_key()
            k_hash = hash_api_key(raw_key)
            k_prefix = key_prefix(raw_key)

            row = await conn.fetchrow(
                """INSERT INTO api_keys (user_id, key_hash, key_prefix, name)
                   VALUES ($1, $2, $3, $4) RETURNING id, created_at""",
                user_id,
                k_hash,
                k_prefix,
                name,
            )
            return {
                "id": str(row["id"]),
                "prefix": k_prefix,
                "name": name,
                "created_at": row["created_at"].isoformat(),
            }, raw_key

    async def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """Deactivate an API key."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """UPDATE api_keys SET is_active = FALSE
                   WHERE id = $1 AND user_id = $2 AND is_active = TRUE""",
                key_id,
                user_id,
            )
            return result == "UPDATE 1"

    async def get_user_by_email(self, email: str) -> UserInfo | None:
        """Look up user by email."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, email, tier FROM users WHERE email = $1", email
            )
            if row:
                return UserInfo(
                    id=str(row["id"]),
                    email=row["email"],
                    tier=row["tier"],
                )
        return None

    async def update_user_tier(
        self,
        email: str,
        tier: str,
        provider: str | None = None,
        provider_customer_id: str | None = None,
        provider_subscription_id: str | None = None,
    ) -> UserInfo | None:
        """Update a user's subscription tier."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """UPDATE users SET
                     tier = $2,
                     provider = COALESCE($3, provider),
                     provider_customer_id = COALESCE($4, provider_customer_id),
                     provider_subscription_id = COALESCE($5, provider_subscription_id),
                     updated_at = NOW()
                   WHERE email = $1
                   RETURNING id, email, tier""",
                email,
                tier,
                provider,
                provider_customer_id,
                provider_subscription_id,
            )
            if row:
                return UserInfo(
                    id=str(row["id"]),
                    email=row["email"],
                    tier=row["tier"],
                )
        return None

    async def get_or_create_user(
        self, email: str, provider: str | None = None
    ) -> UserInfo:
        """Get existing user or create a new one."""
        user = await self.get_user_by_email(email)
        if user:
            return user
        info, _ = await self.register_user(email)
        if provider:
            await self.update_user_tier(email, "free", provider=provider)
        return UserInfo(id=info["user_id"], email=email, tier="free")

    async def get_memory_count(self, user_id: str) -> int:
        """Get memory count for a user (from memories table)."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                """SELECT COUNT(*) FROM information_schema.tables
                   WHERE table_name = 'memories'""",
            )
            if count:
                return await conn.fetchval(
                    "SELECT COUNT(*) FROM memories WHERE user_id = $1::uuid",
                    user_id,
                ) or 0
        return 0

    async def log_subscription_event(
        self,
        user_id: str,
        provider: str,
        event_type: str,
        tier: str,
        amount_cents: int | None = None,
        currency: str = "USD",
        raw_data: dict | None = None,
    ):
        """Log a subscription event."""
        import json

        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO subscription_events
                   (user_id, provider, event_type, tier, amount_cents, currency, raw_data)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                user_id,
                provider,
                event_type,
                tier,
                amount_cents,
                currency,
                json.dumps(raw_data) if raw_data else None,
            )
