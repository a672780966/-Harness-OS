/**
 * Harness OS — Session Manager
 *
 * Thin Harness session lifecycle: create, get, end sessions.
 *
 * Source: CLAUDE.md §8 (Session/State constraints).
 *
 * Design:
 * - In-memory session store (Thin Harness).
 * - Session writes require: clear schema, scope, actor, reason, trace id.
 * - Scoped to session lifetime — NOT global state.
 */

import { type SessionId, type SessionState } from '../types.js';

// ============================================================
// Session Store (in-memory, Thin Harness)
// ============================================================

class SessionStore {
  private sessions: Map<SessionId, SessionState> = new Map();

  add(session: SessionState): void {
    this.sessions.set(session.session_id, session);
  }

  get(id: SessionId): SessionState | undefined {
    return this.sessions.get(id);
  }

  update(id: SessionId, updates: Partial<SessionState>): SessionState | undefined {
    const existing = this.sessions.get(id);
    if (!existing) return undefined;
    const updated = { ...existing, ...updates, session_id: id };
    this.sessions.set(id, updated);
    return updated;
  }

  end(id: SessionId): SessionState | undefined {
    return this.update(id, { status: 'completed', last_active_at: new Date().toISOString() });
  }

  listActive(): SessionState[] {
    return Array.from(this.sessions.values())
      .filter((s) => s.status === 'active')
      .sort((a, b) => a.started_at.localeCompare(b.started_at));
  }

  clear(): void {
    this.sessions.clear();
  }

  get size(): number {
    return this.sessions.size;
  }
}

// Singleton store.
const store = new SessionStore();

// ============================================================
// Session ID Generation
// ============================================================

let counter = 0;

function generateSessionId(): SessionId {
  counter += 1;
  const ts = Date.now().toString(36);
  const seq = counter.toString(36).padStart(4, '0');
  return `ses_${ts}_${seq}` as SessionId;
}

// ============================================================
// Public API
// ============================================================

export interface CreateSessionParams {
  projectId: string;
  metadata?: Record<string, unknown>;
}

/**
 * Create a new session.
 *
 * State write requirements (§8):
 * - Schema: SessionState
 * - Scope: session-lifetime
 * - Actor: caller
 * - Reason: explicit
 * - Trace id: session_id
 */
export function createSession(params: CreateSessionParams): SessionState {
  const now = new Date().toISOString();
  const session: SessionState = {
    session_id: generateSessionId(),
    project_id: params.projectId,
    started_at: now,
    last_active_at: now,
    turn_count: 0,
    status: 'active',
    metadata: params.metadata ?? {},
  };

  store.add(session);
  return session;
}

/**
 * Get a session by ID.
 */
export function getSession(id: SessionId): SessionState | undefined {
  return store.get(id);
}

/**
 * End a session (mark as completed).
 */
export function endSession(id: SessionId): SessionState | undefined {
  return store.end(id);
}

/**
 * List all active sessions.
 */
export function listActiveSessions(): SessionState[] {
  return store.listActive();
}

/**
 * Increment turn count for a session.
 * Called internally by the orchestrator when a turn starts.
 */
export function incrementTurnCount(id: SessionId): number | undefined {
  const session = store.get(id);
  if (!session) return undefined;
  const count = session.turn_count + 1;
  store.update(id, {
    turn_count: count,
    last_active_at: new Date().toISOString(),
  });
  return count;
}

/**
 * Touch last_active_at timestamp.
 */
export function touchSession(id: SessionId): void {
  store.update(id, { last_active_at: new Date().toISOString() });
}

/**
 * Clear all sessions (testing only).
 */
export function __test_clearSessions(): void {
  store.clear();
}
