/**
 * Harness OS — Context Budget Manager
 *
 * Phase 4.4: Token estimation and priority-based trimming.
 *
 * Design (05_CONTEXT_ENGINEERING.md §10):
 * - Default budget: 70% context, 20% response, 10% tool results
 * - Token estimation: Math.ceil(text.length / 4)
 * - Trimming order: P3 → P2 → P1, P0 preserved but may be summarized
 * - Must not delete: current task, AGENTS.md core rules, git status, explicit files
 */

import type { ContextBudget } from '../types.js';
import type { ContextCandidate } from './relevance.js';

// ============================================================
// Default Budget
// ============================================================

export const DEFAULT_MAX_TOKENS = 128_000; // Claude default
export const DEFAULT_RESERVE_RESPONSE = 0.2; // 20%
export const DEFAULT_RESERVE_TOOL_RESULTS = 0.1; // 10%

// ============================================================
// Token Estimation
// ============================================================

/**
 * Estimate token count from text length.
 * ~4 characters per token for code/English text.
 */
export function estimateTokenCount(text: string): number {
  return Math.ceil((text.length || 0) / 4);
}

/**
 * Estimate tokens for a set of file candidates.
 */
export function estimateCandidatesTokens(candidates: ContextCandidate[]): number {
  return candidates.reduce((sum, c) => sum + (c.estimatedTokens || 0), 0);
}

// ============================================================
// Budget Calculation
// ============================================================

export interface BudgetConfig {
  /** Maximum total context tokens (default: 128k). */
  maxTokens?: number;
  /** Fraction reserved for model response (default: 0.20). */
  reserveResponse?: number;
  /** Fraction reserved for tool results (default: 0.10). */
  reserveToolResults?: number;
}

export function calculateBudget(config?: BudgetConfig): ContextBudget {
  const maxTokens = config?.maxTokens ?? DEFAULT_MAX_TOKENS;
  const reserveResponse = config?.reserveResponse ?? DEFAULT_RESERVE_RESPONSE;
  const reserveToolResults = config?.reserveToolResults ?? DEFAULT_RESERVE_TOOL_RESULTS;

  return {
    maxTokens,
    estimatedTokens: 0,
    reservedForResponse: Math.floor(maxTokens * reserveResponse),
    reservedForToolResults: Math.floor(maxTokens * reserveToolResults),
    trimmingApplied: false,
  };
}

// ============================================================
// Available budget for context (after reserves)
// ============================================================

export function availableContextTokens(budget: ContextBudget): number {
  return budget.maxTokens - budget.reservedForResponse - budget.reservedForToolResults;
}

// ============================================================
// Trimming
// ============================================================

export interface TrimResult {
  candidates: ContextCandidate[];
  removed: ContextCandidate[];
  trimmed: ContextCandidate[];
  budget: ContextBudget;
}

/**
 * Trim candidates to fit within the context budget.
 *
 * Trimming strategy:
 *   1. Remove P3 metadata-only candidates
 *   2. Convert P3 summaries to metadata-only
 *   3. Remove P2 older report candidates
 *   4. Convert P2 full → summary
 *   5. Convert P1 full → excerpt
 *   6. P0 preserved but may be summarized
 *
 * Never removes: current task, AGENTS.md, git status, explicit files.
 */
export function trimToBudget(
  candidates: ContextCandidate[],
  budget: ContextBudget,
  preserveP0: string[] = [],
): TrimResult {
  const removed: ContextCandidate[] = [];
  const trimmed: ContextCandidate[] = [];
  let estimated = estimateCandidatesTokens(candidates);
  const available = availableContextTokens(budget);

  if (estimated <= available) {
    budget.estimatedTokens = estimated;
    budget.trimmingApplied = false;
    return { candidates, removed, trimmed, budget };
  }

  // Strategy 1: Remove P3 metadata-only
  const p3Metadata = candidates.filter((c) => c.priority >= 3 && c.contentMode === 'metadata-only');
  for (const c of p3Metadata) {
    if (estimated <= available) break;
    candidates = candidates.filter((x) => x.id !== c.id);
    removed.push(c);
    estimated -= c.estimatedTokens || 0;
  }

  // Strategy 2: Convert P3 full → metadata-only
  const p3Full = candidates.filter((c) => c.priority >= 3 && c.contentMode === 'full');
  for (const c of p3Full) {
    if (estimated <= available) break;
    const idx = candidates.findIndex((x) => x.id === c.id);
    if (idx >= 0) {
      candidates[idx] = { ...c, contentMode: 'metadata-only', estimatedTokens: Math.min(c.estimatedTokens, 50) };
      trimmed.push(c);
      estimated = estimateCandidatesTokens(candidates);
    }
  }

  // Strategy 3: Convert P2 full → excerpt (if still over budget)
  const p2Full = candidates.filter((c) => c.priority >= 2 && c.contentMode === 'full');
  for (const c of p2Full) {
    if (estimated <= available) break;
    const idx = candidates.findIndex((x) => x.id === c.id);
    if (idx >= 0) {
      candidates[idx] = { ...c, contentMode: 'excerpt', estimatedTokens: Math.min(c.estimatedTokens, 200) };
      trimmed.push(c);
      estimated = estimateCandidatesTokens(candidates);
    }
  }

  // Strategy 4: Convert P1 full → excerpt
  const p1Full = candidates.filter((c) => c.priority >= 1 && c.contentMode === 'full' && !preserveP0.includes(c.id));
  for (const c of p1Full) {
    if (estimated <= available) break;
    const idx = candidates.findIndex((x) => x.id === c.id);
    if (idx >= 0) {
      candidates[idx] = { ...c, contentMode: 'excerpt', estimatedTokens: Math.min(c.estimatedTokens, 400) };
      trimmed.push(c);
      estimated = estimateCandidatesTokens(candidates);
    }
  }

  budget.estimatedTokens = estimated;
  budget.trimmingApplied = true;

  return { candidates, removed, trimmed, budget };
}

/**
 * Build the final budget summary for the Context Pack.
 */
export function budgetToContextBudget(candidates: ContextCandidate[], config?: BudgetConfig): ContextBudget {
  const budget = calculateBudget(config);
  budget.estimatedTokens = estimateCandidatesTokens(candidates);
  return budget;
}
