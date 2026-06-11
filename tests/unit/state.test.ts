/**
 * Harness OS — State Module Tests
 *
 * Coverage:
 * - SqliteStore: create/open/close
 * - Session CRUD: create, get, update, list, delete
 * - Turn CRUD: create, get, update, list by session
 * - Approval CRUD: create, get, update, list
 * - Data integrity: JSON field round-trip, cascade delete
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { type SessionId, type TurnId } from '../../src/types.js';
import { type PendingApproval } from '../../src/governance/approval-gate.js';

// We import dynamically because SqliteStore depends on better-sqlite3
// which must be loaded after the temp DB path is determined.

describe('SqliteStore', () => {
  let dbDir: string;
  let dbPath: string;

  beforeEach(() => {
    dbDir = mkdtempSync(join(tmpdir(), 'harness-state-test-'));
    dbPath = join(dbDir, 'test.db');
  });

  afterEach(() => {
    rmSync(dbDir, { recursive: true, force: true });
  });

  async function createStore() {
    const { SqliteStore } = await import('../../src/state/store.js');
    return new SqliteStore({ dbPath, walMode: false });
  }

  // ============================================================
  // Session CRUD
  // ============================================================

  describe('sessions', () => {
    it('creates and retrieves a session', async () => {
      const store = await createStore();
      store.createSession({
        session_id: 'ses_test_001' as SessionId,
        project_id: 'test-proj',
        started_at: '2025-01-01T00:00:00.000Z',
        last_active_at: '2025-01-01T00:00:00.000Z',
        turn_count: 0,
        status: 'active',
        metadata: { env: 'test' },
      });

      const retrieved = store.getSession('ses_test_001' as SessionId);
      expect(retrieved).toBeDefined();
      expect(retrieved!.session_id).toBe('ses_test_001');
      expect(retrieved!.project_id).toBe('test-proj');
      expect(retrieved!.status).toBe('active');
      expect(retrieved!.turn_count).toBe(0);
      expect(retrieved!.metadata).toEqual({ env: 'test' });
      store.close();
    });

    it('returns undefined for non-existent session', async () => {
      const store = await createStore();
      const result = store.getSession('ses_nonexistent' as SessionId);
      expect(result).toBeUndefined();
      store.close();
    });

    it('updates a session', async () => {
      const store = await createStore();
      store.createSession({
        session_id: 'ses_test_001' as SessionId,
        project_id: 'test-proj',
        started_at: '2025-01-01T00:00:00.000Z',
        turn_count: 0,
        status: 'active',
        metadata: {},
      });

      store.updateSession('ses_test_001' as SessionId, {
        status: 'completed',
        turn_count: 5,
      });

      const updated = store.getSession('ses_test_001' as SessionId);
      expect(updated!.status).toBe('completed');
      expect(updated!.turn_count).toBe(5);
      store.close();
    });

    it('lists active sessions', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });
      store.createSession({ session_id: 'ses_2' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });
      store.createSession({ session_id: 'ses_3' as SessionId, project_id: 'p2', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'completed', metadata: {} });

      const active = store.listActiveSessions();
      expect(active).toHaveLength(2);
      expect(active.map(s => s.session_id).sort()).toEqual(['ses_1', 'ses_2']);
      store.close();
    });

    it('lists sessions by project', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });
      store.createSession({ session_id: 'ses_2' as SessionId, project_id: 'p1', started_at: '2025-01-02T00:00:00.000Z', turn_count: 0, status: 'completed', metadata: {} });
      store.createSession({ session_id: 'ses_3' as SessionId, project_id: 'p2', started_at: '2025-01-03T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });

      const p1Sessions = store.listSessionsByProject('p1');
      expect(p1Sessions).toHaveLength(2);
      store.close();
    });

    it('deletes a session', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_test' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });

      const deleted = store.deleteSession('ses_test' as SessionId);
      expect(deleted).toBe(true);

      const retrieved = store.getSession('ses_test' as SessionId);
      expect(retrieved).toBeUndefined();
      store.close();
    });

    it('returns false deleting non-existent session', async () => {
      const store = await createStore();
      const result = store.deleteSession('ses_nonexist' as SessionId);
      expect(result).toBe(false);
      store.close();
    });
  });

  // ============================================================
  // Turn CRUD
  // ============================================================

  describe('turns', () => {
    it('creates and retrieves a turn', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });

      store.createTurn({
        turn_id: 'trn_1' as TurnId,
        session_id: 'ses_1' as SessionId,
        turn_number: 1,
        started_at: '2025-01-01T00:00:00.000Z',
        status: 'completed',
        user_input: 'hello',
        response_summary: 'world',
        tool_calls: [],
      });

      const turn = store.getTurn('trn_1' as TurnId);
      expect(turn).toBeDefined();
      expect(turn!.turn_number).toBe(1);
      expect(turn!.user_input).toBe('hello');
      expect(turn!.response_summary).toBe('world');
      expect(turn!.tool_calls).toEqual([]);
      store.close();
    });

    it('stores and retrieves tool_calls as JSON', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });

      const toolCalls = [
        { tool_name: 'Read', tool_input: { file_path: 'test.ts' }, permission_decision: 'allow', reason: 'ok', session_id: 'ses_1', turn_id: 'trn_1', agent_id: 'agent', tool_use_id: 'tui_1', timestamp: '2025-01-01T00:00:00.000Z' },
        { tool_name: 'Glob', tool_input: { pattern: '*.ts' }, permission_decision: 'allow', reason: 'ok', session_id: 'ses_1', turn_id: 'trn_1', agent_id: 'agent', tool_use_id: 'tui_2', timestamp: '2025-01-01T00:00:00.000Z' },
      ];

      store.createTurn({
        turn_id: 'trn_1' as TurnId,
        session_id: 'ses_1' as SessionId,
        turn_number: 1,
        started_at: '2025-01-01T00:00:00.000Z',
        status: 'active',
        tool_calls: toolCalls,
      });

      const turn = store.getTurn('trn_1' as TurnId);
      expect(turn!.tool_calls).toHaveLength(2);
      expect(turn!.tool_calls[0].tool_name).toBe('Read');
      store.close();
    });

    it('updates a turn', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });
      store.createTurn({ turn_id: 'trn_1' as TurnId, session_id: 'ses_1' as SessionId, turn_number: 1, started_at: '2025-01-01T00:00:00.000Z', status: 'active', tool_calls: [] });

      store.updateTurn('trn_1' as TurnId, {
        status: 'completed',
        response_summary: 'done',
      });

      const turn = store.getTurn('trn_1' as TurnId);
      expect(turn!.status).toBe('completed');
      expect(turn!.response_summary).toBe('done');
      store.close();
    });

    it('lists turns by session ordered by turn_number', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });

      store.createTurn({ turn_id: 'trn_1' as TurnId, session_id: 'ses_1' as SessionId, turn_number: 1, started_at: '2025-01-01T00:00:00.000Z', status: 'completed', tool_calls: [] });
      store.createTurn({ turn_id: 'trn_2' as TurnId, session_id: 'ses_1' as SessionId, turn_number: 2, started_at: '2025-01-02T00:00:00.000Z', status: 'completed', tool_calls: [] });
      store.createTurn({ turn_id: 'trn_3' as TurnId, session_id: 'ses_1' as SessionId, turn_number: 3, started_at: '2025-01-03T00:00:00.000Z', status: 'active', tool_calls: [] });

      const turns = store.listTurnsBySession('ses_1' as SessionId);
      expect(turns).toHaveLength(3);
      expect(turns.map(t => t.turn_number)).toEqual([1, 2, 3]);
      store.close();
    });

    it('deletes turns by session', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });
      store.createTurn({ turn_id: 'trn_1' as TurnId, session_id: 'ses_1' as SessionId, turn_number: 1, started_at: '2025-01-01T00:00:00.000Z', status: 'completed', tool_calls: [] });
      store.createTurn({ turn_id: 'trn_2' as TurnId, session_id: 'ses_1' as SessionId, turn_number: 2, started_at: '2025-01-02T00:00:00.000Z', status: 'completed', tool_calls: [] });

      const count = store.deleteTurnsBySession('ses_1' as SessionId);
      expect(count).toBe(2);

      const turns = store.listTurnsBySession('ses_1' as SessionId);
      expect(turns).toHaveLength(0);
      store.close();
    });
  });

  // ============================================================
  // Approval CRUD
  // ============================================================

  describe('approvals', () => {
    it('creates and retrieves an approval', async () => {
      const store = await createStore();
      store.createApproval({
        id: 'app_001',
        action: 'Bash',
        reason: 'High-risk command',
        riskLevel: 'high',
        affectedPaths: [],
        status: 'pending',
        createdAt: '2025-01-01T00:00:00.000Z',
        expiresAt: '2025-01-02T00:00:00.000Z',
      });

      const approval = store.getApproval('app_001');
      expect(approval).toBeDefined();
      expect(approval!.action).toBe('Bash');
      expect(approval!.riskLevel).toBe('high');
      expect(approval!.status).toBe('pending');
      store.close();
    });

    it('updates an approval status', async () => {
      const store = await createStore();
      store.createApproval({
        id: 'app_001', action: 'Bash', reason: 'test', riskLevel: 'high',
        affectedPaths: [], status: 'pending',
        createdAt: '2025-01-01T00:00:00.000Z', expiresAt: '2025-01-02T00:00:00.000Z',
      });

      store.updateApproval('app_001', {
        status: 'approved',
        resolvedBy: 'operator',
        resolvedAt: '2025-01-01T01:00:00.000Z',
      });

      const approval = store.getApproval('app_001');
      expect(approval!.status).toBe('approved');
      expect(approval!.resolvedBy).toBe('operator');
      store.close();
    });

    it('lists pending approvals', async () => {
      const store = await createStore();
      // Create 2 pending (not expired) + 1 resolved
      store.createApproval({ id: 'app_1', action: 'Bash', reason: 'test', riskLevel: 'high', affectedPaths: [], status: 'pending', createdAt: '2025-01-01T00:00:00.000Z', expiresAt: '2099-01-01T00:00:00.000Z' });
      store.createApproval({ id: 'app_2', action: 'Write', reason: 'test', riskLevel: 'medium', affectedPaths: [], status: 'pending', createdAt: '2025-01-01T00:00:00.000Z', expiresAt: '2099-01-01T00:00:00.000Z' });
      store.createApproval({ id: 'app_3', action: 'Bash', reason: 'test', riskLevel: 'high', affectedPaths: [], status: 'approved', createdAt: '2025-01-01T00:00:00.000Z', expiresAt: '2099-01-01T00:00:00.000Z', resolvedAt: '2025-01-01T01:00:00.000Z', resolvedBy: 'op' });

      const pending = store.listPendingApprovals();
      expect(pending).toHaveLength(2);
      store.close();
    });

    it('deletes an approval', async () => {
      const store = await createStore();
      store.createApproval({
        id: 'app_001', action: 'Bash', reason: 'test', riskLevel: 'high',
        affectedPaths: [], status: 'pending',
        createdAt: '2025-01-01T00:00:00.000Z', expiresAt: '2025-01-02T00:00:00.000Z',
      });

      const deleted = store.deleteApproval('app_001');
      expect(deleted).toBe(true);
      expect(store.getApproval('app_001')).toBeUndefined();
      store.close();
    });
  });

  // ============================================================
  // Maintenance
  // ============================================================

  describe('maintenance', () => {
    it('returns stats', async () => {
      const store = await createStore();
      store.createSession({ session_id: 'ses_1' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });
      store.createSession({ session_id: 'ses_2' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 0, status: 'active', metadata: {} });

      const stats = store.getStats();
      expect(stats.sessions).toBe(2);
      expect(stats.turns).toBe(0);
      expect(stats.approvals).toBe(0);
      expect(stats.dbPath).toContain('test.db');
      store.close();
    });

    it('vacuum does not throw', async () => {
      const store = await createStore();
      expect(() => store.vacuum()).not.toThrow();
      store.close();
    });

    it('persists data across close/reopen', async () => {
      // Write
      const store1 = await createStore();
      store1.createSession({ session_id: 'ses_persist' as SessionId, project_id: 'p1', started_at: '2025-01-01T00:00:00.000Z', turn_count: 42, status: 'active', metadata: { key: 'val' } });
      store1.close();

      // Read with new store instance
      const store2 = await createStore();
      const session = store2.getSession('ses_persist' as SessionId);
      expect(session).toBeDefined();
      expect(session!.turn_count).toBe(42);
      expect(session!.metadata).toEqual({ key: 'val' });
      store2.close();
    });
  });
});
