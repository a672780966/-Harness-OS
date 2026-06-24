"""Integration tests — Loop artifacts → Dashboard end-to-end."""

import json
import os
import tempfile
from pathlib import Path

from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
from harness.copilot.integration.loop_to_copilot_mapper import artifacts_to_dashboard
from harness.copilot.markdown_renderer import render_dashboard
from harness.copilot.json_renderer import render_dashboard_json


class TestSyntheticLoopToDashboard:
    def _create_synthetic_loop(self, tmpdir: str, **overrides):
        """Create a synthetic loop run directory with default passing state."""
        base = Path(tmpdir, "runs", "django__django-12050", "tier_C_full")
        base.mkdir(parents=True)

        defaults = {
            "metrics.json": {
                "instance_id": "django__django-12050",
                "tier": "C",
                "eval_valid": True,
                "resolved_official": True,
                "codex_approved": True,
                "final_gate_passed": True,
                "merge_ready": True,
                "repair_rounds": 0,
                "patch_size_lines": 24,
                "files_changed": 1,
                "mock_used": False,
                "stop_reason": "real_loop_complete",
            },
            "eval_report.json": {
                "eval_valid": True,
                "tests_passed": 45,
                "tests_total": 45,
                "resolved_official": True,
                "generated_at": "2026-06-22T10:00:00",
            },
            "test_result.json": {
                "resolved_official": True,
                "tests_passed": 45,
                "tests_total": 45,
                "eval_valid": True,
            },
            "run_classification.json": {
                "classification": "success",
                "final_gate_passed": True,
                "merge_ready": True,
                "mock_used": False,
            },
            "final_gate_result.md": """# Final Gate Result

| Check | Status |
|-------|--------|
| eval_valid | ✅ | true |
| codex_approved | ✅ | true |

**Result**: ✅ FINAL GATE PASSED
**merge_ready**: true
""",
            "loop_report.md": "# Loop Report — django-12050\n\n## Summary\nFull real loop execution.\n\n## Phases\n| Phase | Duration | Status |\n|-------|----------|--------|\n| Planning | 0s | ✅ |\n| Implementation | 10s | ✅ |\n| Eval | 5s | ✅ |\n| Review | 2s | ✅ |\n| Final Gate | 1s | ✅ |\n\n## Key Findings\nAll tests passed.\n",
        }

        # Apply overrides
        for key, value in overrides.items():
            defaults[key] = value

        for filename, content in defaults.items():
            fp = base / filename
            if filename.endswith(".json"):
                fp.write_text(json.dumps(content))
            else:
                fp.write_text(str(content))

        return str(base)

    def test_loop_to_dashboard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = self._create_synthetic_loop(tmpdir)
            artifacts = load_loop_artifacts(run_dir)
            dashboard = artifacts_to_dashboard(artifacts)
            assert dashboard.project_name == "django__django-12050"
            assert dashboard.overall_risk_level == "low"
            assert dashboard.readiness is not None
            assert dashboard.readiness.is_ready is True

    def test_markdown_render(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = self._create_synthetic_loop(tmpdir)
            artifacts = load_loop_artifacts(run_dir)
            dashboard = artifacts_to_dashboard(artifacts)
            output = render_dashboard(dashboard)
            assert "django__django-12050" in output
            assert "可以合并" in output or "✅" in output

    def test_json_serializable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = self._create_synthetic_loop(tmpdir)
            artifacts = load_loop_artifacts(run_dir)
            dashboard = artifacts_to_dashboard(artifacts)
            output = render_dashboard_json(dashboard)
            parsed = json.loads(output)
            assert parsed["project_name"] == "django__django-12050"
            assert parsed["readiness"]["state"] == "pass"


class TestReviewRejectionFlow:
    def test_review_rejected_generates_repair_card(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir, "runs", "sphinx-doc__sphinx-7590", "tier_C_full")
            base.mkdir(parents=True)

            # Review rejected
            env_dir = Path(base, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps({
                "approved": False,
                "passed": False,
                "blocking_issues": [
                    {"severity": "high", "issue": "Parser can infinite-loop at end-of-input"}
                ],
                "summary": "Rejected. The change introduces a parser hang.",
                "reviewed_at": "2026-06-21T11:08:14+00:00",
            }))

            # Metrics
            (base / "metrics.json").write_text(json.dumps({
                "instance_id": "sphinx-doc__sphinx-7590",
                "codex_approved": False,
                "final_gate_passed": False,
                "eval_valid": True,
                "stop_reason": "codex_final_review_rejected",
                "repair_rounds": 0,
            }))

            (base / "run_classification.json").write_text(json.dumps({
                "classification": "needs_repair",
                "stop_reason": "codex_final_review_rejected",
            }))

            artifacts = load_loop_artifacts(str(base))
            dashboard = artifacts_to_dashboard(artifacts)

            # Check that task cards contain a review repair card
            assert dashboard.task_cards is not None
            assert len(dashboard.task_cards.cards) >= 1

            # Check readiness is blocked
            assert dashboard.readiness is not None
            assert dashboard.readiness.is_blocked is True
            assert dashboard.readiness.is_ready is False


class TestEvalFailureFlow:
    def test_eval_failure_generates_repair_card(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir, "runs", "django__django-11848", "tier_A")
            base.mkdir(parents=True)

            (base / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "tests_passed": 42,
                "tests_total": 45,
                "tests_failed": 3,
                "resolved_official": False,
            }))

            (base / "metrics.json").write_text(json.dumps({
                "instance_id": "django__django-11848",
                "eval_valid": True,
                "resolved_official": False,
                "final_gate_passed": False,
                "codex_approved": None,
            }))

            artifacts = load_loop_artifacts(str(base))
            dashboard = artifacts_to_dashboard(artifacts)

            # Check repair task card generated
            assert dashboard.task_cards is not None
            assert len(dashboard.task_cards.cards) >= 1

            # Check blocked readiness
            assert dashboard.readiness is not None
            assert dashboard.readiness.is_blocked is True


class TestFinalGateMergeReadiness:
    def test_gate_passed_readiness_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir, "runs", "test", "tier_C")
            base.mkdir(parents=True)

            (base / "metrics.json").write_text(json.dumps({
                "final_gate_passed": True,
                "codex_approved": True,
                "eval_valid": True,
                "merge_ready": True,
                "mock_used": False,
            }))

            artifacts = load_loop_artifacts(str(base))
            dashboard = artifacts_to_dashboard(artifacts)

            assert dashboard.readiness is not None
            assert dashboard.readiness.state == "pass"
            assert dashboard.readiness.is_ready is True

    def test_gate_not_passed_readiness_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir, "runs", "test", "tier_A")
            base.mkdir(parents=True)

            (base / "metrics.json").write_text(json.dumps({
                "final_gate_passed": False,
                "codex_approved": False,
                "eval_valid": False,
                "merge_ready": False,
            }))

            artifacts = load_loop_artifacts(str(base))
            dashboard = artifacts_to_dashboard(artifacts)

            assert dashboard.readiness is not None
            assert dashboard.readiness.state == "block"
            assert dashboard.readiness.is_blocked is True
