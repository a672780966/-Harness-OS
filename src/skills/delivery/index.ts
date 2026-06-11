import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'delivery',
  version: '1.0.0',
  description: 'Delivery operations: commit messages, PR bodies, release notes',
  category: 'delivery',
  tools: [
    { name: 'generate_commit_message', description: 'Generate commit message', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
    { name: 'generate_pr_body', description: 'Generate PR body', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
  ],
  riskLevel: 'low',
};
