/**
 * Harness OS — Context Source Collectors
 *
 * Phase 4.1: Collect source data from the project workspace for context building.
 *
 * Collectors:
 * - collectAgentsMd()  — Extract rules from AGENTS.md
 * - collectProject()   — Read project.md + manifest.json
 * - collectGit()       — Read git status/diff/log via simple-git
 * - collectTask()      — Read current active task record
 *
 * Reference: 05_CONTEXT_ENGINEERING.md §5, §7
 */

import { existsSync, readFileSync, readdirSync } from 'fs';
import { join, resolve } from 'path';
import { simpleGit } from 'simple-git';
import type { RuleContext, ProjectContext, GitContext, TaskContext, TaskType } from '../types.js';

// ============================================================
// AGENTS.md Collector
// ============================================================

/**
 * Extract rule sections from AGENTS.md.
 * Looks for ## N. Section headings and captures content below them.
 */
export function collectAgentsMd(projectPath: string): RuleContext {
  const agentsMdPath = join(projectPath, 'AGENTS.md');
  const rules: RuleContext = {
    source: 'AGENTS.md',
    architectureRules: [],
    codingRules: [],
    testingRules: [],
    securityRules: [],
    deliveryRules: [],
    forbiddenPatterns: [],
  };

  if (!existsSync(agentsMdPath)) return rules;

  const content = readFileSync(agentsMdPath, 'utf-8');

  // Extract section content using regex
  const sectionRegex = /^##\s+\d*\.?\s*(.+)$([\s\S]*?)(?=^##\s|\Z)/gm;
  let match: RegExpExecArray | null;
  while ((match = sectionRegex.exec(content)) !== null) {
    const title = match[1].trim().toLowerCase();
    const body = match[2].trim();
    const lines = body
      .split('\n')
      .map((l) => l.replace(/^[-*]\s*/, '').trim())
      .filter(Boolean);

    if (title.includes('architecture')) {
      rules.architectureRules = lines;
    } else if (title.includes('coding')) {
      rules.codingRules = lines;
    } else if (title.includes('testing') || title.includes('verification')) {
      rules.testingRules = lines;
    } else if (title.includes('security')) {
      rules.securityRules = lines;
    } else if (title.includes('delivery') || title.includes('git and delivery')) {
      rules.deliveryRules = lines;
    } else if (title.includes('forbidden') || title.includes('not')) {
      rules.forbiddenPatterns = lines;
    }
  }

  return rules;
}

// ============================================================
// Project State Collector
// ============================================================

/**
 * Read project state from manifest.json and project.md.
 */
export function collectProject(projectPath: string): ProjectContext {
  const manifestPath = join(projectPath, '.project/state/manifest.json');
  const projectMdPath = join(projectPath, '.project/state/project.md');

  let name = projectPath.split(/[/\\]/).pop() || 'unnamed';
  let type = 'unknown';
  let primaryLanguage = 'unknown';
  let runtimeStr = 'unknown';
  let packageManager: string | undefined;
  let techStackSummary: string | undefined;

  // Read manifest
  if (existsSync(manifestPath)) {
    try {
      const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
      name = manifest.projectName || name;
      type = manifest.projectType || type;
      primaryLanguage = manifest.language?.primary || 'unknown';
      runtimeStr = manifest.runtime?.name || 'unknown';
      packageManager = manifest.packageManager?.name;

      // Build tech stack summary from manifest commands
      const cmds = manifest.commands || {};
      const available = Object.entries(cmds)
        .filter(([, v]) => v)
        .map(([k]) => k);
      if (available.length > 0) {
        techStackSummary = `Commands: ${available.join(', ')}`;
      }
    } catch {
      // ignore
    }
  }

  // Read project.md for architecture summary
  let architectureSummary: string | undefined;
  if (existsSync(projectMdPath)) {
    try {
      const content = readFileSync(projectMdPath, 'utf-8');
      // Extract any "## Architecture" or "## Rules" section
      const archMatch = content.match(/## Architecture[^]*?(?=\n##|\Z)/);
      if (archMatch) {
        architectureSummary = archMatch[0].trim();
      }
    } catch {
      // ignore
    }
  }

  return {
    name,
    type,
    primaryLanguage,
    runtime: runtimeStr,
    packageManager,
    repositoryRoot: resolve(projectPath),
    architectureSummary,
    techStackSummary,
  };
}

// ============================================================
// Git Collector
// ============================================================

/**
 * Collect git state: branch, status, diff, recent commits.
 */
export async function collectGit(projectPath: string): Promise<GitContext> {
  const git = simpleGit(projectPath);
  const empty: GitContext = {
    branch: 'unknown',
    statusShort: '',
    diffStat: '',
    changedFiles: [],
    untrackedFiles: [],
    recentCommits: [],
    hasUserChanges: false,
  };

  try {
    const isRepo = await git.checkIsRepo();
    if (!isRepo) return empty;

    const branch = (await git.branch()).current || 'unknown';
    const status = await git.status();
    const diffStat = await git.diff(['--stat']);
    const diffSummary = await git.diff();
    const log = await git.log({ maxCount: 5 });

    return {
      branch,
      statusShort: status.files.map((f) => `${f.working_dir} ${f.path}`).join('\n'),
      diffStat: diffStat || '(no diff)',
      diffSummary: diffSummary?.slice(0, 2000) || undefined,
      changedFiles: status.files.map((f) => f.path),
      untrackedFiles: status.not_added || [],
      recentCommits: log.all.map((c) => `${c.date.slice(0, 10)} ${c.message}`),
      hasUserChanges: status.files.length > 0,
    };
  } catch {
    return empty;
  }
}

// ============================================================
// Task Collector
// ============================================================

/**
 * Read current active task from .project/tasks/active/<task-id>.json
 * If taskId is provided, reads that specific task.
 * Otherwise finds the most recent active task.
 */
export function collectTask(projectPath: string, taskId?: string): TaskContext | undefined {
  const activeDir = join(projectPath, '.project/tasks/active');

  if (!existsSync(activeDir)) return undefined;

  let targetFile: string | undefined;

  if (taskId) {
    const jsonPath = join(activeDir, `${taskId}.json`);
    if (existsSync(jsonPath)) targetFile = jsonPath;
  } else {
    // Find latest active task by timestamp in ID
    const files = readdirSorted(activeDir).filter((f) => f.endsWith('.json'));
    if (files.length > 0) {
      targetFile = join(activeDir, files[files.length - 1]);
    }
  }

  if (!targetFile) return undefined;

  try {
    const json = JSON.parse(readFileSync(targetFile, 'utf-8'));
    return {
      title: json.title || '',
      userInstruction: json.userInstruction || '',
      normalizedInstruction: json.normalizedGoal || json.title || '',
      taskType: (json.type as TaskType) || 'unknown',
      explicitFiles: [],
      explicitCommands: [],
      acceptanceHints: [],
    };
  } catch {
    return undefined;
  }
}

function readdirSorted(dir: string): string[] {
  return readdirSync(dir).sort();
}
