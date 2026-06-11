/**
 * Harness OS — Skill Registry
 *
 * Central registry for all Harness OS skills.
 * Handles skill registration, manifest querying, and project-level enable/disable.
 *
 * Reference: 07_MCP_SKILLS_SPEC.md §6
 */

import type { SkillManifest, SkillCategory } from '../types.js';
import type { SkillExecutor } from './executor.js';

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
   */
  async execute(
    skillName: string,
    toolName: string,
    input: Record<string, unknown>,
    context: import('./executor.js').SkillExecutionContext,
  ): Promise<import('./executor.js').SkillExecutionResult> {
    const executor = this.executors.get(skillName);
    if (!executor) {
      const { failedResult } = await import('./executor.js');
      return failedResult(skillName, toolName, new Error(`No executor registered for skill: ${skillName}`), 0);
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
