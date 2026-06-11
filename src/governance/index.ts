import { PolicyCheckResult, PolicyDecision, RiskLevel } from '../types.js';

export async function checkPolicy(
  action: string,
  args: { affectedPaths?: string[]; command?: string }
): Promise<PolicyCheckResult> {
  console.log(`Checking policy for: ${action}`);
  // TODO: Full Policy Engine per 08_GOVERNANCE_SECURITY.md
  // 1. Read policy sources (global, project, AGENTS.md)
  // 2. Classify risk level
  // 3. Check protected paths
  // 4. Check dangerous commands
  // 5. Return allow/deny/requires-approval
  return { decision: 'allow', reason: 'Default allow', riskLevel: 'low', policySource: 'default', affectedPaths: [] };
}

export function classifyRisk(command: string): RiskLevel {
  const dangerous = ['rm -rf', 'sudo', 'chmod -R', 'chown -R', 'git reset --hard', 'git clean -fd', 'git push --force'];
  for (const d of dangerous) {
    if (command.includes(d)) return 'high';
  }
  return 'low';
}
