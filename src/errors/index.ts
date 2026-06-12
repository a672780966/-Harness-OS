/**
 * Harness OS — Error Codes
 *
 * Structured error codes for all modules.
 * Every error has: code, category, severity, message, recoveryHint, recoverable, retryable.
 *
 * Reference: 14_ERROR_CODES.md
 */

import type { HarnessError, ErrorSeverity } from '../types.js';

// ============================================================
// Error Code Constants
// ============================================================

export const ErrorCodes = {
  // General
  ERR_INTERNAL: 'ERR_INTERNAL',
  ERR_NOT_IMPLEMENTED: 'ERR_NOT_IMPLEMENTED',
  ERR_INVALID_ARGUMENT: 'ERR_INVALID_ARGUMENT',

  // Project (10-19)
  ERR_PROJECT_NOT_FOUND: 'ERR_PROJECT_NOT_FOUND',
  ERR_PROJECT_NOT_GIT_REPO: 'ERR_PROJECT_NOT_GIT_REPO',
  ERR_PROJECT_MISSING_AGENTS_MD: 'ERR_PROJECT_MISSING_AGENTS_MD',
  ERR_PROJECT_INVALID_MANIFEST: 'ERR_PROJECT_INVALID_MANIFEST',
  ERR_PROJECT_MISSING_DIRS: 'ERR_PROJECT_MISSING_DIRS',

  // Task (20-29)
  ERR_TASK_NOT_FOUND: 'ERR_TASK_NOT_FOUND',
  ERR_TASK_INVALID_TRANSITION: 'ERR_TASK_INVALID_TRANSITION',
  ERR_TASK_NOT_RUNNING: 'ERR_TASK_NOT_RUNNING',

  // Governance (30-39)
  ERR_POLICY_DENIED: 'ERR_POLICY_DENIED',
  ERR_APPROVAL_REQUIRED: 'ERR_APPROVAL_REQUIRED',
  ERR_APPROVAL_DENIED: 'ERR_APPROVAL_DENIED',
  ERR_APPROVAL_NOT_FOUND: 'ERR_APPROVAL_NOT_FOUND',
  ERR_PROTECTED_PATH: 'ERR_PROTECTED_PATH',
  ERR_DANGEROUS_COMMAND: 'ERR_DANGEROUS_COMMAND',

  // Context (40-49)
  ERR_CONTEXT_BUILD_FAILED: 'ERR_CONTEXT_BUILD_FAILED',
  ERR_CONTEXT_OVER_BUDGET: 'ERR_CONTEXT_OVER_BUDGET',

  // Skill (50-59)
  ERR_SKILL_NOT_FOUND: 'ERR_SKILL_NOT_FOUND',
  ERR_SKILL_EXECUTION_FAILED: 'ERR_SKILL_EXECUTION_FAILED',
  ERR_SKILL_TIMEOUT: 'ERR_SKILL_TIMEOUT',
  ERR_SKILL_BLOCKED: 'ERR_SKILL_BLOCKED',

  // Verification (60-69)
  ERR_VERIFICATION_FAILED: 'ERR_VERIFICATION_FAILED',
  ERR_VERIFICATION_NOT_RUN: 'ERR_VERIFICATION_NOT_RUN',

  // Delivery (70-79)
  ERR_DELIVERY_BLOCKED: 'ERR_DELIVERY_BLOCKED',
  ERR_DELIVERY_NO_VERIFICATION: 'ERR_DELIVERY_NO_VERIFICATION',
  ERR_DELIVERY_NO_REPORT: 'ERR_DELIVERY_NO_REPORT',
  ERR_DELIVERY_GOVERNANCE: 'ERR_DELIVERY_GOVERNANCE',

  // State (80-89)
  ERR_STATE_NOT_FOUND: 'ERR_STATE_NOT_FOUND',
  ERR_CHECKPOINT_NOT_FOUND: 'ERR_CHECKPOINT_NOT_FOUND',

  // Config (90-99)
  ERR_CONFIG_NOT_FOUND: 'ERR_CONFIG_NOT_FOUND',
  ERR_CONFIG_INVALID: 'ERR_CONFIG_INVALID',

  // CLI (100-109)
  ERR_CLI_INVALID_ARGUMENT: 'ERR_CLI_INVALID_ARGUMENT',
  ERR_CLI_NON_INTERACTIVE: 'ERR_CLI_NON_INTERACTIVE',
  ERR_CLI_APPROVAL_REQUIRED: 'ERR_CLI_APPROVAL_REQUIRED',
} as const;

// ============================================================
// Error Factory
// ============================================================

function createError(
  code: string,
  category: string,
  severity: ErrorSeverity,
  message: string,
  recoveryHint: string,
  recoverable = true,
  retryable = false,
  details?: Record<string, unknown>,
): HarnessError {
  return {
    code,
    category,
    severity,
    message,
    recoveryHint,
    recoverable,
    retryable,
    userActionRequired: severity === 'error' || severity === 'fatal',
    details,
    createdAt: new Date().toISOString(),
  };
}

// ============================================================
// Domain Factories
// ============================================================

export function createInternalError(message: string, details?: Record<string, unknown>): HarnessError {
  return createError(ErrorCodes.ERR_INTERNAL, 'internal', 'fatal', message, 'Report this as a bug', false, false, details);
}

export function createNotImplementedError(feature: string): HarnessError {
  return createError(ErrorCodes.ERR_NOT_IMPLEMENTED, 'internal', 'warning', `${feature} is not yet implemented`, '', false, false);
}

// ---- Project ----

export function createProjectNotFoundError(path: string): HarnessError {
  return createError(ErrorCodes.ERR_PROJECT_NOT_FOUND, 'project', 'error', `Project path does not exist: ${path}`, 'Check the path and try again', true, false, { path });
}

export function createProjectNotGitRepoError(path: string): HarnessError {
  return createError(ErrorCodes.ERR_PROJECT_NOT_GIT_REPO, 'project', 'error', `Not a Git repository: ${path}`, 'Run `git init` or check the path', true, false, { path });
}

export function createProjectMissingAgentsMdError(): HarnessError {
  return createError(ErrorCodes.ERR_PROJECT_MISSING_AGENTS_MD, 'project', 'error', 'AGENTS.md is missing from the project root', 'Run `harness init` or `harness repair` to create it', true, true);
}

export function createProjectInvalidManifestError(reason: string): HarnessError {
  return createError(ErrorCodes.ERR_PROJECT_INVALID_MANIFEST, 'project', 'error', `Invalid project manifest: ${reason}`, 'Run `harness repair` to fix it', true, true);
}

// ---- Task ----

export function createTaskNotFoundError(taskId: string): HarnessError {
  return createError(ErrorCodes.ERR_TASK_NOT_FOUND, 'task', 'error', `Task not found: ${taskId}`, 'Check the task ID and try again', true, false, { taskId });
}

export function createTaskInvalidTransitionError(from: string, to: string): HarnessError {
  return createError(ErrorCodes.ERR_TASK_INVALID_TRANSITION, 'task', 'error', `Invalid task transition: ${from} → ${to}`, 'Check allowed transitions with `harness task status`', true, false, { from, to });
}

// ---- Governance ----

export function createPolicyDeniedError(action: string, reason: string): HarnessError {
  return createError(ErrorCodes.ERR_POLICY_DENIED, 'governance', 'error', `Policy denied: ${action}`, reason, true, false, { action });
}

export function createApprovalRequiredError(action: string, reason: string): HarnessError {
  return createError(ErrorCodes.ERR_APPROVAL_REQUIRED, 'governance', 'error', `Approval required: ${action}`, reason, true, true, { action });
}

export function createApprovalDeniedError(approvalId: string): HarnessError {
  return createError(ErrorCodes.ERR_APPROVAL_DENIED, 'governance', 'error', `Approval denied: ${approvalId}`, 'The operation was rejected by the operator', true, false, { approvalId });
}

// ---- Skill ----

export function createSkillNotFoundError(skillName: string): HarnessError {
  return createError(ErrorCodes.ERR_SKILL_NOT_FOUND, 'skill', 'error', `Skill not found: ${skillName}`, 'Check available skills with `harness skills list`', true, false, { skillName });
}

export function createSkillExecutionError(skillName: string, toolName: string, reason: string): HarnessError {
  return createError(ErrorCodes.ERR_SKILL_EXECUTION_FAILED, 'skill', 'error', `Skill execution failed: ${skillName}.${toolName}: ${reason}`, 'Check the input and try again', true, true, { skillName, toolName });
}

// ---- Verification ----

export function createVerificationFailedError(details?: Record<string, unknown>): HarnessError {
  return createError(ErrorCodes.ERR_VERIFICATION_FAILED, 'verification', 'error', 'Verification failed: one or more checks did not pass', 'Fix the reported issues and run `harness verify` again', true, true, details);
}

export function createVerificationNotRunError(): HarnessError {
  return createError(ErrorCodes.ERR_VERIFICATION_NOT_RUN, 'verification', 'error', 'Verification has not been run', 'Run `harness verify` before delivery', true, false);
}

// ---- Delivery ----

export function createDeliveryBlockedError(reason: string): HarnessError {
  return createError(ErrorCodes.ERR_DELIVERY_BLOCKED, 'delivery', 'error', `Delivery blocked: ${reason}`, 'Resolve the blocking issues and try again', true, false);
}

// ---- State ----

export function createCheckpointNotFoundError(checkpointId: string): HarnessError {
  return createError(ErrorCodes.ERR_CHECKPOINT_NOT_FOUND, 'state', 'error', `Checkpoint not found: ${checkpointId}`, 'Check the checkpoint ID with `harness checkpoint list`', true, false, { checkpointId });
}

// ---- CLI ----

export function createCliInvalidArgumentError(message: string): HarnessError {
  return createError(ErrorCodes.ERR_CLI_INVALID_ARGUMENT, 'cli', 'error', message, 'Check the command usage with --help', true, false);
}

export function createCliNonInteractiveApprovalError(): HarnessError {
  return createError(ErrorCodes.ERR_CLI_NON_INTERACTIVE, 'cli', 'error', 'Action requires approval but running in non-interactive mode', 'Use --approve flag or run in interactive terminal', true, false);
}
