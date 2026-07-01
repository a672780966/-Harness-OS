# Captain Code

> An auditable AI coding workflow.

[![License](https://img.shields.io/badge/license-ISC-green?style=flat-square)](#license)
![Status](https://img.shields.io/badge/status-early%20development-orange?style=flat-square)
![Mode](https://img.shields.io/badge/mode-local--first-blue?style=flat-square)

**English** · [中文](./README.zh.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md)

---

## What is Captain Code

Captain Code is an auditable AI coding workflow that turns development tasks into
**controlled executions, reviewable evidence, gate decisions, and return records**.

It helps developers use AI coding agents without blindly trusting raw agent output.
Instead of accepting "the agent says it's done," Captain Code requires that every
task carries a contract, every execution leaves evidence, and nothing reaches a
trusted state until a gate decision accepts it.

Captain Code is **local-first** and read-first. It runs on your machine, against
your repository, and never pushes, publishes, or deploys on its own.

## The problem

AI coding agents are good at producing diffs and confident summaries. They are bad
at proving that the work is correct, in scope, and safe to accept.

- An agent's claim is not evidence.
- A passing summary is not a passing test.
- A diff that "looks done" is not the same as a diff that is safe to merge.

Without a workflow around the agent, you end up trusting unverified output. Captain
Code puts a thin, auditable layer between the agent and your trusted state, so that
acceptance is a decision backed by evidence rather than a vibe.

## Core workflow

```
TaskEnvelope → Invocation → Artifact / Evidence → Review → GateDecision → AuditEvent → ReturnRecord
```

| Object         | Meaning                                                                   |
| -------------- | ------------------------------------------------------------------------- |
| `TaskEnvelope` | The task contract: goal, scope, acceptance criteria, constraints.         |
| `Invocation`   | One execution attempt against a controlled workspace.                     |
| `Artifact`     | A produced output (diff, generated file, patch, plan).                    |
| `Evidence`     | Something that supports a judgment (test result, log, policy check).       |
| `Review`       | An assessment of artifacts and evidence: approve, repair, or block.       |
| `GateDecision` | The flow decision: `PASS` / `REPAIR` / `BLOCK` / `ESCALATE`.              |
| `AuditEvent`   | An append-only record of what happened, for traceability.                 |
| `ReturnRecord` | The state-return record: what was accepted, rejected, or left unresolved. |

These are **generic protocol objects**. Captain Code is the coding profile of the
protocol, but the objects stay reusable and are not narrowed into code-only terms.

## Minimal example

A task starts as an envelope:

```yaml
# task_envelope.yaml
task_id: task-001
title: "Add a usage section to README"
user_request: "Document how to run the CLI in README.md"
scope:
  allowed_paths: ["README.md"]
  denied_commands: ["git push", "git merge"]
acceptance_criteria:
  - "README has a 'Usage' section"
test_commands: ["pnpm test"]
```

From there the workflow runs:

1. **Invocation** — the worker executes inside a controlled workspace (a git
   worktree), not your main checkout.
2. **Artifact / Evidence** — the diff is captured as an artifact; logs and test
   results are captured as evidence.
3. **Review** — artifacts and evidence are assessed against the acceptance criteria.
4. **GateDecision** — `PASS`, `REPAIR`, `BLOCK`, or `ESCALATE`.
5. **AuditEvent** — every step is appended to the audit log.
6. **ReturnRecord** — the final record of what was accepted and what risks remain.

Nothing is "done" until a `GateDecision` accepts it and a `ReturnRecord` is written.

## Current status

Captain Code is in **early, active development** and should be treated as such.

- **Mode:** local-first, read-first semantic copilot.
- **Available today:** project inspection, diff and evidence collection, a runner
  loop (plan → execute → collect → review → gate), and report generation.
- **Being hardened:** the full write-side `TaskEnvelope → ReturnRecord` loop with
  controlled-workspace execution and closure.
- **Not a sandbox claim:** the controlled workspace is a git worktree. It isolates
  *changes*, not the host. It is **not** a security sandbox (see [Safety model](#safety-model)).

> Note on naming: the CLI is currently invoked as `harness` / `python -m harness.copilot.cli`
> while the `captain-code` naming is being adopted. See [docs/quickstart.md](./docs/quickstart.md).

## Safety model

Captain Code is conservative by default. The following rules are enforced as part of
the workflow, not left to the agent's discretion:

1. **No `TaskEnvelope`, no worker execution.**
2. **No `trace_id`, no trusted execution.**
3. **No diff reference, no done state.**
4. **No test result, no done state.**
5. **Failed tests cannot become accepted.**
6. **Out-of-scope file changes are quarantined**, not silently applied.
7. **Core protocol changes require human approval.**
8. **Three repeated failures trigger pause or human review.**
9. **`git push`, publish, and deploy are blocked.**
10. **A `GateDecision` must be accepted before a `ReturnRecord` is trusted.**

The controlled workspace prevents pollution of your main checkout and makes changes
easy to diff and destroy. It does **not** prevent a malicious command from reading
local files, environment variables, or credentials. Strong isolation (containers,
microVM) is out of scope for this stage.

## What Captain Code does not do

- It is **not** an "Agent OS" or an AI operating system.
- It is **not** an enterprise governance platform.
- It does **not** replace your AI coding agent — it governs how its output is accepted.
- It does **not** host login state or ship any API keys.
- It does **not** push, publish, or deploy.
- It does **not** claim its workspace is a secure sandbox.

## Quickstart

See **[docs/quickstart.md](./docs/quickstart.md)** for install and first run.

The full guided quickstart is still being finalized as the write-side loop is
hardened. Read-only inspection commands work today and are safe to run on any repo.

## Docs

- [Quickstart](./docs/quickstart.md) — install and first run
- [Workflow](./docs/workflow.md) — the protocol objects and the execution loop
- [Architecture (lite)](./docs/architecture-lite.md) — components and boundaries
- [Hermes loop lock](./docs/hermes-loop-lock.md) — Hermes = State Machine Runner + Scheduler + Daily Reporter; runner rules and safety locks

## License

ISC.
