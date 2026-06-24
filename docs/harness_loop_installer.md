# Harness Loop Installer

## Product Vision

**Harness is not a copilot UI. Harness is an agent loop installer.**

When a user installs Hermes, Codex, Claude Code, or OpenCode, Harness detects them and actively suggests establishing a governed engineering loop.

The user transforms from a *message courier* (copying context between agents) into an *approver* (reviewing decisions made by the loop).

## Loop Modes

### Single Agent Loop

One installed agent handles all roles (planner, coder, tester, reviewer, gatekeeper, doc_writer) using an internal sub-agent strategy. The agent produces:

- Task breakdown → implementation → tests → review → evidence → gate

The agent configuration includes:
- `.harness/loop/CLAUDE.md` (or equivalent)
- `.harness/loop/subagents/`
- `.harness/loop/skills.yaml`
- `.harness/loop/policy.yaml`

### Multi-Agent Product Loop

Multiple agents collaborate through the A2A envelope protocol:

| Agent | Role | Responsibilities |
|-------|:----:|:-----------------|
| **Codex** | Planner / Reviewer / Gatekeeper | Plan task nodes, audit evidence, decide continue/repair/stop, approve merge readiness |
| **Hermes** | Executor / Evidence Collector | Inspect files, run tests, collect git state, generate evidence, enforce safety gate |
| **Claude Code** | Implementation Worker | Implement task nodes, repair failed tasks, explain code meaning |
| **OpenCode** | Alternative Worker / Reviewer | Alternative implementation, second review, cross-check diff |
| **Harness Copilot** | Shared Loop Capability | inspect, readiness, task-card, pr-draft, risk scan, evidence report |

## Commands

### `harness loop doctor`

Detects installed tools (git, gh, python, pytest) and AI coding agents (hermes, codex, claude-code, opencode).

Output: System report with tool/agent version and availability.

### `harness loop suggest`

Based on detected agents, recommends single-agent or multi-agent loop topologies with suggested role assignments.

### `harness loop setup`

Interactive prompt that asks:
1. Which mode? (Single Agent / Multi Agent / Custom)
2. Which agents to use?
3. Generates complete loop configuration: roles, skills, instructions, A2A envelopes, policy.

### `harness loop init`

Non-interactive version of setup. Specify `--mode` and `--agents` as flags.

### `harness loop run`

Executes a configured loop cycle (MVP). Runs Harness Copilot commands (inspect, readiness) and generates evidence artifacts.

## Generated Configuration

```
.harness/loop/
├─ loop.yaml              # Topology and policy
├─ agents.yaml            # Agent registry
├─ roles.yaml             # Role assignments
├─ skills.yaml            # Skill assignments
├─ policy.yaml            # Safety policy
├─ a2a.yaml               # A2A envelope protocol
├─ envelopes/
│  ├─ task_envelope.schema.json
│  ├─ result_envelope.schema.json
│  └─ review_envelope.schema.json
├─ instructions/
│  ├─ codex.md
│  ├─ hermes.md
│  ├─ claude-code.md
│  └─ opencode.md
├─ templates/
│  └─ code_meaning_report.md
├─ runs/
└─ README.md
```

## A2A Envelope Protocol

### TaskEnvelope

```json
{
  "protocol": "harness-loop/v1",
  "trace_id": "trace_xxx",
  "task_id": "task_xxx",
  "from_agent": "codex",
  "to_agent": "hermes",
  "objective": "Implement selected task node",
  "acceptance_criteria": [],
  "allowed_actions": ["read files", "edit scoped files", "run tests", "generate report"],
  "requires_human": ["merge PR", "push tag", "force push", "rewrite history", "deploy"]
}
```

### ResultEnvelope

```json
{
  "protocol": "harness-loop/v1",
  "trace_id": "trace_xxx",
  "task_id": "task_xxx",
  "from_agent": "hermes",
  "to_agent": "codex",
  "status": "completed_for_review",
  "changed_files": [],
  "test_result": {"passed": true, "command": "pytest", "summary": ""},
  "code_meaning_report": {"what_changed": "", "why_changed": "", "impact": "", "risk": "", "tests": ""}
}
```

### ReviewEnvelope

```json
{
  "protocol": "harness-loop/v1",
  "trace_id": "trace_xxx",
  "task_id": "task_xxx",
  "from_agent": "codex",
  "to_agent": "hermes",
  "status": "repair_requested",
  "blocking_issues": [],
  "merge_ready": false
}
```

## Safety Policy

### Auto-Allowed (no human needed)

- read files, git status/diff/log
- pytest
- `harness copilot inspect / readiness / task-card / pr-draft`
- write `.harness/loop/runs/` and `docs/*_report.md`

### Requires Human Approval

- git push, push --tags, tag, merge
- git reset, git clean
- rm, delete files
- modify .env or secrets
- deploy
- upload large archives
- rewrite history

## Code Meaning Report

Every code change generates a report with:
- What changed
- Why this change was needed
- Files touched
- Behavioral impact
- Tests run
- Risks
- What was intentionally not changed
- Human approval required?

## Agent Adapter Status

| Agent | Adapter | Status |
|-------|:-------:|:------:|
| Hermes | ✅ | Available |
| Codex | ✅ | Available |
| Claude Code | ✅ | Available |
| OpenCode | ✅ | Available |

If an agent has no adapter, a handoff file is generated instead of pretending full automation.

## MVP Boundary

The MVP does NOT fully automate all agent calls. It:
1. ✅ Detects agents
2. ✅ Recommends loop topology
3. ✅ Generates config and instructions
4. ✅ Generates A2A envelope schemas
5. ✅ Runs Harness Copilot local commands
6. ✅ Generates handoff files for agents without adapters
7. ⏳ Future: replace handoff files with auto-adapters via CLI/API
