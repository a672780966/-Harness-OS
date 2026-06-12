/**
 * Harness OS — Verification Report
 *
 * Phase 6.4: Generate and save verification reports.
 *
 * Output: .project/reports/verification/<run-id>.md
 * Includes: command results table, failure details, risk notes
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §9
 *            11_ACCEPTANCE_CRITERIA.md §12
 */

import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import type { VerificationStep } from './plan.js';
import type { RunResult } from './runner.js';
import { redactText } from '../governance/redactor.js';

// ============================================================
// Types
// ============================================================

export interface VerificationReport {
  runId: string;
  taskId?: string;
  projectPath: string;
  createdAt: string;
  status: RunResult['status'];
  steps: VerificationStep[];
  result: RunResult;
  risks: string[];
}

// ============================================================
// Generate Report
// ============================================================

/**
 * Generate a verification report object.
 */
export function generateReport(
  runId: string,
  steps: VerificationStep[],
  result: RunResult,
  options?: {
    taskId?: string;
    projectPath?: string;
    risks?: string[];
  },
): VerificationReport {
  const risks = options?.risks ?? [];

  // Auto-generate risks from failures
  const failedSteps = steps.filter(s => s.status === 'failed');
  for (const f of failedSteps) {
    risks.push(`Verification failed: ${f.name} (${f.command})`);
  }

  return {
    runId,
    taskId: options?.taskId,
    projectPath: options?.projectPath ?? process.cwd(),
    createdAt: new Date().toISOString(),
    status: result.status,
    steps,
    result,
    risks,
  };
}

// ============================================================
// Save Report
// ============================================================

/**
 * Save a verification report to .project/reports/verification/<run-id>.md
 */
export function saveReport(report: VerificationReport): string {
  const reportDir = join(resolve(report.projectPath), '.project/reports/verification');
  if (!existsSync(reportDir)) {
    mkdirSync(reportDir, { recursive: true });
  }

  const reportPath = join(reportDir, `${report.runId}.md`);
  const content = formatReport(report);
  writeFileSync(reportPath, content, 'utf-8');

  return reportPath;
}

// ============================================================
// Format Report
// ============================================================

/**
 * Format a verification report as Markdown.
 */
function formatReport(report: VerificationReport): string {
  const lines = [
    `# Verification Report: ${report.runId}`,
    '',
    `**Task:** ${report.taskId ?? '(no task)'}`,
    `**Date:** ${report.createdAt}`,
    `**Status:** ${report.status.toUpperCase()}`,
    '',
    '## Summary',
    '',
    `| Metric | Value |`,
    '|--------|-------|',
    `| Passed | ${report.result.passed} |`,
    `| Failed | ${report.result.failed} |`,
    `| Skipped | ${report.result.skipped} |`,
    `| Total | ${report.result.total} |`,
    `| Duration | ${(report.result.durationMs / 1000).toFixed(1)}s |`,
    '',
    '## Step Results',
    '',
    '| # | Name | Type | Status | Exit Code | Duration |',
    '|---|------|------|--------|-----------|----------|',
  ];

  report.steps.forEach((step, i) => {
    lines.push(
      `| ${i + 1} | ${step.name} | ${step.type} | ${step.status} | ${step.exitCode ?? '-'} | ${(step.durationMs / 1000).toFixed(1)}s |`,
    );
  });

  // Failure details
  const failures = report.steps.filter(s => s.status === 'failed');
  if (failures.length > 0) {
    lines.push('', '## Failures', '');
    for (const f of failures) {
      lines.push(`### ${f.name} (${redactText(f.command)})`);
      lines.push('');
      if (f.stdout.trim()) lines.push('```', redactText(f.stdout.slice(0, 1000)), '```', '');
      if (f.stderr.trim()) lines.push('```', redactText(f.stderr.slice(0, 1000)), '```', '');
    }
  }

  // Risks
  if (report.risks.length > 0) {
    lines.push('', '## Risks', '');
    for (const r of report.risks) {
      lines.push(`- ${redactText(r)}`);
    }
  }

  lines.push('');
  return lines.join('\n');
}
