/**
 * Harness OS — Context Engineering Tests
 *
 * Coverage:
 * - Sources: AGENTS.md collector, project state, git state, task reader
 * - Relevance: file scoring, test matching, keywords, token estimation
 * - Budget: calculation, trimming strategy, P0 preservation
 * - Build: full Context Pack assembly from real project
 *
 * Reference: 05_CONTEXT_ENGINEERING.md | 11_ACCEPTANCE_CRITERIA.md §9
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { createProject } from '../../src/project/create.js';
import { createTaskRecord } from '../../src/task/create.js';
import { simpleGit } from 'simple-git';

import {
  collectAgentsMd,
  collectProject,
  collectGit,
  collectTask,
} from '../../src/context/sources.js';

import {
  scoreFile,
  matchTestFile,
  extractKeywords,
  estimateTokens,
  sortCandidates,
} from '../../src/context/relevance.js';

import {
  calculateBudget,
  trimToBudget,
  availableContextTokens,
} from '../../src/context/budget.js';

import { buildContextPack } from '../../src/context/build.js';

let testDir: string;
let projectPath: string;

beforeEach(async () => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-context-test-'));
  projectPath = join(testDir, 'test-proj');
  await createProject({ name: 'test-proj', path: projectPath });
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Source Collectors Tests
// ============================================================

describe('collectAgentsMd', () => {
  it('extracts rules from AGENTS.md', () => {
    const ctx = collectAgentsMd(projectPath);
    expect(ctx.source).toBe('AGENTS.md');
    // At minimum should extract architecture and security rules
    // since the template has those sections
    expect(ctx.architectureRules.length + ctx.codingRules.length + ctx.testingRules.length + ctx.securityRules.length).toBeGreaterThan(0);
  });

  it('returns defaults for missing AGENTS.md', () => {
    rmSync(join(projectPath, 'AGENTS.md'), { force: true });
    const ctx = collectAgentsMd(projectPath);
    expect(ctx.architectureRules).toEqual([]);
  });
});

describe('collectProject', () => {
  it('reads project name from manifest', () => {
    const ctx = collectProject(projectPath);
    expect(ctx.name).toBe('test-proj');
  });

  it('reads tech stack info', () => {
    const ctx = collectProject(projectPath);
    expect(ctx.primaryLanguage).toBeTruthy();
    expect(ctx.repositoryRoot).toBe(projectPath);
  });

  it('works with missing manifest', () => {
    rmSync(join(projectPath, '.project/state/manifest.json'), { force: true });
    const ctx = collectProject(projectPath);
    expect(ctx.name).toBeTruthy();
    expect(ctx.primaryLanguage).toBe('unknown');
  });
});

describe('collectGit', () => {
  it('reads branch from git repo', async () => {
    const ctx = await collectGit(projectPath);
    expect(ctx.branch).toBeTruthy();
  });

  it('reads git status as clean', async () => {
    const ctx = await collectGit(projectPath);
    expect(ctx.hasUserChanges).toBe(false);
  });

  it('detects uncommitted changes', async () => {
    writeFileSync(join(projectPath, 'new-file.txt'), 'hello');
    const ctx = await collectGit(projectPath);
    expect(ctx.hasUserChanges).toBe(true);
    expect(ctx.changedFiles.length).toBeGreaterThan(0);
  });

  it('returns defaults for non-git dir', async () => {
    const emptyDir = join(testDir, 'not-a-repo');
    mkdirSync(emptyDir);
    const ctx = await collectGit(emptyDir);
    expect(ctx.branch).toBe('unknown');
  });
});

describe('collectTask', () => {
  it('returns undefined when no active tasks', () => {
    const result = collectTask(projectPath);
    expect(result).toBeUndefined();
  });

  it('reads task by ID', async () => {
    const record = await createTaskRecord({ projectPath, userInstruction: 'Fix login issue' });
    const result = collectTask(projectPath, record.state.taskId);
    expect(result).toBeDefined();
    expect(result!.title).toBe('Fix login issue');
    expect(result!.taskType).toBe('bugfix');
  });
});

// ============================================================
// Relevance Engine Tests
// ============================================================

describe('scoreFile', () => {
  it('scores explicit file mention as P0', () => {
    const result = scoreFile({
      filePath: 'src/index.ts',
      explicitFiles: ['src/index.ts'],
      gitChangedFiles: [],
      taskKeywords: ['index'],
    });
    expect(result.priority).toBe(0);
    expect(result.score).toBeGreaterThanOrEqual(100);
    expect(result.reason).toBe('explicit');
  });

  it('scores git diff file as high priority', () => {
    const result = scoreFile({
      filePath: 'src/changed.ts',
      explicitFiles: [],
      gitChangedFiles: ['src/changed.ts'],
      taskKeywords: [],
    });
    expect(result.score).toBeGreaterThanOrEqual(90);
    expect(result.reason).toBe('git-diff');
  });

  it('scores test files with test-match', () => {
    const result = scoreFile({
      filePath: 'tests/foo.test.ts',
      explicitFiles: [],
      gitChangedFiles: [],
      taskKeywords: [],
      isTestFile: true,
    });
    expect(result.score).toBeGreaterThanOrEqual(80);
    expect(result.reason).toBe('test-match');
  });

  it('assigns full content to explicit files', () => {
    const r = scoreFile({ filePath: 'a.ts', explicitFiles: ['a.ts'], gitChangedFiles: [], taskKeywords: [] });
    expect(r.contentMode).toBe('full');
  });

  it('assigns metadata-only to low-scored files', () => {
    const r = scoreFile({ filePath: 'unrelated.ts', explicitFiles: [], gitChangedFiles: [], taskKeywords: ['somethingelse'] });
    expect(r.contentMode).toBe('metadata-only');
  });
});

describe('matchTestFile', () => {
  it('maps src/foo.ts to tests/foo.test.ts', () => {
    const matches = matchTestFile('src/foo.ts');
    expect(matches).toContain('tests/foo.test.ts');
    expect(matches).toContain('src/foo.test.ts');
  });

  it('maps components/Button.tsx to co-located test', () => {
    const matches = matchTestFile('components/Button.tsx');
    expect(matches).toContain('components/Button.test.tsx');
    expect(matches).toContain('components/Button.spec.tsx');
  });
});

describe('extractKeywords', () => {
  it('extracts meaningful keywords from text', () => {
    const result = extractKeywords('Fix the login button loading state');
    expect(result).toContain('login');
    expect(result).toContain('button');
    expect(result).toContain('loading');
    expect(result).not.toContain('the'); // stop word filtered
  });

  it('filters short and stop words', () => {
    const result = extractKeywords('a be to for');
    expect(result).toEqual([]);
  });
});

describe('estimateTokens', () => {
  it('estimates ~4 chars per token', () => {
    expect(estimateTokens('hello world')).toBe(3); // 11/4 = ceil(2.75)
    expect(estimateTokens('a'.repeat(100))).toBe(25);
    expect(estimateTokens('')).toBe(0);
  });
});

describe('sortCandidates', () => {
  it('sorts by score descending', () => {
    const items = [
      { id: 'a', path: 'a.ts', priority: 3, score: 10, reason: 'keyword-match', estimatedTokens: 0, contentMode: 'metadata-only' as const },
      { id: 'b', path: 'b.ts', priority: 0, score: 100, reason: 'explicit', estimatedTokens: 0, contentMode: 'full' as const },
    ];
    const sorted = sortCandidates(items);
    expect(sorted[0].id).toBe('b');
    expect(sorted[1].id).toBe('a');
  });
});

// ============================================================
// Budget Manager Tests
// ============================================================

describe('budget', () => {
  it('calculates budget with defaults', () => {
    const budget = calculateBudget();
    expect(budget.maxTokens).toBe(128_000);
    expect(budget.reservedForResponse).toBe(25_600);
    expect(budget.reservedForToolResults).toBe(12_800);
  });

  it('calculates available tokens', () => {
    const budget = calculateBudget({ maxTokens: 100_000, reserveResponse: 0.2, reserveToolResults: 0.1 });
    const available = availableContextTokens(budget);
    expect(available).toBe(70_000);
  });

  it('trims P3 metadata candidates first, preserves P0', () => {
    const budget = calculateBudget({ maxTokens: 1000, reserveResponse: 0, reserveToolResults: 0 });
    const candidates = [
      { id: 'p0-file', path: 'p0.ts', priority: 0, score: 100, reason: 'explicit', estimatedTokens: 200, contentMode: 'full' as const },
      { id: 'p3-file', path: 'p3.ts', priority: 3, score: 10, reason: 'keyword-match', estimatedTokens: 5000, contentMode: 'metadata-only' as const },
      { id: 'p2-file', path: 'p2.ts', priority: 2, score: 30, reason: 'keyword-match', estimatedTokens: 300, contentMode: 'full' as const },
    ];

    const result = trimToBudget(candidates, budget);
    expect(result.candidates.some(c => c.id === 'p0-file')).toBe(true);
    expect(result.candidates.some(c => c.id === 'p3-file')).toBe(false);
    expect(result.removed.some(c => c.id === 'p3-file')).toBe(true);
    expect(result.budget.trimmingApplied).toBe(true);
  });

  it('converts P3 full candidates to metadata-only', () => {
    const budget = calculateBudget({ maxTokens: 500, reserveResponse: 0, reserveToolResults: 0 });
    const candidates = [
      { id: 'keep', path: 'keep.ts', priority: 0, score: 100, reason: 'explicit', estimatedTokens: 50, contentMode: 'full' as const },
      { id: 'trim', path: 'trim.ts', priority: 3, score: 10, reason: 'keyword-match', estimatedTokens: 1000, contentMode: 'full' as const },
    ];

    const result = trimToBudget(candidates, budget);
    // The P3 candidate should be converted to metadata-only in candidates array
    const converted = result.candidates.find(c => c.id === 'trim');
    expect(converted).toBeDefined();
    expect(converted!.contentMode).toBe('metadata-only');
  });
});

// ============================================================
// Full Context Pack Build Tests
// ============================================================

describe('buildContextPack', () => {
  it('builds a complete Context Pack from project', async () => {
    const pack = await buildContextPack({
      projectId: 'proj_test',
      runId: 'run_001',
      userInstruction: 'Fix login issue in src/index.ts',
      workspacePath: projectPath,
    });

    expect(pack.id).toContain('run_001');
    expect(pack.project.name).toBe('test-proj');
    expect(pack.rules.source).toBe('AGENTS.md');
    expect(pack.git.branch).toBeTruthy();
    expect(pack.budget.maxTokens).toBeGreaterThan(0);
    expect(pack.skills.length).toBeGreaterThan(0);
  });

  it('saves JSON and Markdown snapshots', async () => {
    const pack = await buildContextPack({
      projectId: 'proj_test',
      runId: 'run_002',
      userInstruction: 'Test context pack',
      workspacePath: projectPath,
    });

    const jsonPath = join(projectPath, '.project/context', 'run_002.json');
    const mdPath = join(projectPath, '.project/context', 'run_002.md');

    expect(existsSync(jsonPath)).toBe(true);
    expect(existsSync(mdPath)).toBe(true);

    const json = JSON.parse(readFileSync(jsonPath, 'utf-8'));
    expect(json.id).toBe(pack.id);

    const md = readFileSync(mdPath, 'utf-8');
    expect(md).toContain('Context Pack');
    expect(md).toContain('## Task');
    expect(md).toContain('## Project');
    expect(md).toContain('## Git State');
    expect(md).toContain('## Relevant Files');
    expect(md).toContain('## Available Skills');
    expect(md).toContain('## Context Budget');
  });

  it('includes task context when taskId provided', async () => {
    const record = await createTaskRecord({ projectPath, userInstruction: 'Implement user authentication' });

    const pack = await buildContextPack({
      projectId: 'proj_test',
      runId: 'run_003',
      taskId: record.state.taskId,
      userInstruction: 'Implement user authentication',
      workspacePath: projectPath,
    });

    expect(pack.task.title).toBe('Implement user authentication');
    expect(pack.task.taskType).toBe('feature');
  });

  it('propagates git changes into relevant files', async () => {
    mkdirSync(join(projectPath, 'src'), { recursive: true });
    writeFileSync(join(projectPath, 'src/new-feature.ts'), 'export const x = 1;', 'utf-8');

    const pack = await buildContextPack({
      projectId: 'proj_test',
      runId: 'run_004',
      userInstruction: 'Fix login issue',
      workspacePath: projectPath,
    });

    expect(pack.git.hasUserChanges).toBe(true);
  });
});
