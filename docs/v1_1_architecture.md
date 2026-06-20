# v1.1 Architecture — Hermes Auto Loop

> Updated: 2026-06-20 (v1.1 Closure)

## Overview

The v1.1 architecture implements a **5-node linear auto loop** with type-based dispatch:

```
[Codex Graph Planner]
      ↓ (plan files)
[Hermes Auto Loop Runner]
      ↓ (type dispatch)
  ├─ normal          → OpenCode Executor → Fresh Auditor → Repair (if needed)
  ├─ repair_negative_sample → OpenCode Executor → Auditor → force repair trigger
  ├─ final_review    → Codex CLI (direct, not OpenCode)
  └─ final_gate      → Hermes handler (hermes.py commands)
      ↓
[Loop Report + Evidence Pack]
```

## Components

### 1. Codex Graph Planner

Role: Produces plan directory with node definitions, execution order, role bindings.

Outputs:
- `node_index.yaml` — node type definitions (normal, repair_negative_sample, final_review, final_gate)
- `nodes/*.md` — individual node specs
- `execution_order.yaml` — execution sequence + repair bindings
- `role_bindings.yaml` — agent-to-role mapping for each node
- `task_envelope.json` — task contract

### 2. Hermes Auto Loop Runner

Script: `.harness/scripts/hermes_auto_loop.py`

Key methods:
- `run()` — main loop: loads plan → iterates nodes → dispatches by type → generates report
- `_get_node_type(node_id, plan_dir)` — reads `node_index.yaml` to detect `normal`, `repair_negative_sample`, `final_review`, `final_gate`
- `execute_node()` — for `normal` and `repair_negative_sample` nodes: calls OpenCode CLI for execution + audit
- `run_codex_final_review_node()` — **new in v1.1**: collects all evidence, generates prompt, calls Codex CLI, parses output, writes attestation + envelope
- `run_final_gate_node()` — **new in v1.1**: runs `hermes.py final-merge-gate-dry-run`, updates StarMap
- `format_loop_report()` — generates structured markdown report

### 3. OpenCode Node Executor

CLI: `opencode run --model opencode-go/deepseek-v4-flash --dangerously-skip-permissions`

Produces:
- `result_envelope.json` — schema-validated result
- `executor_attestation.json` — signed execution record

### 4. OpenCode Fresh Auditor

CLI: `opencode run --model opencode-go/deepseek-v4-flash` (audit mode)

Produces:
- `review_envelope.json` — schema-validated review
- `auditor_attestation.json` — signed audit record

### 5. Codex Final Reviewer

CLI: `codex exec --dangerously-bypass-approvals-and-sandbox`

Produces:
- `codex_final_review.md` — review artifact
- `final_review_envelope.json` — schema-validated final decision
- `codex_attestation.json` — signed review record

### 6. Final Gate

CLI: `hermes.py final-merge-gate-dry-run`

Produces:
- `gate_result_envelope.json`
- AuditEvent log entry

### 7. StarMap

Location: `.harness/starmap/`

Files:
- `facts.jsonl` — append-only fact log
- `index.json` — fact index

## Type Dispatch Table

| node_index.yaml `type` | Executor | Auditor | Repair | Expected audit_passed |
|-----------------------|----------|---------|--------|----------------------|
| `normal` | OpenCode | OpenCode | yes (max 3 rounds) | true |
| `repair_negative_sample` | OpenCode | OpenCode | yes (detection only) | false (required) |
| `final_review` | Codex CLI | N/A (built-in) | N/A | N/A (approved/rejected) |
| `final_gate` | Hermes handler | N/A | N/A | N/A |

## Evidence Architecture

See `.harness/evidence/v1_1_real_loop/EVIDENCE_INDEX.md` for the full evidence map.

## Design Decisions

1. **No Claude Code in this loop** — DeepSeek provider compatibility was resolved via OpenCode fallback. Architecture supports Claude Code as primary executor.
2. **Type dispatch over string matching** — Explicit `type` field in `node_index.yaml` is cleaner than parsing node names.
3. **Codex CLI direct for final review** — Not routed through OpenCode to ensure independent review from a different model/provider.
4. **Schema validation for all envelopes** — Each envelope validated against JSON schema before acceptance.
5. **Evidence preservation** — All runtime artifacts copied to `.harness/evidence/v1_1_real_loop/` for audit traceability.
