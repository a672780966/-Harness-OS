/**
 * Harness OS — Continuous Learning Foundation
 *
 * Lightweight session pattern observation and memory system.
 * Inspired by everything-claude-code-zh continuous-learning skills.
 *
 * Design:
 * - Observations: record tool call patterns, outcomes, and context signals
 * - ObservationStore: in-memory + JSONL persistence per session
 * - Pattern scoring: frequency-based with recency weighting
 * - Session hooks: capture patterns at PostToolUse and Stop events
 * - Lightweight — no ML, no external service, no vector DB
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { redactObject } from '../governance/redactor.js';

// ============================================================
// Types
// ============================================================

export type ObservationType =
  | 'tool-call'
  | 'tool-result'
  | 'error-pattern'
  | 'task-outcome'
  | 'approval-event'
  | 'user-preference';

export interface Observation {
  /** Unique observation ID. */
  id: string;
  /** When the observation was made. */
  timestamp: string;
  /** Type of observation. */
  type: ObservationType;
  /** Session ID this belongs to. */
  sessionId: string;
  /** The observed signal or pattern. */
  signal: string;
  /** Context: tool name, file, command, etc. */
  context?: string;
  /** Whether the outcome was positive/negative. */
  outcome?: 'success' | 'failure' | 'unknown';
  /** Confidence score (0.0 - 1.0). */
  confidence: number;
  /** How many times this pattern has been seen. */
  frequency: number;
  /** Additional metadata. */
  metadata?: Record<string, unknown>;
}

export interface LearnedPattern {
  /** Canonical signal name. */
  signal: string;
  /** How many times observed. */
  frequency: number;
  /** Average confidence. */
  avgConfidence: number;
  /** Most recent observation timestamp. */
  lastObserved: string;
  /** Most common context. */
  commonContext?: string;
  /** Whether this pattern is actionable. */
  actionable: boolean;
}

// ============================================================
// Observation Store
// ============================================================

const DEFAULT_OBSERVATIONS_FILE = '.claude/observations.jsonl';

export class ObservationStore {
  private observations: Observation[] = [];
  private filePath: string;

  constructor(basePath?: string) {
    this.filePath = basePath ? join(basePath, DEFAULT_OBSERVATIONS_FILE) : DEFAULT_OBSERVATIONS_FILE;

    // Load existing observations
    this.load();
  }

  /**
   * Record a new observation.
   */
  record(obs: Omit<Observation, 'id' | 'timestamp'>): Observation {
    const entry: Observation = {
      ...obs,
      id: `obs_${Date.now().toString(36)}_${this.observations.length.toString(36)}`,
      timestamp: new Date().toISOString(),
    };

    this.observations.push(entry);
    this.append(entry);
    return entry;
  }

  /**
   * Get all observations for a session.
   */
  getBySession(sessionId: string): Observation[] {
    return this.observations.filter((o) => o.sessionId === sessionId);
  }

  /**
   * Get all observations of a type.
   */
  getByType(type: ObservationType): Observation[] {
    return this.observations.filter((o) => o.type === type);
  }

  /**
   * Get recent observations (last N).
   */
  getRecent(limit: number = 50): Observation[] {
    return this.observations.slice(-limit);
  }

  /**
   * Extract learned patterns from observations.
   */
  extractPatterns(minFrequency: number = 2): LearnedPattern[] {
    const groups = new Map<string, Observation[]>();

    for (const obs of this.observations) {
      const key = obs.signal;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(obs);
    }

    const patterns: LearnedPattern[] = [];

    for (const [signal, group] of groups) {
      if (group.length < minFrequency) continue;

      const confidences = group.map((o) => o.confidence);
      const avgConfidence = confidences.reduce((a, b) => a + b, 0) / confidences.length;
      const lastObs = group.reduce((latest, o) => (o.timestamp > latest.timestamp ? o : latest), group[0]);

      // Find most common context
      const contexts = group.filter((o) => o.context).map((o) => o.context!);
      const contextCounts = new Map<string, number>();
      for (const ctx of contexts) {
        contextCounts.set(ctx, (contextCounts.get(ctx) || 0) + 1);
      }
      let commonContext: string | undefined;
      let maxCount = 0;
      for (const [ctx, count] of contextCounts) {
        if (count > maxCount) {
          maxCount = count;
          commonContext = ctx;
        }
      }

      patterns.push({
        signal,
        frequency: group.length,
        avgConfidence,
        lastObserved: lastObs.timestamp,
        commonContext,
        actionable: avgConfidence >= 0.6 && group.length >= minFrequency,
      });
    }

    return patterns.sort((a, b) => b.frequency - a.frequency);
  }

  /**
   * Get total observation count.
   */
  get size(): number {
    return this.observations.length;
  }

  /**
   * Clear all observations (for testing).
   */
  clear(): void {
    this.observations = [];
    writeFileSync(this.filePath, '', 'utf-8');
  }

  // ================================================================
  // Persistence
  // ================================================================

  private ensureDir(): void {
    const dir = dirname(this.filePath);
    if (dir && dir !== '.' && !existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  }

  private load(): void {
    if (!existsSync(this.filePath)) return;
    try {
      const lines = readFileSync(this.filePath, 'utf-8').split('\n').filter(Boolean);
      for (const line of lines) {
        try {
          this.observations.push(JSON.parse(line));
        } catch {
          // skip malformed lines
        }
      }
    } catch {
      // file not readable, start empty
    }
  }

  private append(obs: Observation): void {
    this.ensureDir();
    try {
      const safe = redactObject(obs);
      appendFileSync(this.filePath, JSON.stringify(safe) + '\n', 'utf-8');
    } catch {
      // non-fatal
    }
  }
}

// ============================================================
// Pattern Helpers
// ============================================================

/**
 * Extract a signal name from a tool call for observation.
 */
export function signalFromToolCall(toolName: string, toolInput: Record<string, unknown>): string {
  const parts = [toolName];
  if (typeof toolInput.command === 'string') {
    // Extract first command word
    const cmd = toolInput.command.split(/\s+/)[0];
    if (cmd && cmd.length < 30) parts.push(cmd);
  }
  if (typeof toolInput.file_path === 'string') {
    const ext = toolInput.file_path.split('.').pop();
    if (ext) parts.push(`.${ext}`);
  }
  return parts.join(':');
}

/**
 * Score confidence based on explicit outcome signals.
 */
export function scoreConfidence(outcome: string): number {
  const lower = outcome.toLowerCase();
  if (lower.includes('success') || lower.includes('passed') || lower.includes('completed')) return 0.9;
  if (lower.includes('partial') || lower.includes('warning')) return 0.5;
  if (lower.includes('fail') || lower.includes('error') || lower.includes('denied')) return 0.3;
  return 0.5;
}

// ============================================================
// Singleton
// ============================================================

let _store: ObservationStore | undefined;

export function getObservationStore(basePath?: string): ObservationStore {
  if (!_store) {
    _store = new ObservationStore(basePath);
  }
  return _store;
}

export function resetObservationStore(): void {
  _store = undefined;
}
