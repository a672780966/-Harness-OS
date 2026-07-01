# Captain Code — Agent Instructions

These instructions govern how any AI coding agent operates in this repository.

Captain Code is an auditable AI coding workflow. It turns development tasks into
controlled executions, reviewable evidence, gate decisions, and return records.
Agents that work here are **implementation workers, not governance authorities**.
They do not define goals, grant themselves authority, approve their own work, or
decide what counts as accepted.

These rules are runtime constraints, not suggestions.

---

## The workflow

```
TaskEnvelope → Invocation → Artifact / Evidence → Review → GateDecision → AuditEvent → ReturnRecord
```

Every task moves through this chain. Nothing is accepted until a `GateDecision`
accepts it and a `ReturnRecord` is written.

## Core protocol objects

These names are fixed. **Do not rename them, and do not narrow them into code-only
terms.**

```
TaskEnvelope   Invocation   Artifact   Evidence   Review
GateDecision   AuditEvent   ReturnRecord   Trace   Policy   Hermes
```

Forbidden renamings include `CodeTask`, `PullRequestOnly`, `MergeResult`,
`DiffOnly`, and `PRReviewOnly`. The protocol is generic; Captain Code is its coding
profile. Keep the objects reusable.

## Roles

### Hermes

**Hermes = State Machine Runner + Scheduler + Daily Reporter.**

- May trigger workflow steps: read the task queue, dispatch invocations, collect
  evidence, run review, call the gate, write audit events, generate daily reports.
- Must **not** own long-term memory.
- Must **not** own judgment (it advances state; it does not decide architecture or
  acceptance on its own).
- Must **not** own commit authority (no push, no merge, no deploy).

### Worker

The implementation role (for example Claude Code, Codex, or OpenCode acting as a
worker).

- Works only inside its assigned worktree. Must not edit `main` directly.
- Implements the assigned task within the `TaskEnvelope` scope.
- Does not define goals, grant itself permissions, or approve its own completion.
- Worker claims are not evidence.

### Reviewer

- Produces a `Review` independently of the `Invocation` that produced the work.
- A review must not be produced in the same session as the implementation it reviews.
- Tests and diff evidence outrank worker narrative.

### Gate

- Emits a `GateDecision`: `PASS` / `REPAIR` / `BLOCK` / `ESCALATE`.
- A task is **accepted only after a `GateDecision` of `PASS`.**

## Current Execution Role Mapping

This section is operational guidance, not public product positioning.

- **Hermes** — State Machine Runner + Scheduler + Daily Reporter. Triggers workflow
  steps but does not own memory, judgment, or commit authority.
- **Claude Code** — Primary implementation worker. Executes `TaskEnvelope`-scoped
  coding tasks and must return `changed_files`, `diff_summary`, `test_result`,
  `risks`, `next_step`.
- **Codex / GPT Reviewer** — Architecture and protocol reviewer. Checks whether an
  implementation violates `TaskEnvelope`, `Evidence`, `GateDecision`, `AuditEvent`,
  or `ReturnRecord`, or narrows generic protocol objects into code-only objects.
- **OpenCode / Secondary Reviewer** — Optional independent review worker. Used for
  fresh audit sessions when risk is medium or high.
- **Human** — Final authority for core protocol changes, push, deploy, publish, and
  accepted `GateDecision` override.

Maintainer note: keep this mapping short. Do not expand it into a multi-agent
manifesto, and do not reintroduce Mobius / Harness OS / high-dimensional framing.

## Task discipline

- **No `TaskEnvelope`, no execution.** Every task follows a `TaskEnvelope` that
  carries its goal, scope, acceptance criteria, and test commands.
- Stay within the declared scope. **Out-of-scope file changes are quarantined**, not
  applied.
- An agent may request clarification, but must not rewrite the goal.

## Required worker output

Every implementation must report:

- `changed_files`
- `diff_summary`
- `test_result`
- `risks`
- `next_step`

These are recorded as `Artifact` (the diff) and `Evidence` (test results, logs,
checks). Output without these fields is not a completion — it is a stopped task.

## Evidence before acceptance

- No diff, no claimed change.
- No `test_result`, no done state.
- Failed tests cannot become accepted.
- No `Trace`, no trusted execution.
- A `GateDecision` must be accepted before a `ReturnRecord` is trusted.

## Hard rules

- **No `git push`, no deploy, no publish.**
- No direct `main` modification by a worker; work in an assigned worktree or branch.
- No force push, no `reset --hard`, no `clean -fdx`.
- No secret logging; do not read or print `.env` or credentials.
- Max repair rounds: 3. **Three repeated failures trigger a pause or human review.**
- **Core protocol changes require human approval.**

## High-risk paths

Changes to these paths require human approval:

- `.env`, `.env.*`
- `.github/workflows/`
- `migrations/`
- `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `pyproject.toml`
- `scripts/deploy`

## What Captain Code is not

It is not an "Agent OS", an AI operating system, or an enterprise governance
platform. It governs how AI coding output is accepted; it does not replace the agent.
