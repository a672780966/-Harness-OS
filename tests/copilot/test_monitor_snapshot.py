"""Tests for monitor snapshot — project and loop state capture."""

import os
import tempfile
import pytest

from harness.copilot.monitor.snapshot import (
    capture_project_snapshot,
    capture_loop_snapshot,
    snapshot_diff,
    ProjectSnapshot,
)


class TestProjectSnapshot:
    def test_nonexistent_dir(self):
        snap = capture_project_snapshot("/nonexistent/path")
        assert "error" in snap.timestamp

    def test_git_branch(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        snap = capture_project_snapshot(repo_root)
        assert snap.git_branch
        assert snap.git_commit

    def test_git_status(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        snap = capture_project_snapshot(repo_root)
        assert isinstance(snap.git_status, list)
        assert isinstance(snap.uncommitted_count, int)

    def test_readonly_no_side_effects(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        before = set(os.listdir(repo_root))
        snap = capture_project_snapshot(repo_root)
        after = set(os.listdir(repo_root))
        # Should not create or delete files in project root
        assert before == after

    def test_file_hashes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mini git repo
            import subprocess
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True, timeout=5)
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("# hello")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True, timeout=5)

            snap = capture_project_snapshot(tmpdir)
            assert snap.uncommitted_count == 0

            # Modify file
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("# hello world")

            snap2 = capture_project_snapshot(tmpdir)
            assert snap2.uncommitted_count >= 1

    def test_default_fields(self):
        snap = ProjectSnapshot()
        assert snap.git_branch == ""
        assert snap.uncommitted_count == 0
        assert snap.file_hashes == {}


class TestLoopSnapshot:
    def test_nonexistent_dir(self):
        snap = capture_loop_snapshot("/nonexistent/loop")
        assert snap.timestamp

    def test_loop_artifacts(self):
        # Try a real loop run dir
        eval_base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            ".harness", "evaluations", "swebench_abc_mini_pilot_001", "runs",
        )
        run_dir = None
        if os.path.isdir(eval_base):
            for entry in os.listdir(eval_base):
                candidate = os.path.join(eval_base, entry, "tier_C_full")
                if os.path.isdir(candidate):
                    run_dir = candidate
                    break

        if not run_dir:
            pytest.skip("No loop run dir available")

        snap = capture_loop_snapshot(run_dir)
        assert snap.file_hashes
        # Should have found at least some artifact files
        assert len(snap.file_hashes) > 0


class TestSnapshotDiff:
    def test_no_changes(self):
        old = ProjectSnapshot(git_branch="main", git_commit="abc", git_status=["M file.py"])
        new = ProjectSnapshot(git_branch="main", git_commit="abc", git_status=["M file.py"])
        diffs = snapshot_diff(old, new)
        assert diffs == {}

    def test_branch_change(self):
        old = ProjectSnapshot(git_branch="main")
        new = ProjectSnapshot(git_branch="feature")
        diffs = snapshot_diff(old, new)
        assert "branch_changed" in diffs

    def test_status_change(self):
        old = ProjectSnapshot(git_status=["M a.py"], uncommitted_count=1)
        new = ProjectSnapshot(git_status=["M a.py", "M b.py"], uncommitted_count=2)
        diffs = snapshot_diff(old, new)
        assert "git_status_changed" in diffs

    def test_hash_change(self):
        old = ProjectSnapshot(file_hashes={"f.py": "aaaa"})
        new = ProjectSnapshot(file_hashes={"f.py": "bbbb"})
        diffs = snapshot_diff(old, new)
        assert "changed_files" in diffs

    def test_task_card_count_change(self):
        old = ProjectSnapshot(task_card_count=2, blocking_card_count=1)
        new = ProjectSnapshot(task_card_count=3, blocking_card_count=2)
        diffs = snapshot_diff(old, new)
        assert "task_cards_changed" in diffs
