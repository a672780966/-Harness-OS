"""Tests for Review-triggered Repair Task Card Mapping."""

import json
import tempfile
from pathlib import Path

from harness.copilot.integration.review_mapper import review_to_repair_task_cards
from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
from harness.copilot.schemas import TaskState, CardType, Priority, MergeReadinessState


class TestReviewRejection:
    def test_rejected_creates_repair_card(self):
        """codex_approved=false → review repair card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps({
                "approved": False,
                "passed": False,
                "blocking_issues": [
                    {"severity": "high", "issue": "Infinite loop at end-of-input"}
                ],
                "summary": "Rejected due to parser hang",
                "reviewed_at": "2026-06-21T11:00:00",
            }))
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "codex_approved": False,
                "final_gate_passed": False,
                "stop_reason": "codex_final_review_rejected",
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = review_to_repair_task_cards(artifacts)
            assert len(cards) >= 1
            card = cards[0]
            assert card.card_type == CardType.FIX_REVIEW
            assert card.priority == Priority.CRITICAL
            assert card.state == TaskState.PENDING

    def test_card_contains_rejection_reason(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps({
                "approved": False,
                "blocking_issues": [
                    {"severity": "high", "issue": "The patch introduces a crash when parsing numbers"}
                ],
                "summary": "Rejected",
            }))
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "codex_approved": False,
                "final_gate_passed": False,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = review_to_repair_task_cards(artifacts)
            if cards:
                assert "crash" in cards[0].description or "Rejected" in cards[0].description
                assert len(cards[0].blocking_issues) >= 1

    def test_card_has_acceptance_criteria(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps({
                "approved": False,
                "blocking_issues": [],
                "summary": "Rejected",
            }))
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "codex_approved": False,
                "final_gate_passed": False,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = review_to_repair_task_cards(artifacts)
            if cards:
                # Must include re-eval and re-review acceptance
                criteria_text = " ".join(cards[0].acceptance_criteria)
                assert "eval" in criteria_text or "评估" in criteria_text
                assert "review" in criteria_text or "审查" in criteria_text
                assert "禁止" in criteria_text or "限制" in criteria_text

    def test_card_blocked_for_merge(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps({
                "approved": False,
                "blocking_issues": [{"issue": "Critical bug"}],
                "summary": "Rejected",
            }))
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "codex_approved": False,
                "final_gate_passed": False,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = review_to_repair_task_cards(artifacts)
            if cards:
                assert cards[0].merge_readiness == MergeReadinessState.BLOCK


class TestReviewApproved:
    def test_approved_no_cards(self):
        """codex_approved=true → no repair cards."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps({
                "approved": True,
                "blocking_issues": [],
                "summary": "Approved",
            }))
            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "codex_approved": True,
                "final_gate_passed": True,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = review_to_repair_task_cards(artifacts)
            assert len(cards) == 0


class TestReviewNoData:
    def test_no_review_data_no_cards(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = load_loop_artifacts(tmpdir)
            cards = review_to_repair_task_cards(artifacts)
            assert len(cards) == 0
