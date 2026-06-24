# GitHub Cloud Simulation Report

## Simulation Method

**Chosen**: GitHub Codespaces (not GitHub Actions)

**Reason**: Codespaces simulates a real cloud developer environment more faithfully. The user can open a browser-based VS Code, run `harness copilot` commands interactively, and experience the output firsthand. GitHub Actions would only validate automated runs and artifacts — no hands-on UX feedback.

## Prerequisites

The repo currently lacks a `.devcontainer/` configuration. To launch Codespaces, create:

```yaml
# .devcontainer/devcontainer.json
{
  "name": "Harness OS Codespace",
  "image": "mcr.microsoft.com/devcontainers/universal:2",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    }
  },
  "postCreateCommand": "python3 -m venv .venv && .venv/bin/pip install -e harness/ && pip install pyyaml jsonschema pytest rich",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"]
    }
  }
}
```

This is infrastructure setup (not a new feature) and must be committed to the repo before launching Codespaces.

## Simulation Sequence

### Step 1: Launch Codespace

Open the repo on GitHub → Code → Codespaces → Create codespace on main.

### Step 2: Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e harness/
pip install pyyaml jsonschema pytest rich
```

### Step 3: Run Smoke Test

```bash
pytest tests/copilot/test_pr_draft.py -v
pytest tests/ -x --tb=short
```

Expected: 848 passed. If tests fail, the environment is missing system dependencies (git, ssh, etc.).

### Step 4: Explore — `harness copilot inspect`

```bash
harness copilot inspect .
```

Expected output: module tree, file count, language breakdown.

Dogfood question: *Is the output immediately useful to a new user?*

### Step 5: Explore — `harness copilot readiness`

```bash
harness copilot readiness .
```

Expected output: merge readiness summary (risks, blocking items).

Dogfood question: *Does it highlight real issues or produce noise?*

### Step 6: Explore — `harness copilot task-card`

```bash
harness copilot task-card .
```

Expected output: task recommendation cards referencing specific modules and diffs.

Dogfood question: *Are the cards actionable or too vague?*

### Step 7: Explore — `harness copilot pr-draft`

```bash
harness copilot pr-draft .
```

Expected output: `.harness/pr_drafts/<timestamp>/` with title, body, compare URL, instructions.

Dogfood question: *Is the draft PR body usable as-is, or does it need heavy editing?*

### Step 8: Explore — `harness copilot shell`

```bash
harness copilot shell . --out .harness/copilot_dashboard/
```

Expected output: Static HTML dashboard at `.harness/copilot_dashboard/index.html`.

Dogfood question: *Does the dashboard give a useful project overview?*

### Step 9: Explore — `harness copilot live-dashboard`

```bash
harness copilot live-dashboard . --out .harness/live_dashboard/
```

Expected output: Live dashboard HTML (static snapshot).

Dogfood question: *Is it visually useful without a server?*

## Evaluation Criteria

| # | Question | Answer (to fill after simulation) |
|---|----------|:----------------------------------:|
| 1 | GitHub 云端环境能否成功安装/运行？ | ⬜ |
| 2 | 首次运行命令是什么？ | ⬜ |
| 3 | 输出是否清楚？ | ⬜ |
| 4 | dashboard/readiness/task-card 是否有实际判断价值？ | ⬜ |
| 5 | pr-draft 是否比手动写 PR 更省事？ | ⬜ |
| 6 | 哪些地方让用户困惑？ | ⬜ |
| 7 | 是否值得继续升级，还是应该先简化？ | ⬜ |

## Suggested Commands Cheatsheet (for Codespaces terminal)

```bash
# 1. Activate venv
source .venv/bin/activate

# 2. Explore project
harness copilot inspect .
harness copilot readiness .

# 3. Generate task cards
harness copilot task-card .

# 4. Generate PR draft
harness copilot pr-draft .

# 5. Generate dashboards
harness copilot shell . --out /tmp/dashboard
harness copilot live-dashboard . --out /tmp/live_dashboard

# 6. Open dashboard (if simple HTTP server is available)
python3 -m http.server 8080 -d /tmp/dashboard
```

## Limitations

| Limitation | Impact |
|------------|:------:|
| No `origin/main` diff in Codespaces (fresh clone) | Some commands (`readiness`, `pr-draft`) need a branch with commits ahead of main |
| No gh CLI token by default | `pr-draft --create` unavailable; manual draft only |
| System dependencies (git, python3, pip) are standard in Codespaces | Low risk |
| Large evidence archive (373 MB) not in working tree | Expected — `.gitignore` excludes it; commands should handle this gracefully |

## Next Steps After Simulation

1. Fill in the evaluation table with real results.
2. If any command crashed, file an issue.
3. Decide whether the UX is good enough for public demo or needs simplification first.
