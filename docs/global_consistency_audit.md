# Global Governance Recovery Consistency Audit

**Trace ID:** `dd6c8e13dfa4`
**Task ID:** `task-001`
**Generated:** 2026-06-25
**Branch:** `recovery/v1.2-source-fix-clean`
**Change type:** docs-only global consistency audit

## Decision

**needs_repair**

The governance recovery record is internally consistent on the main conclusion: the temporary loop and related recovery work are not yet canonical Harness OS governance. Several local product and runtime gaps were fixed or partially fixed across v1.2, v1.2.1, v1.3, and v1.3.1, but the core governance blockers remain open: canonical state-machine integration, canonical audit events, canonical envelopes and fatal validation, startup/permission gates, actual review-gate invocation, merge-gate fresh-test enforcement, and mechanical safety enforcement.

The temporary loop may continue only as a documented, non-merge-capable recovery tool. It must not be treated as canonical Harness OS governance until the unresolved global blockers below are closed with source changes, tests, audit events, and review evidence.

## Evidence Sources Read

| Required source | Path | Primary findings used |
|---|---|---|
| v1.1 governance audit | `docs/v1_1_governance_audit_report.md` | CDG-1 through CDG-10; temp loop is a parallel governance system |
| v1.2 governance audit | `docs/v1_2_engineering_copilot_governance_audit.md` | COP-1 through COP-19; copilot/provider guard gaps and follow-ups |
| v1.2 source-fix plan | `docs/v1_2_engineering_copilot_source_fix_plan.md` | Implementation specs for COP-1 through COP-5 workstreams |
| v1.2.1 dogfood audit | `docs/v1_2_1_dogfood_audit_report.md` | Later branch audit claiming COP-5 fixed and CDG gaps still unresolved |
| v1.2.1 dogfood stabilization audit | `docs/v1_2_1_dogfood_stabilization_audit.md` | Earlier audit claiming COP-5 partial and one provider-guard test failure |
| v1.3 foundation runtime audit | `docs/v1_3_foundation_runtime_audit.md` | Secure defaults, provider degraded flag wiring, docs drift, workspace hygiene |
| v1.3.1 PR draft assistant audit | `docs/v1_3_1_pr_draft_assistant_audit.md` | PR draft local artifact governance; no blocking issue in audited scope |
| Loop Installer self-audit | `docs/loop_installer_self_audit.md` | LI-1 through LI-5; `.harness/temp_loop/run.py` still non-canonical |
| Governance recovery report | `docs/governance_recovery_report_c7210bbdf15c.md` | BG-1 through BG-4, TBG-1 through TBG-4, CPG-1 through CPG-5 |

## Phase Matrix

| Phase | Source report | Blocking IDs | Consistency verdict | Current classification |
|---|---|---|---|---|
| v1.1 | `v1_1_governance_audit_report.md` | CDG-1, CDG-2, CDG-3, CDG-4, CDG-5; CDG-6 and CDG-7 medium governance gaps | Consistent with later reports: temp loop bypasses sealed Harness OS state, audit, envelope, startup, permission, review, and final-gate machinery | Unresolved, except CDG-4 partially mitigated by later envelope validator existence |
| v1.2 | `v1_2_engineering_copilot_governance_audit.md` | COP-1, COP-2, COP-3, COP-4, COP-15; COP-5 and COP-13 important follow-ups | Baseline audit correctly separated docs-only COP-15 fix from source/config follow-ups | Mostly fixed by later source-fix work; non-blocking COP items remain accepted follow-up |
| v1.2 source-fix | `v1_2_engineering_copilot_source_fix_plan.md` | COP-1 through COP-5 implementation workstreams | Plan is a specification, not closure evidence; later audits must be used for status | Planned in this artifact; closure depends on v1.2.1 evidence |
| v1.2.1 | `v1_2_1_dogfood_audit_report.md` and `v1_2_1_dogfood_stabilization_audit.md` | B-1 through B-4 in later dogfood audit; earlier B-1 through B-3 in stabilization audit | Reports conflict on COP-5 and provider-guard status; reconciliation below | COP-1 through COP-4 fixed; COP-5 fixed by later report but not fully regression-protected; CDG remains unresolved |
| v1.3 | `v1_3_foundation_runtime_audit.md` | No global governance closure; high-severity docs drift in install/config docs | Secure defaults and provider degraded guard are tested; docs/install claims drift from code | Foundation runtime mostly fixed for local config scope; docs drift planned |
| v1.3.1 | `v1_3_1_pr_draft_assistant_audit.md` | None for audited scope | Consistent: PR draft assistant is a local utility, not a Harness envelope/audit authority | Accepted with non-blocking follow-ups |
| Loop Installer | `loop_installer_self_audit.md` | LI-1, LI-2, LI-3, LI-4, LI-5 | Consistent with CDG/TBG/CPG: temporary runner remains non-canonical | Unresolved global blocker set |
| Cross-pipeline recovery | `governance_recovery_report_c7210bbdf15c.md` | BG-1 through BG-4, TBG-1 through TBG-4, CPG-1 through CPG-5 | Consistent with later Loop Installer self-audit and v1.1 CDG findings | Unresolved unless explicitly listed as partial below |

## Blocking Gap Classification

| ID | Gap summary | Classification | Evidence reference | Closure evidence required |
|---|---|---|---|---|
| CDG-1 | Temp loop state machine bypass | Unresolved | v1.1 audit maps temp states to isolated JSONL; Loop Installer LI-1 confirms current runner still bypasses canonical states | Source change using `.harness/config/state_machine.yaml`/Hermes state APIs plus transition tests and audit events |
| CDG-2 | Startup gate and permission preflight bypass | Unresolved | v1.1 audit CDG-2; Loop Installer LI-4 confirms no startup/permission preflight and full-access Codex dispatch | Startup and permission preflight enforced before dispatch, with failing tests for bypass attempts |
| CDG-3 | Audit trail divergence | Unresolved | v1.1 audit CDG-3; Loop Installer LI-2 confirms temp audit JSONL does not match schema | Canonical AuditEvent records in `.harness/audit/events.jsonl`, schema validation, and ingestion test |
| CDG-4 | Envelope schema misalignment | Partially fixed | v1.2.1 later dogfood says `envelope_validator.py` exists, but temp loop still emits `temporary-loop/v2`; Loop Installer LI-3 confirms divergence | Fatal validation at envelope creation/transition and canonical envelope output |
| CDG-5 | Orchestration role duplication | Unresolved | v1.1 audit CDG-5; Loop Installer confirms temp runner remains separate and writes reports | One canonical orchestrator or explicit non-canonical isolation with merge-capable path blocked |
| CDG-6 | Review envelope structure gap | Unresolved | v1.1 audit CDG-6; Loop Installer review response is not canonical `review_envelope` | Open Code Review adapter output with schema-valid review envelope |
| CDG-7 | Final gate validation gap | Unresolved | v1.1 audit CDG-7; CPG-2 and CPG-3 identify merge-gate/test/review deficiencies | Real Codex final gate evidence, fresh tests, final acceptance envelope, audit trail |
| CDG-8 | Declarative high-risk path enforcement | Unresolved | v1.1 audit CDG-8; CPG-4 safety policy advisory-only | Mechanical safety enforcement before dispatch and write operations |
| CDG-9 | Trace/task naming convention violation | Unresolved | v1.1 audit CDG-9; Loop Installer audit notes raw hex trace and temp protocol | Schema-valid `trace_`/`task_` identifiers or documented temporary schema blocked from canonical path |
| CDG-10 | Emergency reviewer cross-check pattern | Accepted follow-up | v1.1 audit marks positive; Loop Installer says preserve only as break-glass | Port cross-check to canonical emergency path after core gates are fixed |
| COP-1 | CLI docstring missing command catalog | Fixed | Later v1.2.1 dogfood audit cites `tests/copilot/test_cli_documentation.py` and CLI docstring rewrite | Keep argparse-introspection test as future hardening |
| COP-2 | Blanket read-only CLI claim | Fixed | Later v1.2.1 dogfood audit says write/network exceptions are documented | Regression test for governance categories |
| COP-3 | Provider guard config consolidation | Fixed | Later v1.2.1 dogfood audit and v1.3 foundation audit cite schema/loader/resolver/provider guard wiring | Existing provider config tests stay passing |
| COP-4 | `long_phase_allowed_when_degraded` not wired | Fixed | Later v1.2.1 dogfood and v1.3 foundation audits cite health/canary/config tests | Existing degraded long-phase tests stay passing |
| COP-5 | Retry config not exposed in HarnessConfig | Fixed, weakly tested | Later v1.2.1 dogfood audit says fixed; earlier stabilization audit said partial; v1.3 provider default tests cover fields but merge semantics for retry fields had been identified as under-tested | Add explicit retry field merge-precedence tests and `config show`/provider-status evidence |
| COP-7 | `pr-draft --create` governance note | Fixed | Later v1.2.1 and v1.3.1 audits cite CLI docstring and PR draft behavior | Keep PR draft tests passing |
| COP-10 | AgentStateTimeline in live dashboard | Accepted follow-up | v1.2/v1.2.1 audits mark low priority not done | Product enhancement task, not canonical governance blocker |
| COP-11 | argparse epilog completeness | Accepted follow-up | v1.2/v1.2.1 audits mark low priority not done | CLI docs polish task |
| COP-13 | Degraded long-phase check in canary | Fixed | Later v1.2.1 and v1.3 audits cite `check_before_long_phase` tests | Existing provider guard tests |
| COP-14 | Credential storage audit check | Accepted follow-up | v1.2/v1.2.1 mark not done; v1.3 verifies secure default and validator warnings | Optional runtime hardening beyond current blocking set |
| COP-16 | monitor governance block | Accepted follow-up | v1.2/v1.2.1 mark not done, low priority | Documentation/source comment task |
| COP-18 | provider health file path fix | Accepted follow-up | v1.2/v1.2.1 mark not done, low priority | Source cleanup task |
| COP-19 | shell governance block | Accepted follow-up | v1.2/v1.2.1 mark not done, low priority | Documentation/source comment task |
| BG-1 | Mock Codex final review | Unresolved | governance recovery report says `hermes_final_gate.py` still uses mock review; maps to CPG-3 | Actual Codex CLI invocation and review envelope/audit evidence |
| BG-2 | Auto loop results always pass | Unresolved | governance recovery report says hardcoded `test_result.passed = True` remains | Real test execution captured in result envelope |
| BG-3 | Self-audit in auto loop | Unresolved | governance recovery report says no independent audit session enforcement | Fresh review session enforcement and evidence |
| BG-4 | No forced test re-run at merge gate | Unresolved | governance recovery report CPG-2 confirms merge_ready without fresh pytest | Merge gate must execute or verify fresh tests after latest diff |
| TBG-1 | Temp-loop self-review/compliance gaps | Unresolved | governance recovery report plus Loop Installer LI findings | Canonical independent review path and schema-valid review artifacts |
| TBG-2 | Temp-loop trace_id schema violation | Unresolved | governance recovery report and CDG-9 | Schema-valid identifiers or non-canonical quarantine |
| TBG-3 | Open Code Review bypass | Unresolved | governance recovery report and CDG-6 | Open Code Review adapter invocation before Codex advanced review |
| TBG-4 | No review envelope in temp loop | Unresolved | governance recovery report and Loop Installer LI-3 | Schema-valid review envelope |
| CPG-1 | Envelope validation non-fatal | Unresolved | governance recovery report CPG-1 | Validation failures must block state transitions |
| CPG-2 | `merge_ready` without fresh final test run | Unresolved | governance recovery report CPG-2 | Fresh post-diff test event before merge-ready |
| CPG-3 | Codex review is mock | Unresolved | governance recovery report CPG-3 | Real Codex review invocation and output artifact |
| CPG-4 | Safety policy advisory-only | Unresolved | governance recovery report CPG-4 | `is_action_allowed()` or equivalent enforced by dispatchers/gates |
| CPG-5 | Repair loop no escalation path | Unresolved | governance recovery report CPG-5 | Timeout, human handoff, or bounded retry escalation with audit event |
| LI-1 | Temporary loop bypasses canonical state machine | Unresolved | Loop Installer self-audit | Same as CDG-1 closure |
| LI-2 | Audit events not schema-compatible | Unresolved | Loop Installer self-audit | Same as CDG-3 closure |
| LI-3 | Envelope protocol diverges from A2A | Unresolved | Loop Installer self-audit | Same as CDG-4/TBG-4/CPG-1 closure |
| LI-4 | Startup and permission preflight absent | Unresolved | Loop Installer self-audit | Same as CDG-2 closure |
| LI-5 | Hermes writes project-level docs during report generation | Unresolved | Loop Installer self-audit | Restrict report writes to trace dir unless TaskEnvelope explicitly permits docs output |

## Reconciliation of Conflicting Claims

### COP-5 and provider guard status

The two v1.2.1 reports disagree because they audit different points in the recovery timeline.

`docs/v1_2_1_dogfood_stabilization_audit.md` is earlier and records COP-5 as **partial**: `from_harness_config()` existed but retry/timeout fields remained env-only, and the targeted provider-guard suite had one failing test around `canary_timeout_seconds` merge semantics.

`docs/v1_2_1_dogfood_audit_report.md` is later on branch `recovery/v1.2-source-fix-clean` and cites commit `fe0d5fc`. It records COP-5 as **fixed** because `schema.py`, `loader.py`, `resolver.py`, and provider guard config now map `max_retries`, `retry_backoff`, and `retry_jitter`. It also reports provider guard targeted tests passing.

This global audit treats the later report as the stronger current-state evidence for source status, but preserves the earlier report's concern as a testing gap: retry-field merge precedence is not sufficiently regression-protected unless explicit retry merge tests and CLI/config output evidence are added.

### Provider guard degraded long-phase status

The v1.2 governance audit identified `long_phase_allowed_when_degraded` as unwired. The later v1.2.1 dogfood and v1.3 foundation audits agree that the flag is now wired through schema, loader, resolver, provider guard config, health, canary, and validator warnings. Therefore COP-4 and COP-13 are classified as fixed.

This does not close CDG/TBG/LI governance gaps. Provider guard safety protects one provider-degraded workflow; it does not provide canonical state machine, audit, envelope, startup, permission, Open Code Review, or merge-gate enforcement.

## Remaining Global Blockers

The following blockers prevent treating the temporary loop as canonical Harness OS governance:

1. Canonical state machine is bypassed by temporary loop states and JSONL-only transition evidence.
2. Canonical AuditEvent schema is not used by temporary loop audit logs.
3. Canonical A2A envelopes are not emitted and envelope validation is not fatal at transition boundaries.
4. Startup gate and permission preflight are not mechanically enforced before Codex/OpenCode dispatch.
5. Open Code Review is not consistently invoked as the first independent review gate with a schema-valid review envelope.
6. Codex final review is still reported as mock or custom-prompt based in recovery evidence, not a canonical real Codex gate with envelope evidence.
7. Merge readiness can be reached without a fresh final test run after latest diff.
8. Safety policy remains advisory where dispatchers/gates do not enforce allowed/blocked actions.
9. Repair rejection can dead-end without timeout, human escalation, or bounded recovery semantics.
10. Temporary runner writes project-level docs during report generation, which exceeds trace-scoped artifact collection unless the TaskEnvelope permits that output.

## Accepted Follow-Up Work

These items remain useful but are not blockers to the global governance decision when explicitly tracked outside the canonical-loop approval path:

| Item | Source IDs | Reason accepted as follow-up |
|---|---|---|
| AgentStateTimeline in live dashboard | COP-10 | Product UX enhancement, not a merge-governance invariant |
| argparse epilog polish | COP-11 | CLI usability issue; command governance text is already fixed in primary docstring |
| Credential storage runtime audit hardening | COP-14 | v1.3 secure default and validator warning exist; deeper runtime guard can be separate |
| Monitor/shell governance comment blocks | COP-16, COP-19 | Documentation/source comment hardening |
| Provider health workspace-root path cleanup | COP-18 | Low-priority source cleanup |
| PR draft manifest schema/version and manifest self-reference | v1.3.1 non-blocking findings | Local assistant artifact; not a Harness envelope unless promoted |
| Emergency reviewer cross-check port | CDG-10 | Positive pattern to port after core gates are canonical |
| v1.3 docs/install drift | v1.3 docs drift | Important documentation repair, but separate from canonical governance enforcement |

## Remediation Plan

| Priority | Dependency | Target subsystem | Related IDs | Required evidence to close |
|---:|---|---|---|---|
| P0 | None | State machine integration | CDG-1, TBG-1, TBG-2, LI-1 | Source diff using canonical state APIs, valid transition tests, audit event showing no bypass |
| P0 | None | Audit trail integration | CDG-3, TBG-3, LI-2 | Canonical AuditEvent records with schema validation and `.harness/audit/events.jsonl` evidence |
| P0 | State/audit path decided | Envelope validation and handoff | CDG-4, CDG-6, TBG-4, CPG-1, LI-3 | Schema-valid task/result/review/repair/final envelopes; validation failure blocks transition; tests for invalid envelopes |
| P0 | None | Startup and permission gates | CDG-2, CDG-8, CPG-4, LI-4 | Dispatcher/gate source diff, tests proving blocked actions fail before agent dispatch, audit events |
| P0 | Envelope and review schema | Real review gates | BG-1, BG-3, CPG-3, TBG-3 | Actual Codex advanced review invocation, Open Code Review adapter artifact, fresh independent session evidence |
| P0 | Test runner integration | Merge-gate fresh tests | BG-2, BG-4, CPG-2 | Fresh pytest command after latest diff, audit event, merge gate blocks stale/cached test evidence |
| P1 | State/audit paths | Repair escalation | CPG-5 | Timeout/human handoff or bounded retry state, audit event, tests for rejected repair path |
| P1 | Envelope model | Temporary runner quarantine or consolidation | CDG-5, LI-5 | Temp runner either calls canonical orchestrator or is explicitly blocked from merge-capable workflows; no unpermitted project-doc writes |
| P1 | Provider config stable | Provider guard regression tests | COP-5 | Retry merge-precedence tests and `config show`/provider-status evidence for retry fields |
| P2 | Core gates stable | Accepted follow-ups | COP-10, COP-11, COP-14, COP-16, COP-18, COP-19, v1.3 docs drift, v1.3.1 non-blockers | Separate task envelopes, targeted tests or docs diff, no claim that these close global governance blockers |

## Git And Test Evidence For This Docs-Only Audit

This task modifies only `docs/global_consistency_audit.md`.

`pytest` was not run for this report because the change is a docs-only synthesis artifact. The acceptance criteria allow pytest only if useful for validating referenced existing evidence; the referenced phase reports already record their own targeted and full-suite test evidence, and no source/test/config behavior changed here.

Final `git status` and `git diff` evidence was captured after writing the report and is included in the result envelope for this emergency implementation. The workspace contains pre-existing unrelated dirt, especially `docs/temp_loop_first_run_report.md`, prior untracked reports, and untracked runtime validator files; those are excluded from this task and are not attributed to this audit.

## Acceptance Criteria Mapping

| # | Criterion | Status | Evidence |
|---:|---|---|---|
| 1 | Read and cite all required phase reports | PASS | Evidence sources table cites all named reports including governance recovery report `c7210bbdf15c` |
| 2 | Create docs-only artifact | PASS | This file is `docs/global_consistency_audit.md` |
| 3 | Include phase-by-phase matrix | PASS | Phase Matrix section covers v1.1, v1.2, v1.2 source-fix, v1.2.1, v1.3, v1.3.1, Loop Installer, and recovery report |
| 4 | Cross-reference identifiers CDG/COP/BG/TBG/CPG/Loop Installer | PASS | Blocking Gap Classification includes CDG, COP, BG, TBG, CPG, and LI identifiers |
| 5 | Classify every blocking gap | PASS | Classification table assigns fixed, partially fixed, unresolved, planned/specification, or accepted follow-up status |
| 6 | Reconcile COP-5/provider guard conflict | PASS | Reconciliation section explains earlier partial/failing-test evidence versus later fixed/current-state evidence |
| 7 | Identify remaining global blockers | PASS | Remaining Global Blockers section lists canonical blockers |
| 8 | Include remediation plan | PASS | Remediation Plan orders by priority, dependency, target subsystem, IDs, and required evidence |
| 9 | Separate accepted follow-up from unresolved blockers | PASS | Accepted Follow-Up Work section is separate from Remaining Global Blockers |
| 10 | Do not modify source, tests, config, schemas, state, audit logs, or history | PASS | This is a docs-only file; no blocked git operations were used |
| 11 | Run git status and git diff after docs change | PASS | Captured in final emergency implementation JSON result |
| 12 | Run pytest only if useful; do not treat skipped/failed as passing | PASS | Pytest intentionally skipped for this docs-only synthesis; prior report test evidence is cited, not reclassified |

## Risk Assessment

| Risk | Severity | Assessment |
|---|---|---|
| Treating temporary loop evidence as canonical Harness OS evidence | High | Still blocked by CDG/TBG/CPG/LI unresolved items |
| Confusing fixed provider/copilot work with fixed loop governance | High | COP fixes are scoped to copilot/provider guard, not canonical loop enforcement |
| Overstating COP-5 closure | Medium | Current source status is fixed by later evidence, but retry merge semantics need explicit regression coverage |
| Workspace dirt obscuring task evidence | Medium | This report explicitly excludes unrelated pre-existing files and requires path-scoped diff evidence |
| Docs-only audit not enforcing runtime behavior | High | Expected; remediation requires follow-up source tasks through Harness governance |
