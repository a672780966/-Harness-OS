/**
 * Harness OS — Verification Result (Structured)
 *
 * VER3-01: Structured verification result — single source of truth.
 * JSON is the authoritative state; Markdown is for reading only.
 *
 * VER4-01: Worktree digest tracks the actual working tree at verification time.
 * After verification, if any tracked file changes (staged or unstaged), the
 * digest changes and the verification result is invalidated.
 *
 * Design:
 * - verificationId + schemaVersion for schema evolution
 * - projectId / taskId / runId for binding
 * - sourceCommit / sourceTree / sourceWorktreeDigest / sourceStagedDigest
 *   for full codebase binding (VER4-01)
 * - stepResults with per-step status
 * - integrity hash to detect tampering
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §9
 *            03_VERIFICATION_DELIVERY_STRONG_BINDING_FIX.md §4
 *            03_VERIFICATION_WORKTREE_DELIVERY_BINDING_FIX.md §4
 */

import { existsSync, mkdirSync, readFileSync } from 'fs';
import { execSync } from 'child_process';
import { join, resolve } from 'path';
import { createHash } from 'crypto';
import type { VerificationStep } from './plan.js';
import { safeWriteJson } from '../governance/redactor.js';

// ============================================================
// Schema
// ============================================================

export const VERIFICATION_RESULT_SCHEMA_VERSION = '1.0.0';

export interface VerificationResult {
  verificationId: string;
  schemaVersion: string;
  projectId: string;
  taskId?: string;
  runId?: string;
  sourceCommit?: string;
  /** HEAD tree hash (for reference, not authoritative — VER4-01). */
  sourceTree?: string;
  /**
   * SHA-256 digest of the working tree at verification time.
   * Computed over current tracked file contents (staged modifications,
   * unstaged modifications, renames, and deletions).
   * Excludes: node_modules, dist, coverage, .git, .project/**
   * VER4-01: This is the authoritative "the code hasn't changed" proof.
   */
  sourceWorktreeDigest?: string;
  /**
   * SHA-256 digest of the index/staging area.
   */
  sourceStagedDigest?: string;
  status: 'passed' | 'failed' | 'partial' | 'skipped';
  requiredSteps: number;
  stepResults: VerificationStep[];
  startedAt: string;
  finishedAt: string;
  reportPath: string;
  /** SHA-256 hex of key binding fields — tamper detection (VER4-03). */
  integrity: string;
}

// ============================================================
// Integrity computation
// ============================================================

/**
 * Compute integrity hash over the binding-critical fields.
 * This lets consumers verify the result hasn't been re-targeted.
 *
 * VER4-03: Covers all security-relevant fields — identity, source state,
 * step results, required steps, timestamps, and report path.
 * NOTE: This is an integrity hash, NOT a signature. It detects accidental
 * or casual tampering. Authenticity requires the controlled-load path
 * (loadVerificationResult from the guarded directory) combined with
 * identity binding and freshness checks — not just the hash alone.
 */
export function computeIntegrity(result: Omit<VerificationResult, 'integrity'>): string {
  const payload = [
    result.verificationId,
    result.schemaVersion,
    result.projectId,
    result.taskId ?? '',
    result.runId ?? '',
    result.sourceCommit ?? '',
    result.sourceTree ?? '',
    result.sourceWorktreeDigest ?? '',
    result.sourceStagedDigest ?? '',
    result.status,
    String(result.requiredSteps),
    JSON.stringify(result.stepResults.map((s) => `${s.name}:${s.status}:${s.exitCode}`)),
    result.startedAt,
    result.finishedAt,
    result.reportPath,
  ].join('|');
  return createHash('sha256').update(payload).digest('hex');
}

// ============================================================
// Git helpers
// ============================================================

/** Get the current commit hash, or undefined if not a git repo. */
export function getCurrentCommit(projectPath: string): string | undefined {
  try {
    return execSync('git rev-parse HEAD', { cwd: projectPath, encoding: 'utf-8' }).trim();
  } catch {
    return undefined;
  }
}

// ============================================================
// Worktree & Staged Digest (VER4-01)
//
// Instead of using git rev-parse HEAD: (which only reflects the
// committed tree), we compute SHA-256 digests over the actual
// working tree and staging area content.
//
// For working tree: hash git diff and git diff --cached output
// (which captures all unstaged and staged modifications).
// For staged: hash git diff --cached --no-color output.
//
// Excluded paths: node_modules/, dist/, coverage/, .git/, .project/
// These are runtime artifacts, not source code.
// ============================================================

const EXCLUDE_PATTERNS = ['node_modules', 'dist', 'coverage', '.git', '.project'];

/**
 * Check if a path should be excluded from the worktree digest.
 */
function isExcluded(filePath: string): boolean {
  const normalized = filePath.replace(/\\/g, '/');
  for (const pattern of EXCLUDE_PATTERNS) {
    if (normalized === pattern || normalized.startsWith(pattern + '/') || normalized.includes('/' + pattern + '/')) {
      return true;
    }
  }
  return false;
}

/**
 * Bind verification to exact working-tree bytes, including untracked files.
 * Runtime artifact directories remain excluded from the security boundary.
 */
export function computeWorktreeDigest(projectPath: string): string | undefined {
  try {
    const filesOutput = execSync('git ls-files --cached --others --exclude-standard -z', {
      cwd: projectPath,
      encoding: 'buffer',
      maxBuffer: 50 * 1024 * 1024,
    });
    const files = filesOutput
      .toString('utf-8')
      .split('\0')
      .filter(Boolean)
      .filter((filePath) => !isExcluded(filePath))
      .sort();
    const hash = createHash('sha256');

    for (const filePath of files) {
      hash.update(`path:${filePath}\0`);
      try {
        hash.update(readFileSync(join(projectPath, filePath)));
      } catch {
        hash.update('unreadable');
      }
      hash.update('\0');
    }

    return hash.digest('hex');
  } catch {
    return undefined;
  }
}

/**
 * Bind verification to the exact Git index using its content-addressed blobs.
 */
export function computeStagedDigest(projectPath: string): string | undefined {
  try {
    const indexOutput = execSync('git ls-files --stage -z', {
      cwd: projectPath,
      encoding: 'buffer',
      maxBuffer: 50 * 1024 * 1024,
    });
    const records = indexOutput
      .toString('utf-8')
      .split('\0')
      .filter(Boolean)
      .filter((record) => {
        const tabIdx = record.indexOf('\t');
        return tabIdx >= 0 && !isExcluded(record.slice(tabIdx + 1));
      })
      .sort();
    const hash = createHash('sha256');

    for (const record of records) {
      hash.update(record);
      hash.update('\0');
    }

    return hash.digest('hex');
  } catch {
    return undefined;
  }
}

/**
 * Get the HEAD tree hash (for reference/backward compat, VER4-01).
 * This is NOT authoritative — use computeWorktreeDigest for binding.
 */
export function getCurrentTree(projectPath: string): string | undefined {
  try {
    return execSync('git rev-parse HEAD:', { cwd: projectPath, encoding: 'utf-8', timeout: 5000 }).trim();
  } catch {
    return undefined;
  }
}

// ============================================================
// Save / Load
// ============================================================

const VERIFICATION_RESULT_FILENAME = 'verification.json';

/**
 * Directory where structured verification results are stored.
 * Alongside the Markdown reports in .project/reports/verification/.
 */
export function getVerificationResultDir(projectPath: string): string {
  return join(resolve(projectPath), '.project/reports/verification');
}

/**
 * Get the file path for a verification result JSON.
 */
export function getVerificationResultPath(verDir: string, verificationId: string): string {
  return join(verDir, `${verificationId}.${VERIFICATION_RESULT_FILENAME}`);
}

/**
 * Save a structured verification result to disk.
 * Markdown consumers can still use the .md; JSON is the binding source of truth.
 */
export function saveVerificationResult(result: VerificationResult, projectPath: string): string {
  const verDir = getVerificationResultDir(projectPath);
  if (!existsSync(verDir)) {
    mkdirSync(verDir, { recursive: true });
  }

  const filePath = getVerificationResultPath(verDir, result.verificationId);
  const toStore = {
    ...result,
    integrity: result.integrity || computeIntegrity(result),
  };
  safeWriteJson(filePath, toStore, 2);
  return filePath;
}

/**
 * Load a structured verification result from disk.
 * Returns undefined if the file doesn't exist or is malformed.
 */
export function loadVerificationResult(projectPath: string, verificationId: string): VerificationResult | undefined {
  const verDir = getVerificationResultDir(projectPath);
  const filePath = getVerificationResultPath(verDir, verificationId);
  if (!existsSync(filePath)) return undefined;

  try {
    const parsed = JSON.parse(readFileSync(filePath, 'utf-8')) as VerificationResult;
    return parsed;
  } catch {
    return undefined;
  }
}

// ============================================================
// Binding Validation (VER3-02 / VER3-04)
// ============================================================

export interface BindingCheckResult {
  valid: boolean;
  reasons: string[];
}

/**
 * Validate that a verification result matches the current build context.
 * All binding fields are checked against the expected values.
 *
 * VER4-01/VER4-02: Full identity binding:
 * - projectId is checked against the caller's expected project (not the result's own field)
 * - taskId, runId must match if expected
 * - sourceCommit must match HEAD
 * - sourceWorktreeDigest must match current worktree (VER4-01)
 * - sourceStagedDigest must match current staged state
 * - No field is optional for success — all must be present and matching
 *   (if in a git repo). Non-git repos are blocked.
 * - integrity hash is validated
 * - status must be 'passed'
 * - freshness check
 *
 * @param result - Loaded verification result from disk
 * @param expected - Expected identity values from the CURRENT context
 * @returns BindingCheckResult with valid flag and detailed reasons
 */
export function checkVerificationBinding(
  result: VerificationResult,
  expected: {
    projectId: string;
    taskId?: string;
    runId?: string;
    projectPath: string;
    maxAgeMs?: number;
  },
): BindingCheckResult {
  const reasons: string[] = [];
  const maxAge = expected.maxAgeMs ?? 24 * 60 * 60 * 1000; // 24h

  // 1. Integrity check (VER4-03)
  const { integrity: _storedIntegrity, ...resultWithoutIntegrity } = result;
  const computedIntegrity = computeIntegrity(resultWithoutIntegrity);
  if (_storedIntegrity !== computedIntegrity) {
    reasons.push(
      `Integrity mismatch: stored=${_storedIntegrity.slice(0, 12)} computed=${computedIntegrity.slice(0, 12)}`,
    );
  }

  // 2. projectId — compared against CALLER's expected (VER4-02)
  if (!expected.projectId) {
    reasons.push('No expected projectId provided for binding check');
  } else if (!result.projectId) {
    reasons.push('Verification result has no projectId');
  } else if (result.projectId !== expected.projectId) {
    reasons.push(`Project mismatch: result=${result.projectId} expected=${expected.projectId}`);
  }

  // 3. taskId (VER4-02: required for binding, not optional for success)
  if (expected.taskId) {
    if (!result.taskId) {
      reasons.push(`Verification result has no taskId (expected "${expected.taskId}")`);
    } else if (result.taskId !== expected.taskId) {
      reasons.push(`Task mismatch: result=${result.taskId} expected=${expected.taskId}`);
    }
  }

  // 4. runId (VER4-02: required for binding)
  if (expected.runId) {
    if (!result.runId) {
      reasons.push(`Verification result has no runId (expected "${expected.runId}")`);
    } else if (result.runId !== expected.runId) {
      reasons.push(`Run mismatch: result=${result.runId} expected=${expected.runId}`);
    }
  }

  // 5. Non-git repo check (VER4-02/VER4-04)
  const currentCommit = getCurrentCommit(expected.projectPath);
  const isGitRepo = currentCommit !== undefined;

  if (!isGitRepo) {
    reasons.push('Not a git repository — verification binding requires git');
  }

  // 6. sourceCommit vs HEAD
  if (isGitRepo && currentCommit) {
    if (!result.sourceCommit) {
      reasons.push('Verification result has no sourceCommit');
    } else if (result.sourceCommit !== currentCommit) {
      reasons.push(`Commit mismatch: result=${result.sourceCommit.slice(0, 12)} HEAD=${currentCommit.slice(0, 12)}`);
    }
  }

  // 7. HEAD tree hash (reference only, VER4-01)
  if (isGitRepo) {
    const currentTree = getCurrentTree(expected.projectPath);
    if (result.sourceTree && currentTree && result.sourceTree !== currentTree) {
      reasons.push(`HEAD tree mismatch: result=${result.sourceTree.slice(0, 12)} current=${currentTree.slice(0, 12)}`);
    }
  }

  // 8. Worktree digest (VER4-01) — THE authoritative "code hasn't changed" check
  if (isGitRepo) {
    const worktreeDigest = computeWorktreeDigest(expected.projectPath);
    if (!result.sourceWorktreeDigest) {
      reasons.push('Verification result has no sourceWorktreeDigest');
    } else if (!worktreeDigest) {
      reasons.push('Cannot compute worktree digest for binding check');
    } else if (result.sourceWorktreeDigest !== worktreeDigest) {
      reasons.push(
        `Worktree changed since verification: result=${result.sourceWorktreeDigest.slice(0, 12)} current=${worktreeDigest.slice(0, 12)}`,
      );
    }
  }

  // 9. Staged digest
  if (isGitRepo) {
    const stagedDigest = computeStagedDigest(expected.projectPath);
    if (!result.sourceStagedDigest) {
      reasons.push('Verification result has no sourceStagedDigest');
    } else if (!stagedDigest) {
      reasons.push('Cannot compute staged digest for binding check');
    } else if (result.sourceStagedDigest !== stagedDigest) {
      reasons.push(
        `Staged state changed since verification: result=${result.sourceStagedDigest.slice(0, 12)} current=${stagedDigest.slice(0, 12)}`,
      );
    }
  }

  // 10. Status must be passed
  if (result.status !== 'passed') {
    reasons.push(`Verification status is "${result.status}", not "passed"`);
  }

  // 11. Freshness (not expired)
  const finishedAt = new Date(result.finishedAt).getTime();
  if (isNaN(finishedAt)) {
    reasons.push('Verification result has invalid finishedAt timestamp');
  } else if (Date.now() - finishedAt > maxAge) {
    reasons.push(`Verification result expired (finished ${new Date(finishedAt).toISOString()})`);
  }

  return {
    valid: reasons.length === 0,
    reasons,
  };
}
