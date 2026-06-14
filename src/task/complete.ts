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
 * VER3-02: completeTask() only accepts verificationId, which is loaded from
 * disk and validated against current project/task/run/commit bindings.
 * No caller-supplied string or in-memory object can override the persisted result.
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7.7-7.8
 *            03_VERIFICATION_DELIVERY_STRONG_BINDING_FIX.md §4
 */

import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import type { TaskState, TaskStatus } from '../types.js';
import { transitionStatus } from './state-machine.js';
import { loadVerificationResult, checkVerificationBinding } from '../verification/result.js';
import { safeWriteJson, redactText } from '../governance/redactor.js';

// ============================================================
// Verification Binding (VER3-01/VER3-02/VER3-03)
// ============================================================

// ============================================================
// Complete / Fail Types
// ============================================================

export interface CompleteTaskParams {
  projectPath: string;
  taskId: string;
  projectId?: string;
  runId?: string;
  changedFiles?: string[];
  /**
   * Verification result ID. Must reference a persisted structured result
   * on disk. Only status='passed' with matching bindings allows completion.
   * VER3-02: No more legacy verificationStatus string.
   */
  verificationId: string;
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
 * VER3-02 Gate:
 *   1. Load verification result JSON from disk (not caller memory)
 *   2. Validate integrity hash
 *   3. Validate projectId, taskId, runId match current bindings
 *   4. Validate sourceCommit / sourceTree match HEAD
 *   5. Only status=passed can complete the task
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
export async function completeTask(params: CompleteTaskParams): Promise<TaskCompletionResult> {
  const projectPath = resolve(params.projectPath);

  // 1. Read current state
  const state = readTaskState(projectPath, params.taskId);
  if (!state) {
    throw new Error(`Task not found: ${params.taskId}`);
  }

  // ---- VER3-02: Structured Verification Gate ----
  // Load from disk — caller-provided verificationId must reference a real
  // persisted JSON. In-memory objects or strings cannot form a passed.
  if (!params.verificationId) {
    throw new Error(`Cannot complete task: verificationId is required. ` + `[VER3-02 gate: missing verificationId]`);
  }

  const verResult = loadVerificationResult(projectPath, params.verificationId);
  if (!verResult) {
    throw new Error(
      `Cannot complete task: verification result "${params.verificationId}" not found on disk. ` +
        `Run verification first. [VER3-02 gate: result not found]`,
    );
  }

  // Validate bindings: projectId, taskId, runId, sourceCommit, sourceTree
  const bindingCheck = checkVerificationBinding(verResult, {
    projectId: params.projectId ?? state.projectId,
    taskId: params.taskId,
    runId: params.runId,
    projectPath,
  });

  if (!bindingCheck.valid) {
    throw new Error(
      `Cannot complete task: verification binding failed.\n` +
        bindingCheck.reasons.map((r) => `  - ${r}`).join('\n') +
        `\n[VER3-02 gate: binding mismatch]`,
    );
  }

  // Status gate: only "passed" allows completion
  if (verResult.status !== 'passed') {
    throw new Error(
      `Cannot complete task: verification status is "${verResult.status}". ` +
        `Only "passed" allows completion. Use failTask() for non-passed verifications. ` +
        `[VER3-02 gate: status=${verResult.status}]`,
    );
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
    status: 'passed',
    reportPath: verResult.reportPath,
    id: params.verificationId,
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
  safeWriteJson(activeJson, state, 2);

  // 7. Replace markdown summary at the bottom
  if (existsSync(activeMd)) {
    let md = readFileSync(activeMd, 'utf-8');
    md = md.replace(/(## Final Summary\n\n).*/s, `$1${summary}`);

    // Update status line
    md = md.replace(/^(Status: ).*/m, `$1completed`);
    md = md.replace(/^(Updated At: ).*/m, `$1${state.updatedAt}`);

    // Update verification section
    md = md.replace(/(Status: ).*/, `Status: passed`);

    // Update changed files
    const filesSection = state.changedFiles.map((f) => `- ${f}`).join('\n');
    md = md.replace(/(## Changed Files\n\n).*?(?=\n## |\n$)/s, `$1${filesSection || '(none)'}`);

    writeFileSync(activeMd, redactText(md), 'utf-8');
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

export interface FailTaskParams {
  projectPath: string;
  taskId: string;
  projectId?: string;
  runId?: string;
  changedFiles?: string[];
  verificationId?: string;
  failureReason?: string;
  recoveryHint?: string;
  risks?: string[];
  summary?: string;
}

/**
 * Mark a task as failed.
 * Similar to completeTask but moves to failed/ instead of completed/.
 *
 * VER3-03: Failed/blocked tasks record verification status but don't validate
 * bindings — the failure is recorded regardless.
 */
export async function failTask(params: FailTaskParams): Promise<TaskCompletionResult> {
  const projectPath = resolve(params.projectPath);

  // 1. Read current state
  const state = readTaskState(projectPath, params.taskId);
  if (!state) {
    throw new Error(`Task not found: ${params.taskId}`);
  }

  // 2. Validate transition
  const newStatus: TaskStatus = 'failed';
  transitionStatus(state.status, newStatus);

  // 3. Resolve verification for state record
  let effectiveVerStatus = 'failed';
  let verReportPath: string | undefined;
  if (params.verificationId) {
    const verResult = loadVerificationResult(projectPath, params.verificationId);
    if (verResult) {
      effectiveVerStatus = verResult.status;
      verReportPath = verResult.reportPath;
    }
  }

  // 3. Prepare summary
  const failureMsg = params.failureReason ?? 'No failure reason recorded';
  const recoveryMsg = params.recoveryHint ? `\nRecovery: ${params.recoveryHint}` : '';
  const summary = params.summary ?? `Task failed.\n\nReason: ${failureMsg}${recoveryMsg}`;

  // 4. Update state
  state.status = newStatus;
  state.changedFiles = params.changedFiles ?? state.changedFiles;
  state.verification = {
    status: effectiveVerStatus,
    reportPath: verReportPath,
    id: params.verificationId,
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
  safeWriteJson(activeJson, state, 2);

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

    writeFileSync(activeMd, redactText(md), 'utf-8');
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
  verificationId?: string;
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

  // Update verification reference
  if (params.verificationId) {
    state.verification.id = params.verificationId;
  }
  if (params.verificationReportPath) {
    state.verification.reportPath = params.verificationReportPath;
  }

  // Write updated JSON
  safeWriteJson(jsonPath, state, 2);

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
  parts.push(`Verification: passed (${params.verificationId})`);
  if (params.risks && params.risks.length > 0) {
    parts.push(`\nRisks:\n${params.risks.map((r) => `- ${r}`).join('\n')}`);
  }
  return parts.join('\n');
}
