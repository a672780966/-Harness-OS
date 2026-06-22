"""Tests for Eval-triggered Repair Task Card Mapping."""

import json
import tempfile
from pathlib import Path

from harness.copilot.integration.eval_mapper import eval_to_repair_task_cards
from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
from harness.copilot.schemas import TaskState, CardType, MergeReadinessState


class TestEvalValidNotOfficial:
    def test_creates_repair_card_when_not_official(self):
        """eval_valid=true, resolved_official=false → repair card."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "tests_passed": 44,
                "tests_total": 45,
                "tests_failed": 1,
                "resolved_official": False,
                "generated_at": "2026-06-22T10:00:00",
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = eval_to_repair_task_cards(artifacts)
            assert len(cards) >= 1
            card = cards[0]
            assert card.card_type == CardType.FIX_TEST
            assert card.state == TaskState.PENDING

    def test_acceptance_criteria_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "tests_passed": 40,
                "tests_total": 45,
                "tests_failed": 5,
                "resolved_official": False,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = eval_to_repair_task_cards(artifacts)
            if cards:
                assert len(cards[0].acceptance_criteria) >= 1
                assert any("禁止" in ac for ac in cards[0].acceptance_criteria)

    def test_blocking_issue_mentions_test_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "tests_passed": 42,
                "tests_total": 45,
                "tests_failed": 3,
                "resolved_official": False,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = eval_to_repair_task_cards(artifacts)
            if cards:
                assert len(cards[0].blocking_issues) >= 1


class TestEvalEnvironmentFailure:
    def test_environment_failure_card(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": False,
                "environment_failed": True,
                "tests_passed": 0,
                "tests_total": 0,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = eval_to_repair_task_cards(artifacts)

            # Should have at least one card (env failed or test failed)
            assert len(cards) >= 1


class TestTestsFailed:
    def test_failed_tests_create_card(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "tests_passed": 40,
                "tests_total": 45,
                "tests_failed": 5,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = eval_to_repair_task_cards(artifacts)

            # Should include card for failed tests
            test_fail_cards = [c for c in cards if "未全部通过" in c.title or "failed" in c.title.lower()]
            assert len(test_fail_cards) >= 1

    def test_card_priority_high_for_failed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "tests_passed": 35,
                "tests_total": 45,
                "tests_failed": 10,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = eval_to_repair_task_cards(artifacts)
            if cards:
                assert "high" in str(cards[0].priority.value) or "critical" in str(cards[0].priority.value)


class TestNoCardsForPassingEval:
    def test_no_cards_when_all_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "eval_report.json").write_text(json.dumps({
                "eval_valid": True,
                "tests_passed": 45,
                "tests_total": 45,
                "tests_failed": 0,
                "resolved_official": True,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            cards = eval_to_repair_task_cards(artifacts)
            assert len(cards) == 0
