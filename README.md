
<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0--rc.2-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/TypeScript-6.0-blue?style=flat-square" alt="TypeScript">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/tests-528%20passed-brightgreen?style=flat-square" alt="Tests">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<h1 align="center">Harness OS</h1>
<p align="center"><em>Codex‑first Project Operating System — Governed, Auditable, Reproducible Agent Engineering</em></p>

---

**Harness OS** is an operating system for AI coding agents. It doesn't give agents *capabilities* — frameworks do that. It gives agents *boundaries and discipline*: every tool call is gated, every output is redacted, every decision is traced, and every delivery is verified.

Think of it as **Kubernetes for AI agents** — not for running containers, but for running agentic workflows with governance, observability, and auditability baked in.

---

## Why Harness OS?

Frameworks like LangChain, Vercel AI SDK, and OpenAI Agents SDK give agents the ability to call tools, use models, and compose workflows. But they don't answer:

- **Who approved this tool call?** → Harness OS traces every invocation with session, turn, and agent identity.
- **Did any secrets leak in the output?** → Harness OS redacts 15+ secret patterns at every output boundary.
- **Can we replay what happened?** → Every run is recorded as a structured trace with events, approvals, and checkpoints.
- **Is the delivery safe?** → Verification must pass with a cryptographic integrity hash before any commit, PR, or deploy.
- **Can we enforce policy?** → Multi-layered configuration with immutable fields, safety-only override rules, and fail‑closed defaults.

Harness OS is **not a framework**. It's the **governance layer** that wraps around any agent runtime to make it production‑ready.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   CLI (harness)                      │
│  create │ open │ init │ run │ verify │ deliver        │
│  config │ status │ report │ checkpoint │ rollback     │
│  skills │ decision │ repair │ check                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Turn Orchestrator                     │
│  Session → Input → Model Call → Tool Gate → Response │
└──────┬─────────┬──────────┬──────────┬─────────────┘
       │         │          │          │
┌──────▼──┐ ┌───▼────┐ ┌──▼────┐ ┌──▼──────────┐
│ Policy  │ │Approval│ │Secret │ │Observability │
│ Engine  │ │ Gate   │ │Redact │ │ Trace/Events │
└─────────┘ └────────┘ └───────┘ └──────────────┘
       │         │          │          │
┌──────▼─────────▼──────────▼──────────▼──────────┐
│            Verification & Delivery                │
│  Guard → Commit → PR → Release → Deploy          │
└──────────────────────────────────────────────────┘
```

### Thin Harness (implemented)

The minimal viable loop that governs every agent action:

1. Turn input received
2. Model call executed
3. Tool proposal generated
4. **PreToolUse gate** — policy evaluation + secret scan
5. **Allow / Deny / NeedsApproval** decision
6. **Approval resolution** (if needed)
7. Tool execution
8. **PostToolUse trace** — record everything
9. Final response with redacted output

### Thick Harness (planned)

Extended capabilities for production-scale deployments:
- Parallel hook fan-out with publish‑and‑collect
- OpenTelemetry integration
- Policy hot‑reload without restart
- Multi‑provider failover (Claude ↔ GPT ↔ others)
- Budget‑aware provider routing
- Distributed approval UI
- Sandboxed tool execution

---

## Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) >= 22
- [pnpm](https://pnpm.io/) >= 11

### Install & Build

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd Harness-OS
pnpm install
pnpm build
```

### Run

```bash
# Show version
pnpm harness --version
# → 1.0.0-rc.2

# Show help
pnpm harness --help

# Show configuration
pnpm harness config

# Show configuration (JSON)
pnpm harness config --json

# List available skills
pnpm harness skills list

# Check AGENTS.md validity
pnpm harness check

# Initialize Harness OS in a project
pnpm harness init --json

# Run a task
pnpm harness run "add tests for the auth module"
```

### Common Workflow

```bash
# 1. Initialize a project
cd my-project
harness init

# 2. Run a task
harness run "implement user authentication"

# 3. Run verification
harness verify

# 4. Prepare delivery
harness deliver --commit --ver-id <verification-id>
```

---

## CLI Commands

| Command | Description |
|---|---|
| `create <name>` | Create a new Harness OS project |
| `open <path>` | Open an existing project |
| `init` | Initialize Harness OS in an existing project |
| `repair` | Repair missing or invalid project structure |
| `check` | Check AGENTS.md validity |
| `status` | Show current project status |
| `run <task>` | Execute a task (full pipeline) |
| `resume <run-id>` | Resume a paused or interrupted run |
| `verify` | Run verification pipeline (lint, typecheck, test, build) |
| `report <run-id>` | Show run report |
| `deliver` | Prepare delivery (commit / PR / release / deploy) |
| `decision` | Manage architecture decisions (ADR) |
| `skills` | Manage and list skills |
| `checkpoint` | Create a checkpoint capturing git and task state |
| `rollback <checkpoint-id>` | Show rollback information |
| `config` | Show Harness OS configuration |

All commands support `--json` for machine-readable output and `--quiet` for minimal output.

---

## Built-in Capabilities

### Governance & Security
- **Permission tri‑state**: `allow` | `deny` | `needs_approval` — no ambiguous states
- **Secret redaction**: 15+ pattern types — API keys, tokens, private keys automatically redacted from all outputs
- **Protected files**: Dangerous paths blocked from agent access
- **Safety fields**: Immutable config fields, one‑way weakening protection, union‑merge arrays
- **Fail‑closed**: Any hook failure defaults to `needs_approval`

### Verification
- Detects project commands from `AGENTS.md` and `package.json`
- Runs full pipeline: lint → typecheck → test → build
- Produces structured JSON result with cryptographic integrity hash
- Bound to project, task, run, and git commit for non‑repudiation

### Delivery Pipeline
- Guard checks: verification binding, git status, project integrity
- Conventional commit message generation
- PR body generation
- Delivery report with full audit trail

### Observability
- **Events**: JSONL event log with session, actor, and redaction
- **Traces**: Full run trace with tool calls, context packs, checkpoints
- **Reports**: Markdown run report with verification results

### Skills Registry
Built-in skills with risk classification and approval requirements:

| Skill | Risk | Tools |
|---|---|---|
| Filesystem | Medium | read, write, list, search, delete |
| Shell | High | run command, test, build |
| Git | Medium | status, diff, commit, push |
| Repo Scanner | Low | scan, detect, map |

---

## Project Structure

```
Harness-OS/
├── src/
│   ├── cli/              # CLI entry point + formatter
│   ├── config/           # Layered config loader (safety‑aware)
│   ├── governance/       # Policy engine, redactor, hook framework
│   ├── project/          # Project lifecycle (create/open/init/repair)
│   ├── task/             # Task lifecycle (create/complete/fail)
│   ├── decision/         # ADR management (propose/accept/reject)
│   ├── verification/     # Verification pipeline + result binding
│   ├── delivery/         # Delivery pipeline (guard/commit/PR/report)
│   ├── observability/    # Events, traces, run reports
│   ├── runtime/          # Session, pipeline, turn orchestrator
│   ├── context/          # Context Pack building
│   ├── skills/           # MCP Skill registry
│   └── state/            # Run, checkpoint, SQLite state
├── tests/
│   ├── unit/             # 528 unit tests
│   └── integration/      # 28 integration tests
├── harness_os_docs/      # Full design specification (12 documents)
├── .claude/              # Claude Code project configuration
└── .project/             # Harness OS local state (gitignored)
```

---

## Documentation

Full design and engineering specifications are in [`harness_os_docs/`](harness_os_docs/README.md):

| Doc | Description |
|---|---|
| [01_ARCHITECTURE](harness_os_docs/01_ARCHITECTURE.md) | System architecture and core principles |
| [02_CODEX_DEVELOPMENT_SPEC](harness_os_docs/02_CODEX_DEVELOPMENT_SPEC.md) | Development specification for Codex |
| [03_AGENTS_MD_STANDARD](harness_os_docs/03_AGENTS_MD_STANDARD.md) | AGENTS.md protocol standard |
| [04_HARNESS_OS_DESIGN](harness_os_docs/04_HARNESS_OS_DESIGN.md) | Detailed system design |
| [05_CONTEXT_ENGINEERING](harness_os_docs/05_CONTEXT_ENGINEERING.md) | Context engineering specification |
| [06_TASK_DECISION_PROJECT_MANAGER](harness_os_docs/06_TASK_DECISION_PROJECT_MANAGER.md) | Task, decision, and project management |
| [07_MCP_SKILLS_SPEC](harness_os_docs/07_MCP_SKILLS_SPEC.md) | MCP skills specification |
| [08_GOVERNANCE_SECURITY](harness_os_docs/08_GOVERNANCE_SECURITY.md) | Governance and security rules |
| [09_VERIFICATION_OBSERVABILITY](harness_os_docs/09_VERIFICATION_OBSERVABILITY.md) | Verification and observability |
| [10_DELIVERY_PIPELINE](harness_os_docs/10_DELIVERY_PIPELINE.md) | Delivery pipeline specification |
| [11_ACCEPTANCE_CRITERIA](harness_os_docs/11_ACCEPTANCE_CRITERIA.md) | Final acceptance criteria |
| [12_OPEN_SOURCE_REFERENCES](harness_os_docs/12_OPEN_SOURCE_REFERENCES.md) | Open source reference mapping |
| [13_TESTING_STRATEGY](harness_os_docs/13_TESTING_STRATEGY.md) | Testing strategy |
| [14_ERROR_CODES](harness_os_docs/14_ERROR_CODES.md) | Error code reference |
| [15_CONFIG_REFERENCE](harness_os_docs/15_CONFIG_REFERENCE.md) | Configuration reference |
| [16_CLI_OUTPUT_CONTRACT](harness_os_docs/16_CLI_OUTPUT_CONTRACT.md) | CLI output contract |
| [17_PROJECT_STORAGE_GIT_POLICY](harness_os_docs/17_PROJECT_STORAGE_GIT_POLICY.md) | Git and storage policy |
| [18_MIGRATION_VERSIONING](harness_os_docs/18_MIGRATION_VERSIONING.md) | Migration and versioning |

---

## Development

```bash
# Type check
pnpm typecheck

# Run unit tests
pnpm test:unit

# Run integration tests
pnpm test:integration

# Run all tests
pnpm test

# Run with coverage
pnpm test:coverage

# Build
pnpm build

# Format code
pnpm format
```

### Test Status

- **528 unit tests** — 19 test files, all passing
- **28 integration tests** — 1 test file, all passing
- **Coverage threshold**: 80% (configured in vitest.config.ts)
- **TypeScript**: Strict mode, all `as any` eliminated from `src/`

---

## Design Principles

1. **Boundary clarity**: Every module has a defined responsibility. No god objects.
2. **Conservative permissions**: Default `needs_approval`. Never default `allow`.
3. **State traceability**: Every write has a schema, scope, actor, reason, and trace ID.
4. **Tool call auditability**: Every invocation records who, what, input, decision, and timestamp.
5. **Low coupling**: Thin Harness first. Thick Harness as extensions, never mixed in.
6. **Fail closed**: Any hook failure, timeout, or unparseable result → `needs_approval`.

---

## Status

**v1.0.0-rc.2** — Release candidate for core governance and verification.

Implemented:
- ✅ CLI framework (17 commands)
- ✅ Multi-layer config with safety field enforcement
- ✅ Secret redaction (15+ patterns across all output boundaries)
- ✅ Verification pipeline with integrity-bound results
- ✅ Delivery pipeline with guard checks
- ✅ Observability (events, traces, run reports)
- ✅ ADR management (propose/accept/reject/supersede)
- ✅ Session and state management
- ✅ Task lifecycle (create → run → complete → report)
- ✅ Skills registry (4 built-in skills)
- ✅ Checkpoint and rollback analysis
- ✅ 528 unit tests + 28 integration tests

Planned for v1.1+:
- Policy hot-reload
- Multi-provider runtime (Claude + GPT + open models)
- Distributed approval UI
- OpenTelemetry export
- Sandboxed tool execution

---

## v1.1 Real Loop (June 2026)

**Status**: ✅ Closed (`real_loop_complete: true` | `mock_used: false`)

v1.1 implements a **5-node real agent loop** — the first end-to-end execution where Hermes dispatches real agents (OpenCode, Codex) through a governed pipeline without mock or simulation.

| Node | Type | Status | Executor |
|------|------|--------|----------|
| 001 — Fix P1 Gaps | `normal` | ✅ PASSED | OpenCode (DeepSeek) |
| 002 — StarMap Completion | `normal` | ✅ PASSED (2 repairs) | OpenCode (DeepSeek) |
| 003 — Repair Negative Sample | `repair_negative_sample` | ✅ CORRECTLY DETECTED | OpenCode (DeepSeek) |
| 004 — Codex Final Review | `final_review` | ✅ APPROVED | Codex CLI (gpt-5.5) |
| 005 — Merge Gate & StarMap | `final_gate` | ✅ DONE | Hermes handler |

**Key innovations in v1.1**:
- **Type-based dispatch** — `node_index.yaml` type field routes nodes to correct handler
- **Codex Final Reviewer** — Dedicated handler calls Codex CLI directly, not as an executor node
- **Repair negative sample validation** — Node designed to fail audit, proving repair detection works
- **Evidence pack** — All artifacts under `.harness/evidence/v1_1_real_loop/`
- **Hermes as pure orchestrator** — Dispatches but never writes business code

Full report: [`docs/v1_1_real_loop_report.md`](docs/v1_1_real_loop_report.md)
Evidence index: `.harness/evidence/v1_1_real_loop/EVIDENCE_INDEX.md`
Architecture: [`docs/v1_1_architecture.md`](docs/v1_1_architecture.md)

---

## License

ISC
