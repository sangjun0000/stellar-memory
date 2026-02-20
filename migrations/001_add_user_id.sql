-- Migration 001: Add user_id to memories table for multi-tenancy
-- Date: 2026-02-20
-- Feature: saas-multitenant

-- Step 1: Add user_id column (nullable for backward compatibility)
ALTER TABLE memories ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Step 2: Composite indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_memories_user_zone
    ON memories(user_id, zone);
CREATE INDEX IF NOT EXISTS idx_memories_user_score
    ON memories(user_id, total_score DESC);
CREATE INDEX IF NOT EXISTS idx_memories_user_recalled
    ON memories(user_id, last_recalled_at DESC);

-- Step 3: RLS policy (defense in depth)
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
CREATE POLICY memories_tenant_isolation ON memories
    FOR ALL
    USING (
        user_id = current_setting('app.current_user_id', true)::uuid
        OR user_id IS NULL
    );

-- Step 4: Rename 'team' tier to 'promax'
UPDATE users SET tier = 'promax' WHERE tier = 'team';
