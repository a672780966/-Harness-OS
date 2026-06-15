/**
 * Harness OS — Decision Manager
 *
 * Phase C: ADR lifecycle — propose, accept, reject, supersede, list.
 *
 * ADR files: .project/decisions/ADR-NNNN-title.md + .json
 * Status: proposed → accepted | rejected | superseded
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §8
 */

import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import { safeWriteJson, redactText } from '../governance/redactor.js';
import { getApproval, consumeApproval, computeInputDigest } from '../governance/approval-gate.js';

// ============================================================
// Types
// ============================================================

export type DecisionStatus = 'proposed' | 'accepted' | 'rejected' | 'superseded';
export type DecisionType =
  | 'architecture'
  | 'product'
  | 'technology'
  | 'security'
  | 'delivery'
  | 'governance'
  | 'process';

export interface DecisionState {
  id: string;
  number: number;
  title: string;
  status: DecisionStatus;
  type: DecisionType;
  summary: string;
  context: string;
  decision: string;
  consequences: string[];
  risks: string[];
  supersedes?: string;
  supersededBy?: string;
  createdAt: string;
  updatedAt: string;
  approvedBy?: string;
  approvedAt?: string;
}

// ============================================================
// Helpers
// ============================================================

function getDecisionsDir(projectPath: string): string {
  if (!projectPath) throw new Error(`getDecisionsDir: projectPath is undefined`);
  const resolved = resolve(projectPath);
  const dir = join(resolved, '.project/decisions');
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  return dir;
}

function getProjectId(projectPath: string): string {
  try {
    const manifestPath = resolve(projectPath, '.project/state/manifest.json');
    if (existsSync(manifestPath)) {
      const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
      return manifest.projectId || 'unknown';
    }
  } catch {
    /* fall through */
  }
  return 'unknown';
}

function getNextNumber(dir: string): number {
  if (!existsSync(dir)) return 1;
  let max = 0;
  for (const f of readdirSync(dir)) {
    const m = f.match(/^ADR-(\d+)/);
    if (m) max = Math.max(max, parseInt(m[1], 10));
  }
  return max + 1;
}

function fmtId(n: number): string {
  return `ADR-${String(n).padStart(4, '0')}`;
}
function fmtFile(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 60);
}

// ============================================================
// CRUD
// ============================================================

/**
 * Propose a new ADR.
 */
export function proposeDecision(params: {
  projectPath: string;
  title: string;
  type: DecisionType;
  summary: string;
  context: string;
  decision: string;
  consequences?: string[];
  risks?: string[];
  supersedes?: string;
}): DecisionState {
  const dir = getDecisionsDir(params.projectPath);
  const num = getNextNumber(dir);
  const id = fmtId(num);
  const now = new Date().toISOString();

  const state: DecisionState = {
    id,
    number: num,
    title: params.title,
    status: 'proposed',
    type: params.type,
    summary: params.summary,
    context: params.context,
    decision: params.decision,
    consequences: params.consequences ?? [],
    risks: params.risks ?? [],
    supersedes: params.supersedes,
    createdAt: now,
    updatedAt: now,
  };

  // ✅ Node 03: Do NOT mark superseded ADR here.
  //   The old ADR remains accepted until the new ADR is itself
  //   approved via acceptDecision() or supersedeDecision().
  //   Prematurely marking it superseded would let an unapproved
  //   proposal remove a valid architectural constraint.

  const mdPath = join(dir, `${id}-${fmtFile(params.title)}.md`);
  const jsonPath = join(dir, `${id}.json`);
  writeFileSync(mdPath, redactText(generateAdrMarkdown(state)), 'utf-8');
  safeWriteJson(jsonPath, state, 2);
  return state;
}

/**
 * Accept a proposed ADR.
 * Requires a valid, approved, unconsumed approval binding (P0-004).
 *
 * Validation order: verify all required fields → atomic consume → transition.
 * This ensures binding failures don't waste a consumed approval.
 *
 * @param projectPath - The project path
 * @param adrId - The ADR ID to accept
 * @param approvalId - The approval ID from the approval gate
 * @param approvedBy - Audit metadata only (not authorization)
 * @returns The updated DecisionState, or undefined if failed
 */
export function acceptDecision(
  projectPath: string,
  adrId: string,
  approvalId: string,
  approvedBy?: string,
): DecisionState | undefined {
  // P0-004: Step 1 — Get approval WITHOUT consuming
  const approval = getApproval(approvalId);
  if (!approval) {
    throw new Error(`Cannot accept ADR ${adrId}: approval "${approvalId}" not found. [P0-004: binding fail]`);
  }

  // P0-004: Step 2 — Validate all required binding fields BEFORE consumption
  const projectId = getProjectId(projectPath);
  const expectedInput = { action: 'accept_adr', adrId };
  const bindingErrors: string[] = [];

  // 2a. Required: projectId on both sides
  if (!projectId) bindingErrors.push('expected projectId is empty');
  if (!approval.projectId) bindingErrors.push('approval has no projectId');
  if (projectId && approval.projectId && approval.projectId !== projectId) {
    bindingErrors.push(`approval bound to project "${approval.projectId}", cannot use for "${projectId}"`);
  }

  // 2b. Required: toolName === 'decision' on both sides
  if (!approval.toolName) bindingErrors.push('approval has no toolName');
  if (approval.toolName && approval.toolName !== 'decision') {
    bindingErrors.push(`approval bound to tool "${approval.toolName}", expected "decision"`);
  }

  // 2c. Required: action must be accept_adr
  if (!approval.action) bindingErrors.push('approval has no action');
  if (approval.action && approval.action !== 'accept_adr') {
    bindingErrors.push(`approval action is "${approval.action}", expected "accept_adr"`);
  }

  // 2d. Required: input digest must match (catches adrId changes, content changes)
  if (!approval.inputDigest) bindingErrors.push('approval has no inputDigest');
  if (approval.inputDigest) {
    const expectedDigest = computeInputDigest(expectedInput);
    if (approval.inputDigest !== expectedDigest) {
      bindingErrors.push('approval input digest mismatch — adrId or input has changed since approval');
    }
  }

  // 2e. Required: status must be approved, not pending/rejected/expired
  if (approval.status !== 'approved') {
    bindingErrors.push(`approval status is "${approval.status}", expected "approved"`);
  }

  // 2f. Required: not already consumed
  if (approval.consumed) bindingErrors.push('approval already consumed (single-use)');

  // 2g. Required: not expired
  if (approval.expiresAt < new Date().toISOString()) {
    bindingErrors.push('approval has expired');
  }

  // Fail closed on any binding error (approval NOT consumed yet)
  if (bindingErrors.length > 0) {
    throw new Error(
      `Cannot accept ADR ${adrId}: approval binding failed — ${bindingErrors.join('; ')}. [P0-004: binding fail]`,
    );
  }

  // Step 3 — Atomically consume now that all validations pass
  const consumed = consumeApproval(approvalId);
  if (!consumed) {
    throw new Error(
      `Cannot accept ADR ${adrId}: approval "${approvalId}" was consumed by another caller between validation and consumption. [P0-004: race condition]`,
    );
  }

  // Step 4 — Transition ADR state
  const state = loadDecision(projectPath, adrId);
  if (!state || state.status !== 'proposed') return undefined;
  const now = new Date().toISOString();
  state.status = 'accepted';
  state.updatedAt = now;
  state.approvedBy = approvedBy;
  state.approvedAt = now;
  saveDecision(projectPath, state);

  // Step 5 — If this ADR supersedes another, mark the old one as superseded.
  //   This only happens after the new ADR is legitimately accepted, not
  //   at proposal time (prevents unapproved proposals from removing constraints).
  if (state.supersedes) {
    const oldAdr = loadDecision(projectPath, state.supersedes);
    if (oldAdr && oldAdr.status === 'accepted') {
      oldAdr.status = 'superseded';
      oldAdr.supersededBy = adrId;
      oldAdr.updatedAt = now;
      saveDecision(projectPath, oldAdr);
    }
  }

  return state;
}

/**
 * Reject a proposed ADR.
 */
export function rejectDecision(projectPath: string, adrId: string): DecisionState | undefined {
  const state = loadDecision(projectPath, adrId);
  if (!state || state.status !== 'proposed') return undefined;
  state.status = 'rejected';
  state.updatedAt = new Date().toISOString();
  saveDecision(projectPath, state);
  return state;
}

/**
 * Supersede an accepted ADR.
 * Requires a valid, approved, unconsumed approval binding (P0-004).
 */
export function supersedeDecision(
  projectPath: string,
  adrId: string,
  supersededBy: string,
  approvalId: string,
): DecisionState | undefined {
  // P0-004: Step 1 — Get approval WITHOUT consuming
  const approval = getApproval(approvalId);
  if (!approval) {
    throw new Error(`Cannot supersede ADR ${adrId}: approval "${approvalId}" not found. [P0-004: binding fail]`);
  }

  // P0-004: Step 2 — Validate all required binding fields BEFORE consumption
  const projectId = getProjectId(projectPath);
  const expectedInput = { action: 'supersede_adr', adrId, supersededBy };
  const bindingErrors: string[] = [];

  // 2a. Required: projectId on both sides
  if (!projectId) bindingErrors.push('expected projectId is empty');
  if (!approval.projectId) bindingErrors.push('approval has no projectId');
  if (projectId && approval.projectId && approval.projectId !== projectId) {
    bindingErrors.push(`approval bound to project "${approval.projectId}", cannot use for "${projectId}"`);
  }

  // 2b. Required: toolName === 'decision'
  if (!approval.toolName) bindingErrors.push('approval has no toolName');
  if (approval.toolName && approval.toolName !== 'decision') {
    bindingErrors.push(`approval bound to tool "${approval.toolName}", expected "decision"`);
  }

  // 2c. Required: action must be supersede_adr
  if (!approval.action) bindingErrors.push('approval has no action');
  if (approval.action && approval.action !== 'supersede_adr') {
    bindingErrors.push(`approval action is "${approval.action}", expected "supersede_adr"`);
  }

  // 2d. Required: input digest must match (catches adrId/supersededBy changes)
  if (!approval.inputDigest) bindingErrors.push('approval has no inputDigest');
  if (approval.inputDigest) {
    const expectedDigest = computeInputDigest(expectedInput);
    if (approval.inputDigest !== expectedDigest) {
      bindingErrors.push('approval input digest mismatch — input has changed since approval');
    }
  }

  // 2e. Required: status must be approved
  if (approval.status !== 'approved') {
    bindingErrors.push(`approval status is "${approval.status}", expected "approved"`);
  }

  // 2f. Required: not already consumed
  if (approval.consumed) bindingErrors.push('approval already consumed (single-use)');

  // 2g. Required: not expired
  if (approval.expiresAt < new Date().toISOString()) {
    bindingErrors.push('approval has expired');
  }

  // Fail closed — approval NOT consumed yet
  if (bindingErrors.length > 0) {
    throw new Error(
      `Cannot supersede ADR ${adrId}: approval binding failed — ${bindingErrors.join('; ')}. [P0-004: binding fail]`,
    );
  }

  // Step 3 — Atomically consume now that all validations pass
  const consumed = consumeApproval(approvalId);
  if (!consumed) {
    throw new Error(
      `Cannot supersede ADR ${adrId}: approval "${approvalId}" was consumed by another caller between validation and consumption. [P0-004: race condition]`,
    );
  }

  // Step 4 — Validate ADR lifecycle constraints (Node 03)
  const state = loadDecision(projectPath, adrId);
  if (!state) return undefined;
  if (state.status !== 'accepted') {
    throw new Error(
      `Cannot supersede ADR ${adrId}: status is "${state.status}", expected "accepted". [P0-004: lifecycle]`,
    );
  }

  // 4b. Validate supersededBy ADR exists and is accepted
  if (supersededBy) {
    const newAdr = loadDecision(projectPath, supersededBy);
    if (!newAdr) {
      throw new Error(
        `Cannot supersede ADR ${adrId}: supersededBy ADR "${supersededBy}" not found. [P0-004: lifecycle]`,
      );
    }
  }

  // Step 5 — Transition ADR state
  state.status = 'superseded';
  state.supersededBy = supersededBy;
  state.updatedAt = new Date().toISOString();
  saveDecision(projectPath, state);
  return state;
}

/**
 * Load a decision by ADR ID.
 */
export function loadDecision(projectPath: string, adrId: string): DecisionState | undefined {
  const dir = getDecisionsDir(projectPath);
  const jsonPath = join(dir, `${adrId}.json`);
  if (!existsSync(jsonPath)) return undefined;
  try {
    return JSON.parse(readFileSync(jsonPath, 'utf-8'));
  } catch {
    return undefined;
  }
}

function saveDecision(projectPath: string, state: DecisionState): void {
  const dir = getDecisionsDir(projectPath);
  const jsonPath = join(dir, `${state.id}.json`);
  safeWriteJson(jsonPath, state, 2);

  // Also update the markdown file
  const files = readdirSync(dir).filter((f) => f.startsWith(state.id + '-') && f.endsWith('.md'));
  if (files.length > 0) {
    let md = readFileSync(join(dir, files[0]), 'utf-8');
    md = md.replace(/^(Status: ).*/m, `Status: ${state.status}`);
    md = md.replace(/^(Updated At: ).*/m, `Updated At: ${state.updatedAt}`);
    if (state.approvedBy) {
      if (md.includes('Approved By:')) {
        md = md.replace(/^(Approved By:).*/m, `Approved By: ${state.approvedBy}`);
        md = md.replace(/^(Approved At:).*/m, `Approved At: ${state.approvedAt}`);
      } else {
        md += `\n## Approval\n\nApproved By: ${state.approvedBy}\nApproved At: ${state.approvedAt}\n`;
      }
    }
    writeFileSync(join(dir, files[0]), redactText(md), 'utf-8');
  }
}

/**
 * List all decisions, newest first.
 */
export function listDecisions(projectPath: string): DecisionState[] {
  const dir = getDecisionsDir(projectPath);
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith('.json'))
    .map((f) => {
      try {
        return JSON.parse(readFileSync(join(dir, f), 'utf-8'));
      } catch {
        return null;
      }
    })
    .filter((d): d is DecisionState => d !== null)
    .sort((a, b) => b.number - a.number);
}

/**
 * List active (accepted) decisions only.
 */
export function listActiveDecisions(projectPath: string): DecisionState[] {
  return listDecisions(projectPath).filter((d) => d.status === 'accepted');
}

// ============================================================
// Markdown Template
// ============================================================

function generateAdrMarkdown(state: DecisionState): string {
  return [
    `# ${state.id}: ${state.title}`,
    '',
    `Status: ${state.status}`,
    `Type: ${state.type}`,
    `Created At: ${state.createdAt}`,
    `Updated At: ${state.updatedAt}`,
    '',
    '## Summary',
    '',
    state.summary,
    '',
    '## Context',
    '',
    state.context,
    '',
    '## Decision',
    '',
    state.decision,
    '',
    '## Consequences',
    '',
    ...(state.consequences.length > 0 ? state.consequences.map((c) => `- ${c}`) : ['(none documented)']),
    '',
    '## Risks',
    '',
    ...(state.risks.length > 0 ? state.risks.map((r) => `- ${r}`) : ['(none identified)']),
    '',
    state.supersedes ? `## Supersedes\n\n${state.supersedes}\n` : '',
    state.approvedBy ? `## Approval\n\nApproved By: ${state.approvedBy}\nApproved At: ${state.approvedAt}\n` : '',
  ]
    .filter((l) => l !== undefined)
    .join('\n');
}
