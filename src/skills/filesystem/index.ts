import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'filesystem',
  version: '1.0.0',
  description: 'Read, write, and manage project files',
  category: 'filesystem',
  tools: [
    { name: 'read_file', description: 'Read file contents', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
    { name: 'write_file', description: 'Write content to a file', inputSchema: {}, outputSchema: {}, riskLevel: 'medium', requiresApproval: false, timeoutMs: 10000 },
    { name: 'delete_file', description: 'Delete a file', inputSchema: {}, outputSchema: {}, riskLevel: 'high', requiresApproval: true, timeoutMs: 5000 },
    { name: 'list_dir', description: 'List directory contents', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 5000 },
    { name: 'search_text', description: 'Search text in files', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 30000 },
  ],
  riskLevel: 'medium',
};
