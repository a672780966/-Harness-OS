/**
 * Harness OS — Skill Registry
 *
 * Central registry for all Harness OS skills.
 * Handles skill registration, manifest querying, and project-level enable/disable.
 *
 * Reference: 07_MCP_SKILLS_SPEC.md §6
 *
 * Governance: GOV-01 (AUD-P0-001), GOV3-01 (AUD3-P0-001), GOV4-01 (AUD4-P0-001)
 * - executors stored in closure-scoped WeakMap — no runtime-accessible getter.
 * - All skill executions pass through execute() which enforces:
 *     schema → canonical path/cwd → policy → approval binding → executor → audit
 * - _getExecutor() removed as per GOV4-01: no raw executor reachable from public API.
 */

import type { SkillManifest, SkillCategory } from '../types.js';
import type { SkillExecutor } from './executor.js';
import { checkPolicy, type PolicyContext } from '../governance/policy.js';
import {
  submitApproval,
  consumeApproval,
  validateApprovalBinding,
  getApproval,
} from '../governance/approval-gate.js';
import {
  failedResult as failExec,
  blockedResult as blockExec,
  requiresApprovalResult as reqApprovalExec,
} from './executor.js';

// ============================================================
// Closure-scoped executor store (GOV4-01)
//
// Using WeakMap keyed on the SkillRegistry instance makes
// executors unreachable from outside the module — no public
// getter, no property access at runtime.
// ============================================================

const EXECUTOR_MAP = new WeakMap<SkillRegistry, Map<string, SkillExecutor>>();

function getExecutorMap(instance: SkillRegistry): Map<string, SkillExecutor> {
  let map = EXECUTOR_MAP.get(instance);
  if (!map) {
    map = new Map();
    EXECUTOR_MAP.set(instance, map);
  }
  return map;
}

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
   * Executors stored in closure-scoped WeakMap — no public getter (GOV4-01).
   */
  registerExecutor(name: string, executor: SkillExecutor): void {
    getExecutorMap(this).set(name, executor);
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
   * Execute a tool on a registered skill.
   *
   * Governance pipeline (GOV4-02):
   *   1. Manifest validation — unknown tool → blocked
   *   2. Policy check — allow/deny/needs_approval with timeout
   *   3. Approval binding/consumption — single-use, validated (GOV4-03)
   *   4. Executor — called only if all prior gates pass
   *   5. Executor result returned
   *
   * @param approvalId - Optional: if resuming from a previous needs_approval,
   *                     pass the approved approval ID for binding validation
   *                     and single-use consumption (GOV4-03).
   */
  async execute(
    skillName: string,
    toolName: string,
    input: Record<string, unknown>,
    context: import('./executor.js').SkillExecutionContext,
    approvalId?: string,
  ): Promise<import('./executor.js').SkillExecutionResult> {
    const executorMap = getExecutorMap(this);
    const executor = executorMap.get(skillName);
    if (!executor) {
      return failExec(skillName, toolName, new Error(`No executor registered for skill: ${skillName}`), 0);
    }

    // ---- GOV4-03: Approval resume path ----
    // If an approvalId is provided, the caller is resuming an approved
    // tool execution. We must consume the approval atomically and validate
    // bindings before proceeding.
    if (approvalId) {
      const approval = getApproval(approvalId);
      if (!approval) {
        return blockExec(skillName, toolName, `Approval "${approvalId}" not found`, 0);
      }

      // Validate binding: skill, tool, session, input digest
      const bindingErr = validateApprovalBinding(approval, {
        skillName,
        toolName,
        input,
        sessionId: context.sessionId,
      });
      if (bindingErr) {
        return blockExec(skillName, toolName, `Approval binding rejected: ${bindingErr}`, 0);
      }

      // Single-use consumption (GOV4-03): only one executor call per approval
      const consumed = consumeApproval(approvalId);
      if (!consumed) {
        return blockExec(skillName, toolName, `Approval "${approvalId}" cannot be consumed — already consumed, rejected, or expired`, 0);
      }

      // If operator modified the input, use that instead (GOV4-03)
      if (consumed.modifiedInput) {
        input = consumed.modifiedInput;
      }
      // Modified input must be re-validated — skip manifest/policy and go to executor
      return executor(toolName, input, context);
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

    // ---- Policy Gate (GOV4-02) ----
    const action = normalizeSkillAction(skillName, toolName);
    const policyCtx = buildSkillPolicyContext(skillName, toolName, input);

    let policyResult: import('../types.js').PolicyCheckResult;
    try {
      // Policy with timeout (GOV4-02: real timeout, not just type declaration)
      const policyPromise = checkPolicy(action, policyCtx);
      const timeoutMs = 5000; // 5-second policy timeout
      const timeoutPromise = new Promise<import('../types.js').PolicyCheckResult>((_, reject) =>
        setTimeout(() => reject(new Error('Policy check timed out')), timeoutMs)
      );
      policyResult = await Promise.race([policyPromise, timeoutPromise]);
    } catch (err) {
      // Fail closed: any policy error/timout → blocked
      return blockExec(
        skillName,
        toolName,
        `Policy check failed for "${action}": ${err instanceof Error ? err.message : String(err)}`,
        0,
      );
    }

    // Validate policy result structure (GOV3-02/GOV4-02):
    // must be allow|deny|needs_approval
    const validDecisions = ['allow', 'deny', 'needs_approval'];
    if (!policyResult || typeof policyResult.decision !== 'string' || !validDecisions.includes(policyResult.decision)) {
      return blockExec(
        skillName,
        toolName,
        `Policy returned invalid decision "${String(policyResult?.decision)}" for "${action}" — blocked (fail closed)`,
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
          // Strong binding (GOV3-03/GOV4-03)
          skillName,
          toolName,
          input,
          sessionId: context.sessionId,
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
    getExecutorMap(this).clear();
  }
}

// Singleton instance
const registry = new SkillRegistry();

export default registry;

// ============================================================
// Built-in Skills Registration
// ============================================================

// Skills self-register their executors via module-level side effects.
// _execute is NOT exported from skill modules — it's imported here
// and passed to registerExecutor(). No public API can reach raw executors.
import { manifest as filesystem, _register as fsRegister } from '../skills/filesystem/index.js';
import { manifest as shell, _register as shellRegister } from '../skills/shell/index.js';
import { manifest as git, _register as gitRegister } from '../skills/git/index.js';
import { manifest as repoScanner, _register as scannerRegister } from '../skills/repo-scanner/index.js';

registry.registerAll([
  filesystem,
  shell,
  git,
  repoScanner,
]);

// Use self-registration
fsRegister(registry);
shellRegister(registry);
gitRegister(registry);
scannerRegister(registry);

export { SkillRegistry };
