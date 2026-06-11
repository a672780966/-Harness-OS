/**
 * Harness OS — Delivery Pipeline Tests
 *
 * Coverage:
 * - Commit: type mapping, generation, task-based generation
 * - PR body: required sections, optional fields
 * - Report: generation, formatting
 *
 * Reference: 10_DELIVERY_PIPELINE.md | 11_ACCEPTANCE_CRITERIA.md §14
 */

import { describe, it, expect } from 'vitest';

import { generateCommitMessage, generateCommitFromTask, taskTypeToCommitType } from '../../src/delivery/commit.js';
import { generatePrBody } from '../../src/delivery/pr.js';
import { generateDeliveryReport } from '../../src/delivery/report.js';

// ============================================================
// Commit Message Tests
// ============================================================

describe('commit', () => {
  describe('taskTypeToCommitType', () => {
    it('maps feature to feat', () => {
      expect(taskTypeToCommitType('feature')).toBe('feat');
    });
    it('maps bugfix to fix', () => {
      expect(taskTypeToCommitType('bugfix')).toBe('fix');
    });
    it('maps refactor to refactor', () => {
      expect(taskTypeToCommitType('refactor')).toBe('refactor');
    });
    it('maps test to test', () => {
      expect(taskTypeToCommitType('test')).toBe('test');
    });
    it('maps docs to docs', () => {
      expect(taskTypeToCommitType('docs')).toBe('docs');
    });
    it('defaults to chore for unknown', () => {
      expect(taskTypeToCommitType('unknown')).toBe('chore');
    });
  });

  describe('generateCommitMessage', () => {
    it('generates header without scope', () => {
      const msg = generateCommitMessage({ taskType: 'feature', taskSummary: 'Add user authentication' });
      expect(msg.full).toBe('feat: Add user authentication');
      expect(msg.type).toBe('feat');
    });

    it('generates header with scope', () => {
      const msg = generateCommitMessage({ taskType: 'bugfix', taskSummary: 'Fix login crash', scope: 'auth' });
      expect(msg.full).toBe('fix(auth): Fix login crash');
    });

    it('includes body', () => {
      const msg = generateCommitMessage({
        taskType: 'feature',
        taskSummary: 'Add API',
        details: 'Implemented REST endpoints for user management',
      });
      expect(msg.body).toBe('Implemented REST endpoints for user management');
      expect(msg.full).toContain('Implemented REST endpoints');
    });

    it('includes footer', () => {
      const msg = generateCommitMessage({
        taskType: 'fix',
        taskSummary: 'Fix timeout',
        footer: 'Closes #123',
      });
      expect(msg.footer).toBe('Closes #123');
      expect(msg.full).toContain('Closes #123');
    });

    it('generates full message with all parts', () => {
      const msg = generateCommitMessage({
        taskType: 'feature',
        taskSummary: 'Add monitoring',
        scope: 'ops',
        details: 'Added Prometheus metrics endpoint',
        footer: 'Run: run_001',
      });
      expect(msg.full).toContain('feat(ops): Add monitoring');
      expect(msg.full).toContain('Added Prometheus');
      expect(msg.full).toContain('run_001');
    });
  });

  describe('generateCommitFromTask', () => {
    it('generates commit from task data', () => {
      const msg = generateCommitFromTask({
        taskTitle: 'Fix login button',
        taskType: 'bugfix',
        changedFiles: ['src/login.ts', 'tests/login.test.ts'],
        runId: 'run_001',
      });
      expect(msg.type).toBe('fix');
      expect(msg.summary).toBe('Fix login button');
      expect(msg.body).toContain('src/login.ts');
      expect(msg.footer).toContain('run_001');
    });
  });
});

// ============================================================
// PR Body Tests
// ============================================================

describe('generatePrBody', () => {
  it('generates PR body with all required sections', () => {
    const pr = generatePrBody({
      title: 'feat: Add user authentication',
      taskTitle: 'Implement user login flow',
      taskId: 'task_001',
      runId: 'run_001',
      summary: 'Added JWT-based authentication with refresh tokens',
      changedFiles: ['src/auth.ts', 'src/middleware.ts'],
      verificationStatus: 'passed',
      verificationReportPath: '.project/reports/verification/run_001.md',
      risks: ['Token expiration needs monitoring'],
    });

    expect(pr.title).toBe('feat: Add user authentication');
    expect(pr.body).toContain('## Summary');
    expect(pr.body).toContain('## Task');
    expect(pr.body).toContain('## Changed Files');
    expect(pr.body).toContain('## Verification');
    expect(pr.body).toContain('## Risks');
    expect(pr.body).toContain('task_001');
    expect(pr.body).toContain('src/auth.ts');
  });

  it('handles minimal input', () => {
    const pr = generatePrBody({ title: 'fix: typo' });
    expect(pr.title).toBe('fix: typo');
    expect(pr.body).toContain('## Summary');
  });

  it('includes optional sections only when provided', () => {
    const pr = generatePrBody({
      title: 'test: Add tests',
      followUp: ['Add E2E tests'],
      relatedDecisions: ['ADR-0001'],
    });

    expect(pr.body).toContain('## Follow-up');
    expect(pr.body).toContain('## Related Decisions');
    expect(pr.body).not.toContain('## Risks'); // not provided
  });
});

// ============================================================
// Delivery Report Tests
// ============================================================

describe('delivery report', () => {
  it('generates a delivery report', () => {
    const report = generateDeliveryReport({
      deliveryId: 'del_001',
      projectId: 'proj_001',
      type: 'commit',
      taskId: 'task_001',
      summary: 'Commit for login fix',
    });

    expect(report.deliveryId).toBe('del_001');
    expect(report.type).toBe('commit');
    expect(report.status).toBe('ready'); // no guard = ready
    expect(report.createdAt).toBeTruthy();
  });

  it('sets blocked status when guard fails', () => {
    const guard = {
      canProceed: false,
      checks: [{ check: 'test', passed: false, reason: 'missing', severity: 'block' as const }],
      blockedBy: ['missing verification'],
      warnings: [],
    };

    const report = generateDeliveryReport({
      deliveryId: 'del_002',
      projectId: 'proj_001',
      type: 'pull-request',
      guardResult: guard,
    });

    expect(report.status).toBe('blocked');
  });
});
