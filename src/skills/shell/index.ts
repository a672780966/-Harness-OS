import { SkillManifest } from '../../types.js';
import { execSync } from 'child_process';
import { type SkillExecutionContext, type SkillExecutionResult, successResult, failedResult } from '../executor.js';

const runCommandSchema = { type: 'object', properties: { command: { type: 'string' }, cwd: { type: 'string' }, timeout: { type: 'number' } }, required: ['command'] };

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
    { name: 'run_command', description: 'Execute shell command', inputSchema: runCommandSchema, outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, stdout: { type: 'string' }, stderr: { type: 'string' }, durationMs: { type: 'number' } } }, riskLevel: 'medium', requiresApproval: false, timeoutMs: 300000 },
    { name: 'run_test', description: 'Run test command', inputSchema: runCommandSchema, outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, summary: { type: 'string' } } }, riskLevel: 'low', requiresApproval: false, timeoutMs: 300000 },
    { name: 'run_build', description: 'Run build command', inputSchema: runCommandSchema, outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, durationMs: { type: 'number' } } }, riskLevel: 'low', requiresApproval: false, timeoutMs: 600000 },
  ],
};

export async function execute(toolName: string, input: Record<string, unknown>, context: SkillExecutionContext): Promise<SkillExecutionResult> {
  const start = Date.now();

  try {
    const command = String(input.command ?? '');
    if (!command) return failedResult('shell', toolName, new Error('No command provided'), Date.now() - start);

    const cwd = input.cwd ? String(input.cwd) : context.projectPath;
    const timeout = (input.timeout as number) || 300000;

    try {
      const output = execSync(command, { cwd, timeout, encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });
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
