/**
 * Harness OS — Thin Harness E2E Integration Tests
 *
 * Validates end-to-end scenarios covering the full Thin Harness lifecycle:
 *   1. Create project → verify structure
 *   2. Open project → verify readiness
 *   3. Run task → create + context + verification
 *   4. Policy engine blocks high-risk commands
 *   5. Delivery guard blocks without verification
 *   6. Secret redaction works on all outputs
 *   7. Checkpoint creation and rollback analysis
 *
 * Reference: 11_ACCEPTANCE_CRITERIA.md §18
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { simpleGit } from 'simple-git';

// Project Manager
import { createProject } from '../../src/project/create.js';
import { openProject } from '../../src/project/open.js';
import { validateAgentsMd } from '../../src/project/agents-validator.js';

// Task Manager
import { createTaskRecord, normalizeTitle, inferTaskType } from '../../src/task/create.js';
import { transitionStatus, isValidTransition } from '../../src/task/state-machine.js';
import { completeTask } from '../../src/task/complete.js';

// Context Engineering
import { buildContextPack } from '../../src/context/build.js';

// Governance
import { checkPolicy, classifyRisk } from '../../src/governance/policy.js';
import { submitApproval, resolveApproval } from '../../src/governance/approval-gate.js';
import { redactText, isProtectedFile } from '../../src/governance/redactor.js';

// Verification
import { detectCommands } from '../../src/verification/commands.js';
import { buildPlan } from '../../src/verification/plan.js';
import { generateReport, saveReport } from '../../src/verification/report.js';
import {
  loadVerificationResult,
  computeIntegrity,
  saveVerificationResult,
} from '../../src/verification/result.js';

// Delivery
import { runGuard } from '../../src/delivery/guard.js';
import { generateCommitMessage } from '../../src/delivery/commit.js';
import { generatePrBody } from '../../src/delivery/pr.js';
import { generateDeliveryReport, saveDeliveryReport } from '../../src/delivery/report.js';

// Observability
import { logEvent, EventTypes } from '../../src/observability/events.js';
import { createTrace, saveTrace, updateTraceStatus } from '../../src/observability/trace.js';
import { generateRunReport, saveRunReport } from '../../src/observability/report.js';

// Skills
import registry from '../../src/skills/registry.js';

// Checkpoint
import { createCheckpoint } from '../../src/state/checkpoint.js';

let testDir: string;
let projectPath: string;

beforeEach(async () => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-e2e-'));
  projectPath = join(testDir, 'e2e-project');
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// E2E Scenario 1: Create Project
// ============================================================

describe('E2E: Create Project', () => {
  it('harness create: creates complete project structure', async () => {
    const result = await createProject({ name: 'e2e-project', path: projectPath });

    // 1. Directory exists
    expect(existsSync(projectPath)).toBe(true);

    // 2. Git repo initialized
    const git = simpleGit(projectPath);
    expect(await git.checkIsRepo()).toBe(true);

    // 3. AGENTS.md created
    expect(existsSync(join(projectPath, 'AGENTS.md'))).toBe(true);
    const agentsMd = readFileSync(join(projectPath, 'AGENTS.md'), 'utf-8');
    expect(agentsMd).toContain('Project Identity');
    expect(agentsMd).toContain('Permission and Approval Rules');

    // 4. .project/ structure created
    const dirs = ['.project/state', '.project/tasks/active', '.project/tasks/completed',
      '.project/tasks/failed', '.project/decisions', '.project/reports/runs',
      '.project/reports/verification', '.project/reports/delivery', '.project/checkpoints',
      '.project/sessions', '.project/context'];
    for (const dir of dirs) {
      expect(existsSync(join(projectPath, dir))).toBe(true);
    }

    // 5. Manifest valid
    const manifest = JSON.parse(readFileSync(join(projectPath, '.project/state/manifest.json'), 'utf-8'));
    expect(manifest.projectId).toMatch(/^proj_/);
    expect(manifest.skills.enabled).toContain('filesystem');

    // 6. Checkpoint created
    const checkpoints = readdirSync(join(projectPath, '.project/checkpoints'));
    expect(checkpoints.length).toBeGreaterThan(0);
  });

  it('harness create: AGENTS.md passes validation', async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
    const validation = validateAgentsMd(projectPath);
    expect(validation.isValid).toBe(true);
    expect(validation.missingCore).toEqual([]);
  });

  it('harness create: tech-stack.md and repository-map.md exist', async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
    expect(existsSync(join(projectPath, '.project/state/tech-stack.md'))).toBe(true);
    expect(existsSync(join(projectPath, '.project/state/repository-map.md'))).toBe(true);
  });
});

// ============================================================
// E2E Scenario 2: Open Project
// ============================================================

describe('E2E: Open Project', () => {
  it('harness open: validates an existing project', async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
    const result = await openProject(projectPath);
    expect(result.ready).toBe(true);
    expect(result.hasAgentsMd).toBe(true);
    expect(result.hasManifest).toBe(true);
    expect(result.projectDirsOk).toBe(true);
  });

  it('harness open: reports missing AGENTS.md', async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
    rmSync(join(projectPath, 'AGENTS.md'), { force: true });
    const result = await openProject(projectPath);
    expect(result.ready).toBe(false);
    expect(result.warnings.some(w => w.includes('AGENTS.md'))).toBe(true);
  });

  it('harness open: reports uncommitted changes', async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
    writeFileSync(join(projectPath, 'dirty.txt'), 'change', 'utf-8');
    const result = await openProject(projectPath);
    expect(result.hasUserChanges).toBe(true);
  });
});

// ============================================================
// E2E Scenario 3: Run Task — Create + State Machine + Complete
// ============================================================

describe('E2E: Task Execution Flow', () => {
  beforeEach(async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
  });

  it('harness run: creates task record with normalized inputs', async () => {
    const record = await createTaskRecord({
      projectPath,
      userInstruction: 'Fix the login button loading state. It should show a spinner.',
    });
    expect(record.state.taskId).toMatch(/^task_/);
    expect(record.state.title).toBe('Fix the login button loading state');
    expect(record.state.type).toBe('bugfix');
    expect(record.state.status).toBe('created');
    expect(existsSync(record.mdPath)).toBe(true);
    expect(existsSync(record.jsonPath)).toBe(true);
  });

  it('harness run: follows valid state transitions', () => {
    expect(transitionStatus('created', 'ready')).toBe('ready');
    expect(transitionStatus('ready', 'running')).toBe('running');
    expect(transitionStatus('running', 'blocked')).toBe('blocked');
    expect(transitionStatus('blocked', 'running')).toBe('running');
    expect(transitionStatus('running', 'verifying')).toBe('verifying');
    expect(transitionStatus('verifying', 'completed')).toBe('completed');
  });

  it('harness run: rejects invalid transitions', () => {
    expect(() => transitionStatus('created', 'completed')).toThrow();
    expect(() => transitionStatus('completed', 'running')).toThrow();
  });

  it('harness run + verify: completes task with verification', async () => {
    const record = await createTaskRecord({ projectPath, userInstruction: 'Add unit tests' });
    expect(record.state.type).toBe('test');

    // Build Context Pack before completing (task must be active)
    const pack = await buildContextPack({
      projectId: 'proj_e2e',
      runId: 'run_e2e_001',
      taskId: record.state.taskId,
      userInstruction: 'Add unit tests',
      workspacePath: projectPath,
    });
    expect(pack.task.taskType).toBe('test');
    expect(pack.git.branch).toBeTruthy();
    expect(pack.project.name).toBeTruthy();

    // Transition through lifecycle
    const jsonPath = record.jsonPath;
    const state = JSON.parse(readFileSync(jsonPath, 'utf-8'));
    state.status = 'running';
    writeFileSync(jsonPath, JSON.stringify(state, null, 2) + '\n', 'utf-8');

    // Complete task — requires passed verification result on disk (VER3-02)
    const verSteps = [
      { name: 'test', command: 'echo ok', type: 'test' as const, required: true, timeoutMs: 30000,
        source: 'agents-md', uncertain: false, status: 'passed' as const,
        exitCode: 0, stdout: '', stderr: '', durationMs: 1000 },
    ];
    const verResult = { total: 1, passed: 1, failed: 0, skipped: 0, status: 'passed' as const, durationMs: 1000 };
    const verReport = generateReport('ver_e2e_pass', verSteps, verResult, {
      taskId: record.state.taskId,
      projectPath,
    });
    saveReport(verReport);

    // Patch projectId
    const manifest = JSON.parse(readFileSync(join(projectPath, '.project/state/manifest.json'), 'utf-8'));
    const loaded = loadVerificationResult(projectPath, 'ver_e2e_pass');
    if (loaded) {
      loaded.projectId = manifest.projectId;
      loaded.integrity = computeIntegrity(loaded);
      saveVerificationResult(loaded, projectPath);
    }

    const result = await completeTask({
      projectPath,
      taskId: record.state.taskId,
      changedFiles: ['src/test.ts'],
      verificationId: 'ver_e2e_pass',
    });

    expect(result.finalStatus).toBe('completed');
    expect(result.changedFiles).toContain('src/test.ts');

    // Files moved to completed/
    expect(existsSync(join(projectPath, '.project/tasks/completed', `${record.state.taskId}.md`))).toBe(true);
  });
});

// ============================================================
// E2E Scenario 4: Governance — High-risk Commands Blocked
// ============================================================

describe('E2E: Governance — High-Risk Prevention', () => {
  beforeEach(async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
  });

  it('harness run: policy blocks rm -rf', async () => {
    const result = await checkPolicy('Bash', { command: 'rm -rf /tmp' });
    expect(result.decision).toBe('needs_approval');
    expect(result.riskLevel).toBe('high');
  });

  it('harness run: policy blocks dangerous git commands', async () => {
    const result = await checkPolicy('Bash', { command: 'git reset --hard HEAD' });
    expect(result.decision).toBe('needs_approval');
  });

  it('harness run: policy denies credential file writes', async () => {
    const result = await checkPolicy('Write', { affectedPaths: ['config/credentials.json'] });
    expect(result.decision).toBe('deny');
  });

  it('harness run: policy allows read-only tools', async () => {
    const result = await checkPolicy('Read', {});
    expect(result.decision).toBe('allow');
  });

  it('harness run: approval gate works end-to-end', () => {
    const approvalId = `app_e2e_${Date.now().toString(36)}`;
    const approval = submitApproval({
      id: approvalId, action: 'Delete file', reason: 'Cleanup', riskLevel: 'high',
    });
    expect(approval.status).toBe('pending');

    const resolved = resolveApproval(approvalId, { approved: true, resolvedBy: 'operator' });
    expect(resolved!.status).toBe('approved');
  });

  it('secret redactor: redacts all common patterns', () => {
    const input = 'API key: sk-abc123def456ghi789jkl012, DB: postgresql://user:pass@host/db';
    const result = redactText(input);
    expect(result).not.toContain('sk-abc123');
    expect(result).not.toContain('postgresql://user:pass');
    expect(result).toContain('[REDACTED]');
  });

  it('secret redactor: identifies protected files', () => {
    expect(isProtectedFile('.env')).toBe(true);
    expect(isProtectedFile('.env.production')).toBe(true);
    expect(isProtectedFile('credentials.json')).toBe(true);
    expect(isProtectedFile('src/index.ts')).toBe(false);
  });
});

// ============================================================
// E2E Scenario 5: Delivery Guard — Blocks Without Verification
// ============================================================

describe('E2E: Delivery Guard', () => {
  beforeEach(async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
  });

  it('harness deliver: requires git changes', async () => {
    const guard = await runGuard({ deliveryType: 'commit', projectPath });
    expect(guard.blockedBy.length).toBeGreaterThan(0);
    expect(guard.canProceed).toBe(false);
  });

  it('harness deliver: blocks commit without run report', async () => {
    // Create a git change
    const git = simpleGit(projectPath);
    writeFileSync(join(projectPath, 'change.txt'), 'change', 'utf-8');
    await git.add('.');

    const guard = await runGuard({ deliveryType: 'commit', projectPath });
    expect(guard.canProceed).toBe(false);
    expect(guard.blockedBy.some(b => b.includes('run report') || b.includes('Verification'))).toBe(true);
  });

  it('harness deliver: generates commit message with conventional format', () => {
    const msg = generateCommitMessage({
      taskType: 'bugfix',
      taskSummary: 'Fix login timeout',
      scope: 'auth',
      details: 'Increased token expiry to 1 hour',
      footer: 'Closes #42',
    });
    expect(msg.full).toContain('fix(auth): Fix login timeout');
    expect(msg.full).toContain('Closes #42');
  });

  it('harness deliver: PR body has required sections', () => {
    const pr = generatePrBody({
      title: 'Fix login timeout',
      taskId: 'task_001',
      runId: 'run_001',
      changedFiles: ['src/auth.ts'],
      verificationStatus: 'passed',
      risks: ['Token caching needs review'],
    });
    expect(pr.body).toContain('## Summary');
    expect(pr.body).toContain('## Task');
    expect(pr.body).toContain('## Changed Files');
    expect(pr.body).toContain('## Verification');
    expect(pr.body).toContain('## Risks');
  });

  it('harness deliver: generates delivery report', async () => {
    const report = generateDeliveryReport({
      deliveryId: 'del_e2e_001',
      projectId: 'proj_e2e',
      type: 'commit',
      summary: 'E2E test delivery',
    });
    const path = saveDeliveryReport(report, projectPath);
    expect(existsSync(path)).toBe(true);
    const content = readFileSync(path, 'utf-8');
    expect(content).toContain('Delivery Report');
    expect(content).toContain('del_e2e_001');
  });
});

// ============================================================
// E2E Scenario 6: Observability — Events, Trace, Report
// ============================================================

describe('E2E: Observability', () => {
  beforeEach(async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
  });

  it('logEvent writes events to JSONL', () => {
    logEvent({ projectId: 'proj_e2e', type: 'run.started', actor: 'harness', summary: 'E2E run', runId: 'run_e2e' }, projectPath);
    const logPath = join(projectPath, '.project/reports/events/run_e2e.jsonl');
    expect(existsSync(logPath)).toBe(true);
  });

  it('createTrace and saveTrace persist run metadata', () => {
    const trace = createTrace({ runId: 'trace_e2e', projectId: 'proj_e2e', taskId: 'task_e2e' });
    trace.toolCallCount = 5;
    trace.fileChangeCount = 3;
    const path = saveTrace(trace, projectPath);
    expect(existsSync(path)).toBe(true);
  });

  it('generateRunReport produces complete report', () => {
    const trace = createTrace({ runId: 'report_e2e', projectId: 'proj_e2e' });
    updateTraceStatus(trace, 'completed', 'All tests passed');
    const report = generateRunReport(trace, {
      changedFiles: ['src/main.ts'],
      verificationStatus: 'passed',
    });
    const path = saveRunReport(report, projectPath);
    expect(existsSync(path)).toBe(true);
    const content = readFileSync(path, 'utf-8');
    expect(content).toContain('Run Report');
    expect(content).toContain('report_e2e');
    expect(content).toContain('PASSED');
  });
});

// ============================================================
// E2E Scenario 7: Checkpoint & Recovery
// ============================================================

describe('E2E: Checkpoint & Recovery', () => {
  beforeEach(async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
  });

  it('createCheckpoint captures git state', async () => {
    const cp = await createCheckpoint({ projectPath });
    expect(cp.id).toMatch(/^cp_/);
    expect(cp.currentBranch).toBeTruthy();
  });
});

// ============================================================
// E2E Scenario 8: Skill Execution
// ============================================================

describe('E2E: Skill Execution', () => {
  beforeEach(async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
  });

  it('filesystem skill: writes and reads file', async () => {
    const writeResult = await registry.execute('filesystem', 'write_file',
      { path: 'test.txt', content: 'e2e test' }, { projectPath });
    expect(writeResult.status).toBe('success');

    const readResult = await registry.execute('filesystem', 'read_file',
      { path: 'test.txt' }, { projectPath });
    expect(readResult.status).toBe('success');
    expect((readResult.output as any).content).toBe('e2e test');
  });

  it('repo-scanner skill: builds repository map', async () => {
    mkdirSync(join(projectPath, 'src'), { recursive: true });
    writeFileSync(join(projectPath, 'package.json'), JSON.stringify({ name: 'e2e', scripts: { test: 'vitest' } }));
    const result = await registry.execute('repo-scanner', 'build_repository_map', {}, { projectPath });
    expect(result.status).toBe('success');
  });
});

// ============================================================
// E2E Scenario 9: Cross-Process Approval Persistence
// ============================================================

describe('E2E: Cross-Process Approval Persistence', () => {
  beforeEach(async () => {
    await createProject({ name: 'e2e-project', path: projectPath });
  });

  it('create, resolve, consume approval across separate CLI processes', async () => {
    const distPath = join(process.cwd(), 'dist/index.js');
    const execSync = (await import('child_process')).execSync;

    // Helper: run CLI and parse JSON output
    // Handles non-zero exit codes (used for failure-path tests)
    const cli = (args: string): any => {
      const cmd = `node "${distPath}" --json ${args}`;
      try {
        const result = execSync(cmd, {
          cwd: projectPath,
          encoding: 'utf8',
          timeout: 15000,
        });
        return JSON.parse(result.trim());
      } catch (e: unknown) {
        // Non-zero exit — try to parse JSON from stdout
        const execError = e as { stdout?: string };
        if (execError.stdout) {
          try { return JSON.parse(execError.stdout.trim()); } catch { /* ignore parse errors */ }
        }
        throw e;
      }
    };

    // Propose an ADR first
    const proposeResult = cli(
      `decision propose --title "Cross-Process ADR" --type architecture --summary "Testing cross-process" --context "Need persistence" --decision "Use SQLite"`,
    );
    expect(proposeResult.ok).toBe(true);
    const adrId = proposeResult.data.id;

    // Process 1: Create approval
    const createResult = cli(`approval create-adr --action accept --adr ${adrId}`);
    expect(createResult.ok).toBe(true);
    expect(createResult.data.status).toBe('pending');
    const approvalId = createResult.data.id;
    expect(approvalId).toBeTruthy();

    // Process 2: Resolve approval (separate Node process)
    const resolveResult = cli(`approval resolve ${approvalId} --approve --by "e2e-tester"`);
    expect(resolveResult.ok).toBe(true);
    expect(resolveResult.data.status).toBe('approved');

    // Process 3: Accept ADR (separate Node process)
    const acceptResult = cli(`decision accept ${adrId} --approval-id ${approvalId} --by "e2e-tester"`);
    expect(acceptResult.ok).toBe(true);
    expect(acceptResult.data.status).toBe('accepted');

    // Process 4: Reuse — must fail
    const adr2Result = cli(
      `decision propose --title "Second ADR" --type architecture --summary "Test" --context "Test" --decision "Test"`,
    );
    expect(adr2Result.ok).toBe(true);
    const adrId2 = adr2Result.data.id;

    const reuseResult = cli(`decision accept ${adrId2} --approval-id ${approvalId} --by "e2e-tester"`);
    expect(reuseResult.ok).toBe(false);
    expect(reuseResult.error).toBeTruthy();
  });
});
