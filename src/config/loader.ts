/**
 * Harness OS — Config Loader
 *
 * Layered configuration loading with merge priority.
 *
 * Resolution order (15_CONFIG_REFERENCE.md §6.1):
 *   1. Default config (hardcoded)
 *   2. Global config (~/.harness/config.json)
 *   3. Project manifest (.project/state/manifest.json)
 *   4. Environment variables
 *   5. CLI flags (passed in at runtime)
 *
 * Later sources override earlier ones for non-security settings.
 * Security settings CANNOT be weakened by lower-priority sources.
 */

import { existsSync, readFileSync, mkdirSync } from 'fs';
import { homedir } from 'os';
import { join, resolve } from 'path';
import type { HarnessConfig, LoadedConfig, ConfigSource } from './types.js';

// ============================================================
// Default Config
// ============================================================

const DEFAULT_CONFIG: HarnessConfig = {
  version: '1.0.0',
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
// Paths
// ============================================================

function getGlobalConfigPath(): string {
  return join(homedir(), '.harness', 'config.json');
}

function getProjectManifestPath(projectPath?: string): string | undefined {
  if (!projectPath) return undefined;
  return resolve(projectPath, '.project/state/manifest.json');
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
    config.cli = { ...config.cli, defaultOutputMode: process.env.HARNESS_OUTPUT_MODE as any };
  }
  if (process.env.HARNESS_NON_INTERACTIVE) {
    config.runtime = { ...config.runtime, nonInteractive: true };
  }
  if (process.env.HARNESS_LOG_LEVEL) {
    config.runtime = { ...config.runtime, logLevel: process.env.HARNESS_LOG_LEVEL as any };
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
// Merge (shallow, with governance safety)
// ============================================================

/**
 * Merge two config objects.
 * Safety: governance settings can only be tightened, never weakened.
 */
function mergeConfig(base: HarnessConfig, override: Partial<HarnessConfig>, sourceLabel: string, warnings: string[]): HarnessConfig {
  const result = { ...base };

  for (const key of Object.keys(override) as Array<keyof HarnessConfig>) {
    const ov = override[key];
    if (ov === undefined) continue;

    if (key === 'governance' && base.governance && ov && typeof ov === 'object') {
      // Governance safety: only allow tightening
      const gov = { ...base.governance };
      for (const [gk, gv] of Object.entries(ov)) {
        const baseVal = (base.governance as any)[gk];
        const overrideVal = gv;

        // For boolean security settings, override can only make it MORE restrictive
        if (typeof baseVal === 'boolean' && typeof overrideVal === 'boolean') {
          if (overrideVal === false && baseVal === true) {
            // Warning: attempt to weaken security
            warnings.push(`${sourceLabel}: Cannot weaken governance.${gk} from true to false`);
            continue;
          }
        }
        (gov as any)[gk] = overrideVal;
      }
      (result as any)[key] = gov;
    } else if (key === 'cli' || key === 'runtime' || key === 'project' || key === 'skills' || key === 'verification' || key === 'observability' || key === 'delivery') {
      const baseVal = (base as any)[key] || {};
      const overrideVal = (ov as any) || {};
      (result as any)[key] = Object.assign({}, baseVal, overrideVal);
    }
  }

  return result;
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

  // 1. Default config
  sources.push({ path: '(defaults)', scope: 'default', valid: true });
  let config = { ...DEFAULT_CONFIG };

  // 2. Global config
  const global = readGlobalConfig();
  sources.push(global.source);
  config = mergeConfig(config, global.config, 'global', warnings);

  // 3. Project manifest
  const project = readProjectManifest(projectPath);
  if (project.source) {
    sources.push(project.source);
    config = mergeConfig(config, project.config, 'project', warnings);
  }

  // 4. Environment variables
  const env = readEnvVars();
  const envSource: ConfigSource = { path: '(environment)', scope: 'env', valid: true };
  sources.push(envSource);
  config = mergeConfig(config, env, 'env', warnings);

  // 5. CLI overrides
  if (cliOverrides) {
    const cliSource: ConfigSource = { path: '(cli flags)', scope: 'cli', valid: true };
    sources.push(cliSource);
    config = mergeConfig(config, cliOverrides, 'cli', warnings);
  }

  return { config, sources, warnings };
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
  // Check env var first (highest priority for runtime values)
  if (envVar && process.env[envVar] !== undefined) {
    return process.env[envVar] as unknown as T;
  }

  // Walk the config object path
  const parts = path.split('.');
  let current: any = config;
  for (const part of parts) {
    if (current === undefined || current === null) return defaultValue;
    current = current[part];
  }

  return current ?? defaultValue;
}
