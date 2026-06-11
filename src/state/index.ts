/**
 * Harness OS — State Module
 *
 * Persistent state store using SQLite for sessions, turns, and approvals.
 *
 * Source: CLAUDE.md §8 (Session/State constraints).
 *
 * Sub-modules:
 * - store.ts  — SqliteStore: persistent CRUD for sessions/turns/approvals
 * - schema.ts — Table DDL and schema versioning
 *
 * Thin Harness: in-memory stores in runtime/session.ts and
 *   governance/approval-gate.ts are the default.
 *   SqliteStore is the "persistent upgrade" — swap in when needed.
 * Thick Harness extension: distributed state store, OpenTelemetry traces.
 */

export {
  SqliteStore,
  type StoreConfig,
} from './store.js';

// Legacy API — kept for backward compat
import type { Checkpoint } from '../types.js';

export async function createCheckpoint(): Promise<void> {
  console.log('Creating checkpoint');
  // TODO: Save git state, task state, context summary to .project/checkpoints/
}

export async function rollbackTo(checkpointId: string): Promise<void> {
  console.log(`Rolling back to: ${checkpointId}`);
  // TODO: Restore checkpoint state
}
