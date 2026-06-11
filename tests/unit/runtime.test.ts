/**
 * Harness OS — Runtime Module Tests
 *
 * Coverage:
 * - Session: create, get, end, list
 * - Pipeline: buildPolicyContext, evaluateToolCall (allow/deny/needs_approval)
 * - Orchestrator: startTurn, processToolCall, completeTurn
 * - Hook merge edge cases
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { mergeHookDecisions } from '../../src/types.js';
import { createSession, getSession, endSession, listActiveSessions, __test_clearSessions } from '../../src/runtime/session.js';
import { buildPolicyContext, evaluateToolCall, resolveToolCallApproval, checkApprovalStatus } from '../../src/runtime/pipeline.js';
import { __test_clearStore } from '../../src/governance/approval-gate.js';
import { orchestrateCreateSession, startTurn, processToolCall, completeTurn, orchestrateEndSession, __test_resetRuntime } from '../../src/runtime/orchestrator.js';

// ============================================================
// Session Tests
// ============================================================

describe('session', () => {
  beforeEach(() => {
    __test_clearSessions();
  });

  it('creates a session', () => {
    const session = createSession({ projectId: 'test-proj' });
    expect(session.session_id).toMatch(/^ses_/);
    expect(session.project_id).toBe('test-proj');
    expect(session.status).toBe('active');
    expect(session.turn_count).toBe(0);
    expect(session.started_at).toBeDefined();
  });

  it('gets a session by ID', () => {
    const created = createSession({ projectId: 'test-proj' });
    const retrieved = getSession(created.session_id);
    expect(retrieved).toBeDefined();
    expect(retrieved!.session_id).toBe(created.session_id);
  });

  it('returns undefined for unknown session ID', () => {
    const result = getSession('ses_nonexistent' as any);
    expect(result).toBeUndefined();
  });

  it('ends a session', () => {
    const created = createSession({ projectId: 'test-proj' });
    const ended = endSession(created.session_id);
    expect(ended).toBeDefined();
    expect(ended!.status).toBe('completed');

    const retrieved = getSession(created.session_id);
    expect(retrieved!.status).toBe('completed');
  });

  it('lists only active sessions', () => {
    createSession({ projectId: 'proj-1' });
    createSession({ projectId: 'proj-2' });
    const s3 = createSession({ projectId: 'proj-3' });
    endSession(s3.session_id);

    const active = listActiveSessions();
    expect(active).toHaveLength(2);
    expect(active.every(s => s.status === 'active')).toBe(true);
  });

  it('supports metadata on creation', () => {
    const session = createSession({
      projectId: 'test-proj',
      metadata: { env: 'dev', version: '1.0' },
    });
    expect(session.metadata.env).toBe('dev');
    expect(session.metadata.version).toBe('1.0');
  });
});

// ============================================================
// Pipeline Tests
// ============================================================

describe('pipeline', () => {
  beforeEach(() => {
    __test_clearStore();
  });

  describe('buildPolicyContext', () => {
    it('extracts command from Bash tool', () => {
      const ctx = buildPolicyContext('Bash', { command: 'echo hello' });
      expect(ctx.command).toBe('echo hello');
      expect(ctx.toolName).toBe('Bash');
    });

    it('does not set command for non-Bash tools', () => {
      const ctx = buildPolicyContext('Read', { file_path: 'src/index.ts' });
      expect(ctx.command).toBeUndefined();
      expect(ctx.toolName).toBe('Read');
    });

    it('extracts file_path from tool input', () => {
      const ctx = buildPolicyContext('Write', { file_path: 'src/index.ts' });
      expect(ctx.affectedPaths).toEqual(['src/index.ts']);
    });

    it('handles camelCase filePath', () => {
      const ctx = buildPolicyContext('Write', { filePath: 'src/index.ts' });
      expect(ctx.affectedPaths).toEqual(['src/index.ts']);
    });

    it('handles bare path field', () => {
      const ctx = buildPolicyContext('Write', { path: 'src/index.ts' });
      expect(ctx.affectedPaths).toEqual(['src/index.ts']);
    });
  });

  describe('evaluateToolCall', () => {
    const baseParams = {
      sessionId: 'ses_test' as any,
      turnId: 'trn_test' as any,
      agentId: 'test-agent' as any,
      toolUseId: 'tui_test',
      toolInput: {},
    };

    it('allows read-only tools', async () => {
      const verdict = await evaluateToolCall({
        ...baseParams,
        toolName: 'Read',
        toolInput: { file_path: 'src/index.ts' },
      });
      expect(verdict.outcome).toBe('allow');
      expect(verdict.trace.permission_decision).toBe('allow');
    });

    it('denies credential write', async () => {
      const verdict = await evaluateToolCall({
        ...baseParams,
        toolName: 'Write',
        toolInput: { file_path: 'config/credentials.json' },
      });
      expect(verdict.outcome).toBe('deny');
      expect(verdict.trace.permission_decision).toBe('deny');
      expect(verdict.trace.reason).toContain('credential');
    });

    it('needs_approval for dangerous bash', async () => {
      const verdict = await evaluateToolCall({
        ...baseParams,
        toolName: 'Bash',
        toolInput: { command: 'rm -rf /tmp/test' },
      });
      expect(verdict.outcome).toBe('needs_approval');
      if (verdict.outcome === 'needs_approval') {
        expect(verdict.approval).toBeDefined();
        expect(verdict.approval.status).toBe('pending');
      }
    });

    it('needs_approval for protected path write', async () => {
      const verdict = await evaluateToolCall({
        ...baseParams,
        toolName: 'Write',
        toolInput: { file_path: '.env.production' },
      });
      expect(verdict.outcome).toBe('needs_approval');
    });

    it('includes all trace fields', async () => {
      const verdict = await evaluateToolCall({
        ...baseParams,
        toolName: 'Glob',
        toolInput: { pattern: '**/*.ts' },
      });
      expect(verdict.trace.session_id).toBe('ses_test');
      expect(verdict.trace.turn_id).toBe('trn_test');
      expect(verdict.trace.agent_id).toBe('test-agent');
      expect(verdict.trace.tool_use_id).toBe('tui_test');
      expect(verdict.trace.tool_name).toBe('Glob');
      expect(verdict.trace.timestamp).toBeDefined();
    });
  });

  describe('resolveToolCallApproval', () => {
    it('returns undefined for unknown approval', () => {
      const result = resolveToolCallApproval('nonexistent', { approved: true });
      expect(result).toBeUndefined();
    });
  });

  describe('checkApprovalStatus', () => {
    it('returns undefined for unknown approval', () => {
      const result = checkApprovalStatus('nonexistent');
      expect(result).toBeUndefined();
    });
  });
});

// ============================================================
// Orchestrator Tests
// ============================================================

describe('orchestrator', () => {
  beforeEach(() => {
    __test_resetRuntime();
    __test_clearStore();
  });

  it('creates a session and returns its ID', () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    expect(sid).toMatch(/^ses_/);
  });

  it('starts a turn within a session', () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const ctx = startTurn(sid, 'hello world');
    expect(ctx).toBeDefined();
    expect(ctx!.sessionId).toBe(sid);
    expect(ctx!.turnId).toMatch(/^trn_/);
    expect(ctx!.turnNumber).toBe(1);
    expect(ctx!.state.user_input).toBe('hello world');
    expect(ctx!.state.status).toBe('active');
  });

  it('returns undefined starting turn on unknown session', () => {
    const ctx = startTurn('ses_nonexistent' as any, 'test');
    expect(ctx).toBeUndefined();
  });

  it('returns undefined starting turn on ended session', () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    orchestrateEndSession(sid);
    const ctx = startTurn(sid, 'test');
    expect(ctx).toBeUndefined();
  });

  it('processes a tool call and records trace in turn state', async () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const ctx = startTurn(sid, 'read file')!;

    const verdict = await processToolCall(ctx, 'Read', { file_path: 'test.ts' });
    expect(verdict.outcome).toBe('allow');
    expect(ctx.state.tool_calls).toHaveLength(1);
    expect(ctx.state.tool_calls[0].tool_name).toBe('Read');
  });

  it('processes a denied tool call', async () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const ctx = startTurn(sid, 'write credentials')!;

    const verdict = await processToolCall(ctx, 'Write', {
      file_path: 'credentials.json',
    });
    expect(verdict.outcome).toBe('deny');
    expect(ctx.state.tool_calls).toHaveLength(1);
  });

  it('processes a needs_approval tool call', async () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const ctx = startTurn(sid, 'run dangerous command')!;

    const verdict = await processToolCall(ctx, 'Bash', {
      command: 'rm -rf /tmp',
    });
    expect(verdict.outcome).toBe('needs_approval');
  });

  it('completes a turn', () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const ctx = startTurn(sid, 'hello')!;

    const state = completeTurn(ctx, 'Response summary');
    expect(state.status).toBe('completed');
    expect(state.completed_at).toBeDefined();
    expect(state.response_summary).toBe('Response summary');
  });

  it('ends a session', () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const result = orchestrateEndSession(sid);
    expect(result).toBe(true);
  });

  it('returns false ending unknown session', () => {
    const result = orchestrateEndSession('ses_nonexistent' as any);
    expect(result).toBe(false);
  });

  it('starts multiple turns and increments turn number', () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const ctx1 = startTurn(sid, 'first')!;
    expect(ctx1.turnNumber).toBe(1);

    const ctx2 = startTurn(sid, 'second')!;
    expect(ctx2.turnNumber).toBe(2);

    const ctx3 = startTurn(sid, 'third')!;
    expect(ctx3.turnNumber).toBe(3);
  });

  it('accumulates multiple tool calls in one turn', async () => {
    const sid = orchestrateCreateSession({ projectId: 'test-proj' });
    const ctx = startTurn(sid, 'do work')!;

    await processToolCall(ctx, 'Read', { file_path: 'a.ts' });
    await processToolCall(ctx, 'Glob', { pattern: '*.ts' });
    await processToolCall(ctx, 'Read', { file_path: 'b.ts' });

    expect(ctx.state.tool_calls).toHaveLength(3);
  });
});

// ============================================================
// Hook Merge Edge Cases
// ============================================================

describe('mergeHookDecisions — edge cases', () => {
  it('handles single-element decisions', () => {
    expect(mergeHookDecisions([{ decision: 'allow', reason: 'ok' }]).final.decision).toBe('allow');
    expect(mergeHookDecisions([{ decision: 'deny', reason: 'no' }]).final.decision).toBe('deny');
    expect(mergeHookDecisions([{ decision: 'needs_approval', reason: 'maybe' }]).final.decision).toBe('needs_approval');
  });

  it('preserves reason from the winning decision', () => {
    const result = mergeHookDecisions([
      { decision: 'allow', reason: 'first' },
      { decision: 'deny', reason: 'blocked by security' },
      { decision: 'allow', reason: 'second' },
    ]);
    expect(result.final.decision).toBe('deny');
    expect(result.final.reason).toBe('blocked by security');
  });

  it('needs_approval reason is preserved when it wins over allow', () => {
    const result = mergeHookDecisions([
      { decision: 'allow', reason: 'safe' },
      { decision: 'needs_approval', reason: 'suspicious pattern detected' },
    ]);
    expect(result.final.reason).toBe('suspicious pattern detected');
  });

  it('handles many decisions without performance issue', () => {
    const decisions: HookDecision[] = Array.from({ length: 100 }, (_, i) => ({
      decision: i === 50 ? 'deny' as const : 'allow' as const,
      reason: `rule-${i}`,
    }));
    const result = mergeHookDecisions(decisions);
    expect(result.final.decision).toBe('deny');
    expect(result.final.reason).toBe('rule-50');
  });
});
