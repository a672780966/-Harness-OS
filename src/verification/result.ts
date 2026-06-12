/**
 * Harness OS — Verification Result (Structured)
 *
 * VER3-01: Structured verification result — single source of truth.
 * JSON is the authoritative state; Markdown is for reading only.
 *
 * Design:
 * - verificationId + schemaVersion for schema evolution
 * - projectId / taskId / runId for binding
 * - sourceCommit / sourceTree for codebase binding
 * - stepResults with per-step status
 * - integrity hash to detect tampering
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §9
 *            03_VERIFICATION_DELIVERY_STRONG_BINDING_FIX.md §4
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
  sourceTree?: string;
  status: 'passed' | 'failed' | 'partial' | 'skipped';
  requiredSteps: number;
  stepResults: VerificationStep[];
  startedAt: string;
  finishedAt: string;
  reportPath: string;
  /** SHA-256 hex of key binding fields — tamper detection. */
  integrity: string;
}

// ============================================================
// Integrity computation
// ============================================================

/**
 * Compute integrity hash over the binding-critical fields.
 * This lets consumers verify the result hasn't been re-targeted.
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
    result.status,
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

/** Get the current git tree hash (the hash of the working tree as staged). */
export function getCurrentTree(projectPath: string): string | undefined {
  try {
    return execSync('git rev-parse HEAD:',
      { cwd: projectPath, encoding: 'utf-8', timeout: 5000 }).trim();
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
export function saveVerificationResult(
  result: VerificationResult,
  projectPath: string,
): string {
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
export function loadVerificationResult(
  projectPath: string,
  verificationId: string,
): VerificationResult | undefined {
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
 * Checks:
 * - Fields are present
 * - projectId matches
 * - taskId matches (if expected)
 * - runId matches (if expected)
 * - sourceCommit matches current HEAD
 * - sourceTree matches current tree
 * - integrity hash is valid
 * - status is 'passed'
 * - Not expired (freshness — within 24h by default)
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

  // 1. Integrity check
  const { integrity: _storedIntegrity, ...resultWithoutIntegrity } = result;
  const computedIntegrity = computeIntegrity(resultWithoutIntegrity);
  if (_storedIntegrity !== computedIntegrity) {
    reasons.push(`Integrity mismatch: stored=${_storedIntegrity.slice(0, 12)} computed=${computedIntegrity.slice(0, 12)}`);
  }

  // 2. projectId
  if (result.projectId !== expected.projectId) {
    reasons.push(`Project mismatch: result=${result.projectId} expected=${expected.projectId}`);
  }

  // 3. taskId (if expected)
  if (expected.taskId && result.taskId !== expected.taskId) {
    reasons.push(`Task mismatch: result=${result.taskId ?? '(none)'} expected=${expected.taskId}`);
  }

  // 4. runId (if expected)
  if (expected.runId && result.runId !== expected.runId) {
    reasons.push(`Run mismatch: result=${result.runId ?? '(none)'} expected=${expected.runId}`);
  }

  // 5. sourceCommit vs HEAD
  const currentCommit = getCurrentCommit(expected.projectPath);
  if (result.sourceCommit && currentCommit) {
    if (result.sourceCommit !== currentCommit) {
      reasons.push(`Commit mismatch: result=${result.sourceCommit.slice(0, 12)} HEAD=${currentCommit.slice(0, 12)}`);
    }
  }

  // 6. sourceTree
  const currentTree = getCurrentTree(expected.projectPath);
  if (result.sourceTree && currentTree) {
    if (result.sourceTree !== currentTree) {
      reasons.push(`Tree mismatch: result=${result.sourceTree.slice(0, 12)} tree=${currentTree.slice(0, 12)}`);
    }
  }

  // 7. Status must be passed
  if (result.status !== 'passed') {
    reasons.push(`Verification status is "${result.status}", not "passed"`);
  }

  // 8. Freshness (not expired)
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
