/**
 * Harness OS — Verification Module
 *
 * Phase 6: Verification Pipeline — detect commands, build plan, run, report.
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
// CLI Entry Point
// ============================================================

export interface VerificationPipelineOptions {
  taskId?: string;
  runId?: string;
  projectId?: string;
  projectPath?: string;
}

/**
 * Run the full verification pipeline and return structured results.
 *
 * Returns both the RunResult and the verificationId for binding.
 */
export async function runVerificationPipeline(
  options?: VerificationPipelineOptions,
): Promise<{ result: RunResult; verificationId: string }> {
  const projectPath = options?.projectPath ?? process.cwd();

  // 1. Detect commands
  const commands = detectCommands(projectPath);
  if (commands.length === 0) {
    console.log('No verification commands detected');
    return {
      result: { total: 0, passed: 0, failed: 0, skipped: 0, status: 'skipped', durationMs: 0 },
      verificationId: '',
    };
  }

  // 2. Build plan
  const plan = buildPlan(projectPath, commands);
  console.log(formatPlan(plan));
  console.log('');

  // 3. Run
  console.log('Running verification...\n');
  const runResult = await runVerification(plan);

  // 4. Format results
  console.log(formatResults(plan.steps, runResult));

  // 5. Save report (Markdown + structured JSON with binding info)
  // VER4-01/VER4-04: projectId is set at generation time, not patched after.
  const verificationId = options?.runId ?? `ver_${Date.now().toString(36)}`;
  const report = generateReport(verificationId, plan.steps, runResult, {
    projectId: options?.projectId,
    taskId: options?.taskId,
    projectPath,
    risks: [],
  });
  const paths = saveReport(report);

  console.log(`\nReport saved: ${paths.mdPath}`);
  console.log(`Structured result: ${paths.jsonPath}`);

  return { result: runResult, verificationId };
}
