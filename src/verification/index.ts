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

// ============================================================
// CLI Entry Point
// ============================================================

export async function runVerificationPipeline(options?: {
  task?: string;
  run?: string;
  projectPath?: string;
}): Promise<RunResult> {
  const projectPath = options?.projectPath ?? process.cwd();

  // 1. Detect commands
  const commands = detectCommands(projectPath);
  if (commands.length === 0) {
    console.log('No verification commands detected');
    return { total: 0, passed: 0, failed: 0, skipped: 0, status: 'skipped', durationMs: 0 };
  }

  // 2. Build plan
  const plan = buildPlan(projectPath, commands);
  console.log(formatPlan(plan));
  console.log('');

  // 3. Run
  console.log('Running verification...\n');
  const result = await runVerification(plan);

  // 4. Format results
  console.log(formatResults(plan.steps, result));

  // 5. Save report
  const runId = options?.run ?? `ver_${Date.now().toString(36)}`;
  const report = generateReport(runId, plan.steps, result, {
    taskId: options?.task,
    projectPath,
    risks: [],
  });
  const reportPath = saveReport(report);
  console.log(`\nReport saved: ${reportPath}`);

  return result;
}
