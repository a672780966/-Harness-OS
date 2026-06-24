# SWE-bench A/B/C Retest Plan

> Generated: 2026-06-20
> Phase: v1.1 Post-Closure Planning

## Objective

Verify whether **governance discipline** (envelopes, gates, audits, final review) improves **consistency, auditability, and stability** — not necessarily solve rate — in AI coding agent benchmark performance.

**Not claiming:** v1.1 improves SWE-bench solve rate.
**Historical baseline:** baseline 28/49, harness 27/49, patch size reduced (from prior AB50 run).

## Evaluation Tiers

### Tier A — Raw Agent (baseline)

| Field | Value |
|-------|-------|
| **Name** | Raw Agent |
| **Agent** | OpenCode (DeepSeek) or Codex CLI |
| **Model** | opencode-go/deepseek-v4-flash |
| **Governance** | None |
| **Envelopes** | None |
| **Gates** | None |
| **Audit** | None |
| **Final Review** | None |

**Metrics to collect:**
- resolved_count (per SWE-bench instance)
- patch_size (lines added/removed)
- test_pass_rate
- time_to_completion
- human_intervention_count
- mock_used (should be false)

### Tier B — Agent + Harness Governance

| Field | Value |
|-------|-------|
| **Name** | Agent + Governance |
| **Agent** | Hermes Auto Loop Runner |
| **Executor** | OpenCode (DeepSeek) |
| **Governance** | ✅ Permission preflight + result envelope + review envelope |
| **Audit** | ✅ OpenCode Fresh Auditor |
| **Repair Loop** | ✅ Up to 3 rounds |
| **Final Review** | ✅ Codex CLI |
| **Final Gate** | ✅ Hermes final gate |
| **StarMap** | ✅ Fact writeback |

**Additional metrics:**
- repair_rounds (per node)
- audit_failures_detected
- evidence_completeness (envelope validity)
- gate_rejection_rate
- process_attestation_count

### Tier C — Agent + Harness Real Loop (v1.1)

| Field | Value |
|-------|-------|
| **Name** | Agent + Real Loop |
| **Agent** | Hermes Auto Loop Runner |
| **Planner** | Codex Graph Planner (human-supervised) |
| **Executor** | OpenCode (DeepSeek) |
| **Repair** | ✅ repair_negative_sample detection |
| **Final Review** | ✅ Codex CLI (gpt-5.5) |
| **Final Gate** | ✅ Dry run |
| **StarMap** | ✅ Writeback |

**Additional metrics:**
- loop_completion_rate
- Codex_final_review_approval_rate
- StarMap_facts_written
- full_loop_time
- mock_used (must be false)

## Metric Definitions

| Metric | Description |
|--------|-------------|
| **resolved_count** | Number of SWE-bench instances where tests pass after patch |
| **patch_size** | `git diff --stat` total lines added + removed |
| **test_pass_rate** | % of task tests passing after patch |
| **repair_rounds** | Number of repair iterations per node |
| **audit_failures_detected** | Number of audit failures correctly identified |
| **time_to_completion** | Wall clock time from task start to resolution |
| **mock_used** | Whether any agent execution was simulated/mocked |
| **human_intervention_count** | Number of manual overrides or approvals |
| **evidence_completeness** | % of required evidence artifacts present (envelopes, attestations) |
| **gate_rejection_rate** | % of gates that blocked a defective result |
| **Codex approval_rate** | % of final reviews that passed |
| **loop_completion_rate** | % of full 5-node loops that completed |

## Test Setup

### Workload

SWE-bench instances subset (AB50 or smaller):
- 10 easy instances
- 10 medium instances
- 10 hard instances

### Environment

- Cloud VM sandbox (current)
- No external network to SWE-bench verified
- OpenCode CLI for execution
- Codex CLI for final review

### Repository

Separate SWE-bench fork or local clone.
Not modifying the harness-os repository for SWE-bench.
Each tier runs on the same set of instances.

## Execution Protocol

1. **Tier A** — Run OpenCode directly on each instance. Capture: output, patch, test results.
2. **Tier B** — Run Hermes Auto Loop with governance enabled. Collect all envelopes + attestations.
3. **Tier C** — Run full Hermes Auto Loop with all 5 nodes (if applicable) or 3-node subset (execute → audit → final review).

## Output Requirements

Each tier produces:
- `results/` — per-instance result (pass/fail, patch, test output)
- `envelopes/` — result + review envelopes (Tier B/C)
- `attestations/` — executor + auditor attestations (Tier B/C)
- `metrics.json` — aggregated metrics

## Comparison Matrix

| Metric | Tier A | Tier B | Tier C |
|--------|:------:|:------:|:------:|
| resolved_count | ✅ | ✅ | ✅ |
| patch_size | ✅ | ✅ | ✅ |
| test_pass_rate | ✅ | ✅ | ✅ |
| repair_rounds | ❌ N/A | ✅ | ✅ |
| audit_failures | ❌ N/A | ✅ | ✅ |
| mock_used | ✅ | ✅ | ✅ |
| evidence_completeness | ❌ N/A | ✅ | ✅ |
| gate_rejection_rate | ❌ N/A | ✅ | ✅ |
| Codex approval_rate | ❌ N/A | ✅ | ✅ |
| loop_completion | ❌ N/A | ❌ N/A | ✅ |

## Next Steps (Mini Pilot)

1. **Select 5 instances** (2 easy, 2 medium, 1 hard) for mini pilot
2. **Run Tier A** on all 5
3. **Run Tier B** on all 5
4. **Run Tier C** on all 5
5. **Compare** metrics across tiers
6. **Decide** whether full AB50 run is justified

## Known Limitations

- v1.1 did not run SWE-bench — loop was tested on Harness OS codebase only
- Baseline results (28/49, 27/49) are from a prior round with different agent config
- SWE-bench verified requires specific environment that is not fully set up
- Agent consistency varies across runs — single-run results have high variance
