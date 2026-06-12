/**
 * Harness OS — Governance Module
 *
 * Central module for policy evaluation, risk classification, and approval gating.
 *
 * Source: CLAUDE.md §4 (permission three-state), §7 (approval gate),
 *   §10 (tool call trace), §11 (Thin Harness steps 4-6).
 *
 * Sub-modules:
 * - policy.ts       — Policy engine: checkPolicy, classifyRisk, PolicyRule
 * - approval-gate.ts — Approval gate: submit, resolve, query pending approvals
 *
 * Thin Harness scope (§11):
 *   4. PreToolUse gate  → 5. allow/deny/needs_approval  → 6. approval resolve
 */

// Re-export policy
export {
  checkPolicy,
  classifyRisk,
  createRule,
  type PolicyContext,
  type PolicyRule,
} from './policy.js';

// Re-export approval gate
export {
  submitApproval,
  resolveApproval,
  getApproval,
  listPendingApprovals,
  listAllApprovals,
  approvalToDecision,
  __test_clearStore,
  computeInputDigest,
  consumeApproval,
  validateApprovalBinding,
  type ApprovalStatus,
  type PendingApproval,
  type ApprovalResolution,
} from './approval-gate.js';

// Re-export redactor
export {
  redactText,
  redactObject,
  redactFileContent,
  redactError,
  isProtectedFile,
  hasProtectedFragment,
  countRedactions,
  type RedactionReport,
} from './redactor.js';
