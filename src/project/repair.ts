/**
 * Harness OS — Project Init & Repair
 *
 * Phase 1.3: Initialize or repair a Harness OS project structure.
 *
 * Init flow:
 *   1. Detect project type from existing files
 *   2. Create .project/ structure if missing
 *   3. Create AGENTS.md if missing (with template)
 *   4. Generate manifest.json
 *   5. Detect tech stack → tech-stack.md
 *   6. Build repository map → repository-map.md
 *   7. Generate project.md
 *
 * Repair flow:
 *   1. Check each .project/ subdirectory — create missing
 *   2. Validate manifest — add missing fields
 *   3. Check AGENTS.md required sections
 *   4. Refresh tech-stack.md / repository-map.md
 *   5. Generate repair report
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §6
 *            03_AGENTS_MD_STANDARD.md
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import { simpleGit } from 'simple-git';
import type { ProjectManifest } from '../types.js';
import { detectTechStack, buildRepositoryMap } from './create.js';
import { HARNESS_VERSION } from '../version.js';
import { readAgentsMdTemplate } from './template-loader.js';

// ============================================================
// Required sections in AGENTS.md
// ============================================================

const REQUIRED_AGENTS_SECTIONS = [
  'Project Identity',
  'Project Goals',
  'Architecture Rules',
  'Repository Structure',
  'Development Commands',
  'Testing and Verification',
  'Coding Standards',
  'Context Rules',
  'State and Memory Rules',
  'Skill / Tool Rules',
  'Permission and Approval Rules',
  'Git and Delivery Rules',
  'Security Rules',
  'Task Completion Rules',
];

const REQUIRED_PROJECT_DIRS = [
  '.project/state',
  '.project/tasks/active',
  '.project/tasks/completed',
  '.project/tasks/failed',
  '.project/decisions',
  '.project/reports/runs',
  '.project/reports/verification',
  '.project/reports/delivery',
  '.project/reports/events',
  '.project/checkpoints',
  '.project/sessions',
  '.project/context',
];

// ============================================================
// Results
// ============================================================

export interface RepairResult {
  action: 'init' | 'repair';
  path: string;
  dirsCreated: string[];
  dirsExisting: string[];
  manifestCreated: boolean;
  manifestUpdated: boolean;
  agentsMdCreated: boolean;
  agentsMdMissingSections: string[];
  techStackWritten: boolean;
  repoMapWritten: boolean;
  warnings: string[];
}

// ============================================================
// Helpers
// ============================================================

function fillTemplate(template: string, vars: Record<string, string>): string {
  let result = template;
  for (const [key, value] of Object.entries(vars)) {
    result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value || 'unknown');
  }
  return result;
}

function writeJson(path: string, data: unknown): void {
  writeFileSync(path, JSON.stringify(data, null, 2) + '\n', 'utf-8');
}

function readJsonSafe<T>(path: string): { ok: true; data: T } | { ok: false; error: string } {
  try {
    if (!existsSync(path)) return { ok: false, error: 'not found' };
    return { ok: true, data: JSON.parse(readFileSync(path, 'utf-8')) as T };
  } catch (err) {
    return { ok: false, error: (err as Error).message };
  }
}

function extractSections(markdown: string): string[] {
  const sections: string[] = [];
  const headingRegex = /^##\s+\d+\.\s+(.+)$/gm;
  let match: RegExpExecArray | null;
  while ((match = headingRegex.exec(markdown)) !== null) {
    sections.push(match[1].trim());
  }
  return sections;
}

// ============================================================
// Init Project
// ============================================================

/**
 * Initialize Harness OS in an existing project.
 * Creates AGENTS.md and .project/ structure without destroying existing code.
 */
export async function initProject(projectPath?: string): Promise<RepairResult> {
  const resolvedPath = resolve(projectPath || process.cwd());
  const result: RepairResult = {
    action: 'init',
    path: resolvedPath,
    dirsCreated: [],
    dirsExisting: [],
    manifestCreated: false,
    manifestUpdated: false,
    agentsMdCreated: false,
    agentsMdMissingSections: [],
    techStackWritten: false,
    repoMapWritten: false,
    warnings: [],
  };

  // 1. Ensure we're in a Git repo
  const git = simpleGit(resolvedPath);
  const isRepo = await git.checkIsRepo();
  if (!isRepo) {
    result.warnings.push('Not a Git repository — initializing Git');
    await git.init();
  }

  // 2. Detect tech stack
  const techStack = detectTechStack(resolvedPath);

  // 3. Create .project/ directories
  for (const dir of REQUIRED_PROJECT_DIRS) {
    const fullPath = join(resolvedPath, dir);
    if (!existsSync(fullPath)) {
      mkdirSync(fullPath, { recursive: true });
      result.dirsCreated.push(dir);
    } else {
      result.dirsExisting.push(dir);
    }
  }

  // 4. Generate manifest
  const manifestPath = join(resolvedPath, '.project/state/manifest.json');
  const manifestResult = readJsonSafe<ProjectManifest>(manifestPath);

  if (!manifestResult.ok) {
    const projectId = `proj_${Date.now().toString(36)}`;
    const projectName = resolvedPath.split(/[/\\]/).pop() || 'unnamed';
    const manifest: ProjectManifest = {
      version: HARNESS_VERSION,
      projectId,
      projectName,
      projectType: 'unknown',
      rootPath: resolvedPath,
      defaultBranch: 'main',
      language: { primary: techStack.primaryLanguage, secondary: [] },
      runtime: { name: techStack.runtime },
      packageManager: { name: techStack.packageManager },
      commands: {
        install: techStack.installCmd || undefined,
        dev: techStack.devCmd || undefined,
        build: techStack.buildCmd || undefined,
        lint: techStack.lintCmd || undefined,
        typecheck: techStack.typecheckCmd || undefined,
        test: techStack.testCmd || undefined,
        e2e: techStack.e2eCmd || undefined,
      },
      skills: { enabled: ['filesystem', 'shell', 'git', 'repo-scanner'], disabled: [] },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    writeJson(manifestPath, manifest);
    result.manifestCreated = true;
  }

  // 5. Create AGENTS.md if missing
  const agentsMdPath = join(resolvedPath, 'AGENTS.md');
  if (!existsSync(agentsMdPath)) {
    const template = readAgentsMdTemplate();
    const agentsMd = fillTemplate(template, {
      PROJECT_NAME: resolvedPath.split(/[/\\]/).pop() || 'unnamed',
      PROJECT_TYPE: 'unknown',
      PRIMARY_LANGUAGE: techStack.primaryLanguage,
      RUNTIME: techStack.runtime,
      PACKAGE_MANAGER: techStack.packageManager,
      PROJECT_GOALS: 'This project is managed by Harness OS.',
      INSTALL_CMD: techStack.installCmd,
      DEV_CMD: techStack.devCmd,
      BUILD_CMD: techStack.buildCmd,
      LINT_CMD: techStack.lintCmd,
      TYPECHECK_CMD: techStack.typecheckCmd,
      TEST_CMD: techStack.testCmd,
      E2E_CMD: techStack.e2eCmd,
    });
    writeFileSync(agentsMdPath, agentsMd, 'utf-8');
    result.agentsMdCreated = true;
  } else {
    // Check sections
    const content = readFileSync(agentsMdPath, 'utf-8');
    const sections = extractSections(content);
    for (const required of REQUIRED_AGENTS_SECTIONS) {
      if (!sections.some((s) => s.toLowerCase().includes(required.toLowerCase()))) {
        result.agentsMdMissingSections.push(required);
      }
    }
  }

  // 6. Write project.md
  const projectMdPath = join(resolvedPath, '.project/state/project.md');
  if (!existsSync(projectMdPath)) {
    const projectMd = `# ${resolvedPath.split(/[/\\]/).pop() || 'unnamed'}

## Type
unknown

## Tech Stack
- Language: ${techStack.primaryLanguage}
- Runtime: ${techStack.runtime}
- Package Manager: ${techStack.packageManager}

## Status
Active — managed by Harness OS

## Initialized
${new Date().toISOString()}
`;
    writeFileSync(projectMdPath, projectMd, 'utf-8');
  }

  // 7. Write tech-stack.md
  const techStackMdPath = join(resolvedPath, '.project/state/tech-stack.md');
  const techStackMd = `# Tech Stack

## Language
${techStack.primaryLanguage}

## Runtime
${techStack.runtime}

## Package Manager
${techStack.packageManager}

## Commands
| Command | Value |
|---------|-------|
| Install | ${techStack.installCmd || 'not configured'} |
| Dev     | ${techStack.devCmd || 'not configured'} |
| Build   | ${techStack.buildCmd || 'not configured'} |
| Lint    | ${techStack.lintCmd || 'not configured'} |
| Typecheck | ${techStack.typecheckCmd || 'not configured'} |
| Test    | ${techStack.testCmd || 'not configured'} |
| E2E     | ${techStack.e2eCmd || 'not configured'} |
`;
  writeFileSync(techStackMdPath, techStackMd, 'utf-8');
  result.techStackWritten = true;

  // 8. Build and write repository-map.md
  const repoMap = buildRepositoryMap(resolvedPath);
  const repoMapMd = `# Repository Map

## Source Directories
${repoMap.sourceDirs.map((d) => `- ${d}`).join('\n') || '- none detected'}

## Test Directories
${repoMap.testDirs.map((d) => `- ${d}`).join('\n') || '- none detected'}

## Documentation Directories
${repoMap.docDirs.map((d) => `- ${d}`).join('\n') || '- none detected'}

## Configuration Files
${repoMap.configFiles.map((f) => `- ${f}`).join('\n') || '- none detected'}

## Package Files
${repoMap.packageFiles.map((f) => `- ${f}`).join('\n') || '- none detected'}

## Entry Points
${repoMap.entrypoints.map((e) => `- ${e}`).join('\n') || '- none detected'}
`;
  writeFileSync(join(resolvedPath, '.project/state/repository-map.md'), repoMapMd, 'utf-8');
  result.repoMapWritten = true;

  return result;
}

// ============================================================
// Repair Project
// ============================================================

/**
 * Repair a Harness OS project structure.
 * Re-creates missing directories, validates manifest, and refreshes state files.
 */
export async function repairProject(projectPath?: string): Promise<RepairResult> {
  const resolvedPath = resolve(projectPath || process.cwd());
  const result: RepairResult = {
    action: 'repair',
    path: resolvedPath,
    dirsCreated: [],
    dirsExisting: [],
    manifestCreated: false,
    manifestUpdated: false,
    agentsMdCreated: false,
    agentsMdMissingSections: [],
    techStackWritten: false,
    repoMapWritten: false,
    warnings: [],
  };

  // 1. Check path exists
  if (!existsSync(resolvedPath)) {
    result.warnings.push(`Path does not exist: ${resolvedPath}`);
    return result;
  }

  // 2. Check .project/ directories
  for (const dir of REQUIRED_PROJECT_DIRS) {
    const fullPath = join(resolvedPath, dir);
    if (!existsSync(fullPath)) {
      mkdirSync(fullPath, { recursive: true });
      result.dirsCreated.push(dir);
    } else {
      result.dirsExisting.push(dir);
    }
  }

  // 3. Ensure .gitignore includes Harness entries
  const gitignorePath = join(resolvedPath, '.gitignore');
  if (existsSync(gitignorePath)) {
    const gitignore = readFileSync(gitignorePath, 'utf-8');
    if (!gitignore.includes('.project/context/')) {
      // Append Harness ignore rules
      const append = `\n# Harness OS — runtime state (auto-added by repair)\n.project/context/\n.project/reports/events/\n.project/reports/traces/\n.project/checkpoints/\n.project/sessions/\n.project/tasks/active/\n`;
      writeFileSync(gitignorePath, gitignore + append, 'utf-8');
    }
  }

  // 4. Detect tech stack
  const techStack = detectTechStack(resolvedPath);

  // 5. Validate manifest
  const manifestPath = join(resolvedPath, '.project/state/manifest.json');
  const manifestResult = readJsonSafe<ProjectManifest>(manifestPath);

  if (!manifestResult.ok) {
    // Create new manifest
    const projectId = `proj_${Date.now().toString(36)}`;
    const projectName = resolvedPath.split(/[/\\]/).pop() || 'unnamed';
    const manifest: ProjectManifest = {
      version: HARNESS_VERSION,
      projectId,
      projectName,
      projectType: 'unknown',
      rootPath: resolvedPath,
      defaultBranch: 'main',
      language: { primary: techStack.primaryLanguage, secondary: [] },
      runtime: { name: techStack.runtime },
      packageManager: { name: techStack.packageManager },
      commands: {
        install: techStack.installCmd || undefined,
        dev: techStack.devCmd || undefined,
        build: techStack.buildCmd || undefined,
        lint: techStack.lintCmd || undefined,
        typecheck: techStack.typecheckCmd || undefined,
        test: techStack.testCmd || undefined,
        e2e: techStack.e2eCmd || undefined,
      },
      skills: { enabled: ['filesystem', 'shell', 'git', 'repo-scanner'], disabled: [] },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    writeJson(manifestPath, manifest);
    result.manifestCreated = true;
  } else {
    // Update existing manifest fields
    const existing = manifestResult.data;
    let updated = false;

    if (!existing.language || !existing.language.primary) {
      existing.language = { primary: techStack.primaryLanguage, secondary: [] };
      updated = true;
    }
    if (!existing.runtime || !existing.runtime.name) {
      existing.runtime = { name: techStack.runtime };
      updated = true;
    }
    if (!existing.commands) {
      existing.commands = {};
      updated = true;
    }
    if (!existing.skills) {
      existing.skills = { enabled: ['filesystem', 'shell', 'git', 'repo-scanner'], disabled: [] };
      updated = true;
    }
    if (!existing.projectType || existing.projectType === 'unknown') {
      // Try to detect
      if (techStack.primaryLanguage !== 'unknown') {
        existing.projectType = 'unknown'; // keep unknown, can't auto-detect accurately
      }
    }

    if (updated) {
      existing.updatedAt = new Date().toISOString();
      writeJson(manifestPath, existing);
      result.manifestUpdated = true;
    }
  }

  // 6. Check AGENTS.md sections
  const agentsMdPath = join(resolvedPath, 'AGENTS.md');
  if (existsSync(agentsMdPath)) {
    const content = readFileSync(agentsMdPath, 'utf-8');
    const sections = extractSections(content);
    for (const required of REQUIRED_AGENTS_SECTIONS) {
      if (!sections.some((s) => s.toLowerCase().includes(required.toLowerCase()))) {
        result.agentsMdMissingSections.push(required);
      }
    }
  } else {
    result.warnings.push('AGENTS.md is missing — run `harness init` to create it');
  }

  // 7. Refresh tech-stack.md
  const techStackMd = `# Tech Stack (refreshed by repair)

## Language
${techStack.primaryLanguage}

## Runtime
${techStack.runtime}

## Package Manager
${techStack.packageManager}

## Commands
| Command | Value |
|---------|-------|
| Install | ${techStack.installCmd || 'not configured'} |
| Dev     | ${techStack.devCmd || 'not configured'} |
| Build   | ${techStack.buildCmd || 'not configured'} |
| Lint    | ${techStack.lintCmd || 'not configured'} |
| Typecheck | ${techStack.typecheckCmd || 'not configured'} |
| Test    | ${techStack.testCmd || 'not configured'} |
| E2E     | ${techStack.e2eCmd || 'not configured'} |
`;
  writeFileSync(join(resolvedPath, '.project/state/tech-stack.md'), techStackMd, 'utf-8');
  result.techStackWritten = true;

  // 8. Refresh repository-map.md
  const repoMap = buildRepositoryMap(resolvedPath);
  const repoMapMd = `# Repository Map (refreshed by repair)

## Source Directories
${repoMap.sourceDirs.map((d) => `- ${d}`).join('\n') || '- none detected'}

## Test Directories
${repoMap.testDirs.map((d) => `- ${d}`).join('\n') || '- none detected'}

## Documentation Directories
${repoMap.docDirs.map((d) => `- ${d}`).join('\n') || '- none detected'}

## Configuration Files
${repoMap.configFiles.map((f) => `- ${f}`).join('\n') || '- none detected'}

## Package Files
${repoMap.packageFiles.map((f) => `- ${f}`).join('\n') || '- none detected'}

## Entry Points
${repoMap.entrypoints.map((e) => `- ${e}`).join('\n') || '- none detected'}
`;
  writeFileSync(join(resolvedPath, '.project/state/repository-map.md'), repoMapMd, 'utf-8');
  result.repoMapWritten = true;

  return result;
}
