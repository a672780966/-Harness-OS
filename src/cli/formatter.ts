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

import type { OutputMode, CliJsonOutput, CliOutputMeta, HarnessError } from '../types.js';
import { redactText } from '../governance/redactor.js';

// ============================================================
// Output Mode Detection
// ============================================================

/**
 * Detect the output mode from CLI flags and environment.
 * Priority: CLI flag > env var > default
 */
export function detectOutputMode(options?: { json?: boolean; quiet?: boolean }): OutputMode {
  if (options?.json) return 'json';
  if (options?.quiet) return 'quiet';
  if (process.env.HARNESS_OUTPUT_MODE === 'json') return 'json';
  if (process.env.HARNESS_OUTPUT_MODE === 'quiet') return 'quiet';
  if (process.env.CI) return 'quiet';
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

export function buildMeta(
  command: string,
  outputMode: OutputMode,
  overrides?: Partial<CliOutputMeta>,
): CliOutputMeta {
  return {
    version: '1.0.0',
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
    data: params.data,
    error: params.error,
    warnings: params.warnings ?? [],
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
export function prettyError(code: string, title: string, recovery?: string, details?: string): void {
  const lines: string[] = [
    `Error: ${code}`,
    '',
    title,
  ];
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
    ...paths.map(p => `  ${p}`),
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
  const colWidths = headers.map((h, i) =>
    Math.max(h.length, ...rows.map(r => (r[i] || '').length)),
  );

  // Header separator
  const separator = `| ${colWidths.map(w => '-'.repeat(w)).join(' | ')} |`;

  // Header
  const header = `| ${headers.map((h, i) => h.padEnd(colWidths[i])).join(' | ')} |`;
  console.log(redactText([header, separator, ...rows.map(r =>
    `| ${r.map((c, i) => (c || '').padEnd(colWidths[i])).join(' | ')} |`,
  )].join('\n')));
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
  // Ensure redacted
  const redacted = { ...output, meta: { ...output.meta, redacted: true } };
  process.stdout.write(JSON.stringify(redacted, null, 2) + '\n');
}

/**
 * Output NDJSON progress event to stdout.
 * Only for --stream mode.
 */
export function jsonProgress(stage: string, message: string): void {
  const event = JSON.stringify({ type: 'progress', stage, message }) + '\n';
  process.stdout.write(event);
}

// ============================================================
// Quiet Formatter
// ============================================================

/**
 * Quiet mode: success produces minimal output.
 */
export function quietSuccess(message?: string): void {
  if (message) process.stdout.write(message + '\n');
}

/**
 * Quiet mode: error outputs error code + message.
 */
export function quietError(code: string, message: string): void {
  process.stderr.write(`${code}: ${message}\n`);
}
