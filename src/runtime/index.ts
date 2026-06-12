/**
 * Harness OS — Runtime Module
 *
 * Turn orchestrator, session lifecycle, and tool call gate pipeline.
 *
 * Source: CLAUDE.md §8 (Session/State), §10 (Tool call trace),
 *   §11 (Thin Harness steps 1-9).
 *
 * Sub-modules:
 * - session.ts      — Session lifecycle: create, get, end
 * - pipeline.ts     — Tool call gate: evaluate, approve, trace
 * - orchestrator.ts — Turn orchestrator: start, process, complete
 */

// Orchestrator
export {
  startTurn,
  processToolCall,
  completeTurn,
  orchestrateCreateSession,
  orchestrateEndSession,
  getTurnState,
  __test_resetRuntime,
  type TurnContext,
} from './orchestrator.js';

// Session
export {
  createSession,
  getSession,
  endSession,
  listActiveSessions,
  __test_clearSessions,
  type CreateSessionParams,
} from './session.js';

// Pipeline
export {
  evaluateToolCall,
  resolveToolCallApproval,
  checkApprovalStatus,
  buildPolicyContext,
  type ToolCallVerdict,
} from './pipeline.js';

// CLI helpers (legacy — kept for backward compat)
export async function showStatus(): Promise<void> {
  const { listActiveSessions } = await import('./session.js');
  const sessions = listActiveSessions();
  console.log(`Active sessions: ${sessions.length}`);
  for (const s of sessions) {
    console.log(`  ${s.session_id} — turns: ${s.turn_count}`);
  }
}

export async function showConfig(options?: { json?: boolean }): Promise<void> {
  const { HARNESS_VERSION } = await import('../version.js');
  if (options?.json) {
    console.log(JSON.stringify({ runtime: 'thin-harness', version: HARNESS_VERSION }, null, 2));
  } else {
    console.log('Harness OS Runtime — Thin Harness');
    console.log('Session store: in-memory');
    console.log('Policy engine: built-in rules');
    console.log('Approval gate: in-memory (TTL: 5 min)');
  }
}
