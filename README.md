
<p align="center">
  <img src="https://img.shields.io/badge/version-v1.4--loop--installer--mvp-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/copilot_tests-958%20passed-brightgreen?style=flat-square" alt="Copilot Tests">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="License">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<h1 align="center">Harness OS</h1>
<p align="center"><em>Agentic Engineering Governance Platform</em></p>

---

**Harness OS is a governance-first production loop for AI coding agents.** It turns AI-generated code from unsupervised patches into planned, reviewed, evidenced, and auditable engineering changes.

It answers:
- What did the agent actually change?
- What tests prove it works?
- Did a reviewer check the work?
- What risks should a human see?
- Who approved the high-risk actions?
- What is the full audit trail?

---

## Product Story

AI coding agents are powerful, but production engineering requires more than powerful code generation. It requires:

- **Planning** — What exactly should the agent do?
- **Contracts** — What scope is the agent allowed to work in?
- **Evidence** — What proves the work is correct?
- **Review** — Did an independent reviewer check the output?
- **Repair** — Are issues bounded and trackable?
- **Gate** — What evidence is required before acceptance?
- **Audit** — What happened, from start to finish?

Harness OS implements all of this as a **governed agent loop**: Codex plans the work, Hermes dispatches and collects evidence, workers implement within contracts, reviewers verify outputs, repairs are bounded (max 3 rounds), final gates require complete evidence, and everything is audited.

This is **not** another AI IDE or agent framework. It is an **Agentic Engineering Governance Platform** — the control plane for AI-generated code.

---

## Architecture

```
Codex (Planner)
    → TaskEnvelope
Worker (OpenCode / Claude Code)
    → ResultEnvelope + Tests
Open Code Review
    → ReviewEnvelope (blocking/non-blocking issues)
Codex (Advanced Review)
    → FinalEvidence + Audit
Human Approval → Merge
```

**Role separation**: Codex = planner/reviewer/gatekeeper, Hermes = dispatcher/evidence collector, Workers = implementation + self-review.

**Evidence hierarchy** (worker claims are NOT truth):
1. Security and policy rules
2. Test results
3. Audit events
4. Code review results
5. Git diff and changed files
6. Worker result envelope
7. Memory or summaries

See [Architecture](docs/architecture.md) for details.

---

## Quick Start

You have two CLI options. **Python is recommended for first use.**

### Option 1: Python CLI (recommended)

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
python -m pip install -e .
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
python -m harness.copilot.cli dashboard .
python -m harness.copilot.cli inspect .
```

### Option 2: Node CLI

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
pnpm install
pnpm build
./dist/index.js version
./dist/index.js doctor
```

### 5-Minute Demo

```bash
python -m harness.copilot.cli version           # System identity
python -m harness.copilot.cli doctor            # Health check
python -m harness.copilot.cli dashboard .       # Project status
ls .harness/temp_loop/e1b40fbb0476/             # Complete task evidence
cat .harness/temp_loop/e1b40fbb0476/_summary.json  # Task verdict
```

See [MVP Quickstart](docs/mvp_quickstart.md) for the full walkthrough.

---

## What Is Included

### v1.1 — Real Hermes Loop
- Graph planner
- Loop runner/controller
- Executor/auditor
- Eval-triggered repair
- Review-triggered repair
- Final gate
- Evidence pack

### v1.2 — Local Semantic Copilot MVP
- Project inspection
- Diff summary
- Task cards
- Merge readiness
- Evidence pack
- Static shell
- Realtime monitor
- Agent state machine
- PR/MR pack
- Provider reliability guard
- Live dashboard

### v1.2.1 — Dogfood Stabilization
- Risk deduplication
- Source/docs filtering
- File type expansion
- False approval-blocking fix
- Clean-clone idle explanation

### v1.3 — Runtime Foundation
- Config schema / loader / resolver / validator
- Runtime doctor
- Version command
- Provider reliability planning
- Cross-project runtime planning

### v1.3.1 — PR Draft Assistant
- `harness copilot pr-draft`
- GitHub CLI detection
- Manual fallback PR draft generation
- Large-file/cache blocking checks
- Optional authenticated `--create`

### v1.4 — Loop Installer MVP
- Loop setup/init/run commands
- Multi-agent topology suggestions
- Envelope system (task/result/review)
- State machine with transitions

---

## Current Status

- **Baseline**: `v1.4-loop-installer-mvp`
- **CLI commands**: 40+
- **Python tests**: 958 passed / 1 skipped
- **Completed loops**: 2 full evidence chains with repair rounds + human approval
- **Mode**: local-first, read-only semantic copilot
- **License**: ISC

---

## Roadmap

- **Current**: Productization Sprint — making Harness OS installable and understandable for new developers
- **Next**: More complete loop iterations, simplified evidence inspection, public documentation cleanup
- **Future**: Superlog integration, multi-agent orchestration, enterprise RBAC (see AGENTS.md for full scope)

---

## Documentation

| Document | Description |
|----------|-------------|
| [Quickstart](docs/mvp_quickstart.md) | 5-minute walkthrough |
| [Architecture](docs/architecture.md) | Core concepts and role separation |
| [Demo Script](docs/hackathon-demo-script.md) | 5-minute presentation guide |
| [Agent Instructions](AGENTS.md) | Full governance model for AI agents |
| [Contributing](CONTRIBUTING.md) | How to contribute |

---

## What Harness OS Is Not

Harness OS is **not** a model provider, not a general coding framework, and not a cloud SaaS product (yet). It is currently a **local-first governance layer** for AI-assisted engineering.

---

## License

ISC — see [package.json](package.json) for details.
