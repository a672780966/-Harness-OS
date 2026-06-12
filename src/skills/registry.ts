/**
 * Harness OS — Skill Registry
 *
 * Central registry for all Harness OS skills.
 * Handles skill registration, manifest querying, and project-level enable/disable.
 *
 * Reference: 07_MCP_SKILLS_SPEC.md §6
 *
 * Governance: GOV-01 (AUD-P0-001)
 * All skill executions pass through the Policy Engine before reaching the executor.
 * - getExecutor() is available but bypasses policy — use execute() for production paths.
 */

import type { SkillManifest, SkillCategory } from '../types.js';
import type { SkillExecutor } from './executor.js';
import { checkPolicy, type PolicyContext } from '../governance/policy.js';
import { submitApproval } from '../governance/approval-gate.js';
import {
  failedResult as failExec,
  blockedResult as blockExec,
  requiresApprovalResult as reqApprovalExec,
} from './executor.js';

// ============================================================
// Action Normalization
// ============================================================

/**
 * Normalize a skill tool name to a well-known action category for policy matching.
 *
 * Read-only operations → "Read"/"GitRead"
 * Write operations     → "Write"
 * Shell operations     → "Bash"
 * Git operations       → "GitCommit"/"GitPush"/"GitRead"
 * Delete operations    → "Delete"
 * Unknown operations   → "skillName:toolName" (no rule match → needs_approval)
 */
function normalizeSkillAction(skillName: string, toolName: string): string {
  if (skillName === 'filesystem') {
    if (['read_file', 'list_dir', 'read_file_range', 'search_text'].includes(toolName)) return 'Read';
    if (['write_file', 'create_dir'].includes(toolName)) return 'Write';
    if (['delete_file', 'delete_dir'].includes(toolName)) return 'Delete';
  }
  if (skillName === 'shell') {
    if (['run_command', 'run_test', 'run_build'].includes(toolName)) return 'Bash';
  }
  if (skillName === 'git') {
    if (['git_status', 'git_diff', 'git_log'].includes(toolName)) return 'GitRead';
    if (toolName === 'git_commit') return 'GitCommit';
    if (toolName === 'git_push') return 'GitPush';
  }
  if (skillName === 'repo-scanner') {
    return 'Read';
  }
  // Unknown skill/tool: use qualified name — won't match any rule → default needs_approval
  return `${skillName}:${toolName}`;
}

/**
 * Build a PolicyContext from skill tool input.
 * Extracts command (for shell) and file paths (for filesystem).
 */
function buildSkillPolicyContext(
  skillName: string,
  toolName: string,
  input: Record<string, unknown>,
): PolicyContext {
  const ctx: PolicyContext = {
    toolName,
    skillName,
  };

  // Extract command for shell tools
  if (typeof input.command === 'string') {
    ctx.command = input.command;
  }

  // Extract paths from common path fields
  const pathFields = ['path', 'file_path', 'filePath'];
  const paths: string[] = [];
  for (const field of pathFields) {
    const val = input[field];
    if (typeof val === 'string') {
      paths.push(val);
    }
  }
  if (paths.length > 0) {
    ctx.affectedPaths = paths;
  }

  return ctx;
}

// ============================================================
// Skill Registry
// ============================================================

class SkillRegistry {
  private skills: Map<string, SkillManifest> = new Map();
  private executors: Map<string, SkillExecutor> = new Map();

  /**
   * Register a skill manifest.
   */
  register(manifest: SkillManifest): void {
    if (this.skills.has(manifest.name)) {
      console.warn(`Skill already registered: ${manifest.name} — overwriting`);
    }
    this.skills.set(manifest.name, manifest);
  }

  /**
   * Register a skill executor.
   */
  registerExecutor(name: string, executor: SkillExecutor): void {
    this.executors.set(name, executor);
  }

  /**
   * Register multiple skill manifests.
   */
  registerAll(manifests: SkillManifest[]): void {
    for (const m of manifests) {
      this.register(m);
    }
  }

  /**
   * Get a skill manifest by name.
   */
  get(name: string): SkillManifest | undefined {
    return this.skills.get(name);
  }

  /**
   * Get a skill executor by name.
   */
  getExecutor(name: string): SkillExecutor | undefined {
    return this.executors.get(name);
  }

  /**
   * Execute a tool on a registered skill.
   *
   * Governance gate (GOV-01): Policy check runs BEFORE executor.
   *   - allow           → executor is called
   *   - deny            → blockedResult returned (executor NOT called)
   *   - needs_approval  → approval submitted, requires-approval result returned
   *   - policy error    → blockedResult (fail closed)
   *
   * All skill tool executions MUST go through this method for production use.
   * getExecutor() bypasses governance — use only for internal or test paths.
   */
  async execute(
    skillName: string,
    toolName: string,
    input: Record<string, unknown>,
    context: import('./executor.js').SkillExecutionContext,
  ): Promise<import('./executor.js').SkillExecutionResult> {
    const executor = this.executors.get(skillName);
    if (!executor) {
      return failExec(skillName, toolName, new Error(`No executor registered for skill: ${skillName}`), 0);
    }

    // ---- Manifest Validation: unknown tool → blocked (GOV-01) ----
    const manifest = this.skills.get(skillName);
    if (manifest) {
      const knownTool = manifest.tools.find(t => t.name === toolName);
      if (!knownTool) {
        return blockExec(
          skillName,
          toolName,
          `Unknown tool "${toolName}" for skill "${skillName}" — blocked by governance`,
          0,
        );
      }
    }

    // ---- Policy Gate (GOV-01) ----
    const action = normalizeSkillAction(skillName, toolName);
    const policyCtx = buildSkillPolicyContext(skillName, toolName, input);

    let policyResult: import('../types.js').PolicyCheckResult;
    try {
      policyResult = await checkPolicy(action, policyCtx);
    } catch (err) {
      // Fail closed: any policy error → blocked
      return blockExec(
        skillName,
        toolName,
        `Policy check failed for "${action}": ${err instanceof Error ? err.message : String(err)}`,
        0,
      );
    }

    // Handle policy decision
    switch (policyResult.decision) {
      case 'deny':
        return blockExec(skillName, toolName, policyResult.reason, 0);
      case 'needs_approval': {
        const approval = submitApproval({
          id: `app_${skillName}_${toolName}_${Date.now()}`,
          action: `${action}${policyCtx.command ? `: ${policyCtx.command.slice(0, 80)}` : ''}`,
          reason: policyResult.reason,
          riskLevel: policyResult.riskLevel,
          affectedPaths: policyResult.affectedPaths,
        });
        return reqApprovalExec(skillName, toolName, policyResult.reason, approval.id);
      }
      case 'allow':
        break; // proceed to executor
    }

    return executor(toolName, input, context);
  }

  /**
   * List all registered skills.
   */
  list(): SkillManifest[] {
    return Array.from(this.skills.values());
  }

  /**
   * List skills by category.
   */
  listByCategory(category: SkillCategory): SkillManifest[] {
    return this.list().filter(s => s.category === category);
  }

  /**
   * List skills by risk level.
   */
  listByRiskLevel(riskLevel: SkillManifest['riskLevel']): SkillManifest[] {
    return this.list().filter(s => s.riskLevel === riskLevel);
  }

  /**
   * Get only enabled skills (defaultEnabled = true).
   */
  listEnabled(): SkillManifest[] {
    return this.list().filter(s => s.defaultEnabled);
  }

  /**
   * Check if a skill is registered.
   */
  has(name: string): boolean {
    return this.skills.has(name);
  }

  /**
   * Get total count of registered skills.
   */
  get size(): number {
    return this.skills.size;
  }

  /**
   * Clear all registered skills (for testing).
   */
  clear(): void {
    this.skills.clear();
  }
}

// Singleton instance
const registry = new SkillRegistry();

export default registry;

// ============================================================
// Built-in Skills Registration
// ============================================================

import { manifest as filesystem } from '../skills/filesystem/index.js';
import { manifest as shell } from '../skills/shell/index.js';
import { manifest as git } from '../skills/git/index.js';
import { manifest as repoScanner } from '../skills/repo-scanner/index.js';
import { execute as fsExec } from '../skills/filesystem/index.js';
import { execute as shellExec } from '../skills/shell/index.js';
import { execute as gitExec } from '../skills/git/index.js';
import { execute as scannerExec } from '../skills/repo-scanner/index.js';

registry.registerAll([
  filesystem,
  shell,
  git,
  repoScanner,
]);

// Register executors
registry.registerExecutor('filesystem', fsExec);
registry.registerExecutor('shell', shellExec);
registry.registerExecutor('git', gitExec);
registry.registerExecutor('repo-scanner', scannerExec);

export { SkillRegistry };
