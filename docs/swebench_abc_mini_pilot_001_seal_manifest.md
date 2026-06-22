# SWE-bench A/B/C Mini Pilot — Seal Manifest

> seal_name: swebench_abc_mini_pilot_001_final_seal
> base_version: v1.1
> stabilization_version: v1.1.1
> sealed_at: 2026-06-22 09:50 CST
> sealed_by: Hermes Agent
> branch: v1.1/hermes-local-env
> commit: (see below)

---

## Summary

| Field | Value |
|-------|-------|
| **task_id** | swebench_abc_mini_pilot_001 |
| **instances** | 5 |
| **tiers** | A (raw_agent), B (harness_governance), C (harness_real_loop) |
| **final_per_tier_outcome** | 12/15 (80%) |
| **evidence_rows** | 16 (results.csv) |
| **mock_used** | false (all tiers, all instances) |
| **blockers** | 0 |
| **mini_pilot_status** | sealed |
| **report_status** | sealed_after_v1_1_1_stabilization |

## Test Results (pre-seal)

| Suite | Tests | Result |
|-------|:-----:|:------:|
| Adapter tests | 19 | ✅ 19/19 passed |
| Framework routing tests | 14 | ✅ 14/14 passed |
| Full pytest | 153 | ✅ 153/153 passed |

## Key Artifacts

| Artifact | Path |
|----------|------|
| Final report | `docs/swebench_abc_mini_pilot_001_final_report.md` |
| Global report | `docs/swebench_abc_mini_pilot_001_report.md` |
| Results CSV | `.harness/evaluations/swebench_abc_mini_pilot_001/results.csv` |
| Evidence directory | `.harness/evaluations/swebench_abc_mini_pilot_001/` |
| Calibration summaries | 5 files (one per instance) |
| Tier runs | 15 runs across A/B/C for 5 instances |
| Evidence archive | `dist/swebench_abc_mini_pilot_001_final_evidence_f3aca38.tar.gz` |
| Evidence archive SHA256 | `de88b255287899286ba13c74479d92e500a14a42e749835c1516f77c26c4f6c1` |

## Accomplished in v1.1.1 Stabilization

1. **`swebench_docker_eval.py` framework routing**: Fixed hardcoded Sphinx path. Now dispatches by framework (django/Sphinx/unknown).
2. **AGENTS.md drift**: Restored correct v1.1 content (was overwritten by TypeScript project).
3. **Framework routing tests**: 14 new tests added.
4. **Full pytest**: Restored from 137/139 to 153/153.

## Decision Gate

| Field | Value |
|-------|-------|
| **decision_gate** | ready_for_next_phase |
| **recommended_next_phase** | v1.2 Engineering Copilot planning or limited AB50 after explicit decision |

## Git Tag

| Field | Value |
|-------|-------|
| **tag** | `v1.1.1-mini-pilot-sealed` |
| **base** | `v1.1-real-loop-sealed` (unchanged) |

## Verification

```text
git status: clean (all changes committed)
tag: v1.1.1-mini-pilot-sealed (lightweight, no force)
push: false
deploy: false
merge: false
```
