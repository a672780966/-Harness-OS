# v1.2-alpha Local Copilot — Usage Guide

## Product Positioning

Harness Code Copilot 是一个**本地只读 AI 编码语义副驾驶**。它不写代码、不控制 Agent、不调外部 API。它消费项目源码和 Hermes Loop 运行产物，生成人类可读的仪表盘、任务卡、合并就绪度评估和证据包。

## Prerequisites

- Python 3.11+
- Git repository (for diff/status features)
- Hermes Loop artifacts (optional, for `from-loop` / `shell-from-loop`)

## Quick Start

### 1. Scan a Project

```bash
cd your-project/
harness copilot inspect .
```

Shows: files, lines, modules, languages, risk overview.

### 2. View Full Dashboard

```bash
harness copilot dashboard . --format markdown
```

Includes: modules, recent changes, suggestions, task cards, merge readiness, evidence pack.

### 3. Generate HTML Dashboard

```bash
harness copilot shell . --out .harness/copilot_dashboard/
# Open file://.harness/copilot_dashboard/index.html in browser
```

Self-contained HTML with tab navigation, dark theme, and embedded JSON data.

### 4. Preview in Browser

```bash
harness copilot shell . --out /tmp/dash/
harness copilot preview /tmp/dash/ --port 8080
# Visit http://127.0.0.1:8080
```

### 5. Load Hermes Loop Results

```bash
harness copilot from-loop .harness/evaluations/xxx/runs/instance/tier_C_full --format markdown
harness copilot shell-from-loop .harness/evaluations/xxx/runs/instance/tier_C_full --out /tmp/loop-dash/
```

### 6. Export Task Cards

```bash
harness copilot export-task-card . --out tasks.md
harness copilot export-task-card . --card-index 0 --out fix-this.md
```

### 7. Start Monitoring

```bash
harness copilot monitor . --interval 3
# Ctrl+C to stop

# With optional dashboard refresh
harness copilot monitor . --interval 5 --out .harness/copilot_dashboard/

# Loop artifact monitoring
harness copilot monitor-loop .harness/evaluations/xxx/runs/instance/tier_C_full --interval 3
```

## Read-Only Boundary

| Can Do | Cannot Do |
|--------|-----------|
| Read git status/diff | Write to project source |
| Read Hermes Loop artifacts | Modify sealed evidence |
| Write to `--out` directory | Auto-send to Codex/Claude Code |
| Start local preview server | Call external APIs |
| Generate HTML/JSON output | Auto-merge or auto-repair |
| Poll file system for changes | Control agents |
| | Play music or audio |

## What This Tool Does NOT Do

- ❌ Write code
- ❌ Control Claude Code / Codex / OpenCode
- ❌ Auto-merge or auto-push
- ❌ Auto-repair test failures
- ❌ Call external APIs (GitHub, Slack, etc.)
- ❌ Play music or audio
- ❌ Deploy to any environment
- ❌ Upload data to cloud

## Common Workflows

### Daily Development

```bash
# 1. Check project status
harness copilot dashboard .

# 2. Review recent changes
harness copilot diff-summary .

# 3. Export relevant task cards
harness copilot export-task-card . --out tasks.md

# 4. Check merge readiness before PR
harness copilot readiness .
```

### After a Hermes Loop Run

```bash
# 1. Load loop results
harness copilot from-loop runs/my-run/tier_C_full

# 2. Check for repair cards
harness copilot repair-cards runs/my-run/tier_C_full

# 3. Generate browsable HTML
harness copilot shell-from-loop runs/my-run/tier_C_full --out /tmp/review/
harness copilot preview /tmp/review/
```

## FAQ

**Q: Does this tool push to GitHub?**
No. All commands are local-only.

**Q: Does it modify my code?**
No. Read-only by design. Only writes to explicitly specified `--out` directories.

**Q: Can I use it without Hermes Loop?**
Yes. Phase 1/2/4/5 work on any git repo without loop artifacts.

**Q: Can I browse the output in a browser?**
Yes. Use `harness copilot shell` to generate HTML, then `harness copilot preview` to serve it.

**Q: How often does the monitor poll?**
Default 3 seconds. Adjust with `--interval`.
