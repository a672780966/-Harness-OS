import { SkillManifest } from '../../types.js';

export const manifest: SkillManifest = {
  name: 'test-runner',
  version: '1.0.0',
  description: 'Run verification commands: lint, typecheck, test, build',
  category: 'test-runner',
  defaultEnabled: true,
  requiresNetwork: false,
  requiresFilesystem: true,
  riskLevel: 'low',
  tools: [
    {
      name: 'run_lint',
      description: 'Run linter (eslint, ruff, etc.)',
      inputSchema: {
        type: 'object',
        properties: { path: { type: 'string', description: 'File or directory to lint' } },
        required: [],
      },
      outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, output: { type: 'string' } } },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 120000,
    },
    {
      name: 'run_typecheck',
      description: 'Run type checker (tsc, mypy, etc.)',
      inputSchema: { type: 'object', properties: {}, required: [] },
      outputSchema: { type: 'object', properties: { exitCode: { type: 'number' }, errors: { type: 'number' } } },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 180000,
    },
    {
      name: 'run_unit_tests',
      description: 'Run unit tests',
      inputSchema: {
        type: 'object',
        properties: { path: { type: 'string', description: 'Optional test file or directory' } },
        required: [],
      },
      outputSchema: {
        type: 'object',
        properties: {
          passed: { type: 'number' },
          failed: { type: 'number' },
          total: { type: 'number' },
          durationMs: { type: 'number' },
        },
      },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 300000,
    },
  ],
};
