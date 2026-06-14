/**
 * Harness OS — Verification Plan
 *
 * Phase 6.2: Build a verification plan with priority ordering.
 *
 * Priority: lint → typecheck → test → build
 * Required commands must pass; optional commands may be skipped.
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §7
 */

import type { CommandType, DetectedCommand } from './commands.js';

// ============================================================
// Command Priority Order
// ============================================================

const COMMAND_ORDER: CommandType[] = [
  'lint',
  'typecheck',
  'unit-test',
  'test',
  'integration-test',
  'build',
  'e2e-test',
  'install',
  'format-check',
  'custom',
];

// ============================================================
// Types
// ============================================================

export interface VerificationStep {
  name: string;
  command: string;
  type: CommandType;
  required: boolean;
  timeoutMs: number;
  source: string;
  uncertain: boolean;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped';
  exitCode: number | null;
  stdout: string;
  stderr: string;
  durationMs: number;
}

export interface VerificationPlan {
  projectPath: string;
  steps: VerificationStep[];
  createdAt: string;
  totalSteps: number;
  requiredSteps: number;
}

// ============================================================
// Default Timeouts by Type
// ============================================================

const DEFAULT_TIMEOUTS: Record<string, number> = {
  lint: 120_000,
  typecheck: 180_000,
  'unit-test': 300_000,
  test: 300_000,
  'integration-test': 600_000,
  'e2e-test': 600_000,
  build: 600_000,
  install: 900_000,
  'format-check': 60_000,
};

// ============================================================
// Required Command Types
// ============================================================

/** Command types that must run (and pass) before a task can complete. */
const REQUIRED_TYPES: CommandType[] = ['lint', 'typecheck', 'unit-test', 'test', 'build'];

// ============================================================
// Build Plan
// ============================================================

/**
 * Build a verification plan from detected commands.
 * Orders: lint → typecheck → test/test-like → build → other
 */
export function buildPlan(projectPath: string, commands: DetectedCommand[]): VerificationPlan {
  const steps: VerificationStep[] = commands
    .sort((a, b) => {
      const aIdx = COMMAND_ORDER.indexOf(a.type);
      const bIdx = COMMAND_ORDER.indexOf(b.type);
      if (aIdx !== bIdx) return aIdx - bIdx;
      return a.name.localeCompare(b.name);
    })
    .map((cmd) => ({
      name: cmd.name,
      command: cmd.command,
      type: cmd.type,
      required: REQUIRED_TYPES.includes(cmd.type),
      timeoutMs: DEFAULT_TIMEOUTS[cmd.type] ?? 300_000,
      source: cmd.source,
      uncertain: cmd.uncertain,
      status: 'pending',
      exitCode: null,
      stdout: '',
      stderr: '',
      durationMs: 0,
    }));

  return {
    projectPath,
    steps,
    createdAt: new Date().toISOString(),
    totalSteps: steps.length,
    requiredSteps: steps.filter((s) => s.required).length,
  };
}

/**
 * Format a verification plan for display.
 */
export function formatPlan(plan: VerificationPlan): string {
  const lines = [
    `Verification Plan — ${plan.projectPath}`,
    `Created: ${plan.createdAt}`,
    `Steps: ${plan.totalSteps} total, ${plan.requiredSteps} required`,
    '',
    '| # | Type | Command | Required | Timeout | Source |',
    '|---|------|---------|----------|---------|--------|',
  ];

  plan.steps.forEach((step, i) => {
    lines.push(
      `| ${i + 1} | ${step.type} | ${step.command.slice(0, 50)} | ${step.required ? 'yes' : 'no'} | ${(step.timeoutMs / 1000).toFixed(0)}s | ${step.source}${step.uncertain ? '*' : ''} |`,
    );
  });

  if (plan.steps.some((s) => s.uncertain)) {
    lines.push('', '* — inferred command (may not be correct)');
  }

  return lines.join('\n');
}
