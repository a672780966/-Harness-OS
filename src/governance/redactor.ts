/**
 * Harness OS — Secret Redactor
 *
 * Phase 5: Secret detection and redaction for all text, objects, and file outputs.
 *
 * Source: 08_GOVERNANCE_SECURITY.md §13
 *
 * Design:
 * - Pattern-based detection (no ML, no external service)
 * - Unified replacement: [REDACTED]
 * - Functions: redactText, redactObject, isProtectedFile, redactFileContent
 * - Must be applied to all outputs: Context Pack, reports, logs, PRs, commits
 */

import type { HarnessError } from '../types.js';
import { writeFileSync } from 'fs';

// ============================================================
// Secret Patterns
// ============================================================

interface SecretPattern {
  name: string;
  pattern: RegExp;
  /** If true, the matched value is replaced entirely. If false, only the value portion is redacted. */
  replaceFull: boolean;
}

const SECRET_PATTERNS: SecretPattern[] = [
  // API Keys
  { name: 'openai-key', pattern: /sk-[A-Za-z0-9]{20,}/g, replaceFull: true },
  { name: 'anthropic-key', pattern: /sk-ant-[A-Za-z0-9]{20,}/g, replaceFull: true },
  { name: 'api-key', pattern: /(['"]?api[_-]?key['"]?\s*[:=]\s*['"])[^'"]+(['"])/gi, replaceFull: false },

  // Tokens
  { name: 'bearer-token', pattern: /Bearer\s+[A-Za-z0-9_\-.]{8,}/g, replaceFull: true },
  { name: 'basic-auth', pattern: /Basic\s+[A-Za-z0-9+/=]{8,}/g, replaceFull: true },
  { name: 'github-token', pattern: /ghp_[A-Za-z0-9]{8,}/g, replaceFull: true },
  { name: 'gitlab-token', pattern: /glpat-[A-Za-z0-9_-]{8,}/g, replaceFull: true },
  { name: 'slack-token', pattern: /xox[baprs]-[A-Za-z0-9_-]{8,}/g, replaceFull: true },
  { name: 'jwt-token', pattern: /eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g, replaceFull: true },

  // Passwords
  { name: 'password', pattern: /(['"]?passw[o0]rd['"]?\s*[:=]\s*['"])[^'"]+(['"])/gi, replaceFull: false },
  { name: 'pwd', pattern: /(['"]?pwd['"]?\s*[:=]\s*['"])[^'"]+(['"])/gi, replaceFull: false },

  // Private Keys
  { name: 'private-key', pattern: /-----BEGIN\s+.*PRIVATE\s+KEY-----[\s\S]*?-----END\s+.*PRIVATE\s+KEY-----/g, replaceFull: true },
  { name: 'ssh-key', pattern: /ssh-(rsa|ed25519|ecdsa)\s+[A-Za-z0-9+/]{4,}[=]*/g, replaceFull: true },

  // Database URLs
  { name: 'db-url', pattern: /(postgresql?|mysql|mongodb|redis|rediss):\/\/[^\s]+/gi, replaceFull: true },

  // Cloud Credentials
  { name: 'aws-key', pattern: /(['"]?aws_access_key_id['"]?\s*[:=]\s*['"])[^'"]+(['"])/gi, replaceFull: false },
  { name: 'aws-secret', pattern: /(['"]?aws_secret_access_key['"]?\s*[:=]\s*['"])[^'"]+(['"])/gi, replaceFull: false },
  { name: 'azure-conn', pattern: /DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[^;]+/g, replaceFull: true },

  // Authorization header (generic)
  { name: 'auth-header', pattern: /(Authorization|Proxy-Authorization):\s*[A-Za-z0-9+/=_\-.\s]{8,}/gi, replaceFull: true },

  // URL query parameter secrets
  { name: 'url-query-secret', pattern: /[?&](api_key|apikey|secret|token|password|access_token)=[^&\s]+/gi, replaceFull: true },

  // Audit canary (SEC3-05)
  { name: 'audit-canary', pattern: /HARNESS_AUDIT_SECRET_[A-Za-z0-9]+/g, replaceFull: true },

  // Generic sensitive patterns
  { name: 'generic-secret', pattern: /(['"]?secret['"]?\s*[:=]\s*['"])[^'"]+(['"])/gi, replaceFull: false },
  { name: 'generic-token', pattern: /(['"]?token['"]?\s*[:=]\s*['"])[^'"]+(['"])/gi, replaceFull: false },
];

// ============================================================
// Protected Files
// ============================================================

const PROTECTED_FILE_PATTERNS = [
  /\.env$/,
  /\.env\.\w+$/,
  /\.pem$/,
  /\.key$/,
  /id_rsa$/,
  /id_ed25519$/,
  /credentials\.json$/,
  /service-account\.json$/,
  /\.token$/,
  /\.secret$/,
  /oauth.*\.json$/i,
];

const PROTECTED_PATH_FRAGMENTS = [
  '.env',
  '.pem',
  '.key',
  'id_rsa',
  'id_ed25519',
  'credentials',
  'service-account',
  'secrets/',
  'tokens/',
];

// ============================================================
// Redaction
// ============================================================

const REDACTED = '[REDACTED]';

// SEC3-05: Test canary for regression tests — never appears in output.
export const AUDIT_CANARY = 'HARNESS_AUDIT_SECRET_7f31c9';

/**
 * Redact secrets from a text string.
 * Replaces all detected secret values with [REDACTED].
 */
export function redactText(text: string): string {
  if (!text) return text;

  let result = text;
  for (const sp of SECRET_PATTERNS) {
    result = result.replace(sp.pattern, (fullMatch: string, ...captures: string[]) => {
      if (sp.replaceFull) {
        return REDACTED;
      }
      // captures = [p1, p2, ..., offset, string, namedGroups]
      // p1 = prefix before the value (e.g., `"password": "`)
      // p2 = suffix after the value (e.g., `"`)
      if (captures.length >= 3) {
        const prefix = captures[0];
        const suffix = captures[1];
        if (typeof prefix === 'string' && typeof suffix === 'string') {
          return `${prefix}${REDACTED}${suffix}`;
        }
      }
      return REDACTED;
    });
  }

  return result;
}

/**
 * Deep-redact secrets from any JSON-serializable object.
 * Recursively walks object properties and array elements.
 *
 * SEC3-01: Sensitive KEY names are PRESERVED, only VALUES are replaced.
 * No key collision or overwrite can occur.
 */
export function redactObject<T>(obj: T): T {
  if (typeof obj === 'string') {
    return redactText(obj) as unknown as T;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => redactObject(item)) as unknown as T;
  }

  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      // SEC3-01: Keep the key name, redact the value if key is sensitive.
      // NEVER rename the key to [REDACTED] — that would cause overwrite.
      if (redactKeyName(key)) {
        // Sensitive key → redact the entire value
        result[key] = REDACTED;
      } else {
        // Non-sensitive key → recurse into value
        result[key] = redactObject(value);
      }
    }
    return result as unknown as T;
  }

  return obj;
}

/**
 * Check if a key name suggests it contains sensitive data.
 * Case-insensitive (SEC3-01).
 */
function redactKeyName(key: string): boolean {
  const lower = key.toLowerCase();
  const sensitiveKeys = [
    'password', 'secret', 'token', 'apikey', 'api_key',
    'privatekey', 'private_key', 'accesstoken', 'access_token',
    'authtoken', 'auth_token', 'credentials', 'credential',
  ];
  return sensitiveKeys.includes(lower);
}

// ============================================================
// Protected File Checks
// ============================================================

/**
 * Check if a file path is a protected file (shouldn't be read/written freely).
 */
export function isProtectedFile(filePath: string): boolean {
  for (const pattern of PROTECTED_FILE_PATTERNS) {
    if (pattern.test(filePath)) return true;
  }
  return false;
}

/**
 * Check if a path contains protected path fragments.
 */
export function hasProtectedFragment(filePath: string): boolean {
  const normalized = filePath.replace(/\\/g, '/');
  for (const fragment of PROTECTED_PATH_FRAGMENTS) {
    if (normalized.includes(fragment)) return true;
  }
  return false;
}

// ============================================================
// File Content Redaction
// ============================================================

/**
 * Redact secrets from file content.
 * Applies text redaction and also handles .env-style files specially.
 */
export function redactFileContent(content: string, filePath?: string): string {
  let result = redactText(content);

  // For .env files or env-like content, redact all values after '='
  if (filePath && (filePath.includes('.env') || filePath.endsWith('.env'))) {
    result = result.replace(/^([A-Za-z_][A-Za-z0-9_]*)=.*$/gm, '$1=[REDACTED]');
  }

  return result;
}

// ============================================================
// Error Redaction
// ============================================================

/**
 * Redact secrets from a HarnessError object.
 */
export function redactError(error: HarnessError): HarnessError {
  return {
    ...error,
    message: redactText(error.message),
    details: error.details ? redactObject(error.details) : undefined,
  };
}

// ============================================================
// Batch Redaction
// ============================================================

export interface RedactionReport {
  totalRedacted: number;
  patterns: Record<string, number>;
}

/**
 * Count redactions in text (for reporting).
 */
export function countRedactions(original: string, redacted: string): RedactionReport {
  const report: RedactionReport = { totalRedacted: 0, patterns: {} };

  for (const sp of SECRET_PATTERNS) {
    const matches = original.match(sp.pattern);
    if (matches) {
      const count = matches.length;
      report.totalRedacted += count;
      report.patterns[sp.name] = count;
    }
  }

  return report;
}

// ============================================================
// Safe Serialization Helpers (SEC-01)
//
// Unified redaction-gated output functions for all write boundaries.
// All CLI and file write boundaries MUST use these, never raw:
//   - JSON.stringify(untrustedData)
//   - writeFileSync(...raw...)
//   - console.log(untrustedData)
// ============================================================

/**
 * Safely JSON-stringify a value with deep secret redaction.
 * Returns the redacted JSON string. Never outputs raw secrets.
 */
export function safeJsonStringify(value: unknown, space?: number): string {
  const redacted = redactObject(value);
  return JSON.stringify(redacted, null, space) ?? '';
}

/**
 * Safely write a JSON-serializable object to a file, with deep secret redaction.
 * The file is written only after all secrets are redacted.
 */
export function safeWriteJson(path: string, value: unknown, space?: number): void {
  const json = safeJsonStringify(value, space);
  writeFileSync(path, json, 'utf-8');
}

/**
 * Safely write text content to a file, with secret redaction.
 * The file is written only after all secrets are redacted.
 */
export function safeWriteText(path: string, text: string): void {
  const redacted = redactText(text);
  writeFileSync(path, redacted, 'utf-8');
}

/**
 * Safely format text for human-readable output with secret redaction.
 */
export function safeTextOutput(text: string): string {
  return redactText(text);
}
