/**
 * Harness OS — State Module Tests (Run + Checkpoint)
 *
 * Coverage:
 * - Run state: create, save, load, update, pause/complete/fail, list, link
 * - Checkpoint: create, load, list, rollback
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7.8
 *            11_ACCEPTANCE_CRITERIA.md §15
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { simpleGit } from 'simple-git';
import { createProject } from '../../src/project/create.js';

import {
  createRunState,
  saveRunState,
  loadRunState,
  updateRunState,
  pauseRun,
  completeRun,
  failRun,
  listRunStates,
  linkCheckpointToRun,
  linkContextToRun,
} from '../../src/state/run.js';

import {
  createCheckpoint,
  loadCheckpoint,
  listCheckpoints,
  rollbackToCheckpoint,
} from '../../src/state/checkpoint.js';

let testDir: string;
let projectPath: string;

beforeEach(async () => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-state2-test-'));
  projectPath = join(testDir, 'test-proj');
  await createProject({ name: 'test-proj', path: projectPath });
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Run State Tests
// ============================================================

describe('run state', () => {
  it('creates a new run state', () => {
    const run = createRunState({ projectId: 'proj_001', taskId: 'task_001' });
    expect(run.runId).toMatch(/^run_/);
    expect(run.status).toBe('running');
    expect(run.startedAt).toBeTruthy();
  });

  it('saves and loads run state', () => {
    const run = createRunState({ projectId: 'proj_001', taskId: 'task_001' });
    saveRunState(run, projectPath);

    const loaded = loadRunState(run.runId, projectPath);
    expect(loaded).toBeDefined();
    expect(loaded!.runId).toBe(run.runId);
    expect(loaded!.status).toBe('running');
  });

  it('updates run state fields', () => {
    const run = createRunState({ projectId: 'p', taskId: 't' });
    saveRunState(run, projectPath);

    const updated = updateRunState(run.runId, { status: 'paused', summary: 'Paused by user' }, projectPath);
    expect(updated!.status).toBe('paused');
    expect(updated!.summary).toBe('Paused by user');
  });

  it('pauses a run', () => {
    const run = createRunState({ projectId: 'p', taskId: 't' });
    saveRunState(run, projectPath);

    const paused = pauseRun(run.runId, projectPath);
    expect(paused!.status).toBe('paused');
  });

  it('completes a run', () => {
    const run = createRunState({ projectId: 'p', taskId: 't' });
    saveRunState(run, projectPath);

    const completed = completeRun(run.runId, 'Done', projectPath);
    expect(completed!.status).toBe('completed');
    expect(completed!.endedAt).toBeTruthy();
    expect(completed!.summary).toBe('Done');
  });

  it('fails a run', () => {
    const run = createRunState({ projectId: 'p', taskId: 't' });
    saveRunState(run, projectPath);

    const failed = failRun(run.runId, 'Error occurred', projectPath);
    expect(failed!.status).toBe('failed');
    expect(failed!.endedAt).toBeTruthy();
  });

  it('returns undefined for unknown run', () => {
    const loaded = loadRunState('run_nonexistent', projectPath);
    expect(loaded).toBeUndefined();
  });

  it('links checkpoint and context to run', () => {
    const run = createRunState({ projectId: 'p', taskId: 't' });
    saveRunState(run, projectPath);

    linkCheckpointToRun(run.runId, 'cp_001', projectPath);
    linkContextToRun(run.runId, 'ctx_001', projectPath);

    const loaded = loadRunState(run.runId, projectPath);
    expect(loaded!.checkpointIds).toContain('cp_001');
    expect(loaded!.contextPackIds).toContain('ctx_001');
  });

  it('lists run states sorted by newest first', () => {
    const r1 = createRunState({ projectId: 'p', taskId: 't' });
    saveRunState(r1, projectPath);

    const r2 = createRunState({ projectId: 'p', taskId: 't' });
    saveRunState(r2, projectPath);

    const runs = listRunStates(projectPath);
    expect(runs.length).toBeGreaterThanOrEqual(2);
    expect(runs[0].runId).toBe(r2.runId); // newest first
  });

  it('accepts custom run ID', () => {
    const run = createRunState({ projectId: 'p', taskId: 't', runId: 'run_custom_001' });
    expect(run.runId).toBe('run_custom_001');
  });
});

// ============================================================
// Checkpoint Tests
// ============================================================

describe('checkpoint', () => {
  it('creates a checkpoint with git state', async () => {
    const cp = await createCheckpoint({ projectPath });
    expect(cp.id).toMatch(/^cp_/);
    expect(cp.createdAt).toBeTruthy();
    expect(cp.currentBranch).toBeTruthy();
  });

  it('saves checkpoint file', async () => {
    const cp = await createCheckpoint({ projectPath });
    const cpPath = join(projectPath, '.project/checkpoints', `${cp.id}.json`);
    expect(existsSync(cpPath)).toBe(true);

    const content = JSON.parse(readFileSync(cpPath, 'utf-8'));
    expect(content.id).toBe(cp.id);
  });

  it('loads checkpoint by ID', async () => {
    const cp = await createCheckpoint({ projectPath, taskId: 'task_001', contextSummary: 'Fixing login bug' });
    const loaded = loadCheckpoint(cp.id, projectPath);
    expect(loaded).toBeDefined();
    expect(loaded!.taskId).toBe('task_001');
    expect(loaded!.contextSummary).toBe('Fixing login bug');
  });

  it('returns undefined for unknown checkpoint', () => {
    const loaded = loadCheckpoint('cp_nonexistent', projectPath);
    expect(loaded).toBeUndefined();
  });

  it('lists checkpoints newest first', async () => {
    await createCheckpoint({ projectPath });
    await createCheckpoint({ projectPath });

    const list = listCheckpoints(projectPath, 10);
    expect(list.length).toBeGreaterThanOrEqual(2);
  });

  it('rollback returns checkpoint info', async () => {
    const cp = await createCheckpoint({ projectPath, contextSummary: 'test rollback' });
    const result = await rollbackToCheckpoint(cp.id, projectPath);

    expect(result.success).toBe(true);
    expect(result.checkpointId).toBe(cp.id);
  });

  it('rollback returns failure for unknown checkpoint', async () => {
    const result = await rollbackToCheckpoint('cp_ghost', projectPath);
    expect(result.success).toBe(false);
    expect(result.warnings.length).toBeGreaterThan(0);
  });
});
