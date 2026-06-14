/**
 * Harness OS — Policy Engine
 *
 * Thin Harness policy evaluation: rules-based allow/deny/needs_approval.
 *
 * Source: CLAUDE.md §4 (permission three-state), §5 (hook decisions).
 *
 * Design:
 * - Rules are evaluated in declaration order; first match wins.
 * - If no rule matches, default is `needs_approval` (fail closed).
 * - classifyRisk() is a helper for simple command-based risk classification.
 */

import { type PermissionDecision, type PolicyCheckResult, type RiskLevel } from '../types.js';

// ============================================================
// Policy Rule
// ============================================================

export interface PolicyContext {
  /** Shell command (for Bash tools). */
  command?: string;
  /** File paths affected (for Write/Edit/Delete). */
  affectedPaths?: string[];
  /** The tool name being invoked. */
  toolName?: string;
  /** The skill name (for skill-based execution). */
  skillName?: string;
}

export interface PolicyRule {
  /** Unique rule name for traceability. */
  name: string;
  /** Human-readable description. */
  description: string;
  /** Match function — returns true if this rule applies. */
  match: (action: string, context: PolicyContext) => boolean;
  /** Decision if this rule matches. */
  decision: PermissionDecision;
  /** Reason template (may reference action or context). */
  reason: string;
}

// ============================================================
// Default Rules
// ============================================================

function hasDangerousPattern(command: string): boolean {
  const dangerous = [
    'rm -rf',
    'sudo ',
    'chmod -r',
    'chmod 777',
    'chown -r',
    'git reset --hard',
    'git clean -fd',
    'git push --force',
    'git push -f',
    'npm publish',
    'pnpm publish',
    'docker push',
    'kubectl delete',
    'terraform apply',
    'terraform destroy',
    // PowerShell dangerous patterns (GOV3-05)
    'remove-item',
    'ri ',
    'del ',
    'net user',
    'net localgroup',
    'stop-process',
    'kill ',
    'start-process',
    'invoke-expression',
    'iex ',
    'invoke-webrequest',
    'iwr ',
    'wget ',
    'curl ',
    'new-item -type',
    'set-content',
    'add-content',
  ];
  const normalized = command.toLowerCase();
  return dangerous.some((d) => normalized.includes(d));
}

function touchesProtectedPath(paths: string[]): boolean {
  const protectedPaths = [
    '.env',
    '.env.local',
    '.env.production',
    'secrets',
    '.git',
    'credentials',
    'id_rsa',
    'id_ed25519',
    '.pem',
    '.key',
    '.token',
  ];
  return paths.some((p) => protectedPaths.some((pp) => p.includes(pp)));
}

function isSensitiveFileRead(paths: string[]): boolean {
  // Sensitive files that must go through policy even for reads (GOV3-02)
  const sensitive = [
    '.env',
    '.env.local',
    '.env.production',
    'credentials',
    'id_rsa',
    'id_ed25519',
    '.pem',
    '.key',
    '.token',
    'secrets',
  ];
  return paths.some((p) =>
    sensitive.some((s) => {
      const basename = p.split(/[/\\]/).pop() || '';
      return basename.startsWith(s.replace(/^\./, '')) && (p.includes(s) || basename.startsWith(s.replace(/^\./, '')));
    }),
  );
}

function touchesGovernancePaths(paths: string[]): boolean {
  // AGENTS.md, accepted ADRs, governance/config policy files (GOV3-02)
  return paths.some((p) => {
    const name = p.split(/[/\\]/).pop() || '';
    return name === 'AGENTS.md' || (name.endsWith('.md') && p.includes('decisions/')) || name === 'policy.json';
  });
}

const DEFAULT_RULES: PolicyRule[] = [
  // Read-only tools are always allowed (unless reading sensitive files — GOV3-02)
  {
    name: 'read-only-tools',
    description: 'Read-only tools are allowed for non-sensitive files',
    match: (action, ctx) => {
      if (!['Read', 'Glob', 'Grep', 'LS', 'List'].includes(action)) return false;
      // Block reads of sensitive files like .env, credentials (GOV3-02)
      if (ctx.affectedPaths && ctx.affectedPaths.length > 0 && isSensitiveFileRead(ctx.affectedPaths)) {
        return false;
      }
      return true;
    },
    decision: 'allow',
    reason: 'Read-only tool: ${action}',
  },
  // Deny credential write first (strongest decision, highest priority)
  // Matches paths that specifically contain "credential" or "token" as path components.
  // NOTE: does NOT match ".env" here — that's handled by protected-paths (needs_approval).
  {
    name: 'credential-write',
    description: 'Writing credential files is denied by default',
    match: (_, ctx) =>
      !!ctx.affectedPaths &&
      ctx.affectedPaths.some((p) => p.includes('credential') || p.includes('/token') || p.includes('/secret')),
    decision: 'deny',
    reason: 'Writing credential files is denied by default policy',
  },
  // Dangerous commands require human approval
  {
    name: 'high-risk-bash',
    description: 'Dangerous shell commands require human approval',
    match: (_, ctx) => !!ctx.command && hasDangerousPattern(ctx.command),
    decision: 'needs_approval',
    reason: 'High-risk bash command requires human approval',
  },
  // Protected path modification requires approval
  {
    name: 'protected-paths',
    description: 'Protected paths cannot be modified without approval',
    match: (_, ctx) => !!ctx.affectedPaths && ctx.affectedPaths.length > 0 && touchesProtectedPath(ctx.affectedPaths),
    decision: 'needs_approval',
    reason: 'Protected path modification requires human approval',
  },
  // AGENTS.md and ADR writes require approval (GOV3-02)
  {
    name: 'governance-files-write',
    description: 'AGENTS.md, ADR, and policy files require human approval',
    match: (_, ctx) => !!ctx.affectedPaths && ctx.affectedPaths.length > 0 && touchesGovernancePaths(ctx.affectedPaths),
    decision: 'needs_approval',
    reason: 'Governance file modification requires human approval',
  },
  // Non-sensitive write operations (after credential/protected checks above)
  {
    name: 'write-default-allow',
    description: 'Writing non-sensitive files is allowed by default',
    match: (action) => action === 'Write',
    decision: 'allow',
    reason: 'Non-sensitive write operation is allowed',
  },
  // Non-dangerous shell commands (after high-risk check above)
  {
    name: 'bash-default-allow',
    description: 'Non-dangerous shell commands are allowed by default',
    match: (action) => action === 'Bash',
    decision: 'allow',
    reason: 'Non-dangerous shell command is allowed',
  },
  // Read-only git operations
  {
    name: 'git-read-allow',
    description: 'Read-only git operations are allowed',
    match: (action) => action === 'GitRead',
    decision: 'allow',
    reason: 'Read-only git operation is allowed',
  },
  // Git commit requires approval (GOV3-06: no default allow)
  {
    name: 'git-commit-approval',
    description: 'Git commit requires human approval',
    match: (action) => action === 'GitCommit',
    decision: 'needs_approval',
    reason: 'Git commit requires human approval per governance policy',
  },
  // Git push denied by default (must be explicitly approved in policy)
  {
    name: 'git-push-deny',
    description: 'Git push is denied by default policy',
    match: (action) => action === 'GitPush',
    decision: 'deny',
    reason: 'Git push is denied by default policy',
  },
  // Delete operations denied by default
  {
    name: 'delete-default-deny',
    description: 'Delete operations are denied by default',
    match: (action) => action === 'Delete',
    decision: 'deny',
    reason: 'Delete operations are denied by default policy',
  },
];

// ============================================================
// classifyRisk
// ============================================================

/**
 * Classify the risk level of a shell command.
 * Returns 'high' for destructive or dangerous patterns.
 *
 * Source: Derived from pre_tool_guard.py dangerous patterns.
 */
export function classifyRisk(command: string): RiskLevel {
  return hasDangerousPattern(command) ? 'high' : 'low';
}

// ============================================================
// checkPolicy — Main Entry Point
// ============================================================

/**
 * Evaluate an action against policy rules.
 *
 * Rules are evaluated in order; first matching rule determines the decision.
 * If no rule matches, the default is `needs_approval` (fail closed).
 *
 * @param action - Tool name or action identifier (e.g. "Bash", "Write")
 * @param context - Context about the invocation
 * @param rules - Optional custom rules (defaults to DEFAULT_RULES)
 */
export async function checkPolicy(
  action: string,
  context: PolicyContext,
  rules: PolicyRule[] = DEFAULT_RULES,
): Promise<PolicyCheckResult> {
  for (const rule of rules) {
    if (rule.match(action, context)) {
      return {
        decision: rule.decision,
        reason: `${rule.reason} [rule: ${rule.name}]`,
        riskLevel: context.command ? classifyRisk(context.command) : 'low',
        policySource: `builtin:${rule.name}`,
        affectedPaths: context.affectedPaths ?? [],
      };
    }
  }

  // Default: fail closed
  return {
    decision: 'needs_approval',
    reason: `No matching policy rule for "${action}" — requires approval [rule: default-fallback]`,
    riskLevel: 'medium',
    policySource: 'builtin:default-fallback',
    affectedPaths: context.affectedPaths ?? [],
  };
}

/**
 * Create a custom policy rule.
 * Convenience factory for programmatic rule definitions.
 */
export function createRule(
  name: string,
  description: string,
  match: (action: string, context: PolicyContext) => boolean,
  decision: PermissionDecision,
  reason: string,
): PolicyRule {
  return { name, description, match, decision, reason };
}
