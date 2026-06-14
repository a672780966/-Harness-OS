/**
 * Harness OS — Run Report
 *
 * Phase 7.3: Generate run reports at .project/reports/runs/<run-id>.md.
 *
 * Contains: Task, Context Used, Skill Calls, Changes, Verification, Risks, Next Steps.
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §15-19
 */

import { existsSync, mkdirSync, readFileSync } from 'fs';
import { join, resolve } from 'path';
import type { RunTrace } from './trace.js';
import { redactObject, redactText, safeWriteText } from '../governance/redactor.js';

// ============================================================
// Run Report Types
// ============================================================

export interface RunReport {
  runId: string;
  projectId: string;
  taskId?: string;
  sessionId?: string;
  title: string;
  status: string;
  startedAt: string;
  endedAt?: string;
  durationMs?: number;
  summary: string;

  /** Context information. */
  contextUsed?: string[];
  contextExcluded?: string[];
  contextRisks?: string[];

  /** Tool and skill calls. */
  toolCalls?: Array<{ tool: string; count: number }>;

  /** File changes. */
  changedFiles?: string[];

  /** Verification. */
  verificationStatus?: string;
  verificationReportPath?: string;

  /** Approval events. */
  approvals?: Array<{ action: string; status: string }>;

  /** Risk notes. */
  risks?: string[];

  /** Follow-up items. */
  followUp?: string[];

  /** Report file path (set after save). */
  reportPath?: string;
}

// ============================================================
// Generate
// ============================================================

/**
 * Generate a run report from a trace and optional metadata.
 */
export function generateRunReport(
  trace: RunTrace,
  overrides?: Partial<RunReport>,
): RunReport {
  const now = new Date().toISOString();
  const startTime = trace.startedAt;
  const endTime = trace.endedAt || now;
  const durationMs = new Date(endTime).getTime() - new Date(startTime).getTime();

  return {
    runId: trace.runId,
    projectId: trace.projectId,
    taskId: trace.taskId,
    sessionId: trace.sessionId,
    title: overrides?.title ?? `Run ${trace.runId}`,
    status: trace.status,
    startedAt: trace.startedAt,
    endedAt: trace.endedAt,
    durationMs,
    summary: redactText(trace.summary || '(no summary)'),
    contextUsed: overrides?.contextUsed,
    contextExcluded: overrides?.contextExcluded,
    contextRisks: overrides?.contextRisks,
    toolCalls: trace.toolCallCount > 0 ? [{ tool: 'total', count: trace.toolCallCount }] : [],
    changedFiles: overrides?.changedFiles,
    verificationStatus: overrides?.verificationStatus,
    verificationReportPath: overrides?.verificationReportPath,
    approvals: overrides?.approvals,
    risks: overrides?.risks,
    followUp: overrides?.followUp,
    reportPath: overrides?.reportPath,
  };
}

// ============================================================
// Save
// ============================================================

/**
 * Save a run report to .project/reports/runs/<run-id>.md.
 */
export function saveRunReport(
  report: RunReport,
  projectPath?: string,
): string {
  const resolvedPath = resolve(projectPath || process.cwd());
  const reportsDir = join(resolvedPath, '.project/reports/runs');
  if (!existsSync(reportsDir)) {
    mkdirSync(reportsDir, { recursive: true });
  }

  const reportPath = join(reportsDir, `${report.runId}.md`);

  // Redact sensitive fields before formatting (SEC-06)
  const safeReport = redactObject(report) as RunReport;

  const content = formatRunReport(safeReport);
  safeWriteText(reportPath, content);

  report.reportPath = reportPath;
  return reportPath;
}

// ============================================================
// Format
// ============================================================

/**
 * Format a run report as Markdown.
 */
function formatRunReport(report: RunReport): string {
  const lines = [
    `# Run Report: ${report.runId}`,
    '',
    `**Task:** ${report.taskId ?? '(no task)'}`,
    `**Status:** ${report.status.toUpperCase()}`,
    `**Started:** ${report.startedAt}`,
    report.endedAt ? `**Ended:** ${report.endedAt}` : '',
    report.durationMs ? `**Duration:** ${(report.durationMs / 1000).toFixed(1)}s` : '',
    '',
    '## Summary',
    '',
    report.summary || '(no summary)',
    '',
  ];

  // Context Used
  if (report.contextUsed && report.contextUsed.length > 0) {
    lines.push('## Context Used', '');
    for (const item of report.contextUsed) lines.push(`- ${item}`);
    lines.push('');
  }

  // Changes
  if (report.changedFiles && report.changedFiles.length > 0) {
    lines.push('## Changed Files', '');
    for (const f of report.changedFiles) lines.push(`- ${f}`);
    lines.push('');
  } else {
    lines.push('## Changed Files', '', '(none)', '');
  }

  // Tool Calls
  if (report.toolCalls && report.toolCalls.length > 0) {
    lines.push('## Tool Calls', '');
    for (const tc of report.toolCalls) {
      lines.push(`- ${tc.tool}: ${tc.count}`);
    }
    lines.push('');
  }

  // Verification
  if (report.verificationStatus) {
    lines.push('## Verification', '');
    lines.push(`**Status:** ${report.verificationStatus.toUpperCase()}`);
    if (report.verificationReportPath) {
      lines.push(`**Report:** ${report.verificationReportPath}`);
    }
    lines.push('');
  }

  // Approvals
  if (report.approvals && report.approvals.length > 0) {
    lines.push('## Approval Events', '');
    for (const a of report.approvals) {
      lines.push(`- ${a.action}: ${a.status}`);
    }
    lines.push('');
  }

  // Risks
  if (report.risks && report.risks.length > 0) {
    lines.push('## Risks', '');
    for (const r of report.risks) lines.push(`- ${r}`);
    lines.push('');
  }

  // Follow-up
  if (report.followUp && report.followUp.length > 0) {
    lines.push('## Follow-up', '');
    for (const f of report.followUp) lines.push(`- ${f}`);
    lines.push('');
  }

  return lines.filter(l => l !== undefined).join('\n');
}

// ============================================================
// Read
// ============================================================

/**
 * Load a run report from disk.
 */
export function loadRunReport(runId: string, projectPath?: string): string | undefined {
  const resolvedPath = resolve(projectPath || process.cwd());
  const reportPath = join(resolvedPath, '.project/reports/runs', `${runId}.md`);
  if (!existsSync(reportPath)) return undefined;

  try {
    return readFileSync(reportPath, 'utf-8');
  } catch {
    return undefined;
  }
}
