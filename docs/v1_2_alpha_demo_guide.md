# v1.2-alpha Demo Guide

## Prerequisites

- Python 3.10+ with required packages installed
- Working directory: Harness OS project root
- All commands are read-only — no risk to source files

---

## Project Demo (from current project)

### 1. Full Dashboard (Markdown)

```bash
harness copilot dashboard . --format markdown
```

Displays: project overview, risk alerts, merge readiness, evidence summary.

### 2. Static HTML Shell Dashboard

```bash
harness copilot shell . --out .harness/copilot_demo/final_project/
```

Open the generated HTML file:

```
.harness/copilot_demo/final_project/index.html
```

### 3. Agent Lifecycle State

```bash
harness copilot agent-state . --format markdown
```

Shows inferred agent state (e.g., implementing, reviewing, blocked).

### 4. PR Comment Preview

```bash
harness copilot pr-comment . --format markdown
```

Generates a full PR comment with changes summary, risk assessment, blocking issues.

### 5. Live Dashboard HTML

```bash
harness copilot live-dashboard . --out .harness/copilot_demo/final_live_project/
```

Open the generated HTML (includes Agent State card, Merge Readiness, Live Event Timeline, SSE client):

```
.harness/copilot_demo/final_live_project/index.html
```

---

## Loop Artifact Demo (from evaluation run)

### 1. Loop Dashboard (Markdown)

```bash
harness copilot from-loop \
  .harness/evaluations/swebench_abc_mini_pilot_001/runs/django__django-11885/tier_C_full \
  --format markdown
```

### 2. Loop HTML Shell Dashboard

```bash
harness copilot shell-from-loop \
  .harness/evaluations/swebench_abc_mini_pilot_001/runs/django__django-11885/tier_C_full \
  --out .harness/copilot_demo/final_loop/
```

Open:

```
.harness/copilot_demo/final_loop/index.html
```

### 3. Loop Live Dashboard HTML

```bash
harness copilot live-dashboard-from-loop \
  .harness/evaluations/swebench_abc_mini_pilot_001/runs/django__django-11885/tier_C_full \
  --out .harness/copilot_demo/final_live_loop/
```

Open:

```
.harness/copilot_demo/final_live_loop/index.html
```

---

## Live Server Demo

### 1. Start SSE Live Event Server

```bash
harness copilot live-server . --host 127.0.0.1 --port 8765
```

Access:

- `http://127.0.0.1:8765/events` — SSE stream
- `http://127.0.0.1:8765/latest` — Latest events (JSON)
- `http://127.0.0.1:8765/health` — Health check

---

## Quick Smoke Test

```bash
# Verify all major features respond
harness copilot inspect . --json | head -5
harness copilot diff-summary . --quick
harness copilot readiness .
harness copilot provider-status
harness copilot live-events . --once
```
