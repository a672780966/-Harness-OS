/**
 * Harness OS — Checkpoint
 *
 * Phase 9.2: Checkpoint creation, restoration, and rollback.
 *
 * Checkpoints record:
 *   - Git status (branch, changed files, diff)
 *   - Task state
 *   - Run state
 *   - Context summary
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7.8
 *            11_ACCEPTANCE_CRITERIA.md §15
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, resolve } from 'path';
import { execSync } from 'child_process';
import { simpleGit } from 'simple-git';
import type { Checkpoint } from '../types.js';

// ============================================================
// Generate Checkpoint ID
// ============================================================

let _cpCounter = 0;

function generateCheckpointId(): string {
  _cpCounter += 1;
  return `cp_${Date.now().toString(36)}_${_cpCounter.toString(36).padStart(4, '0')}`;
}

// ============================================================
// Create Checkpoint
// ============================================================

export interface CreateCheckpointParams {
  projectPath?: string;
  projectId?: string;
  taskId?: string;
  runId?: string;
  contextSummary?: string;
  lastSuccessfulStep?: string;
  description?: string;
}

/**
 * Create a checkpoint that captures git state and task metadata.
 */
export async function createCheckpoint(
  params: CreateCheckpointParams = {},
): Promise<Checkpoint> {
  const projectPath = resolve(params.projectPath || process.cwd());
  const git = simpleGit(projectPath);

  let gitStatus = '(git not available)';
  let currentBranch = 'unknown';
  let changedFiles: string[] = [];

  try {
    const isRepo = await git.checkIsRepo();
    if (isRepo) {
      const status = await git.status();
      gitStatus = status.files.map(f => `${f.working_dir} ${f.path}`).join('\n') || '(clean)';
      currentBranch = (await git.branch()).current || 'unknown';
      changedFiles = status.files.map(f => f.path);
    }
  } catch {
    gitStatus = '(git error)';
  }

  const checkpointId = generateCheckpointId();
  const now = new Date().toISOString();

  const checkpoint: Checkpoint = {
    id: checkpointId,
    projectId: params.projectId || '',
    taskId: params.taskId,
    runId: params.runId,
    gitStatus,
    currentBranch,
    changedFiles,
    contextSummary: params.contextSummary || '(no context)',
    lastSuccessfulStep: params.lastSuccessfulStep,
    createdAt: now,
  };

  // Save checkpoint file
  const checkpointDir = join(projectPath, '.project/checkpoints');
  if (!existsSync(checkpointDir)) {
    mkdirSync(checkpointDir, { recursive: true });
  }

  const filePath = join(checkpointDir, `${checkpointId}.json`);
  writeFileSync(filePath, JSON.stringify(checkpoint, null, 2) + '\n', 'utf-8');

  return checkpoint;
}

// ============================================================
// Load Checkpoint
// ============================================================

/**
 * Load a checkpoint by ID.
 */
export function loadCheckpoint(
  checkpointId: string,
  projectPath?: string,
): Checkpoint | undefined {
  const resolvedPath = resolve(projectPath || process.cwd());
  const filePath = join(resolvedPath, '.project/checkpoints', `${checkpointId}.json`);

  if (!existsSync(filePath)) return undefined;

  try {
    return JSON.parse(readFileSync(filePath, 'utf-8')) as Checkpoint;
  } catch {
    return undefined;
  }
}

// ============================================================
// List Checkpoints
// ============================================================

/**
 * List all checkpoints, sorted by creation time (newest first).
 */
export function listCheckpoints(projectPath?: string, limit: number = 10): Checkpoint[] {
  const resolvedPath = resolve(projectPath || process.cwd());
  const dir = join(resolvedPath, '.project/checkpoints');
  if (!existsSync(dir)) return [];

  return readdirSync(dir)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      try {
        return JSON.parse(readFileSync(join(dir, f), 'utf-8')) as Checkpoint;
      } catch {
        return null;
      }
    })
    .filter((c): c is Checkpoint => c !== null)
    .sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''))
    .slice(0, limit);
}

// ============================================================
// Rollback
// ============================================================

export interface RollbackResult {
  checkpointId: string;
  success: boolean;
  warnings: string[];
  branch: string;
}

/**
 * Rollback to a checkpoint.
 * Restores git state and returns checkpoint info.
 *
 * Note: This shows what to restore — actual `git checkout` / `git reset`
 * requires separate approval flow.
 */
export async function rollbackToCheckpoint(
  checkpointId: string,
  projectPath?: string,
): Promise<RollbackResult> {
  const resolvedPath = resolve(projectPath || process.cwd());
  const checkpoint = loadCheckpoint(checkpointId, resolvedPath);
  const warnings: string[] = [];

  if (!checkpoint) {
    return {
      checkpointId,
      success: false,
      warnings: [`Checkpoint not found: ${checkpointId}`],
      branch: 'unknown',
    };
  }

  let branch = 'unknown';
  try {
    const git = simpleGit(resolvedPath);
    const isRepo = await git.checkIsRepo();
    if (isRepo) {
      branch = (await git.branch()).current || 'unknown';
    }
  } catch {
    warnings.push('Failed to read git status');
  }

  // Verify we have git state to restore
  if (!checkpoint.currentBranch || checkpoint.currentBranch === 'unknown') {
    warnings.push('Checkpoint has no branch information');
  }

  if (checkpoint.changedFiles.length > 0) {
    warnings.push(
      `Checkpoint has ${checkpoint.changedFiles.length} changed file(s) that may need restoration`,
    );
  }

  return {
    checkpointId,
    success: true,
    warnings,
    branch,
  };
}
