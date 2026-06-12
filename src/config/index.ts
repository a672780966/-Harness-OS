/**
 * Harness OS — Config Module
 *
 * Unified configuration system with layered loading and governance safety.
 *
 * Sources: Defaults → Global (~/.harness/config.json) → Project Manifest → Env Vars → CLI
 * Safety: Governance settings can only be tightened, never weakened.
 *
 * Reference: 15_CONFIG_REFERENCE.md
 */

export { loadConfig, ensureGlobalConfigDir, getConfigValue } from './loader.js';
export type {
  HarnessConfig,
  ProjectConfig,
  RuntimeConfig,
  SkillsConfig,
  GovernanceConfig,
  VerificationConfig,
  ObservabilityConfig,
  DeliveryConfig,
  CliConfig,
  LoadedConfig,
  ConfigSource,
  ConfigFieldSource,
  ConfigValidation,
  SafetyFieldDef,
  SafetyType,
} from './types.js';
export { SAFETY_FIELDS } from './types.js';
