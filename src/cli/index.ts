#!/usr/bin/env node
/**
 * Harness OS CLI Entry Point
 *
 * CLI3-01: All output goes through a single router. Business modules
 * return structured data; the CLI layer formats and outputs.
 *
 * CLI3-02: Every JSON output has a uniform envelope with ok/command/
 * status/data/error/warnings/meta.
 *
 * CLI3-03: All commands support --json output.
 * CLI3-04: --json command and command --json behave identically.
 * CLI3-05: process.exitCode is set, never process.exit() in deep modules.
 *
 * CLI4-01: Only the CLI output router writes stdout. Business modules
 * return structured data; they never console.log() directly.
 *
 * CLI4-02: ok, status, and exit code are always consistent.
 *
 * Codex-first Project Operating System
 * Version 1.0.0
 */

import { Command } from 'commander';
import { HARNESS_VERSION } from '../version.js';
import { redactText } from '../governance/redactor.js';

const program = new Command();

program.name('harness').description('Harness OS - Codex-first Project Operating System');

program
  .option('--json', 'JSON output mode')
  .option('--quiet', 'Quiet output mode')
  .option('--no-color', 'Disable color output')
  .option('--log-level <level>', 'Log level (debug|info|warn|error)');

// Handle --version before Commander's parse
const idxVersion = process.argv.indexOf('--version');
const idxV = process.argv.indexOf('-V');
const idxJson = process.argv.indexOf('--json');
const idxJ = process.argv.indexOf('-j');
const hasVersion = idxVersion >= 0 || idxV >= 0;
const hasJson = idxJson >= 0 || idxJ >= 0;

if (hasVersion) {
  if (hasJson) {
    const envelope = {
      ok: true,
      command: 'version',
      status: 'success' as const,
      data: { version: HARNESS_VERSION },
      warnings: [] as string[],
      meta: {
        version: HARNESS_VERSION,
        outputMode: 'json' as const,
        generatedAt: new Date().toISOString(),
        durationMs: 0,
        redacted: true,
      },
    };
    process.stdout.write(JSON.stringify(envelope, null, 2) + '\n');
  } else {
    console.log(HARNESS_VERSION);
  }
  process.exit(0);
}

// ============================================================
// Project commands
// ============================================================

program
  .command('create <project-name>')
  .description('Create a new Harness OS project')
  .option('-p, --path <path>', 'Custom project path')
  .option('-q, --quiet', 'Quiet output mode')
  .option('-t, --type <type>', 'Project type (web-app, backend-service, cli, library, agent-harness)')
  .action(async (name, options) => {
    const { createProject } = await import('../project/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettySuccess, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = await createProject({ name, path: options.path, projectType: options.type });

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'create',
            status: 'success',
            data: {
              projectId: result.projectId,
              name: result.name,
              path: result.path,
              agentsMdCreated: result.agentsMdCreated,
              manifestPath: result.manifestPath,
              checkpointId: result.checkpointId,
            },
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(result.path);
      } else {
        prettySuccess(
          'Project created',
          {
            Name: result.name,
            Path: result.path,
            'AGENTS.md': result.agentsMdCreated ? 'created' : 'already exists',
            Manifest: result.manifestPath,
            Checkpoint: result.checkpointId,
          },
          [`cd ${result.path}`, 'harness run "your task"'],
        );
      }
    } catch (err) {
      const { createProjectNotFoundError } = await import('../errors/index.js');
      const error =
        err instanceof Error
          ? createProjectNotFoundError(err.message)
          : {
              code: 'ERR_INTERNAL',
              category: 'project',
              severity: 'error' as const,
              message: String(err),
              recoveryHint: 'Check the error and try again',
              recoverable: true,
              retryable: false,
              userActionRequired: true,
              createdAt: new Date().toISOString(),
            };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'create', status: 'failed', error, metaOverrides: { redacted: true } }));
      } else {
        prettyError(error.code, error.message, error.recoveryHint);
      }
      process.exitCode = 1;
    }
  });

program
  .command('open <repo-path>')
  .description('Open an existing project')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (path, options) => {
    const { openProject } = await import('../project/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = await openProject(path);

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'open',
            status: 'success',
            data: {
              path: result.path,
              name: result.name,
              branch: result.branch,
              ready: result.ready,
              hasUserChanges: result.hasUserChanges,
              warnings: result.warnings,
            },
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(result.path);
      } else {
        const status = result.ready ? 'opened' : 'opened with issues';
        console.log(`\nProject ${status}: ${result.name}`);
        console.log(`Path: ${result.path}`);
        console.log(`Branch: ${result.branch}`);
        console.log(`Ready: ${result.ready ? 'yes' : 'no'}`);
        console.log(`Uncommitted changes: ${result.hasUserChanges ? 'yes' : 'no'}`);
        if (result.warnings.length > 0) {
          console.log(`\nWarnings:`);
          for (const w of result.warnings) console.log(`  - ${w}`);
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_OPEN_FAILED',
        category: 'project' as const,
        severity: 'error' as const,
        message,
        recoveryHint: 'Check the path and try again',
        recoverable: true,
        retryable: false,
        userActionRequired: true,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'open', status: 'failed', error, metaOverrides: { redacted: true } }));
      } else {
        prettyError(error.code, error.message, error.recoveryHint);
      }
      process.exitCode = 1;
    }
  });

program
  .command('init')
  .description('Initialize Harness OS in an existing project')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (options) => {
    const { initProject } = await import('../project/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = await initProject();
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'init', status: 'success', data: result, metaOverrides: { redacted: true } }),
        );
      } else if (mode === 'quiet') {
        console.log(result.path);
      } else {
        console.log(`\nInit ${result.path}`);
        console.log(`Directories created: ${result.dirsCreated.length}`);
        console.log(`Manifest: ${result.manifestCreated ? 'created' : 'already exists'}`);
        console.log(`AGENTS.md: ${result.agentsMdCreated ? 'created' : 'already exists'}`);
        if (result.agentsMdMissingSections.length > 0) {
          console.log(`Missing AGENTS.md sections: ${result.agentsMdMissingSections.join(', ')}`);
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_INIT_FAILED',
        category: 'project' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: true,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'init', status: 'failed', error, metaOverrides: { redacted: true } }));
      } else {
        prettyError(error.code, error.message, error.recoveryHint);
      }
      process.exitCode = 1;
    }
  });

program
  .command('repair')
  .description('Repair missing or invalid project structure')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (options) => {
    const { repairProject } = await import('../project/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = await repairProject();
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'repair', status: 'success', data: result, metaOverrides: { redacted: true } }),
        );
      } else if (mode === 'quiet') {
        console.log(result.path);
      } else {
        console.log(`\nRepair ${result.path}`);
        console.log(`Directories created: ${result.dirsCreated.length}`);
        console.log(`Manifest: ${result.manifestCreated ? 'created' : result.manifestUpdated ? 'updated' : 'ok'}`);
        if (result.agentsMdMissingSections.length > 0) {
          console.log(`Missing AGENTS.md sections (${result.agentsMdMissingSections.length}):`);
          for (const s of result.agentsMdMissingSections) console.log(`  - ${s}`);
        }
        console.log(`Tech stack: ${result.techStackWritten ? 'refreshed' : 'ok'}`);
        console.log(`Repository map: ${result.repoMapWritten ? 'refreshed' : 'ok'}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_REPAIR_FAILED',
        category: 'project' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: true,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'repair', status: 'failed', error, metaOverrides: { redacted: true } }));
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 1;
    }
  });

program
  .command('check')
  .description('Check AGENTS.md validity')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (options) => {
    const { validateAgentsMd } = await import('../project/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, resetStartTime } = await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    const result = validateAgentsMd(process.cwd());

    if (mode === 'json') {
      jsonOutput(
        buildJsonOutput({ command: 'check', status: 'success', data: result, metaOverrides: { redacted: true } }),
      );
    } else if (mode === 'quiet') {
      console.log(result.isValid ? 'valid' : 'invalid');
    } else {
      console.log(`\nAGENTS.md check: ${result.fileExists ? 'found' : 'missing'}`);
      console.log(`Valid: ${result.isValid ? 'yes' : 'no'}`);

      const present = result.sections.filter((s) => s.present).length;
      const missing = result.sections.filter((s) => !s.present).length;
      console.log(`Sections: ${present} present, ${missing} missing`);

      if (result.missingCore.length > 0) {
        console.log(`\nBLOCKING �?core sections missing:`);
        for (const s of result.missingCore) console.log(`  - ${s}`);
      }
      if (result.missingRequired.length > 0) {
        console.log(`\nWarnings �?non-core sections missing:`);
        for (const s of result.missingRequired) console.log(`  - ${s}`);
      }
    }
  });

// ============================================================
// Status command
// ============================================================

program
  .command('status')
  .description('Show current project status')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (options) => {
    const { getStatus } = await import('../runtime/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, resetStartTime } = await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    const data = await getStatus();

    if (mode === 'json') {
      jsonOutput(buildJsonOutput({ command: 'status', status: 'success', data, metaOverrides: { redacted: true } }));
    } else if (mode === 'quiet') {
      console.log(String(data.activeSessions));
    } else {
      console.log(`\nActive sessions: ${data.activeSessions}`);
      for (const s of data.sessions) {
        console.log(`  ${redactText(s.session_id)} �?turns: ${s.turn_count}`);
      }
    }
  });

// ============================================================
// Task commands
// ============================================================

program
  .command('run <task>')
  .description('Execute a task')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (task, options) => {
    const { runTask } = await import('../task/index.js');
    await runTask(task, { ...program.opts(), ...options });
  });

program
  .command('resume <run-id>')
  .description('[stub] Show run state — actual execution continuation is planned for v1.1+')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (runId, options) => {
    const { resumeRun } = await import('../task/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      await resumeRun(runId);
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'resume', status: 'success', data: { runId }, metaOverrides: { redacted: true } }),
        );
      } else if (mode === 'quiet') {
        console.log(runId);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_RESUME_FAILED',
        category: 'task' as const,
        severity: 'error' as const,
        message,
        recoveryHint: 'Check the run ID and try again',
        recoverable: true,
        retryable: false,
        userActionRequired: true,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'resume', status: 'failed', error, metaOverrides: { redacted: true } }));
      } else {
        prettyError(error.code, error.message, error.recoveryHint);
      }
      process.exitCode = 1;
    }
  });

// ============================================================
// Verification commands
// ============================================================

program
  .command('verify')
  .description('Run verification pipeline (lint, typecheck, test, build)')
  .option('--task <task-id>', 'Task to verify')
  .option('--run <run-id>', 'Run to verify')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (options) => {
    const { runVerificationPipeline } = await import('../verification/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const pipelineResult = await runVerificationPipeline(options);
      const vResult = pipelineResult.result;

      // CLI4-02: Envelope status matches verification result.
      // "passed" => success, otherwise => failed (includes skipped/partial)
      const isSuccess = vResult.status === 'passed';
      const envelopeStatus = isSuccess ? 'success' : 'failed';

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'verify',
            status: envelopeStatus,
            data: {
              status: vResult.status,
              verificationId: pipelineResult.verificationId,
              passed: vResult.passed,
              failed: vResult.failed,
              skipped: vResult.skipped,
              total: vResult.total,
              durationMs: vResult.durationMs,
              reportPaths: pipelineResult.reportPaths,
            },
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(vResult.status);
      } else {
        if (pipelineResult.planText) console.log('\n' + pipelineResult.planText);
        if (pipelineResult.resultsText) console.log('\n' + pipelineResult.resultsText);
        if (vResult.status === 'passed') {
          console.log('\nVerification passed');
        } else {
          console.log(`\nVerification ${vResult.status}`);
        }
      }

      if (!isSuccess) process.exitCode = 70;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_VERIFY_FAILED',
        category: 'verification' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: true,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'verify', status: 'failed', error, metaOverrides: { redacted: true } }));
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 70;
    }
  });

// ============================================================
// Report command
// ============================================================

program
  .command('report <run-id>')
  .description('Show run report')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (runId, options) => {
    const { getReport } = await import('../observability/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const data = await getReport(runId);

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'report',
            status: data.found ? 'success' : 'failed',
            data,
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(data.found ? 'found' : 'not_found');
      } else {
        if (data.trace) {
          console.log(`\nRun: ${runId}`);
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
      if (!data.found) process.exitCode = 1;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_REPORT_FAILED',
        category: 'observability' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: true,
        retryable: false,
        userActionRequired: true,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'report', status: 'failed', error, metaOverrides: { redacted: true } }));
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 1;
    }
  });

// ============================================================
// Delivery command
// ============================================================

program
  .command('deliver')
  .description('Prepare delivery (commit/PR/release/deploy)')
  .option('--commit', 'Create a commit')
  .option('--pr', 'Create a pull request')
  .option('--release', 'Create a release')
  .option('--deploy <env>', 'Deploy to environment')
  .option('--ver-id <ver-id>', 'Verification result ID (required)')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (options) => {
    const { runDelivery } = await import('../delivery/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, resetStartTime } = await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    const result = await runDelivery({ ...options, _outputMode: mode });

    if (mode === 'json') {
      const status = result.status === 'ready' ? 'success' : 'failed';
      jsonOutput(
        buildJsonOutput({
          command: 'deliver',
          status,
          data: {
            deliveryId: result.deliveryId,
            type: result.type,
            status: result.status,
            commitMessage: result.commitMessage?.full,
            prBody: result.prBody?.body,
            reportPath: result.reportPath,
            blockedBy: result.guardResult.blockedBy,
          },
          metaOverrides: { redacted: true },
        }),
      );
    } else if (mode === 'quiet') {
      console.log(result.status);
    }

    if (result.status !== 'ready') process.exitCode = 1;
  });

// ============================================================
// Decision commands
// ============================================================

const decision = program.command('decision').description('Manage architecture decisions');

decision
  .command('list')
  .description('List decisions')
  .option('-a, --active', 'Only show active (accepted) decisions')
  .option('-j, --json', 'JSON output')
  .action(async (options) => {
    const { listDecisions, listActiveDecisions } = await import('../decision/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyTable } = await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });

    const decisions = options.active ? listActiveDecisions(process.cwd()) : listDecisions(process.cwd());

    if (mode === 'json') {
      jsonOutput(
        buildJsonOutput({
          command: 'decision list',
          status: 'success',
          data: { count: decisions.length, decisions },
          metaOverrides: { redacted: true },
        }),
      );
    } else {
      if (decisions.length === 0) {
        console.log('No decisions found.');
        return;
      }
      console.log(`\nDecisions (${decisions.length}):\n`);
      prettyTable(
        ['ID', 'Title', 'Status', 'Type'],
        decisions.map((d) => [d.id, d.title.slice(0, 40), d.status, d.type]),
      );
    }
  });

decision
  .command('propose')
  .description('Propose a new decision (ADR)')
  .requiredOption('-t, --title <title>', 'Decision title')
  .requiredOption('--type <type>', 'Type: architecture|product|technology|security|delivery|governance|process')
  .requiredOption('-s, --summary <summary>', 'Decision summary')
  .requiredOption('-c, --context <context>', 'Why this decision is needed')
  .requiredOption('-d, --decision <decision>', 'What decision is being made')
  .option('--consequences <items>', 'Comma-separated consequences')
  .option('--risks <items>', 'Comma-separated risks')
  .option('--supersedes <adr-id>', 'ADR ID this supersedes')
  .action(async (options) => {
    const { proposeDecision } = await import('../decision/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettySuccess, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = proposeDecision({
        projectPath: process.cwd(),
        title: options.title,
        type: options.type,
        summary: options.summary,
        context: options.context,
        decision: options.decision,
        consequences: options.consequences?.split(',').map((s: string) => s.trim()) ?? [],
        risks: options.risks?.split(',').map((s: string) => s.trim()) ?? [],
        supersedes: options.supersedes,
      });

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'decision propose',
            status: 'success',
            data: result,
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(result.id);
      } else {
        prettySuccess('ADR proposed', {
          ID: result.id,
          Title: result.title,
          Status: result.status,
          Type: result.type,
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_PROPOSE_FAILED',
        category: 'decision' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: true,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'decision propose', status: 'failed', error, metaOverrides: { redacted: true } }),
        );
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 1;
    }
  });

decision
  .command('accept <decision-id>')
  .description('Accept a proposed decision (requires a pre-approved approval)')
  .requiredOption('-a, --approval-id <id>', 'Approval ID from a previously resolved approval')
  .option('-b, --by <name>', 'Who approved this decision (audit metadata only, not authorization)')
  .action(async (id, options) => {
    const { acceptDecision } = await import('../decision/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      // P0-003: Consume and validate an externally-approved approval
      // The approval must be created via `approval create-adr` and resolved beforehand.
      // acceptDecision() internally calls consumeApproval() for single-use enforcement,
      // and validateApprovalBinding() to verify tool/project/input match.
      const result = acceptDecision(process.cwd(), id, options.approvalId, options.by);
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'decision accept',
            status: result ? 'success' : 'failed',
            data: result ? { id: result.id, title: result.title, status: result.status } : undefined,
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(result ? result.id : 'not_found');
      } else {
        if (result) {
          console.log(`\nAccepted: ${result.id} — ${result.title}`);
        } else {
          console.error(`Decision not found or not in proposed state: ${id}`);
        }
      }
      if (!result) process.exitCode = 1;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_ACCEPT_FAILED',
        category: 'decision' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: false,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'decision accept', status: 'failed', error, metaOverrides: { redacted: true } }),
        );
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 1;
    }
  });

decision
  .command('reject <decision-id>')
  .description('Reject a proposed decision')
  .action(async (id, options) => {
    const { rejectDecision } = await import('../decision/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = rejectDecision(process.cwd(), id);
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'decision reject',
            status: result ? 'success' : 'failed',
            data: result ? { id: result.id, title: result.title, status: result.status } : undefined,
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(result ? result.id : 'not_found');
      } else {
        if (result) {
          console.log(`\nRejected: ${result.id} — ${result.title}`);
        } else {
          console.error(`Decision not found or not in proposed state: ${id}`);
        }
      }
      if (!result) process.exitCode = 1;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_REJECT_FAILED',
        category: 'decision' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: false,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'decision reject', status: 'failed', error, metaOverrides: { redacted: true } }),
        );
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 1;
    }
  });

decision
  .command('supersede <decision-id>')
  .description('Supersede an accepted ADR (requires a pre-approved approval)')
  .requiredOption('-a, --approval-id <id>', 'Approval ID from a previously resolved approval')
  .requiredOption('-b, --by <adr-id>', 'New ADR ID that supersedes this one')
  .action(async (id, options) => {
    const { supersedeDecision } = await import('../decision/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      // P0-003: Consume and validate an externally-approved approval
      const result = supersedeDecision(process.cwd(), id, options.by, options.approvalId);
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'decision supersede',
            status: result ? 'success' : 'failed',
            data: result ? { id: result.id, supersededBy: result.supersededBy } : undefined,
            metaOverrides: { redacted: true },
          }),
        );
      } else if (mode === 'quiet') {
        console.log(result ? result.id : 'not_found');
      } else {
        if (result) {
          console.log(`\nSuperseded: ${result.id} → ${result.supersededBy}`);
        } else {
          console.error(`Decision not found: ${id}`);
        }
      }
      if (!result) process.exitCode = 1;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_SUPERSEDE_FAILED',
        category: 'decision' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: false,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'decision supersede',
            status: 'failed',
            error,
            metaOverrides: { redacted: true },
          }),
        );
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 1;
    }
  });

// ============================================================
// Approval commands (P0-003: ADR approval binding)
// ============================================================

const approval = program.command('approval').description('Manage approvals for ADR state transitions');

approval
  .command('create-adr')
  .description('Create an approval request for an ADR state transition')
  .requiredOption('--adr <id>', 'ADR ID')
  .requiredOption('--action <action>', 'Action: accept|supersede')
  .option('--project-id <id>', 'Project ID (default: from manifest)')
  .action(async (options) => {
    const { submitApproval } = await import('../governance/approval-gate.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      let projectId = options.projectId;
      if (!projectId) {
        try {
          const { readFileSync, existsSync } = await import('fs');
          const { resolve } = await import('path');
          const manifestPath = resolve(process.cwd(), '.project/state/manifest.json');
          if (existsSync(manifestPath)) {
            const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
            projectId = manifest.projectId;
          }
        } catch {
          /* empty — optional manifest field */
        }
      }

      const approvalId = `aprv_${Date.now().toString(36)}`;
      const approval = submitApproval({
        id: approvalId,
        action: `${options.action}_adr`,
        reason: `ADR ${options.adr}: ${options.action === 'accept' ? 'Accept decision' : 'Supersede decision'}`,
        riskLevel: 'medium',
        projectId: projectId || 'unknown',
        toolName: 'decision',
        input: { action: `${options.action}_adr`, adrId: options.adr },
      });

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'approval create-adr',
            status: 'success',
            data: approval,
            metaOverrides: { redacted: true },
          }),
        );
      } else {
        console.log(`\nApproval created: ${approvalId}`);
        console.log(`Action: ${approval.action}`);
        console.log(`Status: ${approval.status}`);
        console.log(`Expires: ${approval.expiresAt}`);
        console.log(`\nUse: approval resolve ${approvalId} --approve --by <name>`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      prettyError('ERR_APPROVAL_FAILED', `Approval creation failed: ${message}`);
      process.exitCode = 1;
    }
  });

approval
  .command('resolve <approval-id>')
  .description('Resolve an approval (approve or reject)')
  .option('--approve', 'Approve the request (mutually exclusive with --reject)')
  .option('--reject', 'Reject the request (mutually exclusive with --approve)')
  .option('--reason <text>', 'Reason for rejection (required if --reject)')
  .option('--by <name>', 'Operator name (audit metadata)')
  .action(async (id, options) => {
    const { resolveApproval } = await import('../governance/approval-gate.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      // Validate mutually exclusive flags
      if (!options.approve && !options.reject) {
        throw new Error('Must specify either --approve or --reject');
      }
      if (options.approve && options.reject) {
        throw new Error('Cannot specify both --approve and --reject');
      }
      if (options.reject && !options.reason) {
        throw new Error('--reason is required when rejecting');
      }

      const result = resolveApproval(id, {
        approved: !!options.approve,
        resolvedBy: options.by,
        rejectionReason: options.reason,
      });

      if (!result) {
        throw new Error(`Approval not found: ${id}`);
      }

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'approval resolve',
            status: 'success',
            data: {
              id: result.id,
              status: result.status,
              resolvedBy: result.resolvedBy,
              resolvedAt: result.resolvedAt,
            },
            metaOverrides: { redacted: true },
          }),
        );
      } else {
        console.log(`\nApproval ${id}: ${result.status}`);
        if (result.resolvedBy) console.log(`Resolved by: ${result.resolvedBy}`);
        if (result.status === 'rejected' && options.reason) {
          console.log(`Reason: ${options.reason}`);
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({
            command: 'approval resolve',
            status: 'failed',
            error: {
              code: 'ERR_APPROVAL_RESOLVE',
              category: 'approval',
              severity: 'error' as const,
              message,
              recoveryHint: null as string | null,
              recoverable: false,
              retryable: true,
              userActionRequired: false,
              createdAt: new Date().toISOString(),
            },
            metaOverrides: { redacted: true },
          }),
        );
      } else {
        prettyError('ERR_APPROVAL_RESOLVE', message);
      }
      process.exitCode = 1;
    }
  });

// ============================================================
// Skills commands
// ============================================================

program
  .command('skills')
  .description('Manage skills')
  .addCommand(
    new Command('list')
      .description('List available skills')
      .option('-j, --json', 'JSON output')
      .action(async (options) => {
        const { getSkillsList } = await import('../skills/index.js');
        const { detectOutputMode, buildJsonOutput, jsonOutput } = await import('./formatter.js');
        const mode = detectOutputMode({ ...program.opts(), ...options });

        const data = await getSkillsList();

        if (mode === 'json') {
          jsonOutput(
            buildJsonOutput({
              command: 'skills list',
              status: 'success',
              data,
              metaOverrides: { redacted: true },
            }),
          );
        } else {
          console.log(`\nRegistered skills: ${data.count}\n`);
          for (const skill of data.skills) {
            const tools = skill.tools.join(', ');
            console.log(`  ${skill.name} (${skill.category})`);
            console.log(`    ${skill.description}`);
            console.log(`    Risk: ${skill.riskLevel} | Enabled: ${skill.defaultEnabled} | Tools: ${tools}`);
            console.log();
          }
        }
      }),
  );

// ============================================================
// Checkpoint commands
// ============================================================

program
  .command('checkpoint')
  .description('Create a checkpoint capturing git and task state')
  .option('--task <task-id>', 'Task ID')
  .option('--run <run-id>', 'Run ID')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (options) => {
    const { createCheckpoint } = await import('../state/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const cp = await createCheckpoint({ taskId: options.task, runId: options.run });

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'checkpoint', status: 'success', data: cp, metaOverrides: { redacted: true } }),
        );
      } else if (mode === 'quiet') {
        console.log(cp.id);
      } else {
        console.log(`\nCheckpoint created: ${cp.id}`);
        console.log(`Branch: ${cp.currentBranch}`);
        console.log(`Changed files: ${cp.changedFiles.length}`);
        console.log(`Created: ${cp.createdAt}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_CHECKPOINT_FAILED',
        category: 'state' as const,
        severity: 'error' as const,
        message,
        recoveryHint: null as string | null,
        recoverable: true,
        retryable: true,
        userActionRequired: false,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'checkpoint', status: 'failed', error, metaOverrides: { redacted: true } }),
        );
      } else {
        prettyError(error.code, error.message);
      }
      process.exitCode = 1;
    }
  });

program
  .command('rollback <checkpoint-id>')
  .description('Show checkpoint rollback information (requires separate approval)')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (id, options) => {
    const { rollbackToCheckpoint } = await import('../state/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettyError, resetStartTime } =
      await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = await rollbackToCheckpoint(id);

      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'rollback', status: 'success', data: result, metaOverrides: { redacted: true } }),
        );
      } else if (mode === 'quiet') {
        console.log(result.success ? 'rollback_possible' : 'rollback_blocked');
      } else {
        console.log(`\nRollback analysis for: ${result.checkpointId}`);
        console.log(`Current branch: ${result.branch}`);
        console.log(`Can rollback: ${result.success ? 'yes' : 'no'}`);
        if (result.warnings.length > 0) {
          console.log(`\nWarnings:`);
          for (const w of result.warnings) console.log(`  - ${w}`);
        }
        console.log(`\nNote: git reset requires explicit human approval.`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      const error = {
        code: 'ERR_ROLLBACK_FAILED',
        category: 'state' as const,
        severity: 'error' as const,
        message,
        recoveryHint: 'Check the checkpoint ID and try again',
        recoverable: true,
        retryable: false,
        userActionRequired: true,
        createdAt: new Date().toISOString(),
      };
      if (mode === 'json') {
        jsonOutput(
          buildJsonOutput({ command: 'rollback', status: 'failed', error, metaOverrides: { redacted: true } }),
        );
      } else {
        prettyError(error.code, error.message, error.recoveryHint);
      }
      process.exitCode = 1;
    }
  });

// ============================================================
// Config command
// ============================================================

program
  .command('config')
  .description('Show Harness OS configuration')
  .option('--show-source', 'Show config source for each value')
  .action(async (options) => {
    const { loadConfig } = await import('../config/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettySuccess, prettyTable } =
      await import('./formatter.js');
    const mergedOpts = { ...program.opts(), ...options };
    const mode = detectOutputMode(mergedOpts);

    const loaded = loadConfig(process.cwd());

    if (mode === 'json') {
      jsonOutput(
        buildJsonOutput({
          command: 'config',
          status: 'success',
          data: {
            config: loaded.config,
            sources: loaded.sources.map((s) => ({ path: s.path, scope: s.scope, valid: s.valid })),
            warnings: loaded.warnings,
          },
          metaOverrides: { redacted: true },
        }),
      );
    } else {
      prettySuccess('Harness OS Configuration', {
        Version: loaded.config.version,
        'Output mode': loaded.config.cli?.defaultOutputMode ?? 'pretty',
        'Secret redaction': loaded.config.governance?.redactSecrets ? 'enabled' : 'disabled',
        'Deploy approval': loaded.config.governance?.requireApprovalForDeploy ? 'required' : 'not required',
        'Push main approval': loaded.config.governance?.requireApprovalForPushMain ? 'required' : 'not required',
        'Auto commit': loaded.config.project?.allowAutoCommit ? 'allowed' : 'not allowed',
      });

      if (options.showSource) {
        console.log('\nConfig sources:');
        prettyTable(
          ['Scope', 'Path', 'Valid'],
          loaded.sources.map((s) => [s.scope, s.path, s.valid ? 'yes' : 'no']),
        );
      }

      if (loaded.warnings.length > 0) {
        console.log('\nWarnings:');
        for (const w of loaded.warnings) console.log(`  - ${w}`);
      }
    }
  });

// ============================================================
// Parse
// ============================================================

program.parse();
