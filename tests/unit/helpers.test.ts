/**
 * Tests for the test helper utilities.
 *
 * Verifies that createTempWorkspace, createHarnessProjectFixture,
 * createGitRepo, and assertion utilities work correctly.
 * These tests use the helpers themselves — meta-testing.
 */

import { describe, it, expect, afterEach } from 'vitest';
import {
  createTempWorkspace,
  removeTempWorkspace,
  createHarnessProjectFixture,
  createGitRepo,
  createInitialCommit,
  writeTaskRecord,
  readJson,
  assertRedacted,
  normalizeForSnapshot,
} from '../helpers/index.js';
import fs from 'fs';
import path from 'path';

describe('createTempWorkspace', () => {
  let ws: string;

  afterEach(() => {
    if (ws) removeTempWorkspace(ws);
  });

  it('creates a writable temporary directory', () => {
    ws = createTempWorkspace();
    expect(fs.existsSync(ws)).toBe(true);
    expect(fs.statSync(ws).isDirectory()).toBe(true);
    expect(fs.accessSync(ws, fs.constants.W_OK)).toBeUndefined();
  });

  it('creates unique directories each time', () => {
    const ws1 = createTempWorkspace();
    const ws2 = createTempWorkspace();
    expect(ws1).not.toBe(ws2);
    removeTempWorkspace(ws1);
    removeTempWorkspace(ws2);
  });
});

describe('removeTempWorkspace', () => {
  it('removes an existing directory', () => {
    const ws = createTempWorkspace();
    expect(fs.existsSync(ws)).toBe(true);
    removeTempWorkspace(ws);
    expect(fs.existsSync(ws)).toBe(false);
  });

  it('does not throw on non-existent directory', () => {
    expect(() => removeTempWorkspace('/nonexistent/path/12345')).not.toThrow();
  });
});

describe('createHarnessProjectFixture', () => {
  let ws: string;

  afterEach(() => { if (ws) removeTempWorkspace(ws); });

  it('creates AGENTS.md', () => {
    ws = createTempWorkspace();
    createHarnessProjectFixture(ws);
    expect(fs.existsSync(path.join(ws, 'AGENTS.md'))).toBe(true);
  });

  it('creates required .project/ subdirectories', () => {
    ws = createTempWorkspace();
    createHarnessProjectFixture(ws);

    const requiredDirs = [
      '.project/state',
      '.project/tasks/active',
      '.project/decisions',
      '.project/context',
      '.project/reports/runs',
      '.project/reports/verification',
      '.project/checkpoints',
    ];

    for (const dir of requiredDirs) {
      expect(fs.existsSync(path.join(ws, dir))).toBe(true);
    }
  });

  it('creates a valid manifest.json', () => {
    ws = createTempWorkspace();
    createHarnessProjectFixture(ws);

    const manifest = readJson(path.join(ws, '.project/state/manifest.json'));
    expect(manifest.projectId).toBe('test-project');
    expect(manifest.version).toBeTruthy();
    expect(manifest.commands).toBeTruthy();
  });
});

describe('createGitRepo', () => {
  let ws: string;

  afterEach(() => { if (ws) removeTempWorkspace(ws); });

  it('initializes a git repository', () => {
    ws = createTempWorkspace();
    createGitRepo(ws);
    expect(fs.existsSync(path.join(ws, '.git'))).toBe(true);
  });
});

describe('writeTaskRecord', () => {
  let ws: string;

  afterEach(() => { if (ws) removeTempWorkspace(ws); });

  it('writes a valid task JSON file', () => {
    ws = createTempWorkspace();
    createHarnessProjectFixture(ws);
    const taskPath = writeTaskRecord(ws, 'task-test-1');

    expect(fs.existsSync(taskPath)).toBe(true);
    const task = readJson(taskPath);
    expect(task.taskId).toBe('task-test-1');
    expect(task.status).toBe('created');
    expect(task.createdAt).toBeTruthy();
  });
});

describe('assertRedacted', () => {
  it('rejects content containing API keys', () => {
    expect(assertRedacted('sk-proj-abcdefghijklmnopqrstuvwxyz')).toBe(false);
  });

  it('rejects content containing GitHub tokens', () => {
    expect(assertRedacted('ghp_abcdefghijklmnopqrstuvwxyz1234567890')).toBe(false);
  });

  it('rejects content containing private keys', () => {
    expect(assertRedacted('-----BEGIN RSA PRIVATE KEY-----')).toBe(false);
  });

  it('accepts clean content without secrets', () => {
    expect(assertRedacted('Hello, this is safe content.')).toBe(true);
  });

  it('accepts content with [REDACTED] placeholder', () => {
    expect(assertRedacted('The key is [REDACTED]')).toBe(true);
  });
});

describe('normalizeForSnapshot', () => {
  it('replaces ISO timestamps', () => {
    const result = normalizeForSnapshot('Created at 2026-06-11T12:00:00.000Z');
    expect(result).toContain('[TIMESTAMP]');
    expect(result).not.toMatch(/\d{4}-\d{2}-\d{2}T/);
  });

  it('replaces run IDs', () => {
    const result = normalizeForSnapshot('Run: run_abc123');
    expect(result).toContain('[RUN_ID]');
  });

  it('replaces task IDs', () => {
    const result = normalizeForSnapshot('Task: task_xyz789');
    expect(result).toContain('[TASK_ID]');
  });
});
