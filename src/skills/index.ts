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

/**
 * List all registered skills (formatted output).
 */
export async function listSkills(): Promise<void> {
  const skills = registry.list();
  console.log(`\nRegistered skills: ${skills.length}\n`);
  for (const skill of skills) {
    const tools = skill.tools.map(t => t.name).join(', ');
    console.log(`  ${skill.name} (${skill.category})`);
    console.log(`    ${skill.description}`);
    console.log(`    Risk: ${skill.riskLevel} | Enabled: ${skill.defaultEnabled} | Tools: ${tools}`);
    console.log();
  }
}
