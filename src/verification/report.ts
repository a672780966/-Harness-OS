/**
 * Harness OS — Verification Report
 *
 * Phase 6.4: Generate and save verification reports.
 *
 * Output: .project/reports/verification/<run-id>.md
 * Output: .project/reports/verification/<run-id>.verification.json  (VER3-01)
 *
 * JSON is the binding source of truth for task completion and delivery.
 * Markdown is for human reading only.
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §9
 *            11_ACCEPTANCE_CRITERIA.md §12
 */

import { existsSync, mkdirSync } from 'fs';
import { join, resolve } from 'path';
import type { VerificationStep } from './plan.js';
import type { RunResult } from './runner.js';
import { redactText, safeWriteText } from '../governance/redactor.js';
import {
  saveVerificationResult,
  getCurrentCommit,
  getCurrentTree,
  computeIntegrity,
  VERIFICATION_RESULT_SCHEMA_VERSION,
  type VerificationResult,
} from './result.js';

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
// Save Report (Markdown + Structured JSON)
// ============================================================

/**
 * Save a verification report to .project/reports/verification/<run-id>.md
 * AND the structured JSON result for strong binding (VER3-01).
 *
 * Returns both file paths: { mdPath, jsonPath }
 */
export function saveReport(report: VerificationReport): { mdPath: string; jsonPath: string } {
  const reportDir = join(resolve(report.projectPath), '.project/reports/verification');
  if (!existsSync(reportDir)) {
    mkdirSync(reportDir, { recursive: true });
  }

  const mdPath = join(reportDir, `${report.runId}.md`);
  const content = formatReport(report);
  safeWriteText(mdPath, content);

  // ── Structured JSON result (VER3-01) ──
  const now = new Date().toISOString();
  const sourceCommit = getCurrentCommit(report.projectPath);
  const sourceTree = getCurrentTree(report.projectPath);

  const verificationResult: VerificationResult = {
    verificationId: report.runId,
    schemaVersion: VERIFICATION_RESULT_SCHEMA_VERSION,
    projectId: 'proj_' + report.runId.replace(/^ver_/, '').replace(/_.*$/, ''),
    taskId: report.taskId,
    sourceCommit,
    sourceTree,
    status: report.status,
    requiredSteps: report.steps.filter(s => s.required).length,
    stepResults: report.steps,
    startedAt: now,
    finishedAt: now,
    reportPath: mdPath,
    integrity: '', // filled by computeIntegrity below
  };

  // Compute integrity after all binding fields are set
  verificationResult.integrity = computeIntegrity(verificationResult);

  const jsonPath = saveVerificationResult(verificationResult, report.projectPath);

  return { mdPath, jsonPath };
}

// ============================================================
// Load
// ============================================================

/**
 * Load a structured verification result by verification ID (VER3-01).
 * Returns undefined if the JSON doesn't exist or is malformed.
 * Does NOT fall back to Markdown — JSON is the binding source of truth.
 */
export { loadVerificationResult } from './result.js';

// ============================================================
// Format Report (Markdown)
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
