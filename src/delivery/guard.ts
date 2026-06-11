/**
 * Harness OS — Delivery Guard
 *
 * Phase 8.1: Check preconditions before delivery.
 *
 * Checks:
 *   1. Verification status — must exist and not be "failed"
 *   2. Run report — must exist
 *   3. Governance — push main / deploy / release require approval
 *
 * Reference: 10_DELIVERY_PIPELINE.md §6, §14
 */

import { existsSync, readFileSync, readdirSync } from 'fs';
import { execSync } from 'child_process';
import { join, resolve } from 'path';

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
 * Check verification result exists and is not "failed".
 */
function checkVerification(projectPath: string, taskId?: string): GuardCheck {
  // Look for verification reports in .project/reports/verification/
  const verDir = join(projectPath, '.project/reports/verification');
  if (!existsSync(verDir)) {
    return {
      check: 'Verification result exists',
      passed: false,
      reason: 'No verification reports directory found',
      severity: 'block',
    };
  }

  const files = readdirSync(verDir).filter(f => f.endsWith('.md'));
  if (files.length === 0) {
    return {
      check: 'Verification result exists',
      passed: false,
      reason: 'No verification reports found — run `harness verify` first',
      severity: 'block',
    };
  }

  // Check the latest report
  const latest = files.sort().reverse()[0];
  const content = readFileSync(join(verDir, latest), 'utf-8');

  if (content.includes('FAILED') || content.includes('failed')) {
    return {
      check: 'Verification passed',
      passed: false,
      reason: `Verification failed — check ${latest}`,
      severity: 'block',
    };
  }

  if (content.includes('PASSED') || content.includes('Status: passed')) {
    return {
      check: 'Verification passed',
      passed: true,
      reason: `Verification passed — ${latest}`,
      severity: 'warn',
    };
  }

  return {
    check: 'Verification status known',
    passed: true,
    reason: `Found verification report: ${latest}`,
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
    const files = readdirSync(runsDir).filter(f => f.endsWith('.md'));
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
 */
export async function runGuard(
  options: {
    deliveryType: 'commit' | 'pull-request' | 'release' | 'deploy' | 'rollback';
    projectPath?: string;
    taskId?: string;
    runId?: string;
  },
): Promise<GuardResult> {
  const projectPath = resolve(options.projectPath || process.cwd());
  const checks: GuardCheck[] = [];

  // 1. Check git status
  checks.push(checkGitStatus(projectPath));

  // 2. Check verification
  checks.push(checkVerification(projectPath, options.taskId));

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
