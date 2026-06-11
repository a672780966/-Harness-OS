/**
 * Harness OS Core Types
 *
 * Shared type definitions used across all modules.
 * Schema definitions follow the Harness OS Data Model (04_HARNESS_OS_DESIGN.md §9).
 */

// ============================================================
// Error Types
// ============================================================

export type ErrorSeverity = 'info' | 'warning' | 'error' | 'fatal';

export interface HarnessError {
  code: string;
  category: string;
  severity: ErrorSeverity;
  message: string;
  recoveryHint: string;
  recoverable: boolean;
  retryable: boolean;
  userActionRequired: boolean;
  details?: Record<string, unknown>;
  createdAt: string;
}

export function createError(
  code: string,
  category: string,
  severity: ErrorSeverity,
  message: string,
  recoveryHint: string,
  recoverable = true,
  retryable = false
): HarnessError {
  return {
    code,
    category,
    severity,
    message,
    recoveryHint,
    recoverable,
    retryable,
    userActionRequired: true,
    createdAt: new Date().toISOString()
  };
}

// ============================================================
// CLI Output Types
// ============================================================

export type OutputMode = 'pretty' | 'json' | 'quiet';

export interface CliOutputMeta {
  version: string;
  outputMode: OutputMode;
  generatedAt: string;
  durationMs?: number;
  projectId?: string;
  taskId?: string;
  runId?: string;
  redacted: boolean;
}

export interface CliJsonOutput<T = unknown> {
  ok: boolean;
  command: string;
  status: 'success' | 'failed' | 'blocked' | 'requires-approval' | 'partial' | 'skipped';
  data?: T;
  error?: HarnessError;
  warnings: Array<{ code: string; message: string; recoveryHint?: string }>;
  meta: CliOutputMeta;
}

// ============================================================
// Project Types
// ============================================================

export interface ProjectManifest {
  version: string;
  projectId: string;
  projectName: string;
  projectType: 'web-app' | 'backend-service' | 'cli' | 'library' | 'agent-harness' | 'unknown';
  rootPath: string;
  defaultBranch: string;
  language: { primary: string; secondary: string[] };
  runtime: { name: string; version?: string };
  packageManager?: { name: string; lockfile?: string };
  commands: {
    install?: string;
    dev?: string;
    build?: string;
    lint?: string;
    typecheck?: string;
    test?: string;
    e2e?: string;
  };
  skills: { enabled: string[]; disabled: string[] };
  createdAt: string;
  updatedAt: string;
}

// ============================================================
// Task Types
// ============================================================

export type TaskStatus = 'created' | 'ready' | 'running' | 'blocked' | 'paused' | 'verifying' | 'completed' | 'failed';
export type TaskType = 'feature' | 'bugfix' | 'refactor' | 'test' | 'docs' | 'investigation' | 'delivery' | 'maintenance' | 'architecture' | 'unknown';

export interface TaskState {
  taskId: string;
  projectId: string;
  title: string;
  type: TaskType;
  status: TaskStatus;
  userInstruction: string;
  normalizedGoal: string;
  runIds: string[];
  contextPackIds: string[];
  checkpointIds: string[];
  changedFiles: string[];
  verification: { status: string; reportPath?: string };
  risks: string[];
  createdAt: string;
  updatedAt: string;
}

// ============================================================
// Context Pack Types
// ============================================================

export interface ContextPack {
  id: string;
  projectId: string;
  taskId: string;
  runId: string;
  createdAt: string;
  task: { title: string; userInstruction: string; taskType: TaskType };
  project: { name: string; type: string; primaryLanguage: string; runtime: string };
  rules: {
    architectureRules: string[];
    codingRules: string[];
    testingRules: string[];
    securityRules: string[];
  };
  git: {
    branch: string;
    statusShort: string;
    changedFiles: string[];
    untrackedFiles: string[];
    hasUserChanges: boolean;
  };
  files: Array<{ path: string; reason: string; contentMode: 'full' | 'excerpt' | 'summary' }>;
  decisions: Array<{ id: string; title: string; status: string; summary: string }>;
  skills: Array<{ name: string; description: string; allowed: boolean; riskLevel: string }>;
  budget: { maxTokens: number; estimatedTokens: number; trimmingApplied: boolean };
}

// ============================================================
// Skill Types
// ============================================================

export type RiskLevel = 'low' | 'medium' | 'high';

export interface SkillManifest {
  name: string;
  version: string;
  description: string;
  category: string;
  tools: SkillToolManifest[];
  riskLevel: RiskLevel;
}

export interface SkillToolManifest {
  name: string;
  description: string;
  inputSchema: unknown;
  outputSchema: unknown;
  riskLevel: RiskLevel;
  requiresApproval: boolean;
  timeoutMs: number;
}

// ============================================================
// Governance Types
// ============================================================

export type PolicyDecision = 'allow' | 'deny' | 'requires-approval';

export interface PolicyCheckResult {
  decision: PolicyDecision;
  reason: string;
  riskLevel: RiskLevel;
  policySource: string;
  affectedPaths: string[];
}

export interface ApprovalRequest {
  id: string;
  projectId: string;
  taskId: string;
  runId: string;
  action: string;
  reason: string;
  riskLevel: RiskLevel;
  affectedPaths: string[];
  status: 'pending' | 'approved' | 'denied';
}

// ============================================================
// Verification Types
// ============================================================

export type VerificationStatus = 'pending' | 'passed' | 'failed' | 'partial' | 'skipped' | 'blocked';

export interface VerificationResult {
  id: string;
  projectId: string;
  taskId: string;
  runId: string;
  status: VerificationStatus;
  commands: Array<{ name: string; command: string; status: string; exitCode: number | null; durationMs: number }>;
  risks: string[];
  reportPath: string;
}

// ============================================================
// Event Types
// ============================================================

export interface HarnessEvent {
  eventId: string;
  projectId: string;
  taskId?: string;
  runId?: string;
  type: string;
  timestamp: string;
  actor: 'user' | 'codex' | 'harness' | 'skill';
  summary: string;
}

// ============================================================
// Checkpoint Types
// ============================================================

export interface Checkpoint {
  id: string;
  projectId: string;
  taskId?: string;
  runId?: string;
  gitStatus: string;
  currentBranch: string;
  changedFiles: string[];
  contextSummary: string;
  lastSuccessfulStep?: string;
  createdAt: string;
}

// ============================================================
// CLI Exit Codes
// ============================================================

export enum HarnessExitCode {
  SUCCESS = 0,
  USER_INPUT_ERROR = 10,
  PROJECT_ERROR = 20,
  TASK_ERROR = 30,
  CONTEXT_ERROR = 40,
  SKILL_ERROR = 50,
  GOVERNANCE_ERROR = 60,
  VERIFICATION_ERROR = 70,
  DELIVERY_ERROR = 80,
  STATE_ERROR = 90,
  CONFIG_ERROR = 100,
  INTERNAL_ERROR = 120
}
