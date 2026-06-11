/**
 * Harness OS — State Module
 *
 * Phase 9: Run state, checkpoint, and session state management.
 *
 * Sub-modules:
 * - store.ts     — SqliteStore: persistent CRUD for sessions/turns/approvals
 * - schema.ts    — Table DDL and schema versioning
 * - run.ts       — Run lifecycle state (create/get/update/pause/fail/complete)
 * - checkpoint.ts — Checkpoint creation, loading, listing, rollback
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7.8
 *            11_ACCEPTANCE_CRITERIA.md §15
 */

export {
  SqliteStore,
  type StoreConfig,
} from './store.js';

export {
  createRunState,
  saveRunState,
  loadRunState,
  updateRunState,
  pauseRun,
  completeRun,
  failRun,
  listRunStates,
  linkCheckpointToRun,
  linkContextToRun,
  type RunStatus,
  type RunState,
} from './run.js';

export {
  createCheckpoint,
  loadCheckpoint,
  listCheckpoints,
  rollbackToCheckpoint,
  type CreateCheckpointParams,
  type RollbackResult,
} from './checkpoint.js';
