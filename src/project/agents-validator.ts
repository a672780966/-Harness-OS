/**
 * Harness OS — AGENTS.md Validator
 *
 * Phase 2.2: Validate AGENTS.md against the standard specification.
 *
 * Flow:
 *   1. Check AGENTS.md exists
 *   2. Parse sections from markdown headings
 *   3. Check all 14 required sections
 *   4. Missing core sections → BLOCK (invalid)
 *   5. Missing non-core sections → WARN
 *
 * Reference: 03_AGENTS_MD_STANDARD.md §3
 */

import { existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';

// ============================================================
// Required Sections (03_AGENTS_MD_STANDARD.md §3)
// ============================================================

export interface AgentsSection {
  /** Section number from the standard. */
  number: number;
  /** Section title (matched against AGENTS.md headings). */
  title: string;
  /** If true, missing this section blocks task execution. */
  isCore: boolean;
}

/**
 * All 14 required AGENTS.md sections.
 * Core sections block task execution if missing.
 */
export const REQUIRED_SECTIONS: AgentsSection[] = [
  { number: 1, title: 'Project Identity', isCore: true },
  { number: 2, title: 'Project Goals', isCore: false },
  { number: 3, title: 'Architecture Rules', isCore: true },
  { number: 4, title: 'Repository Structure', isCore: false },
  { number: 5, title: 'Development Commands', isCore: true },
  { number: 6, title: 'Testing and Verification', isCore: true },
  { number: 7, title: 'Coding Standards', isCore: false },
  { number: 8, title: 'Context Rules', isCore: false },
  { number: 9, title: 'State and Memory Rules', isCore: false },
  { number: 10, title: 'Skill / Tool Rules', isCore: false },
  { number: 11, title: 'Permission and Approval Rules', isCore: true },
  { number: 12, title: 'Git and Delivery Rules', isCore: false },
  { number: 13, title: 'Security Rules', isCore: true },
  { number: 14, title: 'Task Completion Rules', isCore: true },
];

// ============================================================
// Result Types
// ============================================================

export interface SectionResult {
  number: number;
  title: string;
  present: boolean;
  isCore: boolean;
}

export interface AgentsMdValidationResult {
  /** Whether AGENTS.md exists at the expected path. */
  fileExists: boolean;
  /** Absolute path to AGENTS.md. */
  filePath: string;
  /** Results for each of the 14 required sections. */
  sections: SectionResult[];
  /** Names of missing core sections (blockers). */
  missingCore: string[];
  /** Names of missing non-core sections (warnings). */
  missingRequired: string[];
  /** true if no core sections are missing. */
  isValid: boolean;
  /** Human-readable messages. */
  warnings: string[];
}

// ============================================================
// Section Extraction
// ============================================================

/**
 * Extract section headings from AGENTS.md content.
 * Matches headings like:
 *   ## 1. Project Identity
 *   ## Project Identity
 *   ## 3. Architecture Rules
 */
function extractSectionTitles(content: string): string[] {
  const titles: string[] = [];
  // Match "## [N.] Title" pattern (numbered or plain)
  const headingRegex = /^##\s+(?:\d+\.\s+)?(.+)$/gm;
  let match: RegExpExecArray | null;
  while ((match = headingRegex.exec(content)) !== null) {
    titles.push(match[1].trim());
  }
  return titles;
}

/**
 * Normalize a section title for loose matching.
 * Strips whitespace, lowercases, removes punctuation.
 */
function normalizeTitle(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9/ ]/g, '')
    .trim();
}

/**
 * Check if an extracted title matches a required section.
 * Uses loose matching: the extracted title must contain
 * the required section's normalized title as a substring.
 */
function titleMatches(extracted: string, required: string): boolean {
  const normalizedExtracted = normalizeTitle(extracted);
  const normalizedRequired = normalizeTitle(required);
  return normalizedExtracted.includes(normalizedRequired) || normalizedRequired.includes(normalizedExtracted);
}

// ============================================================
// Validator
// ============================================================

/**
 * Validate an AGENTS.md file against the 14-section standard.
 *
 * @param projectPath - Path to the project root (containing AGENTS.md)
 * @returns Validation result with section status and warnings
 */
export function validateAgentsMd(projectPath: string): AgentsMdValidationResult {
  const resolvedPath = resolve(projectPath);
  const agentsMdPath = join(resolvedPath, 'AGENTS.md');
  const result: AgentsMdValidationResult = {
    fileExists: existsSync(agentsMdPath),
    filePath: agentsMdPath,
    sections: [],
    missingCore: [],
    missingRequired: [],
    isValid: false,
    warnings: [],
  };

  // 1. Check file exists
  if (!result.fileExists) {
    result.warnings.push('AGENTS.md is missing — run `harness init` to create it');
    result.sections = REQUIRED_SECTIONS.map((s) => ({
      number: s.number,
      title: s.title,
      present: false,
      isCore: s.isCore,
    }));
    result.missingCore = REQUIRED_SECTIONS.filter((s) => s.isCore).map((s) => s.title);
    result.missingRequired = REQUIRED_SECTIONS.filter((s) => !s.isCore).map((s) => s.title);
    result.isValid = false;
    return result;
  }

  // 2. Read and extract sections
  let content: string;
  try {
    content = readFileSync(agentsMdPath, 'utf-8');
  } catch (err) {
    result.warnings.push(`Failed to read AGENTS.md: ${(err as Error).message}`);
    return result;
  }

  const extractedTitles = extractSectionTitles(content);

  // 3. Check each required section
  for (const section of REQUIRED_SECTIONS) {
    const present = extractedTitles.some((et) => titleMatches(et, section.title));

    result.sections.push({
      number: section.number,
      title: section.title,
      present,
      isCore: section.isCore,
    });

    if (!present) {
      if (section.isCore) {
        result.missingCore.push(section.title);
        result.warnings.push(`Core section missing: "${section.title}" — this blocks task execution`);
      } else {
        result.missingRequired.push(section.title);
        result.warnings.push(`Required section missing: "${section.title}" — consider adding it`);
      }
    }
  }

  // 4. Determine validity
  result.isValid = result.missingCore.length === 0;

  if (result.isValid) {
    result.warnings.push('AGENTS.md is valid');
  }

  return result;
}

/**
 * Quick check: can a task be executed given the current AGENTS.md state?
 * Returns true only if AGENTS.md exists and no core sections are missing.
 */
export function canExecuteTask(projectPath: string): {
  allowed: boolean;
  reason: string;
} {
  const validation = validateAgentsMd(projectPath);

  if (!validation.fileExists) {
    return {
      allowed: false,
      reason: 'AGENTS.md is missing. Run `harness init` to create it.',
    };
  }

  if (validation.missingCore.length > 0) {
    return {
      allowed: false,
      reason: `Core AGENTS.md sections missing: ${validation.missingCore.join(', ')}. Run \`harness repair\` to update.`,
    };
  }

  return {
    allowed: true,
    reason: 'AGENTS.md is valid',
  };
}
