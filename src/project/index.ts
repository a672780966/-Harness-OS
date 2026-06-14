/**
 * Harness OS — Project Manager Module
 *
 * Phase 1-2: Project lifecycle + AGENTS.md validation.
 *
 * Sub-modules:
 * - create.ts           — Create a new Harness OS project
 * - open.ts             — Open an existing Harness OS project
 * - repair.ts           — Initialize or repair project structure
 * - agents-validator.ts — Validate AGENTS.md against 14-section standard
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §6
 *            03_AGENTS_MD_STANDARD.md
 */

export {
  createProject,
  type CreateProjectOptions,
  type CreateProjectResult,
  detectTechStack,
  buildRepositoryMap,
  type TechStack,
  type RepositoryMap,
} from './create.js';

export { openProject, type OpenProjectResult } from './open.js';

export { initProject, repairProject, type RepairResult } from './repair.js';

export {
  validateAgentsMd,
  canExecuteTask,
  type AgentsMdValidationResult,
  type SectionResult,
  type AgentsSection,
  REQUIRED_SECTIONS,
} from './agents-validator.js';
