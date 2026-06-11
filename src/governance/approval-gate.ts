/**
 * Harness OS — Approval Gate
 *
 * Thin Harness approval gate: handles pending approval submission and resolution.
 * Does NOT execute tool calls, bypass policy, or serve as general-purpose storage.
 *
 * Source: CLAUDE.md §7 (Approval Gate constraints).
 *
 * Design:
 * - In-memory pending queue (Thin Harness). Replace with DB-backed store for Thick.
 * - submitApproval() creates a pending entry.
 * - resolveApproval() accepts or rejects by an operator.
 * - Default TTL: 5 minutes — expired entries are auto-rejected on resolve attempt.
 */

import {
  type PermissionDecision,
  type RiskLevel,
} from '../types.js';

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
  /** The session that originated this request. */
  sessionId?: string;
  /** The turn that originated this request. */
  turnId?: string;
  /** The agent that originated this request. */
  agentId?: string;
  /** Current status. */
  status: ApprovalStatus;
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
  sessionId?: string;
  turnId?: string;
  agentId?: string;
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
    sessionId: params.sessionId,
    turnId: params.turnId,
    agentId: params.agentId,
    status: 'pending',
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
