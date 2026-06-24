# Harness OS v1.1 — Release Manifest

> Generated: 2026-06-20 08:28 CST
> Tag: v1.1-real-loop-sealed
> Commit: f3aca38573aafe12e0bf66cfea5c4c014f93a0d5

## Closure Status

| Metric | Value |
|--------|-------|
| **real_loop_complete** | true |
| **mock_used** | false |
| **stop_reason** | real_loop_complete |
| **test_result** | 120/120 passed |
| **worktrees** | 10 → 2 (main + v1_1_upgrade) |
| **branch** | v1.1/hermes-local-env |

## Evidence Archive

| Field | Value |
|-------|-------|
| **Archive path** | `dist/harness_os_v1_1_real_loop_evidence_f3aca38.tar.gz` |
| **SHA256 path** | `dist/harness_os_v1_1_real_loop_evidence_f3aca38.sha256` |
| **SHA256 hash** | `e0cd7932b921ddc428b49d19fa86d7555ad1c60adbf027f4861ade812fec6d7f` |
| **Archive size** | 36 KB |
| **Files included** | 58 non-directory entries |

### Included Files

| Source | Description |
|--------|-------------|
| `.harness/evidence/v1_1_real_loop/` | 49 evidence files (envelopes, attestations, audits, results, nodes, git, starmap, final reviews) |
| `.harness/evidence/v1_1_real_loop/EVIDENCE_INDEX.md` | Full evidence index |
| `.harness/audit/logs/v1_1_release_seal_report.md` | Release seal report |
| `.harness/audit/logs/v1_1_closure_test_report.md` | Test report (110 tests) |
| `.harness/audit/logs/worktree_cleanup_executed.md` | Phase 1 worktree cleanup report |
| `.harness/audit/logs/worktree_cleanup_force_executed.md` | Phase 2 force cleanup report |
| `docs/v1_1_real_loop_report.md` | Full real loop closure report (10 chapters) |
| `docs/v1_1_architecture.md` | v1.1 architecture documentation |
| `BENCHMARK.md` | SWE-bench AB50 results + v1.1 loop results |
| `EVALUATION_PLAN.md` | A/B/C evaluation tiers + evidence requirements |
| `README.md` | Project README (updated with v1.1 section) |

### Excluded Files

| Source | Reason |
|--------|--------|
| `.harness/scripts/` | Gitignored — project design decision |
| `.harness/config/` | Gitignored — project design decision |
| `.harness/envelopes/schema/` | Gitignored — project design decision |
| `.harness/envelopes/templates/` | Gitignored — project design decision |
| `.harness/envelopes/result/` | Gitignored — runtime artifacts |
| `.harness/envelopes/review/` | Gitignored — runtime artifacts |
| `.harness/workers/` | Gitignored — runtime attestations |
| `.harness/starmap/` | Gitignored — runtime facts |
| `.agents/` | Runtime state (not tracked) |
| `.venv/` | Virtual environment (not tracked) |
| `tests/__pycache__/` | Compiled bytecode (not tracked) |
| `node_modules/` | Dependencies (not tracked) |

## Tag Verification

| Check | Result |
|-------|--------|
| **HEAD matches tag** | ✅ `f3aca38` = `v1.1-real-loop-sealed` |
| **Push** | ❌ false — not pushed to remote |
| **Deploy** | ❌ false — not deployed |

## Known Non-Blocking Followups

| Item | Status | Notes |
|------|--------|-------|
| GitHub每日榜单 06/20 error | 🟡 | Monitor next run (06/21 09:00) |
| v1_1_upgrade worktree | 🟢 | Can remove after evidence verified |
| test_hermes_auto_loop_final_review_handler.py now exists | ✅ | 10 tests, all passing |
| SWE-bench A/B/C planning | 📋 | Plan created at docs/swebench_abc_retest_plan.md |
