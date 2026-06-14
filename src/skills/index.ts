/**
 * Harness OS — Skills Module
 *
 * Skill Registry and skill management.
 *
 * Reference: 07_MCP_SKILLS_SPEC.md §6
 */

export { default as registry } from './registry.js';
export { SkillRegistry } from './registry.js';
export type { SkillManifest, SkillToolManifest, SkillCategory, SkillPermission } from '../types.js';
export type { SkillExecutionContext, SkillExecutionResult, SkillExecutor } from './executor.js';

import registry from './registry.js';
import { redactText } from '../governance/redactor.js';

// ============================================================
// Structured skill data (CLI3-01)
// ============================================================

export interface SkillListEntry {
  name: string;
  category: string;
  description: string;
  riskLevel: string;
  defaultEnabled: boolean;
  tools: string[];
}

/**
 * Get structured skill list — does NOT print (CLI3-01).
 * The CLI layer formats and outputs via the formatter.
 */
export async function getSkillsList(): Promise<{ count: number; skills: SkillListEntry[] }> {
  const skills = registry.list();
  return {
    count: skills.length,
    skills: skills.map((s) => ({
      name: s.name,
      category: s.category,
      description: s.description,
      riskLevel: s.riskLevel,
      defaultEnabled: s.defaultEnabled,
      tools: s.tools.map((t) => t.name),
    })),
  };
}

/**
 * Legacy CLI helper. Prefer getSkillsList() + formatter for JSON mode.
 */
export async function listSkills(): Promise<void> {
  const data = await getSkillsList();
  console.log(redactText(`\nRegistered skills: ${data.count}\n`));
  for (const skill of data.skills) {
    const tools = skill.tools.join(', ');
    console.log(redactText(`  ${skill.name} (${skill.category})`));
    console.log(redactText(`    ${skill.description}`));
    console.log(redactText(`    Risk: ${skill.riskLevel} | Enabled: ${skill.defaultEnabled} | Tools: ${tools}`));
    console.log();
  }
}
