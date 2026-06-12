/**
 * Harness OS — CLI Formatter + Error Codes Tests
 *
 * Coverage:
 * - Formatter: detectOutputMode, buildMeta, JSON builder, pretty/quiet formatting
 * - Error codes: domain factories, required fields, code constants
 *
 * Reference: 16_CLI_OUTPUT_CONTRACT.md | 14_ERROR_CODES.md
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  detectOutputMode,
  isNonInteractive,
  buildMeta,
  buildJsonOutput,
} from '../../src/cli/formatter.js';

import {
  createProjectNotFoundError,
  createProjectMissingAgentsMdError,
  createTaskNotFoundError,
  createTaskInvalidTransitionError,
  createPolicyDeniedError,
  createApprovalRequiredError,
  createDeliveryBlockedError,
  createCheckpointNotFoundError,
  createCliInvalidArgumentError,
  ErrorCodes,
} from '../../src/errors/index.js';

// ============================================================
// Formatter Tests
// ============================================================

describe('output mode detection', () => {
  it('defaults to pretty', () => {
    expect(detectOutputMode({})).toBe('pretty');
  });

  it('detects --json flag', () => {
    expect(detectOutputMode({ json: true })).toBe('json');
  });

  it('detects --quiet flag', () => {
    expect(detectOutputMode({ quiet: true })).toBe('quiet');
  });

  it('json flag takes priority over quiet', () => {
    expect(detectOutputMode({ json: true, quiet: true })).toBe('json');
  });
});

describe('buildMeta', () => {
  it('includes version, mode, timestamp', () => {
    const meta = buildMeta('test', 'pretty');
    expect(meta.version).toBe('1.0.0');
    expect(meta.outputMode).toBe('pretty');
    expect(meta.generatedAt).toBeTruthy();
    expect(meta.redacted).toBe(true);
  });

  it('accepts overrides', () => {
    const meta = buildMeta('test', 'json', { projectId: 'proj_001', durationMs: 100 });
    expect(meta.projectId).toBe('proj_001');
    expect(meta.durationMs).toBe(100);
  });
});

describe('buildJsonOutput', () => {
  it('builds success output', () => {
    const out = buildJsonOutput({ command: 'test', status: 'success', data: { key: 'value' } });
    expect(out.ok).toBe(true);
    expect(out.command).toBe('test');
    expect(out.data).toEqual({ key: 'value' });
    expect(out.meta.outputMode).toBe('json');
  });

  it('builds error output', () => {
    const error = createProjectNotFoundError('/path');
    const out = buildJsonOutput({ command: 'open', status: 'failed', error });
    expect(out.ok).toBe(false);
    expect(out.error).toBeDefined();
    expect(out.error!.code).toBe('ERR_PROJECT_NOT_FOUND');
  });

  it('includes warnings', () => {
    const out = buildJsonOutput({
      command: 'verify', status: 'partial',
      warnings: [{ code: 'WARN_SKIPPED', message: 'No test command found' }],
    });
    expect(out.warnings).toHaveLength(1);
    expect(out.warnings[0].code).toBe('WARN_SKIPPED');
  });
});

// ============================================================
// Error Codes Tests
// ============================================================

describe('ErrorCodes constants', () => {
  it('has all required error codes', () => {
    expect(ErrorCodes.ERR_PROJECT_NOT_FOUND).toBe('ERR_PROJECT_NOT_FOUND');
    expect(ErrorCodes.ERR_TASK_NOT_FOUND).toBe('ERR_TASK_NOT_FOUND');
    expect(ErrorCodes.ERR_POLICY_DENIED).toBe('ERR_POLICY_DENIED');
    expect(ErrorCodes.ERR_APPROVAL_REQUIRED).toBe('ERR_APPROVAL_REQUIRED');
    expect(ErrorCodes.ERR_VERIFICATION_FAILED).toBe('ERR_VERIFICATION_FAILED');
    expect(ErrorCodes.ERR_DELIVERY_BLOCKED).toBe('ERR_DELIVERY_BLOCKED');
    expect(ErrorCodes.ERR_CLI_INVALID_ARGUMENT).toBe('ERR_CLI_INVALID_ARGUMENT');
  });
});

describe('error factories', () => {
  it('createProjectNotFoundError has required fields', () => {
    const err = createProjectNotFoundError('/bad/path');
    expect(err.code).toBe('ERR_PROJECT_NOT_FOUND');
    expect(err.category).toBe('project');
    expect(err.severity).toBe('error');
    expect(err.message).toContain('/bad/path');
    expect(err.recoveryHint).toBeTruthy();
    expect(err.recoverable).toBe(true);
    expect(err.createdAt).toBeTruthy();
  });

  it('createProjectMissingAgentsMdError is retryable', () => {
    const err = createProjectMissingAgentsMdError();
    expect(err.retryable).toBe(true);
    expect(err.code).toBe('ERR_PROJECT_MISSING_AGENTS_MD');
  });

  it('createTaskNotFoundError includes task ID', () => {
    const err = createTaskNotFoundError('task_001');
    expect(err.message).toContain('task_001');
    expect(err.details).toEqual({ taskId: 'task_001' });
  });

  it('createTaskInvalidTransitionError includes from/to', () => {
    const err = createTaskInvalidTransitionError('created', 'completed');
    expect(err.message).toContain('created → completed');
  });

  it('createPolicyDeniedError includes action', () => {
    const err = createPolicyDeniedError('rm -rf', 'Dangerous command');
    expect(err.message).toContain('rm -rf');
  });

  it('createApprovalRequiredError includes action', () => {
    const err = createApprovalRequiredError('Delete file', 'High risk');
    expect(err.message).toContain('Delete file');
    expect(err.code).toBe('ERR_APPROVAL_REQUIRED');
  });

  it('createDeliveryBlockedError includes reason', () => {
    const err = createDeliveryBlockedError('No verification result');
    expect(err.code).toBe('ERR_DELIVERY_BLOCKED');
  });

  it('createCheckpointNotFoundError includes ID', () => {
    const err = createCheckpointNotFoundError('cp_001');
    expect(err.details).toEqual({ checkpointId: 'cp_001' });
  });

  it('createCliInvalidArgumentError has cli category', () => {
    const err = createCliInvalidArgumentError('Unknown option --foobar');
    expect(err.category).toBe('cli');
  });
});
