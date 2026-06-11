import { SkillManifest } from '../../types.js';
import { simpleGit } from 'simple-git';
import { type SkillExecutionContext, type SkillExecutionResult, successResult, failedResult, blockedResult } from '../executor.js';

export const manifest: SkillManifest = {
  name: 'git',
  version: '1.0.0',
  description: 'Git operations: status, diff, commit, branch management, push',
  category: 'git',
  defaultEnabled: true,
  requiresNetwork: false,
  requiresFilesystem: true,
  riskLevel: 'medium',
  docPath: 'src/skills/git/SKILL.md',
  permissions: [{ type: 'git-config', description: 'Read and modify git state' }],
  tools: [
    { name: 'git_status', description: 'Show working tree status', inputSchema: { type: 'object', properties: {}, required: [] }, outputSchema: { type: 'object', properties: { branch: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, hasChanges: { type: 'boolean' } } }, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
    { name: 'git_diff', description: 'Show changes', inputSchema: { type: 'object', properties: { path: { type: 'string' }, staged: { type: 'boolean' } }, required: [] }, outputSchema: { type: 'object', properties: { diff: { type: 'string' }, files: { type: 'array', items: { type: 'string' } } } }, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
    { name: 'git_commit', description: 'Create a commit', inputSchema: { type: 'object', properties: { message: { type: 'string' } }, required: ['message'] }, outputSchema: { type: 'object', properties: { hash: { type: 'string' }, message: { type: 'string' } } }, riskLevel: 'medium', requiresApproval: false, timeoutMs: 10000 },
    { name: 'git_push', description: 'Push to remote (requires approval)', inputSchema: { type: 'object', properties: { remote: { type: 'string' }, branch: { type: 'string' } }, required: [] }, outputSchema: { type: 'object', properties: { remote: { type: 'string' }, branch: { type: 'string' }, success: { type: 'boolean' } } }, riskLevel: 'high', requiresApproval: true, timeoutMs: 30000 },
  ],
};

export async function execute(toolName: string, input: Record<string, unknown>, context: SkillExecutionContext): Promise<SkillExecutionResult> {
  const start = Date.now();
  const git = simpleGit(context.projectPath);

  try {
    switch (toolName) {
      case 'git_status': {
        const status = await git.status();
        const branch = await git.branch();
        return successResult('git', toolName,
          { branch: branch.current, files: status.files.map(f => f.path), hasChanges: status.files.length > 0 },
          `Branch: ${branch.current}, ${status.files.length} file(s) changed`,
          Date.now() - start);
      }
      case 'git_diff': {
        const opts: string[] = [];
        if (input.staged) opts.push('--staged');
        if (input.path) opts.push('--', String(input.path));
        const diff = await git.diff(opts);
        const status = await git.status();
        return successResult('git', toolName,
          { diff: diff.slice(0, 10000), files: status.files.map(f => f.path) },
          `Diff: ${diff.length} chars`,
          Date.now() - start);
      }
      case 'git_commit': {
        const message = String(input.message ?? 'commit');
        const result = await git.commit(message);
        return successResult('git', toolName,
          { hash: result.commit || 'unknown', message },
          `Committed: ${(result.commit || '').slice(0, 8)}`,
          Date.now() - start);
      }
      case 'git_push':
        return blockedResult('git', toolName, 'git_push requires human approval', Date.now() - start);
      default:
        return failedResult('git', toolName, new Error(`Unknown tool: ${toolName}`), Date.now() - start);
    }
  } catch (err) {
    return failedResult('git', toolName, err as Error, Date.now() - start);
  }
}
