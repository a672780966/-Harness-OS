# v1.3 Foundation: Config Management — Changelog

## Overview

v1.3 introduces a structured configuration system for Harness Copilot, replacing
ad-hoc environment-variable-based settings with a schema-versioned, file-backed
configuration system that supports global + project-level config files,
environment variable overrides, and CLI-level overrides.

## New Modules

### `harness/config/` — Structured Configuration

| File | Purpose |
|------|---------|
| `schema.py` | `HarnessConfig` dataclass with versioned schema, security-sensitive key detection |
| `loader.py` | YAML/JSON config file parsing, `write_default_global_config()` |
| `resolver.py` | Priority-ordered resolution: CLI > Env > Project File > Global File > Defaults |
| `paths.py` | Global (`~/.harness/config.yaml`) and project (`<root>/.harness/config.yaml`) path resolution |
| `validator.py` | Schema validation, security warnings, sanity checks |

### `harness/runtime/` — Runtime Utilities

| File | Purpose |
|------|---------|
| `doctor.py` | System prerequisite checks: Python, Git, pytest, OS detection, opencode CLI, global config |
| `version.py` | Version info from git tags/commits with hardcoded fallback |

## New CLI Commands

All available under `harness copilot`:

```bash
# Config management
harness copilot config init                  # Create ~/.harness/config.yaml
harness copilot config show --project=<path> # Show effective merged config
harness copilot config path --project=<path> # Show config file paths
harness copilot config validate --project=<> # Validate config for safety

# Runtime utilities
harness copilot doctor                       # System prerequisite checks
harness copilot version --json               # Version info
```

## Config Schema (v1)

```yaml
version: 1
workspace:
  root: ""                          # Project workspace root
provider:
  mode: readonly                    # readonly | primary | fallback
  connect_timeout_seconds: 10
  read_timeout_seconds: 90
  max_retries: 3
  retry_backoff: exponential
  canary_prompt: "OK"
  canary_max_tokens: 10
  canary_timeout_seconds: 45
  long_phase_allowed_when_degraded: false
runtime:
  mode: local                       # local | remote
  readonly_default: true
  allow_external_api: false
security:
  save_credentials: false
  allow_agent_control: false
copilot:
  default_format: markdown          # markdown | json
```

## Resolution Priority

```
Highest: CLI overrides
         Environment variables (HARNESS_*)
         Project config (<root>/.harness/config.yaml)
         Global config (~/.harness/config.yaml)
Lowest:  Schema defaults (hardcoded)
```

## Security-Sensitive Keys

The following keys trigger `config validate` warnings when set to non-default values:

- `save_credentials`: "Storing credentials in config is not recommended"
- `allow_agent_control`: "Allowing agent control is a security risk"
- `allow_external_api`: "Allowing external API calls bypasses local-only safety"
- `long_phase_allowed_when_degraded`: "Running long phases while provider is degraded may cause unexpected failures"

## Doctor Checks

Run `harness copilot doctor` to verify:

- Python >= 3.10
- Git availability
- pytest availability
- OS detection (Linux / macOS / WSL2)
- opencode CLI
- Global config existence
- Runtime directory existence

## New Test Files (7)

| Test File | Tests |
|-----------|-------|
| `tests/test_config_schema.py` | Schema defaults, security keys, merge |
| `tests/test_config_loader.py` | YAML/JSON loading, defaults, error handling |
| `tests/test_config_resolution_priority.py` | Env overrides, CLI overrides, project > global |
| `tests/test_config_paths.py` | Global/project path resolution |
| `tests/test_config_validator.py` | Security warnings, mode validation, errors |
| `tests/test_runtime_doctor.py` | Python/Git/pytest/OS checks, doctor summary |
| `tests/test_runtime_version.py` | Git tag/commit, version formatting |
