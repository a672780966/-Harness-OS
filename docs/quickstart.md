# Quickstart

Captain Code is local-first. Everything in this guide runs on your machine against
a repository you already have. None of these commands push, publish, or deploy.

> **Naming note.** The product is Captain Code. The CLI is currently invoked as
> `harness` (or `python -m harness.copilot.cli`) while the `captain-code` command
> name is being adopted. Where you see `harness` below, read it as "the Captain Code
> CLI."

## Requirements

- Python 3.11+
- Node.js 22 LTS and pnpm (optional — only for the Node CLI and local console)
- git

## Install

Clone the repository:

```bash
git clone <repo-url>
cd <repo-dir>
```

### Option 1 — Python CLI (no build required)

```bash
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
```

### Option 2 — Node CLI

```bash
pnpm install
pnpm build
./dist/index.js version --json
./dist/index.js doctor
```

After building, the CLI binary is at `./dist/index.js`.

## First run (read-only, safe on any repo)

These commands only read and report. They do not modify your working tree.

```bash
# Inspect the current project
python -m harness.copilot.cli inspect .

# Open the local dashboard view
python -m harness.copilot.cli dashboard .

# Draft a PR description from the current changes (does not create or push)
python -m harness.copilot.cli pr-draft --base main
```

## The governed loop (preview)

The write-side workflow — turning a `TaskEnvelope` into a `ReturnRecord` — is being
hardened. The intended flow is:

```bash
captain-code init                  # set up local state and policy
captain-code run "task description" # create envelope + controlled workspace + invoke
captain-code status                # inspect task state
captain-code review <task_id>      # produce a Review
captain-code gate <task_id>        # PASS / REPAIR / BLOCK / ESCALATE
captain-code report <task_id>      # human-readable report
captain-code destroy <task_id>     # close out the controlled workspace
```

Until these are finalized, prefer the read-only commands above. The safety rules in
[the safety model](./../README.md#safety-model) apply to every command: no push, no
publish, no deploy, and nothing reaches a trusted state without a `GateDecision`.

## Where state lives

When initialized, Captain Code keeps local state under a project directory:

```
.captain/                 (or .harness/ in the current implementation)
  config.yaml
  policy.yaml
  state.sqlite
  events.jsonl            # append-only audit log
  tasks/
  worktrees/
```

State is local and append-only. Audit events are never overwritten.

## Next

- [Workflow](./workflow.md) — what each protocol object means
- [Hermes loop lock](./hermes-loop-lock.md) — what the runner may and may not do
