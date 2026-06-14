/**
 * Harness OS — Relevance Engine
 *
 * Phase 4.2: Score and match files, tests, and decisions for context inclusion.
 *
 * Scoring Rules (05_CONTEXT_ENGINEERING.md §21):
 *   explicit file mention     +100
 *   current git diff          +90
 *   test match                +80
 *   symbol match              +70
 *   keyword match in filename +60
 *   keyword match in content  +50
 *   recent task reference     +40
 *   decision reference        +40
 *   project state             +30
 *   old report                +10
 *
 * Priority Levels (05_CONTEXT_ENGINEERING.md §8):
 *   P0 (score >= 90) — must include
 *   P1 (score >= 60) — high priority
 *   P2 (score >= 30) — medium priority
 *   P3 (score < 30)  — low priority
 */

import type { FileContext, ContentMode, FileReason } from '../types.js';

// ============================================================
// Context Candidate
// ============================================================

export interface ContextCandidate {
  id: string;
  path: string;
  priority: number;
  score: number;
  reason: FileReason | string;
  estimatedTokens: number;
  contentMode: ContentMode;
}

// ============================================================
// Scoring
// ============================================================

const SCORE_EXPLICIT = 100;
const SCORE_GIT_DIFF = 90;
const SCORE_TEST_MATCH = 80;
const SCORE_SYMBOL_MATCH = 70;
const SCORE_KEYWORD_FILENAME = 60;
const SCORE_KEYWORD_CONTENT = 50;
const SCORE_TASK_REFERENCE = 40;
const SCORE_DECISION_REFERENCE = 40;
const SCORE_PROJECT_STATE = 30;
const SCORE_OLD_REPORT = 10;

// ============================================================
// Priority Mapping
// ============================================================

export function scoreToPriority(score: number): number {
  if (score >= 90) return 0; // P0
  if (score >= 60) return 1; // P1
  if (score >= 30) return 2; // P2
  return 3; // P3
}

export function priorityLabel(priority: number): string {
  return `P${priority}`;
}

export function isP0(score: number): boolean {
  return score >= 90;
}

// ============================================================
// Token Estimation
// ============================================================

/**
 * Estimate token count from text length.
 * Rule of thumb: ~4 chars per token for code/text.
 */
export function estimateTokens(text: string): number {
  return Math.ceil((text.length || 0) / 4);
}

// ============================================================
// Test File Matcher
// ============================================================

/**
 * Given a source file path, find the corresponding test file path.
 *
 * Rules (05_CONTEXT_ENGINEERING.md §7.6):
 *   src/foo.ts        → tests/foo.test.ts
 *   src/foo.ts        → src/foo.test.ts
 *   components/Button.tsx → components/Button.test.tsx
 */
export function matchTestFile(filePath: string): string[] {
  const candidates: string[] = [];
  const dir = filePath.includes('/') ? filePath.substring(0, filePath.lastIndexOf('/')) : '';
  const basename = filePath.includes('/') ? filePath.substring(filePath.lastIndexOf('/') + 1) : filePath;
  const dotIndex = basename.lastIndexOf('.');
  const name = dotIndex > 0 ? basename.substring(0, dotIndex) : basename;
  const ext = dotIndex > 0 ? basename.substring(dotIndex) : '';

  // src/foo.ts → tests/foo.test.ts
  if (dir.startsWith('src/') || dir === 'src') {
    const subpath = dir === 'src' ? '' : dir.substring(4) + '/';
    candidates.push(`tests/${subpath}${name}.test${ext}`);
    candidates.push(`tests/${subpath}${name}.spec${ext}`);
  }

  // src/foo.ts → src/foo.test.ts (co-located)
  candidates.push(`${dir}/${name}.test${ext}`);
  candidates.push(`${dir}/${name}.spec${ext}`);

  return candidates;
}

// ============================================================
// Keyword Extractor
// ============================================================

/**
 * Extract keywords from text for matching.
 * Returns lowercase words, filtering out common stop words.
 */
export function extractKeywords(text: string): string[] {
  const stopWords = new Set([
    'the',
    'a',
    'an',
    'is',
    'are',
    'was',
    'were',
    'be',
    'been',
    'being',
    'have',
    'has',
    'had',
    'do',
    'does',
    'did',
    'will',
    'would',
    'could',
    'should',
    'may',
    'might',
    'shall',
    'can',
    'need',
    'dare',
    'ought',
    'to',
    'of',
    'in',
    'for',
    'on',
    'with',
    'at',
    'by',
    'from',
    'as',
    'into',
    'through',
    'during',
    'before',
    'after',
    'above',
    'below',
    'between',
    'out',
    'off',
    'over',
    'under',
    'again',
    'further',
    'then',
    'once',
    'here',
    'there',
    'when',
    'where',
    'why',
    'how',
    'all',
    'each',
    'every',
    'both',
    'few',
    'more',
    'most',
    'other',
    'some',
    'such',
    'no',
    'nor',
    'not',
    'only',
    'own',
    'same',
    'so',
    'than',
    'too',
    'very',
    'and',
    'but',
    'or',
    'because',
    'since',
    'until',
    'while',
    'if',
  ]);

  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((w) => w.length >= 3 && !stopWords.has(w));
}

// ============================================================
// Score a candidate file
// ============================================================

export interface ScoreInput {
  filePath: string;
  explicitFiles: string[];
  gitChangedFiles: string[];
  taskKeywords: string[];
  isTestFile?: boolean;
  isDecisionFile?: boolean;
}

/**
 * Score a file for relevance to the current task.
 */
export function scoreFile(input: ScoreInput): ContextCandidate {
  let score = 0;
  let reason: FileReason = 'keyword-match';
  const { filePath } = input;

  // Check explicit mention
  if (input.explicitFiles.some((f) => filePath.includes(f) || f.includes(filePath))) {
    score += SCORE_EXPLICIT;
    reason = 'explicit';
  }

  // Check git diff
  if (input.gitChangedFiles.some((f) => filePath.includes(f) || f.includes(filePath))) {
    score += SCORE_GIT_DIFF;
    if (reason === 'keyword-match') reason = 'git-diff';
  }

  // Check test match
  if (input.isTestFile) {
    score += SCORE_TEST_MATCH;
    if (reason === 'keyword-match') reason = 'test-match';
  }

  // Check decision file
  if (input.isDecisionFile) {
    score += SCORE_DECISION_REFERENCE;
    if (reason === 'keyword-match') reason = 'decision-reference';
  }

  // Check keyword match in filename
  const fileName = filePath.split('/').pop()?.toLowerCase() || '';
  for (const kw of input.taskKeywords) {
    if (fileName.includes(kw)) {
      score += SCORE_KEYWORD_FILENAME;
      break;
    }
  }

  // Determine content mode based on score
  let contentMode: ContentMode;
  if (score >= SCORE_EXPLICIT) {
    contentMode = 'full';
  } else if (score >= SCORE_GIT_DIFF) {
    contentMode = 'full';
  } else if (score >= SCORE_TEST_MATCH) {
    contentMode = 'full';
  } else if (score >= SCORE_KEYWORD_FILENAME) {
    contentMode = 'excerpt';
  } else {
    contentMode = 'metadata-only';
  }

  return {
    id: filePath,
    path: filePath,
    priority: scoreToPriority(score),
    score,
    reason,
    estimatedTokens: 0,
    contentMode,
  };
}

// ============================================================
// Sort candidates by score (highest first)
// ============================================================

export function sortCandidates(candidates: ContextCandidate[]): ContextCandidate[] {
  return [...candidates].sort((a, b) => b.score - a.score);
}

/**
 * Convert a ContextCandidate to a FileContext (with file content).
 */
export function candidateToFileContext(candidate: ContextCandidate, content?: string): FileContext {
  return {
    path: candidate.path,
    reason: candidate.reason as FileReason,
    priority: candidate.priority,
    contentMode: candidate.contentMode,
    content: candidate.contentMode === 'full' ? content : undefined,
    excerpt: candidate.contentMode === 'excerpt' ? content?.slice(0, 500) : undefined,
  };
}
