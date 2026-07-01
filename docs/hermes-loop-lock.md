# Hermes loop lock

Hermes is the runner that drives the Captain Code loop. Its role is deliberately
small, and its limits are part of the safety model — not optional conventions.

## What Hermes is

> **Hermes = State Machine Runner + Scheduler + Daily Reporter.**

Hermes advances tasks through the workflow state machine, schedules invocations, and
reports on what happened. It is plumbing, not a decision-maker.

## Hermes may

- Read the task queue.
- Trigger worker invocation.
- Collect evidence.
- Run review.
- Call the gate / reducer.
- Write audit events.
- Generate daily reports.

## Hermes must not

- Own long-term memory.
- Decide architecture direction.
- Mark tasks complete without evidence.
- Push.
- Publish.
- Deploy.
- Modify the core protocol without human approval.
- Write trusted state without a `GateDecision`.

## Loop locks

These locks keep the runner honest and prevent runaway loops.

1. **Envelope lock** — no `TaskEnvelope`, no invocation. Hermes will not run work
   that has no contract.
2. **Trace lock** — no `trace_id`, no trusted execution. Untraced runs cannot enter
   trusted state.
3. **Evidence lock** — no diff reference and no test result means no `done` state.
   A claim of completion without evidence is rejected.
4. **Failed-test lock** — failed tests cannot be promoted to accepted.
5. **Scope lock** — out-of-scope file changes are quarantined, not applied.
6. **Gate lock** — a `GateDecision` must be accepted before a `ReturnRecord` is
   trusted.
7. **Repeat-failure lock** — three repeated failures trigger a pause or human
   review. The loop does not retry forever.
8. **Protocol lock** — changes to the core protocol require human approval.
9. **Egress lock** — `git push`, publish, and deploy are blocked.

## Daily report format

Hermes produces a daily report summarizing loop activity. A report covers:

- **Tasks** — created, in progress, returned, blocked.
- **Invocations** — count, successes, failures, repair rounds.
- **Evidence** — tests run, pass/fail, policy checks.
- **Gate decisions** — `PASS` / `REPAIR` / `BLOCK` / `ESCALATE` counts.
- **Open risks** — unresolved risks carried in return records.
- **Escalations** — anything handed back to a human.

The report is for humans and is generated from audit events and return records. It
does not change state; it describes it.

## Related

- [Workflow](./workflow.md)
- [Architecture (lite)](./architecture-lite.md)
