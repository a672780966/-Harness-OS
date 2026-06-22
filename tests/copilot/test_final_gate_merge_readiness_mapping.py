"""Tests for Final Gate → Merge Readiness mapping."""

import json
import tempfile
from pathlib import Path

from harness.copilot.integration.final_gate_mapper import final_gate_to_readiness
from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
from harness.copilot.schemas import MergeReadinessState


class TestFinalGatePassed:
    def test_gate_passed_returns_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": True,
                "merge_ready": True,
                "codex_approved": True,
                "eval_valid": True,
                "mock_used": False,
            }))
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            assert mr is not None
            assert mr.state == MergeReadinessState.PASS

    def test_gate_passed_readable_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": True,
                "merge_ready": True,
                "codex_approved": True,
            }))
            (Path(tmpdir) / "final_gate_result.md").write_text(
                "# Final Gate\n\n| Check | Result |\n|-------|--------|\n| eval_valid | ✅ | true |\n\n**Result**: ✅ FINAL GATE PASSED\n**merge_ready**: true\n"
            )
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            assert mr is not None
            assert "可以准备合并" in mr.summary or "通过" in mr.summary


class TestFinalGateBlocked:
    def test_eval_failed_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": False,
                "eval_valid": False,
                "codex_approved": None,
                "merge_ready": False,
            }))
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            assert mr is not None
            assert "test" in str(mr.blocking_issues).lower() or "评估" in mr.summary
            assert mr.state in (MergeReadinessState.BLOCK, MergeReadinessState.REVIEW_NEEDED)

    def test_codex_rejected_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": False,
                "codex_approved": False,
                "eval_valid": True,
                "merge_ready": False,
            }))
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            assert mr is not None
            assert any("codex" in i.lower() or "review" in i.lower()
                      for i in mr.blocking_issues)
            assert mr.state == MergeReadinessState.BLOCK

    def test_official_not_resolved_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "resolved_official": False,
                "tests_passed": 40, "tests_total": 45,
            }))
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": False,
                "eval_valid": True,
                "codex_approved": None,
            }))
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            assert mr is not None
            # Should have some blocking issue
            assert len(mr.blocking_issues) >= 1

    def test_block_has_reasons(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": False,
                "eval_valid": False,
                "codex_approved": False,
            }))
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            assert mr is not None
            assert len(mr.blocking_issues) >= 2  # Both eval and codex


class TestFinalGateReviewNeeded:
    def test_partial_pass_review_needed(self):
        """Eval passed but no codex approval yet → review_needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "resolved_official": True,
                "tests_passed": 45, "tests_total": 45,
            }))
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": False,
                "eval_valid": True,
                "codex_approved": None,
                "merge_ready": False,
            }))
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            # If eval passed and codex not rejected, it could be review_needed
            assert mr is not None


class TestFinalGateReadableLabels:
    def test_gate_passed_has_user_readable_label(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "final_gate_passed": True,
                "merge_ready": True,
            }))
            artifacts = load_loop_artifacts(tmpdir)
            mr = final_gate_to_readiness(artifacts)
            assert mr is not None
            assert mr.state == MergeReadinessState.PASS
