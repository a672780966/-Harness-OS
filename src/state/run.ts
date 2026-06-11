/**
 * Harness OS — Run State
 *
 * Phase 9.1: Run lifecycle state — create, get, update, resume.
 *
 * Run state is stored as JSON files in .project/state/runs/ for portability
 * and can also be persisted in SqliteStore for query performance.
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7.6, §7.8
 *            11_ACCEPTANCE_CRITERIA.md §15
 */

import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';

// ============================================================
// Types
// ============================================================

export type RunStatus = 'running' | 'paused' | 'completed' | 'failed' | 'blocked';

export interface RunState {
  runId: string;
  projectId: string;
  taskId: string;
  sessionId?: string;
  status: RunStatus;
  startedAt: string;
  endedAt?: string;
  contextPackIds: string[];
  checkpointIds: string[];
  currentCheckpointId?: string;
  verificationResultId?: string;
  deliveryIds: string[];
  lastToolCall?: string;
  summary: string;
}

// ============================================================
// Run State Management
// ============================================================

let _runCounter = 0;

function generateRunId(): string {
  _runCounter += 1;
  return `run_${Date.now().toString(36)}_${_runCounter.toString(36).padStart(4, '0')}`;
}

/**
 * Create a new run state.
 */
export function createRunState(params: {
  projectId: string;
  taskId: string;
  sessionId?: string;
  runId?: string;
}): RunState {
  return {
    runId: params.runId ?? generateRunId(),
    projectId: params.projectId,
    taskId: params.taskId,
    sessionId: params.sessionId,
    status: 'running',
    startedAt: new Date().toISOString(),
    contextPackIds: [],
    checkpointIds: [],
    deliveryIds: [],
    summary: '',
  };
}

// ============================================================
// File Operations
// ============================================================

/**
 * Get the run state directory path.
 */
function getRunStateDir(projectPath: string): string {
  return join(resolve(projectPath), '.project/state/runs');
}

/**
 * Save run state to file.
 */
export function saveRunState(state: RunState, projectPath?: string): string {
  const resolvedPath = resolve(projectPath || process.cwd());
  const dir = getRunStateDir(resolvedPath);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  const filePath = join(dir, `${state.runId}.json`);
  writeFileSync(filePath, JSON.stringify(state, null, 2) + '\n', 'utf-8');
  return filePath;
}

/**
 * Load run state from file.
 */
export function loadRunState(runId: string, projectPath?: string): RunState | undefined {
  const resolvedPath = resolve(projectPath || process.cwd());
  const filePath = join(getRunStateDir(resolvedPath), `${runId}.json`);
  if (!existsSync(filePath)) return undefined;

  try {
    return JSON.parse(readFileSync(filePath, 'utf-8')) as RunState;
  } catch {
    return undefined;
  }
}

/**
 * Update run state fields in-place and save.
 */
export function updateRunState(
  runId: string,
  updates: Partial<RunState>,
  projectPath?: string,
): RunState | undefined {
  const state = loadRunState(runId, projectPath);
  if (!state) return undefined;

  Object.assign(state, updates);
  saveRunState(state, projectPath);
  return state;
}

/**
 * Pause a run.
 */
export function pauseRun(runId: string, projectPath?: string): RunState | undefined {
  return updateRunState(runId, { status: 'paused' }, projectPath);
}

/**
 * Complete a run.
 */
export function completeRun(runId: string, summary?: string, projectPath?: string): RunState | undefined {
  return updateRunState(runId, {
    status: 'completed',
    endedAt: new Date().toISOString(),
    summary: summary || 'Completed',
  }, projectPath);
}

/**
 * Fail a run.
 */
export function failRun(runId: string, summary?: string, projectPath?: string): RunState | undefined {
  return updateRunState(runId, {
    status: 'failed',
    endedAt: new Date().toISOString(),
    summary: summary || 'Failed',
  }, projectPath);
}

/**
 * List all run states, sorted by start time descending.
 */
export function listRunStates(projectPath?: string): RunState[] {
  const resolvedPath = resolve(projectPath || process.cwd());
  const dir = getRunStateDir(resolvedPath);
  if (!existsSync(dir)) return [];

  return readdirSync(dir)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      try {
        return JSON.parse(readFileSync(join(dir, f), 'utf-8')) as RunState;
      } catch {
        return null;
      }
    })
    .filter((r): r is RunState => r !== null)
    .sort((a, b) => (b.startedAt || '').localeCompare(a.startedAt || ''));
}

/**
 * Link a checkpoint to a run.
 */
export function linkCheckpointToRun(
  runId: string,
  checkpointId: string,
  projectPath?: string,
): RunState | undefined {
  const state = loadRunState(runId, projectPath);
  if (!state) return undefined;

  if (!state.checkpointIds.includes(checkpointId)) {
    state.checkpointIds.push(checkpointId);
  }
  state.currentCheckpointId = checkpointId;
  saveRunState(state, projectPath);
  return state;
}

/**
 * Link a context pack to a run.
 */
export function linkContextToRun(
  runId: string,
  contextPackId: string,
  projectPath?: string,
): RunState | undefined {
  const state = loadRunState(runId, projectPath);
  if (!state) return undefined;

  if (!state.contextPackIds.includes(contextPackId)) {
    state.contextPackIds.push(contextPackId);
  }
  saveRunState(state, projectPath);
  return state;
}
