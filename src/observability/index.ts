/**
 * Harness OS — Observability Module
 *
 * Phase 7: Event logging, run tracing, and run report generation.
 *
 * Sub-modules:
 * - events.ts — JSONL event logger with secret redaction
 * - trace.ts  — Aggregated run trace with event/skill/approval tracking
 * - report.ts — Run report generation (Markdown) to .project/reports/runs/
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §11-20
 */

export { logEvent, logEvents, EventTypes, type HarnessEvent, type HarnessEventActor } from './events.js';

export {
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
  type RunTrace,
} from './trace.js';

export {
  generateRunReport,
  saveRunReport,
  loadRunReport,
  type RunReport,
} from './report.js';

// ============================================================
// Structured report data (CLI3-01)
// ============================================================

export interface ReportData {
  runId: string;
  trace: {
    status: string;
    startedAt: string;
    endedAt?: string;
    toolCallCount: number;
    contextPackCount: number;
    checkpointCount: number;
  } | null;
  report: string | null;
  found: boolean;
}

/**
 * Get structured report data — does NOT print (CLI3-01).
 * The CLI layer formats and outputs via the formatter.
 */
export async function getReport(runId: string): Promise<ReportData> {
  const { loadTrace } = await import('./trace.js');
  const { loadRunReport } = await import('./report.js');

  const trace = loadTrace(runId);
  const report = loadRunReport(runId);

  return {
    runId,
    trace: trace ? {
      status: trace.status,
      startedAt: trace.startedAt,
      endedAt: trace.endedAt,
      toolCallCount: trace.toolCallCount,
      contextPackCount: trace.contextPackIds.length,
      checkpointCount: trace.checkpointIds.length,
    } : null,
    report: report ?? null,
    found: !!report,
  };
}

/**
 * Legacy CLI helper. Prefer getReport() + formatter for JSON mode.
 */
export async function showReport(runId: string): Promise<void> {
  const data = await getReport(runId);

  if (data.trace) {
    console.log(`\nRun: ${data.runId}`);
    console.log(`Status: ${data.trace.status}`);
    console.log(`Started: ${data.trace.startedAt}`);
    console.log(`Tool calls: ${data.trace.toolCallCount}`);
    console.log(`Context packs: ${data.trace.contextPackCount}`);
    console.log(`Checkpoints: ${data.trace.checkpointCount}`);
    if (data.trace.endedAt) console.log(`Ended: ${data.trace.endedAt}`);
    console.log('');
  }

  if (data.report) {
    console.log(data.report);
  } else {
    console.log(`No run report found for: ${runId}`);
  }
}
