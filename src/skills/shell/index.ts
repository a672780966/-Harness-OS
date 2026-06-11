import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'shell',
  version: '1.0.0',
  description: 'Execute controlled shell commands',
  category: 'shell',
  tools: [
    { name: 'run_command', description: 'Execute a shell command', inputSchema: {}, outputSchema: {}, riskLevel: 'medium', requiresApproval: false, timeoutMs: 300000 },
    { name: 'run_test', description: 'Run test command', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 300000 },
    { name: 'run_build', description: 'Run build command', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 300000 },
  ],
  riskLevel: 'medium',
};
