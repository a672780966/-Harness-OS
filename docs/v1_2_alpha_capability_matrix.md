# v1.2-alpha Capability Matrix

## Capabilities (Have)

| Capability | Module | Status | CLI Entry |
|------------|--------|--------|-----------|
| **Project Semantic Scanning** | `project_scanner.py` | ✅ | `inspect` |
| **Diff Summary & Analysis** | `diff_analyzer.py`, `change_explainer.py` | ✅ | `diff-summary` |
| **Risk Classification** | `risk_classifier.py` | ✅ | (included in task-card / readiness) |
| **Task Cards** | `task_card.py`, `suggestion_engine.py` | ✅ | `task-card` |
| **Merge Readiness Evaluation** | `merge_readiness.py` | ✅ | `readiness` |
| **Full Dashboard (markdown/json)** | `view_models.py`, `markdown_renderer.py`, `json_renderer.py` | ✅ | `dashboard`, `modules`, `task-cards` |
| **Evidence Pack** | `evidence_pack.py` | ✅ | `evidence` |
| **Loop Artifact Mapping** | `integration/` (4 mappers) | ✅ | `from-loop`, `repair-cards`, `evidence` |
| **HTML Static Dashboard** | `shell/` | ✅ | `shell`, `shell-from-loop`, `preview` |
| **Realtime File Monitor** | `monitor/` | ✅ | `monitor`, `monitor-loop` |
| **Agent Lifecycle State** | `agent_state/` | ✅ | `agent-state`, `agent-state-from-loop` |
| **PR/MR Local Pack** | `pr_integration/` | ✅ | `pr-pack`, `pr-pack-from-loop`, `pr-comment`, `pr-comment-from-loop` |
| **Provider Reliability Guard** | `provider_guard/` | ✅ | `provider-status` |
| **Live Event Stream** | `live/` (event bus, SSE server) | ✅ | `live-events`, `live-events-from-loop`, `live-server` |
| **Live Dashboard HTML** | `live/` (dashboard, HTML renderer) | ✅ | `live-dashboard`, `live-dashboard-from-loop` |

## Explicit Exclusion

| Capability | Status | Reason |
|------------|:------:|--------|
| Automatic code modification | ❌ Not included | Read-only by design; local agent calls happen externally |
| Automatic merge / push / deploy | ❌ Not included | Local sandbox only; no CI/CD integration |
| GitHub/GitLab API integration | ❌ Not included | PR pack is local-only; API integration deferred |
| Cloud sync / remote storage | ❌ Not included | All data stored locally |
| Credential / secret storage | ❌ Not included | No tokens, passwords, or API keys managed |
| Music generation / audio APIs | ❌ Not included | Out of scope |
| Agent control / auto-spawn | ❌ Not included | Harness orchestrator role not replicated in local MVP |
| Windows native support | ❌ Not sealed | WSL2 recommended for Windows use |
| Provider model inference | ❌ Degraded | Upstream model timeout; local features unaffected |
