# Architecture (lite)

This is a deliberately small picture of how Captain Code is put together. It covers
the components that exist to support the [workflow](./workflow.md) and the boundaries
between them. It does not describe a larger platform vision.

## Components

```
┌─────────────┐   creates    ┌──────────────┐   runs in    ┌──────────────────────┐
│     CLI     │ ───────────► │ TaskEnvelope │ ───────────► │ Controlled workspace │
└─────────────┘              └──────────────┘              │   (git worktree)     │
       │                                                    └──────────────────────┘
       │                                                              │
       │                                                              ▼
       │                                                       ┌──────────────┐
       │                                                       │   Worker     │
       │                                                       │  invocation  │
       │                                                       └──────────────┘
       │                                                              │
       ▼                                                              ▼
┌─────────────┐     reads     ┌──────────────────────────────────────────────┐
│ Local state │ ◄──────────── │ Artifacts · Evidence · Review · GateDecision  │
│  store      │               └──────────────────────────────────────────────┘
│ (sqlite +   │                                  │
│  jsonl log) │ ◄──────────── AuditEvent · ReturnRecord
└─────────────┘
```

### CLI

The entry point. It creates task envelopes, manages local state, drives the
execution loop, and produces reports. The CLI is the only component a developer
interacts with directly.

### Local state store

A local SQLite database plus an append-only JSONL event log. SQLite holds the
current state of tasks, invocations, artifacts, evidence, reviews, gate decisions,
reports, and return records. The JSONL log holds the audit trail and is never
overwritten.

### Controlled workspace

By default a git worktree, created per task. It keeps task changes out of your main
checkout, makes diffs easy to capture, and makes cleanup straightforward.

It is a **controlled workspace**, not a security sandbox. It isolates changes to your
working tree; it does not restrict what a command can read from the host. Strong
isolation (containers, microVM) is out of scope at this stage.

### Worker invocation

The component that runs the actual work inside the controlled workspace, through an
adapter. Adapters let different execution backends and providers be plugged in
behind the same `Invocation` interface, so the records stay uniform regardless of
which agent did the work.

### Policy

Path scope, command allow/deny lists, secret redaction, and dangerous-operation
blocking. Policy is checked as evidence, not enforced by trust in the agent. Out-of-
scope changes are quarantined rather than applied.

### Hermes runner

The runner that drives the loop: read the task queue, trigger invocation, collect
evidence, run review, call the gate, write audit events, and produce reports. Its
authority is intentionally narrow. See [Hermes loop lock](./hermes-loop-lock.md).

## Boundaries

The protocol objects are generic and reusable. The coding-specific behavior lives in
adapters and policy, not in the core objects. Concretely:

- Core protocol and schema define the objects only. They do not depend on the UI,
  the HTTP layer, the worker adapters, or any provider SDK.
- Adapters and policy depend on the schema, not the other way around.
- The local console (when present) talks to a local API over HTTP only.

This keeps the core small and the objects portable, while the coding profile stays
in the layers that are meant to change.

## What this architecture is not

- Not a four-layer governance platform.
- Not an agent operating system.
- Not a cloud service. Captain Code is local-first by design.

## Related

- [Workflow](./workflow.md)
- [Hermes loop lock](./hermes-loop-lock.md)
