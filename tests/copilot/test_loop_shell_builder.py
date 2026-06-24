"""Tests for loop shell builder — verify from-loop HTML dashboard generation."""

from __future__ import annotations

import os
import tempfile
import pytest

from harness.copilot.shell.loop_shell_builder import build_loop_shell


class TestLoopShellBuilder:
    def test_nonexistent_run_dir(self):
        result = build_loop_shell("/tmp/nonexistent_loop_run", "/tmp/out")
        assert not result.get("success")
        assert "error" in result

    def test_non_dir_run(self):
        with tempfile.NamedTemporaryFile() as f:
            result = build_loop_shell(f.name, "/tmp/out")
        assert not result.get("success")
        assert "error" in result

    def test_output_structure(self):
        """With valid loop artifacts, verify correct output."""
        # Find a known valid loop run directory
        eval_base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            ".harness", "evaluations", "swebench_abc_mini_pilot_001", "runs",
        )

        # Look for any tier_C_full dir
        run_dir = None
        if os.path.isdir(eval_base):
            for entry in os.listdir(eval_base):
                candidate = os.path.join(eval_base, entry, "tier_C_full")
                if os.path.isdir(candidate):
                    run_dir = candidate
                    break

        if not run_dir:
            # Fall back to checking if exists
            run_dir = os.path.join(eval_base, "django__django-11885", "tier_C_full")
            if not os.path.isdir(run_dir):
                run_dir = os.path.join(eval_base, "django__django-12050", "tier_C_full")
                if not os.path.isdir(run_dir):
                    pytest.skip("No valid loop run directory found")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_loop_shell(run_dir, tmpdir)
            assert result.get("success"), f"Failed: {result.get('error')}"
            assert os.path.isfile(result["html_path"])
            assert os.path.isfile(result["json_path"])
            assert result["html_path"].endswith("index.html")

            # Verify HTML content
            with open(result["html_path"], "r") as f:
                html = f.read()
            assert "<!DOCTYPE html>" in html
            assert "Loop详情" in html or "Copilot" in html

            # Verify JSON content
            with open(result["json_path"], "r") as f:
                import json
                data = json.load(f)
            assert isinstance(data, dict)
            assert "project_name" in data
