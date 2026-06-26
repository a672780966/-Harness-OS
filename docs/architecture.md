# Harness OS Architecture

## Core Concept

Harness OS is a **governance-first production loop for AI coding agents**. It treats AI-generated code as a production process, not a chat session.

## The Loop

```
Codex (Planner)
    ↓ TaskEnvelope
Worker (OpenCode / Claude Code)
    ↓ ResultEnvelope
Open Code Review
    ↓ ReviewEnvelope
Codex (Advanced Review)
    ↓ FinalEvidence + Audit
Merge Gate / Human Approval
```

## Role Separation

| Role | Responsibility |
|------|---------------|
| **Codex** | Planner, reviewer, final gatekeeper, emergency implementer |
| **Hermes** | Dispatcher, evidence collector (NOT planner or judge) |
| **OpenCode / Claude Code** | Implementation worker + self-reviewer |
| **Open Code Review** | First review gate, blocking/non-blocking issues |

## Evidence Hierarchy

1. Security and policy rules
2. Test results
3. Audit events
4. Code review results
5. Git diff and changed files
6. Worker result envelope
7. Memory or summaries

Worker claims are NOT treated as truth. Evidence is.

## Key Artifacts

| Artifact | Location |
|----------|----------|
| Task envelopes | `.harness/envelopes/task/` |
| Result envelopes | `.harness/envelopes/result/` |
| Review envelopes | `.harness/envelopes/review/` |
| Final evidence | `.harness/envelopes/final/` |
| Audit logs | `.harness/audit/logs/` |
| State machine | `.harness/state/` |
| Loop traces | `.harness/temp_loop/<trace_id>/` |

## CLI Surface

40 commands organized into: inspection, diff analysis, task cards, readiness, dashboards, live events, PR management, provider health, loop setup, monitoring.
