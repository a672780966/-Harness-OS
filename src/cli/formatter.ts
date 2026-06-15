/**
 * Harness OS — CLI Formatter
 *
 * Standardized output formatting for all CLI commands.
 * Supports pretty (human), json (machine), quiet (minimal) modes.
 *
 * Output rules:
 * - stdout: normal results, JSON, success summaries
 * - stderr: errors, warnings, progress, debug logs
 * - JSON mode: stdout contains ONLY valid JSON
 * - Quiet mode: minimal output, errors only
 *
 * Reference: 16_CLI_OUTPUT_CONTRACT.md §5-7, §23
 */

import {
  type OutputMode,
  type CliJsonOutput,
  type CliOutputMeta,
  type HarnessError,
  HarnessExitCode,
} from '../types.js';
import { redactText, redactObject } from '../governance/redactor.js';
import { HARNESS_VERSION } from '../version.js';

// ============================================================
// Output Mode Detection
// ============================================================

/**
 * Detect the output mode from CLI flags and environment.
 * Priority: CLI flag > env var > default
 */
export function detectOutputMode(options?: { json?: boolean; quiet?: boolean }): OutputMode {
  // Priority: --json > --quiet > HARNESS_OUTPUT_MODE env > pretty (default)
  if (options?.json) return 'json';
  if (options?.quiet) return 'quiet';
  if (process.env.HARNESS_OUTPUT_MODE === 'json') return 'json';
  if (process.env.HARNESS_OUTPUT_MODE === 'quiet') return 'quiet';
  // CI=true does NOT implicitly change default output mode.
  // Use --quiet, --json, or HARNESS_OUTPUT_MODE explicitly.
  return 'pretty';
}

/**
 * Detect if the environment is non-interactive.
 */
export function isNonInteractive(): boolean {
  return !!(process.env.HARNESS_NON_INTERACTIVE || process.env.CI);
}

/**
 * Detect if color output is allowed.
 */
export function isColorAllowed(): boolean {
  if (process.env.NO_COLOR || process.env.HARNESS_NO_COLOR || process.env.CI) return false;
  return process.stdout.isTTY ?? false;
}

// ============================================================
// Meta Builder
// ============================================================

let _startTime = Date.now();

export function buildMeta(command: string, outputMode: OutputMode, overrides?: Partial<CliOutputMeta>): CliOutputMeta {
  return {
    version: HARNESS_VERSION,
    outputMode,
    generatedAt: new Date().toISOString(),
    durationMs: Date.now() - _startTime,
    redacted: true,
    ...overrides,
  };
}

export function resetStartTime(): void {
  _startTime = Date.now();
}

// ============================================================
// JSON Output Builder
// ============================================================

export function buildJsonOutput<T>(params: {
  command: string;
  status: CliJsonOutput['status'];
  data?: T;
  error?: HarnessError;
  warnings?: Array<{ code: string; message: string; recoveryHint?: string }>;
  metaOverrides?: Partial<CliOutputMeta>;
}): CliJsonOutput<T> {
  return {
    ok: params.status === 'success',
    command: params.command,
    status: params.status,
    data: params.data ? redactObject(params.data) : undefined,
    error: params.error ? (redactObject(params.error) as unknown as HarnessError) : undefined,
    warnings:
      params.warnings?.map((w) => ({
        ...w,
        message: redactText(w.message),
        recoveryHint: w.recoveryHint ? redactText(w.recoveryHint) : undefined,
      })) ?? [],
    meta: buildMeta(params.command, 'json', params.metaOverrides),
  };
}

// ============================================================
// Pretty Formatter
// ============================================================

/**
 * Format success output in pretty (human-readable) mode.
 * Output goes to stdout.
 */
export function prettySuccess(title: string, details: Record<string, string>, next?: string[]): void {
  const lines: string[] = [title, ''];
  for (const [key, value] of Object.entries(details)) {
    lines.push(`${key}: ${value}`);
  }
  if (next && next.length > 0) {
    lines.push('', 'Next:');
    for (const n of next) lines.push(`  ${n}`);
  }
  lines.push('');
  console.log(redactText(lines.join('\n')));
}

/**
 * Format error output in pretty mode.
 * Output goes to stderr.
 */
export function prettyError(code: string, title: string, recovery?: string | null, details?: string): void {
  const lines: string[] = [`Error: ${code}`, '', title];
  if (recovery) lines.push('', 'Recovery:', recovery);
  if (details) lines.push('', 'Details:', details);
  console.error(redactText(lines.join('\n')));
}

/**
 * Format a warning in pretty mode.
 */
export function prettyWarning(code: string, message: string, recoveryHint?: string): void {
  const lines = [`Warning: ${code}`, '', message];
  if (recoveryHint) lines.push('', 'Recovery:', recoveryHint);
  console.error(redactText(lines.join('\n')));
}

/**
 * Format approval prompt in pretty mode.
 */
export function prettyApprovalPrompt(action: string, riskLevel: string, reason: string, paths: string[]): void {
  const lines = [
    'Approval required',
    '',
    `Action: ${action}`,
    `Risk: ${riskLevel}`,
    `Reason: ${reason}`,
    '',
    'Affected paths:',
    ...paths.map((p) => `  ${p}`),
    '',
    'Approve? [y/N] ',
  ];
  console.error(redactText(lines.join('\n')));
}

/**
 * Format a table in pretty mode.
 */
export function prettyTable(headers: string[], rows: string[][]): void {
  // Calculate column widths
  const colWidths = headers.map((h, i) => Math.max(h.length, ...rows.map((r) => (r[i] || '').length)));

  // Header separator
  const separator = `| ${colWidths.map((w) => '-'.repeat(w)).join(' | ')} |`;

  // Header
  const header = `| ${headers.map((h, i) => h.padEnd(colWidths[i])).join(' | ')} |`;
  console.log(
    redactText(
      [
        header,
        separator,
        ...rows.map((r) => `| ${r.map((c, i) => (c || '').padEnd(colWidths[i])).join(' | ')} |`),
      ].join('\n'),
    ),
  );
}

/**
 * Format a progress message in pretty mode (stderr).
 */
export function prettyProgress(message: string): void {
  console.error(redactText(message));
}

// ============================================================
// JSON Formatter
// ============================================================

/**
 * Output JSON result to stdout.
 * JSON mode: stdout MUST contain ONLY valid JSON.
 */
export function jsonOutput<T>(output: CliJsonOutput<T>): void {
  // Deep-redact entire output before serialization (SEC-02)
  const redacted = redactObject({
    ...output,
    meta: { ...output.meta, redacted: true },
  });
  process.stdout.write(JSON.stringify(redacted, null, 2) + '\n');
}

/**
 * Output NDJSON progress event to stdout.
 * Only for --stream mode.
 */
export function jsonProgress(stage: string, message: string): void {
  const event = redactObject({ type: 'progress', stage, message });
  process.stdout.write(JSON.stringify(event) + '\n');
}

// ============================================================
// Quiet Formatter
// ============================================================

/**
 * Quiet mode: success produces minimal output.
 */
export function quietSuccess(message?: string): void {
  if (message) process.stdout.write(redactText(message) + '\n');
}

/**
 * Quiet mode: error outputs error code + message.
 */
export function quietError(code: string, message: string): void {
  process.stderr.write(`${code}: ${redactText(message)}\n`);
}

// ============================================================
// Unified CLI Command Output (CLI-01/03/05/06)
//
// runCliCommand handles the common pattern:
//   1. JSON output with envelope
//   2. Pretty output via callback
//   3. Quiet output via callback
//   4. Error output with exit code
//
// Ensures every command has consistent JSON, exit code, and error handling.
// ============================================================

export interface CliCommandHandlers<T> {
  /** Build data payload for JSON mode. */
  jsonData: () => T;
  /** Pretty mode output (stdout). */
  pretty: () => void;
  /** Quiet mode output — return a short string or undefined. */
  quiet?: () => string | undefined;
}

export interface CliCommandResult {
  exitCode: number;
}

/**
 * Run a CLI command with consistent output routing, JSON envelope, and exit code.
 *
 * @param commandName - Command name for JSON envelope (e.g. "config", "check")
 * @param mode - Detected output mode
 * @param handlers - Per-mode callbacks (supports both sync and async)
 * @param errorHandler - Optional custom error handler (default: prettyError/json)
 */
export async function runCliCommand<T>(
  commandName: string,
  mode: OutputMode,
  handlers: CliCommandHandlers<T>,
): Promise<CliCommandResult> {
  try {
    if (mode === 'json') {
      const data = await handlers.jsonData();
      jsonOutput(
        buildJsonOutput({
          command: commandName,
          status: 'success',
          data,
        }),
      );
    } else if (mode === 'quiet') {
      const msg = await handlers.quiet?.();
      if (msg) quietSuccess(msg);
    } else {
      await handlers.pretty();
    }
    return { exitCode: 0 };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const error: HarnessError = {
      code: 'ERR_INTERNAL',
      category: 'cli',
      severity: 'error',
      message,
      recoveryHint: 'Check the error and try again',
      recoverable: true,
      retryable: false,
      userActionRequired: true,
      createdAt: new Date().toISOString(),
    };
    if (mode === 'json') {
      jsonOutput(buildJsonOutput({ command: commandName, status: 'failed', error }));
    } else if (mode === 'quiet') {
      quietError(error.code, error.message);
    } else {
      prettyError(error.code, error.message, error.recoveryHint);
    }
    return { exitCode: HarnessExitCode.INTERNAL_ERROR };
  }
}
