"""Tests for monitor readonly guarantee and monitor CLI registration."""

import os
import subprocess
import pytest

from harness.copilot.monitor import MonitorEvent
from harness.copilot.monitor.snapshot import capture_project_snapshot


class TestMonitorReadonly:
    def test_snapshot_does_not_modify_repo(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        before = set(os.listdir(repo_root))
        capture_project_snapshot(repo_root)
        after = set(os.listdir(repo_root))
        assert before == after

    def test_watcher_poll_does_not_create_files(self):
        """Watcher polling should not create files in project dir."""
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        before = set(os.listdir(repo_root))
        from harness.copilot.monitor.watcher import ProjectWatcher
        w = ProjectWatcher(repo_root)
        w.poll_once()
        after = set(os.listdir(repo_root))
        # Filter ephemeral __pycache__
        before_clean = {f for f in before if "__pycache__" not in f}
        after_clean = {f for f in after if "__pycache__" not in f}
        assert before_clean == after_clean

    def test_event_creation_no_side_effects(self):
        """Creating events should not touch filesystem."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            evt = MonitorEvent.create(
                event_type="test", severity="low", summary="test",
            )
            after = set(os.listdir(tmpdir))
            assert before == after
            assert evt.readonly is True

    def test_sealed_evidence_unchanged(self):
        """Verify sealed Mini Pilot evidence has no modifications."""
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sealed_path = os.path.join(
            repo_root, ".harness", "evaluations", "swebench_abc_mini_pilot_001",
        )
        if not os.path.isdir(sealed_path):
            pytest.skip("Sealed evidence dir not found")

        result = subprocess.run(
            ["git", "diff", "HEAD", "--", sealed_path],
            capture_output=True, text=True, timeout=10, cwd=repo_root,
        )
        assert result.stdout.strip() == "", f"Sealed evidence modified: {result.stdout}"


class TestMonitorCLI:
    def test_monitor_command_in_help(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run(
            ["python3", "harness/copilot/cli.py", "--help"],
            capture_output=True, text=True, timeout=10, cwd=repo_root,
        )
        assert "monitor" in result.stdout
        assert "monitor-loop" in result.stdout

    def test_monitor_command_registered(self):
        from harness.copilot.cli import cmd_monitor, cmd_monitor_loop
        assert callable(cmd_monitor)
        assert callable(cmd_monitor_loop)

    def test_monitor_has_once_flag(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run(
            ["python3", "harness/copilot/cli.py", "monitor", "--help"],
            capture_output=True, text=True, timeout=10, cwd=repo_root,
        )
        assert "--once" in result.stdout

    def test_monitor_loop_has_once_flag(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run(
            ["python3", "harness/copilot/cli.py", "monitor-loop", "--help"],
            capture_output=True, text=True, timeout=10, cwd=repo_root,
        )
        assert "--once" in result.stdout
