from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_claude_worker_files_exist():
    assert (ROOT / ".harness/config/claude_worker.yaml").exists()
    assert (ROOT / ".harness/scripts/hermes_claude_worker.py").exists()
    assert (ROOT / ".harness/workers/claude-code/README.md").exists()


def test_claude_worker_help():
    proc = run([sys.executable, ".harness/scripts/hermes_claude_worker.py", "--help"])
    assert proc.returncode == 0
    assert "Hermes Claude Code Worker Adapter" in proc.stdout


def test_claude_worker_config_valid_yaml():
    import yaml
    with (ROOT / ".harness/config/claude_worker.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["worker"]["id"] == "claude_code_worker"
    assert "mock" in data["execution"]["allowed_modes"]
    assert "manual" in data["execution"]["allowed_modes"]
    assert "execute" in data["execution"]["allowed_modes"]

    # Cloud sandbox dev: execute mode is enabled by default.
    assert data["execution"]["execute_mode_default_enabled"] is True

    # Hard deny flags must remain in place.
    assert data["safety"]["forbid_push"] is True
    assert data["safety"]["forbid_merge"] is True
    assert data["safety"]["forbid_deploy"] is True
    assert data["safety"]["require_worktree_safe"] is True
    assert data["safety"]["require_result_envelope"] is True

    # Permission gate must be present and strict.
    assert data["permission"]["required_profile"] == "cloud_sandbox_dev"
    assert data["permission"]["require_permission_preflight"] is True
    assert data["permission"]["fail_on_missing_permission"] is True
