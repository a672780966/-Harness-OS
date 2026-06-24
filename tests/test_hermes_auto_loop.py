"""Tests for Hermes Auto Node Loop Runner."""
from pathlib import Path
import subprocess
import sys
import json
import tempfile
import os

ROOT = Path(__file__).resolve().parents[1]
AUTO_LOOP = ROOT / ".harness/scripts/hermes_auto_loop.py"
HERMES_PY = ROOT / ".harness/scripts/hermes.py"


def run(cmd, cwd=None):
    return subprocess.run(
        cmd,
        cwd=cwd or str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_auto_loop_script_exists():
    assert AUTO_LOOP.exists(), f"AUTO_LOOP script not found at {AUTO_LOOP}"


def test_run_command_exists():
    proc = run([sys.executable, str(AUTO_LOOP), "--help"])
    assert proc.returncode == 0
    assert "run" in proc.stdout


def test_status_command_exists():
    proc = run([sys.executable, str(AUTO_LOOP), "--help"])
    assert "status" in proc.stdout


def test_stop_reason_command_exists():
    proc = run([sys.executable, str(AUTO_LOOP), "--help"])
    assert "stop-reason" in proc.stdout


def test_run_requires_task_id():
    proc = run([sys.executable, str(AUTO_LOOP), "run"])
    assert proc.returncode != 0
    assert "required" in proc.stderr or "required" in proc.stdout


def test_status_requires_task_id():
    proc = run([sys.executable, str(AUTO_LOOP), "status"])
    assert proc.returncode != 0


def test_hermes_py_has_engineering_loop_run():
    """Verify engineering-loop-run is registered in hermes.py CLI."""
    content = HERMES_PY.read_text(encoding="utf-8")
    assert "engineering-loop-run" in content
    assert "engineering-loop-status" in content
    assert "engineering-loop-stop-reason" in content
    assert "AUTO_LOOP" in content


def test_run_fails_on_missing_worktree():
    """Verify run fails gracefully on non-existent task."""
    proc = run([
        sys.executable, str(AUTO_LOOP), "run",
        "--task-id", "task_nonexistent_fake_001",
    ])
    assert proc.returncode != 0


def test_status_on_nonexistent_task():
    """Verify status fails on non-existent task."""
    proc = run([
        sys.executable, str(AUTO_LOOP), "status",
        "--task-id", "task_nonexistent_fake_001",
    ])
    assert proc.returncode != 0


def test_stop_reason_on_nonexistent_task():
    """Verify stop-reason fails on non-existent task."""
    proc = run([
        sys.executable, str(AUTO_LOOP), "stop-reason",
        "--task-id", "task_nonexistent_fake_001",
    ])
    assert proc.returncode != 0


def test_hermes_py_cli_engineering_commands():
    """Verify engineering-loop CLI commands can be invoked via hermes.py."""
    proc = run([sys.executable, str(HERMES_PY), "--help"])
    assert proc.returncode == 0
    assert "engineering-loop-run" in proc.stdout
    assert "engineering-loop-status" in proc.stdout
    assert "engineering-loop-stop-reason" in proc.stdout
