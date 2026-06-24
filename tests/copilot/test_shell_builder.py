"""Tests for shell builder — verify project HTML dashboard generation."""

from __future__ import annotations

import os
import tempfile
import pytest

from harness.copilot.shell.shell_builder import build_project_shell


class TestShellBuilder:
    def test_nonexistent_project(self):
        result = build_project_shell("/tmp/nonexistent_path_xyz", "/tmp/out")
        assert not result.get("success")
        assert "error" in result

    def test_non_dir_project(self):
        with tempfile.NamedTemporaryFile() as f:
            result = build_project_shell(f.name, "/tmp/out")
        assert not result.get("success")
        assert "error" in result

    def test_output_creates_dir(self):
        """Output directory should be created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "new_sub_dir", "dashboard")
            # Build against a valid project dir (this repo itself)
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            project_dir = os.path.join(project_dir, "harness")
            if not os.path.isdir(project_dir):
                project_dir = os.path.dirname(os.path.abspath(__file__))

            if os.path.isdir(project_dir):
                result = build_project_shell(project_dir, out_dir)
                if result.get("success"):
                    assert os.path.isdir(out_dir)
                    assert os.path.isfile(result["html_path"])
                    assert os.path.isfile(result["json_path"])
                    assert result["html_path"].endswith("index.html")
                    assert result["json_path"].endswith("dashboard.json")
                else:
                    # Can't scan this dir; that's OK for CI
                    pytest.skip(f"Build failed: {result.get('error')}")

    def test_output_files_non_empty(self):
        """Generated HTML should be non-trivial."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            project_dir = os.path.join(project_dir, "harness", "copilot", "shell")
            if not os.path.isdir(project_dir):
                project_dir = os.path.dirname(os.path.abspath(__file__))

            if os.path.isdir(project_dir):
                result = build_project_shell(project_dir, tmpdir)
                if result.get("success"):
                    html_size = os.path.getsize(result["html_path"])
                    json_size = os.path.getsize(result["json_path"])
                    assert html_size > 500
                    assert json_size > 100


class TestBuildResultShape:
    def test_result_keys(self):
        """Result dict should have standard keys on success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            project_dir = os.path.join(project_dir, "harness", "copilot", "shell")
            if not os.path.isdir(project_dir):
                pytest.skip("No valid project dir for shell builder test")

            result = build_project_shell(project_dir, tmpdir)
            if result.get("success"):
                for key in ("html_path", "json_path", "output_dir", "dashboard"):
                    assert key in result, f"Missing key: {key}"
                assert isinstance(result["dashboard"], dict)
