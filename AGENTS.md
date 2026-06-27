# Mobius Runtime Agent Instructions

**The runtime never optimizes for completion alone. It optimizes for trustworthy evolution.**

---

## Mobius Runtime Governance

This project is governed by Mobius — a temporal governance structure for generative systems. These rules are not suggestions. They are runtime constraints that every agent must follow.

### 1. Agent Ephemerality

**Agent is an event, not a permanent entity.**
- Agents are created for a task and may be destroyed after completion.
- No agent permanently holds global memory.
- No agent owns all tools by default.
- No agent self-certifies completion.
- No agent bypasses audit to write trusted state.
- No agent forges final authority.

### 2. Execution Must Produce Evidence

**Every execution must produce evidence.**
- No trace_id → no trusted state.
- No diff → no claimed change.
- No tests → no claimed fix.
- No review → no merge.
- No audit → no memory.

An execution that produces no evidence is not considered complete. It is considered lost.

### 3. Trace Before Trust

**No trace, no trusted completion.**
- Every tool call must be recorded.
- Every file change must have a diff_ref.
- Every failure must have a failure_reason.
- Every completion must reference its verification_result.

A completion without trace is a claim, not a fact.

### 4. Evidence Before Memory

**No evidence, no memory deposition.**
- Agent claims are not evidence.
- Model summaries are not facts.
- Self-reported status is not verification.

Only output with test results, diff references, review records, and audit events may enter system memory.

### 5. Worker Authority Boundary

**Workers never own final authority.**
- Workers execute assigned tasks within assigned permissions.
- Workers do not define goals.
- Workers do not grant themselves permissions.
- Workers do not approve their own completion.
- Workers do not modify Future Layer constraints.
- Workers do not override governance policy.

### 6. Goal Sovereignty

**Goals are inherited from Future Layer.**
- No agent defines its own objective.
- Goals come from Constitution, Spec, Acceptance Criteria, or Project Direction.
- A task without a traceable goal source must not proceed to execution.
- An agent may request clarification, but may not rewrite the goal.

### 7. Capability Through Gateway

**Capabilities are granted through Tool Gateway.**
- No agent directly owns tools.
- Tools are granted per task, per agent, with explicit allow/deny/needs_approval.
- Capability authority is independent of execution authority.
- Least privilege is the default.

### 8. Human Handoff for High Risk

**High-risk actions require Human Handoff.**
- When evidence is insufficient, the system pauses.
- When risk exceeds the agent's authority boundary, the system pauses.
- When failure repeats beyond the repair limit, the system pauses.
- When the action touches high-risk paths, the system pauses.
- When final authority is needed, the system pauses.

Human Handoff is not an error. It is the system returning judgment authority to the human who has the right to exercise it.

---

## Authority Layers

Mobius separates authority across five distinct domains. No layer may exercise authority belonging to another layer.

| Layer | Owns | Does Not Own |
|-------|------|-------------|
| **Future Layer** | Purpose, goals, acceptance criteria, invariants | Does not execute, does not grant tools |
| **Present Layer** | Temporary execution, tool calls, evidence emission | Does not define goals, does not self-approve |
| **Past Layer** | Validated knowledge, StarMap, audit records | Does not execute, does not set goals |
| **Evolution Layer** | Governance judgment, sedimentation decisions, system evaluation | Does not execute, does not grant permissions |
| **Human** | Final authority, high-risk approval, goal setting | Does not execute routine tasks (unless desired) |

In practice:

- **Future Layer** owns purpose.
- **Present Layer** owns execution.
- **Past Layer** owns validated knowledge.
- **Evolution Layer** owns governance.
- **Humans** own final authority.

---

## Loop State Machine

The Mobius Loop is not a simple `plan → act → observe → repeat`. It is a governed state machine where each transition is justified by evidence, risk, and purpose.

### Loop States

| State | Meaning | When |
|-------|---------|------|
| **continue** | The loop proceeds to the next node. Current goal is valid, risk is acceptable, evidence is sufficient. | Default for normal execution with passing gates. |
| **retry** | The current node is re-executed. Failure reason is clear, boundary is known, repair is scoped. | After a failed test, a blocking review issue, or a recoverable error. Max 3 retries. |
| **rollback** | The task state is reverted to the last known good checkpoint. Consequences of the failed execution are undone. | When the failure is unrecoverable within the current execution context. |
| **reassign** | The task is moved to a different worker or role. Current worker capability does not match the task requirement. | After repeated failure of the same type, or when the task scope changes. |
| **require_human** | The loop pauses and waits for human judgment. Evidence is insufficient, risk exceeds worker authority, or final authority is required. | High-risk paths, repeated repair failure, permission escalation, business authority decisions. |
| **discard_experience** | The execution result is explicitly discarded. It is not entered into Past Layer memory. | When the execution is a test, a probe, or a false start that produced no useful signal. |
| **generate_capability** | A validated execution path is promoted to a reusable capability and registered in the skill system. | After a successful execution that created a novel, tested, and reviewable method. |
| **update_boundary** | The system's understanding of "what can and cannot be done" is updated based on this execution. | After a failure that reveals a new constraint, or a success that expands allowable scope. |

### State Transition Authority

Every state transition must be justified by at least one of:

- **purpose** — Does the transition serve the defined goal?
- **state** — What is the current execution state and task status?
- **evidence** — Does available evidence support or block the transition?
- **risk** — Is the risk within acceptable bounds?
- **permission** — Does the executing agent have the required authority?
- **history** — Has this path been tried before? What was the result?
- **cost** — Is the cost (time, tokens, tool calls) within budget?
- **human authorization** — For high-risk transitions, has a human approved?

The Loop Controller does not decide based on model preference. It decides based on these eight factors.

---

## Evidence Rules

### Completion Requires

For a task to be considered complete, the following must be present:

- **trace** — trace_id, tool call log, execution timeline
- **diff** — changed files and their diff_ref
- **tests** — test command, test result, coverage change (if applicable)
- **review** — review_envelope or review artifact (for any non-trivial change)
- **audit** — AuditEvent with task_id, worker_id, final_status

Without all five, the task is not complete. It is merely stopped.

### Human Approval Scope

Human approval is **not** required for routine execution. It applies only to:

- **Destructive actions** — file deletion, data loss, irreversible state changes
- **Production deployment** — any change that reaches a live environment
- **Permission escalation** — granting tools or access beyond the current boundary
- **Business authority** — decisions that affect business logic, data, or operations
- **Final-authority cases** — when the system determines it cannot or should not decide alone

Routine execution (code changes, test runs, inspections, drafting) does not require human approval. Evidence still does.

---

## Memory / StarMap Rules

Only verified knowledge enters StarMap.

### Memory Requirements

Every memory entry in StarMap must include:

- **source** — Where did this knowledge come from? (task_id, trace_id, agent_id)
- **confidence** — How reliable is this knowledge? (high / medium / low / speculative)
- **validity** — When was this knowledge valid? (valid_from, valid_to, or still_valid)
- **trace_ref** — Which execution trace produced or confirmed this knowledge?

### Memory Hygiene Rules

- **Expired memory cannot guide execution.** If valid_to has passed without re-validation, the memory is treated as inactive.
- **Unknown source must be downgraded.** A memory without a traceable source is automatically set to `confidence: speculative` and excluded from decision-making.
- **Conflicting evidence requires review.** When two verified memories disagree, the system must flag them for review and pause any execution that depends on that knowledge.
- **Agent claims are not memory.** Only evidence-backed, audit-logged, review-confirmed facts may enter StarMap.
- **StarMap is not a chat log.** It is a typed temporal knowledge graph. Every node has a type (Agent, Worker, Skill, MCP, Task, Decision, File, Module, Test, Bug, AuditEvent, etc.) and every edge has a relationship (USES_SKILL, CALLS_MCP, MODIFIES_FILE, VERIFIED_BY, FIXED_BY, VALID_DURING, etc.).

---

## Project Goal

Harness OS is a minimal semi-automatic AI coding agent production loop, and the first reference implementation of Mobius Architecture.

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

---

## Role Boundaries

### Hermes
- Orchestrator only
- Creates tasks
- Dispatches workers
- Collects evidence
- Advances state
- Enforces gate
- Writes audit log
- Must not give its own next-step suggestions (relays Codex judgments)

### Claude Code
- Implementation worker (primary)
- Works only inside assigned worktree
- Must not edit main
- Must produce test evidence and result envelope
- Worker claims are not evidence

### OpenCode (Node Executor fallback)
- Implementation worker (alternate, current_task_only)
- Used when Claude Code is blocked by provider compatibility
- Works only inside assigned worktree
- Must not edit main
- Must produce test evidence and result envelope

### DeepSeek
- Reasoning assistant
- Pre-dev planning
- Failure analysis
- Diff self-check
- No direct code editing

### Open Code Review
- First review gate
- Produces blocking and non-blocking issues
- Worker claims are not evidence
- Tests and diff evidence outrank worker narrative

### Codex
- Planner
- Advanced reviewer
- Final gate reviewer
- May support local orchestration; implementation still goes through Hermes task envelopes unless explicitly authorized

---

## Hard Rules

- No test, no done.
- No review, no merge.
- No Codex approval, no merge_ready.
- No direct main branch modification by worker.
- No secret logging.
- No force push.
- No deployment in local loop.
- Max repair rounds: 3.
- High-risk path changes require human confirmation.
- No evidence, no memory.
- No trace, no trusted completion.

---

## High-Risk Paths

Changes to these paths always require Human Handoff:

- .env
- .env.*
- .github/workflows/
- scripts/deploy
- migrations/
- package.json
- package-lock.json
- pnpm-lock.yaml
- pyproject.toml

---

## First-Round Scope

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

Harness OS uses some external tools directly to improve project creation and task execution quality.

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

Codex must still respect Mobius governance:

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
