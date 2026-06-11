/**
 * Harness OS — PR Body Generator
 *
 * Phase 8.3: Generate PR bodies with required sections.
 *
 * Required sections: Task / Summary / Changed Files / Verification / Risks
 *
 * Reference: 10_DELIVERY_PIPELINE.md §8, §13
 *            11_ACCEPTANCE_CRITERIA.md §14
 */

// ============================================================
// Types
// ============================================================

export interface PrBody {
  title: string;
  body: string;
}

export interface PrBodyInput {
  /** PR title (usually the commit message header). */
  title: string;
  /** Task title from task record. */
  taskTitle?: string;
  /** Task ID. */
  taskId?: string;
  /** Run ID. */
  runId?: string;
  /** Summary of changes (human-readable). */
  summary?: string;
  /** List of changed files. */
  changedFiles?: string[];
  /** Verification status. */
  verificationStatus?: string;
  /** Verification report path. */
  verificationReportPath?: string;
  /** Risk notes. */
  risks?: string[];
  /** Related decision IDs. */
  relatedDecisions?: string[];
  /** Follow-up items. */
  followUp?: string[];
}

// ============================================================
// Generate PR Body
// ============================================================

/**
 * Generate a PR body from task and verification data.
 */
export function generatePrBody(input: PrBodyInput): PrBody {
  const lines: string[] = [];

  // Title
  const title = input.title;

  // Summary section
  lines.push('## Summary', '');
  lines.push(input.summary || '(no summary provided)');
  lines.push('');

  // Task section
  lines.push('## Task', '');
  if (input.taskId) lines.push(`**ID:** ${input.taskId}`);
  if (input.taskTitle) lines.push(`**Title:** ${input.taskTitle}`);
  if (input.runId) lines.push(`**Run:** ${input.runId}`);
  lines.push('');

  // Changed Files
  lines.push('## Changed Files', '');
  if (input.changedFiles && input.changedFiles.length > 0) {
    for (const f of input.changedFiles) {
      lines.push(`- ${f}`);
    }
  } else {
    lines.push('(no file changes recorded)');
  }
  lines.push('');

  // Verification
  lines.push('## Verification', '');
  if (input.verificationStatus) {
    lines.push(`**Status:** ${input.verificationStatus.toUpperCase()}`);
    if (input.verificationReportPath) {
      lines.push(`**Report:** ${input.verificationReportPath}`);
    }
  } else {
    lines.push('(verification not run)');
  }
  lines.push('');

  // Risks
  if (input.risks && input.risks.length > 0) {
    lines.push('## Risks', '');
    for (const r of input.risks) lines.push(`- ${r}`);
    lines.push('');
  }

  // Related Decisions
  if (input.relatedDecisions && input.relatedDecisions.length > 0) {
    lines.push('## Related Decisions', '');
    for (const d of input.relatedDecisions) lines.push(`- ${d}`);
    lines.push('');
  }

  // Follow-up
  if (input.followUp && input.followUp.length > 0) {
    lines.push('## Follow-up', '');
    for (const f of input.followUp) lines.push(`- ${f}`);
    lines.push('');
  }

  return {
    title,
    body: lines.join('\n'),
  };
}
