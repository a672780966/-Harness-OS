/**
 * Harness OS — Task Manager Module
 *
 * Phase 3: Task lifecycle — create, start, pause, resume, block, complete, fail.
 *
 * Sub-modules:
 * - create.ts       — Task record creation, title normalization, type inference
 * - state-machine.ts — State transition validation
 * - complete.ts     — Task completion and failure flows
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7
 */

export {
  createTaskRecord,
  normalizeTitle,
  inferTaskType,
  extractExplicitRefs,
  type CreateTaskParams,
  type TaskRecord,
  type ExplicitRefs,
} from './create.js';

export {
  transitionStatus,
  isValidTransition,
  InvalidTransitionError,
  isTerminal,
  isRecoverable,
  getValidTransitions,
  getAllowedTargets,
  TERMINAL_STATUSES,
  ACTIVE_STATUSES,
  STALLED_STATUSES,
} from './state-machine.js';

export {
  completeTask,
  failTask,
  updateTaskState,
  type CompleteTaskParams,
  type FailTaskParams,
  type TaskCompletionResult,
  type UpdateTaskParams,
} from './complete.js';

// Legacy CLI entry points
import { type TaskStatus } from '../types.js';

export async function runTask(
  task: string,
  options?: { json?: boolean; quiet?: boolean },
): Promise<void> {
  const { createTaskRecord } = await import('./create.js');
  const record = await createTaskRecord({
    projectPath: process.cwd(),
    userInstruction: task,
  });

  console.log(`\nTask created: ${record.state.title}`);
  console.log(`Task ID: ${record.state.taskId}`);
  console.log(`Type: ${record.state.type}`);
  console.log(`Status: ${record.state.status}`);
  console.log(`\nRecord: ${record.mdPath}`);
  console.log(`\nNext:`);
  console.log(`  Context Pack will be built before execution.`);
}

export async function resumeRun(runId: string): Promise<void> {
  console.log(`Resuming run: ${runId}`);
  // TODO: Read run state, restore checkpoint, continue execution
}
