/**
 * Harness OS — Redactor + Learning Tests
 *
 * Coverage:
 * - redactText: API keys, tokens, passwords, private keys, DB URLs, .env
 * - redactObject: deep object redaction
 * - isProtectedFile: file path checks
 * - redactFileContent: file-level redaction
 * - countRedactions: reporting
 * - ObservationStore: record, query, extract patterns
 * - signalFromToolCall: learning signal extraction
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { mkdtempSync, rmSync, writeFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

import {
  redactText,
  redactObject,
  redactFileContent,
  isProtectedFile,
  hasProtectedFragment,
  countRedactions,
} from '../../src/governance/redactor.js';

import {
  ObservationStore,
  signalFromToolCall,
  scoreConfidence,
  resetObservationStore,
} from '../../src/learning/index.js';

// ============================================================
// Redactor Tests
// ============================================================

describe('redactText', () => {
  it('redacts OpenAI API keys', () => {
    const result = redactText('sk-abc123def456ghi789jkl012');
    expect(result).toContain('[REDACTED]');
    expect(result).not.toContain('sk-abc123');
  });

  it('redacts Anthropic API keys', () => {
    const result = redactText('sk-ant-abc123def456ghi789jkl012mnop345');
    expect(result).toContain('[REDACTED]');
  });

  it('redacts GitHub tokens', () => {
    const result = redactText('ghp_abcdef123456789012345678901234567890');
    expect(result).toContain('[REDACTED]');
  });

  it('redacts JWT tokens', () => {
    const jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNqPnd9M5J2wKkAJf';
    const result = redactText(jwt);
    expect(result).toContain('[REDACTED]');
  });

  it('redacts password values in JSON-like text', () => {
    const result = redactText('"password": "mysecret123"');
    expect(result).toContain('[REDACTED]');
    expect(result).not.toContain('mysecret123');
  });

  it('redacts private keys', () => {
    const key = `-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0OcDQm
-----END RSA PRIVATE KEY-----`;
    const result = redactText(key);
    expect(result).toContain('[REDACTED]');
  });

  it('redacts database URLs', () => {
    const result = redactText('postgresql://user:password@localhost:5432/db');
    expect(result).toContain('[REDACTED]');
  });

  it('redacts .env file content', () => {
    const result = redactFileContent('DATABASE_URL=postgres://localhost/mydb\nSECRET_KEY=abc123', '.env');
    expect(result).toContain('[REDACTED]');
    expect(result).not.toContain('postgres://localhost/mydb');
  });

  it('returns empty string for empty input', () => {
    expect(redactText('')).toBe('');
  });

  it('handles text with no secrets', () => {
    const result = redactText('Hello world, this is clean text.');
    expect(result).toBe('Hello world, this is clean text.');
  });

  it('redacts multiple secrets in one string', () => {
    const input = 'key=sk-abc123, db=postgresql://user:pass@host/db';
    const result = redactText(input);
    expect(result).toContain('[REDACTED]');
    // DB URL is also redacted
    expect(result).not.toContain('postgresql://');
  });
});

describe('redactObject', () => {
  it('redacts strings in nested objects', () => {
    const obj = {
      name: 'test',
      connection: { password: 'supersecret', url: 'postgresql://user:pass@host/db' },
    };
    const result = redactObject(obj);
    // The password value gets redacted
    expect(JSON.stringify(result)).toContain('[REDACTED]');
    // Name should stay
    expect(result.name).toBe('test');
  });

  it('redacts arrays of strings', () => {
    const arr = ['hello', 'sk-abc123def456ghi789jkl012'];
    const result = redactObject(arr);
    expect(result[0]).toBe('hello');
    expect(result[1]).toContain('[REDACTED]');
  });

  it('handles null', () => {
    expect(redactObject(null)).toBe(null);
  });

  it('handles numbers', () => {
    expect(redactObject(42)).toBe(42);
  });
});

describe('isProtectedFile', () => {
  it('detects .env files', () => {
    expect(isProtectedFile('.env')).toBe(true);
    expect(isProtectedFile('.env.production')).toBe(true);
    expect(isProtectedFile('path/to/.env')).toBe(true);
  });

  it('detects .pem files', () => {
    expect(isProtectedFile('key.pem')).toBe(true);
  });

  it('detects credentials files', () => {
    expect(isProtectedFile('credentials.json')).toBe(true);
    expect(isProtectedFile('service-account.json')).toBe(true);
  });

  it('allows normal source files', () => {
    expect(isProtectedFile('src/index.ts')).toBe(false);
    expect(isProtectedFile('package.json')).toBe(false);
  });
});

describe('hasProtectedFragment', () => {
  it('detects .env in path', () => {
    expect(hasProtectedFragment('config/.env')).toBe(true);
  });

  it('detects credentials in path', () => {
    expect(hasProtectedFragment('config/credentials.json')).toBe(true);
  });

  it('allows normal paths', () => {
    expect(hasProtectedFragment('src/index.ts')).toBe(false);
  });
});

describe('countRedactions', () => {
  it('counts redacted patterns', () => {
    const original = 'key=sk-abc123def456ghi789jkl012 and another sk-xyz789';
    const redacted = redactText(original);
    const report = countRedactions(original, redacted);
    expect(report.totalRedacted).toBeGreaterThanOrEqual(1);
  });
});

describe('redactFileContent', () => {
  it('redacts .env file content specially', () => {
    const content = 'DATABASE_URL=postgres://localhost:5432/mydb\nSECRET_KEY=abc123\nDEBUG=true';
    const result = redactFileContent(content, 'config/.env');
    // Values after '=' should be redacted
    expect(result).toContain('DATABASE_URL=[REDACTED]');
    expect(result).toContain('SECRET_KEY=[REDACTED]');
    expect(result).toContain('DEBUG=[REDACTED]');
  });

  it('applies normal redaction for non-env files', () => {
    const content = 'const apiKey = "sk-abc123def456ghi789jkl012";';
    const result = redactFileContent(content, 'src/index.ts');
    expect(result).toContain('[REDACTED]');
    expect(result).not.toContain('sk-abc123');
  });
});

// ============================================================
// Learning Tests
// ============================================================

describe('ObservationStore', () => {
  let store: ObservationStore;
  let tmpDir: string;

  beforeEach(() => {
    resetObservationStore();
    tmpDir = mkdtempSync(join(tmpdir(), 'harness-learning-test-'));
    store = new ObservationStore(tmpDir);
  });

  afterEach(() => {
    rmSync(tmpDir, { recursive: true, force: true });
  });

  it('records observations', () => {
    const obs = store.record({
      type: 'tool-call',
      sessionId: 'ses_001',
      signal: 'Read:.ts',
      outcome: 'success',
      confidence: 0.9,
      frequency: 1,
    });

    expect(obs.id).toMatch(/^obs_/);
    expect(obs.type).toBe('tool-call');
    expect(obs.signal).toBe('Read:.ts');
    expect(store.size).toBe(1);
  });

  it('queries by session', () => {
    store.record({ type: 'tool-call', sessionId: 'ses_001', signal: 'Read', outcome: 'success', confidence: 0.8, frequency: 1 });
    store.record({ type: 'tool-call', sessionId: 'ses_002', signal: 'Write', outcome: 'success', confidence: 0.8, frequency: 1 });

    const ses1 = store.getBySession('ses_001');
    expect(ses1).toHaveLength(1);
    expect(ses1[0].signal).toBe('Read');
  });

  it('queries by type', () => {
    store.record({ type: 'tool-call', sessionId: 'ses_001', signal: 'Read', outcome: 'success', confidence: 0.8, frequency: 1 });
    store.record({ type: 'error-pattern', sessionId: 'ses_001', signal: 'TypeError', outcome: 'failure', confidence: 0.5, frequency: 1 });

    const errors = store.getByType('error-pattern');
    expect(errors).toHaveLength(1);
  });

  it('extracts patterns with minimum frequency', () => {
    // Add 3 observations of the same signal
    for (let i = 0; i < 3; i++) {
      store.record({
        type: 'tool-call',
        sessionId: 'ses_001',
        signal: 'Bash:pnpm:test',
        context: 'test-runner',
        outcome: 'success',
        confidence: 0.9,
        frequency: 1,
      });
    }
    // Add 1 different signal
    store.record({
      type: 'tool-call',
      sessionId: 'ses_001',
      signal: 'Read:.ts',
      context: 'code-reading',
      outcome: 'success',
      confidence: 0.8,
      frequency: 1,
    });

    const patterns = store.extractPatterns(2); // min frequency 2
    expect(patterns).toHaveLength(1); // only Bash:pnpm:test appears 3 times
    expect(patterns[0].signal).toBe('Bash:pnpm:test');
    expect(patterns[0].frequency).toBe(3);
    expect(patterns[0].actionable).toBe(true);
  });

  it('persists to JSONL file', () => {
    store.record({ type: 'tool-call', sessionId: 'ses_001', signal: 'Read', outcome: 'success', confidence: 0.8, frequency: 1 });

    // Create new store instance with same path — should load from file
    const store2 = new ObservationStore(tmpDir);
    expect(store2.size).toBe(1);
  });
});

describe('signalFromToolCall', () => {
  it('extracts signal from Read tool', () => {
    const signal = signalFromToolCall('Read', { file_path: 'src/index.ts' });
    expect(signal).toBe('Read:.ts');
  });

  it('extracts signal from Bash tool', () => {
    const signal = signalFromToolCall('Bash', { command: 'pnpm test --run' });
    expect(signal).toBe('Bash:pnpm');
  });

  it('handles unknown tools gracefully', () => {
    const signal = signalFromToolCall('UnknownTool', {});
    expect(signal).toBe('UnknownTool');
  });
});

describe('scoreConfidence', () => {
  it('scores success high', () => {
    expect(scoreConfidence('completed successfully')).toBe(0.9);
    expect(scoreConfidence('passed')).toBe(0.9);
  });

  it('scores failure low', () => {
    expect(scoreConfidence('failed with error')).toBe(0.3);
  });

  it('scores unknown medium', () => {
    expect(scoreConfidence('something else')).toBe(0.5);
  });
});
