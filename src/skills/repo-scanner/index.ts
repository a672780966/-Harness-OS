import { SkillManifest } from '../../types.js';
import { existsSync, readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { type SkillExecutionContext, type SkillExecutionResult, successResult, failedResult } from '../executor.js';
import { type SkillRegistry } from '../registry.js';

export const manifest: SkillManifest = {
  name: 'repo-scanner',
  version: '1.0.0',
  description: 'Scan repository structure, detect tech stack, build repository maps',
  category: 'repo-scanner',
  defaultEnabled: true,
  requiresNetwork: false,
  requiresFilesystem: true,
  riskLevel: 'low',
  docPath: 'src/skills/repo-scanner/SKILL.md',
  tools: [
    {
      name: 'scan_files',
      description: 'Scan files matching a pattern',
      inputSchema: {
        type: 'object',
        properties: { path: { type: 'string' }, pattern: { type: 'string' } },
        required: [],
      },
      outputSchema: { type: 'array', items: { type: 'string' } },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 30000,
    },
    {
      name: 'build_repository_map',
      description: 'Build repository structure map',
      inputSchema: { type: 'object', properties: {}, required: [] },
      outputSchema: {
        type: 'object',
        properties: {
          sourceDirs: { type: 'array', items: { type: 'string' } },
          configFiles: { type: 'array', items: { type: 'string' } },
          commands: { type: 'object' },
        },
      },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 30000,
    },
    {
      name: 'detect_commands',
      description: 'Detect commands from project files',
      inputSchema: { type: 'object', properties: {}, required: [] },
      outputSchema: {
        type: 'object',
        properties: { packageManager: { type: 'string' }, commands: { type: 'object' } },
      },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 10000,
    },
  ],
};

function detectLanguage(projectPath: string): string {
  if (existsSync(join(projectPath, 'package.json'))) return 'TypeScript/JavaScript';
  if (existsSync(join(projectPath, 'pyproject.toml'))) return 'Python';
  if (existsSync(join(projectPath, 'Cargo.toml'))) return 'Rust';
  if (existsSync(join(projectPath, 'go.mod'))) return 'Go';
  return 'unknown';
}

function detectPackageManager(projectPath: string): string {
  if (existsSync(join(projectPath, 'pnpm-lock.yaml'))) return 'pnpm';
  if (existsSync(join(projectPath, 'yarn.lock'))) return 'yarn';
  if (existsSync(join(projectPath, 'package-lock.json'))) return 'npm';
  if (existsSync(join(projectPath, 'pyproject.toml'))) return 'uv';
  if (existsSync(join(projectPath, 'Cargo.toml'))) return 'cargo';
  if (existsSync(join(projectPath, 'go.mod'))) return 'go';
  return 'unknown';
}

function scanDirectories(projectPath: string): string[] {
  const dirs = ['src', 'lib', 'app', 'packages', 'components', 'tests', 'docs'];
  return dirs.filter((d) => existsSync(join(projectPath, d)));
}

function scanConfigFiles(projectPath: string): string[] {
  const candidates = [
    'tsconfig.json',
    'package.json',
    '.eslintrc.js',
    '.prettierrc',
    'biome.json',
    'Makefile',
    'Dockerfile',
    'pyproject.toml',
    'Cargo.toml',
    'go.mod',
  ];
  return candidates.filter((c) => existsSync(join(projectPath, c)));
}

function detectScripts(projectPath: string): Record<string, string> {
  if (!existsSync(join(projectPath, 'package.json'))) return {};
  try {
    const pkg = JSON.parse(readFileSync(join(projectPath, 'package.json'), 'utf-8'));
    return pkg.scripts || {};
  } catch {
    return {};
  }
}

// GOV4-01: _execute is NOT exported from barrel.
async function _execute(
  toolName: string,
  _input: Record<string, unknown>,
  context: SkillExecutionContext,
): Promise<SkillExecutionResult> {
  const start = Date.now();

  try {
    switch (toolName) {
      case 'scan_files': {
        const dirs = scanDirectories(context.projectPath);
        return successResult(
          'repo-scanner',
          toolName,
          dirs,
          `Found ${dirs.length} source directories`,
          Date.now() - start,
        );
      }
      case 'build_repository_map': {
        const map = {
          language: detectLanguage(context.projectPath),
          packageManager: detectPackageManager(context.projectPath),
          sourceDirs: scanDirectories(context.projectPath),
          configFiles: scanConfigFiles(context.projectPath),
          commands: detectScripts(context.projectPath),
        };
        return successResult(
          'repo-scanner',
          toolName,
          map,
          `Mapped repository: ${map.sourceDirs.length} dirs, ${map.configFiles.length} configs`,
          Date.now() - start,
        );
      }
      case 'detect_commands': {
        const commands = detectScripts(context.projectPath);
        return successResult(
          'repo-scanner',
          toolName,
          { packageManager: detectPackageManager(context.projectPath), commands },
          `Detected ${Object.keys(commands).length} script(s)`,
          Date.now() - start,
        );
      }
      default:
        return failedResult('repo-scanner', toolName, new Error(`Unknown tool: ${toolName}`), Date.now() - start);
    }
  } catch (err) {
    return failedResult('repo-scanner', toolName, err as Error, Date.now() - start);
  }
}

// GOV4-01: Self-registration.
export function _register(r: SkillRegistry): void {
  r.registerExecutor('repo-scanner', _execute);
}
