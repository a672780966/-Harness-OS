/**
 * Harness OS — Project Open
 *
 * Phase 1.2: Open an existing Harness OS project.
 *
 * Flow:
 *   1. Validate path exists and is a Git repo
 *   2. Check AGENTS.md exists
 *   3. Check .project/ directory integrity
 *   4. Read and validate manifest.json
 *   5. Read project state files
 *   6. Refresh repository-map.md
 *   7. Read git status
 *   8. Output project open summary
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §6
 *            11_ACCEPTANCE_CRITERIA.md §5
 */

import { existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';
import { simpleGit } from 'simple-git';
import type { ProjectManifest } from '../types.js';
import { buildRepositoryMap } from './create.js';

// ============================================================
// Required .project/ directories
// ============================================================

const REQUIRED_PROJECT_DIRS = [
  '.project/state',
  '.project/tasks/active',
  '.project/tasks/completed',
  '.project/tasks/failed',
  '.project/decisions',
  '.project/reports/runs',
  '.project/reports/verification',
  '.project/reports/delivery',
  '.project/reports/events',
  '.project/checkpoints',
  '.project/sessions',
  '.project/context',
];

// ============================================================
// Open Result
// ============================================================

export interface OpenProjectResult {
  projectId: string;
  name: string;
  path: string;
  branch: string;
  ready: boolean;
  hasAgentsMd: boolean;
  hasManifest: boolean;
  projectDirsOk: boolean;
  hasUserChanges: boolean;
  warnings: string[];
}

// ============================================================
// Helper: read JSON safely
// ============================================================

function readJsonSafe<T>(path: string): { ok: true; data: T } | { ok: false; error: string } {
  try {
    if (!existsSync(path)) return { ok: false, error: `File not found: ${path}` };
    const content = readFileSync(path, 'utf-8');
    const data = JSON.parse(content) as T;
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: `Failed to parse ${path}: ${(err as Error).message}` };
  }
}

// ============================================================
// Open Project
// ============================================================

/**
 * Open an existing Harness OS project.
 *
 * @param projectPath - Path to the project directory
 * @returns Open result with readiness status and warnings
 */
export async function openProject(projectPath: string): Promise<OpenProjectResult> {
  const resolvedPath = resolve(projectPath);
  const warnings: string[] = [];

  // 1. Validate path exists (before initializing git)
  if (!existsSync(resolvedPath)) {
    return {
      projectId: '',
      name: '',
      path: resolvedPath,
      branch: '',
      ready: false,
      hasAgentsMd: false,
      hasManifest: false,
      projectDirsOk: false,
      hasUserChanges: false,
      warnings: [`Path does not exist: ${resolvedPath}`],
    };
  }

  const git = simpleGit(resolvedPath);

  // 2. Validate it's a Git repo
  const isRepo = await git.checkIsRepo();
  if (!isRepo) {
    return {
      projectId: '',
      name: '',
      path: resolvedPath,
      branch: '',
      ready: false,
      hasAgentsMd: false,
      hasManifest: false,
      projectDirsOk: false,
      hasUserChanges: false,
      warnings: [`Not a Git repository: ${resolvedPath}`],
    };
  }

  // 3. Check AGENTS.md
  const agentsMdPath = join(resolvedPath, 'AGENTS.md');
  const hasAgentsMd = existsSync(agentsMdPath);
  if (!hasAgentsMd) {
    warnings.push('AGENTS.md is missing — run `harness repair` or `harness init`');
  }

  // 4. Check .project/ integrity
  let projectDirsOk = true;
  for (const dir of REQUIRED_PROJECT_DIRS) {
    if (!existsSync(join(resolvedPath, dir))) {
      warnings.push(`Missing directory: ${dir} — run \`harness repair\``);
      projectDirsOk = false;
    }
  }

  // 5. Read manifest.json
  const manifestPath = join(resolvedPath, '.project/state/manifest.json');
  const manifestResult = readJsonSafe<ProjectManifest>(manifestPath);
  const hasManifest = manifestResult.ok;

  if (!manifestResult.ok) {
    warnings.push(`Project manifest issue: ${manifestResult.error}`);
  }

  // 6. Read git status
  let branch = 'unknown';
  let hasUserChanges = false;
  try {
    branch = (await git.branch()).current || 'unknown';
    const status = await git.status();
    hasUserChanges = status.files.length > 0;
  } catch {
    warnings.push('Failed to read git status');
  }

  // 7. Refresh repository-map.md
  try {
    const repoMap = buildRepositoryMap(resolvedPath);
    const repoMapLines = [
      '# Repository Map\n',
      '## Source Directories',
      ...(repoMap.sourceDirs.length > 0 ? repoMap.sourceDirs.map((d) => `- ${d}`) : ['- none detected']),
      '',
      '## Test Directories',
      ...(repoMap.testDirs.length > 0 ? repoMap.testDirs.map((d) => `- ${d}`) : ['- none detected']),
      '',
      '## Configuration Files',
      ...repoMap.configFiles.map((f) => `- ${f}`),
      '',
      '## Package Files',
      ...repoMap.packageFiles.map((f) => `- ${f}`),
    ];
    // Don't fail if we can't write
    try {
      const { writeFileSync } = await import('fs');
      writeFileSync(join(resolvedPath, '.project/state/repository-map.md'), repoMapLines.join('\n'), 'utf-8');
    } catch {
      // non-fatal
    }
  } catch {
    warnings.push('Failed to generate repository map');
  }

  // 8. Build result
  const ready = hasAgentsMd && hasManifest && projectDirsOk;

  return {
    projectId: manifestResult.ok ? manifestResult.data.projectId : '',
    name: manifestResult.ok ? manifestResult.data.projectName : resolvedPath.split(/[/\\]/).pop() || '',
    path: resolvedPath,
    branch,
    ready,
    hasAgentsMd,
    hasManifest,
    projectDirsOk,
    hasUserChanges,
    warnings,
  };
}
