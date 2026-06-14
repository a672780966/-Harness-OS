/**
 * Harness OS — Delivery Module
 *
 * Phase 8: Delivery Pipeline — guard, commit message, PR body, report.
 *
 * VER3-05: Guard-blocked deliveries produce NO ready output:
 * - No commit message generated
 * - No PR body generated
 * - Delivery report status=blocked with guard reasons
 * - Non-zero exit code
 *
 * CLI3-03: Delivery supports --json output via _outputMode parameter.
 *
 * Reference: 10_DELIVERY_PIPELINE.md
 *            03_VERIFICATION_DELIVERY_STRONG_BINDING_FIX.md §4
 */

export { runGuard, formatGuardResult, type GuardResult, type GuardCheck } from './guard.js';
export { generateCommitMessage, generateCommitFromTask, taskTypeToCommitType, type CommitMessage } from './commit.js';
export { generatePrBody, type PrBody, type PrBodyInput } from './pr.js';
export { generateDeliveryReport, saveDeliveryReport, type DeliveryReport, type DeliveryType, type DeliveryStatus } from './report.js';

// ============================================================
// Types
// ============================================================

import type { DeliveryType } from './report.js';
import { redactText } from '../governance/redactor.js';

export interface DeliveryResult {
  deliveryId: string;
  type: DeliveryType;
  status: 'ready' | 'blocked';
  guardResult: import('./guard.js').GuardResult;
  commitMessage?: import('./commit.js').CommitMessage;
  prBody?: import('./pr.js').PrBody;
  reportPath?: string;
}

// ============================================================
// CLI Entry Point
// ============================================================

/**
 * Run the delivery pipeline.
 *
 * @param options._outputMode - Internal: set by CLI layer for JSON routing.
 *   When 'json', always outputs a JSON envelope via process.stdout.
 */
export async function runDelivery(options?: {
  commit?: boolean;
  pr?: boolean;
  release?: boolean;
  deploy?: string;
  taskId?: string;
  runId?: string;
  verId?: string;
  taskTitle?: string;
  taskType?: string;
  changedFiles?: string[];
  projectPath?: string;
  /** Internal: output mode from CLI layer. */
  _outputMode?: 'json' | 'pretty' | 'quiet';
}): Promise<DeliveryResult> {
  const projectPath = options?.projectPath ?? process.cwd();
  const projectId = 'proj_' + Date.now().toString(36);
  const outputMode = options?._outputMode;

  // Determine delivery type
  let deliveryType: DeliveryType = 'commit';
  if (options?.pr) deliveryType = 'pull-request';
  if (options?.release) deliveryType = 'release';
  if (options?.deploy) deliveryType = 'deploy';

  // 1. Run guard — verId is required (VER3-04)
  const { runGuard, formatGuardResult } = await import('./guard.js');
  const guard = await runGuard({
    deliveryType,
    projectPath,
    taskId: options?.taskId,
    runId: options?.runId,
    verId: options?.verId ?? '',
  });

  // Format guard output
  if (outputMode !== 'json') {
    console.log(redactText(formatGuardResult(guard)));
    console.log('');
  }

  // VER3-05: Guard blocked → no commit message, no PR, no ready output
  if (!guard.canProceed) {
    const { generateDeliveryReport, saveDeliveryReport } = await import('./report.js');
    const deliveryId = `del_${Date.now().toString(36)}`;
    const report = generateDeliveryReport({
      deliveryId,
      projectId,
      type: deliveryType,
      taskId: options?.taskId,
      runId: options?.runId,
      guardResult: guard,
      summary: `Delivery blocked by guard checks (verId: ${options?.verId ?? 'none'})`,
    });
    const reportPath = saveDeliveryReport(report, projectPath);

    if (outputMode !== 'json') {
      console.log(redactText(`Blocked delivery report saved: ${reportPath}`));
      console.log(redactText('\n❌ Delivery blocked by guard checks.'));
      console.log(redactText('No commit message or PR body generated. [VER3-05]'));
    }

    // In JSON mode, return the result (CLI layer outputs the envelope)
    if (outputMode === 'json') {
      return {
        deliveryId,
        type: deliveryType,
        status: 'blocked',
        guardResult: guard,
        reportPath,
      };
    }

    return {
      deliveryId,
      type: deliveryType,
      status: 'blocked',
      guardResult: guard,
      reportPath,
    };
  }

  // 2. Generate commit message
  const { generateCommitFromTask } = await import('./commit.js');
  const commitMsg = generateCommitFromTask({
    taskTitle: options?.taskTitle ?? 'Update',
    taskType: options?.taskType,
    changedFiles: options?.changedFiles,
    runId: options?.runId,
  });

  if (outputMode !== 'json') {
    console.log(redactText('Generated commit message:'));
    console.log('---');
    console.log(redactText(commitMsg.full));
    console.log('---\n');
  }

  // 3. Generate PR body if requested
  let prBody;
  if (options?.pr) {
    const { generatePrBody } = await import('./pr.js');
    prBody = generatePrBody({
      title: commitMsg.full,
      taskId: options?.taskId,
      runId: options?.runId,
      changedFiles: options?.changedFiles,
    });
    if (outputMode !== 'json') {
      console.log(redactText('Generated PR body:'));
      console.log('---');
      console.log(redactText(prBody.body));
      console.log('---\n');
    }
  }

  // 4. Save delivery report
  const { generateDeliveryReport, saveDeliveryReport } = await import('./report.js');
  const deliveryId = `del_${Date.now().toString(36)}`;
  const report = generateDeliveryReport({
    deliveryId,
    projectId,
    type: deliveryType,
    taskId: options?.taskId,
    runId: options?.runId,
    commitMessage: commitMsg,
    prBody,
    guardResult: guard,
    summary: `Delivery for ${options?.taskTitle || 'untitled task'}`,
  });
  const reportPath = saveDeliveryReport(report, projectPath);

  if (outputMode !== 'json') {
    console.log(redactText(`Delivery report saved: ${reportPath}`));
    console.log(redactText('\n✅ Delivery guard passed. Ready to proceed.'));
  }

  return {
    deliveryId,
    type: deliveryType,
    status: 'ready',
    guardResult: guard,
    commitMessage: commitMsg,
    prBody,
    reportPath,
  };
}
