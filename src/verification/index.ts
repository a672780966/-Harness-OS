/**
 * Harness OS — Verification Module
 *
 * Phase 6: Verification Pipeline — detect commands, build plan, run, report.
 *
 * CLI4-01: Business modules return structured data.
 * NO console.log() here — CLI layer formats and outputs.
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §6-10
 */

import { detectCommands } from './commands.js';
import { buildPlan, formatPlan } from './plan.js';
import { runVerification, formatResults } from './runner.js';
import { generateReport, saveReport } from './report.js';
import type { RunResult } from './runner.js';

export { detectCommands, type CommandType, type DetectedCommand } from './commands.js';
export { buildPlan, formatPlan, type VerificationPlan, type VerificationStep } from './plan.js';
export { runVerification, formatResults, type RunResult } from './runner.js';
export { generateReport, saveReport, type VerificationReport } from './report.js';
export {
  saveVerificationResult,
  loadVerificationResult,
  checkVerificationBinding,
  computeIntegrity,
  getCurrentCommit,
  getCurrentTree,
  VERIFICATION_RESULT_SCHEMA_VERSION,
  type VerificationResult,
  type BindingCheckResult,
} from './result.js';

// ============================================================
// Structured Pipeline Result (CLI4-01)
// ============================================================

export interface VerificationPipelineResult {
  result: RunResult;
  verificationId: string;
  /** Human-readable plan text (for pretty mode). */
  planText?: string;
  /** Human-readable results text (for pretty mode). */
  resultsText?: string;
  /** Paths to saved reports. */
  reportPaths?: { mdPath: string; jsonPath: string };
}

export interface VerificationPipelineOptions {
  taskId?: string;
  runId?: string;
  projectId?: string;
  projectPath?: string;
}

/**
 * Run the full verification pipeline and return structured results.
 *
 * CLI4-01: Returns data only — NO console.log() calls.
 * CLI layer decides how to format/output.
 */
export async function runVerificationPipeline(
  options?: VerificationPipelineOptions,
): Promise<VerificationPipelineResult> {
  const projectPath = options?.projectPath ?? process.cwd();

  // 1. Detect commands
  const commands = detectCommands(projectPath);
  if (commands.length === 0) {
    return {
      result: { total: 0, passed: 0, failed: 0, skipped: 0, status: 'skipped', durationMs: 0 },
      verificationId: '',
      planText: 'No verification commands detected',
    };
  }

  // 2. Build plan
  const plan = buildPlan(projectPath, commands);
  const planText = formatPlan(plan);

  // 3. Run
  const runResult = await runVerification(plan);
  const resultsText = formatResults(plan.steps, runResult);

  // 4. Save report (Markdown + structured JSON with binding info)
  const verificationId = options?.runId ?? `ver_${Date.now().toString(36)}`;
  const report = generateReport(verificationId, plan.steps, runResult, {
    projectId: options?.projectId,
    taskId: options?.taskId,
    runId: options?.runId,
    projectPath,
    risks: [],
  });
  const paths = saveReport(report);

  return {
    result: runResult,
    verificationId,
    planText,
    resultsText,
    reportPaths: paths,
  };
}
