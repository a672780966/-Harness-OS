| Run directories | `.harness/evaluations/swebench_abc_mini_pilot_001/runs/` |

---

## 16. Review-Triggered Repair Loop — sphinx-doc__sphinx-7590

### Summary

sphinx-doc__sphinx-7590 exposed a gap: Docker targeted eval passed, but Codex final review found a blocking edge case (EOF sentinel `"EOF".isalpha()` infinite loop). The pipeline was extended and validated so final review rejection can trigger repair, re-eval, re-review, and final gate.

### Process Flow

```
Codex Reject (round 1)
  → Hermes reads review_envelope blocking_issues
  → Hermes generates repair_prompt_from_codex_review.md
  → OpenCode executes repair (adds `not self.eof` guards)
  → OpenCode produces patch_repair_round_1.diff → patch_final.diff
  → Docker scoped eval runs (CPP_SMOKE_PASSED, resolved_targeted: true)
  → Codex final review round 2 (approved: true, blocking_issues: [])
  → Final Gate check (passed: true)
  → StarMap writeback
  → Results.csv updated (row 15 appended)
```

### Key Artifacts

| Artifact | Path |
|----------|------|
| Repair prompt | `tier_C_review_repair_v1/repair_prompt_from_codex_review.md` |
| Repair output | `tier_C_review_repair_v1/plan/repair_raw_output_round_1.md` |
| Repaired patch | `tier_C_review_repair_v1/patch_final.diff` |
| Docker eval | `tier_C_review_repair_v1/eval_report.json` |
| Codex round 2 review | `tier_C_review_repair_v1/review_envelopes/final_review_envelope.json` |
| Final gate | `tier_C_review_repair_v1/result_envelopes/final_gate_envelope.json` |
| Metrics | `tier_C_review_repair_v1/metrics.json` |
| Old rejected run (preserved) | `tier_C_full/` |

### Results

| Metric | Value |
|--------|-------|
| Evaluated A/B/C tiers using same eval family | ✅ Yes (all targeted_cpp_domain) |
| mock_used (all tiers) | false |
| official_eval_blocked | true |
| resolved_targeted (Tier C repair) | true |
| codex_approved (round 2) | true |
| final_gate_passed | true |
| merge_ready | true |
| stop_reason | real_loop_complete_after_review_repair |

---

## 17. Final Section — Mini Pilot Complete

The SWE-bench A/B/C Mini Pilot is complete. See the full Final Report:

[swebench_abc_mini_pilot_001_final_report.md](swebench_abc_mini_pilot_001_final_report.md)**Summary**:
- 5/5 instances completed with A/B/C data
- 12/15 tier pass rate (80%)
- Tier C full real loop validated: repair loop, review-triggered repair, Final Gate, StarMap all functional
- Decision gate recommendation: v1.1.1_stabilization_before_ab50_or_v1_2

For detailed evidence: `calibration_*.md` files, `results.csv`, and `runs/` directory under
`.harness/evaluations/swebench_abc_mini_pilot_001/`.
