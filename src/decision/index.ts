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

// ============================================================
// Types
// ============================================================

export type DecisionStatus = 'proposed' | 'accepted' | 'rejected' | 'superseded';
export type DecisionType = 'architecture' | 'product' | 'technology' | 'security' | 'delivery' | 'governance' | 'process';

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

function getNextNumber(dir: string): number {
  if (!existsSync(dir)) return 1;
  let max = 0;
  for (const f of readdirSync(dir)) {
    const m = f.match(/^ADR-(\d+)/);
    if (m) max = Math.max(max, parseInt(m[1], 10));
  }
  return max + 1;
}

function fmtId(n: number): string { return `ADR-${String(n).padStart(4, '0')}`; }
function fmtFile(title: string): string { return title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60); }

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
    id, number: num, title: params.title, status: 'proposed', type: params.type,
    summary: params.summary, context: params.context, decision: params.decision,
    consequences: params.consequences ?? [], risks: params.risks ?? [],
    supersedes: params.supersedes, createdAt: now, updatedAt: now,
  };

  // Update superseded ADR if applicable
  if (params.supersedes && state.status === 'proposed') {
    const old = loadDecision(params.projectPath, params.supersedes);
    if (old) {
      old.status = 'superseded';
      old.supersededBy = id;
      old.updatedAt = now;
      saveDecision(params.projectPath, old);
    }
  }

  const mdPath = join(dir, `${id}-${fmtFile(params.title)}.md`);
  const jsonPath = join(dir, `${id}.json`);
  writeFileSync(mdPath, redactText(generateAdrMarkdown(state)), 'utf-8');
  safeWriteJson(jsonPath, state, 2);
  return state;
}

/**
 * Accept a proposed ADR.
 */
export function acceptDecision(projectPath: string, adrId: string, approvedBy?: string): DecisionState | undefined {
  const state = loadDecision(projectPath, adrId);
  if (!state || state.status !== 'proposed') return undefined;
  const now = new Date().toISOString();
  state.status = 'accepted';
  state.updatedAt = now;
  state.approvedBy = approvedBy;
  state.approvedAt = now;
  saveDecision(projectPath, state);
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
 */
export function supersedeDecision(projectPath: string, adrId: string, supersededBy: string): DecisionState | undefined {
  const state = loadDecision(projectPath, adrId);
  if (!state) return undefined;
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
  try { return JSON.parse(readFileSync(jsonPath, 'utf-8')); }
  catch { return undefined; }
}

function saveDecision(projectPath: string, state: DecisionState): void {
  const dir = getDecisionsDir(projectPath);
  const jsonPath = join(dir, `${state.id}.json`);
  safeWriteJson(jsonPath, state, 2);

  // Also update the markdown file
  const files = readdirSync(dir).filter(f => f.startsWith(state.id + '-') && f.endsWith('.md'));
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
    .filter(f => f.endsWith('.json'))
    .map(f => { try { return JSON.parse(readFileSync(join(dir, f), 'utf-8')); } catch { return null; } })
    .filter((d): d is DecisionState => d !== null)
    .sort((a, b) => b.number - a.number);
}

/**
 * List active (accepted) decisions only.
 */
export function listActiveDecisions(projectPath: string): DecisionState[] {
  return listDecisions(projectPath).filter(d => d.status === 'accepted');
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
    ...(state.consequences.length > 0 ? state.consequences.map(c => `- ${c}`) : ['(none documented)']),
    '',
    '## Risks',
    '',
    ...(state.risks.length > 0 ? state.risks.map(r => `- ${r}`) : ['(none identified)']),
    '',
    state.supersedes ? `## Supersedes\n\n${state.supersedes}\n` : '',
    state.approvedBy ? `## Approval\n\nApproved By: ${state.approvedBy}\nApproved At: ${state.approvedAt}\n` : '',
  ].filter(l => l !== undefined).join('\n');
}
