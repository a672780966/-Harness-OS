/**
 * Harness OS — Tool Call Pipeline
 *
 * The PreToolUse → PostToolUse gate pipeline.
 * Orchestrates: policy evaluation → approval resolution → trace recording.
 *
 * Source: CLAUDE.md §5 (Hook), §6 (Merge), §10 (Trace), §11 (Thin Harness steps 4-8).
 *
 * Pipeline:
 *   1. Build PolicyContext from tool input
 *   2. checkPolicy() → allow / deny / needs_approval
 *   3. If needs_approval → submitApproval() → wait for resolve
 *   4. Record ToolCallTrace
 *   5. Return verdict to caller
 *
 * Thin Harness: synchronous in-memory pipeline.
 * Thick Harness extension: parallel hook fanout, publish-and-collect, OpenTelemetry.
 */

import {
  type AgentId,
  type PermissionDecision,
  type PolicyCheckResult,
  type SessionId,
  type ToolCallTrace,
  type TraceId,
  type TurnId,
} from '../types.js';
import {
  type PolicyContext,
  checkPolicy,
} from '../governance/policy.js';
import {
  type PendingApproval,
  submitApproval,
  resolveApproval,
  approvalToDecision,
  getApproval,
} from '../governance/approval-gate.js';

// ============================================================
// Verdict Types
// ============================================================

/**
 * Outcome of a tool call evaluation.
 * The caller uses this to decide whether to execute the tool.
 */
export type ToolCallVerdict =
  | { outcome: 'allow'; trace: ToolCallTrace }
  | { outcome: 'deny'; trace: ToolCallTrace }
  | { outcome: 'needs_approval'; approval: PendingApproval; trace: ToolCallTrace };

// ============================================================
// Trace ID Generation
// ============================================================

let counter = 0;

function generateTraceId(): string {
  counter += 1;
  return `trc_${Date.now().toString(36)}_${counter.toString(36).padStart(4, '0')}`;
}

// ============================================================
// Trace Builder
// ============================================================

function buildTrace(params: {
  sessionId: SessionId;
  turnId: TurnId;
  agentId: AgentId;
  toolUseId: string;
  parentToolUseId?: string;
  toolName: string;
  toolInput: unknown;
  permissionDecision: PermissionDecision;
  reason: string;
}): ToolCallTrace {
  return {
    session_id: params.sessionId,
    turn_id: params.turnId,
    agent_id: params.agentId,
    tool_use_id: params.toolUseId,
    parent_tool_use_id: params.parentToolUseId,
    tool_name: params.toolName,
    tool_input: params.toolInput,
    permission_decision: params.permissionDecision,
    reason: params.reason,
    timestamp: new Date().toISOString(),
    trace_id: `trc_${Date.now().toString(36)}_${counter.toString(36).padStart(4, '0')}` as TraceId,
  };
}

// ============================================================
// PolicyContext Builder
// ============================================================

/**
 * Build a PolicyContext from raw tool input.
 * Extracts command (for Bash) and file paths (for Write/Edit).
 */
export function buildPolicyContext(toolName: string, toolInput: Record<string, unknown>): PolicyContext {
  const context: PolicyContext = {
    toolName,
  };

  if (toolName === 'Bash' && typeof toolInput.command === 'string') {
    context.command = toolInput.command;
  }

  const pathFields = ['file_path', 'filePath', 'path'];
  const paths: string[] = [];
  for (const field of pathFields) {
    const val = toolInput[field];
    if (typeof val === 'string') {
      paths.push(val);
    }
  }
  if (paths.length > 0) {
    context.affectedPaths = paths;
  }

  return context;
}

// ============================================================
// Pipeline — Evaluate
// ============================================================

/**
 * Evaluate a tool call through the pipeline.
 *
 * Step 1: Build policy context
 * Step 2: Check policy
 * Step 3: If needs_approval → create approval request
 * Step 4: Build and return verdict with trace
 *
 * @returns A ToolCallVerdict — caller decides how to proceed.
 */
export async function evaluateToolCall(params: {
  sessionId: SessionId;
  turnId: TurnId;
  agentId: AgentId;
  toolUseId: string;
  parentToolUseId?: string;
  toolName: string;
  toolInput: Record<string, unknown>;
}): Promise<ToolCallVerdict> {
  const { sessionId, turnId, agentId, toolUseId, parentToolUseId, toolName, toolInput } = params;

  // 1. Build policy context from raw tool input
  const policyContext = buildPolicyContext(toolName, toolInput);

  // 2. Check policy
  const policyResult: PolicyCheckResult = await checkPolicy(toolName, policyContext);

  // 3. Build trace
  const trace = buildTrace({
    sessionId,
    turnId,
    agentId,
    toolUseId,
    parentToolUseId,
    toolName,
    toolInput,
    permissionDecision: policyResult.decision,
    reason: policyResult.reason,
  });

  // 4. Handle decision
  switch (policyResult.decision) {
    case 'allow':
      return { outcome: 'allow', trace };

    case 'deny':
      return { outcome: 'deny', trace };

    case 'needs_approval': {
      const approval = submitApproval({
        id: `app_${toolUseId}`,
        action: `${toolName}${policyContext.command ? `: ${policyContext.command.slice(0, 80)}` : ''}`,
        reason: policyResult.reason,
        riskLevel: policyResult.riskLevel,
        affectedPaths: policyContext.affectedPaths ?? [],
        sessionId,
        turnId,
        agentId,
      });
      return { outcome: 'needs_approval', approval, trace };
    }

    default:
      return { outcome: 'deny', trace };
  }
}

// ============================================================
// Pipeline — Resolve Approval
// ============================================================

/**
 * Resolve a pending approval and return the updated trace.
 *
 * Call this when the operator has made a decision.
 *
 * @param approvalId - The approval ID to resolve
 * @param resolution - Operator decision
 * @returns Updated ToolCallTrace with final decision, or undefined if not found
 */
export function resolveToolCallApproval(
  approvalId: string,
  resolution: {
    approved: boolean;
    resolvedBy?: string;
    rejectionReason?: string;
  },
): ToolCallTrace | undefined {
  const resolved = resolveApproval(approvalId, resolution);
  if (!resolved) return undefined;

  const decision = approvalToDecision(resolved);

  // Return a minimal trace update
  return {
    session_id: '' as SessionId,
    turn_id: '' as TurnId,
    agent_id: '' as AgentId,
    tool_use_id: approvalId.replace('app_', ''),
    tool_name: resolved.action,
    tool_input: {},
    permission_decision: decision.decision,
    reason: decision.reason,
    timestamp: new Date().toISOString(),
  };
}

// ============================================================
// Pipeline — Check Approval Status
// ============================================================

/**
 * Check if a pending approval has been resolved.
 * Returns the updated verdict if resolved, or the current pending status.
 */
export function checkApprovalStatus(approvalId: string): ToolCallVerdict | undefined {
  const approval = getApproval(approvalId);
  if (!approval) return undefined;

  if (approval.status === 'pending' || approval.status === 'expired') {
    // Re-check expired status on access
    const now = new Date().toISOString();
    if (approval.status === 'pending' && approval.expiresAt < now) {
      // Expired — resolve as expired
      const expired = resolveApproval(approvalId, { approved: false });
      if (!expired) return undefined;
      const decision = approvalToDecision(expired);
      return {
        outcome: 'deny',
        trace: {
          session_id: '' as SessionId,
          turn_id: '' as TurnId,
          agent_id: '' as AgentId,
          tool_use_id: approvalId,
          tool_name: approval.action,
          tool_input: {},
          permission_decision: decision.decision,
          reason: decision.reason,
          timestamp: new Date().toISOString(),
        },
      };
    }

    return {
      outcome: 'needs_approval',
      approval,
      trace: {
        session_id: '' as SessionId,
        turn_id: '' as TurnId,
        agent_id: '' as AgentId,
        tool_use_id: approvalId,
        tool_name: approval.action,
        tool_input: {},
        permission_decision: 'needs_approval',
        reason: 'Still pending approval',
        timestamp: new Date().toISOString(),
      },
    };
  }

  // Resolved
  const decision = approvalToDecision(approval);
  return {
    outcome: decision.decision === 'allow' ? 'allow' : 'deny',
    trace: {
      session_id: '' as SessionId,
      turn_id: '' as TurnId,
      agent_id: '' as AgentId,
      tool_use_id: approvalId,
      tool_name: approval.action,
      tool_input: {},
      permission_decision: decision.decision,
      reason: decision.reason,
      timestamp: new Date().toISOString(),
    },
  };
}
