# Governance Recovery Report — Cross-Pipeline Consistency Audit

**Trace ID:** `c7210bbdf15c`
**Task ID:** `task-001`
**Generated:** 2026-06-24
**Worker:** OpenCode (DeepSeek v4 Flash)
**Profile:** temporary-loop/v1 — cloud_sandbox_dev
**Branch:** `feat/loop-installer-mvp`

---

## 1. Relationship to Prior Reports

This is the **third** governance recovery report for the Harness OS temp loop series.
It does not supersede prior reports. It audits what they did not cover.

| Dimension | Report 1 (390a7db51139) | Report 2 (514693628bc5) | Report 3 (c7210bbdf15c, this) |
|---|---|---|---|
| Scope | Hermes full pipeline (auto_loop, final_gate, audit, state, worktree) | Temp loop (`run.py`), config files, TypeScript governance | **Cross-pipeline consistency, drift measurement, repair verification, full-chain audit** |
| Blocking gaps | 4 (BG-1 to BG-4) | 4 (TBG-1 to TBG-4) | 5 (CPG-1 to CPG-5, see §4) |
| Non-blocking | 5 (NB-1 to NB-5) | 5 (TNB-1 to TNB-5) | 5 (CPN-1 to CPN-5, see §5) |
| Prior gaps closed | — | 0 / 4 BG gaps closed | **0 / 8 prior BG gaps closed** (see §3) |
| Test count | 88 passed | 873 passed | **873 passed** (confirmed same suite) |

**Key finding:** Zero of the 8 blocking gaps identified across reports 1 and 2 have been closed in code. The governance system has documentation of gaps but no remediation has occurred.

---

## 2. Audited Components

### 2.1 Governance Configuration Layer (`.harness/config/`)

All 18 YAML config files exist and are structurally valid:

| File | Path | Lines | Purpose |
|---|---|---|---|
| State Machine | `.harness/config/state_machine.yaml` | ~166 | 48 states, 8 hard rules |
| Final Merge Gate | `.harness/config/final_merge_gate.yaml` | ~60 | 8 hard blocks, 12 requirements, dry-run only |
| Review Rules | `.harness/config/review_rules.yaml` | ~70 | 9 blocking categories, 6 codex approval reqs |
| Policies | `.harness/config/policies.yaml` | ~50 | 7 hard rules, 5 soft rules |
| Open Code Review | `.harness/config/open_code_review.yaml` | ~30 | OCR adapter config, review-only mode |
| Permissions | `.harness/config/permissions.cloud_sandbox.yaml` | ~80 | Role-based permissions |
| Repair Loop | `.harness/config/repair_loop.yaml` | ~30 | Repair orchestration config |
| Codex Adv Review | `.harness/config/codex_advanced_review.yaml` | ~30 | Advanced review config |
| Agents | `.harness/config/agents.yaml` | ~30 | Agent definitions |
| Tools | `.harness/config/tools.yaml` | ~80 | Tool definitions incl OCR role |
| Real Tools | `.harness/config/real_tools.yaml` | ~20 | Real tool attestation paths |
| Real Tool Attest | `.harness/config/real_tool_attestation.yaml` | ~30 | Attestation config |
| Budgets | `.harness/config/budgets.yaml` | ~10 | Budget config |
| StarMap | `.harness/config/starmap.yaml` | ~10 | StarMap writeback config |
| Claude Worker | `.harness/config/claude_worker.yaml` | ~20 | Claude worker config |
| Hermes Config | `.harness/config/hermes.config.yaml` | ~134 | Pipeline stages, security, audit |
| Startup Tools | `.harness/config/startup_tools.yaml` | ~10 | Startup tool definitions |
| Review Sessions | `.harness/config/review_sessions.yaml` | ~10 | Review session config |

**Finding (CPN-1):** No cross-referencing exists to verify that YAML config rules are actually enforced by code. Example: `policies.yaml` declares `no_test_no_merge: block` but `task_state.json` shows tasks at `merge_ready` without evidence of a fresh test run at merge time.

### 2.2 Envelope Schema Compliance

Actual envelopes compared against their Draft 2020-12 schemas:

| Envelope Type | Schema | Actual Examined | Compliant? | Evidence |
|---|---|---|---|---|
| Task | `task_envelope.schema.json` (23 req) | `task_real_loop_001_interactive_round_1.json` | ✅ Yes | All 23 required fields present |
| Result | `result_envelope.schema.json` (14 req) | `task_worker_e2e_001_round_1.json` | ❌ No | See CPG-1 |
| Review | `review_envelope.schema.json` (8 req) | `task_worker_e2e_001_round_1_review.json` | ❌ No | See CPG-1 |
| Final Review | `final_review_envelope.schema.json` (10 req) | `task_real_loop_001_interactive_round_1_final_review.json` | ❌ No | See CPG-1 |
| Repair | `repair_envelope.schema.json` (10 req) | `task_repair_e2e_001_round_1_repair.json` | ❌ No | See CPG-1 |

**Finding (CPG-1):** Schema validation is defined but not enforced at envelope creation time. Hermes' `validate_envelope.py` is called but its failure is non-fatal — execution continues with a warning (`hermes_auto_loop.py:1257-1258`). This means non-compliant envelopes enter the pipeline.

### 2.3 State Machine Fidelity

The defined state machine (`state_machine.yaml`) declares 48 states with 8 hard rules. The actual `task_state.json` tracks 10 tasks across these states:

| task_id | status in task_state.json | Valid state machine state? | Evidence |
|---|---|---|---|
| task_connector_001 | startup_verify | ✅ Yes | Valid transition: pending→startup_verify |
| task_worker_001 | running | ✅ Yes | Valid transition chain |
| task_worker_e2e_001 | review_passed | ✅ Yes | Valid |
| task_worker_e2e_002 | review_passed | ✅ Yes | Valid |
| task_repair_e2e_001 | repair_requested | ✅ Yes | Valid |
| v1_1_real_task_001_starmap_writeback | pending | ✅ Yes | Valid |
| task_v1_1_real_001_starmap | pending | ✅ Yes | Valid |
| task_v1_1_real_002_intake_contract | review_passed | ✅ Yes | Valid |
| task_real_cli_smoke_001 | pending | ⚠️ Stale | See CPN-2 |
| task_real_loop_001_interactive | merge_ready | ⚠️ Unverified | See CPG-2 |

**Finding (CPG-2):** `task_real_loop_001_interactive` reached `merge_ready` status, but the audit trail shows the merge gate dry-run passed without a final `pytest` re-run. The state machine's hard rule `no_done_without_audit_event` is satisfied (events 115-125 in `events.jsonl`), but the gate's own `require_final_test_run` field in `final_merge_gate.yaml` was not cross-checked.

**Finding (CPN-2):** `task_real_cli_smoke_001` is stuck at `pending` status with two `tool_process_failed` events (events 100, 103 in `events.jsonl`) but was never moved to `failed`. The state machine has no timeout mechanism to detect stuck tasks.

### 2.4 Full-Chain Audit of `task_real_loop_001_interactive`

This task reached `merge_ready`, making it the most mature task in the system. Full audit trail from `events.jsonl`:

| Step | Event | Actor | Status |
|---|---|---|---|
| 1 | task_created (evt_354878510e84) | hermes | pending |
| 2 | task_entered_startup_verify (evt_47fb4cf8d608) | hermes | startup_verify |
| 3 | startup_verify_passed (evt_41d921019e9e) | hermes | permission_check_running |
| 4 | permission_preflight_passed (evt_20260619072903078067_fc6f) | hermes | permission_check_passed |
| 5 | permission_check_complete (evt_d7ae29d32487) | hermes | assigned |
| 6 | assigned_to_startup_gate (evt_386900094fbf) | hermes | startup_gate |
| 7 | startup_gate_passed (evt_50a2e244f0e3) | hermes | running |
| 8 | worktree_created (evt_2114ca33a866) | hermes | worktree_ready |
| 9 | dev_completed (evt_5d6111b907e2) | opencode_deepseek_worker | completed_for_review |
| 10 | open_code_review_prepared (evt_51cb9cb61edd) | hermes | review_running |
| 11 | open_code_review_started (evt_95cb5e3b587a) | open_code_review | review_running |
| 12 | open_code_review_review_passed (evt_ede51fb97e61) | open_code_review | review_passed |
| 13 | codex_review_started (evt_a1fcad5af1df) | codex_advanced_reviewer | codex_review_running |
| 14 | codex_advanced_review_completed (evt_6c25266d0432) | codex_advanced_reviewer | codex_approved |
| 15 | final_merge_gate_dry_run_completed (evt_c87f5c92fe91) | hermes | merge_ready |
| 16 | final_validation_started (evt_4120bc8564a9) | codex_advanced_reviewer | final_validation_running |
| 17 | final_validation_passed (evt_87f467169ac6) | codex_advanced_reviewer | final_passed |
| 18 | final_merge_gate_dry_run_completed (evt_b000009d8ce1) | hermes | merge_ready |

**Finding (CPG-3):** Despite reaching `merge_ready`, the chain has 3 issues:
- **No pytest run between review and merge gate**: Events 9-18 contain no `test_executed` event. The merge gate trusted a cached result.
- **Codex review was mock**: As identified in prior BG-1, the Codex advanced review in `hermes_final_gate.py` does not invoke actual Codex CLI — it makes autonomous approval decisions based on field checks.
- **No independent audit session**: The Open Code Review adapter ran in the same context as implementation (violating `CLAUDE.md` Fresh Audit Policy).

### 2.5 Connector System Audit

The `.harness/connector/` inbox/outbox/processed mechanism is present but:

| Component | Files | Status | Evidence |
|---|---|---|---|
| inbox/task/ | 9 files | ✅ Has unprocessed envelopes | Files present with payloads |
| inbox/result/ | 0 files | ✅ Empty (expected — results go to envelopes/result/) | Directory exists, empty |
| inbox/review/ | 0 files | ✅ Empty | Directory exists, empty |
| inbox/repair/ | 0 files | ✅ Empty | Directory exists, empty |
| inbox/final/ | 0 files | ✅ Empty | Directory exists, empty |
| outbox/repair/ | 0 files | ✅ Empty | Directory exists, empty |
| outbox/review/ | 0 files | ✅ Empty | Directory exists, empty |
| processed/task/ | 0 files | ✅ Empty | Directory exists, empty |
| processed/result/ | 0 files | ✅ Empty | Directory exists, empty |
| processed/review/ | 0 files | ✅ Empty | Directory exists, empty |
| processed/final/ | 0 files | ✅ Empty | Directory exists, empty |

**Finding (CPN-3):** The connector inbox for tasks has 9 unprocessed envelopes, while outbox and processed directories are empty. No evidence of outbound dispatch or processing completion was found. This suggests the connector is directory-based but no processing daemon or scheduler actually moves envelopes through the pipeline.

### 2.6 Safety Policy Enforcement Verification

`harness/loop/safety.py` defines `ALLOWED_ACTIONS` and `BLOCKED_ACTIONS` sets with `is_action_allowed()` and `check_git_status()` functions. However:

**Finding (CPG-4):** The safety policy is **advisory only** — `safety_report()` generates a human-readable report but does not enforce any restrictions. The function is called from `runner.py:37` and the report is written to disk, but no caller checks the return value to block execution. The `is_action_allowed()` function is never called from any dispatcher or runner. This means all safety policy violations are purely self-enforced by agent instructions.

### 2.7 Repair Loop Effectiveness

`task_repair_e2e_001` was the only repair task in the system. Its outcome:

| Dimension | Finding | Evidence |
|---|---|---|
| Initial result | test_failed | `events.jsonl:66` — claude_code_worker reported test_failed |
| Repair requested | Yes | `events.jsonl:67` — repair_needed, repair_requested |
| Repair envelope | Created | `events.jsonl:68` — repair_envelope_created |
| Codex review | codex_rejected | `events.jsonl:71` — codex_advanced_review_completed, codex_rejected |
| Merge gate | block | `events.jsonl:72` — final_merge_gate_dry_run_completed, still repair_requested |
| Resolution | **Stuck** | Task remains in repair_requested state with codex_rejected |

**Finding (CPG-5):** The repair loop has no mechanism to escalate a `codex_rejected` verdict — the task stays in `repair_requested` permanently. The state machine allows this state indefinitely with no timeout, human notification, or automatic escalation path.

### 2.8 Loop Runner Components (`harness/loop/`)

| Component | Path | Status | Evidence |
|---|---|---|---|
| Runner | `harness/loop/runner.py` | ✅ Implemented | 94 lines, 5 steps (safety, detect, inspect, readiness, summary) |
| Safety | `harness/loop/safety.py` | ⚠️ Advisory only | See CPG-4 — no enforcement |
| Envelope | `harness/loop/envelope.py` | ✅ Implemented | 112 lines, 3 envelope generators |
| Roles | `harness/loop/roles.py` | ✅ Defined | 12 role definitions |
| Topology | `harness/loop/topology.py` | ✅ Implemented | Topology suggestion based on detected agents |
| Discovery | `harness/loop/discovery.py` | ✅ Implemented | Agent detection |
| Config | `harness/loop/config.py` | ✅ Implemented | Loop setup config generation |
| Setup | `harness/loop/setup.py` | ✅ Implemented | Loop installation |
| Skills | `harness/loop/skills.py` | ✅ Implemented | Skill detection |
| Reports | `harness/loop/reports.py` | ✅ Implemented | Report generation |
| Instructions | `harness/loop/instructions.py` | ✅ Implemented | Instructions generation |

**Finding (CPN-4):** The `harness/loop/` Python package is well-structured (11 modules) but is NOT integrated with the Hermes pipeline (`hermes_auto_loop.py`) or the temp loop (`run.py`). It is a standalone loop installer that was never wired into the actual task execution flow. This means two separate loop implementations exist with no shared governance enforcement.

### 2.9 Audit Trail Integrity Cross-Check

Three audit event sources exist. Cross-checked for consistency:

| Source | Events | Trace c7210bbdf15c present? | Format |
|---|---|---|---|
| `.harness/audit/events.jsonl` | 168 events | ❌ No (hermes-audit format) | 11-field AuditEvent schema |
| `.harness/temp_loop/c7210bbdf15c/audit_events.jsonl` | 8 events | ✅ Yes | 5-field simplified format |
| `.harness/temp_loop/c7210bbdf15c/state_transitions.jsonl` | 4 events | ✅ Yes | 6-field state transition format |

**Finding (CPN-5):** The temp loop audit events (5 fields: `trace_id`, `event`, `actor`, `reason`, `evidence_ref`, `created_at`) do not match the formal 11-field AuditEvent schema (needs `event_id`, `span_id`, `event_type`, `from_status`, `to_status`, `sensitivity`, `redaction_level`). This means temp loop audits cannot be ingested into the main audit pipeline.

---

## 3. Prior Gap Closure Status

| Prior Gap | Report | Status | Evidence |
|---|---|---|---|
| BG-1: Mock Codex final review | Report 1 | ❌ NOT FIXED | `hermes_final_gate.py` still uses mock `codex_advanced_review()` |
| BG-2: Auto loop results always pass | Report 1 | ❌ NOT FIXED | `hermes_auto_loop.py` still hardcodes `test_result.passed = True` |
| BG-3: Self-audit in auto loop | Report 1 | ❌ NOT FIXED | No independent audit session enforcement added |
| BG-4: No forced test re-run at merge gate | Report 1 | ❌ NOT FIXED | `final_merge_gate_dry_run` still trusts cached result |
| TBG-1: Self-review in temp loop | Report 2 | ❌ NOT FIXED | `run.py:482-568` still inline, no fresh session |
| TBG-2: Temp loop trace_id schema violation | Report 2 | ❌ NOT FIXED | `run.py:16` still uses bare hex |
| TBG-3: Open Code Review bypass | Report 2 | ❌ NOT FIXED | `run.py` still skips OCR |
| TBG-4: No review envelope in temp loop | Report 2 | ❌ NOT FIXED | Temp loop still produces raw JSON |

**Verdict: 0 / 8 prior blocking gaps closed. All 8 remain open and unaddressed.**

---

## 4. Blocking Governance Gaps

| # | Gap | Severity | Invariant Violated | Evidence |
|---|---|---|---|---|
| CPG-1 | **Non-fatal envelope validation**: Hermes `validate_envelope()` failure is logged as warning, not a blocking error — non-compliant envelopes enter the pipeline silently | BLOCKING | Invariant 5 (envelope-based handoff) | `hermes_auto_loop.py:1257-1258` — `logger.warning` instead of `raise` or `sys.exit` |
| CPG-2 | **merge_ready without fresh test re-run**: `task_real_loop_001_interactive` reached merge_ready with no `pytest` event between last edit and merge gate | BLOCKING | Invariant 1 (no test, no done) | `events.jsonl:114-125` — no `test_executed` or `test_passed` event in the review→merge gate chain |
| CPG-3 | **Codex review is a mock**: The codex_advanced_reviewer `codex_advanced_review_completed` event comes from `hermes_final_gate.py` which does autonomous approval without actual Codex CLI | BLOCKING | Invariant 3 (no Codex approval, no merge_ready) | `hermes_final_gate.py:107-198` — blocking issues determined by field checks, not LLM review |
| CPG-4 | **Safety policy is advisory-only**: `safety.py`'s `is_action_allowed()` is never called by any dispatcher, runner, or gate — all safety enforcement is self-enforced by agent instructions | BLOCKING | Invariant 7 (no direct main modification) | `runner.py:37` calls `safety_report()` but discards output; `is_action_allowed()` has zero callers |
| CPG-5 | **Repair loop has no escalation path**: `task_repair_e2e_001` received `codex_rejected` and remains stuck in `repair_requested` with no timeout, notification, or auto-escalation mechanism | BLOCKING | Invariant 6 (audit trail) | `events.jsonl:71-72` — codex_rejected, no further transitions |

---

## 5. Non-Blocking Risks

| # | Risk | Severity | Details |
|---|---|---|---|
| CPN-1 | **Config-to-code enforcement gap**: 18 YAML config files define rules but no mechanism verifies code actually enforces them | Medium | Example: `policies.yaml` has `no_test_no_merge: block` but no cross-reference to `final_merge_gate.yaml` enforcement |
| CPN-2 | **Stuck task not detected**: `task_real_cli_smoke_001` stalled at `pending` since 2026-06-19 with 2 `tool_process_failed` events but never moved to `failed` | Medium | `task_state.json` — task has `status: pending` since `2026-06-19T13:51:12` |
| CPN-3 | **Connector inbox orphanage**: 9 unprocessed envelopes in inbox/task/, 0 files in outbox/ or processed/ — no evidence of processing pipeline | Medium | `.harness/connector/inbox/task/` — 9 files, no corresponding outbox/processed entries |
| CPN-4 | **Dual loop implementations**: `harness/loop/` (Python installer package) and `hermes_auto_loop.py` (Hermes pipeline) are independent — no shared governance enforcement | Low | `hermes_auto_loop.py` does not import from `harness/loop/` |
| CPN-5 | **Temp loop audit schema mismatch**: 5-field temp loop audit format vs 11-field formal AuditEvent schema — temp loop audits cannot be ingested into main pipeline | Medium | `run.py:69-80` — simplified audit_event() vs `audit_event.schema.json` — 11 required fields |

---

## 6. Prior Recommendations Restated (Unresolved)

The following recovery actions from Reports 1 and 2 remain unaddressed and are restated here:

| Order | Action | Original Reference | Priority |
|---|---|---|---|
| 1 | Fix BG-2: Replace hardcoded `test_result.passed = True` with actual pytest execution | Report 1 §6 | P0 |
| 2 | Fix BG-1/BG-3: Wire Codex CLI for actual LLM-based review instead of mock | Report 1 §6 | P0 |
| 3 | Fix BG-4: Add pytest re-run inside merge gate before trusting cached results | Report 1 §6 | P0 |
| 4 | Fix BG-3/TBG-1: Add independent fresh audit session enforcement | Reports 1+2 §6 | P0 |
| 5 | Fix TBG-2: Align temp loop trace_id to schema pattern | Report 2 §7 | P0 |
| 6 | Fix TBG-3: Add OCR phase between implementation and Codex review in temp loop | Report 2 §7 | P0 |
| 7 | Fix TBG-4: Generate schema-validated review envelope in temp loop | Report 2 §7 | P0 |

---

## 7. New Recommended Recovery Sequence

| Order | Action | Target | Priority |
|---|---|---|---|
| 1 | **Fix CPG-4**: Wire `safety.py:is_action_allowed()` into actual dispatch and runner code — make safety enforcement mechanical, not advisory | `harness/loop/safety.py`, `runner.py`, `hermes_auto_loop.py` | P0 |
| 2 | **Fix CPG-1**: Make envelope validation failure fatal — replace `logger.warning` with exception or non-zero exit | `hermes_auto_loop.py:1257-1258`, `validate_envelope.py` | P0 |
| 3 | **Fix CPG-2**: Enforce `pytest` re-run as a required step in the merge gate before `merge_ready` transition | `hermes_final_gate.py:226-228` | P0 |
| 4 | **Fix CPG-5**: Add escalation path for `codex_rejected` — human notification, timeout, or automatic retry with reduced scope | `hermes_auto_loop.py`, `state_machine.yaml` | P0 |
| 5 | **Fix CPG-3**: Replace mock `codex_advanced_review()` with actual Codex CLI invocation | `hermes_final_gate.py:107-198` | P0 |
| 6 | **Fix CPN-3**: Add connector processing daemon or cron job to move inbox→outbox→processed | `.harness/connector/` or `hermes_connector.py` | P1 |
| 7 | **Fix CPN-5**: Align temp loop audit format to formal AuditEvent schema | `run.py:69-80` | P1 |
| 8 | **Fix CPN-1**: Add config-to-code compliance verification test | `tests/` | P2 |
| 9 | **Fix CPN-2**: Add state machine timeout for stuck tasks — auto-transition `pending`→`failed` after 24h with no updates | `hermes_state.py` | P2 |
| 10 | **Fix CPN-4**: Consolidate dual loop implementations or add shared governance dependency | `harness/loop/` + `hermes_auto_loop.py` | P3 |

---

## 8. Test Results Status

**Command run:** `python -m pytest tests/ -x -q --no-header`
**Overall status:** 873 passed, 0 failed
**Duration:** 29.92s

| Metric | Value |
|---|---|
| Total tests | 873 |
| Passed | 873 |
| Failed | 0 |
| Prior report test count | 873 (confirmed identical) |

**Key finding:** 873 tests pass, but zero tests exist for:
- `harness/loop/` Python package (runner, safety, envelope, etc.)
- Temp loop `run.py`
- Connector inbox/outbox processing
- Config-to-code compliance verification

---

## 9. Files Changed

- `docs/governance_recovery_report_c7210bbdf15c.md` — **NEW** — This report

---

## 10. Known Risks

1. **Documentation only**: No code, config, schemas, or tests were modified. All 5 new blocking gaps (CPG-1 to CPG-5) and all 8 prior blocking gaps remain open.
2. **Non-fatal envelope validation** (CPG-1) means non-compliant envelopes may enter the pipeline silently — this undermines the entire envelope-based handoff design.
3. **Advisory-only safety policy** (CPG-4) means all safety enforcement relies on agent instruction compliance — there is no mechanical enforcement of blocked actions.
4. **Stuck repair loop** (CPG-5) has no auto-escalation — a `codex_rejected` verdict is a dead end with no process to unblock it.
5. **merge_ready without test re-run** (CPG-2) means the most mature task in the system reached its final state without satisfying Invariant 1 ("no test, no done").
6. **873 tests pass but coverage does not include the governance enforcement code** — the tests validate individual components but not the end-to-end governance pipeline.
