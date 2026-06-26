# Harness OS — 5-Minute Quickstart

```bash
# 1. Clone
git clone https://github.com/a672780966/-Harness-OS.git
cd -Harness-OS

# 2. Install Python CLI
python -m pip install -e .

# 3. Verify
python -m harness.copilot.cli version
# → Harness Copilot vv1.4-loop-installer-mvp

# 4. Health check
python -m harness.copilot.cli doctor
# → 5/7 checks pass, 2 benign warnings

# 5. Dashboard
python -m harness.copilot.cli dashboard .

# 6. Inspect
python -m harness.copilot.cli inspect .

# 7. Explore completed loop evidence
ls .harness/temp_loop/e1b40fbb0476/
cat .harness/temp_loop/e1b40fbb0476/_summary.json
```

## What you just saw

| Command | What it shows |
|---------|---------------|
| `version` | System identity and current release |
| `doctor` | Environment readiness check |
| `dashboard .` | Project state, agent lifecycle, merge readiness |
| `inspect .` | Codebase overview (files, modules, risk) |
| Evidence dir | Complete task lifecycle: plan → work → review → gate → audit |

## Node CLI (alternative)

```bash
pnpm install
pnpm build
./dist/index.js version
./dist/index.js doctor
```
