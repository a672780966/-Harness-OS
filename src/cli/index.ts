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
  .option('-t, --type <type>', 'Project type (web-app, backend-service, cli, library, agent-harness)')
  .action(async (name, options) => {
    const { createProject } = await import('../project/index.js');
    try {
      const result = await createProject({
        name,
        path: options.path,
        projectType: options.type,
      });
      console.log(`\nProject created: ${result.name}`);
      console.log(`Path: ${result.path}`);
      console.log(`AGENTS.md: ${result.agentsMdCreated ? 'created' : 'already exists'}`);
      console.log(`Manifest: ${result.manifestPath}`);
      console.log(`Checkpoint: ${result.checkpointId}`);
      console.log(`\nNext:`);
      console.log(`  cd ${result.path}`);
      console.log(`  harness run "your task"`);
    } catch (err) {
      console.error(`Error creating project: ${(err as Error).message}`);
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
