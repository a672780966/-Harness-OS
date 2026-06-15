/**
 * Harness OS — Context Pack Builder
 *
 * Phase 4.3: Assemble Context Pack from collected sources, apply budget, save snapshots.
 *
 * Flow (05_CONTEXT_ENGINEERING.md §7.1):
 *   1. Load AGENTS.md
 *   2. Load project state
 *   3. Inspect git state
 *   4. Load current task
 *   5. Build file candidates
 *   6. Apply budget
 *   7. Assemble Context Pack
 *   8. Save JSON + Markdown snapshots
 *
 * Reference: 05_CONTEXT_ENGINEERING.md §6, §7, §11, §12
 */

import { existsSync, mkdirSync } from 'fs';
import { join, resolve } from 'path';
import type { ContextPack, FileContext, DecisionContext, SkillContext } from '../types.js';
import { collectAgentsMd, collectProject, collectGit, collectTask } from './sources.js';
import { scoreFile, sortCandidates, extractKeywords } from './relevance.js';
import { calculateBudget, trimToBudget } from './budget.js';
import { redactObject, safeWriteJson, safeWriteText } from '../governance/redactor.js';

// ============================================================
// Build Input
// ============================================================

export interface BuildContextInput {
  /** Harness project ID. */
  projectId: string;
  /** Current run ID. */
  runId: string;
  /** Task ID (null for taskless runs). */
  taskId?: string;
  /** User's instruction for this run. */
  userInstruction: string;
  /** Workspace path (project root). */
  workspacePath: string;
  /** Optional max tokens override. */
  maxTokens?: number;
}

/**
 * Load accepted ADRs. Superseded/rejected decisions are excluded.
 * Returns an empty array if the decisions directory doesn't exist.
 */
async function loadActiveDecisions(projectPath: string): Promise<DecisionContext[]> {
  try {
    const { listActiveDecisions } = await import('../decision/index.js');
    const active = listActiveDecisions(projectPath);
    return active.map((d) => ({
      id: d.id,
      path: `.project/decisions/${d.id}.json`,
      title: d.title,
      status: d.status,
      summary: d.summary,
      relevanceReason: `Active ${d.type} decision — Constrains project architecture and design choices`,
    }));
  } catch {
    return [];
  }
}

// ============================================================
// Build Context Pack
// ============================================================

/**
 * Build a Context Pack for a Codex run.
 *
 * Returns the assembled ContextPack and saves JSON + Markdown snapshots.
 */
export async function buildContextPack(input: BuildContextInput): Promise<ContextPack> {
  const workspacePath = resolve(input.workspacePath);
  const contextDir = join(workspacePath, '.project/context');
  const packId = `ctx_${input.runId}`;

  // 1. Collect sources
  const rules = collectAgentsMd(workspacePath);
  const project = collectProject(workspacePath);
  const git = await collectGit(workspacePath);
  const task = input.taskId ? collectTask(workspacePath, input.taskId) : undefined;

  // 2. Prepare file candidates
  const gitChangedFiles = git.changedFiles || [];
  const explicitFiles = task?.explicitFiles || [];
  const taskKeywords = task
    ? extractKeywords(`${task.title} ${task.userInstruction}`)
    : extractKeywords(input.userInstruction);

  // Build file candidates from changed files
  const candidateInputs = [
    // From git diff
    ...gitChangedFiles.map((path) => ({
      filePath: path,
      explicitFiles,
      gitChangedFiles,
      taskKeywords,
    })),
    // From explicit files
    ...explicitFiles.map((path) => ({
      filePath: path,
      explicitFiles,
      gitChangedFiles,
      taskKeywords,
    })),
  ];

  // Deduplicate by filePath
  const seen = new Set<string>();
  const uniqueInputs = candidateInputs.filter((i) => {
    if (seen.has(i.filePath)) return false;
    seen.add(i.filePath);
    return true;
  });

  const candidates = uniqueInputs.map((i) => scoreFile(i));
  const sorted = sortCandidates(candidates);

  // 3. Apply budget
  const budget = calculateBudget({
    maxTokens: input.maxTokens,
  });
  const trimmed = trimToBudget(sorted, budget);

  // 4. Determine skills (from project manifest)
  const skills = getDefaultSkills();

  // 5. Build decisions from accepted ADRs (P1-003)
  const decisions: DecisionContext[] = await loadActiveDecisions(input.workspacePath);

  // 6. Build FileContexts from candidates
  const files: FileContext[] = trimmed.candidates.map((c) => ({
    path: c.path,
    reason: c.reason as FileContext['reason'],
    priority: c.priority,
    contentMode: c.contentMode,
  }));

  // 7. Build Context Pack
  const pack: ContextPack = {
    id: packId,
    projectId: input.projectId,
    taskId: input.taskId || '',
    runId: input.runId,
    createdAt: new Date().toISOString(),
    task: task || {
      title: '',
      userInstruction: input.userInstruction,
      normalizedInstruction: input.userInstruction,
      taskType: 'unknown',
      explicitFiles,
      explicitCommands: [],
      acceptanceHints: [],
    },
    project,
    rules,
    git,
    files,
    decisions,
    skills,
    budget,
    notes: [],
  };

  // 8. Save snapshots
  saveContextPack(pack, contextDir);

  return pack;
}

// ============================================================
// Save Snapshots
// ============================================================

/**
 * Save Context Pack as JSON + Markdown snapshots.
 */
function saveContextPack(pack: ContextPack, contextDir: string): void {
  if (!existsSync(contextDir)) {
    mkdirSync(contextDir, { recursive: true });
  }

  const runId = pack.runId;

  // Deep-redact before serialization (SEC-05)
  const safePack: ContextPack = redactObject(pack) as ContextPack;

  // JSON snapshot
  const jsonPath = join(contextDir, `${runId}.json`);
  safeWriteJson(jsonPath, safePack, 2);

  // Markdown snapshot
  const mdPath = join(contextDir, `${runId}.md`);
  const md = generateContextMarkdown(safePack);
  safeWriteText(mdPath, md);
}

// ============================================================
// Markdown Generator
// ============================================================

/**
 * Generate human-readable Markdown from a Context Pack.
 */
function generateContextMarkdown(pack: ContextPack): string {
  const lines: string[] = [
    `# Context Pack: ${pack.id}`,
    '',
    `Run: ${pack.runId}  `,
    `Task: ${pack.taskId}  `,
    `Created: ${pack.createdAt}  `,
    '',
    '## Task',
    '',
    `**${pack.task.title}**`,
    '',
    pack.task.userInstruction,
    '',
    '## Project',
    '',
    `Name: ${pack.project.name}  `,
    `Type: ${pack.project.type}  `,
    `Language: ${pack.project.primaryLanguage}  `,
    `Runtime: ${pack.project.runtime}  `,
    pack.project.packageManager ? `Package Manager: ${pack.project.packageManager}  \n` : '',
    '',
    '## Rules from AGENTS.md',
    '',
    ...(pack.rules.architectureRules.length > 0
      ? ['### Architecture Rules', ...pack.rules.architectureRules.map((r) => `- ${r}`), '']
      : []),
    ...(pack.rules.codingRules.length > 0
      ? ['### Coding Rules', ...pack.rules.codingRules.map((r) => `- ${r}`), '']
      : []),
    ...(pack.rules.testingRules.length > 0
      ? ['### Testing Rules', ...pack.rules.testingRules.map((r) => `- ${r}`), '']
      : []),
    ...(pack.rules.securityRules.length > 0
      ? ['### Security Rules', ...pack.rules.securityRules.map((r) => `- ${r}`), '']
      : []),
    '',
    '## Git State',
    '',
    `Branch: ${pack.git.branch}  `,
    `User changes: ${pack.git.hasUserChanges ? 'yes' : 'no'}  `,
    `Changed files: ${pack.git.changedFiles.length}  `,
    '',
    ...(pack.git.changedFiles.length > 0
      ? ['### Changed Files', ...pack.git.changedFiles.map((f) => `- ${f}`), '']
      : []),
    '',
    '## Relevant Files',
    '',
    ...pack.files.map(
      (f) => `### ${f.path}\n\nReason: ${f.reason}  \nPriority: P${f.priority}  \nMode: ${f.contentMode}\n`,
    ),
    '',
    '## Available Skills',
    '',
    ...pack.skills.map(
      (s) => `- **${s.name}** — ${s.description} (${s.riskLevel}, ${s.allowed ? 'allowed' : 'disabled'})`,
    ),
    '',
    '## Context Budget',
    '',
    `Max tokens: ${pack.budget.maxTokens.toLocaleString()}  `,
    `Estimated: ${pack.budget.estimatedTokens.toLocaleString()}  `,
    `Response reserve: ${pack.budget.reservedForResponse.toLocaleString()}  `,
    `Tool results reserve: ${pack.budget.reservedForToolResults.toLocaleString()}  `,
    `Trimming: ${pack.budget.trimmingApplied ? 'applied' : 'none'}  `,
    '',
  ];

  return lines.join('\n');
}

// ============================================================
// Default Skills
// ============================================================

function getDefaultSkills(): SkillContext[] {
  return [
    {
      name: 'filesystem',
      description: 'Read, write, edit, and list project files',
      allowed: true,
      riskLevel: 'medium',
      requiresApproval: false,
    },
    {
      name: 'shell',
      description: 'Execute shell commands within workspace',
      allowed: true,
      riskLevel: 'high',
      requiresApproval: true,
    },
    {
      name: 'git',
      description: 'Git status, diff, log, and commit operations',
      allowed: true,
      riskLevel: 'medium',
      requiresApproval: false,
    },
    {
      name: 'repo-scanner',
      description: 'Scan repository structure, detect tech stack, build maps',
      allowed: true,
      riskLevel: 'low',
      requiresApproval: false,
    },
  ];
}
