/**
 * Test Helpers for Harness OS
 *
 * Provides reusable fixtures, workspace management, and assertion utilities.
 * Follows 13_TESTING_STRATEGY.md §30 (Test Helpers).
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { execSync, ExecSyncOptions } from 'child_process';
import { ProjectManifest } from '../../src/types.js';

// ============================================================
// Workspace Management
// ============================================================

/**
 * Create a temporary workspace directory for testing.
 * Automatically cleaned up unless `preserveOnFail` is set and test fails.
 */
export function createTempWorkspace(): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'harness-test-'));
  return dir;
}

/**
 * Remove a temporary workspace.
 */
export function removeTempWorkspace(dir: string): void {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

// ============================================================
// Project Fixtures
// ============================================================

/**
 * Create a minimal Harness OS project fixture in the given directory.
 * Creates AGENTS.md, .project/ structure, and manifest.json.
 */
export function createHarnessProjectFixture(root: string): void {
  // AGENTS.md
  writeAgentsMd(root);

  // .project/ structure
  const projectDirs = [
    '.project/state',
    '.project/tasks/active',
    '.project/tasks/completed',
    '.project/tasks/failed',
    '.project/decisions',
    '.project/context',
    '.project/reports/runs',
    '.project/reports/verification',
    '.project/reports/delivery',
    '.project/reports/events',
    '.project/reports/traces',
    '.project/checkpoints',
    '.project/sessions',
  ];
  for (const d of projectDirs) {
    fs.mkdirSync(path.join(root, d), { recursive: true });
  }

  // manifest.json
  writeManifest(root, {
    version: '1.0',
    projectId: 'test-project',
    projectName: path.basename(root),
    projectType: 'cli',
    rootPath: root,
    defaultBranch: 'main',
    language: { primary: 'typescript', secondary: [] },
    runtime: { name: 'node', version: '22' },
    packageManager: { name: 'pnpm' },
    commands: {
      test: 'pnpm test',
      lint: 'pnpm lint',
      build: 'pnpm build',
    },
    skills: { enabled: ['filesystem', 'shell', 'git'], disabled: [] },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  });
}

// ============================================================
// Git Repo Management
// ============================================================

/**
 * Initialize a Git repository in the given directory.
 * Sets up user config for the test environment.
 */
export function createGitRepo(dir: string): void {
  execSync('git init', { cwd: dir, stdio: 'pipe' });
  execSync('git config user.email test@harness-os.test', { cwd: dir, stdio: 'pipe' });
  execSync('git config user.name "Harness OS Test"', { cwd: dir, stdio: 'pipe' });
}

/**
 * Create an initial commit in the repository.
 */
export function createInitialCommit(dir: string): void {
  execSync('git add -A', { cwd: dir, stdio: 'pipe' });
  execSync('git commit -m "test: initial commit" --allow-empty', { cwd: dir, stdio: 'pipe' });
}

// ============================================================
// File Writers
// ============================================================

/**
 * Write AGENTS.md to the project root.
 */
export function writeAgentsMd(root: string, content?: string): void {
  const defaultContent = `# AGENTS.md

## Project Identity

Project Name: test-project
Project Type: cli
Primary Language: typescript
Runtime: node
Package Manager: pnpm

## Project Goals

- Test Harness OS functionality

## Architecture Rules

1. Single Agent
2. Skills are tools

## Development Commands

Install: pnpm install
Test: pnpm test
Build: pnpm build

## Testing and Verification

Required:
- lint
- typecheck
- test
`;
  fs.writeFileSync(path.join(root, 'AGENTS.md'), content || defaultContent);
}

/**
 * Write a project manifest.json.
 */
export function writeManifest(root: string, manifest: ProjectManifest): void {
  const manifestPath = path.join(root, '.project/state/manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
}

/**
 * Write a task record to .project/tasks/active/
 */
export function writeTaskRecord(root: string, taskId: string, overrides?: Partial<Record<string, unknown>>): string {
  const taskDir = path.join(root, '.project/tasks/active');
  fs.mkdirSync(taskDir, { recursive: true });

  const task = {
    taskId,
    projectId: 'test-project',
    title: 'Test task',
    type: 'feature',
    status: 'created',
    userInstruction: 'Run a test task',
    normalizedGoal: 'Test task goal',
    runIds: [],
    contextPackIds: [],
    checkpointIds: [],
    changedFiles: [],
    verification: { status: 'pending' },
    risks: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };

  const taskPath = path.join(taskDir, `${taskId}.json`);
  fs.writeFileSync(taskPath, JSON.stringify(task, null, 2));
  return taskPath;
}

// ============================================================
// CLI Execution
// ============================================================

/**
 * Run a Harness CLI command in the given workspace.
 * Returns stdout, stderr, and exit code.
 */
export function runHarnessCli(
  args: string[],
  options?: { cwd?: string; env?: Record<string, string> }
): { stdout: string; stderr: string; exitCode: number } {
  const harnessEntry = path.resolve(__dirname, '../../src/cli/index.ts');
  const cwd = options?.cwd || process.cwd();

  try {
    const result = execSync(
      `npx tsx ${harnessEntry} ${args.join(' ')}`,
      {
        cwd,
        encoding: 'utf-8',
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, ...options?.env, HARNESS_TEST_MODE: 'true' },
        timeout: 30_000,
      }
    );
    return { stdout: result.stdout || '', stderr: result.stderr || '', exitCode: 0 };
  } catch (e) {
    return {
      stdout: e.stdout?.toString() || '',
      stderr: e.stderr?.toString() || '',
      exitCode: e.status || 1,
    };
  }
}

// ============================================================
// File Readers
// ============================================================

/**
 * Read and parse a JSON file safely.
 */
export function readJson(filePath: string): Record<string, unknown> {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

/**
 * Read a Markdown file.
 */
export function readMarkdown(filePath: string): string {
  return fs.readFileSync(filePath, 'utf-8');
}

// ============================================================
// Assertion Utilities
// ============================================================

/**
 * Assert that an event exists in a JSONL event log.
 */
export function assertEventExists(
  eventLogPath: string,
  eventType: string,
  predicate?: (event: any) => boolean
): boolean {
  if (!fs.existsSync(eventLogPath)) return false;

  const lines = fs.readFileSync(eventLogPath, 'utf-8').split('\n').filter(Boolean);
  for (const line of lines) {
    try {
      const event = JSON.parse(line);
      if (event.type === eventType) {
        if (!predicate || predicate(event)) return true;
      }
    } catch {
      continue;
    }
  }
  return false;
}

/**
 * Assert that a policy decision matches expected result.
 */
export function assertPolicyDecision(
  decision: { decision: string; riskLevel: string },
  expected: { decision: string; riskLevel?: string }
): boolean {
  const decisionMatch = decision.decision === expected.decision;
  const riskMatch = expected.riskLevel ? decision.riskLevel === expected.riskLevel : true;
  return decisionMatch && riskMatch;
}

/**
 * Assert that a string contains no unredacted secret patterns.
 */
export function assertRedacted(content: string): boolean {
  const secretPatterns = [
    /sk-[a-zA-Z0-9_-]{20,}/,
    /ghp_[a-zA-Z0-9]{36,}/,
    /gho_[a-zA-Z0-9]{36,}/,
    /-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----/,
    /AKIA[0-9A-Z]{16}/,
    /eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}/,
  ];

  for (const pattern of secretPatterns) {
    if (pattern.test(content)) return false;
  }
  return true;
}

// ============================================================
// Snapshot Helpers
// ============================================================

/**
 * Normalize a string for snapshot testing by replacing
 * dynamic values (timestamps, IDs, absolute paths) with placeholders.
 */
export function normalizeForSnapshot(content: string): string {
  return content
    .replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z/g, '[TIMESTAMP]')
    .replace(/run_[a-zA-Z0-9_-]+/g, '[RUN_ID]')
    .replace(/task_[a-zA-Z0-9_-]+/g, '[TASK_ID]')
    .replace(/checkpoint_[a-zA-Z0-9_-]+/g, '[CHECKPOINT_ID]')
    .replace(/C:\\[^\s"]+/g, '[ABSOLUTE_PATH]')
    .replace(/\/tmp\/[^\s"]+/g, '[TEMP_PATH]');
}
