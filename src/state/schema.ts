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
 */

export const SCHEMA_VERSION = 1;

// ============================================================
// DDL
// ============================================================

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

-- Approvals table
CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  reason TEXT NOT NULL,
  risk_level TEXT NOT NULL CHECK(risk_level IN ('low', 'medium', 'high')),
  affected_paths TEXT NOT NULL DEFAULT '[]',
  session_id TEXT,
  turn_id TEXT,
  agent_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'expired')),
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
// Migration Runner
// ============================================================

export function getMigrationQueries(): string[] {
  return [CREATE_SCHEMA_SQL];
}
