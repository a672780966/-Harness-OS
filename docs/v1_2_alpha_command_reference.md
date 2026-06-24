# v1.2-alpha Command Reference

## Overview

All commands are run via:

```bash
python3 -m harness.copilot.cli <command> [args...]
```

Or via the provided entry point (if installed):

```bash
harness copilot <command> [args...]
```

All commands are **read-only**. No code modification, no external agent control.

---

## Command List

### Project Inspection

| Command | Description | Example |
|---------|-------------|---------|
| `inspect <project_path>` | Scan project structure and show semantic map | `inspect .` |

### Diff Analysis

| Command | Description | Example |
|---------|-------------|---------|
| `diff-summary <project_path> [--diff-ref=<ref>] [--quick]` | Summarize recent git changes | `diff-summary . --diff-ref=HEAD~3` |

### Task Cards

| Command | Description | Example |
|---------|-------------|---------|
| `task-card <project_path> [--diff-ref=<ref>] [--json] [--verbose]` | Generate prioritized task cards | `task-card . --verbose` |

### Merge Readiness

| Command | Description | Example |
|---------|-------------|---------|
| `readiness <project_path> [--diff-ref=<ref>] [--json]` | Evaluate merge readiness | `readiness . --json` |

### Dashboard (User-Friendly)

| Command | Description | Example |
|---------|-------------|---------|
| `dashboard <project_path> [--diff-ref=<ref>] [--format=markdown\|json]` | Full project dashboard | `dashboard . --format markdown` |
| `modules <project_path> [--diff-ref=<ref>] [--format=markdown\|json]` | Module cards | `modules .` |
| `task-cards <project_path> [--diff-ref=<ref>] [--format=markdown\|json]` | Task cards (UX) | `task-cards .` |

### Loop Artifact Integration

| Command | Description | Example |
|---------|-------------|---------|
| `from-loop <loop_run_dir> [--format=markdown\|json]` | Dashboard from loop artifacts | `from-loop <dir>` |
| `evidence <loop_run_dir> [--format=markdown\|json]` | Evidence pack from loop | `evidence <dir>` |
| `repair-cards <loop_run_dir> [--format=markdown\|json]` | Repair cards from loop | `repair-cards <dir>` |

### HTML Shell Dashboard

| Command | Description | Example |
|---------|-------------|---------|
| `shell <project_path> [--out=<dir>] [--diff-ref=<ref>]` | Generate static HTML dashboard | `shell . --out ./dashboard/` |
| `shell-from-loop <loop_run_dir> [--out=<dir>]` | Generate HTML dashboard from loop | `shell-from-loop <dir>` |
| `export-task-card <project_path> [--out=<file>] [--diff-ref=<ref>] [--card-index=<n>]` | Export task card(s) as markdown | `export-task-card . --card-index=0` |
| `preview <dashboard_dir> [--port=8080]` | Start local read-only preview server | `preview ./dashboard/` |

### Realtime Monitor

| Command | Description | Example |
|---------|-------------|---------|
| `monitor <project_path> [--interval=3.0] [--out=<dir>]` | Start file monitoring | `monitor .` |
| `monitor-loop <loop_run_dir> [--interval=3.0] [--out=<dir>]` | Start loop artifact monitoring | `monitor-loop <dir>` |

### Agent State

| Command | Description | Example |
|---------|-------------|---------|
| `agent-state <project_path> [--diff-ref=<ref>] [--format=markdown\|json]` | Inferred agent lifecycle state | `agent-state . --format json` |
| `agent-state-from-loop <loop_run_dir> [--format=markdown\|json]` | Agent state from loop | `agent-state-from-loop <dir>` |

### PR/MR Local Pack

| Command | Description | Example |
|---------|-------------|---------|
| `pr-pack <project_path> [--out=<dir>] [--diff-ref=<ref>]` | Export local PR review pack | `pr-pack . --out ./pr-pack/` |
| `pr-pack-from-loop <loop_run_dir> [--out=<dir>]` | PR pack from loop | `pr-pack-from-loop <dir>` |
| `pr-comment <project_path> [--diff-ref=<ref>] [--format=markdown\|json]` | Generate PR comment text | `pr-comment . --format markdown` |
| `pr-comment-from-loop <loop_run_dir> [--format=markdown\|json]` | PR comment from loop | `pr-comment-from-loop <dir>` |

### Provider Reliability Guard

| Command | Description | Example |
|---------|-------------|---------|
| `provider-status [--check] [--format=markdown\|json]` | Show provider health | `provider-status --json` |

### Live Event Stream

| Command | Description | Example |
|---------|-------------|---------|
| `live-events <project_path> [--diff-ref=<ref>]` | Capture project live events | `live-events .` |
| `live-events-from-loop <loop_run_dir>` | Capture loop live events | `live-events-from-loop <dir>` |
| `live-server <project_path> [--host=127.0.0.1] [--port=8765] [--once]` | Start local SSE live event server | `live-server . --once` |

### Live Dashboard HTML

| Command | Description | Example |
|---------|-------------|---------|
| `live-dashboard <project_path> [--out=<dir>] [--diff-ref=<ref>]` | Generate live dashboard HTML | `live-dashboard . --out ./live/` |
| `live-dashboard-from-loop <loop_run_dir> [--out=<dir>]` | Live dashboard from loop | `live-dashboard-from-loop <dir>` |

---

## Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Output full JSON (some commands) |
| `--verbose`, `-v` | Verbose output |
