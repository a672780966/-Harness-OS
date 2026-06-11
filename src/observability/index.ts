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
// CLI Entry Point
// ============================================================

export async function showReport(runId: string): Promise<void> {
  const { loadTrace } = await import('./trace.js');
  const { loadRunReport } = await import('./report.js');

  // Try to load trace first
  const trace = loadTrace(runId);
  if (trace) {
    console.log(`\nRun: ${trace.runId}`);
    console.log(`Status: ${trace.status}`);
    console.log(`Started: ${trace.startedAt}`);
    console.log(`Tool calls: ${trace.toolCallCount}`);
    console.log(`Context packs: ${trace.contextPackIds.length}`);
    console.log(`Checkpoints: ${trace.checkpointIds.length}`);
    if (trace.endedAt) console.log(`Ended: ${trace.endedAt}`);
    console.log('');
  }

  // Try to load run report
  const report = loadRunReport(runId);
  if (report) {
    console.log(report);
  } else {
    console.log(`No run report found for: ${runId}`);
  }
}
