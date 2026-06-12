/**
 * Harness OS — Task Record Creator
 *
 * Phase 3.1: Create a task record with ID, normalized title, type inference,
 * and write Markdown + JSON to .project/tasks/active/.
 *
 * Flow:
 *   1. Generate task ID
 *   2. Normalize title from user input
 *   3. Infer task type from keywords
 *   4. Extract explicit files and commands
 *   5. Write .project/tasks/active/<task-id>.md
 *   6. Write .project/tasks/active/<task-id>.json
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7.3
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import type { TaskState, TaskStatus, TaskType } from '../types.js';
import { safeWriteJson, redactText } from '../governance/redactor.js';

// ============================================================
// ID Generation
// ============================================================

let counter = 0;

function generateTaskId(): string {
  counter += 1;
  const ts = Date.now().toString(36);
  const seq = counter.toString(36).padStart(4, '0');
  return `task_${ts}_${seq}`;
}

// ============================================================
// Title Normalization
// ============================================================

/**
 * Normalize a user instruction into a short task title.
 * - Takes the first sentence or first 80 chars
 * - Capitalizes first letter
 * - Removes trailing punctuation
 */
export function normalizeTitle(input: string): string {
  let title = input.trim();

  // Take first sentence (up to first . ! ? followed by space or end)
  const sentenceMatch = title.match(/^.*?[.!?](?:\s|$)/);
  if (sentenceMatch) {
    title = sentenceMatch[0].trim().replace(/[.!?\s]+$/, '');
  }

  // Truncate to 80 chars
  if (title.length > 80) {
    title = title.slice(0, 77) + '...';
  }

  // Capitalize first letter
  title = title.charAt(0).toUpperCase() + title.slice(1);

  return title || 'Untitled task';
}

// ============================================================
// Task Type Inference
// ============================================================

const TYPE_KEYWORDS: Record<string, string[]> = {
  // More specific types first (checked first)
  test:      ['test', 'coverage', 'spec', 'assert', 'mock'],
  bugfix:    ['fix', 'bug', 'error', 'crash', 'broken', 'incorrect', 'wrong'],
  investigation: ['investigate', 'research', 'root cause', 'analyze', 'explore'],
  docs:      ['doc', 'readme', 'documentation', 'comment', 'api doc'],
  refactor:  ['refactor', 'rewrite', 'restructure', 'clean up', 'simplify'],
  delivery:  ['deliver', 'release', 'publish', 'deploy', 'pr', 'commit'],
  maintenance: ['update', 'upgrade', 'migrate', 'bump', 'deprecat', 'audit'],
  // Generic types last (fallback)
  feature:   ['implement', 'create', 'new', 'feature', 'build', 'support'],
};

/**
 * Infer the task type from user instruction text.
 */
export function inferTaskType(instruction: string): TaskType {
  const lower = instruction.toLowerCase();

  for (const [type, keywords] of Object.entries(TYPE_KEYWORDS)) {
    for (const kw of keywords) {
      if (lower.includes(kw)) return type as TaskType;
    }
  }

  return 'unknown';
}

// ============================================================
// Extract Explicit References
// ============================================================

export interface ExplicitRefs {
  files: string[];
  commands: string[];
}

/**
 * Extract explicitly mentioned file paths and commands from user instruction.
 * Simple heuristic: looks for paths with extensions, and backtick-quoted words.
 */
export function extractExplicitRefs(instruction: string): ExplicitRefs {
  const files: string[] = [];
  const commands: string[] = [];

  // Match file paths with extensions (e.g. src/index.ts, ./README.md)
  const fileRegex = /(?:^|\s)(\.?\/?[\w./-]+\.[a-z]{1,4})(?:\s|$)/gi;
  let match: RegExpExecArray | null;
  while ((match = fileRegex.exec(instruction)) !== null) {
    const path = match[1].trim();
    if (!files.includes(path)) files.push(path);
  }

  // Match backtick-quoted text as potential commands
  const cmdRegex = /`([^`]+)`/g;
  while ((match = cmdRegex.exec(instruction)) !== null) {
    const cmd = match[1].trim();
    if (cmd.includes(' ') || cmd.startsWith('pnpm') || cmd.startsWith('npm') || cmd.startsWith('git')) {
      if (!commands.includes(cmd)) commands.push(cmd);
    }
  }

  return { files, commands };
}

// ============================================================
// Create Task Record
// ============================================================

export interface CreateTaskParams {
  /** The project's root path. */
  projectPath: string;
  /** The user's raw instruction. */
  userInstruction: string;
  /** Optional project ID (read from manifest if not provided). */
  projectId?: string;
  /** Optional explicit task type override. */
  taskType?: TaskType;
}

export interface TaskRecord {
  state: TaskState;
  mdPath: string;
  jsonPath: string;
}

/**
 * Create a new task record.
 *
 * Steps:
 *   1. Generate task ID
 *   2. Normalize title
 *   3. Infer task type
 *   4. Extract explicit refs
 *   5. Write task record files
 */
export async function createTaskRecord(
  params: CreateTaskParams,
): Promise<TaskRecord> {
  const projectPath = resolve(params.projectPath);
  const activeDir = join(projectPath, '.project/tasks/active');

  // Ensure directory exists
  if (!existsSync(activeDir)) {
    mkdirSync(activeDir, { recursive: true });
  }

  // 1. Generate ID
  const taskId = generateTaskId();

  // 2. Normalize title
  const title = normalizeTitle(params.userInstruction);

  // 3. Infer task type
  const taskType = params.taskType ?? inferTaskType(params.userInstruction);

  // 4. Extract explicit refs
  const refs = extractExplicitRefs(params.userInstruction);

  // 5. Read projectId from manifest if not provided
  let projectId = params.projectId ?? '';
  if (!projectId) {
    try {
      const manifestPath = join(projectPath, '.project/state/manifest.json');
      if (existsSync(manifestPath)) {
        const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
        projectId = manifest.projectId ?? '';
      }
    } catch {
      // ignore — projectId stays empty
    }
  }

  // 6. Build task state
  const now = new Date().toISOString();
  const state: TaskState = {
    taskId,
    projectId,
    title,
    type: taskType,
    status: 'created',
    userInstruction: params.userInstruction,
    normalizedGoal: title,
    runIds: [],
    contextPackIds: [],
    checkpointIds: [],
    changedFiles: [],
    verification: { status: 'pending' },
    risks: [],
    createdAt: now,
    updatedAt: now,
  };

  // 7. Generate markdown
  const md = generateTaskMarkdown(state, refs);

  // 8. Write files
  const mdPath = join(activeDir, `${taskId}.md`);
  const jsonPath = join(activeDir, `${taskId}.json`);

  writeFileSync(mdPath, redactText(md), 'utf-8');
  safeWriteJson(jsonPath, state, 2);

  return { state, mdPath, jsonPath };
}

// ============================================================
// Markdown Generator
// ============================================================

function generateTaskMarkdown(state: TaskState, refs: ExplicitRefs): string {
  const lines = [
    `# Task: ${state.title}`,
    '',
    `Task ID: ${state.taskId}`,
    `Status: ${state.status}`,
    `Type: ${state.type}`,
    `Created At: ${state.createdAt}`,
    `Updated At: ${state.updatedAt}`,
    '',
    '## User Instruction',
    '',
    state.userInstruction,
    '',
    '## Normalized Goal',
    '',
    state.normalizedGoal,
    '',
    '## Explicit Files',
    '',
    ...(refs.files.length > 0 ? refs.files.map(f => `- ${f}`) : ['- (none detected)']),
    '',
    '## Explicit Commands',
    '',
    ...(refs.commands.length > 0 ? refs.commands.map(c => `- \`${c}\``) : ['- (none detected)']),
    '',
    '## Context Links',
    '',
    '- Context Pack: (not yet built)',
    '- Related Decisions: (none)',
    '- Related Reports: (none)',
    '',
    '## Execution Runs',
    '',
    '- (none yet)',
    '',
    '## Changed Files',
    '',
    '- (none yet)',
    '',
    '## Verification',
    '',
    'Status: pending',
    '',
    'Commands:',
    '',
    'Results:',
    '',
    '## Risks',
    '',
    '- (none identified yet)',
    '',
    '## Follow-up',
    '',
    '- (none)',
    '',
    '## Final Summary',
    '',
    '(to be completed)',
    '',
  ];

  return lines.join('\n');
}
