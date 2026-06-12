/**
 * Harness OS — Approval Gate
 *
 * Thin Harness approval gate: handles pending approval submission and resolution.
 * Does NOT execute tool calls, bypass policy, or serve as general-purpose storage.
 *
 * Source: CLAUDE.md §7 (Approval Gate constraints).
 *
 * GOV3-03: Approval strong binding.
 * - approval binds to skill, tool, input digest, project, task, run, session
 * - approved can only be consumed once
 * - rejected/expired/consumed approvals cannot be replayed
 * - modifiedInput must be re-validated before execution
 */

import {
  type PermissionDecision,
  type RiskLevel,
} from '../types.js';
import { createHash } from 'crypto';

// ============================================================
// Types
// ============================================================

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired';

export interface PendingApproval {
  /** Unique approval identifier. */
  id: string;
  /** The tool call or action that triggered approval. */
  action: string;
  /** Human-readable reason why approval was requested. */
  reason: string;
  /** Risk level from policy evaluation. */
  riskLevel: RiskLevel;
  /** Affected file paths, if any. */
  affectedPaths: string[];

  // ---- Strong binding fields (GOV3-03) ----
  /** Skill name that originated this request. */
  skillName?: string;
  /** Tool name that originated this request. */
  toolName?: string;
  /** Project ID binding. */
  projectId?: string;
  /** Task ID binding. */
  taskId?: string;
  /** Run ID binding. */
  runId?: string;
  /** The session that originated this request. */
  sessionId?: string;
  /** The turn that originated this request. */
  turnId?: string;
  /** The agent that originated this request. */
  agentId?: string;
  /** SHA-256 digest of the normalized input (for binding verification). */
  inputDigest?: string;

  /** Current status. */
  status: ApprovalStatus;
  /** Whether this approval has been consumed (single-use, GOV3-03). */
  consumed?: boolean;
  /** ISO-8601 submission timestamp. */
  createdAt: string;
  /** ISO-8601 expiration timestamp (createdAt + TTL). */
  expiresAt: string;
  /** ISO-8601 resolution timestamp (set on approve/reject). */
  resolvedAt?: string;
  /** The actor who resolved this approval (operator). */
  resolvedBy?: string;
  /** Optional modified input provided by the operator on approval. */
  modifiedInput?: Record<string, unknown>;
}

export interface ApprovalResolution {
  approval: PendingApproval;
  accepted: boolean;
  /** If rejected, the reason for rejection. */
  rejectionReason?: string;
  /** Modified input (operator can alter tool input before allowing). */
  modifiedInput?: Record<string, unknown>;
}

// ============================================================
// Default Configuration
// ============================================================

const DEFAULT_TTL_MS = 5 * 60 * 1000; // 5 minutes

// ============================================================
// Approval Gate Store (in-memory, Thin Harness)
// ============================================================

/**
 * A simple in-memory store for pending approvals.
 *
 * Thin Harness: in-memory only.
 * Thick Harness extension: replace with persistent store (better-sqlite3,
 *   JSONL file, or external approval service).
 */
class ApprovalStore {
  private approvals: Map<string, PendingApproval> = new Map();

  add(approval: PendingApproval): void {
    this.approvals.set(approval.id, approval);
  }

  get(id: string): PendingApproval | undefined {
    return this.approvals.get(id);
  }

  update(id: string, updates: Partial<PendingApproval>): PendingApproval | undefined {
    const existing = this.approvals.get(id);
    if (!existing) return undefined;
    const updated = { ...existing, ...updates };
    this.approvals.set(id, updated);
    return updated;
  }

  listPending(): PendingApproval[] {
    const now = new Date().toISOString();
    return Array.from(this.approvals.values())
      .filter(a => a.status === 'pending' && a.expiresAt > now)
      .sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  }

  listAll(): PendingApproval[] {
    return Array.from(this.approvals.values())
      .sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  }

  clear(): void {
    this.approvals.clear();
  }

  get size(): number {
    return this.approvals.size;
  }
}

// Singleton store for Thin Harness.
// Replace with dependency injection for testability.
const store = new ApprovalStore();

// ============================================================
// Public API
// ============================================================

/**
 * Compute a SHA-256 digest of normalized tool input for binding (GOV3-03).
 */
export function computeInputDigest(input: Record<string, unknown>): string {
  const normalized = JSON.stringify(input, Object.keys(input).sort());
  return createHash('sha256').update(normalized).digest('hex');
}

/**
 * Submit a new approval request.
 *
 * @param params - The approval request parameters
 * @returns The created PendingApproval
 */
export function submitApproval(params: {
  id: string;
  action: string;
  reason: string;
  riskLevel: RiskLevel;
  affectedPaths?: string[];
  // Strong binding fields (GOV3-03)
  skillName?: string;
  toolName?: string;
  projectId?: string;
  taskId?: string;
  runId?: string;
  sessionId?: string;
  turnId?: string;
  agentId?: string;
  input?: Record<string, unknown>;
  ttlMs?: number;
}): PendingApproval {
  const now = new Date();
  const ttl = params.ttlMs ?? DEFAULT_TTL_MS;

  const approval: PendingApproval = {
    id: params.id,
    action: params.action,
    reason: params.reason,
    riskLevel: params.riskLevel,
    affectedPaths: params.affectedPaths ?? [],
    // Strong binding (GOV3-03)
    skillName: params.skillName,
    toolName: params.toolName,
    projectId: params.projectId,
    taskId: params.taskId,
    runId: params.runId,
    sessionId: params.sessionId,
    turnId: params.turnId,
    agentId: params.agentId,
    inputDigest: params.input ? computeInputDigest(params.input) : undefined,
    status: 'pending',
    consumed: false,
    createdAt: now.toISOString(),
    expiresAt: new Date(now.getTime() + ttl).toISOString(),
  };

  store.add(approval);
  return approval;
}

/**
 * Resolve a pending approval.
 *
 * @param id - The approval ID
 * @param resolution - Whether approved or rejected, with optional reason/modified input
 * @returns The resolved PendingApproval, or undefined if not found
 */
export function resolveApproval(
  id: string,
  resolution: {
    approved: boolean;
    resolvedBy?: string;
    rejectionReason?: string;
    modifiedInput?: Record<string, unknown>;
  },
): PendingApproval | undefined {
  const approval = store.get(id);
  if (!approval) return undefined;

  // Expired check
  const now = new Date();
  if (approval.expiresAt < now.toISOString()) {
    return store.update(id, {
      status: 'expired',
      resolvedAt: now.toISOString(),
      resolvedBy: resolution.resolvedBy,
    });
  }

  if (approval.status !== 'pending') {
    // Already resolved — return as-is
    return approval;
  }

  return store.update(id, {
    status: resolution.approved ? 'approved' : 'rejected',
    resolvedAt: now.toISOString(),
    resolvedBy: resolution.resolvedBy,
    modifiedInput: resolution.approved ? resolution.modifiedInput : undefined,
  });
}

/**
 * Consume an approved approval (single-use, GOV3-03).
 * Marks it as consumed so it cannot be reused.
 * Returns the approval with modifiedInput if provided, or undefined if
 * the approval cannot be consumed (not found, not approved, already consumed, expired).
 */
export function consumeApproval(id: string): PendingApproval | undefined {
  const approval = store.get(id);
  if (!approval) return undefined;

  // Reject if not approved
  if (approval.status !== 'approved') return undefined;

  // Reject if already consumed (single-use enforcement)
  if (approval.consumed) return undefined;

  // Reject if expired
  const now = new Date();
  if (approval.expiresAt < now.toISOString()) {
    store.update(id, { status: 'expired', resolvedAt: now.toISOString() });
    return undefined;
  }

  // Mark consumed and return
  return store.update(id, { consumed: true, resolvedAt: now.toISOString() });
}

/**
 * Validate that an approval matches the expected binding context (GOV3-03).
 * Returns null if valid, or an error message string if binding mismatch.
 */
export function validateApprovalBinding(
  approval: PendingApproval,
  expected: {
    skillName?: string;
    toolName?: string;
    projectId?: string;
    taskId?: string;
    sessionId?: string;
    input?: Record<string, unknown>;
  },
): string | null {
  // Cross-tool binding check
  if (approval.skillName && expected.skillName && approval.skillName !== expected.skillName) {
    return `Approval bound to skill "${approval.skillName}", cannot use for "${expected.skillName}"`;
  }
  if (approval.toolName && expected.toolName && approval.toolName !== expected.toolName) {
    return `Approval bound to tool "${approval.toolName}", cannot use for "${expected.toolName}"`;
  }
  // Cross-project binding check
  if (approval.projectId && expected.projectId && approval.projectId !== expected.projectId) {
    return `Approval bound to project "${approval.projectId}", cannot use for "${expected.projectId}"`;
  }
  // Cross-session binding check
  if (approval.sessionId && expected.sessionId && approval.sessionId !== expected.sessionId) {
    return `Approval bound to session "${approval.sessionId}", cannot use for "${expected.sessionId}"`;
  }
  // Input digest check (if both have input)
  if (expected.input && approval.inputDigest) {
    const digest = computeInputDigest(expected.input);
    if (approval.inputDigest !== digest) {
      return `Approval input digest mismatch — input has changed since approval was granted`;
    }
  }
  return null;
}

/**
 * Get a specific approval by ID.
 */
export function getApproval(id: string): PendingApproval | undefined {
  return store.get(id);
}

/**
 * List all pending (unexpired) approvals.
 */
export function listPendingApprovals(): PendingApproval[] {
  return store.listPending();
}

/**
 * List all approvals (including resolved and expired).
 */
export function listAllApprovals(): PendingApproval[] {
  return store.listAll();
}

/**
 * Convert a resolved approval back to a PermissionDecision.
 * Useful for propagating the result back to the tool call gate.
 */
export function approvalToDecision(approval: PendingApproval): {
  decision: PermissionDecision;
  reason: string;
} {
  switch (approval.status) {
    case 'approved':
      return { decision: 'allow', reason: `Approved by ${approval.resolvedBy ?? 'operator'}` };
    case 'rejected':
      return { decision: 'deny', reason: `Rejected by ${approval.resolvedBy ?? 'operator'}` };
    case 'expired':
      return { decision: 'deny', reason: `Approval request expired at ${approval.expiresAt}` };
    case 'pending':
      return { decision: 'needs_approval', reason: `Still pending: ${approval.reason}` };
  }
}

/**
 * Clear the store (for testing only).
 */
export function __test_clearStore(): void {
  store.clear();
}
