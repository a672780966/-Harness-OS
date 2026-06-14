/**
 * Harness OS — Shared Template Loader
 *
 * Single source of truth for loading the AGENTS.md template.
 * Supports both source (tsx dev) and built (dist artifact) runtimes.
 * Lazy-loads the template so errors happen at call time, not module import time.
 *
 * Path resolution order:
 *   1. ./templates                           — built dist:  dist/templates/
 *   2. ../../templates                        — source dev:  src/project/../../templates/
 *   3. ../templates                           — fallback:    dist/../templates/ (repo root)
 *
 * Reference: 01_ARTIFACT_TEMPLATE.md
 */

import { existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';

// ============================================================
// Path Resolution
// ============================================================

/**
 * Find the templates directory. Tries multiple candidates to support
 * different runtime modes (source dev, built dist, standalone artifact).
 *
 * This is called lazily (not at module load time) so errors surface
 * during command execution and can be caught by the CLI error handler.
 */
function findTemplatesDir(): string {
  const candidates = [
    resolve(import.meta.dirname, './templates'),       // built/standalone: dist/templates/
    resolve(import.meta.dirname, '../../templates'),    // source dev:       src/project/../../templates/
    resolve(import.meta.dirname, '../templates'),       // fallback:         dist/../templates/
  ];

  for (const dir of candidates) {
    if (existsSync(dir)) return dir;
  }

  throw new Error(
    `AGENTS.md template not found. Tried:\n  ${candidates.join('\n  ')}\n` +
      'Ensure templates/ directory is included in the package or reinstall.',
  );
}

// ============================================================
// Template Loading
// ============================================================

/**
 * Read the AGENTS.md template file.
 * Throws an Error with a descriptive message if not found.
 * The CLI layer wraps this into a structured HarnessError envelope.
 */
export function readAgentsMdTemplate(): string {
  const templatesDir = findTemplatesDir();
  const templatePath = join(templatesDir, 'AGENTS.md');

  if (!existsSync(templatePath)) {
    throw new Error(
      `AGENTS.md template file not found at ${templatePath}. ` +
        'Ensure templates/ directory is included in the package.',
    );
  }

  return readFileSync(templatePath, 'utf-8');
}
