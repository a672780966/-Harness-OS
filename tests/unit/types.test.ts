/**
 * Unit tests for core types and utility functions.
 *
 * Covers: src/types.ts
 * Reference: 13_TESTING_STRATEGY.md §6 (Unit Tests)
 *           14_ERROR_CODES.md §27 (Error Code Testing)
 */

import { describe, it, expect } from 'vitest';
import { createError, HarnessExitCode } from '../../src/types.js';

describe('HarnessError', () => {
  it('creates an error with all required fields', () => {
    const err = createError(
      'ERR_TEST',
      'test',
      'error',
      'Test error message',
      'Run a test to recover',
      true,
      true
    );

    expect(err.code).toBe('ERR_TEST');
    expect(err.category).toBe('test');
    expect(err.severity).toBe('error');
    expect(err.message).toBe('Test error message');
    expect(err.recoveryHint).toBe('Run a test to recover');
    expect(err.recoverable).toBe(true);
    expect(err.retryable).toBe(true);
    expect(err.userActionRequired).toBe(true);
    expect(err.createdAt).toBeTruthy();
    expect(() => new Date(err.createdAt)).not.toThrow();
  });

  it('defaults recoverable to true and retryable to false', () => {
    const err = createError('ERR_DEFAULT', 'test', 'warning', 'Default', 'Fix it');
    expect(err.recoverable).toBe(true);
    expect(err.retryable).toBe(false);
  });

  it('generates a valid ISO timestamp', () => {
    const err = createError('ERR_TIME', 'test', 'fatal', 'Time test', 'Wait');
    const created = new Date(err.createdAt);
    const now = new Date();
    expect(created.getTime()).toBeLessThanOrEqual(now.getTime());
    expect(created.getTime()).toBeGreaterThan(now.getTime() - 5000);
  });
});

describe('HarnessExitCode', () => {
  it('assigns correct exit codes', () => {
    expect(HarnessExitCode.SUCCESS).toBe(0);
    expect(HarnessExitCode.USER_INPUT_ERROR).toBe(10);
    expect(HarnessExitCode.PROJECT_ERROR).toBe(20);
    expect(HarnessExitCode.TASK_ERROR).toBe(30);
    expect(HarnessExitCode.CONTEXT_ERROR).toBe(40);
    expect(HarnessExitCode.SKILL_ERROR).toBe(50);
    expect(HarnessExitCode.GOVERNANCE_ERROR).toBe(60);
    expect(HarnessExitCode.VERIFICATION_ERROR).toBe(70);
    expect(HarnessExitCode.DELIVERY_ERROR).toBe(80);
    expect(HarnessExitCode.STATE_ERROR).toBe(90);
    expect(HarnessExitCode.CONFIG_ERROR).toBe(100);
    expect(HarnessExitCode.INTERNAL_ERROR).toBe(120);
  });

  it('has unique exit codes', () => {
    const codes = Object.values(HarnessExitCode).filter(v => typeof v === 'number');
    const unique = new Set(codes);
    expect(codes.length).toBe(unique.size);
  });

  it('uses multiples of 10 for easy parsing', () => {
    const codes = Object.values(HarnessExitCode).filter(v => typeof v === 'number') as number[];
    for (const code of codes) {
      expect(code % 10).toBe(0);
    }
  });
});

describe('Error Code Format (14_ERROR_CODES.md §5)', () => {
  it('follows ERR_DOMAIN_REASON format', () => {
    const codes = [
      'ERR_PROJECT_NOT_FOUND',
      'ERR_PROJECT_MISSING_AGENTS_MD',
      'ERR_TASK_NOT_FOUND',
      'ERR_TASK_INVALID_STATE',
      'ERR_CONTEXT_BUILD_FAILED',
      'ERR_SKILL_TIMEOUT',
      'ERR_POLICY_DENIED',
      'ERR_APPROVAL_REQUIRED',
      'ERR_VERIFICATION_FAILED',
      'ERR_DELIVERY_BLOCKED',
      'ERR_CHECKPOINT_NOT_FOUND',
      'ERR_CONFIG_INVALID',
      'ERR_MIGRATION_FAILED',
      'ERR_CLI_INVALID_ARGUMENTS',
      'ERR_INTERNAL_INVARIANT_BROKEN',
    ];

    const pattern = /^ERR_[A-Z]+_[A-Z_]+$/;
    for (const code of codes) {
      expect(code).toMatch(pattern);
    }
  });

  it('warning codes follow WARN_DOMAIN_REASON format', () => {
    const codes = [
      'WARN_CONTEXT_TRIMMED',
      'WARN_VERIFICATION_SKIPPED',
      'WARN_GIT_DIRTY_STATE',
    ];

    const pattern = /^WARN_[A-Z]+_[A-Z_]+$/;
    for (const code of codes) {
      expect(code).toMatch(pattern);
    }
  });
});
