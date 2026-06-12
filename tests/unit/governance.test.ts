/**
 * Harness OS — Governance Module Tests
 *
 * Coverage (CLAUDE.md §14):
 * - Policy: allow path, deny path, needs_approval path, no matching rule
 * - Approval: approve, reject, expired, not found
 * - Hook merge: single hook decisions, multi-hook merge, deny priority
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { checkPolicy, classifyRisk, createRule } from '../../src/governance/policy.js';
import {
  submitApproval,
  resolveApproval,
  getApproval,
  listPendingApprovals,
  listAllApprovals,
  approvalToDecision,
  __test_clearStore,
  computeInputDigest,
  consumeApproval,
  validateApprovalBinding,
} from '../../src/governance/approval-gate.js';
import { mergeHookDecisions, type HookDecision } from '../../src/types.js';

// ============================================================
// Policy Tests
// ============================================================

describe('checkPolicy', () => {
  it('allows read-only tools', async () => {
    const result = await checkPolicy('Read', {});
    expect(result.decision).toBe('allow');
    expect(result.reason).toContain('Read-only tool');
    expect(result.policySource).toContain('read-only-tools');
  });

  it('allows Glob tool', async () => {
    const result = await checkPolicy('Glob', {});
    expect(result.decision).toBe('allow');
  });

  it('needs_approval for dangerous bash commands', async () => {
    const result = await checkPolicy('Bash', { command: 'rm -rf /tmp/test' });
    expect(result.decision).toBe('needs_approval');
    expect(result.reason).toContain('High-risk');
    expect(result.policySource).toContain('high-risk-bash');
  });

  it('needs_approval for protected path modifications', async () => {
    const result = await checkPolicy('Write', {
      affectedPaths: ['.env.production'],
    });
    expect(result.decision).toBe('needs_approval');
    expect(result.policySource).toContain('protected-paths');
  });

  it('denies credential file writes', async () => {
    const result = await checkPolicy('Write', {
      affectedPaths: ['config/credentials.json'],
    });
    expect(result.decision).toBe('deny');
    expect(result.policySource).toContain('credential-write');
  });

  it('falls back to needs_approval when no rule matches', async () => {
    const result = await checkPolicy('UnknownTool99', {});
    expect(result.decision).toBe('needs_approval');
    expect(result.reason).toContain('No matching policy rule');
    expect(result.policySource).toContain('default-fallback');
    expect(result.riskLevel).toBe('medium');
  });

  it('accepts custom rules', async () => {
    const customRule = createRule(
      'custom-allow',
      'Custom allow rule',
      () => true,
      'allow',
      'Custom allowed',
    );
    const result = await checkPolicy('Anything', {}, [customRule]);
    expect(result.decision).toBe('allow');
    expect(result.policySource).toContain('custom-allow');
  });

  it('first matching rule wins', async () => {
    const rules = [
      createRule('first', 'First rule matches all', () => true, 'deny', 'Denied by first'),
      createRule('second', 'Second rule', () => true, 'allow', 'Allowed by second'),
    ];
    const result = await checkPolicy('Bash', { command: 'echo hi' }, rules);
    expect(result.decision).toBe('deny');
    expect(result.policySource).toContain('first');
  });
});

// ============================================================
// classifyRisk Tests
// ============================================================

describe('classifyRisk', () => {
  it('classifies rm -rf as high risk', () => {
    expect(classifyRisk('rm -rf /')).toBe('high');
    expect(classifyRisk('rm -rf node_modules')).toBe('high');
  });

  it('classifies sudo as high risk', () => {
    expect(classifyRisk('sudo rm file')).toBe('high');
    expect(classifyRisk('sudo rm -rf /')).toBe('high');
  });

  it('classifies git push force as high risk', () => {
    expect(classifyRisk('git push --force origin main')).toBe('high');
    expect(classifyRisk('git push -f origin main')).toBe('high');
  });

  it('classifies git reset --hard as high risk', () => {
    expect(classifyRisk('git reset --hard HEAD')).toBe('high');
  });

  it('classifies git clean -fd as high risk', () => {
    expect(classifyRisk('git clean -fd')).toBe('high');
  });

  it('classifies chmod -R as high risk', () => {
    expect(classifyRisk('chmod -R 777 /')).toBe('high');
  });

  it('classifies chown -R as high risk', () => {
    expect(classifyRisk('chown -R root /')).toBe('high');
  });

  it('classifies npm publish as high risk', () => {
    expect(classifyRisk('npm publish')).toBe('high');
  });

  it('classifies terraform destroy as high risk', () => {
    expect(classifyRisk('terraform destroy')).toBe('high');
  });

  it('classifies safe commands as low risk', () => {
    expect(classifyRisk('pnpm test')).toBe('low');
    expect(classifyRisk('git status')).toBe('low');
    expect(classifyRisk('git diff')).toBe('low');
    expect(classifyRisk('ls -la')).toBe('low');
    expect(classifyRisk('cat README.md')).toBe('low');
    expect(classifyRisk('echo hello')).toBe('low');
    expect(classifyRisk('npm run build')).toBe('low');
    expect(classifyRisk('git push origin main')).toBe('low');
  });
});

// ============================================================
// Approval Gate Tests
// ============================================================

describe('approval-gate', () => {
  beforeEach(() => {
    __test_clearStore();
  });

  it('submits a pending approval', () => {
    const approval = submitApproval({
      id: 'test-1',
      action: 'Bash',
      reason: 'High-risk command',
      riskLevel: 'high',
    });

    expect(approval.id).toBe('test-1');
    expect(approval.status).toBe('pending');
    expect(approval.action).toBe('Bash');
    expect(approval.riskLevel).toBe('high');
    expect(approval.createdAt).toBeDefined();
    expect(approval.expiresAt).toBeDefined();
  });

  it('approves a pending approval', () => {
    submitApproval({ id: 'test-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    const resolved = resolveApproval('test-1', { approved: true, resolvedBy: 'operator' });

    expect(resolved).toBeDefined();
    expect(resolved!.status).toBe('approved');
    expect(resolved!.resolvedBy).toBe('operator');
    expect(resolved!.resolvedAt).toBeDefined();
  });

  it('rejects a pending approval', () => {
    submitApproval({ id: 'test-1', action: 'Write', reason: 'test', riskLevel: 'medium' });
    const resolved = resolveApproval('test-1', {
      approved: false,
      resolvedBy: 'operator',
      rejectionReason: 'Not needed',
    });

    expect(resolved).toBeDefined();
    expect(resolved!.status).toBe('rejected');
    expect(resolved!.resolvedBy).toBe('operator');
  });

  it('returns undefined for unknown approval ID', () => {
    const resolved = resolveApproval('nonexistent', { approved: true });
    expect(resolved).toBeUndefined();
  });

  it('lists only pending (unexpired) approvals', () => {
    submitApproval({ id: 'pending-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    submitApproval({ id: 'pending-2', action: 'Write', reason: 'test', riskLevel: 'medium' });
    resolveApproval('pending-1', { approved: true, resolvedBy: 'op' });

    const pending = listPendingApprovals();
    expect(pending).toHaveLength(1);
    expect(pending[0].id).toBe('pending-2');
  });

  it('lists all approvals regardless of status', () => {
    submitApproval({ id: 'a-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    submitApproval({ id: 'a-2', action: 'Write', reason: 'test', riskLevel: 'low' });
    resolveApproval('a-1', { approved: false, resolvedBy: 'op' });

    const all = listAllApprovals();
    expect(all).toHaveLength(2);
  });

  it('converts approved to allow decision', () => {
    submitApproval({ id: 'test-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    resolveApproval('test-1', { approved: true, resolvedBy: 'operator' });
    const approval = getApproval('test-1')!;

    const d = approvalToDecision(approval);
    expect(d.decision).toBe('allow');
  });

  it('converts rejected to deny decision', () => {
    submitApproval({ id: 'test-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    resolveApproval('test-1', { approved: false, resolvedBy: 'operator' });
    const approval = getApproval('test-1')!;

    const d = approvalToDecision(approval);
    expect(d.decision).toBe('deny');
  });

  it('converts pending to needs_approval decision', () => {
    submitApproval({ id: 'test-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    const approval = getApproval('test-1')!;

    const d = approvalToDecision(approval);
    expect(d.decision).toBe('needs_approval');
  });

  it('marks expired approvals when resolved after TTL', async () => {
    submitApproval({ id: 'test-1', action: 'Bash', reason: 'test', riskLevel: 'high', ttlMs: 0 });
    await new Promise(r => setTimeout(r, 5));

    const resolved = resolveApproval('test-1', { approved: true, resolvedBy: 'op' });
    expect(resolved!.status).toBe('expired');

    const d = approvalToDecision(resolved!);
    expect(d.decision).toBe('deny');
    expect(d.reason).toContain('expired');
  });

  it('cannot approve an already resolved request', () => {
    submitApproval({ id: 'test-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    resolveApproval('test-1', { approved: true, resolvedBy: 'op' });

    // second resolve should return the already-approved state
    const second = resolveApproval('test-1', { approved: false, resolvedBy: 'op2' });
    expect(second!.status).toBe('approved'); // unchanged
  });

  it('rejects expired approvals with deny decision', async () => {
    submitApproval({ id: 'test-1', action: 'Bash', reason: 'test', riskLevel: 'high', ttlMs: 0 });
    await new Promise(r => setTimeout(r, 5));

    const resolved = resolveApproval('test-1', { approved: true });
    expect(resolved!.status).toBe('expired');
  });
});

// ============================================================
// Hook Merge Tests
// ============================================================

describe('mergeHookDecisions', () => {
  it('single allow stays allow', () => {
    const result = mergeHookDecisions([{ decision: 'allow', reason: 'safe' }]);
    expect(result.final.decision).toBe('allow');
    expect(result.sources).toHaveLength(1);
  });

  it('single deny stays deny', () => {
    const result = mergeHookDecisions([{ decision: 'deny', reason: 'blocked' }]);
    expect(result.final.decision).toBe('deny');
  });

  it('single needs_approval stays needs_approval', () => {
    const result = mergeHookDecisions([{ decision: 'needs_approval', reason: 'check' }]);
    expect(result.final.decision).toBe('needs_approval');
  });

  it('deny overrides allow', () => {
    const result = mergeHookDecisions([
      { decision: 'allow', reason: 'safe' },
      { decision: 'deny', reason: 'blocked' },
    ]);
    expect(result.final.decision).toBe('deny');
  });

  it('deny overrides needs_approval', () => {
    const result = mergeHookDecisions([
      { decision: 'needs_approval', reason: 'check' },
      { decision: 'deny', reason: 'blocked' },
    ]);
    expect(result.final.decision).toBe('deny');
  });

  it('needs_approval overrides allow', () => {
    const result = mergeHookDecisions([
      { decision: 'allow', reason: 'safe' },
      { decision: 'needs_approval', reason: 'check' },
    ]);
    expect(result.final.decision).toBe('needs_approval');
  });

  it('multiple allow stays allow', () => {
    const result = mergeHookDecisions([
      { decision: 'allow', reason: 'rule-1' },
      { decision: 'allow', reason: 'rule-2' },
      { decision: 'allow', reason: 'rule-3' },
    ]);
    expect(result.final.decision).toBe('allow');
  });

  it('deny has highest priority among mixed decisions', () => {
    const result = mergeHookDecisions([
      { decision: 'allow', reason: 'safe' },
      { decision: 'needs_approval', reason: 'check' },
      { decision: 'deny', reason: 'blocked' },
      { decision: 'allow', reason: 'also-safe' },
    ]);
    expect(result.final.decision).toBe('deny');
  });

  it('returns sources array with all inputs', () => {
    const decisions: HookDecision[] = [
      { decision: 'allow', reason: 'a' },
      { decision: 'deny', reason: 'b' },
    ];
    const result = mergeHookDecisions(decisions);
    expect(result.sources).toHaveLength(2);
    expect(result.sources[0].decision).toBe('allow');
    expect(result.sources[1].decision).toBe('deny');
  });

  it('empty array falls back to needs_approval', () => {
    const result = mergeHookDecisions([]);
    expect(result.final.decision).toBe('needs_approval');
    expect(result.final.reason).toContain('no matching rule');
  });
});

// ============================================================
// GOV3-03: Approval Strong Binding Tests
// ============================================================

describe('GOV3-03: approval binding', () => {
  beforeEach(() => {
    __test_clearStore();
  });

  it('computeInputDigest produces stable hash', () => {
    const d1 = computeInputDigest({ path: 'test.txt', content: 'hello' });
    const d2 = computeInputDigest({ content: 'hello', path: 'test.txt' });
    expect(d1).toBe(d2);
    expect(d1.length).toBe(64); // SHA-256 hex
  });

  it('submitApproval with binding fields sets inputDigest', () => {
    const app = submitApproval({
      id: 'bind-1', action: 'Write: test.txt', reason: 'test',
      riskLevel: 'medium', skillName: 'filesystem', toolName: 'write_file',
      input: { path: 'test.txt', content: 'data' },
    });
    expect(app.skillName).toBe('filesystem');
    expect(app.toolName).toBe('write_file');
    expect(app.inputDigest).toBeDefined();
    expect(app.inputDigest!.length).toBe(64);
  });

  it('consumeApproval succeeds on approved approval', () => {
    submitApproval({ id: 'c-1', action: 'Bash', reason: 'test', riskLevel: 'high' });
    resolveApproval('c-1', { approved: true, resolvedBy: 'op' });
    const consumed = consumeApproval('c-1');
    expect(consumed).toBeDefined();
    expect(consumed!.consumed).toBe(true);
  });

  it('consumeApproval returns undefined on pending (not yet approved)', () => {
    submitApproval({ id: 'c-2', action: 'Bash', reason: 'test', riskLevel: 'high' });
    const consumed = consumeApproval('c-2');
    expect(consumed).toBeUndefined();
  });

  it('consumeApproval returns undefined on already consumed (single-use)', () => {
    submitApproval({ id: 'c-3', action: 'Bash', reason: 'test', riskLevel: 'high' });
    resolveApproval('c-3', { approved: true, resolvedBy: 'op' });
    consumeApproval('c-3');
    const second = consumeApproval('c-3');
    expect(second).toBeUndefined();
  });

  it('validateApprovalBinding rejects cross-tool usage', () => {
    const app = submitApproval({
      id: 'bind-2', action: 'Write', reason: 'test', riskLevel: 'low',
      skillName: 'filesystem', toolName: 'write_file',
    });
    const err = validateApprovalBinding(app, { skillName: 'shell', toolName: 'run_command' });
    expect(err).toContain('filesystem');
  });

  it('validateApprovalBinding rejects changed input', () => {
    const app = submitApproval({
      id: 'bind-3', action: 'Write: test.txt', reason: 'test', riskLevel: 'low',
      input: { path: 'test.txt', content: 'original' },
    });
    const err = validateApprovalBinding(app, { input: { path: 'test.txt', content: 'modified' } });
    expect(err).toContain('digest mismatch');
  });

  it('validateApprovalBinding returns null for matching context', () => {
    const app = submitApproval({
      id: 'bind-4', action: 'Write', reason: 'test', riskLevel: 'low',
      skillName: 'filesystem', toolName: 'write_file',
      input: { path: 'test.txt', content: 'data' },
    });
    const err = validateApprovalBinding(app, {
      skillName: 'filesystem', toolName: 'write_file',
      input: { path: 'test.txt', content: 'data' },
    });
    expect(err).toBeNull();
  });
});
