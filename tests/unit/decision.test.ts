/**
 * Harness OS — Decision Manager Tests
 *
 * Coverage:
 * - proposeDecision: creates ADR files, auto-increment ID, markdown sections
 * - acceptDecision / rejectDecision: status transitions, edge cases
 * - supersedeDecision: marks old as superseded
 * - listDecisions / listActiveDecisions: query, filtering
 * - loadDecision: by ADR ID
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §8
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync, readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import { createProject } from '../../src/project/create.js';

import {
  proposeDecision,
  acceptDecision,
  rejectDecision,
  supersedeDecision,
  listDecisions,
  listActiveDecisions,
  loadDecision,
} from '../../src/decision/index.js';

import {
  submitApproval,
  resolveApproval,
  __test_clearStore,
} from '../../src/governance/approval-gate.js';

let testDir: string;

/**
 * Create an approved approval for ADR accept/supersede actions (P0-003).
 * Returns the approval ID for use with acceptDecision / supersedeDecision.
 */
function createAdrApproval(adrId: string, action: 'accept_adr' | 'supersede_adr', extraInput?: Record<string, string>): string {
  const approvalId = `test_aprv_${Date.now().toString(36)}`;
  const input: Record<string, unknown> = { action, adrId, ...extraInput };
  submitApproval({
    id: approvalId,
    action,
    reason: `Test approval for ADR ${adrId}`,
    riskLevel: 'medium',
    toolName: 'decision',
    input,
  });
  resolveApproval(approvalId, { approved: true, resolvedBy: 'test-operator' });
  return approvalId;
}
let projectPath: string;
let base: ReturnType<typeof makeBase>;

function makeBase(overrides: Record<string, string> = {}) {
  return {
    projectPath,
    title: 'Use SQLite for state storage',
    type: 'architecture' as const,
    summary: 'Use SQLite for local state',
    context: 'We need persistent local state',
    decision: 'Adopt SQLite via better-sqlite3',
    ...overrides,
  };
}

beforeEach(async () => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-adr-test-'));
  projectPath = join(testDir, 'test-proj');
  await createProject({ name: 'test-proj', path: projectPath });
  __test_clearStore(); // Clear approval store between tests (P0-003)
  base = makeBase();
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Propose Tests
// ============================================================

describe('proposeDecision', () => {
  it('creates ADR-0001 with correct ID', () => {
    const adr = proposeDecision(base);
    expect(adr.id).toBe('ADR-0001');
    expect(adr.number).toBe(1);
    expect(adr.status).toBe('proposed');
    expect(adr.title).toBe('Use SQLite for state storage');
  });

  it('creates both .md and .json files', () => {
    proposeDecision(base);
    const files = readdirSync(join(projectPath, '.project/decisions'));
    expect(files.some(f => f.startsWith('ADR-0001') && f.endsWith('.md'))).toBe(true);
    expect(files.some(f => f.startsWith('ADR-0001') && f.endsWith('.json'))).toBe(true);
  });

  it('markdown has all required sections', () => {
    proposeDecision({ ...base, consequences: ['More complex setup'], risks: ['Lock contention'] });
    const mdFile = readdirSync(join(projectPath, '.project/decisions')).find(f => f.startsWith('ADR-0001') && f.endsWith('.md'));
    const md = readFileSync(join(projectPath, '.project/decisions', mdFile!), 'utf-8');
    expect(md).toContain('ADR-0001: Use SQLite for state storage');
    expect(md).toContain('Status: proposed');
    expect(md).toContain('## Summary');
    expect(md).toContain('## Context');
    expect(md).toContain('## Decision');
    expect(md).toContain('## Consequences');
    expect(md).toContain('## Risks');
  });

  it('increments ADR numbers', () => {
    proposeDecision(base);
    proposeDecision(makeBase({ title: 'Second' }));
    proposeDecision(makeBase({ title: 'Third' }));
    const decisions = listDecisions(projectPath);
    expect(decisions).toHaveLength(3);
    expect(decisions[0].id).toBe('ADR-0003');
  });
});

// ============================================================
// Accept / Reject Tests
// ============================================================

describe('acceptDecision / rejectDecision', () => {
  it('accepts a proposed decision', () => {
    const proposed = proposeDecision(base);
    const apId = createAdrApproval(proposed.id, 'accept_adr');
    const accepted = acceptDecision(projectPath, proposed.id, apId, 'Tester');
    expect(accepted).toBeDefined();
    expect(accepted!.status).toBe('accepted');
    expect(accepted!.approvedBy).toBe('Tester');
    expect(accepted!.approvedAt).toBeTruthy();
  });

  it('rejects a proposed decision', () => {
    const proposed = proposeDecision(base);
    const rejected = rejectDecision(projectPath, proposed.id);
    expect(rejected).toBeDefined();
    expect(rejected!.status).toBe('rejected');
  });

  it('returns undefined for non-existent ADR', () => {
    expect(() => acceptDecision(projectPath, 'ADR-9999', 'ignored')).toThrow('approval');
  });

  it('returns undefined for already accepted ADR', () => {
    const proposed = proposeDecision(base);
    const ap1 = createAdrApproval(proposed.id, 'accept_adr');
    acceptDecision(projectPath, proposed.id, ap1, 'Op');
    const ap2 = createAdrApproval(proposed.id, 'accept_adr');
    expect(acceptDecision(projectPath, proposed.id, ap2, 'Op2')).toBeUndefined();
  });

  it('updates JSON file on accept', () => {
    const proposed = proposeDecision(base);
    const apId = createAdrApproval(proposed.id, 'accept_adr');
    acceptDecision(projectPath, proposed.id, apId, 'Admin');
    const loaded = loadDecision(projectPath, proposed.id);
    expect(loaded!.status).toBe('accepted');
    expect(loaded!.approvedBy).toBe('Admin');
  });

  it('updates Markdown file on accept', () => {
    const proposed = proposeDecision(base);
    const apId = createAdrApproval(proposed.id, 'accept_adr');
    acceptDecision(projectPath, proposed.id, apId, 'Admin');
    const files = readdirSync(join(projectPath, '.project/decisions')).filter(f => f.startsWith('ADR-0001') && f.endsWith('.md'));
    const md = readFileSync(join(projectPath, '.project/decisions', files[0]), 'utf-8');
    expect(md).toContain('Status: accepted');
    expect(md).toContain('Approved By: Admin');
  });
});

// ============================================================
// Supersede Tests
// ============================================================

describe('supersedeDecision', () => {
  it('marks an accepted ADR as superseded', () => {
    const old = proposeDecision(base);
    const ap1 = createAdrApproval(old.id, 'accept_adr');
    acceptDecision(projectPath, old.id, ap1, 'Admin');
    const ap2 = createAdrApproval(old.id, 'supersede_adr', { supersededBy: 'ADR-0002' });
    const updated = supersedeDecision(projectPath, old.id, 'ADR-0002', ap2);
    expect(updated).toBeDefined();
    expect(updated!.status).toBe('superseded');
    expect(updated!.supersededBy).toBe('ADR-0002');
  });
});

// ============================================================
// List Tests
// ============================================================

describe('listDecisions', () => {
  it('lists all decisions newest first', () => {
    proposeDecision(base);
    proposeDecision({ ...base, title: 'Second' });
    const list = listDecisions(projectPath);
    expect(list).toHaveLength(2);
    expect(list[0].number).toBeGreaterThan(list[1].number);
  });

  it('listActiveDecisions filters accepted only', () => {
    const a1 = proposeDecision(base);
    const a2 = proposeDecision(base);
    acceptDecision(projectPath, a1.id, createAdrApproval(a1.id, 'accept_adr'), 'Op');
    acceptDecision(projectPath, a2.id, createAdrApproval(a2.id, 'accept_adr'), 'Op');
    const a3 = proposeDecision(base);
    rejectDecision(projectPath, a3.id);

    const active = listActiveDecisions(projectPath);
    expect(active).toHaveLength(2);
    for (const d of active) expect(d.status).toBe('accepted');
  });
});

// ============================================================
// Load Tests
// ============================================================

describe('loadDecision', () => {
  it('loads decision by ADR ID', () => {
    const proposed = proposeDecision(base);
    const loaded = loadDecision(projectPath, proposed.id);
    expect(loaded).toBeDefined();
    expect(loaded!.id).toBe(proposed.id);
    expect(loaded!.title).toBe('Use SQLite for state storage');
    expect(loaded!.type).toBe('architecture');
  });

  it('returns undefined for unknown ADR', () => {
    expect(loadDecision(projectPath, 'ADR-9999')).toBeUndefined();
  });
});
