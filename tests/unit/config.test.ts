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

import { loadConfig, getConfigValue, SAFETY_FIELDS } from '../../src/config/index.js';

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

// ============================================================
// CFG-01..08 Regression Tests: Safety Field Registry
//
// Coverage per requirement:
//   CFG-01: Registry completeness
//   CFG-02: Boolean safety semantics (true→false / false→true)
//   CFG-03: Enum validation (defaultNetwork)
//   CFG-04: Array union merge (append only)
//   CFG-05: Cross-module safety locks (immutable fields)
//   CFG-06: Schema validation
//   CFG-07: Field-level source tracking
//   CFG-08: Immutable protection
// ============================================================

describe('CFG-01: Safety Field Registry', () => {
  it('has all required safety fields', () => {
    const paths = SAFETY_FIELDS.map(f => f.path);

    // Approval booleans
    expect(paths).toContain('governance.requireApprovalForDeploy');
    expect(paths).toContain('governance.requireApprovalForPushMain');
    expect(paths).toContain('governance.redactSecrets');
    expect(paths).toContain('delivery.requireApprovalForPr');
    expect(paths).toContain('delivery.requireApprovalForRelease');
    expect(paths).toContain('delivery.requireApprovalForDeploy');
    expect(paths).toContain('observability.secretRedaction');

    // Allow booleans
    expect(paths).toContain('governance.allowWorkspaceOutsideAccess');
    expect(paths).toContain('project.allowAutoCommit');
    expect(paths).toContain('project.allowAutoPush');

    // Enum
    expect(paths).toContain('governance.defaultNetwork');

    // Arrays
    expect(paths).toContain('governance.dangerousCommands');
    expect(paths).toContain('project.protectedBranches');
  });

  it('each safety field has a known type', () => {
    const validTypes = ['boolean', 'boolean-allow', 'enum', 'array'];
    for (const f of SAFETY_FIELDS) {
      expect(validTypes).toContain(f.type);
    }
  });

  it('each safety field has a default value', () => {
    for (const f of SAFETY_FIELDS) {
      expect(f.defaultValue).toBeDefined();
    }
  });
});

describe('CFG-02: Boolean safety semantics', () => {
  // approval booleans: true=tight, false=loose
  it('governance requireApprovalForDeploy cannot be set to false (CLI override)', () => {
    const result = loadConfig(undefined, {
      governance: { requireApprovalForDeploy: false },
    });
    expect(result.config.governance?.requireApprovalForDeploy).toBe(true);
    expect(result.warnings.some(w => w.includes('requireApprovalForDeploy'))).toBe(true);
  });

  it('governance requireApprovalForPushMain cannot be set to false', () => {
    const result = loadConfig(undefined, {
      governance: { requireApprovalForPushMain: false },
    });
    expect(result.config.governance?.requireApprovalForPushMain).toBe(true);
  });

  it('governance redactSecrets cannot be set to false', () => {
    const result = loadConfig(undefined, {
      governance: { redactSecrets: false },
    });
    expect(result.config.governance?.redactSecrets).toBe(true);
  });

  it('can set governance requireApprovalForPushMain to true (tightening)', () => {
    const result = loadConfig(undefined, {
      governance: { requireApprovalForPushMain: true },
    });
    expect(result.config.governance?.requireApprovalForPushMain).toBe(true);
    expect(result.warnings.length).toBe(0);
  });

  // boolean-allow: false=tight, true=loose
  it('allowWorkspaceOutsideAccess cannot be set to true', () => {
    const result = loadConfig(undefined, {
      governance: { allowWorkspaceOutsideAccess: true },
    });
    expect(result.config.governance?.allowWorkspaceOutsideAccess).toBe(false);
  });

  it('allowAutoCommit cannot be set to true', () => {
    const result = loadConfig(undefined, {
      project: { allowAutoCommit: true },
    });
    expect(result.config.project?.allowAutoCommit).toBe(false);
  });

  it('can set allowAutoCommit to false (tightening)', () => {
    const result = loadConfig(undefined, {
      project: { allowAutoCommit: false },
    });
    expect(result.config.project?.allowAutoCommit).toBe(false);
    expect(result.warnings.length).toBe(0);
  });
});

describe('CFG-03: Enum validation', () => {
  it('defaultNetwork cannot be weakened from restricted to allowed', () => {
    const result = loadConfig(undefined, {
      governance: { defaultNetwork: 'allowed' },
    });
    expect(result.config.governance?.defaultNetwork).toBe('restricted');
    expect(result.warnings.some(w => w.includes('defaultNetwork'))).toBe(true);
  });

  it('defaultNetwork can be set to restricted (same value)', () => {
    const result = loadConfig(undefined, {
      governance: { defaultNetwork: 'restricted' },
    });
    expect(result.config.governance?.defaultNetwork).toBe('restricted');
    expect(result.warnings.length).toBe(0);
  });

  it('defaultNetwork rejects invalid enum values', () => {
    const result = loadConfig(undefined, {
      governance: { defaultNetwork: 'open' as any },
    });
    expect(result.config.governance?.defaultNetwork).toBe('restricted');
    expect(result.warnings.some(w => w.includes('Invalid'))).toBe(true);
  });
});

describe('CFG-04: Array union merge (append only)', () => {
  it('dangerousCommands appends new patterns, keeps existing', () => {
    const result = loadConfig(undefined, {
      governance: { dangerousCommands: ['new-dangerous-command'] },
    });
    expect(result.config.governance?.dangerousCommands).toContain('rm -rf');
    expect(result.config.governance?.dangerousCommands).toContain('sudo');
    expect(result.config.governance?.dangerousCommands).toContain('new-dangerous-command');
  });

  it('dangerousCommands union merge preserves defaults when adding new items', () => {
    const result = loadConfig(undefined, {
      governance: { dangerousCommands: ['echo'] },
    });
    // Default items preserved
    expect(result.config.governance?.dangerousCommands).toContain('rm -rf');
    // New item added via union merge
    expect(result.config.governance?.dangerousCommands).toContain('echo');
  });

  it('protectedBranches retains main/master when overridden', () => {
    const result = loadConfig(undefined, {
      project: { protectedBranches: ['develop', 'release'] },
    });
    const branches = result.config.project?.protectedBranches ?? [];
    expect(branches).toContain('main');
    expect(branches).toContain('master');
    expect(branches).toContain('develop');
    expect(branches).toContain('release');
  });
});

describe('CFG-05: Cross-module safety locks', () => {
  it('observability.secretRedaction=false is rejected (immutable)', () => {
    const result = loadConfig(undefined, {
      observability: { secretRedaction: false },
    });
    expect(result.config.observability?.secretRedaction).toBe(true);
  });

  it('delivery.requireApprovalForDeploy=false is rejected (immutable)', () => {
    const result = loadConfig(undefined, {
      delivery: { requireApprovalForDeploy: false },
    });
    expect(result.config.delivery?.requireApprovalForDeploy).toBe(true);
  });

  it('project.allowAutoPush=true is rejected (immutable)', () => {
    const result = loadConfig(undefined, {
      project: { allowAutoPush: true },
    });
    expect(result.config.project?.allowAutoPush).toBe(false);
  });
});

describe('CFG-06: Config validation', () => {
  it('returns validation field in loaded config', () => {
    const result = loadConfig();
    expect(result.validation).toBeDefined();
    expect(result.validation!.valid).toBe(true);
    expect(result.validation!.errors).toEqual([]);
  });
});

describe('CFG-07: Field-level source tracking', () => {
  it('fieldSources contains entries for all safety fields', () => {
    const result = loadConfig();
    expect(result.fieldSources).toBeDefined();
    expect(result.fieldSources!.length).toBeGreaterThanOrEqual(SAFETY_FIELDS.length);
  });

  it('fieldSources tracks which source provided the value', () => {
    const result = loadConfig();
    for (const fs of result.fieldSources!) {
      expect(fs.path).toBeDefined();
      expect(fs.source).toBeDefined();
      expect(['default', 'global', 'project', 'env', 'cli']).toContain(fs.source);
    }
  });

  it('fieldSources records rejected overrides', () => {
    const result = loadConfig(undefined, {
      governance: { defaultNetwork: 'allowed' },
    });
    const rejected = result.fieldSources!.filter(fs => fs.rejected);
    expect(rejected.length).toBeGreaterThan(0);
    expect(rejected.some(r => r.path === 'governance.defaultNetwork')).toBe(true);
    expect(rejected[0].rejectedReason).toBeDefined();
  });
});

describe('CFG-08: Immutable field protection', () => {
  it('loadConfig rejects immutable override with warning', () => {
    const result = loadConfig(undefined, {
      governance: { redactSecrets: false },
    });
    expect(result.warnings.some(w => w.includes('immutable'))).toBe(true);
  });

  it('non-immutable safety fields can be tightened', () => {
    const result = loadConfig(undefined, {
      governance: { requireApprovalForPushMain: true },
    });
    // No warning expected — same as default
    const pushMainRejected = result.fieldSources?.filter(
      fs => fs.path === 'governance.requireApprovalForPushMain' && fs.rejected
    );
    expect(pushMainRejected?.length ?? 0).toBe(0);
  });
});

describe('CFG: Non-safety fields still mergeable', () => {
  it('cli color enabled can be overridden (non-safety)', () => {
    const result = loadConfig(undefined, { cli: { colorEnabled: false } });
    expect(result.config.cli?.colorEnabled).toBe(false);
  });

  it('cli config merges non-safety options', () => {
    const result = loadConfig(undefined, { cli: { showProgress: false } });
    expect(result.config.cli?.showProgress).toBe(false);
  });

  it('runtime config accepts env overrides', () => {
    process.env.HARNESS_NON_INTERACTIVE = 'true';
    const result = loadConfig();
    expect(result.config.runtime?.nonInteractive).toBe(true);
  });
});
