/**
 * Harness OS — Task State Machine
 *
 * Phase 3.2: Task lifecycle state transitions.
 *
 * State graph (06_TASK_DECISION_PROJECT_MANAGER.md §7.2):
 *
 *   created ──► ready ──► running ──► blocked ──► running
 *                           │  ▲          │
 *                           │  └── paused ─┘
 *                           │
 *                           ├──► verifying ──► completed
 *                           └──► failed
 *
 * All states can transition to "failed" except completed/failed.
 */

import type { TaskStatus } from '../types.js';

// ============================================================
// Valid Transitions
// ============================================================

const VALID_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  'created':    ['ready', 'failed'],
  'ready':      ['running', 'failed'],
  'running':    ['blocked', 'paused', 'verifying', 'completed', 'failed'],
  'blocked':    ['running', 'failed'],
  'paused':     ['running', 'failed'],
  'verifying':  ['completed', 'running', 'failed'],
  'completed':  [],
  'failed':     [],
};

// ============================================================
// Transition Error
// ============================================================

export class InvalidTransitionError extends Error {
  constructor(from: TaskStatus, to: TaskStatus) {
    super(`Invalid task status transition: ${from} → ${to}`);
    this.name = 'InvalidTransitionError';
  }
}

// ============================================================
// isValidTransition
// ============================================================

/**
 * Check if a status transition is valid.
 */
export function isValidTransition(from: TaskStatus, to: TaskStatus): boolean {
  return VALID_TRANSITIONS[from]?.includes(to) ?? false;
}

// ============================================================
// transitionStatus
// ============================================================

/**
 * Attempt to transition a task status.
 * Throws InvalidTransitionError if the transition is not allowed.
 *
 * @returns The new status on success.
 */
export function transitionStatus(
  current: TaskStatus,
  target: TaskStatus,
): TaskStatus {
  if (!isValidTransition(current, target)) {
    throw new InvalidTransitionError(current, target);
  }
  return target;
}

// ============================================================
// Terminal States
// ============================================================

/** States that cannot be transitioned away from. */
export const TERMINAL_STATUSES: TaskStatus[] = ['completed', 'failed'];

/** States that indicate the task is actively executing. */
export const ACTIVE_STATUSES: TaskStatus[] = ['running', 'verifying'];

/** States that indicate the task is not progressing. */
export const STALLED_STATUSES: TaskStatus[] = ['blocked', 'paused'];

/**
 * Returns true if the status is a terminal state (completed or failed).
 */
export function isTerminal(status: TaskStatus): boolean {
  return TERMINAL_STATUSES.includes(status);
}

/**
 * Returns true if the status is recoverable (can be resumed).
 */
export function isRecoverable(status: TaskStatus): boolean {
  return !isTerminal(status) && status !== 'created';
}

// ============================================================
// Transition Table (for reporting/debugging)
// ============================================================

export function getValidTransitions(status: TaskStatus): TaskStatus[] {
  return VALID_TRANSITIONS[status] ?? [];
}

export function getAllowedTargets(status: TaskStatus): string {
  const targets = getValidTransitions(status);
  if (targets.length === 0) return '(none — terminal)';
  return targets.join(', ');
}
