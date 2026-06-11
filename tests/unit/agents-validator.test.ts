/**
 * Harness OS — AGENTS.md Validator Tests
 *
 * Coverage:
 * - Existing AGENTS.md: all sections present, some missing, core missing, empty
 * - Non-existent AGENTS.md
 * - Section extraction: standard headings, non-standard headings
 * - canExecuteTask: allowed/blocked states
 *
 * Reference: 03_AGENTS_MD_STANDARD.md | 11_ACCEPTANCE_CRITERIA.md §6
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';
import {
  validateAgentsMd,
  canExecuteTask,
  REQUIRED_SECTIONS,
} from '../../src/project/agents-validator.js';

let testDir: string;

beforeEach(() => {
  testDir = mkdtempSync(join(tmpdir(), 'harness-agents-test-'));
});

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true });
});

// ============================================================
// Helpers
// ============================================================

const VALID_AGENTS_MD = `# AGENTS.md

## 1. Project Identity

Project Name: test

## 2. Project Goals

Test project

## 3. Architecture Rules

Single agent

## 4. Repository Structure

Standard layout

## 5. Development Commands

Install: pnpm install

## 6. Testing and Verification

Run tests before completing

## 7. Coding Standards

Match existing code style

## 8. Context Rules

Read AGENTS.md first

## 9. State and Memory Rules

Use .project/ for state

## 10. Skill / Tool Rules

Skills are tools

## 11. Permission and Approval Rules

High risk requires approval

## 12. Git and Delivery Rules

Check git status first

## 13. Security Rules

Protect secrets

## 14. Task Completion Rules

Verification must pass
`;

const CORE_SECTIONS_ONLY = `# AGENTS.md

## 1. Project Identity

Name: test

## 3. Architecture Rules

Single agent

## 5. Development Commands

Install: test

## 6. Testing and Verification

Test

## 11. Permission and Approval Rules

Approval required

## 13. Security Rules

Redact secrets

## 14. Task Completion Rules

Verify before done
`;

// ============================================================
// validateAgentsMd Tests
// ============================================================

describe('validateAgentsMd', () => {
  it('validates a complete AGENTS.md', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), VALID_AGENTS_MD, 'utf-8');
    const result = validateAgentsMd(testDir);

    expect(result.fileExists).toBe(true);
    expect(result.isValid).toBe(true);
    expect(result.missingCore).toHaveLength(0);
    expect(result.missingRequired).toHaveLength(0);
    expect(result.sections).toHaveLength(14);

    const allPresent = result.sections.every(s => s.present);
    expect(allPresent).toBe(true);
  });

  it('reports missing AGENTS.md', () => {
    const result = validateAgentsMd(testDir);

    expect(result.fileExists).toBe(false);
    expect(result.isValid).toBe(false);
    expect(result.sections).toHaveLength(14);
    expect(result.sections.every(s => !s.present)).toBe(true);
    expect(result.missingCore.length).toBeGreaterThan(0);
    expect(result.missingRequired.length).toBeGreaterThan(0);
  });

  it('detects missing core sections', () => {
    // Only include non-core sections
    writeFileSync(join(testDir, 'AGENTS.md'), `# AGENTS.md

## 2. Project Goals

Test

## 4. Repository Structure

Standard

## 7. Coding Standards

Match style

## 8. Context Rules

Read first

## 9. State and Memory Rules

Use .project/

## 10. Skill / Tool Rules

Tools only

## 12. Git and Delivery Rules

Check status
`, 'utf-8');

    const result = validateAgentsMd(testDir);
    expect(result.isValid).toBe(false);
    expect(result.missingCore.length).toBeGreaterThan(0);

    // Should include critical core sections
    const coreTitles = REQUIRED_SECTIONS.filter(s => s.isCore).map(s => s.title);
    for (const core of coreTitles) {
      expect(result.missingCore).toContain(core);
    }
  });

  it('allows non-core sections to be missing', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), CORE_SECTIONS_ONLY, 'utf-8');
    const result = validateAgentsMd(testDir);

    expect(result.isValid).toBe(true); // all core sections present
    expect(result.missingCore).toHaveLength(0);
    expect(result.missingRequired.length).toBeGreaterThan(0); // non-core missing
  });

  it('detects single missing core section', () => {
    const content = VALID_AGENTS_MD.replace(/^## 13. Security Rules.*?(?=^## )/ms, '');
    writeFileSync(join(testDir, 'AGENTS.md'), content, 'utf-8');

    const result = validateAgentsMd(testDir);
    expect(result.isValid).toBe(false);
    expect(result.missingCore).toContain('Security Rules');
  });

  it('handles empty AGENTS.md', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), '', 'utf-8');
    const result = validateAgentsMd(testDir);

    expect(result.fileExists).toBe(true);
    expect(result.isValid).toBe(false);
    expect(result.sections.every(s => !s.present)).toBe(true);
  });

  it('handles non-numbered section headings', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), `# AGENTS.md

## Project Identity

Name: test

## Architecture Rules

Single agent

## Development Commands

Install: pnpm install
`, 'utf-8');

    const result = validateAgentsMd(testDir);
    // These sections should match by name even without numbers
    const projectId = result.sections.find(s => s.title === 'Project Identity');
    expect(projectId?.present).toBe(true);
  });

  it('reports warning messages for missing sections', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), `# AGENTS.md

## 1. Project Identity

Name: test
`, 'utf-8');

    const result = validateAgentsMd(testDir);
    expect(result.warnings.length).toBeGreaterThan(0);
    expect(result.warnings.some(w => w.includes('missing'))).toBe(true);
  });
});

// ============================================================
// canExecuteTask Tests
// ============================================================

describe('canExecuteTask', () => {
  it('allows execution when AGENTS.md is valid', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), VALID_AGENTS_MD, 'utf-8');
    const result = canExecuteTask(testDir);
    expect(result.allowed).toBe(true);
    expect(result.reason).toContain('valid');
  });

  it('blocks execution when AGENTS.md is missing', () => {
    const result = canExecuteTask(testDir);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('missing');
  });

  it('blocks execution when core sections are missing', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), `# AGENTS.md

## 2. Project Goals

Test
`, 'utf-8');

    const result = canExecuteTask(testDir);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('Core');
  });

  it('allows execution when only non-core sections missing', () => {
    writeFileSync(join(testDir, 'AGENTS.md'), CORE_SECTIONS_ONLY, 'utf-8');
    const result = canExecuteTask(testDir);
    expect(result.allowed).toBe(true);
  });
});

// ============================================================
// Section Definition Tests
// ============================================================

describe('REQUIRED_SECTIONS', () => {
  it('has exactly 14 sections', () => {
    expect(REQUIRED_SECTIONS).toHaveLength(14);
  });

  it('has 7 core sections', () => {
    const core = REQUIRED_SECTIONS.filter(s => s.isCore);
    expect(core).toHaveLength(7);
  });

  it('core sections are correct', () => {
    const coreTitles = REQUIRED_SECTIONS.filter(s => s.isCore).map(s => s.title);
    expect(coreTitles).toContain('Project Identity');
    expect(coreTitles).toContain('Architecture Rules');
    expect(coreTitles).toContain('Development Commands');
    expect(coreTitles).toContain('Testing and Verification');
    expect(coreTitles).toContain('Permission and Approval Rules');
    expect(coreTitles).toContain('Security Rules');
    expect(coreTitles).toContain('Task Completion Rules');
  });

  it('all sections have unique numbers', () => {
    const numbers = REQUIRED_SECTIONS.map(s => s.number);
    expect(new Set(numbers).size).toBe(14);
  });
});
