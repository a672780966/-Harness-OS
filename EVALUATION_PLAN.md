# Evaluation Plan

> Updated: 2026-06-20 (v1.1 Closure)

## A/B/C Evaluation Tiers

### Tier A — Raw Agent (baseline)

**Agent**: OpenCode (DeepSeek) or Claude Code, unrestricted

**What to measure**:
- Solve rate (SWE-bench, custom tasks)
- Patch size (lines added/removed)
- Time to completion
- Error rate

**Evidence requirements**:
- Task result output only
- No process attestation required

### Tier B — Agent + Harness Governance

**Setup**: Add Hermes governance layer (envelopes, type dispatch, repair loop, audit, gates)

**What to measure**:
- Solve rate vs Tier A
- Patch size vs Tier A
- Process attestation presence
- Number of repair rounds
- Gate rejection rate

**Evidence requirements**:
- `result_envelope.json` — schema validated
- `review_envelope.json` — schema validated
- `executor_attestation.json` — signed
- `auditor_attestation.json` — signed

### Tier C — Agent + Harness + Real Loop (v1.1+)

**Setup**: Full Hermes Auto Loop with real agent execution, final review, merge gate, StarMap

**What to measure**:
- Full loop completion rate
- Number of repair rounds per node
- Codex final review approval rate
- StarMap writeback integrity
- Evidence coverage

**Evidence requirements**:
- All Tier B evidence +
- `final_review_envelope.json` — Codex-approved
- `gate_result_envelope.json` — merge-ready
- `loop_report.md` — structured loop summary
- `starmap/facts.jsonl` — final decision fact
- `codex_attestation.json` — signed final review

## Evidence Requirements (All Tiers)

| Evidence Artifact | Tier A | Tier B | Tier C | Schema |
|------------------|:------:|:------:|:------:|--------|
| Task output/log | ✅ | ✅ | ✅ | — |
| `result_envelope.json` | ❌ | ✅ | ✅ | `.harness/envelopes/schema/result_envelope.schema.json` |
| `review_envelope.json` | ❌ | ✅ | ✅ | `.harness/envelopes/schema/review_envelope.schema.json` |
| `executor_attestation.json` | ❌ | ✅ | ✅ | `.harness/workers/` |
| `auditor_attestation.json` | ❌ | ✅ | ✅ | `.harness/workers/` |
| `final_review_envelope.json` | ❌ | ❌ | ✅ | `.harness/envelopes/schema/final_review_envelope.schema.json` |
| `gate_result_envelope.json` | ❌ | ❌ | ✅ | `.harness/envelopes/schema/` |
| `loop_report.md` | ❌ | ❌ | ✅ | Structured markdown |
| `starmap/facts.jsonl` | ❌ | ❌ | ✅ | JSONL format |
| `codex_attestation.json` | ❌ | ❌ | ✅ | `.harness/workers/codex/` |

## Test Suites

| Test Suite | File | What It Validates |
|-----------|------|-------------------|
| Auto Loop | `tests/test_hermes_auto_loop.py` | Execution dispatch, node indexing, loop state |
| Negative Sample | `tests/test_hermes_auto_loop_negative_sample.py` | repair_negative_sample type detection and audit |
| Final Review Handler | `tests/test_hermes_auto_loop_final_review_handler.py` *(pending)* | Codex final review dispatch and result parsing |
| StartUp Gate | `tests/test_hermes_startup_gate.py` | Boot verification |
| State Machine | `tests/test_hermes_state_audit.py` | State transitions |
| Worktree | `tests/test_hermes_worktree.py` | Worktree lifecycle |
| Task Envelope | `tests/test_task_envelope_intake_contract.py` | Schema validation |
| Claude Worker | `tests/test_claude_worker_adapter.py` | Worker adapter |
| Fresh Audit | `tests/test_claude_fresh_audit.py` | Fresh audit flow |
| External Tools | `tests/test_external_tools_baseline.py` | Tool integration base |
| Final Gate | `tests/test_final_gate.py` | Merge gate dry run |
| StarMap | `tests/test_starmap_writeback.py` | StarMap persistence |
| Permission Preflight | `tests/test_permission_preflight.py` | Permission checks |

## Evaluation Schedule (Proposed)

| Phase | What | When |
|-------|------|------|
| v1.1 Closure | Evidence pack, docs, cleanup | ✅ Complete |
| v1.2 Tier B/C convergence | Run Tier B+C evaluations on benchmark suite | Next iteration |
| v1.2 SWE-bench A/B | Re-run AB50 with harness vs raw | Next iteration |
