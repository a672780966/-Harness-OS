# Harness Copilot v1.3 Install Baseline

## Prerequisites

- **Python** >= 3.10 (tested on 3.11.15)
- **Git** (for version detection, project operations)
- **pytest** (for running tests)

## Installation

### 1. Clone the repository

```bash
git clone <repo-url> -Harness-OS
cd -Harness-OS
```

### 2. Set up virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### 3. Install dependencies

```bash
pip install -e .
# or for development:
pip install -e ".[dev]"
```

### 4. Initialize default config

```bash
harness copilot config init
```

This creates `~/.harness/config.yaml` with secure defaults:
- Read-only mode
- No external API access
- No credential storage
- No agent control

### 5. Run doctor

```bash
harness copilot doctor
```

Verify all prerequisite checks pass (Python, Git, pytest, OS detection).

## Configuration Files

| File | Purpose | Created By |
|------|---------|------------|
| `~/.harness/config.yaml` | Global user config | `harness config init` |
| `<project>/.harness/config.yaml` | Per-project overrides | Manual |
| `~/.harness/runtime/` | Runtime state directory | Auto |

## Verification

```bash
# Show effective configuration
harness copilot config show

# Validate for safety
harness copilot config validate

# Show config file paths
harness copilot config path

# Check version
harness copilot version
```

## Project-Level Config Example

Place at `<project-root>/.harness/config.yaml`:

```yaml
version: 1
provider:
  mode: fallback
  canary_timeout_seconds: 60
runtime:
  readonly_default: false
copilot:
  default_format: json
```

This merges on top of the global config, with project values taking priority.

## Running Tests

```bash
# All tests
pytest tests/

# Config-specific tests
pytest tests/test_config_*.py

# Runtime-specific tests
pytest tests/test_runtime_*.py
```

## OS Support

| OS | Status | Notes |
|----|--------|-------|
| Linux | ✅ Full | Primary development target |
| macOS | ✅ Supported | Untested in CI |
| WSL2 | ✅ Detected | Doctor reports as wsl2 |
| Windows (native) | ⚠️ Partial | Doctor reports as windows-native, WSL2 recommended |
