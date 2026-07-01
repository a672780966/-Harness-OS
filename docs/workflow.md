# Workflow

Captain Code turns a development task into an auditable chain of records. This page
describes each object in that chain and how the loop runs.

```
TaskEnvelope → Invocation → Artifact / Evidence → Review → GateDecision → AuditEvent → ReturnRecord
```

These are generic protocol objects. Captain Code is the **coding profile**, but the
objects are deliberately not narrowed into code-only names like `CodeTask`,
`PullRequestOnly`, or `DiffOnly`.

## TaskEnvelope

The contract for a task. It defines intent and limits *before* any execution happens.

A `TaskEnvelope` carries:

- **Identity:** `task_id`, `trace_id`, optional `parent_task_id`.
- **Intent:** title, user request, acceptance criteria.
- **Scope:** allowed and denied paths; allowed and denied commands.
- **Verification:** test commands that must run.
- **Limits:** max repair rounds, max duration, risk level.

Rule: **no `TaskEnvelope`, no worker execution.**

## Invocation

A single execution attempt. One task may have several invocations — the first run,
then repair round 1, repair round 2, and so on.

An `Invocation` records the role (worker, reviewer, etc.), the adapter used, the
workspace it ran in, its status, and timing. The workspace is a **controlled
workspace** — by default a git worktree, isolated from your main checkout.

Rule: **no `trace_id`, no trusted execution.**

## Artifact and Evidence

Execution produces two kinds of records.

- **Artifact** — a produced output. A diff is one kind of artifact, not the only
  kind. Generated files, patches, and plans are also artifacts.
- **Evidence** — something that supports a judgment. Test results, execution logs,
  command output, policy checks, secret scans, and path-scope checks are evidence.

The split matters: an artifact is *what was made*; evidence is *why it can be
trusted*. Captain Code accepts work based on evidence, not on the artifact alone.

Rules: **no diff reference, no done state. No test result, no done state.**

## Review

An assessment of the artifacts and evidence against the acceptance criteria. A
`Review` produces a status — `approved`, `needs_repair`, or `blocked` — along with
findings, required repairs, and a risk level.

A review may be performed by rules, a model, a human, or a hybrid. When the planner
and reviewer share the same model, the report flags the possible same-source bias.

## GateDecision

The flow decision. A `GateDecision` is **not** a review opinion — it is the control
point that decides what happens next:

- `PASS` — accept and proceed to return.
- `REPAIR` — send back for another invocation, within the repair limit.
- `BLOCK` — stop; the work cannot be accepted.
- `ESCALATE` — hand the decision to a human.

Rules: **failed tests cannot become accepted. Out-of-scope file changes are
quarantined. A `GateDecision` must be accepted before a `ReturnRecord` is trusted.**

## AuditEvent

Every meaningful step appends an `AuditEvent` to an append-only log. Audit events are
never overwritten. They are the trace of what the system actually did, independent of
any summary.

```json
{"type":"task.created","trace_id":"trace-1","task_id":"task-42"}
{"type":"invocation.started","trace_id":"trace-1","task_id":"task-42","invocation_id":"inv-1"}
{"type":"artifact.created","trace_id":"trace-1","task_id":"task-42","kind":"code_diff"}
{"type":"evidence.created","trace_id":"trace-1","task_id":"task-42","kind":"test_result"}
{"type":"gate.decided","trace_id":"trace-1","task_id":"task-42","decision":"REPAIR"}
{"type":"return.created","trace_id":"trace-1","task_id":"task-42","return_id":"ret-1"}
```

## ReturnRecord

The state-return record. A report is for humans; a `ReturnRecord` is the system's
record of how the task returned to a trusted state. It answers:

- Which artifacts were accepted?
- Which evidence was accepted?
- Which artifacts were rejected?
- Which risks remain unresolved?
- Which `GateDecision` was final?
- Were the resources closed out?

Without a `ReturnRecord`, Captain Code is just a task runner. With it, every action
returns to the system as accepted state, rejected work, or an explicit open risk.

## The loop, end to end

```
create envelope
  → invoke worker in a controlled workspace
  → collect artifacts and evidence
  → review
  → gate decision
  → (repair, bounded by max rounds)
  → audit
  → return record
  → close out the workspace
```

Repairs are bounded. **Three repeated failures trigger a pause or human review** —
the loop does not spin indefinitely.

## Related

- [Architecture (lite)](./architecture-lite.md)
- [Hermes loop lock](./hermes-loop-lock.md)
