import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'delivery',
  version: '1.0.0',
  description: 'Delivery operations: commit messages, PR bodies, release notes',
  category: 'delivery',
  defaultEnabled: true,
  requiresNetwork: false,
  requiresFilesystem: true,
  riskLevel: 'low',
  tools: [
    {
      name: 'generate_commit_message',
      description: 'Generate a conventional commit message from task summary and diff',
      inputSchema: {
        type: 'object',
        properties: { summary: { type: 'string' }, files: { type: 'array', items: { type: 'string' } } },
        required: ['summary'],
      },
      outputSchema: { type: 'object', properties: { message: { type: 'string' }, type: { type: 'string' } } },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 10000,
    },
    {
      name: 'generate_pr_body',
      description: 'Generate a PR body from task record and verification result',
      inputSchema: {
        type: 'object',
        properties: { taskId: { type: 'string' }, runId: { type: 'string' } },
        required: ['taskId'],
      },
      outputSchema: {
        type: 'object',
        properties: { body: { type: 'string' }, sections: { type: 'array', items: { type: 'string' } } },
      },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 10000,
    },
  ],
};
