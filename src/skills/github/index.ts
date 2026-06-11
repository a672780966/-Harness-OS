import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'github',
  version: '1.0.0',
  description: 'GitHub operations: PR, issues, releases',
  category: 'github',
  tools: [
    { name: 'create_pr', description: 'Create a pull request', inputSchema: {}, outputSchema: {}, riskLevel: 'high', requiresApproval: true, timeoutMs: 30000 },
    { name: 'create_issue', description: 'Create an issue', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
  ],
  riskLevel: 'high',
};
