/**
 * Harness OS — SQLite State Store
 *
 * Persistent storage for sessions, turns, and approvals using better-sqlite3.
 *
 * Source: CLAUDE.md §8 (State/Session constraints).
 *
 * Design:
 * - better-sqlite3 synchronous API for simplicity.
 * - Store file at configurable path (default: .harness/state.db).
 * - Each method mirrors the in-memory stores from runtime/session.ts and
 *   governance/approval-gate.ts for easy swap-in.
 * - Complex fields stored as JSON text.
 *
 * State write requirements (§8):
 *   1. Clear schema — enforced by table DDL
 *   2. Clear scope — each table has owned scope
 *   3. Clear actor — session_id/agent_id fields
 *   4. Clear reason — reason/description fields
 *   5. Clear trace id — session_id/turn_id fields
 */

import Database from 'better-sqlite3';
import type { SessionId, SessionState, TurnState, TurnId } from '../types.js';
import type { PendingApproval } from '../governance/approval-gate.js';
import { CREATE_SCHEMA_SQL, SCHEMA_VERSION } from './schema.js';
import { existsSync, mkdirSync } from 'fs';
import { dirname, resolve } from 'path';

// ============================================================
// Types
// ============================================================

export interface StoreConfig {
  /** Path to the SQLite database file. */
  dbPath: string;
  /** If true, enables WAL mode for better concurrency. */
  walMode?: boolean;
}

// ============================================================
// Default Path
// ============================================================

const DEFAULT_STATE_DIR = '.harness';

function defaultDbPath(): string {
  return resolve(process.cwd(), DEFAULT_STATE_DIR, 'state.db');
}

// ============================================================
// SqliteStore
// ============================================================

export class SqliteStore {
  private db: Database.Database;
  private dbPath: string;

  constructor(config?: Partial<StoreConfig>) {
    this.dbPath = config?.dbPath ?? defaultDbPath();

    // Ensure directory exists
    const dir = dirname(this.dbPath);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }

    this.db = new Database(this.dbPath);

    // Enable WAL mode if requested
    if (config?.walMode ?? true) {
      this.db.pragma('journal_mode = WAL');
    }

    // Enable foreign keys
    this.db.pragma('foreign_keys = ON');

    // Run schema migration
    this.migrate();
  }

  /**
   * Close the database connection.
   */
  close(): void {
    this.db.close();
  }

  /**
   * Get the underlying database instance for advanced operations.
   */
  get rawDb(): Database.Database {
    return this.db;
  }

  // ================================================================
  // Schema Migration
  // ================================================================

  private migrate(): void {
    // Run base schema DDL (CREATE TABLE IF NOT EXISTS)
    this.db.exec(CREATE_SCHEMA_SQL);

    // Check current schema version
    const row = this.db.prepare('SELECT MAX(version) as version FROM schema_version').get() as
      | { version: number | null }
      | undefined;
    const currentVersion = row?.version ?? 0;

    if (currentVersion < SCHEMA_VERSION) {
      // Run migration queries for each version gap
      if (currentVersion <= 1 && SCHEMA_VERSION >= 2) {
        // v1 → v2: add columns. ALTER TABLE ADD COLUMN may fail on
        // re-run if columns already exist; we catch and ignore those.
        try {
          this.db.exec('ALTER TABLE approvals ADD COLUMN skill_name TEXT');
        } catch {
          // column may already exist — safe to ignore
        }
        try {
          this.db.exec('ALTER TABLE approvals ADD COLUMN tool_name TEXT');
        } catch {
          // ignore
        }
        try {
          this.db.exec('ALTER TABLE approvals ADD COLUMN project_id TEXT');
        } catch {
          // ignore
        }
        try {
          this.db.exec('ALTER TABLE approvals ADD COLUMN task_id TEXT');
        } catch {
          // ignore
        }
        try {
          this.db.exec('ALTER TABLE approvals ADD COLUMN run_id TEXT');
        } catch {
          // ignore
        }
        try {
          this.db.exec('ALTER TABLE approvals ADD COLUMN input_digest TEXT');
        } catch {
          // ignore
        }
        try {
          this.db.exec('ALTER TABLE approvals ADD COLUMN consumed INTEGER NOT NULL DEFAULT 0');
        } catch {
          // ignore
        }
      }

      this.db.prepare('INSERT INTO schema_version (version) VALUES (?)').run(SCHEMA_VERSION);
    }
  }

  // ================================================================
  // Session Operations
  // ================================================================

  /**
   * Insert a new session.
   */
  createSession(session: SessionState): void {
    this.db
      .prepare(
        `
      INSERT INTO sessions (session_id, project_id, started_at, last_active_at, turn_count, status, metadata)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `,
      )
      .run(
        session.session_id,
        session.project_id,
        session.started_at,
        session.last_active_at ?? null,
        session.turn_count,
        session.status,
        JSON.stringify(session.metadata),
      );
  }

  /**
   * Get a session by ID.
   */
  getSession(id: SessionId): SessionState | undefined {
    const row = this.db.prepare('SELECT * FROM sessions WHERE session_id = ?').get(id) as
      | Record<string, unknown>
      | undefined;
    if (!row) return undefined;
    return this.rowToSession(row);
  }

  /**
   * Update a session.
   */
  updateSession(id: SessionId, updates: Partial<SessionState>): SessionState | undefined {
    const existing = this.getSession(id);
    if (!existing) return undefined;

    const merged = { ...existing, ...updates, session_id: id };

    this.db
      .prepare(
        `
      UPDATE sessions SET
        project_id = ?, last_active_at = ?, turn_count = ?,
        status = ?, metadata = ?, updated_at = datetime('now')
      WHERE session_id = ?
    `,
      )
      .run(
        merged.project_id,
        merged.last_active_at ?? null,
        merged.turn_count,
        merged.status,
        JSON.stringify(merged.metadata),
        id,
      );

    return merged;
  }

  /**
   * List all active sessions.
   */
  listActiveSessions(): SessionState[] {
    const rows = this.db
      .prepare("SELECT * FROM sessions WHERE status = 'active' ORDER BY started_at ASC")
      .all() as Record<string, unknown>[];
    return rows.map((r) => this.rowToSession(r));
  }

  /**
   * List sessions by project.
   */
  listSessionsByProject(projectId: string): SessionState[] {
    const rows = this.db
      .prepare('SELECT * FROM sessions WHERE project_id = ? ORDER BY started_at DESC')
      .all(projectId) as Record<string, unknown>[];
    return rows.map((r) => this.rowToSession(r));
  }

  /**
   * Delete a session and its turns (cascade).
   */
  deleteSession(id: SessionId): boolean {
    const result = this.db.prepare('DELETE FROM sessions WHERE session_id = ?').run(id);
    return result.changes > 0;
  }

  // ================================================================
  // Turn Operations
  // ================================================================

  /**
   * Insert a new turn.
   */
  createTurn(turn: TurnState): void {
    this.db
      .prepare(
        `
      INSERT INTO turns (turn_id, session_id, turn_number, started_at, completed_at, status, user_input, response_summary, tool_calls)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `,
      )
      .run(
        turn.turn_id,
        turn.session_id,
        turn.turn_number,
        turn.started_at,
        turn.completed_at ?? null,
        turn.status,
        turn.user_input ?? null,
        turn.response_summary ?? null,
        JSON.stringify(turn.tool_calls),
      );
  }

  /**
   * Get a turn by ID.
   */
  getTurn(id: TurnId): TurnState | undefined {
    const row = this.db.prepare('SELECT * FROM turns WHERE turn_id = ?').get(id) as Record<string, unknown> | undefined;
    if (!row) return undefined;
    return this.rowToTurn(row);
  }

  /**
   * Update a turn.
   */
  updateTurn(id: TurnId, updates: Partial<TurnState>): TurnState | undefined {
    const existing = this.getTurn(id);
    if (!existing) return undefined;

    const merged = { ...existing, ...updates, turn_id: id };

    this.db
      .prepare(
        `
      UPDATE turns SET
        completed_at = ?, status = ?, response_summary = ?,
        tool_calls = ?, updated_at = datetime('now')
      WHERE turn_id = ?
    `,
      )
      .run(
        merged.completed_at ?? null,
        merged.status,
        merged.response_summary ?? null,
        JSON.stringify(merged.tool_calls),
        id,
      );

    return merged;
  }

  /**
   * List turns for a session, ordered by turn number.
   */
  listTurnsBySession(sessionId: SessionId): TurnState[] {
    const rows = this.db
      .prepare('SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number ASC')
      .all(sessionId) as Record<string, unknown>[];
    return rows.map((r) => this.rowToTurn(r));
  }

  /**
   * Delete all turns for a session.
   */
  deleteTurnsBySession(sessionId: SessionId): number {
    const result = this.db.prepare('DELETE FROM turns WHERE session_id = ?').run(sessionId);
    return result.changes;
  }

  // ================================================================
  // Approval Operations
  // ================================================================

  /**
   * Insert a new approval with all PendingApproval fields (v2 schema).
   */
  createApproval(approval: PendingApproval): void {
    this.db
      .prepare(
        `
      INSERT INTO approvals (id, action, reason, risk_level, affected_paths,
        skill_name, tool_name, project_id, task_id, run_id, input_digest,
        session_id, turn_id, agent_id, status, consumed,
        created_at, expires_at, resolved_at, resolved_by, modified_input)
      VALUES (?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?)
    `,
      )
      .run(
        approval.id,
        approval.action,
        approval.reason,
        approval.riskLevel,
        JSON.stringify(approval.affectedPaths),
        approval.skillName ?? null,
        approval.toolName ?? null,
        approval.projectId ?? null,
        approval.taskId ?? null,
        approval.runId ?? null,
        approval.inputDigest ?? null,
        approval.sessionId ?? null,
        approval.turnId ?? null,
        approval.agentId ?? null,
        approval.status,
        approval.consumed ? 1 : 0,
        approval.createdAt,
        approval.expiresAt,
        approval.resolvedAt ?? null,
        approval.resolvedBy ?? null,
        approval.modifiedInput ? JSON.stringify(approval.modifiedInput) : null,
      );
  }

  /**
   * Get an approval by ID.
   */
  getApproval(id: string): PendingApproval | undefined {
    const row = this.db.prepare('SELECT * FROM approvals WHERE id = ?').get(id) as Record<string, unknown> | undefined;
    if (!row) return undefined;
    return this.rowToApproval(row);
  }

  /**
   * Update an approval.
   */
  updateApproval(id: string, updates: Partial<PendingApproval>): PendingApproval | undefined {
    const existing = this.getApproval(id);
    if (!existing) return undefined;

    const merged = { ...existing, ...updates, id };

    this.db
      .prepare(
        `
      UPDATE approvals SET
        status = ?, consumed = ?, resolved_at = ?, resolved_by = ?,
        modified_input = ?, updated_at = datetime('now')
      WHERE id = ?
    `,
      )
      .run(
        merged.status,
        merged.consumed ? 1 : 0,
        merged.resolvedAt ?? null,
        merged.resolvedBy ?? null,
        merged.modifiedInput ? JSON.stringify(merged.modifiedInput) : null,
        id,
      );

    return merged;
  }

  /**
   * Consume an approved approval exactly once.
   * The conditional UPDATE keeps the single-use transition atomic.
   */
  consumeApproval(id: string, now: string): PendingApproval | undefined {
    const result = this.db
      .prepare(
        `
      UPDATE approvals SET
        consumed = 1,
        resolved_at = COALESCE(resolved_at, ?),
        updated_at = datetime('now')
      WHERE id = ?
        AND status = 'approved'
        AND consumed = 0
        AND expires_at > ?
    `,
      )
      .run(now, id, now);

    if (result.changes !== 1) {
      return undefined;
    }

    return this.getApproval(id);
  }

  /**
   * List pending (unexpired) approvals.
   */
  listPendingApprovals(): PendingApproval[] {
    const rows = this.db
      .prepare(
        "SELECT * FROM approvals WHERE status = 'pending' AND expires_at > datetime('now') ORDER BY created_at ASC",
      )
      .all() as Record<string, unknown>[];
    return rows.map((r) => this.rowToApproval(r));
  }

  /**
   * List all approvals.
   */
  listAllApprovals(): PendingApproval[] {
    const rows = this.db.prepare('SELECT * FROM approvals ORDER BY created_at DESC').all() as Record<string, unknown>[];
    return rows.map((r) => this.rowToApproval(r));
  }

  /**
   * Delete all approvals from the store.
   * Used for test isolation (called by __test_clearStore).
   */
  clearAllApprovals(): void {
    this.db.prepare('DELETE FROM approvals').run();
  }

  /**
   * Delete an approval.
   */
  deleteApproval(id: string): boolean {
    const result = this.db.prepare('DELETE FROM approvals WHERE id = ?').run(id);
    return result.changes > 0;
  }

  // ================================================================
  // Maintenance
  // ================================================================

  /**
   * Get database statistics.
   */
  getStats(): Record<string, unknown> {
    const sessionCount = (this.db.prepare('SELECT COUNT(*) as count FROM sessions').get() as { count: number }).count;
    const turnCount = (this.db.prepare('SELECT COUNT(*) as count FROM turns').get() as { count: number }).count;
    const approvalCount = (this.db.prepare('SELECT COUNT(*) as count FROM approvals').get() as { count: number }).count;
    const pendingApprovals = (
      this.db.prepare("SELECT COUNT(*) as count FROM approvals WHERE status = 'pending'").get() as { count: number }
    ).count;

    return {
      dbPath: this.dbPath,
      sessions: sessionCount,
      turns: turnCount,
      approvals: approvalCount,
      pendingApprovals,
      schemaVersion: SCHEMA_VERSION,
    };
  }

  /**
   * Vacuum the database (reclaim space).
   */
  vacuum(): void {
    this.db.exec('VACUUM');
  }

  // ================================================================
  // Row Mappers
  // ================================================================

  private rowToSession(row: Record<string, unknown>): SessionState {
    return {
      session_id: row.session_id as SessionId,
      project_id: row.project_id as string,
      started_at: row.started_at as string,
      last_active_at: (row.last_active_at as string) ?? undefined,
      turn_count: row.turn_count as number,
      status: row.status as SessionState['status'],
      metadata: JSON.parse((row.metadata as string) || '{}'),
    };
  }

  private rowToTurn(row: Record<string, unknown>): TurnState {
    return {
      turn_id: row.turn_id as TurnId,
      session_id: row.session_id as SessionId,
      turn_number: row.turn_number as number,
      started_at: row.started_at as string,
      completed_at: (row.completed_at as string) ?? undefined,
      status: row.status as TurnState['status'],
      user_input: (row.user_input as string) ?? undefined,
      response_summary: (row.response_summary as string) ?? undefined,
      tool_calls: JSON.parse((row.tool_calls as string) || '[]'),
    };
  }

  private rowToApproval(row: Record<string, unknown>): PendingApproval {
    const approval: PendingApproval = {
      id: row.id as string,
      action: row.action as string,
      reason: row.reason as string,
      riskLevel: row.risk_level as PendingApproval['riskLevel'],
      affectedPaths: JSON.parse((row.affected_paths as string) || '[]'),

      // Strong-binding fields (v2)
      skillName: (row.skill_name as string) ?? undefined,
      toolName: (row.tool_name as string) ?? undefined,
      projectId: (row.project_id as string) ?? undefined,
      taskId: (row.task_id as string) ?? undefined,
      runId: (row.run_id as string) ?? undefined,
      inputDigest: (row.input_digest as string) ?? undefined,

      sessionId: (row.session_id as string) ?? undefined,
      turnId: (row.turn_id as string) ?? undefined,
      agentId: (row.agent_id as string) ?? undefined,

      status: row.status as PendingApproval['status'],
      consumed: row.consumed === 1 || row.consumed === true,
      createdAt: row.created_at as string,
      expiresAt: row.expires_at as string,
      resolvedAt: (row.resolved_at as string) ?? undefined,
      resolvedBy: (row.resolved_by as string) ?? undefined,
    };

    if (row.modified_input) {
      approval.modifiedInput = JSON.parse(row.modified_input as string);
    }

    return approval;
  }
}
