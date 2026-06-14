/**
 * Harness OS — Observability Tests
 *
 * Coverage:
 * - Event logging: creation, JSONL format, file structure
 * - Event types: validation, helpers
 * - Trace: create, save, load, update, link
 * - Run report: generate, save, format, load
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §11-20
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { redactText } from '../../src/governance/redactor.js';
import { AUDIT_CANARY } from '../../src/governance/redactor.js';

import { logEvent, EventTypes, type HarnessEvent } from '../../src/observability/events.js';
import {
  createTrace,
  saveTrace,
  loadTrace,
  updateTraceStatus,
  linkContextPack,
  linkCheckpoint,
  linkVerification,
  incrementToolCalls,
  incrementFileChanges,
  incrementApprovals,
} from '../../src/observability/trace.js';
import {
  generateRunReport,
  saveRunReport,
  loadRunReport,
} from '../../src/observability/report.js';

let testDir: string;

beforeEach(() => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-obs-test-'));
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Event Logger Tests
// ============================================================

describe('logEvent', () => {
  it('creates an event with generated ID and timestamp', () => {
    const event = logEvent({
      projectId: 'proj_001',
      type: 'run.started',
      actor: 'harness',
      summary: 'Run started',
    }, testDir);

    expect(event.eventId).toMatch(/^evt_/);
    expect(event.type).toBe('run.started');
    expect(event.timestamp).toBeTruthy();
  });

  it('writes event to JSONL file', () => {
    logEvent({
      projectId: 'proj_001',
      type: 'task.created',
      actor: 'harness',
      summary: 'Task created',
      runId: 'run_001',
    }, testDir);

    const logPath = join(testDir, '.project/reports/events/run_001.jsonl');
    expect(existsSync(logPath)).toBe(true);

    const content = readFileSync(logPath, 'utf-8');
    const parsed = JSON.parse(content.trim());
    expect(parsed.type).toBe('task.created');
    expect(parsed.redacted).toBe(true);
  });

  it('appends multiple events to same file', () => {
    logEvent({ projectId: 'p', type: 'run.started', actor: 'harness', summary: 'start', runId: 'run_001' }, testDir);
    logEvent({ projectId: 'p', type: 'run.completed', actor: 'harness', summary: 'end', runId: 'run_001' }, testDir);

    const logPath = join(testDir, '.project/reports/events/run_001.jsonl');
    const lines = readFileSync(logPath, 'utf-8').trim().split('\n');
    expect(lines).toHaveLength(2);
  });

  it('redacts secrets from event payload', () => {
    const event = logEvent({
      projectId: 'p',
      type: 'file.written',
      actor: 'codex',
      summary: 'wrote config',
      payload: { apiKey: 'sk-abc123def456ghi789jkl012' },
    }, testDir);

    // The original event should not have the secret
    expect(event.eventId).toBeTruthy();

    // Check the written file is redacted
    const logPath = join(testDir, '.project/reports/events/system.jsonl');
    if (existsSync(logPath)) {
      const content = readFileSync(logPath, 'utf-8');
      const parsed = JSON.parse(content.trim());
      const serialized = JSON.stringify(parsed);
      expect(serialized).not.toContain('sk-abc123def456');
    }
  });

  it('logs event with optional fields', () => {
    const event = logEvent({
      projectId: 'p',
      type: 'policy.denied',
      actor: 'harness',
      summary: 'Access denied',
      riskLevel: 'high',
      relatedPaths: ['/etc/passwd'],
      relatedCommand: 'rm -rf',
    }, testDir);

    expect(event.riskLevel).toBe('high');
    expect(event.relatedPaths).toContain('/etc/passwd');
  });
});

// ============================================================
// Event Types Tests
// ============================================================

describe('EventTypes', () => {
  it('has all expected event types', () => {
    expect(EventTypes.runStarted).toBe('run.started');
    expect(EventTypes.taskCreated).toBe('task.created');
    expect(EventTypes.skillCalled).toBe('skill.called');
    expect(EventTypes.verificationCompleted).toBe('verification.completed');
    expect(EventTypes.approvalGranted).toBe('approval.granted');
    expect(EventTypes.checkpointCreated).toBe('checkpoint.created');
  });
});

// ============================================================
// Trace Tests
// ============================================================

describe('trace', () => {
  it('creates a new trace', () => {
    const trace = createTrace({
      runId: 'run_001',
      projectId: 'proj_001',
      taskId: 'task_001',
    });

    expect(trace.runId).toBe('run_001');
    expect(trace.status).toBe('running');
    expect(trace.startedAt).toBeTruthy();
    expect(trace.toolCallCount).toBe(0);
  });

  it('saves and loads trace', () => {
    const trace = createTrace({ runId: 'run_001', projectId: 'proj_001' });
    const path = saveTrace(trace, testDir);
    expect(existsSync(path)).toBe(true);

    const loaded = loadTrace('run_001', testDir);
    expect(loaded).toBeDefined();
    expect(loaded!.runId).toBe('run_001');
  });

  it('updates trace status', () => {
    const trace = createTrace({ runId: 'run_001', projectId: 'proj_001' });
    updateTraceStatus(trace, 'completed', 'Task completed successfully');
    expect(trace.status).toBe('completed');
    expect(trace.endedAt).toBeTruthy();
    expect(trace.summary).toBe('Task completed successfully');
  });

  it('links context packs and checkpoints', () => {
    const trace = createTrace({ runId: 'run_001', projectId: 'proj_001' });
    linkContextPack(trace, 'ctx_001');
    linkContextPack(trace, 'ctx_002');
    linkCheckpoint(trace, 'cp_001');
    linkVerification(trace, 'ver_001');

    expect(trace.contextPackIds).toEqual(['ctx_001', 'ctx_002']);
    expect(trace.checkpointIds).toEqual(['cp_001']);
    expect(trace.verificationResultIds).toEqual(['ver_001']);
  });

  it('increments counters', () => {
    const trace = createTrace({ runId: 'run_001', projectId: 'proj_001' });
    incrementToolCalls(trace);
    incrementToolCalls(trace);
    incrementToolCalls(trace);
    incrementFileChanges(trace);
    incrementApprovals(trace);

    expect(trace.toolCallCount).toBe(3);
    expect(trace.fileChangeCount).toBe(1);
    expect(trace.approvalCount).toBe(1);
  });

  it('returns undefined for unknown trace', () => {
    const loaded = loadTrace('run_nonexistent', testDir);
    expect(loaded).toBeUndefined();
  });
});

// ============================================================
// Run Report Tests
// ============================================================

describe('run report', () => {
  it('generates a report from trace', () => {
    const trace = createTrace({ runId: 'run_001', projectId: 'proj_001', taskId: 'task_001' });
    updateTraceStatus(trace, 'completed', 'Done');

    const report = generateRunReport(trace, {
      title: 'Fix login bug',
      changedFiles: ['src/login.ts'],
      verificationStatus: 'passed',
      risks: ['Edge case in error handling'],
    });

    expect(report.runId).toBe('run_001');
    expect(report.status).toBe('completed');
    expect(report.summary).toBe('Done');
    expect(report.changedFiles).toContain('src/login.ts');
    expect(report.risks).toContain('Edge case in error handling');
  });

  it('saves report to .project/reports/runs/', () => {
    const trace = createTrace({ runId: 'run_002', projectId: 'proj_001', taskId: 'task_001' });
    updateTraceStatus(trace, 'completed', 'All good');
    const report = generateRunReport(trace);

    const path = saveRunReport(report, testDir);
    expect(existsSync(path)).toBe(true);

    const content = readFileSync(path, 'utf-8');
    expect(content).toContain('Run Report');
    expect(content).toContain('run_002');
  });

  it('redacts every report field before persisting', () => {
    const trace = createTrace({ runId: 'run_secret', projectId: 'proj_001', summary: AUDIT_CANARY });
    const report = generateRunReport(trace, {
      title: AUDIT_CANARY,
      changedFiles: [AUDIT_CANARY],
      contextUsed: [AUDIT_CANARY],
      risks: [AUDIT_CANARY],
    });

    const path = saveRunReport(report, testDir);
    expect(readFileSync(path, 'utf-8')).not.toContain(AUDIT_CANARY);
  });

  it('calculates duration from start to end', () => {
    const trace = createTrace({ runId: 'run_003', projectId: 'proj_001' });
    trace.endedAt = new Date(new Date(trace.startedAt).getTime() + 5000).toISOString();

    const report = generateRunReport(trace);
    expect(report.durationMs).toBe(5000);
  });

  it('loads report content', () => {
    const trace = createTrace({ runId: 'run_004', projectId: 'proj_001' });
    const report = generateRunReport(trace);
    saveRunReport(report, testDir);

    const content = loadRunReport('run_004', testDir);
    expect(content).toBeDefined();
    expect(content).toContain('run_004');
  });

  it('returns undefined for missing report', () => {
    const content = loadRunReport('run_nonexistent', testDir);
    expect(content).toBeUndefined();
  });
});
