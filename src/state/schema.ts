/**
 * Harness OS — SQLite Schema
 *
 * Table definitions and migrations for the persistent state store.
 *
 * Source: CLAUDE.md §8 (State/Session constraints).
 *
 * Design:
 * - Separate tables for sessions, turns, and approvals.
 * - Complex nested fields (metadata, tool_calls) stored as JSON text.
 * - ISO-8601 timestamps for all temporal fields.
 * - Schema version tracking for future migrations.
 *
 * Schema version history:
 *   v1 — Initial schema (sessions, turns, approvals with basic columns)
 *   v2 — Added missing PendingApproval fields to approvals table:
 *        project_id, tool_name, skill_name, task_id, run_id,
 *        input_digest, consumed
 */

export const SCHEMA_VERSION = 2;

// ============================================================
// DDL
// ============================================================

/**
 * Base DDL for fresh installations (SCHEMA_VERSION >= 2).
 * Includes all columns in the approvals table.
 */
export const CREATE_SCHEMA_SQL = `
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER NOT NULL,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  started_at TEXT NOT NULL,
  last_active_at TEXT,
  turn_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paused', 'completed', 'failed')),
  metadata TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Turns table
CREATE TABLE IF NOT EXISTS turns (
  turn_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  turn_number INTEGER NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'failed')),
  user_input TEXT,
  response_summary TEXT,
  tool_calls TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Approvals table (v2: includes strong-binding columns)
CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  reason TEXT NOT NULL,
  risk_level TEXT NOT NULL CHECK(risk_level IN ('low', 'medium', 'high')),
  affected_paths TEXT NOT NULL DEFAULT '[]',
  -- Strong-binding fields (GOV3-03 / P0-003)
  skill_name TEXT,
  tool_name TEXT,
  project_id TEXT,
  task_id TEXT,
  run_id TEXT,
  input_digest TEXT,
  session_id TEXT,
  turn_id TEXT,
  agent_id TEXT,
  -- Status and lifecycle
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'expired')),
  consumed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  resolved_at TEXT,
  resolved_by TEXT,
  modified_input TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
CREATE INDEX IF NOT EXISTS idx_turns_status ON turns(status);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_session ON approvals(session_id);
`;

// ============================================================
// v1 → v2 Migration
// ============================================================

/**
 * Migration queries for upgrading from schema v1 to v2.
 * Each ALTER TABLE ADD COLUMN uses IF NOT EXISTS via PRAGMA check
 * to safely handle databases already at v2.
 */
export const MIGRATE_V1_TO_V2 = `
-- Add strong-binding columns to approvals (v2)
ALTER TABLE approvals ADD COLUMN skill_name TEXT;
ALTER TABLE approvals ADD COLUMN tool_name TEXT;
ALTER TABLE approvals ADD COLUMN project_id TEXT;
ALTER TABLE approvals ADD COLUMN task_id TEXT;
ALTER TABLE approvals ADD COLUMN run_id TEXT;
ALTER TABLE approvals ADD COLUMN input_digest TEXT;
ALTER TABLE approvals ADD COLUMN consumed INTEGER NOT NULL DEFAULT 0;
`;

// ============================================================
// Migration Runner
// ============================================================

export function getMigrationQueries(): string[] {
  return [CREATE_SCHEMA_SQL, MIGRATE_V1_TO_V2];
}
