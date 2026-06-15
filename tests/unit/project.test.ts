/**
 * Harness OS — Project Manager Tests
 *
 * Coverage (Phase 1):
 * - create: project directory, .gitignore, AGENTS.md, .project/ structure,
 *   manifest.json, tech-stack.md, repository-map.md, git commit
 * - open: path validation, git repo check, AGENTS.md check, .project/ integrity,
 *   manifest reading, git status, warnings
 * - init: missing structure creation, AGENTS.md injection, manifest generation
 * - repair: missing dir fix, manifest update, AGENTS.md section check
 *
 * Reference: 11_ACCEPTANCE_CRITERIA.md §5
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, mkdirSync, writeFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { simpleGit } from 'simple-git';
import { createProject, detectTechStack, buildRepositoryMap } from '../../src/project/create.js';
import { openProject } from '../../src/project/open.js';
import { initProject, repairProject } from '../../src/project/repair.js';

let testDir: string;

beforeEach(() => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-project-test-'));
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Create Tests
// ============================================================

describe('createProject', () => {
  it('creates project directory with .git', async () => {
    const result = await createProject({ name: 'demo', path: testDir });
    expect(existsSync(join(testDir, '.git'))).toBe(true);
    expect(result.path).toBe(testDir);
  });

  it('rejects .git indirection that points outside the target repo', async () => {
    const targetDir = join(testDir, 'indirected');
    const externalGitDir = join(testDir, 'external-git');
    mkdirSync(targetDir, { recursive: true });
    mkdirSync(externalGitDir, { recursive: true });
    const git = simpleGit(externalGitDir);
    await git.init();
    writeFileSync(join(targetDir, '.git'), `gitdir: ${externalGitDir.replace(/\\/g, '/')}\n`, 'utf-8');

    await expect(createProject({ name: 'demo', path: targetDir })).rejects.toThrow(
      /Git root|unable to verify Git repository root/,
    );
  });

  it('creates .gitignore with Harness entries', async () => {
    await createProject({ name: 'demo', path: testDir });
    const gitignore = readFileSync(join(testDir, '.gitignore'), 'utf-8');
    expect(gitignore).toContain('.project/context/');
    expect(gitignore).toContain('.env');
    expect(gitignore).toContain('node_modules/');
  });

  it('creates AGENTS.md with required sections', async () => {
    await createProject({ name: 'demo', path: testDir });
    const agentsMd = readFileSync(join(testDir, 'AGENTS.md'), 'utf-8');
    expect(agentsMd).toContain('Project Identity');
    expect(agentsMd).toContain('Project Name: demo');
    expect(agentsMd).toContain('Architecture Rules');
    expect(agentsMd).toContain('Permission and Approval Rules');
    expect(agentsMd).toContain('Task Completion Rules');
  });

  it('creates all .project/ subdirectories', async () => {
    await createProject({ name: 'demo', path: testDir });
    const dirs = [
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
    for (const dir of dirs) {
      expect(existsSync(join(testDir, dir))).toBe(true);
    }
  });

  it('creates manifest.json with required fields', async () => {
    await createProject({ name: 'demo', path: testDir });
    const manifest = JSON.parse(readFileSync(join(testDir, '.project/state/manifest.json'), 'utf-8'));
    expect(manifest.projectId).toBeTruthy();
    expect(manifest.projectName).toBe('demo');
    expect(manifest.version).toMatch(/^1\.0\.0/);
    expect(manifest.commands).toBeDefined();
    expect(manifest.skills.enabled).toContain('filesystem');
  });

  it('creates project.md', async () => {
    await createProject({ name: 'demo', path: testDir });
    const projectMd = readFileSync(join(testDir, '.project/state/project.md'), 'utf-8');
    expect(projectMd).toContain('demo');
    expect(projectMd).toContain('Harness OS');
  });

  it('creates tech-stack.md', async () => {
    await createProject({ name: 'demo', path: testDir });
    const techStack = readFileSync(join(testDir, '.project/state/tech-stack.md'), 'utf-8');
    expect(techStack).toContain('Tech Stack');
    expect(techStack).toContain('Commands');
  });

  it('creates repository-map.md', async () => {
    await createProject({ name: 'demo', path: testDir });
    const repoMap = readFileSync(join(testDir, '.project/state/repository-map.md'), 'utf-8');
    expect(repoMap).toContain('Repository Map');
  });

  it('creates an initial git commit', async () => {
    await createProject({ name: 'demo', path: testDir });
    const git = simpleGit(testDir);
    const log = await git.log({ maxCount: 1 });
    expect(log.latest).toBeDefined();
    expect(log.latest!.message).toContain('Initial Harness OS');
  });

  it('creates an initial checkpoint file', async () => {
    await createProject({ name: 'demo', path: testDir });
    const checkpointsDir = join(testDir, '.project/checkpoints');
    const entries = readdirSync(checkpointsDir);
    expect(entries.length).toBeGreaterThan(0);
    expect(entries[0]).toMatch(/^cp_/);
  });

  it('returns correct result object', async () => {
    const result = await createProject({ name: 'demo', path: testDir });
    expect(result.projectId).toMatch(/^proj_/);
    expect(result.name).toBe('demo');
    expect(result.path).toBe(testDir);
    expect(result.agentsMdCreated).toBe(true);
    expect(result.checkpointId).toMatch(/^cp_/);
  });
});

// ============================================================
// Open Tests
// ============================================================

describe('openProject', () => {
  it('returns error for non-existent path', async () => {
    const result = await openProject(join(testDir, 'nonexistent'));
    expect(result.ready).toBe(false);
    expect(result.warnings.length).toBeGreaterThan(0);
  });

  it('returns error for non-git directory', async () => {
    mkdirSync(join(testDir, 'plain-dir'));
    const result = await openProject(join(testDir, 'plain-dir'));
    expect(result.ready).toBe(false);
    expect(result.warnings.some(w => w.includes('Git'))).toBe(true);
  });

  it('opens a valid Harness project as ready', async () => {
    await createProject({ name: 'valid-project', path: testDir });
    const result = await openProject(testDir);
    expect(result.ready).toBe(true);
    expect(result.hasAgentsMd).toBe(true);
    expect(result.hasManifest).toBe(true);
    expect(result.projectDirsOk).toBe(true);
    expect(result.name).toBe('valid-project');
  });

  it('detects missing AGENTS.md', async () => {
    await createProject({ name: 'test', path: testDir });
    rmSync(join(testDir, 'AGENTS.md'), { force: true });
    const result = await openProject(testDir);
    expect(result.hasAgentsMd).toBe(false);
    expect(result.ready).toBe(false);
    expect(result.warnings.some(w => w.includes('AGENTS.md'))).toBe(true);
  });

  it('detects missing .project/ subdirectories', async () => {
    await createProject({ name: 'test', path: testDir });
    rmSync(join(testDir, '.project/context'), { recursive: true, force: true });
    const result = await openProject(testDir);
    expect(result.projectDirsOk).toBe(false);
    expect(result.warnings.some(w => w.includes('context'))).toBe(true);
  });

  it('detects uncommitted changes', async () => {
    await createProject({ name: 'test', path: testDir });
    writeFileSync(join(testDir, 'new-file.txt'), 'hello');
    const result = await openProject(testDir);
    expect(result.hasUserChanges).toBe(true);
  });
});

// ============================================================
// Init Tests
// ============================================================

describe('initProject', () => {
  it('creates .project/ structure in an existing git repo', async () => {
    const git = simpleGit(testDir);
    await git.init();
    writeFileSync(join(testDir, 'README.md'), '# test');

    const result = await initProject(testDir);
    expect(existsSync(join(testDir, '.project/state'))).toBe(true);
    expect(existsSync(join(testDir, '.project/tasks/active'))).toBe(true);
    expect(result.dirsCreated.length).toBeGreaterThan(0);
  });

  it('creates AGENTS.md when missing', async () => {
    const git = simpleGit(testDir);
    await git.init();
    await initProject(testDir);
    expect(existsSync(join(testDir, 'AGENTS.md'))).toBe(true);
    const content = readFileSync(join(testDir, 'AGENTS.md'), 'utf-8');
    expect(content).toContain('Project Identity');
  });

  it('creates manifest.json when missing', async () => {
    const git = simpleGit(testDir);
    await git.init();
    await initProject(testDir);
    expect(existsSync(join(testDir, '.project/state/manifest.json'))).toBe(true);
    const manifest = JSON.parse(readFileSync(join(testDir, '.project/state/manifest.json'), 'utf-8'));
    expect(manifest.projectId).toMatch(/^proj_/);
  });

  it('detects existing AGENTS.md sections', async () => {
    const git = simpleGit(testDir);
    await git.init();
    writeFileSync(join(testDir, 'AGENTS.md'), '# Test\n\n## 1. Project Identity\n\nName: test\n', 'utf-8');
    await initProject(testDir);
    // Verify it didn't break
    expect(existsSync(join(testDir, '.project/state/manifest.json'))).toBe(true);
  });

  it('creates tech-stack.md and repository-map.md', async () => {
    const git = simpleGit(testDir);
    await git.init();
    writeFileSync(join(testDir, 'package.json'), JSON.stringify({ name: 'test', scripts: {} }));
    await initProject(testDir);
    expect(existsSync(join(testDir, '.project/state/tech-stack.md'))).toBe(true);
    expect(existsSync(join(testDir, '.project/state/repository-map.md'))).toBe(true);
  });
});

// ============================================================
// Repair Tests
// ============================================================

describe('repairProject', () => {
  it('repairs missing .project/ directories', async () => {
    await createProject({ name: 'test', path: testDir });
    rmSync(join(testDir, '.project/checkpoints'), { recursive: true, force: true });
    rmSync(join(testDir, '.project/sessions'), { recursive: true, force: true });

    const result = await repairProject(testDir);
    expect(result.dirsCreated.length).toBe(2);
    expect(existsSync(join(testDir, '.project/checkpoints'))).toBe(true);
    expect(existsSync(join(testDir, '.project/sessions'))).toBe(true);
  });

  it('returns warning for non-existent path', async () => {
    const result = await repairProject(join(testDir, 'ghost'));
    expect(result.warnings.length).toBeGreaterThan(0);
  });

  it('refreshes tech-stack.md', async () => {
    await createProject({ name: 'test', path: testDir });
    writeFileSync(join(testDir, '.project/state/tech-stack.md'), 'corrupted', 'utf-8');
    await repairProject(testDir);
    const content = readFileSync(join(testDir, '.project/state/tech-stack.md'), 'utf-8');
    expect(content).toContain('Tech Stack');
    expect(content).toContain('refreshed by repair');
  });

  it('detects missing AGENTS.md and warns', async () => {
    await createProject({ name: 'test', path: testDir });
    rmSync(join(testDir, 'AGENTS.md'), { force: true });

    const result = await repairProject(testDir);
    expect(result.warnings.some(w => w.includes('AGENTS.md'))).toBe(true);
  });
});

// ============================================================
// Tech Stack Detection Tests
// ============================================================

describe('detectTechStack', () => {
  it('detects TypeScript Node.js project from package.json', () => {
    writeFileSync(join(testDir, 'package.json'), JSON.stringify({
      name: 'test',
      scripts: { test: 'vitest', build: 'tsup' },
      engines: { node: '>=18' },
    }));
    const result = detectTechStack(testDir);
    expect(result.primaryLanguage).toBe('TypeScript');
    expect(result.runtime).toContain('Node.js');
  });

  it('detects pnpm from pnpm-lock.yaml', () => {
    writeFileSync(join(testDir, 'package.json'), JSON.stringify({ name: 'test', scripts: {} }));
    writeFileSync(join(testDir, 'pnpm-lock.yaml'), '');
    const result = detectTechStack(testDir);
    expect(result.packageManager).toBe('pnpm');
  });

  it('returns defaults for empty directory', () => {
    const result = detectTechStack(testDir);
    expect(result.primaryLanguage).toBe('unknown');
    expect(result.runtime).toBe('unknown');
  });
});

// ============================================================
// Repository Map Tests
// ============================================================

describe('buildRepositoryMap', () => {
  it('detects source and test directories', () => {
    mkdirSync(join(testDir, 'src'), { recursive: true });
    mkdirSync(join(testDir, 'tests'), { recursive: true });
    const map = buildRepositoryMap(testDir);
    expect(map.sourceDirs).toContain('src');
    expect(map.testDirs).toContain('tests');
  });

  it('detects config files', () => {
    writeFileSync(join(testDir, 'tsconfig.json'), '{}');
    writeFileSync(join(testDir, 'package.json'), '{}');
    const map = buildRepositoryMap(testDir);
    expect(map.configFiles).toContain('tsconfig.json');
    expect(map.packageFiles).toContain('package.json');
  });

  it('returns empty arrays for empty directory', () => {
    const map = buildRepositoryMap(testDir);
    expect(map.sourceDirs).toEqual([]);
    expect(map.configFiles).toEqual([]);
  });
});
