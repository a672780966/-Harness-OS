from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_permission_config_exists():
    assert (ROOT / ".harness/config/permissions.cloud_sandbox.yaml").exists()


def test_permission_preflight_script_exists():
    assert (ROOT / ".harness/scripts/hermes_permission_preflight.py").exists()


def test_permission_preflight_runs_for_hermes():
    proc = run([
        sys.executable,
        ".harness/scripts/hermes_permission_preflight.py",
        "--task-id", "task_permission_test_001",
        "--trace-id", "trace_permission_test_001",
        "--role", "hermes",
    ])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    assert data["passed"] is True
    assert data["report_ref"]


def test_permission_preflight_outputs_report():
    report = ROOT / ".harness/audit/logs/permissions/task_permission_test_001_hermes_permission_preflight_report.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "Permission Preflight Report" in text
