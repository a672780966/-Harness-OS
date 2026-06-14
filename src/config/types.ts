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
  fieldSources?: ConfigFieldSource[];
  validation?: ConfigValidation;
}

// ============================================================
// Safety Field Registry (CFG-01)
//
// Every safety-locked field has a definition declaring its type,
// tighten direction, and behavior when overridden.
//
// Sources: 15_CONFIG_REFERENCE.md §7, AUD-P0-002 CFG-01..08
// ============================================================

export type SafetyType =
  | 'boolean' // true=tight, false=loose — reject false override
  | 'boolean-allow' // false=tight, true=loose — reject true override
  | 'enum' // validate against known values; reject unknown
  | 'array' // union merge only — cannot remove items
  | 'immutable-boolean'; // cannot be changed from default

export interface SafetyFieldDef {
  /** Dotted config path, e.g. "governance.redactSecrets" */
  path: string;
  /** Safety type determining merge/validation behavior */
  type: SafetyType;
  /** Default value from DEFAULT_CONFIG */
  defaultValue: unknown;
  /** CFG-08: If true, this field cannot be changed by ANY non-default source */
  immutable?: boolean;
  /** For enum type: list of valid values */
  validValues?: string[];
  /** Human-readable description of what tightening means */
  description?: string;
}

/**
 * Safety Field Registry — all config fields with security implications.
 *
 * Rules per type:
 * - `boolean`:         rejecting a false override means the field stays true (tight)
 * - `boolean-allow`:   rejecting a true  override means the field stays false (tight)
 * - `enum`:            rejecting invalid/weakening values; valid tightening allowed
 * - `array`:           union merge — items can only be added, never removed
 * - `immutable-boolean`: cannot be changed by any non-default source
 */
export const SAFETY_FIELDS: SafetyFieldDef[] = [
  // ---- approval booleans (true = more restrictive) ----
  {
    path: 'governance.requireApprovalForDeploy',
    type: 'boolean',
    defaultValue: true,
    immutable: true,
    description: 'Require approval for deploy',
  },
  {
    path: 'governance.requireApprovalForPushMain',
    type: 'boolean',
    defaultValue: true,
    description: 'Require approval for push to main',
  },
  {
    path: 'governance.requireApprovalForDependencyAdd',
    type: 'boolean',
    defaultValue: true,
    description: 'Require approval for adding dependencies',
  },
  {
    path: 'governance.requireApprovalForDeleteFile',
    type: 'boolean',
    defaultValue: true,
    description: 'Require approval for deleting files',
  },
  {
    path: 'governance.requireApprovalForModifyAgentsMd',
    type: 'boolean',
    defaultValue: true,
    description: 'Require approval for modifying AGENTS.md',
  },
  {
    path: 'governance.redactSecrets',
    type: 'boolean',
    defaultValue: true,
    immutable: true,
    description: 'Redact secrets in outputs',
  },
  {
    path: 'delivery.requireApprovalForPr',
    type: 'boolean',
    defaultValue: true,
    description: 'Require approval for PRs',
  },
  {
    path: 'delivery.requireApprovalForRelease',
    type: 'boolean',
    defaultValue: true,
    description: 'Require approval for release',
  },
  {
    path: 'delivery.requireApprovalForDeploy',
    type: 'boolean',
    defaultValue: true,
    immutable: true,
    description: 'Require approval for deploy',
  },
  {
    path: 'observability.secretRedaction',
    type: 'boolean',
    defaultValue: true,
    immutable: true,
    description: 'Redact secrets in observability output',
  },

  // ---- allow booleans (false = more restrictive) ----
  {
    path: 'governance.allowWorkspaceOutsideAccess',
    type: 'boolean-allow',
    defaultValue: false,
    description: 'Allow workspace outside access',
  },
  {
    path: 'project.allowAutoCommit',
    type: 'boolean-allow',
    defaultValue: false,
    description: 'Allow automatic commits',
  },
  {
    path: 'project.allowAutoPush',
    type: 'boolean-allow',
    defaultValue: false,
    immutable: true,
    description: 'Allow automatic pushes (immutable: cannot be enabled)',
  },

  // ---- enum fields ----
  {
    path: 'governance.defaultNetwork',
    type: 'enum',
    defaultValue: 'restricted',
    validValues: ['restricted', 'allowed'],
    description: 'Default network access (restricted=strict)',
  },

  // ---- array fields (union merge only) ----
  {
    path: 'governance.dangerousCommands',
    type: 'array',
    defaultValue: [
      'rm -rf',
      'sudo',
      'chmod -R',
      'chown -R',
      'git reset --hard',
      'git clean -fd',
      'git push --force',
      'curl | sh',
      'wget | sh',
    ],
    description: 'Dangerous command patterns (append only)',
  },
  {
    path: 'project.protectedBranches',
    type: 'array',
    defaultValue: ['main', 'master'],
    description: 'Protected branches (append only)',
  },
];

// ============================================================
// Config Field Source Tracking (CFG-07)
// ============================================================

export interface ConfigFieldSource {
  /** Dotted config path */
  path: string;
  /** The effective value */
  value: unknown;
  /** Which source provided this value */
  source: ConfigSource['scope'];
  /** Whether this override was rejected by safety rules */
  rejected?: boolean;
  /** If rejected, why */
  rejectedReason?: string;
}

export interface ConfigValidation {
  valid: boolean;
  errors: string[];
}
