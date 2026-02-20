"""Tier-based usage limits configuration."""

from __future__ import annotations

TIER_LIMITS: dict[str, dict] = {
    "free": {
        "max_memories": -1,   # unlimited
        "max_agents": -1,     # unlimited
        "rate_limit": 120,    # per minute (server protection only)
        "max_api_keys": -1,   # unlimited
    },
    "pro": {
        "max_memories": -1,
        "max_agents": -1,
        "rate_limit": 120,
        "max_api_keys": -1,
    },
    "promax": {
        "max_memories": -1,
        "max_agents": -1,
        "rate_limit": 120,
        "max_api_keys": -1,
    },
}

# Tier ordering for upgrade suggestions
_TIER_ORDER = ["free", "pro", "promax"]


def get_tier_limits(tier: str) -> dict:
    """Get limits for a given tier. Defaults to free if unknown."""
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


def next_tier(current: str) -> str | None:
    """Return the next upgrade tier, or None if already at top."""
    try:
        idx = _TIER_ORDER.index(current)
        if idx + 1 < len(_TIER_ORDER):
            return _TIER_ORDER[idx + 1]
    except ValueError:
        pass
    return None
