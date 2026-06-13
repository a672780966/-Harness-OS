/**
 * Harness OS — Task Manager Module
 *
 * Phase 3 + D: Task lifecycle and full run pipeline.
 *
 * Full run flow (Phase D):
 *   1. Create task record
 *   2. Transition to running
 *   3. Build Context Pack
 *   4. Create run state + trace — with verificationId binding
 *   5. Record observability events
 *   6. Create checkpoint
 *   7. Run verification — produces structured JSON result
 *   8. Complete task — loads verification from disk (VER3-02)
 *   9. Generate delivery outputs
 *   10. Save run report
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §7
 *            03_VERIFICATION_DELIVERY_STRONG_BINDING_FIX.md §4
 */

export {
  createTaskRecord,
  normalizeTitle,
  inferTaskType,
  extractExplicitRefs,
  type CreateTaskParams,
  type TaskRecord,
  type ExplicitRefs,
} from './create.js';

export {
  transitionStatus,
  isValidTransition,
  InvalidTransitionError,
  isTerminal,
  isRecoverable,
  getValidTransitions,
  getAllowedTargets,
  TERMINAL_STATUSES,
  ACTIVE_STATUSES,
  STALLED_STATUSES,
} from './state-machine.js';

export {
  completeTask,
  failTask,
  updateTaskState,
  type CompleteTaskParams,
  type FailTaskParams,
  type TaskCompletionResult,
  type UpdateTaskParams,
} from './complete.js';

// ============================================================
// CLI Entry Point — Full Run Pipeline
// ============================================================

import { readFileSync, writeFileSync } from 'fs';

async function getProjectId(projectPath: string): Promise<string> {
  try {
    const { existsSync } = await import('fs');
    const { join } = await import('path');
    const manifestPath = join(projectPath, '.project/state/manifest.json');
    if (existsSync(manifestPath)) {
      const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
      return manifest.projectId || 'unknown';
    }
  } catch {}
  return 'unknown';
}

/**
 * Full run: create task → context pack → verify → complete → report.
 *
 * VER3-02/VER3-03: Verification produces a structured result with integrity
 * hash. completeTask() loads it from disk — caller strings cannot override.
 */
export async function runTask(
  task: string,
  options?: { json?: boolean; quiet?: boolean },
): Promise<void> {
  const projectPath = process.cwd();
  const { detectOutputMode, jsonOutput, buildJsonOutput, prettySuccess, prettyError, prettyProgress, resetStartTime } = await import('../cli/formatter.js');
  const mode = detectOutputMode(options);
  resetStartTime();

  try {
    const projectId = await getProjectId(projectPath);
    const runId = `run_${Date.now().toString(36)}`;

    // ── 1. Create task record ──
    const { createTaskRecord } = await import('./create.js');
    const record = await createTaskRecord({ projectPath, userInstruction: task });
    const taskId = record.state.taskId;

    if (mode !== 'quiet') prettyProgress(`Task created: ${taskId} — ${record.state.title}`);

    // ── 2. Build Context Pack ──
    const { buildContextPack } = await import('../context/build.js');
    if (mode !== 'quiet') prettyProgress('Building Context Pack...');
    const pack = await buildContextPack({
      projectId,
      runId,
      taskId,
      userInstruction: task,
      workspacePath: projectPath,
    });

    // ── 3. Create run state ──
    const { createRunState, saveRunState, linkContextToRun } = await import('../state/run.js');
    const runState = createRunState({ projectId, taskId, runId });
    linkContextToRun(runState.runId, pack.id, projectPath);
    saveRunState(runState, projectPath);

    // ── 4. Create trace ──
    const { createTrace, saveTrace, linkContextPack } = await import('../observability/trace.js');
    const trace = createTrace({ runId, projectId, taskId, summary: record.state.title });
    linkContextPack(trace, pack.id);
    saveTrace(trace, projectPath);

    // ── 5. Record events ──
    const { logEvent, EventTypes } = await import('../observability/events.js');
    logEvent({ projectId, type: EventTypes.runStarted, actor: 'harness', summary: `Run started: ${record.state.title}`, runId, taskId }, projectPath);
    logEvent({ projectId, type: EventTypes.taskCreated, actor: 'harness', summary: `Task created: ${taskId}`, runId, taskId }, projectPath);
    logEvent({ projectId, type: EventTypes.contextBuildCompleted, actor: 'harness', summary: `Context Pack built: ${pack.id}`, runId, taskId, payload: { files: pack.files.length, skills: pack.skills.length } }, projectPath);

    // ── 6. Create checkpoint ──
    const { createCheckpoint } = await import('../state/checkpoint.js');
    const cp = await createCheckpoint({ projectPath, taskId, runId, contextSummary: record.state.title });
    const { linkCheckpointToRun } = await import('../state/run.js');
    linkCheckpointToRun(runId, cp.id, projectPath);

    if (mode !== 'quiet') prettyProgress(`Checkpoint: ${cp.id}`);

    // ── 7. Run verification ──
    // VER3-02/VER3-03: Use structured verification pipeline that produces
    // a JSON result with integrity hash, bound to project/task/run/commit.
    const { detectCommands } = await import('../verification/commands.js');
    const { buildPlan } = await import('../verification/plan.js');
    const { runVerification, formatResults } = await import('../verification/runner.js');
    const { generateReport, saveReport } = await import('../verification/report.js');
    const { loadVerificationResult } = await import('../verification/result.js');

    if (mode !== 'quiet') prettyProgress('Running verification...');

    let verificationId: string | undefined;
    let verificationStatus: 'passed' | 'failed' | 'skipped' = 'skipped';
    const commands = detectCommands(projectPath);
    if (commands.length > 0) {
      logEvent({ projectId, type: EventTypes.verificationStarted, actor: 'harness', summary: `Verification: ${commands.length} commands`, runId, taskId }, projectPath);

      const plan = buildPlan(projectPath, commands);
      const result = await runVerification(plan);
      verificationId = `ver_${Date.now().toString(36)}`;
      const report = generateReport(verificationId, plan.steps, result, {
        projectId,
        taskId,
        projectPath,
        risks: [],
      });

      // Save both Markdown and structured JSON with binding (VER4-01/VER4-04)
      const paths = saveReport(report);

      verificationStatus = result.status === 'passed' ? 'passed' : result.status === 'failed' ? 'failed' : 'skipped';

      logEvent({
        projectId, type: verificationStatus === 'passed' ? EventTypes.verificationCompleted : EventTypes.verificationFailed,
        actor: 'harness', summary: `Verification ${verificationStatus}: ${result.passed}/${result.total} passed`,
        runId, taskId, payload: { passed: result.passed, failed: result.failed, skipped: result.skipped },
      }, projectPath);

      if (mode !== 'quiet') console.log(formatResults(plan.steps, result));
    }

    // ── 8. Complete task ──
    const { completeTask, failTask } = await import('./complete.js');

    let completionResult: Awaited<ReturnType<typeof completeTask>>;

    if (verificationId && verificationStatus === 'passed') {
      // VER3-02: completeTask() loads verification from disk internally
      completionResult = await completeTask({
        projectPath,
        taskId,
        projectId,
        runId,
        changedFiles: [],
        verificationId,
      });

      logEvent({
        projectId, type: EventTypes.taskCompleted, actor: 'harness',
        summary: `Task completed: ${record.state.title}`,
        runId, taskId,
      }, projectPath);

      // VER3-03: Update run state with verificationId
      const { updateRunState } = await import('../state/run.js');
      updateRunState(runId, { verificationResultId: verificationId }, projectPath);

    } else {
      // Failed/skipped verification → fail the task
      const reason = verificationId
        ? `Verification ${verificationStatus}`
        : 'No verification commands found';

      completionResult = await failTask({
        projectPath,
        taskId,
        verificationId,
        failureReason: reason,
        recoveryHint: verificationStatus === 'failed'
          ? 'Fix the failing checks and re-run verification'
          : 'Configure verification commands in AGENTS.md or package.json',
      });

      logEvent({
        projectId, type: EventTypes.taskFailed, actor: 'harness',
        summary: `Task failed: ${record.state.title} (${reason})`,
        runId, taskId,
      }, projectPath);
    }

    // ── 9. Generate run report ──
    const { generateRunReport, saveRunReport } = await import('../observability/report.js');
    const runReport = generateRunReport(trace, {
      title: record.state.title,
      verificationStatus,
      // risks: completionResult.risks,
    });
    const reportPath = saveRunReport(runReport, projectPath);

    // ── 10. Generate delivery outputs ──
    const { generateCommitMessage } = await import('../delivery/commit.js');
    const commitMsg = generateCommitMessage({
      taskType: record.state.type,
      taskSummary: record.state.title,
      details: `Verification: ${verificationStatus} (${verificationId ?? 'none'})`,
    });

    // ── Output ──
    if (mode === 'json') {
      jsonOutput(buildJsonOutput({
        command: 'run', status: completionResult.finalStatus === 'completed' ? 'success' : 'failed',
        data: {
          taskId, runId, title: record.state.title, type: record.state.type,
          verificationId, verificationStatus, checkpointId: cp.id, contextPackId: pack.id, reportPath,
          finalStatus: completionResult.finalStatus,
          commitMessage: commitMsg.full,
        },
      }));
    } else if (mode === 'quiet') {
      console.log(taskId);
    } else {
      const statusLine = completionResult.finalStatus === 'completed' ? 'Run completed' : 'Run failed';
      prettySuccess(statusLine, {
        Task: `${taskId} — ${record.state.title}`,
        Type: record.state.type,
        'Context Pack': pack.id,
        Checkpoint: cp.id,
        Verification: `${verificationStatus}${verificationId ? ` (${verificationId})` : ''}`,
        'Final Status': completionResult.finalStatus,
        Report: reportPath,
      }, [
        `harness verify --task ${taskId}`,
        `harness report ${runId}`,
      ]);
    }

    // ── Complete trace ──
    const { updateTraceStatus, saveTrace: saveTrace2 } = await import('../observability/trace.js');
    updateTraceStatus(trace, completionResult.finalStatus === 'completed' ? 'completed' : 'failed',
      `Task ${completionResult.finalStatus}`);
    saveTrace2(trace, projectPath);

    logEvent({
      projectId, type: EventTypes.runCompleted, actor: 'harness',
      summary: `Run ${completionResult.finalStatus}: ${runId}`,
      runId, taskId,
    }, projectPath);

  } catch (err) {
    const error = err instanceof Error ? err.message : String(err);
    if (mode === 'json') {
      jsonOutput(buildJsonOutput({ command: 'run', status: 'failed', error: { code: 'ERR_RUN_FAILED', category: 'task', severity: 'error' as const, message: error, recoveryHint: 'Check the error and try again', recoverable: true, retryable: true, userActionRequired: false, createdAt: new Date().toISOString() } }));
    } else {
      prettyError('ERR_RUN_FAILED', `Run failed: ${error}`, 'Check the error and try again');
    }
    process.exitCode = 1;
  }
}

/**
 * Resume a run (read run state and continue).
 */
export async function resumeRun(runId: string): Promise<void> {
  const { loadRunState } = await import('../state/run.js');
  const { loadTrace } = await import('../observability/trace.js');

  const state = loadRunState(runId);
  if (!state) {
    console.error(`Run not found: ${runId}`);
    process.exitCode = 1;
    return;
  }

  console.log(`\nResuming run: ${runId}`);
  console.log(`Task: ${state.taskId}`);
  console.log(`Status: ${state.status}`);
  console.log(`Checkpoints: ${state.checkpointIds.length}`);
  if (state.currentCheckpointId) {
    console.log(`Last checkpoint: ${state.currentCheckpointId}`);
  }
  // TODO: Restore checkpoint and continue execution
}
