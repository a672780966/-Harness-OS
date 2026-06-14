/**
 * Harness OS — Context Engineering Module
 *
 * Phase 4: Context Pack generation pipeline.
 *
 * Sub-modules:
 * - sources.ts   — Source collectors: AGENTS.md, project, git, task
 * - relevance.ts — Relevance engine: file scoring, test matching, keywords
 * - budget.ts    — Context budget manager: token estimation, trimming
 * - build.ts     — Context Pack assembler: collect → score → trim → save
 *
 * Reference: 05_CONTEXT_ENGINEERING.md
 */

export { collectAgentsMd, collectProject, collectGit, collectTask } from './sources.js';

export {
  scoreFile,
  sortCandidates,
  matchTestFile,
  extractKeywords,
  estimateTokens,
  scoreToPriority,
  candidateToFileContext,
  type ContextCandidate,
  type ScoreInput,
} from './relevance.js';

export {
  calculateBudget,
  estimateTokenCount,
  trimToBudget,
  availableContextTokens,
  budgetToContextBudget,
  type BudgetConfig,
  type TrimResult,
} from './budget.js';

export { buildContextPack, type BuildContextInput } from './build.js';
