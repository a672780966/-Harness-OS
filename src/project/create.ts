/**
 * Harness OS — Project Create
 *
 * Phase 1.1: Create a new Harness OS project.
 *
 * Flow:
 *   1. Create project directory
 *   2. Initialize Git repo
 *   3. Write .gitignore
 *   4. Inject AGENTS.md template
 *   5. Create .project/ directory structure
 *   6. Write manifest.json
 *   7. Write project.md
 *   8. Detect tech stack → tech-stack.md
 *   9. Build repository map → repository-map.md
 *   10. Git add + initial commit
 *   11. Output project created summary
 *
 * Reference: 06_TASK_DECISION_PROJECT_MANAGER.md §6
 *            17_PROJECT_STORAGE_GIT_POLICY.md §5
 */

import { mkdirSync, writeFileSync, existsSync, readFileSync } from 'fs';
import { join, resolve } from 'path';
import { simpleGit } from 'simple-git';
import { type ProjectManifest } from '../types.js';
import { HARNESS_VERSION } from '../version.js';

// ============================================================
// Constants
// ============================================================

/**
 * Find the templates directory regardless of runtime (source vs dist).
 *
 * When running via tsx (source):     import.meta.dirname = src/project/ → ../../templates
 * When running via node (built dist): import.meta.dirname = dist/       → ../templates
 */
function findTemplatesDir(): string {
  const candidates = [
    resolve(import.meta.dirname, '../../templates'), // source:   src/project/../../templates
    resolve(import.meta.dirname, '../templates'), // built:    dist/../templates
    resolve(process.cwd(), 'templates'), // fallback: cwd/templates
  ];
  for (const dir of candidates) {
    if (existsSync(dir)) return dir;
  }
  throw new Error(
    `AGENTS.md template not found. Tried:\n  ${candidates.join('\n  ')}\n` +
      `Ensure templates/ directory exists in the package root.`,
  );
}

const TEMPLATES_DIR = findTemplatesDir();
const AGENTS_MD_TEMPLATE_PATH = join(TEMPLATES_DIR, 'AGENTS.md');

const PROJECT_DIRS = [
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

const GITIGNORE_CONTENT = `# Harness OS — Git tracking policy
# Reference: 17_PROJECT_STORAGE_GIT_POLICY.md

# B. Reviewable Project Memory (optional per policy)
# .project/tasks/completed/

# C. Local Runtime State — never tracked
.project/context/
.project/reports/events/
.project/reports/traces/
.project/checkpoints/
.project/sessions/
.project/tasks/active/

# D. Sensitive / Large / Temporary
.env
.env.*
*.pem
*.key
id_rsa
id_ed25519
credentials.json
service-account.json
*.log
node_modules/
dist/
build/
coverage/
.tmp/
`;

// ============================================================
// Template Helpers
// ============================================================

function readAgentsMdTemplate(): string {
  if (!existsSync(AGENTS_MD_TEMPLATE_PATH)) {
    throw new Error(`AGENTS.md template not found at ${AGENTS_MD_TEMPLATE_PATH}`);
  }
  return readFileSync(AGENTS_MD_TEMPLATE_PATH, 'utf-8');
}

function fillTemplate(template: string, vars: Record<string, string>): string {
  let result = template;
  for (const [key, value] of Object.entries(vars)) {
    result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value || 'unknown');
  }
  return result;
}

// ============================================================
// Detect Tech Stack
// ============================================================

export interface TechStack {
  primaryLanguage: string;
  runtime: string;
  packageManager: string;
  installCmd: string;
  devCmd: string;
  buildCmd: string;
  lintCmd: string;
  typecheckCmd: string;
  testCmd: string;
  e2eCmd: string;
}

export function detectTechStack(projectPath: string): TechStack {
  const defaults: TechStack = {
    primaryLanguage: 'unknown',
    runtime: 'unknown',
    packageManager: 'unknown',
    installCmd: '',
    devCmd: '',
    buildCmd: '',
    lintCmd: '',
    typecheckCmd: '',
    testCmd: '',
    e2eCmd: '',
  };

  const pkgJsonPath = join(projectPath, 'package.json');
  if (existsSync(pkgJsonPath)) {
    try {
      const pkg = JSON.parse(readFileSync(pkgJsonPath, 'utf-8'));
      const scripts = pkg.scripts || {};

      // Detect lockfile to determine package manager
      if (existsSync(join(projectPath, 'pnpm-lock.yaml'))) {
        defaults.packageManager = 'pnpm';
      } else if (existsSync(join(projectPath, 'yarn.lock'))) {
        defaults.packageManager = 'yarn';
      } else if (existsSync(join(projectPath, 'package-lock.json'))) {
        defaults.packageManager = 'npm';
      } else {
        defaults.packageManager = 'npm';
      }

      const pm = defaults.packageManager;
      defaults.installCmd = scripts.install ? `${pm} install` : `${pm} install`;
      defaults.devCmd = scripts.dev ? `${pm} ${scripts.dev}` : '';
      defaults.buildCmd = scripts.build ? `${pm} run build` : '';
      defaults.lintCmd = scripts.lint ? `${pm} run lint` : '';
      defaults.typecheckCmd = scripts.typecheck ? `${pm} run typecheck` : '';
      defaults.testCmd = scripts.test ? `${pm} test` : '';
      defaults.e2eCmd = scripts.e2e ? `${pm} run e2e` : '';
      defaults.primaryLanguage = 'TypeScript';
      defaults.runtime = pkg.engines?.node ? `Node.js ${pkg.engines.node}` : 'Node.js';

      return defaults;
    } catch {
      return defaults;
    }
  }

  // Check for other languages
  if (existsSync(join(projectPath, 'pyproject.toml'))) {
    defaults.primaryLanguage = 'Python';
    defaults.runtime = 'Python';
    defaults.packageManager = 'uv';
  } else if (existsSync(join(projectPath, 'Cargo.toml'))) {
    defaults.primaryLanguage = 'Rust';
    defaults.runtime = 'Rust';
    defaults.packageManager = 'cargo';
  } else if (existsSync(join(projectPath, 'go.mod'))) {
    defaults.primaryLanguage = 'Go';
    defaults.runtime = 'Go';
    defaults.packageManager = 'go';
  }

  return defaults;
}

// ============================================================
// Build Repository Map
// ============================================================

export interface RepositoryMap {
  rootPath: string;
  sourceDirs: string[];
  testDirs: string[];
  docDirs: string[];
  configFiles: string[];
  packageFiles: string[];
  entrypoints: string[];
  majorModules: string[];
}

export function buildRepositoryMap(projectPath: string): RepositoryMap {
  const map: RepositoryMap = {
    rootPath: projectPath,
    sourceDirs: [],
    testDirs: [],
    docDirs: [],
    configFiles: [],
    packageFiles: [],
    entrypoints: [],
    majorModules: [],
  };

  const entries = ['src', 'lib', 'app', 'packages', 'services', 'components', 'tests', 'docs'];
  for (const entry of entries) {
    const fullPath = join(projectPath, entry);
    if (existsSync(fullPath)) {
      if (entry === 'tests' || entry.startsWith('test')) {
        map.testDirs.push(entry);
      } else if (entry === 'docs') {
        map.docDirs.push(entry);
      } else {
        map.sourceDirs.push(entry);
      }
    }
  }

  // Config & package files
  const configCandidates = [
    'tsconfig.json',
    '.eslintrc.js',
    '.eslintrc.json',
    '.eslintrc.yaml',
    'prettier.config.js',
    '.prettierrc',
    '.prettierrc.json',
    'biome.json',
    'biome.jsonc',
    'Makefile',
    'Dockerfile',
    'docker-compose.yml',
    '.github/workflows',
  ];
  for (const cfg of configCandidates) {
    if (existsSync(join(projectPath, cfg))) {
      map.configFiles.push(cfg);
    }
  }

  const packageCandidates = [
    'package.json',
    'pnpm-lock.yaml',
    'yarn.lock',
    'package-lock.json',
    'pyproject.toml',
    'Cargo.toml',
    'go.mod',
    'go.sum',
    'Gemfile',
    'Gemfile.lock',
  ];
  for (const pkg of packageCandidates) {
    if (existsSync(join(projectPath, pkg))) {
      map.packageFiles.push(pkg);
    }
  }

  const entryCandidates = [
    'src/index.ts',
    'src/index.js',
    'src/main.ts',
    'src/main.js',
    'index.ts',
    'index.js',
    'app.ts',
    'app.js',
    'main.py',
    'main.rs',
    'main.go',
  ];
  for (const ep of entryCandidates) {
    if (existsSync(join(projectPath, ep))) {
      map.entrypoints.push(ep);
    }
  }

  return map;
}

// ============================================================
// Write Helpers
// ============================================================

function writeJson(path: string, data: unknown): void {
  writeFileSync(path, JSON.stringify(data, null, 2) + '\n', 'utf-8');
}

function writeMarkdown(path: string, content: string): void {
  writeFileSync(path, content, 'utf-8');
}

// ============================================================
// Create Project
// ============================================================

export interface CreateProjectOptions {
  /** Project display name. */
  name: string;
  /** Optional custom path (defaults to ./name). */
  path?: string;
  /** Optional project type override. */
  projectType?: ProjectManifest['projectType'];
}

export interface CreateProjectResult {
  projectId: string;
  name: string;
  path: string;
  agentsMdCreated: boolean;
  projectDirCreated: boolean;
  manifestPath: string;
  checkpointId: string;
}

/**
 * Create a new Harness OS project.
 *
 * Steps:
 *   1. Create directory
 *   2. git init
 *   3. Write .gitignore
 *   4. Inject AGENTS.md
 *   5. Create .project/ structure
 *   6. Write manifest.json
 *   7. Write project.md
 *   8. Detect tech stack
 *   9. Build repository map
 *   10. Generate tech-stack.md
 *   11. Generate repository-map.md
 *   12. Git add + initial commit
 */
export async function createProject(opts: CreateProjectOptions): Promise<CreateProjectResult> {
  const projectPath = resolve(opts.path || opts.name);
  const projectName = opts.name;

  // 1. Create project directory
  if (!existsSync(projectPath)) {
    mkdirSync(projectPath, { recursive: true });
  }
  const projectDirCreated = !existsSync(join(projectPath, '.git'));

  // 2. Initialize Git repo
  const git = simpleGit(projectPath);
  const isRepo = await git.checkIsRepo();
  if (!isRepo) {
    await git.init();
  }

  // 3. Write .gitignore
  writeFileSync(join(projectPath, '.gitignore'), GITIGNORE_CONTENT, 'utf-8');

  // 4. Detect tech stack (before AGENTS.md so we can fill values)
  const techStack = detectTechStack(projectPath);

  // 5. Inject AGENTS.md from template
  const template = readAgentsMdTemplate();
  const agentsMd = fillTemplate(template, {
    PROJECT_NAME: projectName,
    PROJECT_TYPE: opts.projectType || 'unknown',
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
  writeFileSync(join(projectPath, 'AGENTS.md'), agentsMd, 'utf-8');

  // 6. Create .project/ directory structure
  for (const dir of PROJECT_DIRS) {
    mkdirSync(join(projectPath, dir), { recursive: true });
  }

  // 7. Generate project ID
  const projectId = `proj_${Date.now().toString(36)}`;

  // 8. Write manifest.json
  const manifest: ProjectManifest = {
    version: HARNESS_VERSION,
    projectId,
    projectName,
    projectType: opts.projectType || 'unknown',
    rootPath: projectPath,
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
  const manifestPath = join(projectPath, '.project/state/manifest.json');
  writeJson(manifestPath, manifest);

  // 9. Write project.md
  const projectMd = `# ${projectName}

## Project ID
${projectId}

## Type
${opts.projectType || 'unknown'}

## Tech Stack
- Language: ${techStack.primaryLanguage}
- Runtime: ${techStack.runtime}
- Package Manager: ${techStack.packageManager}

## Status
Active — managed by Harness OS

## Created
${new Date().toISOString()}
`;
  writeMarkdown(join(projectPath, '.project/state/project.md'), projectMd);

  // 10. Build and write tech-stack.md
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
  writeMarkdown(join(projectPath, '.project/state/tech-stack.md'), techStackMd);

  // 11. Build and write repository-map.md
  const repoMap = buildRepositoryMap(projectPath);
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
  writeMarkdown(join(projectPath, '.project/state/repository-map.md'), repoMapMd);

  // 12. Git add + initial commit
  // Set local git config for commit authorship
  await git.addConfig('user.email', 'harness@localhost', false, 'local');
  await git.addConfig('user.name', 'Harness OS', false, 'local');
  await git.add('.');
  await git.commit('Initial Harness OS project setup', undefined, {
    '--allow-empty': null,
  });

  const checkpointId = `cp_${Date.now().toString(36)}`;
  writeJson(join(projectPath, `.project/checkpoints/${checkpointId}.json`), {
    checkpointId,
    projectId,
    timestamp: new Date().toISOString(),
    event: 'project.created',
    description: 'Initial project creation checkpoint',
    gitStatus: 'clean',
    changedFiles: [],
    branch: 'main',
  });

  return {
    projectId,
    name: projectName,
    path: projectPath,
    agentsMdCreated: true,
    projectDirCreated,
    manifestPath: '.project/state/manifest.json',
    checkpointId,
  };
}
