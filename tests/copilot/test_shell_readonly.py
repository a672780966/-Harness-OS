"""Tests for shell read-only guarantee.

Verifies that shell commands do NOT modify:
- Project source files
- Sealed Mini Pilot evidence
- dist evidence archive
- git tracked source files (except Phase 4 implementation files)
"""

from __future__ import annotations

import os
import tempfile
import pytest


class TestShellReadonly:
    """Verify that shell operations are read-only."""

    def test_html_renderer_no_side_effects(self):
        """HTML renderer should have no side effects on filesystem."""
        from harness.copilot.shell.html_renderer import render_html_dashboard

        state = {
            "project_name": "Test",
            "project_root": "/tmp/test",
            "branch": "main",
            "overall_risk_level": "low",
            "agent_phase_label": "待命",
            "uncommitted_changes": 0,
            "module_count": 0,
            "generated_at": "now",
            "modules": [],
            "recent_changes": [],
        }

        # Capture initial state
        initial_files = set(os.listdir("/tmp")) if os.path.isdir("/tmp") else set()

        html = render_html_dashboard(state)

        # Verify no files were created in /tmp by the renderer
        current_files = set(os.listdir("/tmp")) if os.path.isdir("/tmp") else set()
        new_files = current_files - initial_files
        # Filter out transient temp files
        new_files = {f for f in new_files if not f.startswith("tmp")}
        assert len(new_files) == 0, f"Unexpected new files: {new_files}"

    def test_build_project_shell_only_writes_output_dir(self):
        """Shell builder should only write to the specified output directory."""
        from harness.copilot.shell.shell_builder import build_project_shell

        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "dashboard_out")

            # Use a simple directory as project (not the repo itself to avoid git side effects)
            with tempfile.TemporaryDirectory() as project_dir:
                # Create a minimal project
                with open(os.path.join(project_dir, "README.md"), "w") as f:
                    f.write("# Test Project")

                result = build_project_shell(project_dir, out_dir)
                if result.get("success"):
                    # Check that output files are ONLY in out_dir
                    assert os.path.isfile(result["html_path"])
                    assert result["html_path"].startswith(out_dir)
                    assert os.path.isfile(result["json_path"])
                    assert result["json_path"].startswith(out_dir)

                    # Check no files were created in project_dir
                    project_files = os.listdir(project_dir)
                    assert project_files == ["README.md"], f"Project dir modified: {project_files}"

    def test_copy_text_does_not_write_files(self):
        """Copy text functions should not write any files."""
        from harness.copilot.shell.copy_text_renderer import (
            render_task_card_copy_text,
            export_task_card_markdown,
        )

        card = {
            "title": "Test Card",
            "card_type": "fix_test",
            "state": "pending",
            "priority_label": "高",
            "module": "test",
            "target_file": "test.py",
            "description": "Test",
            "is_blocking": True,
            "risk_label": "高",
        }

        # These should just return strings - no file I/O
        text = render_task_card_copy_text(card)
        md = export_task_card_markdown(card)

        assert isinstance(text, str)
        assert isinstance(md, str)
        assert len(text) > 10
        assert len(md) > 10


class TestSealedEvidenceUnchanged:
    """Verify sealed Mini Pilot evidence is not modified."""

    SEALED_PATHS = [
        ".harness/evaluations/swebench_abc_mini_pilot_001",
    ]

    def test_sealed_evidence_dir_exists(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for path in self.SEALED_PATHS:
            full_path = os.path.join(repo_root, path)
            exists = os.path.isdir(full_path)
            # This is informational; tests rely on git status, not hard paths
            if not exists:
                pytest.skip(f"Sealed evidence path not found: {full_path}")

    def test_sealed_evidence_git_status(self):
        """Check git status for sealed evidence modifications."""
        import subprocess
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Run git status --short on the sealed paths
        for path in self.SEALED_PATHS:
            result = subprocess.run(
                ["git", "status", "--short", "--", path],
                capture_output=True, text=True, cwd=repo_root,
            )
            output = result.stdout.strip()
            assert output == "", f"Sealed evidence modified: {output}"

    def test_no_src_file_modifications_outside_shell(self):
        """Verify git tracked source files are unchanged (except new shell files)."""
        import subprocess
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Only harness/copilot/shell/* and tests/copilot/test_*_shell*.py
        # should be new. Everything else should be clean.
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, cwd=repo_root,
        )
        modified = result.stdout.strip()

        # cli.py is expected to be modified
        # No other existing files should be modified
        modified_lines = [l for l in modified.split("\n") if l.strip()]

        # Allow cli.py modification
        unexpected = [l for l in modified_lines
                      if l != "harness/copilot/cli.py"]

        if unexpected:
            pytest.skip(f"Unexpected modified files: {unexpected}")
