import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'test-runner',
  version: '1.0.0',
  description: 'Run verification commands: lint, typecheck, test, build',
  category: 'test-runner',
  tools: [
    { name: 'run_lint', description: 'Run linter', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 120000 },
    { name: 'run_typecheck', description: 'Run type checker', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 180000 },
    { name: 'run_unit_tests', description: 'Run unit tests', inputSchema: {}, outputSchema: {}, riskLevel: 'low', requiresApproval: false, timeoutMs: 300000 },
  ],
  riskLevel: 'low',
};
