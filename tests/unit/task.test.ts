/**
 * Harness OS — Task Manager Tests
 *
 * Coverage:
 * - State machine: valid/invalid transitions, terminal states, edge cases
 * - Task creation: ID, title normalization, type inference, file extraction
 * - Task completion: state update, file movement, summary generation
 * - Task linking: runs, contexts, checkpoints
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7
 *            11_ACCEPTANCE_CRITERIA.md §7
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { createProject } from '../../src/project/create.js';
import {
  transitionStatus,
  isValidTransition,
  isTerminal,
  isRecoverable,
  InvalidTransitionError,
  TERMINAL_STATUSES,
  ACTIVE_STATUSES,
} from '../../src/task/state-machine.js';
import {
  createTaskRecord,
  normalizeTitle,
  inferTaskType,
  extractExplicitRefs,
} from '../../src/task/create.js';
import {
  completeTask,
  failTask,
  updateTaskState,
} from '../../src/task/complete.js';

let testDir: string;
let projectPath: string;

beforeEach(async () => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-task-test-'));
  projectPath = join(testDir, 'test-proj');
  await createProject({ name: 'test-proj', path: projectPath });
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Helper
// ============================================================

async function createAndStart(instruction: string = 'Fix login bug'): Promise<string> {
  const record = await createTaskRecord({ projectPath, userInstruction: instruction });
  // Update JSON to 'running' for valid completion transition
  const jsonPath = record.jsonPath;
  const state = JSON.parse(readFileSync(jsonPath, 'utf-8'));
  state.status = 'running';
  writeFileSync(jsonPath, JSON.stringify(state, null, 2) + '\n', 'utf-8');
  return record.state.taskId;
}

// ============================================================
// State Machine Tests
// ============================================================

describe('state machine', () => {
  it('allows valid transitions', () => {
    expect(transitionStatus('created', 'ready')).toBe('ready');
    expect(transitionStatus('ready', 'running')).toBe('running');
    expect(transitionStatus('running', 'completed')).toBe('completed');
    expect(transitionStatus('running', 'blocked')).toBe('blocked');
    expect(transitionStatus('blocked', 'running')).toBe('running');
    expect(transitionStatus('running', 'failed')).toBe('failed');
    expect(transitionStatus('running', 'verifying')).toBe('verifying');
    expect(transitionStatus('verifying', 'completed')).toBe('completed');
  });

  it('rejects invalid transitions', () => {
    expect(() => transitionStatus('created', 'completed')).toThrow(InvalidTransitionError);
    expect(() => transitionStatus('completed', 'running')).toThrow(InvalidTransitionError);
    expect(() => transitionStatus('failed', 'running')).toThrow(InvalidTransitionError);
    expect(() => transitionStatus('ready', 'completed')).toThrow(InvalidTransitionError);
    expect(() => transitionStatus('created', 'running')).toThrow(InvalidTransitionError);
  });

  it('rejects transition from terminal states', () => {
    for (const terminal of TERMINAL_STATUSES) {
      expect(() => transitionStatus(terminal as any, 'running')).toThrow();
    }
  });

  it('isValidTransition returns boolean', () => {
    expect(isValidTransition('created', 'ready')).toBe(true);
    expect(isValidTransition('created', 'completed')).toBe(false);
    expect(isValidTransition('running', 'paused')).toBe(true);
    expect(isValidTransition('paused', 'running')).toBe(true);
    expect(isValidTransition('completed', 'running')).toBe(false);
    expect(isValidTransition('running', 'failed')).toBe(true);
    expect(isValidTransition('failed', 'running')).toBe(false);
  });

  it('identifies terminal states', () => {
    expect(isTerminal('completed')).toBe(true);
    expect(isTerminal('failed')).toBe(true);
    expect(isTerminal('running')).toBe(false);
    expect(isTerminal('created')).toBe(false);
  });

  it('identifies recoverable states', () => {
    expect(isRecoverable('paused')).toBe(true);
    expect(isRecoverable('blocked')).toBe(true);
    expect(isRecoverable('running')).toBe(true);
    expect(isRecoverable('completed')).toBe(false);
    expect(isRecoverable('failed')).toBe(false);
    expect(isRecoverable('created')).toBe(false);
  });

  it('all transitions from every state are valid', () => {
    const allStatuses = ['created', 'ready', 'running', 'blocked', 'paused', 'verifying', 'completed', 'failed'];
    for (const from of allStatuses) {
      for (const to of allStatuses) {
        if (isValidTransition(from as any, to as any)) {
          expect(() => transitionStatus(from as any, to as any)).not.toThrow();
        } else {
          expect(() => transitionStatus(from as any, to as any)).toThrow(InvalidTransitionError);
        }
      }
    }
  });
});

// ============================================================
// Task Creation Tests
// ============================================================

describe('createTaskRecord', () => {
  it('creates a task record with ID and initial state', async () => {
    const record = await createTaskRecord({
      projectPath,
      userInstruction: 'Fix the login button loading state',
    });

    expect(record.state.taskId).toMatch(/^task_/);
    expect(record.state.title).toBe('Fix the login button loading state');
    expect(record.state.type).toBe('bugfix');
    expect(record.state.status).toBe('created');
    expect(record.state.runIds).toEqual([]);
  });

  it('writes task record files to .project/tasks/active/', async () => {
    const record = await createTaskRecord({
      projectPath,
      userInstruction: 'Add new feature for user auth',
    });

    expect(existsSync(record.mdPath)).toBe(true);
    expect(existsSync(record.jsonPath)).toBe(true);

    const json = JSON.parse(readFileSync(record.jsonPath, 'utf-8'));
    expect(json.taskId).toBe(record.state.taskId);
    expect(json.status).toBe('created');

    const md = readFileSync(record.mdPath, 'utf-8');
    expect(md).toContain('Task: Add new feature for user auth');
    expect(md).toContain('## User Instruction');
    expect(md).toContain('## Changed Files');
  });

  it('increments task IDs', async () => {
    const r1 = await createTaskRecord({ projectPath, userInstruction: 'Task one' });
    const r2 = await createTaskRecord({ projectPath, userInstruction: 'Task two' });
    expect(r1.state.taskId).not.toBe(r2.state.taskId);
  });

  it('infers type from instruction', async () => {
    const r = await createTaskRecord({ projectPath, userInstruction: 'Refactor the database module' });
    expect(r.state.type).toBe('refactor');
  });

  it('supports explicit type override', async () => {
    const r = await createTaskRecord({ projectPath, userInstruction: 'Do something', taskType: 'docs' });
    expect(r.state.type).toBe('docs');
  });
});

// ============================================================
// Title Normalization Tests
// ============================================================

describe('normalizeTitle', () => {
  it('takes first sentence as title', () => {
    expect(normalizeTitle('Fix the login button. It has a loading state bug.')).toBe(
      'Fix the login button',
    );
  });

  it('truncates long titles to 80 chars', () => {
    const long = 'A'.repeat(200);
    const result = normalizeTitle(long);
    expect(result.length).toBeLessThanOrEqual(80);
  });

  it('capitalizes first letter', () => {
    expect(normalizeTitle('add new feature')).toBe('Add new feature');
  });

  it('handles empty string', () => {
    expect(normalizeTitle('')).toBe('Untitled task');
  });

  it('handles whitespace-only input', () => {
    expect(normalizeTitle('   ')).toBe('Untitled task');
  });
});

// ============================================================
// Type Inference Tests
// ============================================================

describe('inferTaskType', () => {
  it('infers feature type', () => {
    expect(inferTaskType('Implement user authentication')).toBe('feature');
    expect(inferTaskType('Add new API endpoint')).toBe('feature');
  });

  it('infers bugfix type', () => {
    expect(inferTaskType('Fix the login crash')).toBe('bugfix');
    expect(inferTaskType('Bug in payment processing')).toBe('bugfix');
  });

  it('infers refactor type', () => {
    expect(inferTaskType('Refactor the database layer')).toBe('refactor');
  });

  it('infers test type', () => {
    expect(inferTaskType('Add tests for auth module')).toBe('test');
  });

  it('infers docs type', () => {
    expect(inferTaskType('Update API documentation')).toBe('docs');
  });

  it('infers investigation type', () => {
    expect(inferTaskType('Investigate performance issue')).toBe('investigation');
  });

  it('infers delivery type', () => {
    expect(inferTaskType('Deploy to production')).toBe('delivery');
  });

  it('infers maintenance type', () => {
    expect(inferTaskType('Update dependencies')).toBe('maintenance');
  });

  it('returns unknown for generic input', () => {
    expect(inferTaskType('Do something')).toBe('unknown');
  });
});

// ============================================================
// Explicit Reference Extraction Tests
// ============================================================

describe('extractExplicitRefs', () => {
  it('extracts file paths with extensions', () => {
    const result = extractExplicitRefs('Fix the bug in src/index.ts');
    expect(result.files).toContain('src/index.ts');
  });

  it('extracts backtick commands', () => {
    const result = extractExplicitRefs('Run `pnpm test` to verify');
    expect(result.commands).toContain('pnpm test');
  });

  it('returns empty arrays when nothing found', () => {
    const result = extractExplicitRefs('Do something');
    expect(result.files).toEqual([]);
    expect(result.commands).toEqual([]);
  });

  it('extracts multiple files', () => {
    const result = extractExplicitRefs('Fix src/a.ts and src/b.ts');
    expect(result.files).toHaveLength(2);
  });
});

// ============================================================
// Task Completion Tests
// ============================================================

describe('completeTask', () => {
  it('completes a task and moves files to completed/', async () => {
    const taskId = await createAndStart();
    const result = await completeTask({
      projectPath,
      taskId,
      changedFiles: ['src/login.ts', 'tests/login.test.ts'],
      verificationStatus: 'passed',
    });

    expect(result.finalStatus).toBe('completed');
    expect(result.changedFiles).toContain('src/login.ts');

    // Files moved to completed/
    expect(existsSync(join(projectPath, '.project/tasks/completed', `${taskId}.md`))).toBe(true);
    expect(existsSync(join(projectPath, '.project/tasks/completed', `${taskId}.json`))).toBe(true);

    // Active files removed
    expect(existsSync(join(projectPath, '.project/tasks/active', `${taskId}.md`))).toBe(false);
    expect(existsSync(join(projectPath, '.project/tasks/active', `${taskId}.json`))).toBe(false);

    // Verify JSON
    const json = JSON.parse(readFileSync(join(projectPath, '.project/tasks/completed', `${taskId}.json`), 'utf-8'));
    expect(json.status).toBe('completed');
    expect(json.verification.status).toBe('passed');
  });

  it('throws error for unknown task', async () => {
    await expect(completeTask({ projectPath, taskId: 'task_nonexistent' })).rejects.toThrow('not found');
  });

  it('rejects invalid transition from created to completed', async () => {
    const record = await createTaskRecord({ projectPath, userInstruction: 'Fix bug' });
    await expect(completeTask({ projectPath, taskId: record.state.taskId, verificationStatus: 'passed' })).rejects.toThrow(
      'Invalid task status transition',
    );
  });

  // ---- VER-02/VER-03: Verification Gate ----
  it('rejects completion with non-passed verification status', async () => {
    const taskId = await createAndStart();
    await expect(completeTask({
      projectPath,
      taskId,
      verificationStatus: 'failed',
    })).rejects.toThrow('Cannot complete task');
  });

  it('rejects completion with partial verification status', async () => {
    const taskId = await createAndStart();
    await expect(completeTask({
      projectPath,
      taskId,
      verification: { id: 'ver_001', status: 'partial' },
    })).rejects.toThrow('Cannot complete task');
  });

  it('rejects completion with skipped verification status', async () => {
    const taskId = await createAndStart();
    await expect(completeTask({
      projectPath,
      taskId,
      verification: { id: 'ver_002', status: 'skipped' },
    })).rejects.toThrow('Cannot complete task');
  });

  it('accepts completion with VerificationRef passed status', async () => {
    const taskId = await createAndStart();
    const result = await completeTask({
      projectPath,
      taskId,
      changedFiles: ['src/main.ts'],
      verification: { id: 'ver_003', status: 'passed', reportPath: '.project/reports/verification/ver_003.md' },
    });
    expect(result.finalStatus).toBe('completed');
    expect(result.changedFiles).toContain('src/main.ts');
  });
});

// ============================================================
// Task Failure Tests
// ============================================================

describe('failTask', () => {
  it('fails a task and moves files to failed/', async () => {
    const taskId = await createAndStart();
    const result = await failTask({
      projectPath,
      taskId,
      failureReason: 'Verification failed: lint errors',
      recoveryHint: 'Run pnpm lint and fix errors',
    });

    expect(result.finalStatus).toBe('failed');
    expect(existsSync(join(projectPath, '.project/tasks/failed', `${taskId}.md`))).toBe(true);
    expect(existsSync(join(projectPath, '.project/tasks/failed', `${taskId}.json`))).toBe(true);

    const json = JSON.parse(readFileSync(join(projectPath, '.project/tasks/failed', `${taskId}.json`), 'utf-8'));
    expect(json.status).toBe('failed');
  });

  it('throws error for unknown task', async () => {
    await expect(failTask({ projectPath, taskId: 'task_nonexistent' })).rejects.toThrow('not found');
  });
});

// ============================================================
// Task Update Tests
// ============================================================

describe('updateTaskState', () => {
  it('updates task state with run/context/checkpoint links', async () => {
    const taskId = await createAndStart();

    const updated = updateTaskState({
      projectPath,
      taskId,
      runId: 'run_001',
      contextPackId: 'cp_001',
      checkpointId: 'ck_001',
      changedFiles: ['src/login.ts'],
      risks: ['May affect edge case'],
    });

    expect(updated).toBeDefined();
    expect(updated!.runIds).toContain('run_001');
    expect(updated!.contextPackIds).toContain('cp_001');
    expect(updated!.checkpointIds).toContain('ck_001');
    expect(updated!.changedFiles).toContain('src/login.ts');
    expect(updated!.risks).toContain('May affect edge case');
  });

  it('does not modify terminal tasks', async () => {
    const taskId = await createAndStart();
    await completeTask({ projectPath, taskId, verificationStatus: 'passed' });

    const updated = updateTaskState({ projectPath, taskId, runId: 'run_new' });
    // Terminal tasks should not be modified
    expect(updated?.status).toBe('completed');
    // runIds should NOT contain 'run_new' since the state is terminal
    expect(updated?.runIds).not.toContain('run_new');
  });

  it('accumulates multiple links', async () => {
    const taskId = await createAndStart();

    updateTaskState({ projectPath, taskId, runId: 'run_001' });
    updateTaskState({ projectPath, taskId, runId: 'run_002' });
    updateTaskState({ projectPath, taskId, contextPackId: 'cp_001' });
    const updated = updateTaskState({ projectPath, taskId, checkpointId: 'ck_001' });

    expect(updated!.runIds).toEqual(['run_001', 'run_002']);
    expect(updated!.contextPackIds).toEqual(['cp_001']);
    expect(updated!.checkpointIds).toEqual(['ck_001']);
  });

  it('returns undefined for unknown task', () => {
    const result = updateTaskState({ projectPath, taskId: 'task_nonexistent' });
    expect(result).toBeUndefined();
  });
});
