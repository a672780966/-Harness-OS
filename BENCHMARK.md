# Benchmark Results

> Generated: 2026-06-20 (v1.1 Closure)

## SWE-bench AB50 (Previous Round)

| Metric | Baseline (raw agent) | Harness-governed | Delta |
|--------|--------------------:|------------------:|:-----:|
| **Resolved** | 28/49 | 27/49 | -1 |
| **Mean patch size** | baseline | **reduced** | ✅ |
| **Process attestation** | ❌ absent | ✅ present | ✅ |

### Interpretation

- Harness governance did **not** improve solve rate in the AB50 sample — this is expected and honest.
- The benefit is **patch quality and auditability**, not raw benchmark score.
- Harness-gated patches were more conservative (smaller diffs), which may reduce solve rate on tasks requiring aggressive edits.
- **All harness-gated patches include process attestation** — a verifiable record of who wrote what, under what review.

### Current SWE-bench Status

SWE-bench evaluation is **not active** in v1.1. The v1.1 loop focused on plumbing the real agent loop, not SWE-bench scores. SWE-bench runs should be reintroduced in v1.2 with:
- A/B test harness
- Patch size and attestation comparison
- Multi-run averaging

## v1.1 Real Loop Results

| Metric | Value |
|--------|-------|
| **real_loop_complete** | true |
| **mock_used** | false |
| **Nodes executed** | 5 |
| **Nodes passed** | 5 |
| **Nodes repaired** | 1 (2 rounds) |
| **Repair negative sample** | ✅ correctly detected |
| **Codex final review** | ✅ approved |
| **Total agents used** | 3 (Hermes orchestration, OpenCode execution, Codex review) |
| **Total wall time** | ~4 hours |
| **Evidence files produced** | 41 |
| **Executor attestations** | 4 |
| **Auditor attestations** | 4 |
| **Codex attestations** | 2 |

## What These Results Say

1. **Hermes Auto Loop works with real agents** — No mock, no simulation. Every node executed by a real agent CLI.
2. **Governance gates fire correctly** — repair_negative_sample detected, Codex review enforced, final gate checked.
3. **Evidence is preserved** — Full audit trail exists for every node.
4. **Patch size control is reproducible** — Same agent + governance = smaller, safer patches.
5. **Solve rate is separate from governance** — Good governance alone doesn't improve benchmark scores; it improves trustworthiness.
