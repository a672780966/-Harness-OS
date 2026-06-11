/**
 * Harness OS — Commit Message Generator
 *
 * Phase 8.2: Generate Conventional Commit messages from task summary + diff.
 *
 * Format: <type>(<scope>): <summary>
 *
 * Reference: 10_DELIVERY_PIPELINE.md §8, §12
 */

// ============================================================
// Types
// ============================================================

export type CommitType = 'feat' | 'fix' | 'refactor' | 'test' | 'docs' | 'chore' | 'build' | 'ci' | 'perf' | 'revert';

export interface CommitMessage {
  type: CommitType;
  scope?: string;
  summary: string;
  body?: string;
  footer?: string;
  full: string;
}

// ============================================================
// Map task type to commit type
// ============================================================

const TASK_TYPE_MAP: Record<string, CommitType> = {
  feature: 'feat',
  bugfix: 'fix',
  refactor: 'refactor',
  test: 'test',
  docs: 'docs',
  maintenance: 'chore',
  delivery: 'chore',
  investigation: 'chore',
};

/**
 * Map a task type string to a Conventional Commit type.
 */
export function taskTypeToCommitType(taskType: string): CommitType {
  return TASK_TYPE_MAP[taskType] ?? 'chore';
}

// ============================================================
// Generate commit message
// ============================================================

export interface CommitMessageInput {
  /** Task type (feature, bugfix, refactor, etc). */
  taskType?: string;
  /** Task title / summary. */
  taskSummary: string;
  /** Optional scope (module, component). */
  scope?: string;
  /** Optional detailed body. */
  details?: string;
  /** Optional footer (e.g. "Closes #123"). */
  footer?: string;
}

/**
 * Generate a Conventional Commit message.
 */
export function generateCommitMessage(input: CommitMessageInput): CommitMessage {
  const type = input.taskType
    ? taskTypeToCommitType(input.taskType)
    : 'chore';

  const summary = input.taskSummary.trim();

  // Build full message
  const header = input.scope
    ? `${type}(${input.scope}): ${summary}`
    : `${type}: ${summary}`;

  const body = input.details?.trim();
  const footer = input.footer?.trim();

  const parts = [header];
  if (body) parts.push('', body);
  if (footer) parts.push('', footer);

  return {
    type,
    scope: input.scope,
    summary,
    body,
    footer,
    full: parts.join('\n'),
  };
}

/**
 * Generate a commit message from task data.
 */
export function generateCommitFromTask(params: {
  taskTitle: string;
  taskType?: string;
  changedFiles?: string[];
  runId?: string;
}): CommitMessage {
  const details = params.changedFiles && params.changedFiles.length > 0
    ? `Changed files:\n${params.changedFiles.map(f => `- ${f}`).join('\n')}`
    : undefined;

  const footer = params.runId
    ? `Run: ${params.runId}`
    : undefined;

  return generateCommitMessage({
    taskType: params.taskType,
    taskSummary: params.taskTitle,
    details,
    footer,
  });
}
