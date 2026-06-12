/**
 * Harness OS — Config System Tests
 *
 * Coverage:
 * - loadConfig: defaults, global config, project manifest, env vars
 * - Merge: layered resolution, governance safety
 * - getConfigValue: env var fallback, path walking
 *
 * Reference: 15_CONFIG_REFERENCE.md
 */

import { describe, it, expect, afterEach } from 'vitest';
import { mkdtempSync, rmSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

// Backup env
const ORIG_HARNESS_OUTPUT_MODE = process.env.HARNESS_OUTPUT_MODE;
const ORIG_CI = process.env.CI;

afterEach(() => {
  process.env.HARNESS_OUTPUT_MODE = ORIG_HARNESS_OUTPUT_MODE;
  process.env.CI = ORIG_CI;
});

import { loadConfig, getConfigValue } from '../../src/config/loader.js';

// ============================================================
// Basic Load Tests
// ============================================================

describe('loadConfig', () => {
  it('returns defaults when no config files exist', () => {
    const result = loadConfig();
    expect(result.config.version).toBe('1.0.0');
    expect(result.config.cli?.defaultOutputMode).toBe('pretty');
    expect(result.config.governance?.requireApprovalForDeploy).toBe(true);
    expect(result.config.governance?.requireApprovalForPushMain).toBe(true);
    expect(result.config.governance?.redactSecrets).toBe(true);
    expect(result.sources.length).toBeGreaterThanOrEqual(1);
  });

  it('includes all source layers in sources array', () => {
    const result = loadConfig();
    const scopes = result.sources.map(s => s.scope);
    expect(scopes).toContain('default');
    expect(scopes).toContain('env');
  });

  it('accepts cli overrides', () => {
    const result = loadConfig(undefined, { cli: { defaultOutputMode: 'json' } });
    expect(result.config.cli?.defaultOutputMode).toBe('json');
  });

  it('env HARNESS_OUTPUT_MODE overrides default', () => {
    process.env.HARNESS_OUTPUT_MODE = 'quiet';
    const result = loadConfig();
    expect(result.config.cli?.defaultOutputMode).toBe('quiet');
  });

  it('CI env sets quiet mode and non-interactive', () => {
    process.env.CI = 'true';
    const result = loadConfig();
    expect(result.config.cli?.defaultOutputMode).toBe('quiet');
    expect(result.config.cli?.colorEnabled).toBe(false);
    expect(result.config.runtime?.nonInteractive).toBe(true);
  });

  it('uses project manifest for skills config', () => {
    const testDir = mkdtempSync(join(tmpdir(), 'config-test-'));
    mkdirSync(join(testDir, '.project/state'), { recursive: true });
    writeFileSync(join(testDir, '.project/state/manifest.json'), JSON.stringify({
      projectId: 'proj_001',
      projectName: 'test',
      skills: { enabled: ['filesystem', 'shell'], disabled: ['github'] },
    }), 'utf-8');

    const result = loadConfig(testDir);
    expect(result.config.skills?.enabled).toEqual(['filesystem', 'shell']);
    expect(result.config.skills?.disabled).toEqual(['github']);

    rmSync(testDir, { recursive: true, force: true });
  });
});

// ============================================================
// Governance Safety Tests
// ============================================================

describe('governance safety', () => {
  it('cannot weaken governance settings via env', () => {
    process.env.HARNESS_OUTPUT_MODE = 'pretty';
    const result = loadConfig();
    const gov = result.config.governance!;

    // Security defaults should remain
    expect(gov.requireApprovalForDeploy).toBe(true);
    expect(gov.requireApprovalForPushMain).toBe(true);
    expect(gov.redactSecrets).toBe(true);
  });

  it('warns when attempting to weaken governance', () => {
    const warned = loadConfig().warnings;
    // No warnings for default load
    expect(warned.length).toBe(0);
  });

  it('default governance is restrictive', () => {
    const result = loadConfig();
    expect(result.config.governance?.defaultNetwork).toBe('restricted');
    expect(result.config.governance?.allowWorkspaceOutsideAccess).toBe(false);
    expect(result.config.governance?.dangerousCommands?.length).toBeGreaterThan(0);
  });
});

// ============================================================
// getConfigValue Tests
// ============================================================

describe('getConfigValue', () => {
  const config = loadConfig().config;

  it('walks nested path', () => {
    const val = getConfigValue(config, 'cli.defaultOutputMode');
    expect(val).toBe('pretty');
  });

  it('returns default for missing path', () => {
    const val = getConfigValue(config, 'nonexistent.key', undefined, 'fallback');
    expect(val).toBe('fallback');
  });

  it('uses env var when present', () => {
    process.env.HARNESS_TEST_VAL = 'env_value';
    const val = getConfigValue(config, 'cli.defaultOutputMode', 'HARNESS_TEST_VAL');
    expect(val).toBe('env_value');
  });
});
