import { SkillManifest } from '../../types.js';
import { execSync } from 'child_process';
import { resolve } from 'path';
import { type SkillExecutionContext, type SkillExecutionResult, successResult, failedResult, blockedResult } from '../executor.js';
import { type SkillRegistry } from '../registry.js';

const runCommandSchema = { type: 'object', properties: { command: { type: 'string' }, cwd: { type: 'string' }, timeout: { type: 'number' } }, required: ['command'] };

const DANGEROUS_PATTERNS = [
  'rm -rf', 'sudo ', 'chmod -R', 'chown -R', 'git reset --hard', 'git clean -fd',
  'git push --force', 'git push -f', 'curl | sh', 'wget | sh',
  'npm publish', 'pnpm publish', 'docker system prune',
  'kubectl delete', 'terraform apply', 'terraform destroy',
];

export const manifest: SkillManifest = {
  name: 'shell',
  version: '1.0.0',
  description: 'Execute controlled shell commands within workspace boundary',
  category: 'shell',
  defaultEnabled: true,
  requiresNetwork: false,
  requiresFilesystem: true,
  riskLevel: 'high',
  docPath: 'src/skills/shell/SKILL.md',
  permissions: [{ type: 'filesystem-read', description: 'Read command output' }, { type: 'filesystem-write', description: 'Write artifacts' }],
  tools: [
    { name: 'run_command', description: 'Execute shell command (dangerous patterns blocked)', inputSchema: runCommandSchema, outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, stdout: { type: 'string' }, stderr: { type: 'string' }, durationMs: { type: 'number' } } }, riskLevel: 'high', requiresApproval: false, timeoutMs: 300000 },
    { name: 'run_test', description: 'Run test command', inputSchema: runCommandSchema, outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, summary: { type: 'string' } } }, riskLevel: 'low', requiresApproval: false, timeoutMs: 300000 },
    { name: 'run_build', description: 'Run build command', inputSchema: runCommandSchema, outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, durationMs: { type: 'number' } } }, riskLevel: 'low', requiresApproval: false, timeoutMs: 600000 },
  ],
};

// GOV4-01/GOV4-04: _execute is NOT exported. cwd is canonicalized and
// bounded to workspace. Shell commands default needs_approval via policy.
async function _execute(toolName: string, input: Record<string, unknown>, context: SkillExecutionContext): Promise<SkillExecutionResult> {
  const start = Date.now();

  try {
    const command = String(input.command ?? '');
    if (!command) return failedResult('shell', toolName, new Error('No command provided'), Date.now() - start);

    // Check for dangerous patterns
    const normalized = command.toLowerCase();
    for (const pattern of DANGEROUS_PATTERNS) {
      if (normalized.includes(pattern)) {
        return blockedResult('shell', toolName, `Dangerous command pattern detected: ${pattern}. This requires human approval.`, Date.now() - start);
      }
    }

    // GOV4-04: Canonicalize cwd and verify it's within workspace
    const workspacePath = resolve(context.projectPath);
    const rawCwd = input.cwd ? String(input.cwd) : '';
    let effectiveCwd = workspacePath;
    if (rawCwd) {
      const resolvedCwd = resolve(workspacePath, rawCwd);
      const rel = resolve(resolvedCwd);
      if (!rel.startsWith(workspacePath + '/') && !rel.startsWith(workspacePath + '\\') && rel !== workspacePath) {
        return blockedResult('shell', toolName, `cwd "${rawCwd}" resolves outside workspace — blocked (GOV4-04)`, Date.now() - start);
      }
      effectiveCwd = rel;
    }

    const timeout = (input.timeout as number) || 300000;

    try {
      const output = execSync(command, { cwd: effectiveCwd, timeout, encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });
      return successResult('shell', toolName,
        { exitCode: 0, stdout: output.slice(0, 5000), stderr: '', durationMs: Date.now() - start },
        `Command completed (exit 0)`,
        Date.now() - start);
    } catch (execErr: any) {
      const stdout = execErr.stdout?.toString().slice(0, 5000) || '';
      const stderr = execErr.stderr?.toString().slice(0, 2000) || '';
      return successResult('shell', toolName,
        { exitCode: execErr.status ?? 1, stdout, stderr, durationMs: Date.now() - start },
        `Command exited with code ${execErr.status ?? '?'}`,
        Date.now() - start);
    }
  } catch (err) {
    return failedResult('shell', toolName, err as Error, Date.now() - start);
  }
}

// GOV4-01: Self-registration — only entry point for executor registration.
export function _register(r: SkillRegistry): void {
  r.registerExecutor('shell', _execute);
}
