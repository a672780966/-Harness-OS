# v1.3.1 PR Draft Assistant Audit

Audit date: 2026-06-25
Trace ID: fa2ace05d055
Task ID: task-001
Scope: docs-only governance audit of the PR Draft Assistant, PR review workflow integration, evidence collection, and envelope/audit-trail alignment.

## Decision

approve

The v1.3.1 PR Draft Assistant is acceptable for the audited scope. It generates the required local PR draft artifacts, documents and isolates the `--create` network/write side effect, blocks known unsafe file classes, connects to the PR pack/comment review workflow, and uses existing loop artifact and evidence pack surfaces for review evidence. The main limitation is explicit: `pr_draft.json` is a local manifest, not a `task_envelope`, `result_envelope`, `review_envelope`, or audit event.

## Evidence

### Repository Path Mapping

| Audited behavior | Concrete path |
|---|---|
| PR draft generation and optional PR creation | `harness/copilot/pr_draft.py` |
| Blocked file pattern list | `harness/copilot/pr_draft.py:15` |
| Blocked file diff scan | `harness/copilot/pr_draft.py:36` |
| Worktree cleanliness check | `harness/copilot/pr_draft.py:63` |
| GitHub CLI availability and auth checks | `harness/copilot/pr_draft.py:72`, `harness/copilot/pr_draft.py:80` |
| Compare URL generation | `harness/copilot/pr_draft.py:98` |
| PR body generation | `harness/copilot/pr_draft.py:133` |
| Draft output writer | `harness/copilot/pr_draft.py:211` |
| `gh pr create` side effect path | `harness/copilot/pr_draft.py:296` |
| CLI command handler | `harness/copilot/cli.py:794` |
| CLI governance command documentation | `harness/copilot/cli.py:1` |
| PR pack project and loop builders | `harness/copilot/pr_integration/pr_pack.py:34`, `harness/copilot/pr_integration/pr_pack.py:51` |
| PR pack export writer | `harness/copilot/pr_integration/pr_pack.py:138` |
| PR comment integration | `harness/copilot/pr_integration/pr_comment_renderer.py` |
| Reviewer actions | `harness/copilot/pr_integration/reviewer_actions.py` |
| Risk checklist | `harness/copilot/pr_integration/risk_checklist.py` |
| Loop artifact loading | `harness/copilot/integration/loop_artifact_loader.py:56` |
| Loop artifact evidence mapping | `harness/copilot/integration/loop_to_copilot_mapper.py:101` |
| Evidence pack construction | `harness/copilot/evidence_pack.py` |
| Evidence and task card schemas | `harness/copilot/schemas.py:203`, `harness/copilot/schemas.py:281` |
| EvidencePack sha256 integrity | `harness/copilot/schemas.py:303` |
| Loop envelope generation | `harness/loop/envelope.py:10`, `harness/loop/envelope.py:49`, `harness/loop/envelope.py:89` |
| Envelope governance schemas | `.harness/envelopes/schema/` |
| Envelope validation | `harness/runtime/envelope_validator.py` |
| PR draft tests | `tests/copilot/test_pr_draft.py` |
| PR integration CLI tests | `tests/copilot/test_pr_integration_cli.py` |
| Evidence pack from loop tests | `tests/copilot/test_evidence_pack_from_loop.py` |
| CLI documentation tests | `tests/copilot/test_cli_documentation.py` |

### PR Draft Output Evaluation

`pr_title.txt`: Supported. `generate_pr_draft()` writes it at `harness/copilot/pr_draft.py:237`. The title includes the current head branch and detected base branch. `tests/copilot/test_pr_draft.py:152` verifies the branch appears in the title.

`pr_body.md`: Supported. `generate_pr_draft()` writes it at `harness/copilot/pr_draft.py:238` from `generate_pr_body()`. The body includes summary, validation, tag/evidence notes, merge recommendation, and explicit "Do Not Do" guidance. `tests/copilot/test_pr_draft.py:104` and `tests/copilot/test_pr_draft.py:161` cover the body sections and blocked tag note.

`compare_url.txt`: Supported. `generate_pr_draft()` writes it at `harness/copilot/pr_draft.py:239`. `generate_compare_url()` derives a GitHub compare URL when the origin remote can be parsed, otherwise returns an empty URL without failing draft generation.

`pr_open_instructions.md`: Supported. `generate_pr_draft()` writes it at `harness/copilot/pr_draft.py:266`. The content records `gh` availability, auth status, account, and whether `--create` can be used. If creation is unavailable, it gives manual PR opening steps.

`pr_draft.json`: Supported as a local manifest. `generate_pr_draft()` writes it at `harness/copilot/pr_draft.py:288`. The manifest includes `success`, `created_at`, `project_root`, `head_branch`, `base_branch`, `compare_url`, `worktree_clean`, `gh_available`, `gh_authenticated`, `gh_account`, `can_create_pr`, and a `files` map. `tests/copilot/test_pr_draft.py:131` verifies required manifest fields. It does not include the manifest itself in the `files` map; that is a non-blocking completeness note.

### Write and Network Governance

Default `pr-draft` behavior is local-write only. `run_pr_draft()` uses `.harness/pr_drafts/{timestamp}` when no `--out` is supplied (`harness/copilot/pr_draft.py:367`). It performs local git and filesystem reads, then writes the five draft artifacts. It does not call `gh pr create` unless `create=True`.

`--create` is the explicit WRITE + NETWORK side effect. `run_pr_draft()` dispatches to `create_pr()` when `create=True` (`harness/copilot/pr_draft.py:363`). `create_pr()` checks `gh` availability/auth (`harness/copilot/pr_draft.py:309`) and then invokes `gh pr create` (`harness/copilot/pr_draft.py:324`). The CLI docstring lists `pr-draft --create` under the "WRITE + NETWORK exception" section (`harness/copilot/cli.py:84`). `tests/copilot/test_cli_documentation.py` covers the command-surface and governance text.

No push, merge, tag, deploy, force-push, reset, clean, or history rewrite behavior was found in the PR draft code path.

### Blocked File Safeguards

`BLOCKED_PATTERNS` covers large archives (`dist/*.tar.gz`, `*.tar.gz`, `*.tgz`, `*.zip`), generated Python artifacts (`__pycache__/`, `*.pyc`), local virtual/cache directories (`.venv/`, `.ocr/`), agent directories (`.claude/`, `.agents/`, `.specify/`), and related generated outputs (`harness/copilot/pr_draft.py:15`).

`check_blocked_files()` scans the git diff versus `origin/main..HEAD`, falling back to `HEAD~1` if needed, and matches changed paths against the blocked pattern list (`harness/copilot/pr_draft.py:36`). `run_pr_draft()` refuses to proceed when blocked files are detected (`harness/copilot/pr_draft.py:354`). Tests cover clean diffs, archive detection, and blocked draft rejection in `tests/copilot/test_pr_draft.py:66`, `tests/copilot/test_pr_draft.py:73`, and `tests/copilot/test_pr_draft.py:144`.

The public-safe evidence strategy is referenced in the generated PR body: `docs/public_safe_evidence_strategy.md`, `docs/public_safe_tag_mapping.md`, and `docs/large_evidence_archive_manifest.md` are emitted by `generate_pr_body()` (`harness/copilot/pr_draft.py:190`). This keeps large evidence archives out of GitHub-visible refs while preserving auditability by reference.

### Review Workflow Integration

`pr-pack` builds review packs from either the project diff (`build_pr_pack()`) or loop artifacts (`build_pr_pack_from_loop()`), then exports markdown files and `pr_pack.json` (`harness/copilot/pr_integration/pr_pack.py:34`, `harness/copilot/pr_integration/pr_pack.py:51`, `harness/copilot/pr_integration/pr_pack.py:138`). The pack contains merge readiness, risk checklist, task cards, evidence, evidence files, reviewer actions, and read-only/no-external-API flags.

`pr-comment` uses the PR pack renderer (`harness/copilot/cli.py:831`) and the loop variant uses loop artifacts through `build_pr_pack_from_loop()` (`harness/copilot/cli.py:845`). Reviewer actions are generated from merge state, blocking issues, pending task cards, high-risk count, agent state, and evidence totals in `harness/copilot/pr_integration/reviewer_actions.py`.

Loop artifact loading reads task/result/final gate envelope locations, review envelope directories, patch diffs, repair rounds, process attestations, test results, and final gate markdown (`harness/copilot/integration/loop_artifact_loader.py:56`). Final gate evidence is loaded as `final_gate_result` (`harness/copilot/integration/loop_artifact_loader.py:84`) and mapped into dashboard/readiness flows through `final_gate_to_readiness()` from `harness/copilot/integration/final_gate_mapper.py`.

### Evidence Collection

`EvidencePack` entries are modeled in `harness/copilot/schemas.py:281`; the pack-level `sha256` property hashes the dataclass content deterministically (`harness/copilot/schemas.py:303`). `harness/copilot/evidence_pack.py` builds packs from task card verification entries, evidence directories, or minimal test/review results.

Loop artifact evidence mapping happens through `_build_evidence_pack()` in `harness/copilot/integration/loop_to_copilot_mapper.py`, reached from `artifacts_to_dashboard()` at `harness/copilot/integration/loop_to_copilot_mapper.py:101`. The required evidence classes are represented in tests: test result evidence, review/final gate evidence, patch evidence, passed counts, and sha256 integrity are covered by `tests/copilot/test_evidence_pack_from_loop.py`.

The evidence model supports test/review/final-gate/patch evidence through artifact loading plus evidence pack rendering. The exact categorization is distributed across `loop_artifact_loader.py`, `loop_to_copilot_mapper.py`, `evidence_pack.py`, and PR pack export rather than being owned by `pr_draft.py`.

### Envelope Protocol and Audit Trail Compliance

Supported envelope serialization exists for task cards through `TaskCard.to_envelope()` and `TaskCard.from_envelope()` (`harness/copilot/schemas.py:224`). Loop envelope generation exists for TaskEnvelope, ResultEnvelope, and ReviewEnvelope in `harness/loop/envelope.py`.

`pr_draft.json` is not a Harness task/result/review envelope and is not an audit event. It does not bind generated PR draft output to `task_envelope`, `result_envelope`, `review_envelope`, `final_acceptance`, or `audit_events.jsonl`. This is acceptable for the audited v1.3.1 feature because PR draft generation is a local assistant utility, while Harness worker handoff and audit trail binding remain in the loop/envelope and runtime/audit layers. The distinction should remain explicit in user-facing docs to avoid treating a PR draft manifest as final gate evidence.

## Missing Evidence

- No live E2E execution of `gh pr create`; that would require authenticated GitHub CLI credentials and intentional network/write side effects.
- No formal JSON Schema exists specifically for `pr_draft.json`.
- `pr_draft.json` is not bound to a Harness audit event or result envelope by `pr_draft.py`; envelope/audit binding is supplied by the wider loop, not the draft assistant.
- Current workspace contains unrelated dirty/untracked files, so git evidence must distinguish the task artifact from pre-existing work.

## Blocking Issues

None for this docs-only audit.

## Non-Blocking Issues

- `pr_draft.json` has no dedicated schema file, which makes downstream validation looser than `task_envelope`/`result_envelope` validation.
- `pr_draft.json` omits a `manifest_version` field and does not include `pr_draft.json` in its own `files` map.
- `check_blocked_files()` only evaluates tracked git diff paths, so local untracked archive/cache files are not blocked until staged/committed or otherwise included in the compared diff.
- The `--create` path depends on `gh` CLI behavior and is not covered by a live integration test.

## Required Fixes

No code fixes are required for this task. Future hardening should add a `pr_draft.json` schema and optional audit-event/result-envelope binding when PR draft output is promoted from local assistant artifact to formal Harness loop evidence.

## Risk Assessment

| Risk | Severity | Assessment |
|---|---|---|
| Network/write side effect through `--create` | Medium | Explicit flag only; CLI governance documents it; auth check runs before `gh pr create`. |
| Misreading `pr_draft.json` as a Harness envelope | Medium | Report documents the distinction; future docs should keep it explicit. |
| Blocked file bypass via untracked files | Low | PR diff safeguards cover changed git paths; untracked local files are outside PR draft diff scope. |
| Missing schema for draft manifest | Low | Tests verify field shape; schema would improve downstream validation. |

## Test Evidence

Command run:

```text
PYTHONPATH=. pytest tests/copilot/test_pr_draft.py tests/copilot/test_pr_integration_cli.py tests/copilot/test_evidence_pack_from_loop.py tests/copilot/test_cli_documentation.py
```

Result:

```text
collected 63 items
tests/copilot/test_pr_draft.py .............                             [ 20%]
tests/copilot/test_pr_integration_cli.py .......                         [ 31%]
tests/copilot/test_evidence_pack_from_loop.py .......                    [ 42%]
tests/copilot/test_cli_documentation.py ................................ [ 93%]
....                                                                     [100%]
63 passed in 7.12s
exit code: 0
```

Broader evidence supplied in the task context also showed `933 passed, 1 skipped in 29.67s`, exit code 0.

## Git Evidence

Command run:

```text
git status --short --branch
```

Observed status before the final report update:

```text
## recovery/v1.2-source-fix-clean
 M docs/temp_loop_first_run_report.md
?? docs/v1_1_governance_audit_report.md
?? docs/v1_2_1_dogfood_audit_report.md
?? docs/v1_2_1_dogfood_stabilization_audit.md
?? docs/v1_2_engineering_copilot_governance_audit.md
?? docs/v1_2_engineering_copilot_source_fix_plan.md
?? docs/v1_3_1_pr_draft_assistant_audit.md
?? docs/v1_3_foundation_runtime_audit.md
?? harness/runtime/envelope_validator.py
?? tests/test_runtime_envelope_validator.py
```

Task artifact: `docs/v1_3_1_pr_draft_assistant_audit.md`.

Unrelated pre-existing workspace dirt excluded from this task evidence: `docs/temp_loop_first_run_report.md`, the other untracked docs reports, `harness/runtime/envelope_validator.py`, and `tests/test_runtime_envelope_validator.py`. This task did not modify source code, tests, package manifests, lockfiles, migrations, workflows, secrets, or deployment scripts.

Diff evidence for this task should be captured with:

```text
git diff --no-index /dev/null docs/v1_3_1_pr_draft_assistant_audit.md
```

That command produces a new-file patch for only `docs/v1_3_1_pr_draft_assistant_audit.md`; `docs/temp_loop_first_run_report.md` is explicitly excluded from this task's patch evidence.
