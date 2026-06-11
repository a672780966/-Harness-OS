import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'github',
  version: '1.0.0',
  description: 'GitHub operations: issues, PRs, reviews, releases',
  category: 'github',
  defaultEnabled: false,
  requiresNetwork: true,
  requiresFilesystem: false,
  riskLevel: 'high',
  tools: [
    {
      name: 'create_pr',
      description: 'Create a pull request (requires approval)',
      inputSchema: { type: 'object', properties: { title: { type: 'string' }, body: { type: 'string' }, head: { type: 'string' }, base: { type: 'string' } }, required: ['title', 'head'] },
      outputSchema: { type: 'object', properties: { url: { type: 'string' }, number: { type: 'number' } } },
      riskLevel: 'high', requiresApproval: true, timeoutMs: 30000,
    },
    {
      name: 'create_issue',
      description: 'Create an issue',
      inputSchema: { type: 'object', properties: { title: { type: 'string' }, body: { type: 'string' } }, required: ['title'] },
      outputSchema: { type: 'object', properties: { url: { type: 'string' }, number: { type: 'number' } } },
      riskLevel: 'medium', requiresApproval: false, timeoutMs: 15000,
    },
  ],
};
