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
  .action(async (name) => {
    const { createProject } = await import('../project/index.js');
    await createProject(name);
  });

program
  .command('open <repo-path>')
  .description('Open an existing project')
  .action(async (path) => {
    const { openProject } = await import('../project/index.js');
    await openProject(path);
  });

program
  .command('init')
  .description('Initialize Harness OS in an existing project')
  .action(async () => {
    const { initProject } = await import('../project/index.js');
    await initProject();
  });

program
  .command('repair')
  .description('Repair missing or invalid project structure')
  .action(async () => {
    const { repairProject } = await import('../project/index.js');
    await repairProject();
  });

// Task commands
program
  .command('run <task>')
  .description('Execute a task')
  .option('-j, --json', 'JSON output mode')
  .option('-q, --quiet', 'Quiet output mode')
  .action(async (task, options) => {
    const { runTask } = await import('../task/index.js');
    await runTask(task, options);
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
  .description('Run verification pipeline')
  .option('--task <task-id>', 'Task to verify')
  .option('--run <run-id>', 'Run to verify')
  .action(async (options) => {
    const { runVerification } = await import('../verification/index.js');
    await runVerification(options);
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
      .action(async () => {
        const { listDecisions } = await import('../decision/index.js');
        await listDecisions();
      })
  )
  .addCommand(
    new Command('propose')
      .description('Propose a new decision')
      .action(async () => {
        const { proposeDecision } = await import('../decision/index.js');
        await proposeDecision();
      })
  )
  .addCommand(
    new Command('accept <decision-id>')
      .description('Accept a proposed decision')
      .action(async (id) => {
        const { acceptDecision } = await import('../decision/index.js');
        await acceptDecision(id);
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
  .description('Create or manage checkpoints')
  .action(async () => {
    const { createCheckpoint } = await import('../state/index.js');
    await createCheckpoint();
  });

program
  .command('rollback <checkpoint-id>')
  .description('Rollback to a checkpoint')
  .action(async (id) => {
    const { rollbackTo } = await import('../state/index.js');
    await rollbackTo(id);
  });

// Config command
program
  .command('config')
  .description('Show Harness OS configuration')
  .option('--json', 'JSON output')
  .action(async (options) => {
    const { showConfig } = await import('../runtime/index.js');
    await showConfig(options);
  });

// Global options
program
  .option('--json', 'JSON output mode')
  .option('--quiet', 'Quiet output mode')
  .option('--no-color', 'Disable color output')
  .option('--log-level <level>', 'Log level (debug|info|warn|error)');

program.parse();
