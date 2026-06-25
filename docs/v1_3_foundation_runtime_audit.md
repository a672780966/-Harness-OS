# v1.3 Foundation Config and Runtime Audit Report

> **Task**: Audit the v1.3 Foundation Config and Runtime modules for governance completeness, workspace hygiene, pre-merge cleanup needs, and config documentation gaps.
> **Date**: 2026-06-25
> **Branch**: `recovery/v1.2-source-fix-clean`
> **Auditor**: OpenCode (temporary-loop worker)

---

## 1. Scope

### Config modules (harness/config/)

| File | Lines | Role |
|------|-------|------|
| `harness/config/schema.py` | 193 | `HarnessConfig` dataclass, `ProviderConfig`, `WorkspaceConfig`, `RuntimeConfig`, `CopilotConfig`, `SecurityConfig`, `SECURITY_SENSITIVE_KEYS`, merge logic |
| `harness/config/loader.py` | 253 | YAML/JSON config file parsing, `_parse_bool`, `write_default_global_config`, `_render_yaml` |
| `harness/config/resolver.py` | 152 | Priority-ordered resolution: CLI > Env > Project > Global > Defaults |
| `harness/config/validator.py` | 107 | Config validation, security warnings, mode/timeout sanity checks |
| `harness/config/paths.py` | 48 | Global (`~/.harness/config.yaml`) and project (`<root>/.harness/config.yaml`) path resolution |

### Runtime modules (harness/runtime/)

| File | Lines | Role |
|------|-------|------|
| `harness/runtime/doctor.py` | 195 | System prerequisite checks (Python, Git, pytest, OS, opencode CLI, global config, runtime dir) |
| `harness/runtime/version.py` | 87 | Version info from git tags/commits with hardcoded fallback |

### Provider guard integration

| File | Lines | Role |
|------|-------|------|
| `harness/copilot/provider_guard/config.py` | 140 | `ProviderGuardConfig` dataclass, `from_harness_config()`, `from_env()`, `_parse_bool` |
| `harness/copilot/provider_guard/canary.py` | 286 | Canary runner, `check_before_long_phase()`, failure classification |
| `harness/copilot/provider_guard/health.py` | 258 | `ProviderHealthState`, persistence, `can_proceed_to_long_phase()`, `health_check_needed()` |
| `harness/copilot/provider_guard/__init__.py` | 58 | Public API surface |

### Targeted test files

| Test file | Tests |
|-----------|-------|
| `tests/test_config_schema.py` | 18 tests — schema defaults, security keys, ProviderConfig, merge |
| `tests/test_config_loader.py` | 13 tests — YAML/JSON loading, bool parsing, write defaults |
| `tests/test_config_resolution_priority.py` | 9 tests — env overrides, CLI overrides, project > global |
| `tests/test_config_validator.py` | 14 tests — security warnings, mode validation, version errors |
| `tests/test_config_paths.py` | 9 tests — global/project path resolution |
| `tests/test_runtime_doctor.py` | 12 tests — Python/Git/pytest/OS checks, doctor summary |
| `tests/test_runtime_version.py` | 10 tests — git tag/commit, version formatting |
| `tests/copilot/test_provider_guard.py` | 50 tests — config, health state, canary, guard integration, read-only safety |

### Reference docs

| Doc | Lines | Role |
|-----|-------|------|
| `docs/v1_3_foundation_config.md` | 113 | Config management changelog with schema, CLI, resolution priority, security keys |
| `docs/v1_3_install_baseline.md` | 115 | Install guide with prerequisites, config init, doctor, OS support |
| `docs/v1_3_runtime_migration_plan.md` | 153 | Cross-platform migration plan for runtime |

---

## 2. Governance Completeness

### 2.1 Secure defaults

| Setting | Default | Secure? | Verified by test |
|---------|---------|---------|-----------------|
| `runtime.readonly_default` | `True` | ✅ | `test_default_readonly` |
| `runtime.allow_external_api` | `False` | ✅ | `test_default_no_external_api` |
| `security.save_credentials` | `False` | ✅ | `test_default_no_save_credentials` |
| `security.allow_agent_control` | `False` | ✅ | `test_default_no_agent_control` |
| `provider.mode` | `"readonly"` | ✅ | `test_default_provider_mode_readonly` |
| `provider.long_phase_allowed_when_degraded` | `False` | ✅ | `test_default_long_phase_disabled_when_degraded` |

**Verdict**: All security-sensitive settings default to OFF. Secure defaults are complete and tested.

### 2.2 Security-sensitive setting warnings

The `SECURITY_SENSITIVE_KEYS` dict in `schema.py` defines 4 keys that trigger validator warnings:

| Key | Warning message |
|-----|----------------|
| `save_credentials` | "Enabling save_credentials stores API tokens on disk." |
| `allow_agent_control` | "Enabling allow_agent_control permits automatic code modification." |
| `allow_external_api` | "Enabling allow_external_api makes network requests." |
| `long_phase_allowed_when_degraded` | "Running long phases while provider is degraded may hang." |

**Tested**: All 4 keys have corresponding validator tests (`test_save_credentials_triggers_security`, `test_allow_agent_control_triggers_security`, `test_allow_external_api_triggers_security`, `test_long_phase_when_degraded_triggers_security`). All pass.

### 2.3 Credential storage

`save_credentials` defaults to `False`. The provider guard module has a dedicated read-only safety test (`test_no_credential_strings`) that scans source files for hardcoded `api_key`, `api_secret`, `api_token`, `password`, `bearer ` patterns. All pass.

### 2.4 Agent control

`allow_agent_control` defaults to `False`. The provider guard's `check_before_long_phase()` gate blocks degraded/failed states from proceeding to long implementation phases. The `long_phase_allowed_when_degraded` flag provides an explicit opt-in.

### 2.5 External API gating

`allow_external_api` defaults to `False`. The provider guard module has a `test_no_external_api_imports` test that bans `requests`, `flask`, `fastapi`, `github`, `httpx` from the provider guard submodules.

### 2.6 Provider degraded-phase behavior

The `long_phase_allowed_when_degraded` flag is wired through:
1. `harness/config/schema.py` → `ProviderConfig` field (default `False`)
2. `harness/config/loader.py` → parsed via `_parse_bool` in provider section
3. `harness/config/resolver.py` → included in `_merge_raw_override`
4. `harness/config/validator.py` → triggers security warning when `True`
5. `harness/copilot/provider_guard/config.py` → `ProviderGuardConfig` field from `ProviderConfig` defaults
6. `harness/copilot/provider_guard/health.py` → `can_proceed_to_long_phase()` checks it
7. `harness/copilot/provider_guard/canary.py` → `check_before_long_phase()` checks it

**Tested**: `test_can_proceed_degraded_with_override`, `test_can_proceed_degraded_with_override_false`, `test_degraded_allows_with_override_config`, `test_degraded_blocks_with_override_false_config`. All pass.

**Gap**: The `_parse_bool` function is defined twice — once in `loader.py` and once in `provider_guard/config.py`. These have slightly different implementations (`loader.py`'s version checks `value.strip().lower() in ("true", "yes", "1", "on")` while `config.py`'s version checks `value.strip().lower() in ("true", "yes", "1", "on")` — functionally identical but a maintenance risk).

### 2.7 CLI/documentation claims

`docs/v1_3_foundation_config.md` documents 6 new CLI commands:
- `harness copilot config init`
- `harness copilot config show --project=<path>`
- `harness copilot config path --project=<path>`
- `harness copilot config validate --project=<>`
- `harness copilot doctor`
- `harness copilot version --json`

**Gap**: The config schema example YAML in `docs/v1_3_foundation_config.md` includes fields (`canary_prompt`, `canary_max_tokens`) that do not exist in the actual `schema.py` `ProviderConfig`. The actual schema defines `canary_timeout_seconds` but not `canary_prompt` or `canary_max_tokens`. These exist only in `ProviderGuardConfig` in `provider_guard/config.py`. This is a **documentation drift** issue.

**Doc field**: `docs/v1_3_foundation_config.md` schema lists `canary_prompt: "OK"` and `canary_max_tokens: 10` under `provider:`. These fields are not part of `ProviderConfig` — they belong to `ProviderGuardConfig`. The correct config schema for `ProviderConfig` includes only: `mode`, `primary`, `fallback`, `connect_timeout_seconds`, `read_timeout_seconds`, `canary_timeout_seconds`, `max_retries`, `retry_backoff`, `retry_jitter`, `long_phase_allowed_when_degraded`.

---

## 3. Workspace Hygiene and Pre-Merge Cleanup

### 3.1 Current git status

```
## recovery/v1.2-source-fix-clean
 M docs/temp_loop_first_run_report.md
?? docs/v1_1_governance_audit_report.md
?? docs/v1_2_1_dogfood_audit_report.md
?? docs/v1_2_1_dogfood_stabilization_audit.md
?? docs/v1_2_engineering_copilot_governance_audit.md
?? docs/v1_2_engineering_copilot_source_fix_plan.md
?? docs/v1_3_foundation_runtime_audit.md
?? harness/runtime/envelope_validator.py
?? tests/test_runtime_envelope_validator.py
```

### 3.2 Observations

1. **Modified tracked file (pre-existing dirty)**: `docs/temp_loop_first_run_report.md` has unstaged modifications (300-line diff). This file belongs to a previous temporary loop (v1.2.1 dogfood audit) and was **not changed by this task**. The prior `git diff` at task start already showed only this file as modified. The diff content references `v1_2_1_dogfood_audit_report.md` and unrelated graph nodes — confirming this is pre-existing dirty state from a prior loop.
2. **Untracked task artifact**: `docs/v1_3_foundation_runtime_audit.md` is the only file created by this task. It is listed above as an untracked file.
3. **Pre-existing untracked docs files**: 5 untracked docs files (`v1_1_governance_audit_report.md`, `v1_2_1_dogfood_audit_report.md`, `v1_2_1_dogfood_stabilization_audit.md`, `v1_2_engineering_copilot_governance_audit.md`, `v1_2_engineering_copilot_source_fix_plan.md`) from previous audit/investigation tasks. None were touched by this task.
4. **Pre-existing untracked source files**: `harness/runtime/envelope_validator.py` and `tests/test_runtime_envelope_validator.py` are untracked source/test files not registered in any task. These appear to be leftover from a prior loop (referenced in `temp_loop_first_run_report.md` as pre-existing). Not part of this task.
5. **No source, test, config, or Harness state changes**: This audit produces `docs/v1_3_foundation_runtime_audit.md` as its only artifact. No source code, tests, harness state, envelope files, audit logs, configuration files, or git history were modified.

### 3.3 Pre-merge cleanup checklist

| Item | Status | Action |
|------|--------|--------|
| `docs/temp_loop_first_run_report.md` stale diff | ⚠️ | Revert or commit before merge |
| 6 untracked docs files (5 pre-existing + 1 task artifact) | ⚠️ | Review and either commit or clean |
| `harness/runtime/envelope_validator.py` untracked | ⚠️ | Source code outside any task — review and decide |
| `tests/test_runtime_envelope_validator.py` untracked | ⚠️ | Test file outside any task — review and decide |
| `__pycache__/` artifacts | ⚠️ | Add `__pycache__/` to `.gitignore` if not already |
| `.venv/`, `.ocr/`, `.claude/`, `.agents/`, `.specify/`, `.codex/` directories | ✅ | Already in `.gitignore` per merge readiness prep |

---

## 4. Config Documentation Gaps / Drift

### 4.1 Schema vs docs: `docs/v1_3_foundation_config.md`

| Field in docs schema | In actual `ProviderConfig`? | Severity |
|---------------------|----------------------------|----------|
| `canary_prompt: "OK"` | ❌ No — only in `ProviderGuardConfig` | **HIGH** — docs claim a config field that does not exist |
| `canary_max_tokens: 10` | ❌ No — only in `ProviderGuardConfig` | **HIGH** — docs claim a config field that does not exist |
| `workspace.root: ""` | ✅ Yes — but default is `"~/harness-workspace"`, not `""` | **LOW** — default shown in docs differs from actual default |
| `mode: readonly` under `provider:` | ✅ Yes | OK |
| `readonly_default: true` under `runtime:` | ✅ Yes | OK |
| `default_format: markdown` under `copilot:` | ✅ Yes | OK |

**Root cause**: The docs describe the intended multi-provider fallback plan from `v1_3_provider_reliability_plan.md` (which proposed `canary_prompt` and `canary_max_tokens` as future config schema fields), but these fields were never added to `ProviderConfig`. The actual schema keeps canary prompt/max_tokens as `ProviderGuardConfig`-only constants.

### 4.2 Schema vs docs: `docs/v1_3_install_baseline.md`

| Claim | Actual | Severity |
|-------|--------|----------|
| `pip install -e .` works | ❌ No `setup.py` or `pyproject.toml` exists in the repo root | **HIGH** — install instructions reference non-existent entrypoint |
| `harness copilot config init` creates `~/.harness/config.yaml` | ✅ Loader has `write_default_global_config()` but no CLI entrypoint was verified to call it | **MEDIUM** — the function exists but CLI routing needs verification |
| `harness copilot doctor` verifies prerequisites | ✅ `doctor.py` implements all 7 checks | OK |
| `pytest tests/test_config_*.py` | ✅ Files exist, 63 config tests pass | OK |
| `pytest tests/test_runtime_*.py` | ✅ Files exist, 22 runtime tests pass | OK |

### 4.3 Schema vs docs: `docs/v1_3_runtime_migration_plan.md`

| Claim | Actual | Severity |
|-------|--------|----------|
| Provider guard config consolidation with `~/.harness/config.yaml` | ✅ Done — `ProviderGuardConfig.from_harness_config()` exists | OK |
| Per-project `.harness/provider.yaml` support | ❌ Not implemented — only `.harness/config.yaml` is supported | **MEDIUM** — migration plan describes feature not implemented |
| `.harness/runtime/` directory migration (Phase 2: `--runtime-dir` arg) | ❌ Not implemented | **MEDIUM** — planned but not in current code |
| Hardcoded cooldown 120s made configurable | ❌ Still hardcoded as `health_check_cooldown_seconds` in `ProviderGuardConfig` | **LOW** — it's configurable in ProviderGuardConfig but not in `HarnessConfig` schema |

### 4.4 Schema vs tests

| Test assertion | Actual schema/source | Severity |
|---------------|---------------------|----------|
| `test_cli_help_shows_command` is a no-op (`assert True`) | ❌ Does not actually verify CLI help text | **LOW** — structural stub |
| `test_defaults_match_provider_guard_config` compares ProviderConfig defaults vs ProviderGuardConfig | ✅ Verifies `connect_timeout_seconds`, `read_timeout_seconds`, `max_retries`, `retry_backoff`, `retry_jitter` match | OK |
| `test_no_external_api_imports` bans `requests`, `flask`, `fastapi`, `github`, `httpx` | ✅ Provider guard submodules do not import these | OK |

---

## 5. Test Evidence

All 8 targeted test suites were run with `PYTHONPATH=.`:

| Suite | Tests | Passed | Failed | Time |
|-------|-------|--------|--------|------|
| `test_config_schema.py` | 18 | 18 | 0 | 0.03s |
| `test_config_loader.py` | 13 | 13 | 0 | 0.05s |
| `test_config_resolution_priority.py` | 9 | 9 | 0 | 0.04s |
| `test_config_validator.py` | 14 | 14 | 0 | 0.03s |
| `test_config_paths.py` | 9 | 9 | 0 | 0.03s |
| `test_runtime_doctor.py` | 12 | 12 | 0 | 2.80s |
| `test_runtime_version.py` | 10 | 10 | 0 | 0.08s |
| `test_provider_guard.py` | 50 | 50 | 0 | 0.82s |
| **Total** | **135** | **135** | **0** | **3.82s** |

**Command**: `PYTHONPATH=. python -m pytest tests/test_config_schema.py tests/test_config_loader.py tests/test_config_resolution_priority.py tests/test_config_validator.py tests/test_config_paths.py tests/test_runtime_doctor.py tests/test_runtime_version.py tests/copilot/test_provider_guard.py -v --tb=short`

**Verdict**: All 135 targeted tests pass with no failures.

### Tests not run and why

- `test_runtime_envelope_validator.py`: Untracked file, not part of v1.3 Foundation Config/Runtime scope. Belongs to a separate envelope validation feature.
- Full 900+ test suite: Not required per acceptance criteria. Task specifies "targeted config/runtime suites."
- `tests/copilot/test_pr_integration_cli.py`, `tests/copilot/test_pr_draft.py`, `tests/copilot/test_risk_classifier_dedup.py`: Outside config/runtime scope.

---

## 6. Blocking Issues

### B-1: Config doc schema shows non-existent fields

**File**: `docs/v1_3_foundation_config.md:47-70`
**Issue**: The example schema YAML includes `canary_prompt` and `canary_max_tokens` under `provider:`, but these fields do not exist in `ProviderConfig`. They are `ProviderGuardConfig`-only constants.
**Severity**: HIGH — docs claim config fields that do not exist, which would cause silent ignore or user confusion.
**Fix**: Remove `canary_prompt` and `canary_max_tokens` from the example schema, or add them to `ProviderConfig` if they are intended to be user-configurable.
**Evidence**: `harness/config/schema.py:18-56` shows `ProviderConfig` fields. `harness/copilot/provider_guard/config.py:32-49` shows `ProviderGuardConfig` fields including `minimal_canary_prompt` and `canary_max_tokens`.

### B-2: Install docs reference non-existent setup.py/pyproject.toml

**File**: `docs/v1_3_install_baseline.md:29-32`
**Issue**: `pip install -e .` is documented as the install method, but no `setup.py`, `setup.cfg`, or `pyproject.toml` exists in the repository root.
**Severity**: HIGH — install instructions cannot be followed.
**Fix**: Add `pyproject.toml` with standard Python packaging metadata, or update docs to use the actual install method (e.g., `PYTHONPATH=.` or entry-point script).
**Evidence**: `ls` of repo root shows no `setup.py` or `pyproject.toml`. The `__init__.py` files suggest namespace package usage without package metadata.

---

## 7. Non-Blocking Issues

### NB-1: Duplicate `_parse_bool` implementation

**Files**: `harness/config/loader.py:99-110` and `harness/copilot/provider_guard/config.py:126-136`
**Issue**: `_parse_bool` is defined in both modules with functionally identical but independently maintained implementations.
**Risk**: LOW — both handle the same edge cases identically, but future changes to one will not apply to the other.
**Fix**: Either export `_parse_bool` from a shared utility module, or have `provider_guard/config.py` import from `loader.py` (with care for circular imports).

### NB-2: Workspace root default mismatch

**File**: `docs/v1_3_foundation_config.md:50` shows `workspace.root: ""`, but the actual default in `schema.py:63` is `"~/harness-workspace"`.
**Risk**: LOW — the empty string default in docs may lead users to expect no workspace root is set by default.
**Fix**: Align docs with actual default.

### NB-3: `test_cli_help_shows_command` is a structural no-op

**File**: `tests/copilot/test_provider_guard.py:558-561`
**Issue**: The test is `assert True` with a comment explaining it's a structural check. It does not actually verify CLI help text.
**Risk**: LOW — the CLI subparser registration is verified by import success, but the help text content is not validated.
**Fix**: Implement actual argparse introspection to verify the command appears in help output.

### NB-4: Runtime migration plan describes unimplemented features

**File**: `docs/v1_3_runtime_migration_plan.md`
**Issues**:
- Per-project `.harness/provider.yaml` is described but not implemented
- `--runtime-dir` CLI argument is planned but not implemented
- `ProviderChain` class with multi-provider fallback is described in the plan but does not exist in source
**Risk**: MEDIUM — these are planning documents, not production docs, so the risk is primarily confusion about current vs. planned capabilities.

### NB-5: `health_check_cooldown_seconds` is configurable in `ProviderGuardConfig` but not in `HarnessConfig`

**File**: `harness/copilot/provider_guard/config.py:49` (`health_check_cooldown_seconds: float = 120.0`)
**Issue**: The cooldown value is part of `ProviderGuardConfig` defaults but is not exposed through `HarnessConfig.provider` schema. The migration plan marked this as a planned improvement (v1.3).
**Risk**: LOW — env var override exists via `from_env()`, but config file users cannot set it.

### NB-6: `consecutive_failures_to_degrade` is not configurable via config file

**File**: `harness/copilot/provider_guard/config.py:47`
**Issue**: The degradation threshold (2 consecutive failures) is a hardcoded constant in `ProviderGuardConfig`. It is not exposed in `HarnessConfig.provider` schema.
**Risk**: LOW — acceptable for v1.3. Env var override could be added, but no use case requires it yet.

---

## 8. Config Documentation Drift Summary

| Area | Drift | Severity |
|------|-------|----------|
| `v1_3_foundation_config.md` schema has canary_prompt/canary_max_tokens not in actual schema | B-1 | HIGH |
| `v1_3_install_baseline.md` references non-existent setup.py | B-2 | HIGH |
| `v1_3_foundation_config.md` shows workspace.root default as "" (actual: "~/harness-workspace") | NB-2 | LOW |
| `v1_3_runtime_migration_plan.md` describes unimplemented features | NB-4 | MEDIUM |
| `v1_3_foundation_config.md` does not document `primary`/`fallback` model fields | NB-7 | LOW |

### NB-7: Schema fields undocumented

**Files**: `harness/config/schema.py:28-29` and `docs/v1_3_foundation_config.md`
**Issue**: The `ProviderConfig` fields `primary` (default: "opencode-go/deepseek-v4-flash") and `fallback` (default: "opencode/deepseek-v4-flash-free") are not shown in the docs example schema. Only `mode` is shown under `provider:`.
**Fix**: Add `primary` and `fallback` fields to the example schema in the doc.

---

## 9. Required Fixes for Merge

| Priority | Fix | File | Associated issue |
|----------|-----|------|-----------------|
| HIGH | Remove canary_prompt/canary_max_tokens from schema example or add to ProviderConfig | `docs/v1_3_foundation_config.md` | B-1 |
| HIGH | Add pyproject.toml or update install instructions | `docs/v1_3_install_baseline.md` or repo root | B-2 |
| LOW | Align workspace.root default in docs | `docs/v1_3_foundation_config.md` | NB-2 |
| LOW | Document primary/fallback model fields | `docs/v1_3_foundation_config.md` | NB-7 |
| MEDIUM | Revert or commit `docs/temp_loop_first_run_report.md` | Workspace hygiene | 3.3 |
| MEDIUM | Review untracked source/test files | Workspace hygiene | 3.3 |

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Users confused by non-existent config fields (canary_prompt/canary_max_tokens) | MEDIUM | LOW — config loader silently ignores unknown keys | Fix docs (B-1) |
| Users cannot `pip install -e .` as documented | HIGH | MEDIUM — setup instructions fail | Fix docs or add packaging (B-2) |
| Provider guard `_parse_bool` divergence | LOW | LOW — functionally identical | Consolidate (NB-1) |
| CLI docs drift from actual commands | LOW | MEDIUM — stale docs lead to user confusion | Not verified in this audit |
| Untracked source files merged accidentally | LOW | MEDIUM — envelope_validator is pre-loop work | Clean before merge |

---

## 11. Self-Review

### 11.1 Issues found during audit

1. **Config doc schema has phantom fields**: `canary_prompt` and `canary_max_tokens` in `docs/v1_3_foundation_config.md` do not exist in `ProviderConfig`. Only `ProviderGuardConfig` has them.
2. **Install doc has missing package metadata**: `pip install -e .` requires `pyproject.toml` or `setup.py`, neither exists.
3. **Provider config has undocumented model fields**: `primary` and `fallback` model identifiers are in the schema but not in the docs.
4. **Duplicate `_parse_bool` in loader.py and provider_guard/config.py**: Maintenance hazard.
5. **Workspace hygiene**: There are 8 untracked/modified files that are not part of this task.
6. **Coverage `test_cli_help_shows_command` is a no-op**: Does not actually verify CLI help content.

### 11.2 Self-review evidence

- All source and test files were read and analyzed before writing the report (see Read tool calls above).
- Targeted config/runtime test suites run: 135 tests pass.
- No source, test, config, Harness state, envelope, audit, or git files were modified by this task.
- Only `docs/v1_3_foundation_runtime_audit.md` is created by this task.

### 11.3 Remaining risks

- Full test suite (900+ tests) not run — only 135 targeted config/runtime tests were executed.
- Envelope validator (`harness/runtime/envelope_validator.py`) and its tests (`tests/test_runtime_envelope_validator.py`) are untracked, pre-existing files. Not reviewed in this audit.
- CLI routing for config commands (`config init`, `config show`, `config path`, `config validate`) was not verified end-to-end. The `cli.py` module was not analyzed for command registration.
- The `test_no_external_api_imports` test verifies provider_guard submodules only — other runtime modules (doctor.py, version.py) may need similar guards.
