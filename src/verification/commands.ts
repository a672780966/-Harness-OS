/**
 * Harness OS — Verification Command Detector
 *
 * Phase 6.1: Detect verification commands from project sources.
 *
 * Command sources (priority order):
 *   1. AGENTS.md — Development Commands section
 *   2. .project/state/manifest.json — commands field
 *   3. package.json — scripts field
 *   4. Other package files (pyproject.toml, Makefile, etc.)
 *
 * Reference: 09_VERIFICATION_OBSERVABILITY.md §6, §7
 */

import { existsSync, readFileSync } from 'fs';
import { join } from 'path';

// ============================================================
// Types
// ============================================================

export interface DetectedCommand {
  name: string;
  command: string;
  source: 'agents-md' | 'manifest' | 'package-json' | 'inferred';
  uncertain: boolean;
  type: CommandType;
}

export type CommandType =
  | 'lint'
  | 'typecheck'
  | 'test'
  | 'unit-test'
  | 'integration-test'
  | 'e2e-test'
  | 'build'
  | 'install'
  | 'format-check'
  | 'custom';

const COMMAND_ORDER: CommandType[] = [
  'lint',
  'typecheck',
  'unit-test',
  'test',
  'integration-test',
  'build',
  'e2e-test',
  'install',
  'format-check',
  'custom',
];

// ============================================================
// Command Name → Type Mapping
// ============================================================

function commandNameToType(name: string): CommandType {
  const lower = name.toLowerCase();
  if (lower.includes('lint')) return 'lint';
  if (lower.includes('typecheck') || lower.includes('type-check') || lower === 'tsc') return 'typecheck';
  if (lower.includes('e2e')) return 'e2e-test';
  if (lower.includes('integration')) return 'integration-test';
  if (lower === 'test' || lower.includes('unit')) return 'unit-test';
  if (lower.includes('build')) return 'build';
  if (lower.includes('install')) return 'install';
  if (lower.includes('format')) return 'format-check';
  return 'test';
}

// ============================================================
// Detect from AGENTS.md
// ============================================================

/**
 * Read commands from AGENTS.md "Development Commands" section.
 * Looks for lines like: Lint: eslint, Test: pnpm test
 */
function detectFromAgentsMd(projectPath: string): DetectedCommand[] {
  const agentsMdPath = join(projectPath, 'AGENTS.md');
  if (!existsSync(agentsMdPath)) return [];

  const content = readFileSync(agentsMdPath, 'utf-8');
  const commands: DetectedCommand[] = [];

  // Match lines like "Lint: eslint" or "Test: pnpm test" in the dev commands section
  const sectionMatch = content.match(/##\s+\d*\.?\s*Development Commands\n([\s\S]*?)(?=\n##\s|\Z)/i);
  if (!sectionMatch) return [];

  const section = sectionMatch[1];
  const cmdRegex = /^(\w+):\s*(.+)$/gm;
  let match: RegExpExecArray | null;

  while ((match = cmdRegex.exec(section)) !== null) {
    const name = match[1].trim().toLowerCase();
    const command = match[2].trim();
    if (command && command !== 'unknown' && command !== 'not configured') {
      commands.push({
        name,
        command,
        source: 'agents-md',
        uncertain: false,
        type: commandNameToType(name),
      });
    }
  }

  return commands;
}

// ============================================================
// Detect from Manifest
// ============================================================

function detectFromManifest(projectPath: string): DetectedCommand[] {
  const manifestPath = join(projectPath, '.project/state/manifest.json');
  if (!existsSync(manifestPath)) return [];

  try {
    const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'));
    const cmds = manifest.commands || {};
    const commands: DetectedCommand[] = [];

    for (const [name, command] of Object.entries(cmds)) {
      if (command && typeof command === 'string') {
        commands.push({
          name,
          command,
          source: 'manifest',
          uncertain: false,
          type: commandNameToType(name),
        });
      }
    }

    return commands;
  } catch {
    return [];
  }
}

// ============================================================
// Detect from package.json
// ============================================================

function detectFromPackageJson(projectPath: string): DetectedCommand[] {
  const pkgPath = join(projectPath, 'package.json');
  if (!existsSync(pkgPath)) return [];

  try {
    const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
    const scripts = pkg.scripts || {};
    const commands: DetectedCommand[] = [];

    for (const [name, command] of Object.entries(scripts)) {
      if (command && typeof command === 'string' && !name.startsWith('pre') && !name.startsWith('post')) {
        commands.push({
          name,
          command,
          source: 'package-json',
          uncertain: true, // inferred, not declared in AGENTS.md
          type: commandNameToType(name),
        });
      }
    }

    return commands;
  } catch {
    return [];
  }
}

// ============================================================
// Main API
// ============================================================

/**
 * Detect all verification commands from project sources.
 * Merges results with priority: AGENTS.md > manifest > package.json.
 */
export function detectCommands(projectPath: string): DetectedCommand[] {
  const agentsCmds = detectFromAgentsMd(projectPath);
  const manifestCmds = detectFromManifest(projectPath);
  const pkgCmds = detectFromPackageJson(projectPath);

  // Merge: AGENTS.md takes priority, package.json fills gaps
  const merged = new Map<string, DetectedCommand>();

  for (const cmd of agentsCmds) {
    merged.set(cmd.name, cmd);
  }
  for (const cmd of manifestCmds) {
    if (!merged.has(cmd.name)) merged.set(cmd.name, cmd);
  }
  for (const cmd of pkgCmds) {
    if (!merged.has(cmd.name)) merged.set(cmd.name, cmd);
  }

  // Sort by command type priority
  return Array.from(merged.values()).sort((a, b) => {
    const aIdx = COMMAND_ORDER.indexOf(a.type);
    const bIdx = COMMAND_ORDER.indexOf(b.type);
    if (aIdx !== bIdx) return aIdx - bIdx;
    return a.name.localeCompare(b.name);
  });
}
