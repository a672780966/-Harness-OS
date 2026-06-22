# Harness OS v1.1 Project Agent Instructions

## Project goal

Harness OS v1.1 is a minimal semi-automatic AI coding agent production loop.

The target loop is:

Spec Kit / Codex planning
→ Hermes task envelope
→ Claude Code + DeepSeek first implementation
→ Open Code Review first review
→ Claude Code + DeepSeek repair
→ Codex advanced review
→ Codex + Open Code Review final acceptance
→ Merge gate
→ Audit log
→ StarMap minimal writeback

## Role boundaries

Hermes:
- Orchestrator only
- Creates tasks
- Dispatches workers
- Collects evidence
- Advances state
- Enforces gate
- Writes audit log

Claude Code:
- Implementation worker (primary)
- Works only inside assigned worktree
- Must not edit main
- Must produce test evidence and result envelope

OpenCode (Node Executor fallback):
- Implementation worker (alternate, current_task_only)
- Used when Claude Code is blocked by provider compatibility
- Works only inside assigned worktree
- Must not edit main
- Must produce test evidence and result envelope
- Current binding: task_real_loop_001_interactive

DeepSeek:
- Reasoning assistant
- Pre-dev planning
- Failure analysis
- Diff self-check
- No direct code editing

Open Code Review:
- First review gate
- Produces blocking and non-blocking issues

Codex:
- Planner
- Advanced reviewer
- Final gate reviewer
- Does not implement by default

## Hard rules

- No test, no done.
- No review, no merge.
- No Codex approval, no merge_ready.
- No direct main branch modification by worker.
- No secret logging.
- No force push.
- No deployment in v1.1 local loop.
- Max repair rounds: 3.
- High-risk path changes require human confirmation.

## High-risk paths

- .env
- .env.*
- .github/workflows/
- scripts/deploy
- migrations/
- package.json
- package-lock.json
- pnpm-lock.yaml
- pyproject.toml

## First-round scope

Do not implement:

- Superlog
- AGNTCY
- iii workers harness
- full LangGraph orchestration
- full OpenAI Agents SDK orchestration
- enterprise RBAC
- 3D StarMap UI
- automatic push or deployment

---

# Project Skill Pack

Harness OS v1.1 uses the following skill pack:

## Spec Kit

Role: task contract.

Allowed:

- /speckit.constitution
- /speckit.specify
- /speckit.plan
- /speckit.tasks

Blocked in first round:

- /speckit.implement

## mattpocock/skills

Role: clarification and context discipline.

Use for:

- task clarification
- shared language
- docs-based grilling
- avoiding premature implementation

Preferred:

- /grill-me
- /grill-with-docs
- CONTEXT.md

## Ponytail

Role: anti-bloat gate.

Use for:

- minimal sufficient patch
- avoiding over-engineering
- avoiding broad refactor
- checking whether new abstraction is necessary

## Understand Anything

Role: code graph and StarMap seed.

Use for:

- repo map
- module relationship
- impact analysis
- context entrypoint

Not used as:

- scheduler
- loop controller
- final source of truth

## Open Code Review

Role: review gate.

Use for:

- first review
- final validation
- blocking issue extraction
- review artifact generation

## Harness Native Skills

Role: governance discipline.

Includes:

- task envelope discipline
- result envelope discipline
- audit discipline
- merge gate discipline

---

# External Tool Invocation Baseline

Harness OS v1.1 uses some external tools directly to improve project creation and task execution quality.

These tools are not internal Harness subsystems.

## Understand Anything

Role:

- external repo understanding tool
- project creation context assistant
- task context discovery tool
- impact analysis assistant

Use before:

- project planning
- task splitting
- Claude Code implementation
- Codex review
- Open Code Review

Output should be saved under:

```text
.harness/external-tools/runs/understand-anything/
```

Rules:

- advisory only
- may be referenced in context_refs
- must not change state
- must not approve merge
- must not replace AuditEvent

## Superlog

Role:

- external telemetry and debugging tool
- failure analysis assistant
- trace/log observation assistant

Use after:

- failed task
- failed tests
- blocked state
- repeated repair failure
- before human handoff

Output should be saved under:

```text
.harness/external-tools/runs/superlog/
```

Rules:

- advisory only
- may be referenced by AuditEvent.payload_ref
- must not replace AuditEvent
- must not change state
- must not approve merge
- full stack is not started unless user explicitly asks

---

# Cloud Sandbox Dev Permission Profile

This project is currently configured for high-permission development inside an empty cloud VM sandbox.

Codex may use the `cloud_sandbox_dev` profile for project creation, planning support, and local development orchestration.

Codex must still respect Harness governance:

- no push
- no deploy
- no direct main write
- no merge without final gate
- no state change without AuditEvent
- no worker completion without result_envelope
- no review completion without review_envelope
- no final acceptance without evidence refs

For review-only work, use the `review_only` profile.

External tool outputs from Understand Anything and Superlog are advisory only.
AuditEvent remains the source of truth.
State Machine remains the source of task status.
Envelope remains the source of agent handoff.

---

# First Review Fresh Session Policy

First-round audit must be independent from implementation context.

If Claude Code participates in first-round audit:

- Start a fresh Claude Code session.
- Do not continue the implementation session.
- Do not resume previous worker context.
- Load Claude Code Fresh Audit Skill.
- Review only.
- No code edits.
- Output review_envelope.

Codex must reject any review that was produced in the same context as implementation.

Open Code Review artifacts and Claude fresh audit artifacts may both be used as review evidence.

---

# Open Code Review Adapter Policy

Open Code Review is the first-round machine review gate.

It runs after Claude Code Worker produces result_envelope and the task reaches completed_for_review.

Rules:

- Review only.
- Do not edit code.
- Do not generate patch.
- Do not merge.
- Do not push.
- Do not deploy.
- Must read task_envelope, result_envelope, diff_ref, changed_files, test_result, acceptance criteria.
- Must output review_envelope.
- Worker claims are not evidence.
- Tests and diff evidence outrank worker narrative.
- If blocking issues exist, task must go to repair_requested.
- If no blocking issues exist, task may go to review_passed before Codex advanced review.
