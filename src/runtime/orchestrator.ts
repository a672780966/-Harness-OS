/**
 * Harness OS — Turn Orchestrator
 *
 * Coordinates the full Thin Harness turn lifecycle (§11):
 *   1. Turn input → 2. Model call → 3. Tool proposal →
 *   4. PreToolUse gate → 5. allow/deny/needs_approval →
 *   6. Approval resolve → 7. Tool execution → 8. PostToolUse trace →
 *   9. Final response
 *
 * Source: CLAUDE.md §11 (Thin Harness), §8 (Session/State),
 *   §10 (Tool call trace).
 *
 * Design:
 * - TurnOrchestrator is the top-level coordinator.
 * - It delegates to SessionManager (lifecycle) and ToolCallPipeline (gate).
 * - Model calls and tool execution are handled by the caller (CLI layer).
 * - The orchestrator manages state, gating, and tracing.
 */

import { type AgentId, type SessionId, type TurnId, type TurnState, createTurnState } from '../types.js';
import { type ToolCallVerdict, evaluateToolCall } from './pipeline.js';
import {
  createSession,
  getSession,
  endSession,
  incrementTurnCount,
  __test_clearSessions,
  type CreateSessionParams,
} from './session.js';

// ============================================================
// Turn ID Generation
// ============================================================

let turnCounter = 0;

function generateTurnId(sessionId: SessionId): TurnId {
  turnCounter += 1;
  const ts = Date.now().toString(36);
  const seq = turnCounter.toString(36).padStart(4, '0');
  return `trn_${ts}_${seq}` as TurnId;
}

// ============================================================
// Turn Orchestrator
// ============================================================

/**
 * Context for an active turn.
 * Holds references to session and turn state for the duration of one turn.
 */
export interface TurnContext {
  sessionId: SessionId;
  turnId: TurnId;
  turnNumber: number;
  agentId: AgentId;
  state: TurnState;
}

/**
 * Create a new session and return its ID.
 * Shorthand for session.createSession().
 */
export function orchestrateCreateSession(params: CreateSessionParams): SessionId {
  const session = createSession(params);
  return session.session_id;
}

/**
 * Start a new turn within a session.
 *
 * Steps (§11):
 *   1. Increment turn counter
 *   2. Create TurnState
 *   3. Return TurnContext
 *
 * @param sessionId - Active session
 * @param userInput - The user's input for this turn
 * @param agentId - The agent executing this turn
 * @returns TurnContext for this turn
 */
export function startTurn(
  sessionId: SessionId,
  userInput: string,
  agentId: AgentId = 'harness-cli' as AgentId,
): TurnContext | undefined {
  const session = getSession(sessionId);
  if (!session) return undefined;
  if (session.status !== 'active') return undefined;

  const turnNumber = incrementTurnCount(sessionId);
  if (turnNumber === undefined) return undefined;

  const turnId = generateTurnId(sessionId);

  const state = createTurnState({
    turn_id: turnId,
    session_id: sessionId,
    turn_number: turnNumber,
    user_input: userInput,
  });

  return {
    sessionId,
    turnId,
    turnNumber,
    agentId,
    state,
  };
}

/**
 * Process a tool call through the PreToolUse gate.
 *
 * Steps (§11):
 *   4. PreToolUse gate → 5. allow/deny/needs_approval
 *
 * Delegates to ToolCallPipeline.evaluateToolCall().
 *
 * @param context - Active turn context
 * @param toolName - Name of the tool being called
 * @param toolInput - Raw tool arguments
 * @returns Verdict with trace
 */
export async function processToolCall(
  context: TurnContext,
  toolName: string,
  toolInput: Record<string, unknown>,
): Promise<ToolCallVerdict> {
  const toolUseId = `tui_${Date.now().toString(36)}_${turnCounter.toString(36).padStart(4, '0')}`;

  const verdict = await evaluateToolCall({
    sessionId: context.sessionId,
    turnId: context.turnId,
    agentId: context.agentId,
    toolUseId,
    toolName,
    toolInput,
  });

  // Record trace in turn state
  context.state.tool_calls.push(verdict.trace);

  return verdict;
}

/**
 * Complete a turn.
 *
 * Steps (§11):
 *   8. PostToolUse trace → 9. Final response
 *
 * Records the response summary and marks turn as completed.
 *
 * @param context - Active turn context
 * @param responseSummary - Summary of the model's response
 * @returns Completed TurnState
 */
export function completeTurn(context: TurnContext, responseSummary: string): TurnState {
  const now = new Date().toISOString();
  context.state.completed_at = now;
  context.state.response_summary = responseSummary;
  context.state.status = 'completed';
  return context.state;
}

/**
 * End a session.
 * Shorthand for session.endSession().
 */
export function orchestrateEndSession(sessionId: SessionId): boolean {
  const ended = endSession(sessionId);
  return ended !== undefined;
}

/**
 * Get turn state from a completed context.
 * Useful for persisting after the turn ends.
 */
export function getTurnState(context: TurnContext): TurnState {
  return context.state;
}

/**
 * Clear all sessions and reset turn counter (testing only).
 */
export function __test_resetRuntime(): void {
  __test_clearSessions();
  turnCounter = 0;
}
