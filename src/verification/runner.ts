/**
 * Harness OS — Verification Runner
 *
 * Phase 6.3: Execute verification commands and capture results.
 *
 * Design:
 * - Executes commands via child_process with cwd=workspace root
 * - Captures exit code, stdout, stderr, duration
 * - Reports timeout handling
 * - Skips commands if a prior required command fails (fail-fast)
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §8
 */

import { execFile, exec } from 'child_process';
import { promisify } from 'util';
import type { VerificationPlan, VerificationStep } from './plan.js';

const execFileAsync = promisify(execFile);
const execAsync = promisify(exec);

// ============================================================
// Run Result
// ============================================================

export interface RunResult {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  status: 'passed' | 'failed' | 'partial' | 'skipped';
  durationMs: number;
}

// ============================================================
// Run a single step
// ============================================================

/**
 * Execute a single verification command.
 */
async function runStep(
  step: VerificationStep,
  cwd: string,
): Promise<VerificationStep> {
  const start = Date.now();
  step.status = 'running';

  try {
    // Use full command string on Windows (for .cmd/.bat), execFile+args on Unix
    let stdout: string, stderr: string;

    if (process.platform === 'win32') {
      const result = await execAsync(step.command, {
        cwd,
        timeout: step.timeoutMs,
        maxBuffer: 10 * 1024 * 1024,
      });
      stdout = result.stdout || '';
      stderr = result.stderr || '';
    } else {
      const parts = step.command.split(/\s+/);
      const program = parts[0];
      const args = parts.slice(1);
      const result = await execFileAsync(program, args, {
        cwd,
        timeout: step.timeoutMs,
        maxBuffer: 10 * 1024 * 1024,
      });
      stdout = result.stdout || '';
      stderr = result.stderr || '';
    }

    step.exitCode = 0;
    step.stdout = stdout.slice(0, 5000); // Summarize
    step.stderr = stderr.slice(0, 2000);
    step.status = 'passed';
  } catch (err: any) {
    if (err.killed || err.signal) {
      // Timeout
      step.exitCode = -1;
      step.stderr = (step.stderr + '\n[TIMEOUT]').trim();
      step.status = 'failed';
    } else if (err.code === 'ENOENT') {
      // Command not found
      step.exitCode = -1;
      step.stderr = `Command not found: ${step.command}`;
      step.status = 'skipped';
    } else {
      // Failed
      step.exitCode = err.code ?? 1;
      step.stdout = (err.stdout || '').toString().slice(0, 5000);
      step.stderr = (err.stderr || '').toString().slice(0, 2000);
      step.status = 'failed';
    }
  }

  step.durationMs = Date.now() - start;
  return step;
}

// ============================================================
// Run all steps
// ============================================================

/**
 * Execute the full verification plan.
 * Fail-fast: if a required step fails, subsequent required steps are skipped.
 * Optional steps are always attempted.
 */
export async function runVerification(
  plan: VerificationPlan,
): Promise<RunResult> {
  let hasFailed = false;
  const start = Date.now();

  for (const step of plan.steps) {
    // Skip if a prior required step failed
    if (hasFailed && step.required) {
      step.status = 'skipped';
      step.stderr = 'Skipped due to prior required step failure';
      continue;
    }

    await runStep(step, plan.projectPath);

    if (step.required && step.status === 'failed') {
      hasFailed = true;
    }
  }

  const passed = plan.steps.filter(s => s.status === 'passed').length;
  const failed = plan.steps.filter(s => s.status === 'failed').length;
  const skipped = plan.steps.filter(s => s.status === 'skipped').length;
  const total = plan.steps.length;

  let status: RunResult['status'];
  if (failed > 0 && passed === 0) status = 'failed';
  else if (failed > 0) status = 'partial';
  else if (passed === 0) status = 'skipped';
  else status = 'passed';

  return {
    total,
    passed,
    failed,
    skipped,
    status,
    durationMs: Date.now() - start,
  };
}

/**
 * Format verification results.
 */
export function formatResults(steps: VerificationStep[], result: RunResult): string {
  const lines = [
    'Verification Results',
    '====================',
    `Status: ${result.status.toUpperCase()}`,
    `Passed: ${result.passed} | Failed: ${result.failed} | Skipped: ${result.skipped} | Total: ${result.total}`,
    `Duration: ${(result.durationMs / 1000).toFixed(1)}s`,
    '',
    '| # | Step | Type | Status | Exit Code | Duration |',
    '|---|------|------|--------|-----------|----------|',
  ];

  steps.forEach((step, i) => {
    lines.push(
      `| ${i + 1} | ${step.name} | ${step.type} | ${step.status} | ${step.exitCode ?? '-'} | ${(step.durationMs / 1000).toFixed(1)}s |`,
    );
  });

  // Add failure details
  const failures = steps.filter(s => s.status === 'failed');
  if (failures.length > 0) {
    lines.push('', 'Failure Details:', '');
    for (const f of failures) {
      lines.push(`--- ${f.command} ---`);
      if (f.stdout) lines.push(f.stdout.slice(0, 500));
      if (f.stderr) lines.push(f.stderr.slice(0, 500));
      lines.push('');
    }
  }

  return lines.join('\n');
}
