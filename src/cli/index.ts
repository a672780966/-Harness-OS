#!/usr/bin/env node
/**
 * Harness OS CLI Entry Point
 *
 * Codex-first Project Operating System
 * Version 1.0.0
 */

import { Command } from 'commander';

const program = new Command();

program
  .name('harness')
  .description('Harness OS - Codex-first Project Operating System')
  .version('1.0.0');

// Project commands
program
  .command('create <project-name>')
  .description('Create a new Harness OS project')
  .option('-p, --path <path>', 'Custom project path')
  .option('-j, --json', 'JSON output mode')
  .option('-q, --quiet', 'Quiet output mode')
  .option('-t, --type <type>', 'Project type (web-app, backend-service, cli, library, agent-harness)')
  .action(async (name, options) => {
    const { createProject } = await import('../project/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettySuccess, prettyError, resetStartTime } = await import('./formatter.js');
    const mode = detectOutputMode({ ...program.opts(), ...options });
    resetStartTime();

    try {
      const result = await createProject({ name, path: options.path, projectType: options.type });

      if (mode === 'json') {
        jsonOutput(buildJsonOutput({
          command: 'create', status: 'success',
          data: { projectId: result.projectId, name: result.name, path: result.path, agentsMdCreated: result.agentsMdCreated, manifestPath: result.manifestPath, checkpointId: result.checkpointId },
        }));
      } else if (mode === 'quiet') {
        console.log(result.path);
      } else {
        prettySuccess('Project created', {
          Name: result.name, Path: result.path,
          'AGENTS.md': result.agentsMdCreated ? 'created' : 'already exists',
          Manifest: result.manifestPath,
          Checkpoint: result.checkpointId,
        }, [`cd ${result.path}`, 'harness run "your task"']);
      }
    } catch (err) {
      const { createProjectNotFoundError } = await import('../errors/index.js');
      const error = err instanceof Error
        ? createProjectNotFoundError(err.message)
        : { code: 'ERR_INTERNAL', category: 'project', severity: 'error' as const, message: String(err), recoveryHint: 'Check the error and try again', recoverable: true, retryable: false, userActionRequired: true, createdAt: new Date().toISOString() };
      if (mode === 'json') {
        jsonOutput(buildJsonOutput({ command: 'create', status: 'failed', error }));
      } else {
        prettyError(error.code, error.message, error.recoveryHint);
      }
      process.exit(1);
    }
  });

program
  .command('open <repo-path>')
  .description('Open an existing project')
  .action(async (path) => {
    const { openProject } = await import('../project/index.js');
    const result = await openProject(path);
    if (!result.ready) {
      console.log(`\nProject opened with issues:`);
    } else {
      console.log(`\nProject opened: ${result.name}`);
    }
    console.log(`Path: ${result.path}`);
    console.log(`Branch: ${result.branch}`);
    console.log(`Ready: ${result.ready ? 'yes' : 'no'}`);
    console.log(`Uncommitted changes: ${result.hasUserChanges ? 'yes' : 'no'}`);
    if (result.warnings.length > 0) {
      console.log(`\nWarnings:`);
      for (const w of result.warnings) console.log(`  - ${w}`);
    }
  });

program
  .command('init')
  .description('Initialize Harness OS in an existing project')
  .action(async () => {
    const { initProject } = await import('../project/index.js');
    const result = await initProject();
    console.log(`\nInit ${result.path}`);
    console.log(`Directories created: ${result.dirsCreated.length}`);
    console.log(`Manifest: ${result.manifestCreated ? 'created' : 'already exists'}`);
    console.log(`AGENTS.md: ${result.agentsMdCreated ? 'created' : 'already exists'}`);
    if (result.agentsMdMissingSections.length > 0) {
      console.log(`Missing AGENTS.md sections: ${result.agentsMdMissingSections.join(', ')}`);
    }
  });

program
  .command('repair')
  .description('Repair missing or invalid project structure')
  .action(async () => {
    const { repairProject } = await import('../project/index.js');
    const result = await repairProject();
    console.log(`\nRepair ${result.path}`);
    console.log(`Directories created: ${result.dirsCreated.length}`);
    console.log(`Manifest: ${result.manifestCreated ? 'created' : result.manifestUpdated ? 'updated' : 'ok'}`);
    if (result.agentsMdMissingSections.length > 0) {
      console.log(`Missing AGENTS.md sections (${result.agentsMdMissingSections.length}):`);
      for (const s of result.agentsMdMissingSections) console.log(`  - ${s}`);
    }
    console.log(`Tech stack: ${result.techStackWritten ? 'refreshed' : 'ok'}`);
    console.log(`Repository map: ${result.repoMapWritten ? 'refreshed' : 'ok'}`);
  });

program
  .command('check')
  .description('Check AGENTS.md validity')
  .action(async () => {
    const { validateAgentsMd } = await import('../project/index.js');
    const result = validateAgentsMd(process.cwd());
    console.log(`\nAGENTS.md check: ${result.fileExists ? 'found' : 'missing'}`);
    console.log(`Valid: ${result.isValid ? 'yes' : 'no'}`);

    const present = result.sections.filter(s => s.present).length;
    const missing = result.sections.filter(s => !s.present).length;
    console.log(`Sections: ${present} present, ${missing} missing`);

    if (result.missingCore.length > 0) {
      console.log(`\nBLOCKING — core sections missing:`);
      for (const s of result.missingCore) console.log(`  - ${s}`);
    }
    if (result.missingRequired.length > 0) {
      console.log(`\nWarnings — non-core sections missing:`);
      for (const s of result.missingRequired) console.log(`  - ${s}`);
    }
  });

// Task commands
program
  .command('run <task>')
  .description('Execute a task')
  .option('-j, --json', 'JSON output mode')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (task, options) => {
    const { runTask } = await import('../task/index.js');
    await runTask(task, { ...program.opts(), ...options });
  });

program
  .command('resume <run-id>')
  .description('Resume a paused or interrupted run')
  .action(async (runId) => {
    const { resumeRun } = await import('../task/index.js');
    await resumeRun(runId);
  });

program
  .command('status')
  .description('Show current project status')
  .action(async () => {
    const { showStatus } = await import('../runtime/index.js');
    await showStatus();
  });

// Verification commands
program
  .command('verify')
  .description('Run verification pipeline (lint → typecheck → test → build)')
  .option('--task <task-id>', 'Task to verify')
  .option('--run <run-id>', 'Run to verify')
  .action(async (options) => {
    const { runVerificationPipeline } = await import('../verification/index.js');
    const result = await runVerificationPipeline(options);
    if (result.status === 'passed') {
      console.log('\n✅ Verification passed');
    } else {
      console.log(`\n❌ Verification ${result.status}`);
      process.exit(70); // verification error exit code
    }
  });

// Report commands
program
  .command('report <run-id>')
  .description('Show run report')
  .action(async (runId) => {
    const { showReport } = await import('../observability/index.js');
    await showReport(runId);
  });

// Delivery commands
program
  .command('deliver')
  .description('Prepare delivery (commit/PR/release/deploy)')
  .option('--commit', 'Create a commit')
  .option('--pr', 'Create a pull request')
  .option('--release', 'Create a release')
  .option('--deploy <env>', 'Deploy to environment')
  .action(async (options) => {
    const { runDelivery } = await import('../delivery/index.js');
    await runDelivery(options);
  });

// Decision commands
program
  .command('decision')
  .description('Manage architecture decisions')
  .addCommand(
    new Command('list')
      .description('List decisions')
      .option('-a, --active', 'Only show active (accepted) decisions')
      .option('-j, --json', 'JSON output')
      .action(async (options) => {
        const { listDecisions, listActiveDecisions } = await import('../decision/index.js');
        const { detectOutputMode, buildJsonOutput, jsonOutput, prettyTable } = await import('./formatter.js');
        const mode = detectOutputMode({ ...program.opts(), ...options });

        const decisions = options.active
          ? listActiveDecisions(process.cwd())
          : listDecisions(process.cwd());

        if (mode === 'json') {
          jsonOutput(buildJsonOutput({
            command: 'decision list', status: 'success',
            data: { count: decisions.length, decisions },
          }));
        } else {
          if (decisions.length === 0) {
            console.log('No decisions found.');
            return;
          }
          console.log(`\nDecisions (${decisions.length}):\n`);
          prettyTable(
            ['ID', 'Title', 'Status', 'Type'],
            decisions.map(d => [d.id, d.title.slice(0, 40), d.status, d.type]),
          );
        }
      })
  )
  .addCommand(
    new Command('propose')
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
        const { prettySuccess } = await import('./formatter.js');

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

        prettySuccess('ADR proposed', {
          ID: result.id,
          Title: result.title,
          Status: result.status,
          Type: result.type,
        });
      })
  )
  .addCommand(
    new Command('accept <decision-id>')
      .description('Accept a proposed decision')
      .option('-b, --by <name>', 'Who approved this decision')
      .action(async (id, options) => {
        const { acceptDecision } = await import('../decision/index.js');
        const result = acceptDecision(process.cwd(), id, options.by);
        if (result) {
          console.log(`\nAccepted: ${result.id} — ${result.title}`);
        } else {
          console.error(`Decision not found or not in proposed state: ${id}`);
        }
      })
  )
  .addCommand(
    new Command('reject <decision-id>')
      .description('Reject a proposed decision')
      .action(async (id) => {
        const { rejectDecision } = await import('../decision/index.js');
        const result = rejectDecision(process.cwd(), id);
        if (result) {
          console.log(`\nRejected: ${result.id} — ${result.title}`);
        } else {
          console.error(`Decision not found or not in proposed state: ${id}`);
        }
      })
  )
  .addCommand(
    new Command('supersede <decision-id>')
      .description('Supersede an accepted ADR')
      .requiredOption('-b, --by <adr-id>', 'New ADR ID that supersedes this one')
      .action(async (id, options) => {
        const { supersedeDecision } = await import('../decision/index.js');
        const result = supersedeDecision(process.cwd(), id, options.by);
        if (result) {
          console.log(`\nSuperseded: ${result.id} → ${result.supersededBy}`);
        } else {
          console.error(`Decision not found: ${id}`);
        }
      })
  );

// Skills commands
program
  .command('skills')
  .description('Manage skills')
  .addCommand(
    new Command('list')
      .description('List available skills')
      .action(async () => {
        const { listSkills } = await import('../skills/index.js');
        await listSkills();
      })
  );

// Checkpoint commands
program
  .command('checkpoint')
  .description('Create a checkpoint capturing git and task state')
  .option('--task <task-id>', 'Task ID')
  .option('--run <run-id>', 'Run ID')
  .action(async (options) => {
    const { createCheckpoint } = await import('../state/index.js');
    const cp = await createCheckpoint({
      taskId: options.task,
      runId: options.run,
    });
    console.log(`\nCheckpoint created: ${cp.id}`);
    console.log(`Branch: ${cp.currentBranch}`);
    console.log(`Changed files: ${cp.changedFiles.length}`);
    console.log(`Created: ${cp.createdAt}`);
  });

program
  .command('rollback <checkpoint-id>')
  .description('Show checkpoint rollback information (requires separate approval)')
  .action(async (id) => {
    const { rollbackToCheckpoint } = await import('../state/index.js');
    const result = await rollbackToCheckpoint(id);
    console.log(`\nRollback analysis for: ${result.checkpointId}`);
    console.log(`Current branch: ${result.branch}`);
    console.log(`Can rollback: ${result.success ? 'yes' : 'no'}`);
    if (result.warnings.length > 0) {
      console.log(`\nWarnings:`);
      for (const w of result.warnings) console.log(`  - ${w}`);
    }
    console.log(`\nNote: git reset requires explicit human approval.`);
  });

// Config command
program
  .command('config')
  .description('Show Harness OS configuration')
  .option('--json', 'JSON output')
  .option('--show-source', 'Show config source for each value')
  .action(async (options) => {
    const { loadConfig } = await import('../config/index.js');
    const { detectOutputMode, buildJsonOutput, jsonOutput, prettySuccess, prettyTable } = await import('./formatter.js');
    // Merge global opts + command opts
    const mergedOpts = { ...program.opts(), ...options };
    const mode = detectOutputMode(mergedOpts);

    const loaded = loadConfig(process.cwd());

    if (mode === 'json') {
      jsonOutput(buildJsonOutput({
        command: 'config', status: 'success',
        data: {
          config: loaded.config,
          sources: loaded.sources.map(s => ({ path: s.path, scope: s.scope, valid: s.valid })),
          warnings: loaded.warnings,
        },
      }));
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
          loaded.sources.map(s => [s.scope, s.path, s.valid ? 'yes' : 'no']),
        );
      }

      if (loaded.warnings.length > 0) {
        console.log('\nWarnings:');
        for (const w of loaded.warnings) console.log(`  - ${w}`);
      }
    }
  });

// Global options
program
  .option('--json', 'JSON output mode')
  .option('--quiet', 'Quiet output mode')
  .option('--no-color', 'Disable color output')
  .option('--log-level <level>', 'Log level (debug|info|warn|error)');

program.parse();
