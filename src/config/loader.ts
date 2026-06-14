/**
 * Harness OS — Config Loader
 *
 * Layered configuration loading with merge priority and safety field enforcement.
 *
 * Resolution order (15_CONFIG_REFERENCE.md §6.1):
 *   1. Default config (hardcoded)
 *   2. Global config (~/.harness/config.json)
 *   3. Project manifest (.project/state/manifest.json)
 *   4. Environment variables
 *   5. CLI flags (passed in at runtime)
 *
 * Safety (AUD-P0-002):
 *   - Immutable fields cannot be overridden by any source
 *   - Boolean safety fields can only be tightened, never weakened
 *   - Enum fields are validated against allowed values
 *   - Array fields use union merge (append only)
 *   - All overrides are tracked at the field level
 */

import { existsSync, readFileSync, mkdirSync } from 'fs';
import { homedir } from 'os';
import { join, resolve } from 'path';
import type {
  HarnessConfig,
  LoadedConfig,
  ConfigSource,
  ConfigFieldSource,
  SafetyFieldDef,
  ConfigValidation,
} from './types.js';
import { SAFETY_FIELDS } from './types.js';
import { HARNESS_VERSION } from '../version.js';

// ============================================================
// Default Config
// ============================================================

const DEFAULT_CONFIG: HarnessConfig = {
  version: HARNESS_VERSION,
  cli: { defaultOutputMode: 'pretty', colorEnabled: true, showProgress: true },
  governance: {
    requireApprovalForDeploy: true,
    requireApprovalForPushMain: true,
    requireApprovalForDependencyAdd: true,
    requireApprovalForDeleteFile: true,
    requireApprovalForModifyAgentsMd: true,
    redactSecrets: true,
    defaultNetwork: 'restricted',
    allowWorkspaceOutsideAccess: false,
    dangerousCommands: ['rm -rf', 'sudo', 'chmod -R', 'chown -R', 'git reset --hard', 'git clean -fd', 'git push --force', 'curl | sh', 'wget | sh'],
  },
  verification: { failFast: true, timeoutMs: 300000 },
  observability: { enabled: true, secretRedaction: true },
  delivery: { requireApprovalForPr: true, requireApprovalForRelease: true, requireApprovalForDeploy: true, commitMessageFormat: 'conventional' },
  skills: { timeoutMs: 300000 },
  project: { allowAutoCommit: false, allowAutoPush: false, protectedBranches: ['main', 'master'] },
};

// ============================================================
// Path Helpers
// ============================================================

function getGlobalConfigPath(): string {
  return join(homedir(), '.harness', 'config.json');
}

function getProjectManifestPath(projectPath?: string): string | undefined {
  if (!projectPath) return undefined;
  return resolve(projectPath, '.project/state/manifest.json');
}

// ============================================================
// Deep get/set helpers for dotted paths
// ============================================================

function getFieldAtPath(obj: Record<string, unknown>, path: string): unknown {
  const parts = path.split('.');
  let current: unknown = obj;
  for (const part of parts) {
    if (current === undefined || current === null || typeof current !== 'object') return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  return current;
}

function setFieldAtPath(obj: Record<string, unknown>, path: string, value: unknown): void {
  const parts = path.split('.');
  let current = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    if (!current[part] || typeof current[part] !== 'object') {
      current[part] = {};
    }
    current = current[part] as Record<string, unknown>;
  }
  current[parts[parts.length - 1]] = value;
}

function deleteFieldAtPath(obj: Record<string, unknown>, path: string): void {
  const parts = path.split('.');
  let current = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (!current[parts[i]] || typeof current[parts[i]] !== 'object') return;
    current = current[parts[i]] as Record<string, unknown>;
  }
  delete current[parts[parts.length - 1]];
}

// ============================================================
// Safety Validation (CFG-02..05, CFG-08)
// ============================================================

/**
 * Check if a safety field override is valid according to its type.
 * Returns null if valid, or a rejection reason string if invalid.
 */
function checkSafetyOverride(
  def: SafetyFieldDef,
  currentValue: unknown,
  newValue: unknown,
): string | null {
  // Same value is always fine (no weakening)
  if (JSON.stringify(currentValue) === JSON.stringify(newValue)) return null;

  // CFG-08: Immutable fields cannot be changed at all
  if (def.immutable) {
    return `Cannot change immutable field "${def.path}" — ${def.description ?? 'no override allowed'}`;
  }

  switch (def.type) {
    case 'boolean': {
      // true = tight, false = loose.
      // Override from true→false is weakening → reject (CFG-02)
      if (currentValue === true && newValue === false) {
        return `Cannot weaken "${def.path}" from true to false — ${def.description ?? 'approval requirement cannot be disabled'}`;
      }
      return null;
    }

    case 'boolean-allow': {
      // false = tight, true = loose.
      // Override from false→true is weakening → reject (CFG-02)
      if (currentValue === false && newValue === true) {
        return `Cannot weaken "${def.path}" from false to true — ${def.description ?? 'allow setting cannot be enabled'}`;
      }
      return null;
    }

    case 'enum': {
      // Validate against known values (CFG-03)
      if (def.validValues && !def.validValues.includes(String(newValue))) {
        return `Invalid value "${String(newValue)}" for "${def.path}" — must be one of: ${def.validValues.join(', ')}`;
      }
      // For enum with known tighten direction:
      // "allowed" → "restricted" is tightening (ok)
      // "restricted" → "allowed" is weakening (reject)
      if (def.path === 'governance.defaultNetwork') {
        if (currentValue === 'restricted' && newValue === 'allowed') {
          return `Cannot weaken "${def.path}" from "restricted" to "allowed" — network restriction cannot be disabled`;
        }
      }
      return null;
    }

    case 'array': {
      // Array safety: items can only be added, never removed (CFG-04)
      // The override is treated as additions to the current list.
      // Only reject if override is an explicit attempt to clear.
      if (!Array.isArray(currentValue) || !Array.isArray(newValue)) {
        return `Cannot replace "${def.path}" — array fields use union merge (append only)`;
      }
      if (newValue.length === 0) {
        return `Cannot clear "${def.path}" — array fields use union merge (append only)`;
      }
      return null;
    }

    default:
      return null;
  }
}

/**
 * Apply a safety-approved override value to the base config.
 * For arrays, performs union merge. For other types, replaces.
 */
function applySafeOverride(
  base: HarnessConfig,
  def: SafetyFieldDef,
  newValue: unknown,
): void {
  const baseObj = base as unknown as Record<string, unknown>;

  if (def.type === 'array' && Array.isArray(newValue)) {
    // Union merge: combine current + new, deduplicate (CFG-04)
    const current = (getFieldAtPath(baseObj, def.path) as unknown[]) ?? [];
    const merged = [...current];
    for (const item of newValue) {
      if (!merged.some(existing => JSON.stringify(existing) === JSON.stringify(item))) {
        merged.push(item);
      }
    }
    setFieldAtPath(baseObj, def.path, merged);
  } else {
    setFieldAtPath(baseObj, def.path, newValue);
  }
}

// ============================================================
// Source Readers
// ============================================================

function readGlobalConfig(): { config: Partial<HarnessConfig>; source: ConfigSource } {
  const path = getGlobalConfigPath();
  const source: ConfigSource = { path, scope: 'global', valid: false };
  try {
    if (!existsSync(path)) {
      source.loadError = 'File not found';
      return { config: {}, source };
    }
    const raw = JSON.parse(readFileSync(path, 'utf-8'));
    source.valid = true;
    return { config: raw, source };
  } catch (err) {
    source.loadError = (err as Error).message;
    return { config: {}, source };
  }
}

function readProjectManifest(projectPath?: string): { config: Partial<HarnessConfig>; source: ConfigSource | null } {
  const manifestPath = getProjectManifestPath(projectPath);
  if (!manifestPath) return { config: {}, source: null };

  const source: ConfigSource = { path: manifestPath, scope: 'project', valid: false };
  try {
    if (!existsSync(manifestPath)) {
      source.loadError = 'File not found';
      return { config: {}, source };
    }
    const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));

    // Map manifest fields to config structure
    const config: Partial<HarnessConfig> = {};
    if (manifest.commands) {
      config.verification = {};
    }
    if (manifest.skills) {
      config.skills = { enabled: manifest.skills.enabled, disabled: manifest.skills.disabled };
    }
    if (manifest.defaultBranch) {
      config.project = { ...config.project, defaultBranch: manifest.defaultBranch };
    }

    source.valid = true;
    return { config, source };
  } catch (err) {
    source.loadError = (err as Error).message;
    return { config: {}, source };
  }
}

function readEnvVars(): Partial<HarnessConfig> {
  const config: Partial<HarnessConfig> = {};

  // CLI
  if (process.env.HARNESS_OUTPUT_MODE) {
    config.cli = { ...config.cli, defaultOutputMode: process.env.HARNESS_OUTPUT_MODE as 'pretty' | 'json' | 'quiet' };
  }
  if (process.env.HARNESS_NON_INTERACTIVE) {
    config.runtime = { ...config.runtime, nonInteractive: true };
  }
  if (process.env.HARNESS_LOG_LEVEL) {
    config.runtime = { ...config.runtime, logLevel: process.env.HARNESS_LOG_LEVEL as 'debug' | 'info' | 'warn' | 'error' };
  }
  if (process.env.NO_COLOR || process.env.HARNESS_NO_COLOR) {
    config.cli = { ...config.cli, colorEnabled: false };
  }
  if (process.env.CI) {
    config.cli = { ...config.cli, defaultOutputMode: 'quiet', colorEnabled: false, showProgress: false };
    config.runtime = { ...config.runtime, nonInteractive: true };
  }

  return config;
}

// ============================================================
// Field-Level Merge with Safety (CFG-01..08)
// ============================================================

/**
 * Merge a partial override into the base config using the Safety Field Registry.
 *
 * For each safety field present in the override:
 *   1. Look up its SafetyFieldDef from the registry
 *   2. Check if the override attempts to weaken the field
 *   3. If weakening → reject with warning, keep current value
 *   4. If valid → apply (with union merge for arrays)
 *   5. Track field-level source for auditability (CFG-07)
 *
 * For non-safety fields, fall through to shallow merge (original behavior).
 */
function mergeConfig(
  base: HarnessConfig,
  override: Partial<HarnessConfig>,
  sourceLabel: string,
  scope: ConfigSource['scope'],
  warnings: string[],
  fieldSources: ConfigFieldSource[],
): HarnessConfig {
  const result: Record<string, unknown> = { ...base as unknown as Record<string, unknown> };

  // Walk safety fields first for type-specific enforcement
  for (const def of SAFETY_FIELDS) {
    const currentValue = getFieldAtPath(base as any, def.path);
    const overrideValue = getFieldAtPath(override as any, def.path);

    if (overrideValue === undefined) continue; // not in override

    const rejection = checkSafetyOverride(def, currentValue, overrideValue);
    if (rejection) {
      // Rejected: keep current value, record warning and field source (CFG-07)
      warnings.push(`${sourceLabel}: ${rejection}`);
      fieldSources.push({
        path: def.path,
        value: currentValue,
        source: scope,
        rejected: true,
        rejectedReason: rejection,
      });
    } else {
      // Allowed: apply with type-specific merge semantics
      applySafeOverride(result as unknown as HarnessConfig, def, overrideValue);
      fieldSources.push({
        path: def.path,
        value: overrideValue,
        source: scope,
        rejected: false,
      });
    }

    // Remove processed safety fields from override so they don't
    // get double-processed by the shallow merge fallback below.
    deleteFieldAtPath(override as any, def.path);
  }

  // For remaining non-safety fields: shallow merge (original behavior)
  for (const key of Object.keys(override) as Array<keyof HarnessConfig>) {
    const ov = override[key];
    if (ov === undefined) continue;

    if (key === 'cli' || key === 'runtime' || key === 'project' || key === 'skills' ||
        key === 'verification' || key === 'observability' || key === 'delivery') {
      const baseVal = result[key] || {};
      const overrideVal = ov || {};
      result[key] = Object.assign({}, baseVal, overrideVal);
    }
  }

  return result as unknown as HarnessConfig;
}

// ============================================================
// Config Validation (CFG-06)
// ============================================================

/**
 * Validate the final merged config for structural correctness.
 * Returns a ConfigValidation with errors for invalid values.
 */
function validateConfig(config: HarnessConfig): ConfigValidation {
  const errors: string[] = [];

  // Validate enum fields against allowed values
  const enumFields = SAFETY_FIELDS.filter(f => f.type === 'enum');
  for (const def of enumFields) {
    const value = getFieldAtPath(config as any, def.path);
    if (value !== undefined && def.validValues && !def.validValues.includes(String(value))) {
      errors.push(`Config validation: "${def.path}" has invalid value "${String(value)}" — must be one of: ${def.validValues.join(', ')}`);
    }
  }

  // Validate dangerousCommands is always an array
  const dangerous = getFieldAtPath(config as any, 'governance.dangerousCommands');
  if (dangerous !== undefined && !Array.isArray(dangerous)) {
    errors.push('Config validation: "governance.dangerousCommands" must be an array');
  }

  // Validate protectedBranches contains main or master
  const branches = getFieldAtPath(config as any, 'project.protectedBranches') as string[] | undefined;
  if (Array.isArray(branches) && !branches.some(b => b === 'main' || b === 'master')) {
    errors.push('Config validation: "project.protectedBranches" must include "main" or "master"');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

// ============================================================
// Main Loader
// ============================================================

/**
 * Load and merge configuration from all sources.
 *
 * @param projectPath Optional project path for project-level config
 * @param cliOverrides Optional CLI flag overrides
 */
export function loadConfig(
  projectPath?: string,
  cliOverrides?: Partial<HarnessConfig>,
): LoadedConfig {
  const warnings: string[] = [];
  const sources: ConfigSource[] = [];
  const fieldSources: ConfigFieldSource[] = [];

  // 1. Default config — all field sources start as "default"
  sources.push({ path: '(defaults)', scope: 'default', valid: true });
  let config = { ...DEFAULT_CONFIG };

  // Record default values for safety fields
  for (const def of SAFETY_FIELDS) {
    const val = getFieldAtPath(config as any, def.path);
    fieldSources.push({
      path: def.path,
      value: val,
      source: 'default',
      rejected: false,
    });
  }

  // 2. Global config
  const global = readGlobalConfig();
  sources.push(global.source);
  config = mergeConfig(config, global.config, 'global', 'global', warnings, fieldSources);

  // 3. Project manifest
  const project = readProjectManifest(projectPath);
  if (project.source) {
    sources.push(project.source);
    config = mergeConfig(config, project.config, 'project', 'project', warnings, fieldSources);
  }

  // 4. Environment variables
  const env = readEnvVars();
  const envSource: ConfigSource = { path: '(environment)', scope: 'env', valid: true };
  sources.push(envSource);
  config = mergeConfig(config, env, 'env', 'env', warnings, fieldSources);

  // 5. CLI overrides
  if (cliOverrides) {
    const cliSource: ConfigSource = { path: '(cli flags)', scope: 'cli', valid: true };
    sources.push(cliSource);
    config = mergeConfig(config, cliOverrides, 'cli', 'cli', warnings, fieldSources);
  }

  // Validate final config
  const validation = validateConfig(config);

  return {
    config,
    sources,
    warnings,
    fieldSources,
    validation,
  };
}

/**
 * Ensure global config directory exists.
 */
export function ensureGlobalConfigDir(): string {
  const dir = join(homedir(), '.harness');
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  return dir;
}

/**
 * Get a specific config value with environment variable fallback.
 */
export function getConfigValue<T>(
  config: HarnessConfig,
  path: string,
  envVar?: string,
  defaultValue?: T,
): T | undefined {
  if (envVar && process.env[envVar] !== undefined) {
    return process.env[envVar] as unknown as T;
  }

  const parts = path.split('.');
  let current: any = config;
  for (const part of parts) {
    if (current === undefined || current === null) return defaultValue;
    current = current[part];
  }

  return current ?? defaultValue;
}
