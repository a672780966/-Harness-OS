# Governance Recovery — Verdict Matrix

**Generated**: 2026-06-25T06:30 CST

## Verdict Matrix

| # | Phase | Trace ID | Verdict | OpenCode Payload | 3 Rounds | Emergency | Final Gate | Hermes Direct | Full Tests |
|:-:|:------|:--------:|:-------:|:----------------:|:--------:|:---------:|:----------:|:--------------:|:----------:|
| 1 | v1.2 source-fix (COP-1~COP-5) | `8487477ea2c2` | ✅ `DONE_WITH_USER_APPROVED_SCOPE_EXTENSION` | Empty × 4 | ✅ Exhausted | ✅ 1× Codex (source) | BLOCKED→User Approved | 0 | ✅ 933/1 |
| 2 | v1.2.1 Dogfood audit | `b969a673ca1b` | ✅ `DONE` | Empty R1, Done R2 | ✅ Completed R2 | ❌ None | DONE | 0 | ✅ 933/1 |
| 3 | v1.3 Foundation Config | `ab7a02e015d0` | ✅ `DONE` | Empty × 2, Done R3 | ✅ Completed R3 | ✅ 1× Codex (docs) | DONE | 0 | ✅ 933/1 |
| 4 | v1.3.1 PR Draft Asst | `fa2ace05d055` | ✅ `DONE` | Empty × 4 | ✅ Exhausted | ✅ 1× Codex (docs) | DONE | 0 | ✅ 933/1 |
| 5 | Loop Installer self-audit | `cfad57b8d83c` | ✅ `DONE` | Empty × 2, Done R1 | ✅ Completed R1 | ✅ 1× Codex (docs) | DONE | 0 | ✅ 933/1 |
| 6 | Global Consistency | `dd6c8e13dfa4` | ✅ `DONE` | Empty × 4 | ✅ Exhausted | ✅ 1× Codex (docs) | DONE | 0 | ✅ 933/1 |

## Actor Distribution

```
OpenCode initial (workers):   6 calls  → 1 success → 16.7%
OpenCode repair (workers):   12 calls  → 3 success → 25%
OpenCode reviewer:            6 calls  → 0 success → 0%
Codex reviewer:              18 calls  → 0 success → 0% (all → REPAIR)
Codex emergency:              5 phases → 5 success → 100%
Codex final gate:             6 gates  → 6 success → 100%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total actor calls:           53
Hermes direct source mod:     0
```

## Phase state transitions (concatenated)

```
6 phases × typical flow:
  created
  → codex_planning
  → task_envelope_ready
  → dispatched_to_opencode
  → codex_reviewing (initial)
  → repair_required
  → opencode_repair_round_[1-3]
  → codex_reviewing_round_[1-3]
  → (3 rounds exhausted →) codex_emergency_implementation
  → codex_final_gate
  → final_evidence_ready
```

Exceptions:
- `b969a673ca1b`: OpenCode success at round 2 → no emergency
- `8487477ea2c2`: Codex Final Gate `BLOCKED_REQUIRES_USER_APPROVAL` → user approved
