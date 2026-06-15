/**
 * Harness OS — Skill Executor
 *
 * Standard execution interface for all Harness OS skills.
 *
 * Every registered skill can provide an executor that takes tool input
 * and returns tool output.
 *
 * Reference: 07_MCP_SKILLS_SPEC.md §7
 */

// ============================================================
// Execution Context
// ============================================================

export interface SkillExecutionContext {
  projectPath: string;
  taskId?: string;
  runId?: string;
  sessionId?: string;
}

// ============================================================
// Execution Result
// ============================================================

export interface SkillExecutionResult {
  skillName: string;
  toolName: string;
  status: 'success' | 'failed' | 'blocked' | 'requires-approval';
  output?: unknown;
  summary: string;
  durationMs: number;
  error?: { code: string; message: string; recoverable: boolean };
}

// ============================================================
// Executor Type
// ============================================================

/**
 * A skill executor function that runs a specific tool.
 */
export type SkillExecutor = (
  toolName: string,
  input: Record<string, unknown>,
  context: SkillExecutionContext,
) => Promise<SkillExecutionResult>;

/**
 * Error to signal that a tool requires approval.
 */
export class ApprovalRequiredError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ApprovalRequiredError';
  }
}

// ============================================================
// Result Builder Helpers
// ============================================================

export function successResult(
  skillName: string,
  toolName: string,
  output: unknown,
  summary: string,
  durationMs: number,
): SkillExecutionResult {
  return { skillName, toolName, status: 'success', output, summary, durationMs };
}

export function failedResult(
  skillName: string,
  toolName: string,
  error: Error,
  durationMs: number,
): SkillExecutionResult {
  return {
    skillName,
    toolName,
    status: 'failed',
    summary: error.message,
    durationMs,
    error: {
      code: error.name === 'ApprovalRequiredError' ? 'APPROVAL_REQUIRED' : 'EXECUTION_ERROR',
      message: error.message,
      recoverable: error.name !== 'ApprovalRequiredError',
    },
  };
}

export function blockedResult(
  skillName: string,
  toolName: string,
  reason: string,
  durationMs: number,
): SkillExecutionResult {
  return {
    skillName,
    toolName,
    status: 'blocked',
    summary: reason,
    durationMs,
    error: { code: 'BLOCKED', message: reason, recoverable: true },
  };
}

/**
 * Result indicating that the tool requires human approval.
 * Used when policy returns needs_approval — the caller must resolve
 * the approval before the tool can be executed.
 */
export function requiresApprovalResult(
  skillName: string,
  toolName: string,
  reason: string,
  approvalId: string,
): SkillExecutionResult {
  return {
    skillName,
    toolName,
    status: 'requires-approval',
    summary: reason,
    durationMs: 0,
    output: { approvalId },
    error: { code: 'APPROVAL_REQUIRED', message: reason, recoverable: true },
  };
}
