/**
 * Harness OS — Task Completion & Failure
 *
 * Phase 3.3: Complete or fail a task, move records, generate summaries.
 *
 * Flow:
 *   1. Collect changed files and run data
 *   2. Generate task summary
 *   3. Update task state JSON
 *   4. Move Markdown + JSON from active/ → completed/ or failed/
 *   5. Generate completion event data
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7.7-7.8
 */

import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import type { TaskState, TaskStatus } from '../types.js';
import { transitionStatus } from './state-machine.js';

// ============================================================
// Complete / Fail Types
// ============================================================

export interface CompleteTaskParams {
  projectPath: string;
  taskId: string;
  changedFiles?: string[];
  verificationStatus?: string;
  verificationReportPath?: string;
  risks?: string[];
  summary?: string;
}

export interface TaskCompletionResult {
  taskId: string;
  finalStatus: 'completed' | 'failed';
  summary: string;
  mdPath: string;
  jsonPath: string;
  changedFiles: string[];
  risks: string[];
}

// ============================================================
// Helper: Find task files
// ============================================================

function findTaskPath(projectPath: string, taskId: string): string | undefined {
  const dirs = ['active', 'completed', 'failed'];
  for (const dir of dirs) {
    const mdPath = join(projectPath, `.project/tasks/${dir}/${taskId}.md`);
    if (existsSync(mdPath)) return join(projectPath, `.project/tasks/${dir}`);
  }
  return undefined;
}

function readTaskState(projectPath: string, taskId: string): TaskState | undefined {
  // Try active first, then other dirs
  const dirs = ['active', 'completed', 'failed'];
  for (const dir of dirs) {
    const jsonPath = join(projectPath, `.project/tasks/${dir}/${taskId}.json`);
    if (existsSync(jsonPath)) {
      try {
        return JSON.parse(readFileSync(jsonPath, 'utf-8')) as TaskState;
      } catch {
        return undefined;
      }
    }
  }
  return undefined;
}

function ensureDir(dir: string): void {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

// ============================================================
// Complete Task
// ============================================================

/**
 * Mark a task as completed.
 *
 * Steps:
 *   1. Read current task state
 *   2. Transition status: current → completed
 *   3. Update state with changed files, verification, risks
 *   4. Write updated JSON
 *   5. Generate summary
 *   6. Move files from active/ → completed/
 *   7. Return completion result
 */
export async function completeTask(
  params: CompleteTaskParams,
): Promise<TaskCompletionResult> {
  const projectPath = resolve(params.projectPath);

  // 1. Read current state
  const state = readTaskState(projectPath, params.taskId);
  if (!state) {
    throw new Error(`Task not found: ${params.taskId}`);
  }

  // 2. Validate transition
  const newStatus: TaskStatus = 'completed';
  transitionStatus(state.status, newStatus);

  // 3. Prepare summary
  const summary = params.summary ?? generateDefaultSummary(state, params);

  // 4. Update state
  state.status = newStatus;
  state.changedFiles = params.changedFiles ?? state.changedFiles;
  state.verification = {
    status: params.verificationStatus ?? 'passed',
    reportPath: params.verificationReportPath,
  };
  state.risks = params.risks ?? state.risks;
  state.updatedAt = new Date().toISOString();

  // 5. Determine paths
  const activeDir = join(projectPath, '.project/tasks/active');
  const completedDir = join(projectPath, '.project/tasks/completed');
  ensureDir(completedDir);

  const activeMd = join(activeDir, `${params.taskId}.md`);
  const activeJson = join(activeDir, `${params.taskId}.json`);
  const completedMd = join(completedDir, `${params.taskId}.md`);
  const completedJson = join(completedDir, `${params.taskId}.json`);

  // 6. Write updated JSON
  writeFileSync(activeJson, JSON.stringify(state, null, 2) + '\n', 'utf-8');

  // 7. Replace markdown summary at the bottom
  if (existsSync(activeMd)) {
    let md = readFileSync(activeMd, 'utf-8');
    md = md.replace(/(## Final Summary\n\n).*/s, `$1${summary}`);

    // Update status line
    md = md.replace(/^(Status: ).*/m, `$1completed`);
    md = md.replace(/^(Updated At: ).*/m, `$1${state.updatedAt}`);

    // Update verification section
    md = md.replace(
      /(Status: ).*/,
      `Status: ${params.verificationStatus ?? 'passed'}`,
    );

    // Update changed files
    const filesSection = state.changedFiles.map(f => `- ${f}`).join('\n');
    md = md.replace(
      /(## Changed Files\n\n).*?(?=\n## |\n$)/s,
      `$1${filesSection || '(none)'}`,
    );

    writeFileSync(activeMd, md, 'utf-8');
  }

  // 8. Move files
  if (existsSync(activeMd)) renameSync(activeMd, completedMd);
  if (existsSync(activeJson)) renameSync(activeJson, completedJson);

  return {
    taskId: params.taskId,
    finalStatus: 'completed',
    summary,
    mdPath: completedMd,
    jsonPath: completedJson,
    changedFiles: state.changedFiles,
    risks: state.risks,
  };
}

// ============================================================
// Fail Task
// ============================================================

export interface FailTaskParams extends CompleteTaskParams {
  failureReason?: string;
  recoveryHint?: string;
}

/**
 * Mark a task as failed.
 * Similar to completeTask but moves to failed/ instead of completed/.
 */
export async function failTask(
  params: FailTaskParams,
): Promise<TaskCompletionResult> {
  const projectPath = resolve(params.projectPath);

  // 1. Read current state
  const state = readTaskState(projectPath, params.taskId);
  if (!state) {
    throw new Error(`Task not found: ${params.taskId}`);
  }

  // 2. Validate transition
  const newStatus: TaskStatus = 'failed';
  transitionStatus(state.status, newStatus);

  // 3. Prepare summary
  const failureMsg = params.failureReason ?? 'No failure reason recorded';
  const recoveryMsg = params.recoveryHint ? `\nRecovery: ${params.recoveryHint}` : '';
  const summary = params.summary ?? `Task failed.\n\nReason: ${failureMsg}${recoveryMsg}`;

  // 4. Update state
  state.status = newStatus;
  state.changedFiles = params.changedFiles ?? state.changedFiles;
  state.verification = {
    status: params.verificationStatus ?? 'failed',
    reportPath: params.verificationReportPath,
  };
  state.risks = params.risks ?? state.risks;
  state.updatedAt = new Date().toISOString();

  // 5. Determine paths
  const activeDir = join(projectPath, '.project/tasks/active');
  const failedDir = join(projectPath, '.project/tasks/failed');
  ensureDir(failedDir);

  const activeMd = join(activeDir, `${params.taskId}.md`);
  const activeJson = join(activeDir, `${params.taskId}.json`);
  const failedMd = join(failedDir, `${params.taskId}.md`);
  const failedJson = join(failedDir, `${params.taskId}.json`);

  // 6. Write updated JSON
  writeFileSync(activeJson, JSON.stringify(state, null, 2) + '\n', 'utf-8');

  // 7. Update markdown
  if (existsSync(activeMd)) {
    let md = readFileSync(activeMd, 'utf-8');
    md = md.replace(/^(Status: ).*/m, `$1failed`);
    md = md.replace(/^(Updated At: ).*/m, `$1${state.updatedAt}`);
    md = md.replace(/(## Final Summary\n\n).*/s, `$1${summary}`);

    // Add failure info section if not present
    if (!md.includes('## Failure Reason')) {
      md += `\n## Failure Reason\n\n${failureMsg}\n`;
      if (params.recoveryHint) md += `\n## Recovery\n\n${params.recoveryHint}\n`;
    }

    writeFileSync(activeMd, md, 'utf-8');
  }

  // 8. Move files
  if (existsSync(activeMd)) renameSync(activeMd, failedMd);
  if (existsSync(activeJson)) renameSync(activeJson, failedJson);

  return {
    taskId: params.taskId,
    finalStatus: 'failed',
    summary,
    mdPath: failedMd,
    jsonPath: failedJson,
    changedFiles: state.changedFiles,
    risks: state.risks,
  };
}

// ============================================================
// Update Task State (in-place, no status change)
// ============================================================

export interface UpdateTaskParams {
  projectPath: string;
  taskId: string;
  runId?: string;
  contextPackId?: string;
  checkpointId?: string;
  changedFiles?: string[];
  risks?: string[];
  verificationStatus?: string;
  verificationReportPath?: string;
}

/**
 * Update a task's state fields without changing status.
 * Skips terminal tasks (completed/failed).
 */
export function updateTaskState(params: UpdateTaskParams): TaskState | undefined {
  const projectPath = resolve(params.projectPath);
  const state = readTaskState(projectPath, params.taskId);
  if (!state) return undefined;

  // Don't update terminal tasks
  if (state.status === 'completed' || state.status === 'failed') return state;

  state.updatedAt = new Date().toISOString();

  // 1. Read current dir
  const activeDir = join(projectPath, '.project/tasks/active');
  const jsonPath = join(activeDir, `${params.taskId}.json`);

  // Link run
  if (params.runId && !state.runIds.includes(params.runId)) {
    state.runIds.push(params.runId);
  }

  // Link context pack
  if (params.contextPackId && !state.contextPackIds.includes(params.contextPackId)) {
    state.contextPackIds.push(params.contextPackId);
  }

  // Link checkpoint
  if (params.checkpointId && !state.checkpointIds.includes(params.checkpointId)) {
    state.checkpointIds.push(params.checkpointId);
  }

  // Update changed files
  if (params.changedFiles) {
    const existing = new Set(state.changedFiles);
    for (const f of params.changedFiles) existing.add(f);
    state.changedFiles = [...existing];
  }

  // Update risks
  if (params.risks) {
    const existing = new Set(state.risks);
    for (const r of params.risks) existing.add(r);
    state.risks = [...existing];
  }

  // Update verification
  if (params.verificationStatus) {
    state.verification.status = params.verificationStatus;
  }
  if (params.verificationReportPath) {
    state.verification.reportPath = params.verificationReportPath;
  }

  // Write updated JSON
  writeFileSync(jsonPath, JSON.stringify(state, null, 2) + '\n', 'utf-8');

  return state;
}

// ============================================================
// Default Summary Generator
// ============================================================

function generateDefaultSummary(state: TaskState, params: CompleteTaskParams): string {
  const parts: string[] = ['Task completed.\n'];
  if (params.changedFiles && params.changedFiles.length > 0) {
    parts.push(`Files changed: ${params.changedFiles.length}`);
  }
  parts.push(`Verification: ${params.verificationStatus ?? 'passed'}`);
  if (params.risks && params.risks.length > 0) {
    parts.push(`\nRisks:\n${params.risks.map(r => `- ${r}`).join('\n')}`);
  }
  return parts.join('\n');
}
