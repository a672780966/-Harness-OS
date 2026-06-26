# Contributing to Harness OS

Thank you for considering contributing to Harness OS!

## Quick Start

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS

# Node CLI (primary)
pnpm install
pnpm build
./dist/index.js version

# Python CLI (optional)
python -m pip install -e .
python -m harness.copilot.cli version
```

## Development Workflow

Harness OS follows a governed agent loop:

1. **Plan** — Codex creates a task envelope with objective and acceptance criteria
2. **Implement** — Worker (OpenCode / Claude Code) works within assigned scope
3. **Test** — All changes must have passing tests
4. **Review** — Open Code Review + Codex Review must pass
5. **Evidence** — Result envelopes, review envelopes, and audit events are required
6. **Final Gate** — Codex must approve before merge

## Branch Convention

- Feature branches: `feat/<description>`
- Fix branches: `fix/<description>`
- Productization branches: `productize/<description>`

## Before Submitting

- [ ] Python tests: `python -m pytest tests/ -q`
- [ ] Node tests: `pnpm test --run`
- [ ] Node build: `pnpm build`
- [ ] CLI smoke: `python -m harness.copilot.cli version`
- [ ] No modified files outside change scope

## Hard Rules

- No direct main branch modification
- No force push
- No deployment in local loop
- Max 3 repair rounds per task
- High-risk path changes (`.github/workflows/`, `pyproject.toml`, etc.) require human approval
- Worker claims are not evidence — tests, diffs, audit events, and review outputs are

## Governance

Every task moves through: Planner → TaskEnvelope → Worker → ResultEnvelope → Reviewer → ReviewEnvelope → Codex Review → FinalEvidence → Audit

See `AGENTS.md` for the full governance model.
