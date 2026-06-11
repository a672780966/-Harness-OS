/**
 * Harness OS Core Types
 *
 * Shared type definitions used across all modules.
 *
 * Source: CLAUDE.md project constraints — permission types (§4), hook types (§5),
 * hook merge rules (§6), tool call trace (§10), session/state constraints (§8).
 */

// ============================================================
// Core ID Types
// ============================================================

/** Globally unique session identifier. */
export type SessionId = string & { readonly __brand: 'SessionId' };

/** Turn identifier, unique within a session. */
export type TurnId = string & { readonly __brand: 'TurnId' };

/** Agent or actor identifier. */
export type AgentId = string & { readonly __brand: 'AgentId' };

/** Trace identifier for observability and audit. */
export type TraceId = string & { readonly __brand: 'TraceId' };

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

export interface TaskContext {
  title: string;
  userInstruction: string;
  normalizedInstruction: string;
  taskType: TaskType;
  explicitFiles: string[];
  explicitCommands: string[];
  acceptanceHints: string[];
}

export interface ProjectContext {
  name: string;
  type: string;
  primaryLanguage: string;
  runtime: string;
  packageManager?: string;
  repositoryRoot: string;
  architectureSummary?: string;
  techStackSummary?: string;
}

export interface RuleContext {
  source: 'AGENTS.md';
  architectureRules: string[];
  codingRules: string[];
  testingRules: string[];
  securityRules: string[];
  deliveryRules: string[];
  forbiddenPatterns: string[];
}

export interface GitContext {
  branch: string;
  statusShort: string;
  diffStat: string;
  diffSummary?: string;
  changedFiles: string[];
  untrackedFiles: string[];
  recentCommits: string[];
  hasUserChanges: boolean;
}

export type FileReason =
  | 'explicit'
  | 'git-diff'
  | 'keyword-match'
  | 'symbol-match'
  | 'test-match'
  | 'decision-reference'
  | 'recent-task-reference';

export type ContentMode = 'full' | 'excerpt' | 'summary' | 'metadata-only';

export interface FileContext {
  path: string;
  reason: FileReason;
  priority: number;
  contentMode: ContentMode;
  content?: string;
  excerpt?: string;
  summary?: string;
  symbols?: string[];
}

export interface DecisionContext {
  id: string;
  path: string;
  title: string;
  status: 'proposed' | 'accepted' | 'rejected' | 'superseded';
  summary: string;
  relevanceReason: string;
}

export interface SkillContext {
  name: string;
  description: string;
  allowed: boolean;
  riskLevel: RiskLevel;
  requiresApproval: boolean;
}

export interface ContextBudget {
  maxTokens: number;
  estimatedTokens: number;
  reservedForResponse: number;
  reservedForToolResults: number;
  trimmingApplied: boolean;
}

export interface ContextPack {
  id: string;
  projectId: string;
  taskId: string;
  runId: string;
  createdAt: string;
  task: TaskContext;
  project: ProjectContext;
  rules: RuleContext;
  git: GitContext;
  files: FileContext[];
  decisions: DecisionContext[];
  skills: SkillContext[];
  budget: ContextBudget;
  notes: string[];
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
// Permission & Governance Types
//
// Canonical three-state permission model (CLAUDE.md §4):
//   allow | deny | needs_approval
// No fuzzy states — every decision must resolve to one of these.
// ============================================================

/**
 * Canonical three-state permission decision.
 *
 * CLAUDE.md §4:
 * - allow:  permitted to proceed
 * - deny:   rejected, must not execute
 * - needs_approval:  requires human or upstream approval before proceeding
 */
export type PermissionDecision = 'allow' | 'deny' | 'needs_approval';

/**
 * Structured hook decision output (CLAUDE.md §5).
 *
 * Every PreToolUse hook must return one of these three shapes.
 * No "maybe", "safe", "unsafe" — only the three canonical states.
 */
export type HookDecision =
  | { decision: 'allow'; reason: string }
  | { decision: 'deny'; reason: string }
  | { decision: 'needs_approval'; reason: string };

/**
 * Hook merge result after combining multiple hook decisions.
 *
 * CLAUDE.md §6 defines the priority ordering:
 *   1. deny  >  2. needs_approval  >  3. allow
 *
 * If no hook matched, the default is needs_approval (fail closed).
 */
export interface HookMergeResult {
  final: HookDecision;
  sources: HookDecision[];
}

/**
 * Merge multiple hook decisions following CLAUDE.md §6 priority rules.
 *
 * - Any deny → final is deny
 * - Any needs_approval (no deny) → final is needs_approval
 * - All allow → final is allow
 */
export function mergeHookDecisions(decisions: HookDecision[]): HookMergeResult {
  let result: HookDecision = { decision: 'needs_approval', reason: 'hook failed or no matching rule' };

  for (const d of decisions) {
    if (d.decision === 'deny') {
      return { final: d, sources: decisions };
    }
    if (d.decision === 'needs_approval') {
      result = d;
    }
    if (d.decision === 'allow' && result.decision === 'needs_approval') {
      // keep needs_approval as current worst-case, update only if first iteration
    }
  }

  // If all are allow, result stays as the last allow
  const allAllow = decisions.every(d => d.decision === 'allow');
  if (allAllow && decisions.length > 0) {
    result = decisions[decisions.length - 1];
  }

  return { final: result, sources: decisions };
}

// Legacy alias — use PermissionDecision in new code.
export type PolicyDecision = PermissionDecision;

export interface PolicyCheckResult {
  decision: PermissionDecision;
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
// Tool Call Trace (CLAUDE.md §10)
//
// Every tool call must produce a trace event answering:
//  1. Who initiated?
//  2. What tool was called?
//  3. What was the input?
//  4. Any side effects?
//  5. Permission result?
//  6. Approval needed?
//  7. Trace id?
//  8. Failure handling?
// ============================================================

export interface ToolCallTrace {
  /** Session that owns this tool call. */
  session_id: SessionId;
  /** Turn within the session. */
  turn_id: TurnId;
  /** Agent or actor that initiated the call. */
  agent_id: AgentId;
  /** Unique identifier for this tool use instance. */
  tool_use_id: string;
  /** Parent tool use id if this is a nested/sub call. */
  parent_tool_use_id?: string;
  /** Tool name as exposed to the model (e.g. "Bash", "Write", "Read"). */
  tool_name: string;
  /** The raw input arguments passed to the tool. */
  tool_input: unknown;
  /** Final permission decision after all hooks and policy checks. */
  permission_decision: PermissionDecision;
  /** Human-readable explanation of the decision. */
  reason: string;
  /** ISO-8601 timestamp of when the call was traced. */
  timestamp: string;
  /** Trace id for cross-referencing with observability. */
  trace_id?: TraceId;
}

// ============================================================
// Session & Turn State (CLAUDE.md §8)
//
// session/state is the persistence boundary for operational facts,
// NOT free-form agent memory.
//
// State writes require:
//  1. clear schema
//  2. clear scope
//  3. clear actor
//  4. clear reason
//  5. clear trace id
// ============================================================

/**
 * Runtime state for an active Harness OS session.
 * Scoped to session lifetime (not global).
 */
export interface SessionState {
  /** Unique session identifier. */
  session_id: SessionId;
  /** Project this session is operating on. */
  project_id: string;
  /** ISO-8601 start timestamp. */
  started_at: string;
  /** ISO-8601 last activity timestamp. */
  last_active_at?: string;
  /** Monotonically increasing turn counter. */
  turn_count: number;
  /** Current session status. */
  status: 'active' | 'paused' | 'completed' | 'failed';
  /** Arbitrary metadata (no credentials, no free-text guesses). */
  metadata: Record<string, unknown>;
}

/**
 * State for a single turn within a session.
 * Turns are the unit of interaction (one user message → one response cycle).
 */
export interface TurnState {
  /** Unique turn identifier. */
  turn_id: TurnId;
  /** Parent session. */
  session_id: SessionId;
  /** Turn sequence number within the session. */
  turn_number: number;
  /** ISO-8601 start timestamp. */
  started_at: string;
  /** ISO-8601 completion timestamp. */
  completed_at?: string;
  /** Tool calls made during this turn. */
  tool_calls: ToolCallTrace[];
  /** Current turn status. */
  status: 'active' | 'completed' | 'failed';
  /** The user's input for this turn. */
  user_input?: string;
  /** The model's response (summary only — not raw output). */
  response_summary?: string;
}

/**
 * Creates a new TurnState with defaults.
 */
export function createTurnState(params: {
  turn_id: TurnId;
  session_id: SessionId;
  turn_number: number;
  user_input?: string;
}): TurnState {
  return {
    turn_id: params.turn_id,
    session_id: params.session_id,
    turn_number: params.turn_number,
    started_at: new Date().toISOString(),
    tool_calls: [],
    status: 'active',
    user_input: params.user_input,
  };
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
