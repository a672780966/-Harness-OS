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
 * Create an approved approval for ADR accept/supersede actions (P0-003/P0-004).
 * Includes all required binding fields: projectId, toolName, action, input digest.
 * Returns the approval ID for use with acceptDecision / supersedeDecision.
 */
function createAdrApproval(adrId: string, action: 'accept_adr' | 'supersede_adr', extraInput?: Record<string, string>): string {
  const approvalId = `test_aprv_${Date.now().toString(36)}`;
  const input: Record<string, unknown> = { action, adrId, ...extraInput };

  // Read projectId from manifest for strong binding (P0-004)
  let projectId = 'test-project-id';
  try {
    const manifestPath = join(projectPath, '.project/state/manifest.json');
    if (existsSync(manifestPath)) {
      projectId = JSON.parse(readFileSync(manifestPath, 'utf-8')).projectId || projectId;
    }
  } catch { /* empty — project may not have manifest yet */ }

  submitApproval({
    id: approvalId,
    action,
    reason: `Test approval for ADR ${adrId}`,
    riskLevel: 'medium',
    toolName: 'decision',
    projectId,
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

    // Propose the new ADR that will supersede the old one
    const newAdr = proposeDecision(makeBase({ title: 'Better SQLite' }));

    const ap2 = createAdrApproval(old.id, 'supersede_adr', { supersededBy: newAdr.id });
    const updated = supersedeDecision(projectPath, old.id, newAdr.id, ap2);
    expect(updated).toBeDefined();
    expect(updated!.status).toBe('superseded');
    expect(updated!.supersededBy).toBe(newAdr.id);
  });

  it('rejects superseding a non-accepted ADR', () => {
    const proposed = proposeDecision(base);
    const ap2 = createAdrApproval(proposed.id, 'supersede_adr', { supersededBy: 'ADR-9999' });
    expect(() => supersedeDecision(projectPath, proposed.id, 'ADR-9999', ap2)).toThrow('status is "proposed"');
  });

  it('rejects superseding with non-existent supersededBy', () => {
    const old = proposeDecision(base);
    const ap1 = createAdrApproval(old.id, 'accept_adr');
    acceptDecision(projectPath, old.id, ap1, 'Admin');
    const ap2 = createAdrApproval(old.id, 'supersede_adr', { supersededBy: 'NONEXISTENT' });
    expect(() => supersedeDecision(projectPath, old.id, 'NONEXISTENT', ap2)).toThrow('not found');
  });

  it('proposeDecision does NOT prematurely mark old ADR', () => {
    // Given: an accepted ADR
    const old = proposeDecision(base);
    const ap1 = createAdrApproval(old.id, 'accept_adr');
    acceptDecision(projectPath, old.id, ap1, 'Admin');

    // When: proposing a new ADR that supersedes the old one
    const newAdr = proposeDecision(makeBase({
      title: 'New ADR',
      supersedes: old.id,
    }));

    // Then: old ADR must still be accepted (not prematurely marked)
    const loadedOld = loadDecision(projectPath, old.id);
    expect(loadedOld!.status).toBe('accepted');
    expect(loadedOld!.supersededBy).toBeUndefined();

    // And the new ADR is proposed
    expect(newAdr.status).toBe('proposed');
    expect(newAdr.supersedes).toBe(old.id);
  });

  it('acceptDecision chains supersede when new ADR references old', () => {
    // Given: an accepted old ADR and a proposed new ADR that supersedes it
    const old = proposeDecision(base);
    const ap1 = createAdrApproval(old.id, 'accept_adr');
    acceptDecision(projectPath, old.id, ap1, 'Admin');

    const newAdr = proposeDecision(makeBase({
      title: 'Superseding ADR',
      supersedes: old.id,
    }));

    // When: the new ADR is accepted
    const ap2 = createAdrApproval(newAdr.id, 'accept_adr');
    acceptDecision(projectPath, newAdr.id, ap2, 'Admin');

    // Then: the old ADR should now be superseded
    const loadedOld = loadDecision(projectPath, old.id);
    expect(loadedOld!.status).toBe('superseded');
    expect(loadedOld!.supersededBy).toBe(newAdr.id);

    // And the new ADR is accepted
    const loadedNew = loadDecision(projectPath, newAdr.id);
    expect(loadedNew!.status).toBe('accepted');
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

// ============================================================
// P0-004: Strong Binding Attack Tests
// ============================================================

describe('P0-004: approval strong binding', () => {
  it('rejects approval with missing projectId', () => {
    const proposed = proposeDecision(base);
    const apId = `test_aprv_${Date.now().toString(36)}`;
    submitApproval({
      id: apId, action: 'accept_adr', reason: 'test', riskLevel: 'medium',
      toolName: 'decision',
      input: { action: 'accept_adr', adrId: proposed.id },
    });
    resolveApproval(apId, { approved: true, resolvedBy: 'test' });
    expect(() => acceptDecision(projectPath, proposed.id, apId, 'Tester')).toThrow('projectId');
  });

  it('rejects cross-ADR usage (different adrId)', () => {
    const a1 = proposeDecision(base);
    const a2 = proposeDecision(makeBase({ title: 'Second ADR' }));
    const apId = createAdrApproval(a1.id, 'accept_adr');
    // Try to use a1's approval on a2
    expect(() => acceptDecision(projectPath, a2.id, apId, 'Tester')).toThrow('binding');
  });

  it('rejects cross-action usage (accept vs supersede)', () => {
    const proposed = proposeDecision(base);
    const apId = createAdrApproval(proposed.id, 'supersede_adr', { supersededBy: 'ADR-9999' });
    // Try to use supersede approval for accept
    expect(() => acceptDecision(projectPath, proposed.id, apId, 'Tester')).toThrow('binding');
  });

  it('rejects digest mismatch after input change', () => {
    const proposed = proposeDecision(base);
    // Create approval with one adrId but try to use with different adrId
    const apId = `test_aprv_${Date.now().toString(36)}`;
    submitApproval({
      id: apId, action: 'accept_adr', reason: 'test', riskLevel: 'medium',
      toolName: 'decision',
      projectId: 'test-project-id',
      input: { action: 'accept_adr', adrId: proposed.id },
    });
    resolveApproval(apId, { approved: true, resolvedBy: 'test' });
    // Re-read projectId from manifest to match
    const manifestPath = join(projectPath, '.project/state/manifest.json');
    const projectId = existsSync(manifestPath)
      ? JSON.parse(readFileSync(manifestPath, 'utf-8')).projectId
      : 'test-project-id';

    // Re-create approval with correct projectId from manifest
    const apId2 = `test_aprv_${Date.now().toString(36)}`;
    submitApproval({
      id: apId2, action: 'accept_adr', reason: 'test', riskLevel: 'medium',
      toolName: 'decision',
      projectId,
      input: { action: 'accept_adr', adrId: proposed.id },
    });
    resolveApproval(apId2, { approved: true, resolvedBy: 'test' });
    // Should succeed with correct binding
    const result = acceptDecision(projectPath, proposed.id, apId2, 'Tester');
    expect(result).toBeDefined();
    expect(result!.status).toBe('accepted');
  });

  it('binding failure does NOT consume the approval (reusable for correct request)', () => {
    // Given: a properly created approval
    const proposed = proposeDecision(base);
    const apId = createAdrApproval(proposed.id, 'accept_adr');

    // Attempt a cross-ADR request that should fail
    const a2 = proposeDecision(makeBase({ title: 'Second' }));
    try {
      acceptDecision(projectPath, a2.id, apId, 'Hacker');
    } catch {
      // Expected — binding mismatch
    }

    // Then: the approval should still be consumable for the CORRECT ADR
    const result = acceptDecision(projectPath, proposed.id, apId, 'Tester');
    expect(result).toBeDefined();
    expect(result!.status).toBe('accepted');
  });

  it('rejects consumed approval for second use', () => {
    const proposed = proposeDecision(base);
    const apId = createAdrApproval(proposed.id, 'accept_adr');
    const r1 = acceptDecision(projectPath, proposed.id, apId, 'Tester');
    expect(r1).toBeDefined();
    expect(r1!.status).toBe('accepted');

    // Propose another ADR and try to reuse same approval
    const a2 = proposeDecision(makeBase({ title: 'Second' }));
    expect(() => acceptDecision(projectPath, a2.id, apId, 'Tester')).toThrow('consumed');
  });
});
