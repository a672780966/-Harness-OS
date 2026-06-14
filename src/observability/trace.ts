/**
 * Harness OS — Run Trace
 *
 * Phase 7.2: Aggregated run trace with event references.
 * Stored as JSON at .project/reports/traces/<run-id>.json.
 *
 * Tracks: events, tool calls, file changes, approvals, context, verification.
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §13
 */

import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join, resolve } from 'path';
import { redactObject } from '../governance/redactor.js';

// ============================================================
// Types
// ============================================================

export interface RunTrace {
  runId: string;
  projectId: string;
  taskId?: string;
  sessionId?: string;
  status: 'running' | 'paused' | 'completed' | 'failed' | 'blocked';
  startedAt: string;
  endedAt?: string;
  contextPackIds: string[];
  checkpointIds: string[];
  verificationResultIds: string[];
  eventsPath: string;
  reportPath?: string;
  summary: string;
  toolCallCount: number;
  fileChangeCount: number;
  approvalCount: number;
}

// ============================================================
// Trace Store
// ============================================================

/**
 * Create a new run trace.
 */
export function createTrace(params: {
  runId: string;
  projectId: string;
  taskId?: string;
  sessionId?: string;
  summary?: string;
}): RunTrace {
  return {
    runId: params.runId,
    projectId: params.projectId,
    taskId: params.taskId,
    sessionId: params.sessionId,
    status: 'running',
    startedAt: new Date().toISOString(),
    contextPackIds: [],
    checkpointIds: [],
    verificationResultIds: [],
    eventsPath: `.project/reports/events/${params.runId}.jsonl`,
    summary: params.summary ?? '',
    toolCallCount: 0,
    fileChangeCount: 0,
    approvalCount: 0,
  };
}

// ============================================================
// Trace Operations
// ============================================================

/**
 * Save a trace to disk.
 */
export function saveTrace(trace: RunTrace, projectPath?: string): string {
  const resolvedPath = resolve(projectPath || process.cwd());
  const tracesDir = join(resolvedPath, '.project/reports/traces');
  if (!existsSync(tracesDir)) {
    mkdirSync(tracesDir, { recursive: true });
  }

  const tracePath = join(tracesDir, `${trace.runId}.json`);
  // Redact trace before persisting (SEC-06)
  const safeTrace = redactObject(trace) as RunTrace;
  writeFileSync(tracePath, JSON.stringify(safeTrace, null, 2) + '\n', 'utf-8');
  return tracePath;
}

/**
 * Load a trace from disk.
 */
export function loadTrace(runId: string, projectPath?: string): RunTrace | undefined {
  const resolvedPath = resolve(projectPath || process.cwd());
  const tracePath = join(resolvedPath, '.project/reports/traces', `${runId}.json`);
  if (!existsSync(tracePath)) return undefined;

  try {
    return JSON.parse(readFileSync(tracePath, 'utf-8')) as RunTrace;
  } catch {
    return undefined;
  }
}

// ============================================================
// Trace Updaters
// ============================================================

/**
 * Update trace status.
 */
export function updateTraceStatus(trace: RunTrace, status: RunTrace['status'], summary?: string): RunTrace {
  trace.status = status;
  if (status === 'completed' || status === 'failed') {
    trace.endedAt = new Date().toISOString();
  }
  if (summary) trace.summary = summary;
  return trace;
}

/**
 * Link a context pack to the trace.
 */
export function linkContextPack(trace: RunTrace, contextPackId: string): void {
  if (!trace.contextPackIds.includes(contextPackId)) {
    trace.contextPackIds.push(contextPackId);
  }
}

/**
 * Link a checkpoint to the trace.
 */
export function linkCheckpoint(trace: RunTrace, checkpointId: string): void {
  if (!trace.checkpointIds.includes(checkpointId)) {
    trace.checkpointIds.push(checkpointId);
  }
}

/**
 * Link a verification result to the trace.
 */
export function linkVerification(trace: RunTrace, verificationId: string): void {
  if (!trace.verificationResultIds.includes(verificationId)) {
    trace.verificationResultIds.push(verificationId);
  }
}

/**
 * Increment tool call counter.
 */
export function incrementToolCalls(trace: RunTrace): void {
  trace.toolCallCount += 1;
}

/**
 * Increment file change counter.
 */
export function incrementFileChanges(trace: RunTrace): void {
  trace.fileChangeCount += 1;
}

/**
 * Increment approval counter.
 */
export function incrementApprovals(trace: RunTrace): void {
  trace.approvalCount += 1;
}
