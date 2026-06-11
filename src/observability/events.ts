/**
 * Harness OS — Event Logger
 *
 * Phase 7.1: JSONL event logging to .project/reports/events/<run-id>.jsonl.
 *
 * All events are secret-redacted before writing.
 * Format: one JSON object per line, append-only.
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §12
 *            08_GOVERNANCE_SECURITY.md §13 (secret redaction)
 */

import { existsSync, mkdirSync, appendFileSync } from 'fs';
import { join, resolve } from 'path';
import { redactObject } from '../governance/redactor.js';

// ============================================================
// Types
// ============================================================

export type HarnessEventActor = 'user' | 'codex' | 'harness' | 'skill' | 'system';

export interface HarnessEvent {
  eventId: string;
  projectId: string;
  taskId?: string;
  runId?: string;
  sessionId?: string;
  type: string;
  timestamp: string;
  actor: HarnessEventActor;
  summary: string;
  payload?: unknown;
  riskLevel?: 'low' | 'medium' | 'high';
  relatedPaths?: string[];
  relatedCommand?: string;
  redacted: boolean;
}

// ============================================================
// Event ID Generation
// ============================================================

let counter = 0;

function generateEventId(): string {
  counter += 1;
  return `evt_${Date.now().toString(36)}_${counter.toString(36).padStart(4, '0')}`;
}

// ============================================================
// Validate event type
// ============================================================

const VALID_EVENT_PREFIXES = [
  'run.', 'task.', 'context.', 'skill.', 'file.', 'git.',
  'policy.', 'approval.', 'verification.', 'delivery.',
  'checkpoint.', 'secret.', 'security.',
];

function validateEventType(type: string): boolean {
  return VALID_EVENT_PREFIXES.some(p => type.startsWith(p));
}

// ============================================================
// Event Logger
// ============================================================

/**
 * Write a single event to the JSONL event log.
 *
 * @param params - Event data (without eventId/timestamp — auto-generated)
 * @param projectPath - Project root (default: cwd)
 * @returns The created event
 */
export function logEvent(
  params: {
    projectId: string;
    type: string;
    actor: HarnessEventActor;
    summary: string;
    taskId?: string;
    runId?: string;
    sessionId?: string;
    payload?: unknown;
    riskLevel?: 'low' | 'medium' | 'high';
    relatedPaths?: string[];
    relatedCommand?: string;
  },
  projectPath?: string,
): HarnessEvent {
  const resolvedPath = resolve(projectPath || process.cwd());
  const runId = params.runId || 'system';

  if (!validateEventType(params.type)) {
    console.warn(`Warning: event type "${params.type}" doesn't match expected prefix pattern`);
  }

  // Create event
  const event: HarnessEvent = {
    eventId: generateEventId(),
    projectId: params.projectId,
    taskId: params.taskId,
    runId,
    sessionId: params.sessionId,
    type: params.type,
    timestamp: new Date().toISOString(),
    actor: params.actor,
    summary: params.summary,
    payload: params.payload,
    riskLevel: params.riskLevel,
    relatedPaths: params.relatedPaths,
    relatedCommand: params.relatedCommand,
    redacted: false,
  };

  // Redact sensitive data before writing
  const redacted = redactObject(event) as HarnessEvent;
  redacted.redacted = true;

  // Ensure directory exists
  const eventsDir = join(resolvedPath, '.project/reports/events');
  if (!existsSync(eventsDir)) {
    mkdirSync(eventsDir, { recursive: true });
  }

  // Append to JSONL
  const logPath = join(eventsDir, `${runId}.jsonl`);
  appendFileSync(logPath, JSON.stringify(redacted) + '\n', 'utf-8');

  return event;
}

/**
 * Log multiple events in batch.
 */
export function logEvents(
  events: Array<Parameters<typeof logEvent>[0]>,
  projectPath?: string,
): HarnessEvent[] {
  return events.map(e => logEvent(e, projectPath));
}

// ============================================================
// Event Type Helpers
// ============================================================

export const EventTypes = {
  // Run lifecycle
  runStarted: 'run.started',
  runPaused: 'run.paused',
  runResumed: 'run.resumed',
  runCompleted: 'run.completed',
  runFailed: 'run.failed',

  // Task lifecycle
  taskCreated: 'task.created',
  taskReady: 'task.ready',
  taskStarted: 'task.started',
  taskBlocked: 'task.blocked',
  taskVerifying: 'task.verifying',
  taskCompleted: 'task.completed',
  taskFailed: 'task.failed',

  // Context
  contextBuildStarted: 'context.build.started',
  contextBuildCompleted: 'context.build.completed',
  contextRefreshed: 'context.refreshed',
  contextSnapshotSaved: 'context.snapshot.saved',

  // Skill
  skillCalled: 'skill.called',
  skillCompleted: 'skill.completed',
  skillFailed: 'skill.failed',
  skillBlocked: 'skill.blocked',

  // File
  fileRead: 'file.read',
  fileWritten: 'file.written',
  fileEdited: 'file.edited',
  fileDeleted: 'file.deleted',
  fileBlocked: 'file.blocked',

  // Policy / Approval
  policyChecked: 'policy.checked',
  policyAllowed: 'policy.allowed',
  policyDenied: 'policy.denied',
  approvalRequested: 'approval.requested',
  approvalGranted: 'approval.granted',
  approvalDenied: 'approval.denied',

  // Verification
  verificationStarted: 'verification.started',
  verificationCommandStarted: 'verification.command.started',
  verificationCommandCompleted: 'verification.command.completed',
  verificationCommandFailed: 'verification.command.failed',
  verificationCompleted: 'verification.completed',
  verificationFailed: 'verification.failed',

  // Delivery
  deliveryStarted: 'delivery.started',
  deliveryCommitGenerated: 'delivery.commit.generated',
  deliveryPrGenerated: 'delivery.pr.generated',
  deliveryCompleted: 'delivery.completed',
  deliveryBlocked: 'delivery.blocked',

  // Checkpoint
  checkpointCreated: 'checkpoint.created',
  checkpointRestored: 'checkpoint.restored',

  // Security
  secretRedacted: 'secret.redacted',
  securityViolation: 'security.violation',
} as const;
