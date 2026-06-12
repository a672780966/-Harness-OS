/**
 * Harness OS — Config Types
 *
 * Unified configuration schema for all Harness OS modules.
 *
 * Sources: Global (~/.harness/config.json), Project (.project/state/), Environment, Defaults
 * Priority: User Instruction > AGENTS.md > Project Policy > Global Policy > Global Config > Default
 *
 * Reference: 15_CONFIG_REFERENCE.md §7
 */

// ============================================================
// Root Config
// ============================================================

export interface HarnessConfig {
  version: string;
  project?: ProjectConfig;
  runtime?: RuntimeConfig;
  skills?: SkillsConfig;
  governance?: GovernanceConfig;
  verification?: VerificationConfig;
  observability?: ObservabilityConfig;
  delivery?: DeliveryConfig;
  cli?: CliConfig;
}

// ============================================================
// Project Config
// ============================================================

export interface ProjectConfig {
  defaultBranch?: string;
  protectedBranches?: string[];
  allowAutoCommit?: boolean;
  allowAutoPush?: boolean;
}

// ============================================================
// Runtime Config
// ============================================================

export interface RuntimeConfig {
  outputMode?: 'pretty' | 'json' | 'quiet';
  nonInteractive?: boolean;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
  maxTokens?: number;
}

// ============================================================
// Skills Config
// ============================================================

export interface SkillsConfig {
  enabled?: string[];
  disabled?: string[];
  timeoutMs?: number;
}

// ============================================================
// Governance Config
// ============================================================

export interface GovernanceConfig {
  requireApprovalForDeploy?: boolean;
  requireApprovalForPushMain?: boolean;
  requireApprovalForDependencyAdd?: boolean;
  requireApprovalForDeleteFile?: boolean;
  requireApprovalForModifyAgentsMd?: boolean;
  redactSecrets?: boolean;
  defaultNetwork?: 'restricted' | 'allowed';
  allowWorkspaceOutsideAccess?: boolean;
  dangerousCommands?: string[];
}

// ============================================================
// Verification Config
// ============================================================

export interface VerificationConfig {
  failFast?: boolean;
  timeoutMs?: number;
  requiredTypes?: string[];
}

// ============================================================
// Observability Config
// ============================================================

export interface ObservabilityConfig {
  enabled?: boolean;
  logRetentionDays?: number;
  secretRedaction?: boolean;
}

// ============================================================
// Delivery Config
// ============================================================

export interface DeliveryConfig {
  requireApprovalForCommit?: boolean;
  requireApprovalForPr?: boolean;
  requireApprovalForRelease?: boolean;
  requireApprovalForDeploy?: boolean;
  commitMessageFormat?: 'conventional' | 'plain';
}

// ============================================================
// CLI Config
// ============================================================

export interface CliConfig {
  defaultOutputMode?: 'pretty' | 'json' | 'quiet';
  colorEnabled?: boolean;
  showProgress?: boolean;
}

// ============================================================
// Config Source Metadata
// ============================================================

export interface ConfigSource {
  path: string;
  scope: 'default' | 'global' | 'project' | 'env' | 'cli';
  valid: boolean;
  loadError?: string;
}

export interface LoadedConfig {
  config: HarnessConfig;
  sources: ConfigSource[];
  warnings: string[];
}
