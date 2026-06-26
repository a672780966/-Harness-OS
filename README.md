
<p align="center">
  <img src="https://img.shields.io/badge/version-v1.4--loop--installer--mvp-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/copilot_tests-616%20passed-brightgreen?style=flat-square" alt="Copilot Tests">
  <img src="https://img.shields.io/badge/full_pytest-848%20passed-brightgreen?style=flat-square" alt="Full Tests">
  <img src="https://img.shields.io/badge/license-ISC-green?style=flat-square" alt="License">
</p>

<p align="center">
  <a href="README.md"><strong>🇬🇧 English</strong></a> ·
  <a href="README.zh.md"><strong>🇨🇳 中文</strong></a> ·
  <a href="README.ja.md"><strong>🇯🇵 日本語</strong></a> ·
  <a href="README.ko.md"><strong>🇰🇷 한국어</strong></a>
</p>

<h1 align="center">Harness OS</h1>
<p align="center"><em>Local Semantic Copilot + Governed Agent Engineering Runtime</em></p>

---

**Harness OS is a local semantic copilot and governed agent engineering runtime for AI-assisted software delivery.**

It answers:
- What changed?
- What modules are affected?
- Is this ready to merge?
- What risks should a reviewer see?
- What evidence supports the decision?
- How should a PR be drafted?

---

## Current Status

- **Baseline**: `v1.4-loop-installer-mvp`
- **Latest capability**: `v1.4-loop-installer-mvp`
- **Copilot tests**: `616 passed`
- **Full pytest**: `848 passed`
- **Mode**: local-first, read-only semantic copilot
- **GitHub tag policy**: public-safe tags only; large evidence archives are kept out of Git tags

---

## What Is Included

### v1.1 — Real Hermes Loop
- graph planner
- loop runner/controller
- executor/auditor
- eval-triggered repair
- review-triggered repair
- final gate
- evidence pack

### v1.2 — Local Semantic Copilot MVP
- project inspection
- diff summary
- task cards
- merge readiness
- evidence pack
- static shell
- realtime monitor
- agent state machine
- PR/MR pack
- provider reliability guard
- live dashboard

### v1.2.1 — Dogfood Stabilization
- risk deduplication
- source/docs filtering
- file type expansion
- false approval-blocking fix
- clean-clone idle explanation

### v1.3 — Runtime Foundation
- config schema / loader / resolver / validator
- runtime doctor
- version command
- provider reliability planning
- cross-project runtime planning
- public-safe evidence strategy

### v1.3.1 — PR Draft Assistant
- `harness copilot pr-draft`
- GitHub CLI detection
- manual fallback PR draft generation
- large-file/cache blocking checks
- optional authenticated `--create`

---

## Quick Start

```bash
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS
# Option 1: Python CLI (no install required)
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
python -m harness.copilot.cli inspect .
python -m harness.copilot.cli dashboard .
python -m harness.copilot.cli pr-draft --base main

# Option 2: Node CLI (requires pnpm + node)
pnpm install
pnpm build
./dist/index.js version --json
./dist/index.js doctor
```

If the `harness` command is not available:
```bash
python -m harness.copilot.cli version --json
python -m harness.copilot.cli doctor
```
After building (`pnpm install && pnpm build`), the `harness` bin is at `./dist/index.js`.

---

## Important Docs

- [v1.3 Main Integration Seal](docs/v1_3_main_integration_seal.md)
- [v1.2 Alpha Final Seal Manifest](docs/v1_2_alpha_final_seal_manifest.md)
- [v1.2 Alpha Command Reference](docs/v1_2_alpha_command_reference.md)
- [Public-Safe Evidence Strategy](docs/public_safe_evidence_strategy.md)
- [Public-Safe Tag Mapping](docs/public_safe_tag_mapping.md)
- [Large Evidence Archive Manifest](docs/large_evidence_archive_manifest.md)
- [GitHub Cloud Simulation Report](docs/github_cloud_simulation_report.md)

---

## Tag / Evidence Policy

Some local sealed tags are intentionally **not pushed** to GitHub because their reachable history includes a 373 MB SWE-bench evidence archive, which GitHub rejects due to the 100 MB blob limit.

Public-safe tags are pushed. Large evidence archives should be stored as release assets or external cold archives, while Git keeps manifests and SHA256 references.

---

## What Harness OS Is Not

Harness OS is **not** a model provider, not a general coding framework, and not a cloud SaaS product yet.

It is currently a **local-first semantic copilot and governance layer** for AI-assisted engineering.
