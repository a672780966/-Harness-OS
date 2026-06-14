import { SkillManifest } from '../../types.js';
import { existsSync, readFileSync, writeFileSync, readdirSync, mkdirSync, realpathSync } from 'fs';
import { join, resolve, relative } from 'path';
import {
  type SkillExecutionContext,
  type SkillExecutionResult,
  successResult,
  failedResult,
  blockedResult,
} from '../executor.js';
import { redactText } from '../../governance/redactor.js';

// ============================================================
// JSON Schemas
// ============================================================

const readFileSchema = {
  type: 'object',
  properties: { path: { type: 'string' }, startLine: { type: 'number' }, endLine: { type: 'number' } },
  required: ['path'],
};
const writeFileSchema = {
  type: 'object',
  properties: { path: { type: 'string' }, content: { type: 'string' }, createIfMissing: { type: 'boolean' } },
  required: ['path', 'content'],
};
const listDirSchema = {
  type: 'object',
  properties: { path: { type: 'string' }, recursive: { type: 'boolean' } },
  required: ['path'],
};
const searchTextSchema = {
  type: 'object',
  properties: { pattern: { type: 'string' }, path: { type: 'string' } },
  required: ['pattern'],
};
const deleteFileSchema = { type: 'object', properties: { path: { type: 'string' } }, required: ['path'] };

export const manifest: SkillManifest = {
  name: 'filesystem',
  version: '1.0.0',
  description: 'Read, write, and manage project files within workspace boundary',
  category: 'filesystem',
  defaultEnabled: true,
  requiresNetwork: false,
  requiresFilesystem: true,
  riskLevel: 'medium',
  docPath: 'src/skills/filesystem/SKILL.md',
  permissions: [
    { type: 'filesystem-read', description: 'Read workspace files' },
    { type: 'filesystem-write', description: 'Write and edit workspace files' },
  ],
  tools: [
    {
      name: 'read_file',
      description: 'Read file contents with optional line range',
      inputSchema: readFileSchema,
      outputSchema: { type: 'object', properties: { content: { type: 'string' }, path: { type: 'string' } } },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 10000,
    },
    {
      name: 'write_file',
      description: 'Write content to a file',
      inputSchema: writeFileSchema,
      outputSchema: { type: 'object', properties: { path: { type: 'string' }, size: { type: 'number' } } },
      riskLevel: 'medium',
      requiresApproval: false,
      timeoutMs: 10000,
    },
    {
      name: 'list_dir',
      description: 'List directory contents',
      inputSchema: listDirSchema,
      outputSchema: { type: 'array', items: { type: 'string' } },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 5000,
    },
    {
      name: 'search_text',
      description: 'Search text patterns in files',
      inputSchema: searchTextSchema,
      outputSchema: {
        type: 'array',
        items: {
          type: 'object',
          properties: { path: { type: 'string' }, line: { type: 'number' }, match: { type: 'string' } },
        },
      },
      riskLevel: 'low',
      requiresApproval: false,
      timeoutMs: 30000,
    },
    {
      name: 'delete_file',
      description: 'Delete a file (requires approval)',
      inputSchema: deleteFileSchema,
      outputSchema: { type: 'object', properties: { path: { type: 'string' }, deleted: { type: 'boolean' } } },
      riskLevel: 'high',
      requiresApproval: true,
      timeoutMs: 5000,
    },
  ],
};

// ============================================================
// Executor
// ============================================================

function safeResolve(inputPath: string, basePath: string): string {
  // Reject empty and absolute input paths (relative paths only)
  if (!inputPath || !inputPath.trim()) {
    throw new Error(`Path is empty`);
  }

  // Normalize path separators
  const normalizedInput = inputPath.replace(/\\/g, '/');

  // Reject UNC paths and absolute paths
  if (
    normalizedInput.startsWith('//') ||
    normalizedInput.startsWith('\\\\') ||
    normalizedInput.match(/^[A-Za-z]:\\/) ||
    normalizedInput.match(/^[A-Za-z]:\//) ||
    normalizedInput.startsWith('/')
  ) {
    throw new Error(`Path escape detected: absolute/UNC path not allowed: ${redactText(inputPath)}`);
  }

  // Resolve the full path
  const base = resolve(basePath);
  const resolved = resolve(basePath, normalizedInput);

  // --- Symlink-aware boundary check ---
  // To handle symlink/junction escapes, we need to check the realpath
  // of the resolved path (if it exists) or its nearest existing parent.

  function isWithinBase(target: string, baseCanonical: string): boolean {
    const rel = relative(baseCanonical, target);
    // relative() returns '' if target === base, or starts with '..' if outside
    return rel === '' || !rel.startsWith('..');
  }

  // Check logical resolved path first
  if (!isWithinBase(resolved, base)) {
    throw new Error(`Path escape detected: ${redactText(inputPath)} resolves outside workspace`);
  }

  // For existing paths, verify realpath
  let resolvedReal: string | undefined;
  try {
    resolvedReal = realpathSync(resolved);
  } catch {
    // Path doesn't exist yet — check parent directory's realpath to prevent
    // symlink/junction escape via parent.
    // Skip when the path resolves to base itself ('./' or '.')
    if (resolved !== base) {
      try {
        const parentDir = resolve(resolved, '..');
        const parentReal = realpathSync(parentDir);
        const newFilePath = join(parentReal, relative(base, resolved));
        if (!isWithinBase(newFilePath, base)) {
          throw new Error(`Path escape detected via parent symlink: ${redactText(inputPath)}`);
        }
      } catch (pathErr) {
        if (pathErr instanceof Error && pathErr.message.includes('Path escape')) {
          throw pathErr;
        }
        // Parent doesn't exist either — use logical path (already checked above)
      }
    }
  }

  // If realpath resolved and differs from logical path, verify realpath is within base
  if (resolvedReal && resolvedReal !== resolved) {
    if (!isWithinBase(resolvedReal, base)) {
      throw new Error(
        `Path escape detected via symlink: ${redactText(inputPath)} resolves to ${redactText(resolvedReal)}`,
      );
    }
    return resolvedReal;
  }

  return resolved;
}

// GOV4-01: _execute is NOT exported — raw executors cannot be reached from
// public API. Skills self-register via _register() below.
import { type SkillRegistry } from '../registry.js';

async function _execute(
  toolName: string,
  input: Record<string, unknown>,
  context: SkillExecutionContext,
): Promise<SkillExecutionResult> {
  const start = Date.now();
  const base = context.projectPath;

  try {
    switch (toolName) {
      case 'read_file': {
        const path = safeResolve(input.path as string, base);
        if (!existsSync(path))
          return failedResult('filesystem', toolName, new Error(`Not found: ${input.path}`), Date.now() - start);
        let content = readFileSync(path, 'utf-8');
        const sl = input.startLine as number | undefined;
        const el = input.endLine as number | undefined;
        if (sl || el) {
          const lines = content.split('\n');
          content = lines
            .slice(sl ? Math.max(0, sl - 1) : 0, el ? Math.min(lines.length, el) : lines.length)
            .join('\n');
        }
        return successResult(
          'filesystem',
          toolName,
          { path: input.path, content },
          `Read ${input.path}`,
          Date.now() - start,
        );
      }
      case 'write_file': {
        const path = safeResolve(input.path as string, base);
        const dir =
          path.includes('/') || path.includes('\\')
            ? path.substring(0, Math.max(path.lastIndexOf('/'), path.lastIndexOf('\\')))
            : '.';
        if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
        writeFileSync(path, String(input.content ?? ''), 'utf-8');
        return successResult(
          'filesystem',
          toolName,
          { path: input.path, size: String(input.content ?? '').length },
          `Written ${input.path}`,
          Date.now() - start,
        );
      }
      case 'list_dir': {
        const path = safeResolve(input.path as string, base);
        if (!existsSync(path))
          return failedResult('filesystem', toolName, new Error(`Not found: ${input.path}`), Date.now() - start);
        return successResult('filesystem', toolName, readdirSync(path), `Listed ${path}`, Date.now() - start);
      }
      case 'delete_file':
        return blockedResult('filesystem', toolName, 'delete_file requires human approval', Date.now() - start);
      default:
        return failedResult('filesystem', toolName, new Error(`Unknown tool: ${toolName}`), Date.now() - start);
    }
  } catch (err) {
    return failedResult('filesystem', toolName, err as Error, Date.now() - start);
  }
}

// GOV4-01: Self-registration — called by registry.ts at import time.
// Only entry point for executor registration; _execute is module-private.
export function _register(r: SkillRegistry): void {
  r.registerExecutor('filesystem', _execute);
}
