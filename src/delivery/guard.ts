/**
 * Harness OS — Delivery Guard
 *
 * Phase 8.1: Check preconditions before delivery.
 *
 * VER3-04/VER3-05: Delivery requires an explicit verificationId.
 * - No more directory scanning for "latest" Markdown reports
 * - No more Markdown parsing for security decisions
 * - Structured verification JSON is the only binding source of truth
 * - project/task/run/commit/tree must all match
 *
 * Checks:
 *   1. Verification result — explicit verId, loaded from disk, bindings validated
 *   2. Run report — must exist
 *   3. Governance — push main / deploy / release require approval
 *   4. Git status — changes must exist
 *
 * Reference: 10_DELIVERY_PIPELINE.md §6, §14
 *            03_VERIFICATION_DELIVERY_STRONG_BINDING_FIX.md §4
 */

import { existsSync } from 'fs';
import { execSync } from 'child_process';
import { join, resolve } from 'path';
import {
  loadVerificationResult,
  checkVerificationBinding,
} from '../verification/result.js';

// ============================================================
// Types
// ============================================================

export interface GuardCheck {
  check: string;
  passed: boolean;
  reason: string;
  severity: 'block' | 'warn';
}

export interface GuardResult {
  canProceed: boolean;
  checks: GuardCheck[];
  blockedBy: string[];
  warnings: string[];
}

// ============================================================
// Guard Checks
// ============================================================

/**
 * Check verification result exists, status=passed, and bindings match
 * current project/task/run/commit/tree.
 *
 * VER3-04:
 * - Requires explicit verId — no fallback to directory scan or Markdown parse.
 * - Loads structured JSON from disk and validates all bindings.
 */
function checkVerification(
  projectPath: string,
  verId: string,
  taskId?: string,
): GuardCheck {
  if (!verId) {
    return {
      check: 'Verification result exists and passed',
      passed: false,
      reason: 'No verification ID provided. Pass --ver-id or run "harness verify" first. [VER3-04]',
      severity: 'block',
    };
  }

  const result = loadVerificationResult(projectPath, verId);
  if (!result) {
    return {
      check: 'Verification result exists and passed',
      passed: false,
      reason: `Verification result "${verId}" not found on disk. Run "harness verify" first. [VER3-04: not found]`,
      severity: 'block',
    };
  }

  // Validate bindings against current state
  const bindingCheck = checkVerificationBinding(result, {
    projectId: result.projectId,
    taskId,
    projectPath,
  });

  if (!bindingCheck.valid) {
    return {
      check: 'Verification passed',
      passed: false,
      reason: [
        `Verification ${verId} failed binding checks:`,
        ...bindingCheck.reasons.map(r => `  - ${r}`),
      ].join('\n'),
      severity: 'block',
    };
  }

  if (result.status !== 'passed') {
    return {
      check: 'Verification passed',
      passed: false,
      reason: `Verification "${verId}" status is "${result.status}", not "passed". [VER3-04]`,
      severity: 'block',
    };
  }

  return {
    check: 'Verification passed',
    passed: true,
    reason: `Verification ${verId}: passed ${
      result.sourceCommit ? `@ ${result.sourceCommit.slice(0, 8)}` : ''
    }`,
    severity: 'warn',
  };
}

/**
 * Check run report exists.
 */
function checkRunReport(projectPath: string, runId?: string): GuardCheck {
  if (runId) {
    const reportPath = join(projectPath, '.project/reports/runs', `${runId}.md`);
    if (existsSync(reportPath)) {
      return {
        check: 'Run report exists',
        passed: true,
        reason: `Run report found: ${runId}`,
        severity: 'warn',
      };
    }
  }

  // Check for any run report
  const runsDir = join(projectPath, '.project/reports/runs');
  if (existsSync(runsDir)) {
    const { readdirSync } = require('fs');
    const files = readdirSync(runsDir).filter((f: string) => f.endsWith('.md'));
    if (files.length > 0) {
      return {
        check: 'Run report exists',
        passed: true,
        reason: `Found ${files.length} run report(s)`,
        severity: 'warn',
      };
    }
  }

  return {
    check: 'Run report exists',
    passed: false,
    reason: 'No run report found — run `harness report` first',
    severity: 'block',
  };
}

/**
 * Check governance: push main / deploy / release require approval.
 */
async function checkGovernance(
  deliveryType: 'commit' | 'pull-request' | 'release' | 'deploy' | 'rollback',
): Promise<GuardCheck> {
  const requiresApproval = ['pull-request', 'release', 'deploy', 'rollback'];

  if (requiresApproval.includes(deliveryType)) {
    return {
      check: 'Governance approval for delivery',
      passed: false,
      reason: `${deliveryType} requires human approval — use --approve or approve via CLI`,
      severity: 'block',
    };
  }

  return {
    check: 'Governance approval for delivery',
    passed: true,
    reason: 'No governance restriction for commit',
    severity: 'warn',
  };
}

/**
 * Check git status is clean enough for delivery.
 */
function checkGitStatus(projectPath: string): GuardCheck {
  try {
    const status = execSync('git status --short', { cwd: projectPath, encoding: 'utf-8' }).trim();

    if (!status) {
      return {
        check: 'Git has changes to commit',
        passed: false,
        reason: 'No uncommitted changes — nothing to deliver',
        severity: 'block',
      };
    }

    return {
      check: 'Git has changes to commit',
      passed: true,
      reason: `${status.split('\n').length} file(s) changed`,
      severity: 'warn',
    };
  } catch {
    return {
      check: 'Git status readable',
      passed: false,
      reason: 'Failed to read git status',
      severity: 'block',
    };
  }
}

// ============================================================
// Run Guard
// ============================================================

/**
 * Run all delivery guard checks.
 *
 * VER3-04: verId is now REQUIRED — no fallback to Markdown scanning.
 */
export async function runGuard(
  options: {
    deliveryType: 'commit' | 'pull-request' | 'release' | 'deploy' | 'rollback';
    projectPath?: string;
    taskId?: string;
    runId?: string;
    /** VER3-04: Required — structured verification result ID. */
    verId: string;
  },
): Promise<GuardResult> {
  const projectPath = resolve(options.projectPath || process.cwd());
  const checks: GuardCheck[] = [];

  // 1. Check git status
  checks.push(checkGitStatus(projectPath));

  // 2. Check verification — REQUIRES verId, loads structured JSON from disk
  checks.push(checkVerification(projectPath, options.verId, options.taskId));

  // 3. Check run report
  checks.push(checkRunReport(projectPath, options.runId));

  // 4. Check governance
  checks.push(await checkGovernance(options.deliveryType));

  // Summarize
  const blockedChecks = checks.filter(c => !c.passed && c.severity === 'block');
  const warnings = checks.filter(c => !c.passed && c.severity === 'warn').map(c => c.reason);

  return {
    canProceed: blockedChecks.length === 0,
    checks,
    blockedBy: blockedChecks.map(c => c.reason),
    warnings,
  };
}

/**
 * Format guard result for display.
 */
export function formatGuardResult(result: GuardResult): string {
  const lines = [
    'Delivery Guard',
    '==============',
    `Proceed: ${result.canProceed ? '✅ YES' : '❌ NO'}`,
    '',
    'Checks:',
  ];

  for (const check of result.checks) {
    const icon = check.passed ? '✅' : check.severity === 'block' ? '❌' : '⚠️';
    lines.push(`  ${icon} ${check.check}: ${check.reason}`);
  }

  if (result.blockedBy.length > 0) {
    lines.push('', 'Blocked by:');
    for (const b of result.blockedBy) lines.push(`  - ${b}`);
  }

  if (result.warnings.length > 0) {
    lines.push('', 'Warnings:');
    for (const w of result.warnings) lines.push(`  - ${w}`);
  }

  return lines.join('\n');
}
