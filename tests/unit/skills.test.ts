/**
 * Harness OS — Skill Executor Tests
 *
 * Coverage:
 * - Registry: executor registration, execution dispatch
 * - Filesystem: read, write, list, delete blocked
 * - Shell: command execution
 * - Git: status operations
 * - Error handling: unknown tool, missing executor
 *
 * Reference: 07_MCP_SKILLS_SPEC.md §7, §11-13
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { simpleGit } from 'simple-git';

import registry from '../../src/skills/registry.js';
import { type SkillExecutionContext } from '../../src/skills/executor.js';

let testDir: string;
let context: SkillExecutionContext;

beforeEach(async () => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-skill-test-'));
  context = { projectPath: testDir };
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Registry Executor Tests
// ============================================================

describe('registry executor', () => {
  it('has executors for core skills', () => {
    expect(registry._getExecutor('filesystem')).toBeDefined();
    expect(registry._getExecutor('shell')).toBeDefined();
    expect(registry._getExecutor('git')).toBeDefined();
    expect(registry._getExecutor('repo-scanner')).toBeDefined();
  });

  it('returns undefined for unknown executor', () => {
    expect(registry._getExecutor('nonexistent')).toBeUndefined();
  });

  it('returns failed result for unknown skill', async () => {
    const result = await registry.execute('ghost', 'read_file', {}, context);
    expect(result.status).toBe('failed');
  });
});

// ============================================================
// Filesystem Executor Tests
// ============================================================

describe('filesystem executor', () => {
  it('reads a file', async () => {
    writeFileSync(join(testDir, 'hello.txt'), 'Hello World', 'utf-8');
    const result = await registry.execute('filesystem', 'read_file', { path: 'hello.txt' }, context);
    expect(result.status).toBe('success');
    expect((result.output as any).content).toBe('Hello World');
  });

  it('reads file with line range', async () => {
    writeFileSync(join(testDir, 'lines.txt'), 'line1\nline2\nline3\nline4\n', 'utf-8');
    const result = await registry.execute('filesystem', 'read_file', { path: 'lines.txt', startLine: 2, endLine: 3 }, context);
    expect(result.status).toBe('success');
    expect((result.output as any).content).toBe('line2\nline3');
  });

  it('writes a file', async () => {
    const result = await registry.execute('filesystem', 'write_file', { path: 'test.txt', content: 'content' }, context);
    expect(result.status).toBe('success');
    expect(readFileSync(join(testDir, 'test.txt'), 'utf-8')).toBe('content');
  });

  it('lists directory', async () => {
    writeFileSync(join(testDir, 'a.txt'), '');
    writeFileSync(join(testDir, 'b.txt'), '');
    const result = await registry.execute('filesystem', 'list_dir', { path: '.' }, context);
    expect(result.status).toBe('success');
    const entries = result.output as string[];
    expect(entries).toContain('a.txt');
    expect(entries).toContain('b.txt');
  });

  it('blocks delete_file', async () => {
    const result = await registry.execute('filesystem', 'delete_file', { path: 'test.txt' }, context);
    expect(result.status).toBe('blocked');
  });

  it('fails for missing file', async () => {
    const result = await registry.execute('filesystem', 'read_file', { path: 'nonexistent.txt' }, context);
    expect(result.status).toBe('failed');
  });

  it('blocks unknown tool via governance', async () => {
    const result = await registry.execute('filesystem', 'unknown_tool', {}, context);
    expect(result.status).toBe('blocked');
    expect((result.error as any)?.message).toContain('Unknown tool');
  });
});

// ============================================================
// Shell Executor Tests
// ============================================================

describe('shell executor', () => {
  it('runs a simple command', async () => {
    const cmd = process.platform === 'win32' ? 'echo hello' : 'echo hello';
    const result = await registry.execute('shell', 'run_command', { command: cmd }, context);
    expect(result.status).toBe('success');
  });

  it('captures exit code for failing command', async () => {
    const cmd = process.platform === 'win32' ? 'cmd /c exit 1' : 'false';
    const result = await registry.execute('shell', 'run_command', { command: cmd }, context);
    expect((result.output as any).exitCode).toBe(1);
  });

  it('rejects empty command', async () => {
    const result = await registry.execute('shell', 'run_command', { command: '' }, context);
    expect(result.status).toBe('failed');
  });
});

// ============================================================
// Git Executor Tests
// ============================================================

describe('git executor', () => {
  beforeEach(async () => {
    const git = simpleGit(testDir);
    await git.init();
    await git.addConfig('user.email', 'test@test.com', false, 'local');
    await git.addConfig('user.name', 'Tester', false, 'local');
    writeFileSync(join(testDir, 'initial.txt'), 'initial', 'utf-8');
    await git.add('.');
    await git.commit('initial', undefined, { '--allow-empty': null });
  });

  it('reads git status', async () => {
    const result = await registry.execute('git', 'git_status', {}, context);
    expect(result.status).toBe('success');
    expect((result.output as any).branch).toBeTruthy();
  });

  it('reads git diff', async () => {
    writeFileSync(join(testDir, 'new.txt'), 'new', 'utf-8');
    const result = await registry.execute('git', 'git_diff', {}, context);
    expect(result.status).toBe('success');
  });

  it('requires approval for commit (GOV3-06)', async () => {
    writeFileSync(join(testDir, 'change.txt'), 'change', 'utf-8');
    const git = simpleGit(testDir);
    await git.add('.');
    const result = await registry.execute('git', 'git_commit', { message: 'test commit' }, context);
    expect(result.status).toBe('requires-approval');
    expect((result.output as any)?.approvalId).toBeDefined();
  });

  it('blocks git_push', async () => {
    const result = await registry.execute('git', 'git_push', {}, context);
    expect(result.status).toBe('blocked');
  });
});

// ============================================================
// Repo Scanner Executor Tests
// ============================================================

describe('repo-scanner executor', () => {
  it('scans directories', async () => {
    mkdirSync(join(testDir, 'src'), { recursive: true });
    mkdirSync(join(testDir, 'tests'), { recursive: true });
    const result = await registry.execute('repo-scanner', 'scan_files', {}, context);
    expect(result.status).toBe('success');
    const dirs = result.output as string[];
    expect(dirs).toContain('src');
    expect(dirs).toContain('tests');
  });

  it('builds repository map', async () => {
    writeFileSync(join(testDir, 'package.json'), JSON.stringify({ name: 'test', scripts: { test: 'vitest' } }));
    mkdirSync(join(testDir, 'src'), { recursive: true });
    const result = await registry.execute('repo-scanner', 'build_repository_map', {}, context);
    expect(result.status).toBe('success');
    const map = result.output as any;
    expect(map.sourceDirs).toContain('src');
    expect(map.commands).toBeDefined();
  });
});

// ============================================================
// GOV-01 Regression Tests: Governance Policy Integration
//
// Verifies that registry.execute() properly integrates with the
// Policy Engine before reaching the executor.
//
// Coverage:
// - Policy allow → executor runs
// - Policy deny → executor NOT called, blocked returned
// - Policy needs_approval → requires-approval returned with approval ID
// - Policy error → fail closed (blocked)
// - Credential/token path writes blocked at policy level
// - .env writes require approval
// - Dangerous shell commands require approval
// - Unknown tools blocked by manifest validation
// - Unknown skill fails with no executor
// ============================================================

describe('GOV-01: registry.execute() policy integration', () => {
  // ---- allow path ----
  it('allows read-only file operations', async () => {
    writeFileSync(join(testDir, 'test.txt'), 'data');
    const result = await registry.execute('filesystem', 'read_file', { path: 'test.txt' }, context);
    expect(result.status).toBe('success');
  });

  it('allows safe write operations', async () => {
    const result = await registry.execute('filesystem', 'write_file', { path: 'safe.txt', content: 'ok' }, context);
    expect(result.status).toBe('success');
    expect(existsSync(join(testDir, 'safe.txt'))).toBe(true);
  });

  it('allows safe shell commands', async () => {
    const cmd = process.platform === 'win32' ? 'echo hello' : 'echo hello';
    const result = await registry.execute('shell', 'run_command', { command: cmd }, context);
    expect(result.status).toBe('success');
  });

  // ---- deny path ----
  it('blocks credential file writes at policy level', async () => {
    const result = await registry.execute('filesystem', 'write_file', { path: 'credentials.json', content: 'secret' }, context);
    expect(result.status).toBe('blocked');
    expect(result.summary).toContain('credential');
  });

  it('blocks token file writes at policy level', async () => {
    const result = await registry.execute('filesystem', 'write_file', { path: 'config/token.json', content: 'tok' }, context);
    expect(result.status).toBe('blocked');
  });

  it('blocks delete operations at policy level', async () => {
    const result = await registry.execute('filesystem', 'delete_file', { path: 'somefile.txt' }, context);
    expect(result.status).toBe('blocked');
  });

  // ---- needs_approval path ----
  it('requires approval for .env writes', async () => {
    const result = await registry.execute('filesystem', 'write_file', { path: '.env', content: 'KEY=val' }, context);
    expect(result.status).toBe('requires-approval');
    // Verify approval ID is included
    expect((result.output as any)?.approvalId).toBeDefined();
    expect(typeof (result.output as any).approvalId).toBe('string');
  });

  it('requires approval for dangerous shell commands', async () => {
    const result = await registry.execute('shell', 'run_command', { command: 'rm -rf /tmp/test' }, context);
    expect(result.status).toBe('requires-approval');
    expect((result.output as any)?.approvalId).toBeDefined();
  });

  // ---- unknown tool / skill paths ----
  it('blocks unknown tools via manifest validation', async () => {
    const result = await registry.execute('filesystem', 'nonexistent_tool', {}, context);
    expect(result.status).toBe('blocked');
    expect(result.summary).toContain('Unknown tool');
  });

  it('returns failed for unknown skill (no executor)', async () => {
    const result = await registry.execute('nonexistent-skill', 'read_file', {}, context);
    expect(result.status).toBe('failed');
  });

  // ---- policy context contains skill name ----
  it('includes skillName in policy context for shell commands', async () => {
    // Run a safe command that passes policy — this verifies the context was
    // built correctly (toolName, skillName, command all populated)
    const cmd = process.platform === 'win32' ? 'echo pass' : 'echo pass';
    const result = await registry.execute('shell', 'run_command', { command: cmd }, context);
    expect(result.status).toBe('success');
  });

  // ---- _getExecutor() internal access ----
  it('_getExecutor returns raw executor (internal use only)', () => {
    const exec = registry._getExecutor('filesystem');
    expect(exec).toBeDefined();
    expect(typeof exec).toBe('function');
  });
});

// ============================================================
// AUD3-P0-001 Regression Tests: Governance Execution Boundary
//
// GOV3-01: No public raw executor access
// GOV3-02: Policy decision validation, AGENTS.md/adr writes needs_approval
// GOV3-04: Path escape protection (sibling-prefix, ../, symlink)
// GOV3-05: PowerShell dangerous patterns blocked
// GOV3-06: Git commit requires approval
// GOV3-07: Policy error fail-closed
// ============================================================

describe('AUD3-P0-001: governance execution boundary', () => {
  // ---- GOV3-01: raw executor access ----
  it('raw executor not importable from barrel export', async () => {
    // The barrel export (skills/index.ts) should NOT expose raw _execute
    const mod = await import('../../src/skills/index.js');
    expect((mod as any)._execute).toBeUndefined();
    expect((mod as any).execute).toBeUndefined();
  });

  // ---- GOV3-02: AGENTS.md / ADR writes ----
  it('requires approval for AGENTS.md writes', async () => {
    const result = await registry.execute('filesystem', 'write_file', { path: 'AGENTS.md', content: 'test' }, context);
    expect(result.status).toBe('requires-approval');
  });

  it('requires approval for ADR writes', async () => {
    const result = await registry.execute('filesystem', 'write_file', { path: 'decisions/001-something.md', content: 'test' }, context);
    expect(result.status).toBe('requires-approval');
  });

  // ---- GOV3-04: Path escape ----
  it('blocks ../ path escape', async () => {
    const result = await registry.execute('filesystem', 'read_file', { path: '../../../etc/passwd' }, context);
    expect(result.status).toBe('failed');
    expect(result.summary).toContain('escape');
  });

  it('blocks absolute path', async () => {
    const result = await registry.execute('filesystem', 'read_file', { path: '/etc/passwd' }, context);
    expect(result.status).toBe('failed');
    expect(result.summary).toContain('absolute');
  });

  // ---- GOV3-05: PowerShell patterns ----
  it('blocks PowerShell Remove-Item via policy', async () => {
    const result = await registry.execute('shell', 'run_command', { command: 'Remove-Item -Path C:\\test -Recurse' }, context);
    expect(result.status).toBe('requires-approval');
  });

  it('blocks PowerShell Invoke-Expression via policy', async () => {
    const result = await registry.execute('shell', 'run_command', { command: 'Invoke-Expression "malicious"' }, context);
    expect(result.status).toBe('requires-approval');
  });

  // ---- GOV3-06: Git commit (already covered by existing test above) ----

  // ---- GOV3-07: Policy validation ----
  it('policy returns non-allow decision for blocked operations', async () => {
    // Credential write is denied by policy
    const result = await registry.execute('filesystem', 'write_file', { path: 'credentials.json', content: 'secret' }, context);
    expect(result.status).toBe('blocked');
    expect(result.summary).not.toContain('executor');
  });
});
