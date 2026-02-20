"""Database schema and operations for billing/auth.

Uses raw SQL with asyncpg for simplicity (no SQLAlchemy ORM dependency).
"""

from __future__ import annotations

# SQL schema for PostgreSQL (Neon-compatible)
SCHEMA_SQL = """
-- users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(20) NOT NULL DEFAULT 'free',
    provider VARCHAR(20),
    provider_customer_id VARCHAR(255),
    provider_subscription_id VARCHAR(255),
    billing_key VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100) DEFAULT 'Default',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- subscription_events table
CREATE TABLE IF NOT EXISTS subscription_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    provider VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    amount_cents INTEGER,
    currency VARCHAR(3) DEFAULT 'USD',
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_subscription_events_user ON subscription_events(user_id);
"""

# Individual table creation for environments that need piecemeal setup
USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(20) NOT NULL DEFAULT 'free',
    provider VARCHAR(20),
    provider_customer_id VARCHAR(255),
    provider_subscription_id VARCHAR(255),
    billing_key VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

API_KEYS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100) DEFAULT 'Default',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

SUBSCRIPTION_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS subscription_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    provider VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    tier VARCHAR(20) NOT NULL,
    amount_cents INTEGER,
    currency VARCHAR(3) DEFAULT 'USD',
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""
