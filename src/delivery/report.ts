/**
 * Harness OS — Delivery Report
 *
 * Phase 8.4: Generate and save delivery reports.
 *
 * Output: .project/reports/delivery/<delivery-id>.md
 *
 * Reference: 10_DELIVERY_PIPELINE.md §15
 */

import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import type { CommitMessage } from './commit.js';
import type { PrBody } from './pr.js';
import type { GuardResult } from './guard.js';
import { redactText } from '../governance/redactor.js';

// ============================================================
// Types
// ============================================================

export type DeliveryType = 'commit' | 'pull-request' | 'release' | 'deploy' | 'rollback';
export type DeliveryStatus = 'planned' | 'guarded' | 'ready' | 'committed' | 'pull-requested' | 'released' | 'deployed' | 'completed' | 'blocked' | 'failed';

export interface DeliveryReport {
  deliveryId: string;
  projectId: string;
  taskId?: string;
  runId?: string;
  type: DeliveryType;
  status: DeliveryStatus;
  createdAt: string;
  commitMessage?: CommitMessage;
  prBody?: PrBody;
  guardResult?: GuardResult;
  summary: string;
  reportPath?: string;
}

// ============================================================
// Generate Report
// ============================================================

/**
 * Generate a delivery report.
 */
export function generateDeliveryReport(params: {
  deliveryId: string;
  projectId: string;
  type: DeliveryType;
  taskId?: string;
  runId?: string;
  commitMessage?: CommitMessage;
  prBody?: PrBody;
  guardResult?: GuardResult;
  summary?: string;
}): DeliveryReport {
  return {
    deliveryId: params.deliveryId,
    projectId: params.projectId,
    taskId: params.taskId,
    runId: params.runId,
    type: params.type,
    status: params.guardResult === undefined
      ? 'ready'
      : params.guardResult.canProceed ? 'ready' : 'blocked',
    createdAt: new Date().toISOString(),
    commitMessage: params.commitMessage,
    prBody: params.prBody,
    guardResult: params.guardResult,
    summary: params.summary ?? `${params.type} delivery`,
  };
}

// ============================================================
// Save Report
// ============================================================

/**
 * Save a delivery report to .project/reports/delivery/<delivery-id>.md
 */
export function saveDeliveryReport(
  report: DeliveryReport,
  projectPath?: string,
): string {
  const resolvedPath = resolve(projectPath || process.cwd());
  const reportDir = join(resolvedPath, '.project/reports/delivery');
  if (!existsSync(reportDir)) {
    mkdirSync(reportDir, { recursive: true });
  }

  const reportPath = join(reportDir, `${report.deliveryId}.md`);
  const content = formatDeliveryReport(report);
  writeFileSync(reportPath, content, 'utf-8');
  report.reportPath = reportPath;

  return reportPath;
}

// ============================================================
// Format
// ============================================================

/**
 * Format a delivery report as Markdown.
 */
function formatDeliveryReport(report: DeliveryReport): string {
  const lines = [
    `# Delivery Report: ${report.deliveryId}`,
    '',
    `**Type:** ${report.type}`,
    `**Status:** ${report.status.toUpperCase()}`,
    `**Date:** ${report.createdAt}`,
    report.taskId ? `**Task:** ${report.taskId}` : '',
    report.runId ? `**Run:** ${report.runId}` : '',
    '',
    '## Summary',
    '',
    report.summary,
    '',
  ];

  // Commit message
  if (report.commitMessage) {
    lines.push('## Commit Message', '', '```', redactText(report.commitMessage.full), '```', '');
  }

  // PR body
  if (report.prBody) {
    lines.push('## PR Body', '', redactText(report.prBody.body), '');
  }

  // Guard results
  if (report.guardResult) {
    lines.push('## Delivery Guard', '');
    for (const check of report.guardResult.checks) {
      const icon = check.passed ? '✅' : '❌';
      lines.push(`${icon} ${check.check}: ${redactText(check.reason)}`);
    }
    lines.push('');
  }

  // Blocked reasons
  if (report.status === 'blocked' && report.guardResult) {
    lines.push('## Blocked By', '');
    for (const b of report.guardResult.blockedBy) {
      lines.push(`- ${redactText(b)}`);
    }
    lines.push('');
  }

  return lines.filter(l => l !== undefined).join('\n');
}
