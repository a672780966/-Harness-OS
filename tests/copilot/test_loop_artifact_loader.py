"""Tests for Loop Artifact Loader — loads real and synthetic artifacts."""

import json
import os
import tempfile
from pathlib import Path

from harness.copilot.integration.loop_artifact_loader import (
    load_loop_artifacts,
    LoopArtifacts,
)


class TestLoadEmptyDirectory:
    def test_nonexistent_dir(self):
        artifacts = load_loop_artifacts("/nonexistent/path")
        assert len(artifacts.load_errors) == 1
        assert artifacts.eval_report is None

    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = load_loop_artifacts(tmpdir)
            assert artifacts.eval_report is None
            assert artifacts.loop_report is None
            assert artifacts.repair_rounds == []


class TestLoadWithRealData:
    def test_load_django_11885_tier_c(self):
        """Load a real loop run directory."""
        run_dir = os.path.join(
            os.path.dirname(__file__), "..", "..",
            ".harness/evaluations/swebench_abc_mini_pilot_001",
            "runs/django__django-11885/tier_C_full",
        )
        if not os.path.isdir(run_dir):
            pytest.skip("Real loop dir not found")

        artifacts = load_loop_artifacts(run_dir)
        assert artifacts.instance_id == "django__django-11885"
        assert artifacts.eval_report is not None
        assert artifacts.metrics is not None
        assert artifacts.metrics.get("eval_valid") is True
        assert artifacts.loop_report is not None
        assert len(artifacts.repair_rounds) >= 0

    def test_load_sphinx_7590_tier_c(self):
        """Load sphinx-7590 review rejection artifacts."""
        run_dir = os.path.join(
            os.path.dirname(__file__), "..", "..",
            ".harness/evaluations/swebench_abc_mini_pilot_001",
            "runs/sphinx-doc__sphinx-7590/tier_C_full",
        )
        if not os.path.isdir(run_dir):
            pytest.skip("Real loop dir not found")

        artifacts = load_loop_artifacts(run_dir)
        if artifacts.final_review_envelope:
            assert "passed" in artifacts.final_review_envelope or "approved" in artifacts.final_review_envelope


class TestLoadArtifactTypes:
    def test_load_eval_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = {
                "eval_valid": True,
                "tests_passed": 45,
                "tests_total": 45,
                "resolved_official": True,
            }
            Path(tmpdir, "eval_report.json").write_text(json.dumps(report))
            artifacts = load_loop_artifacts(tmpdir)
            assert artifacts.eval_report["eval_valid"] is True
            assert artifacts.eval_report["tests_passed"] == 45

    def test_load_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = {
                "instance_id": "django__django-11885",
                "final_gate_passed": True,
                "codex_approved": True,
                "repair_rounds": 1,
            }
            Path(tmpdir, "metrics.json").write_text(json.dumps(metrics))
            artifacts = load_loop_artifacts(tmpdir)
            assert artifacts.metrics["final_gate_passed"] is True
            # instance_id may come from path or metrics — check metrics directly
            assert artifacts.metrics["instance_id"] == "django__django-11885"

    def test_load_loop_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = "# Loop Report\n\n## Summary\nTest execution completed.\n\n## Phases\n| Phase | Status |\n|-------|--------|\n| Eval | ✅ |\n"
            Path(tmpdir, "loop_report.md").write_text(report)
            artifacts = load_loop_artifacts(tmpdir)
            assert artifacts.loop_report is not None
            assert "Loop Report" in artifacts.loop_report

    def test_load_review_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            envelope = {
                "approved": False,
                "blocking_issues": [{"severity": "high", "issue": "Parser hangs"}],
                "summary": "Rejected due to infinite loop",
            }
            env_dir = Path(tmpdir, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps(envelope))
            artifacts = load_loop_artifacts(tmpdir)
            assert artifacts.final_review_envelope is not None
            assert artifacts.final_review_envelope["approved"] is False

    def test_load_repair_rounds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repair_dir = Path(tmpdir, "repair_rounds", "round_1")
            repair_dir.mkdir(parents=True)
            (repair_dir / "patch_repair.diff").write_text("--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n")
            (repair_dir / "repair_stdout.log").write_text("Repair completed\n")
            (repair_dir / "test_result.json").write_text(json.dumps({"tests_passed": 44, "tests_total": 45}))

            artifacts = load_loop_artifacts(tmpdir)
            assert len(artifacts.repair_rounds) == 1
            assert artifacts.repair_rounds[0]["round_name"] == "round_1"

    def test_load_final_gate_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gate_md = """# Final Gate Result

| Check | Status |
|-------|--------|
| eval_valid | ✅ | true |
| codex_approved | ✅ | true |

**Result**: ✅ FINAL GATE PASSED
**merge_ready**: true
"""
            Path(tmpdir, "final_gate_result.md").write_text(gate_md)
            artifacts = load_loop_artifacts(tmpdir)
            assert artifacts.final_gate_result is not None
            assert artifacts.final_gate_result.get("merge_ready") is True

    def test_load_patch_diff(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            diff = "diff --git a/file.py b/file.py\nindex abc..def\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n"
            Path(tmpdir, "patch.diff").write_text(diff)
            artifacts = load_loop_artifacts(tmpdir)
            assert artifacts.patch_diff is not None
            assert "file.py" in artifacts.patch_diff


class TestLoopArtifactsDefault:
    def test_default_instance_id(self):
        la = LoopArtifacts(run_dir="/tmp")
        assert la.run_dir == "/tmp"
        assert la.load_errors == []
        assert la.repair_rounds == []
        assert la.review_repair_rounds == []


# Needed for skipif
import pytest
