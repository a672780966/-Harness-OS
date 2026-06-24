# v1.2-alpha Local Copilot — CLI Reference

**16 commands** across 5 phases. All read-only, no external API, no agent control.

---

## Phase 1: Kernel Layer

### `harness copilot inspect <project_path>`

Scan project structure and show semantic map overview.

```
$ harness copilot inspect .
📁 Project: -Harness-OS
   Files: 213
   Lines: 31,240
   Modules: 12
```

### `harness copilot diff-summary <project_path> [--diff-ref=<ref>]`

Summarize recent git changes with module-level intent analysis.

### `harness copilot task-card <project_path> [--diff-ref=<ref>]`

Generate task cards from risk alerts, change explanations, and suggestions.

### `harness copilot readiness <project_path> [--diff-ref=<ref>]`

Evaluate merge readiness: pass / block / review_needed.

---

## Phase 2: UX Layer

### `harness copilot dashboard <project_path> [--format markdown|json]`

Full project dashboard with modules, changes, suggestions, task cards, merge readiness, evidence.

### `harness copilot modules <project_path> [--format markdown|json]`

Module cards view — risk levels, dependencies, high-risk files.

### `harness copilot task-cards <project_path> [--format markdown|json]`

Task cards with priority labels and blocking status.

---

## Phase 3: Integration Layer

### `harness copilot from-loop <loop_run_dir> [--format markdown|json]`

Load Hermes Loop artifacts and render as Copilot dashboard.

### `harness copilot evidence <loop_run_dir> [--format markdown|json]`

Show evidence pack from a loop run (SHA256 integrity, pass/fail counts).

### `harness copilot repair-cards <loop_run_dir> [--format markdown|json]`

Extract repair task cards from eval failures and Codex review rejections.

---

## Phase 4: Local HTML Shell

### `harness copilot shell <project_path> --out <output_dir>`

Generate a self-contained static HTML dashboard for a project. Embedded CSS, tab navigation, copy support.

### `harness copilot shell-from-loop <loop_run_dir> --out <output_dir>`

Generate a static HTML dashboard from a Hermes Loop run directory.

### `harness copilot export-task-card <project_path> [--card-index <n>] [--out <file.md>]`

Export task cards as copyable text and markdown documents.

### `harness copilot preview <dashboard_dir> [--port <n>]`

Start a local read-only HTTP server (default port 8080) to preview a dashboard. Refuses PUT/POST/DELETE.

---

## Phase 5: Realtime Monitor

### `harness copilot monitor <project_path> [--interval <s>] [--out <dir>] [--once]`

Poll-based project watcher. Detects file changes, git status changes, module risk changes. Outputs color-coded terminal events.

### `harness copilot monitor-loop <loop_run_dir> [--interval <s>] [--out <dir>] [--once]`

Poll-based loop artifact watcher. Detects eval/review/gate/report changes. Events: eval_report_changed, test_result_changed, review_result_changed, final_gate_changed, loop_report_changed.

---

## Common Options

| Flag | Applies To | Description |
|------|-----------|-------------|
| `--format markdown\|json` | dashboard, modules, task-cards, from-loop, evidence, repair-cards | Output format |
| `--diff-ref <ref>` | diff-summary, task-card, readiness, shell | Git diff base ref (default: HEAD~1) |
| `--out <path>` | shell, shell-from-loop, export-task-card, monitor, monitor-loop | Output directory or file |
| `--interval <s>` | monitor, monitor-loop | Poll interval in seconds (default: 3) |
| `--once` | monitor, monitor-loop | Single poll then exit |
| `--port <n>` | preview | HTTP port (default: 8080) |
| `--json` | inspect, diff-summary, task-card, readiness | Full JSON output |
| `--verbose, -v` | All | Verbose output |
