import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'repo-scanner',
  version: '1.0.0',
  description: 'Scan repository structure, dependencies, symbols, and commands',
  category: 'repo-scanner',
  tools: [
    { name: 'scan_files', description: 'Scan files in repository', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 30000 },
    { name: 'build_repository_map', description: 'Build repository map', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 30000 },
    { name: 'detect_commands', description: 'Detect package manager and commands', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 10000 },
  ],
  riskLevel: 'low',
};
