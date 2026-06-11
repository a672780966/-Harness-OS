import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'git',
  version: '1.0.0',
  description: 'Git operations: status, diff, commit, branch management',
  category: 'git',
  tools: [
    { name: 'git_status', description: 'Show working tree status', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
    { name: 'git_diff', description: 'Show changes', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
    { name: 'git_commit', description: 'Create a commit', inputSchema: {}, outputSchema: {}, riskLevel: 'medium', requiresApproval: false, timeoutMs: 10000 },
    { name: 'git_push', description: 'Push to remote', inputSchema: {}, outputSchema: {}, riskLevel: 'high', requiresApproval: true, timeoutMs: 30000 },
  ],
  riskLevel: 'medium',
};
