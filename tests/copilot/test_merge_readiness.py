"""Tests for Merge Readiness Evaluator."""

from harness.copilot.merge_readiness import (
    evaluate_merge_readiness,
    merge_readiness_to_dict,
)
from harness.copilot.schemas import (
    TaskCard, CardType, TaskState, Priority, Source,
    MergeReadinessState, RiskAlert, RiskLevel,
)


class TestEvaluateMergeReadiness:
    def test_pass_no_issues(self):
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=[],
            tests_passed=True,
            codex_approved=True,
        )
        assert mr.state == MergeReadinessState.PASS
        assert mr.blocking_issues == []
        assert mr.tests_passed is True

    def test_blocked_by_tests(self):
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=[],
            tests_passed=False,
        )
        assert mr.state == MergeReadinessState.REVIEW_NEEDED
        assert any("failing" in i.lower() for i in mr.blocking_issues)

    def test_blocked_by_risk_alert(self):
        alerts = [
            RiskAlert(
                alert_id="r1", title="Critical security issue",
                level=RiskLevel.CRITICAL, is_blocking=True,
                created_at="now",
            )
        ]
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=alerts,
            tests_passed=True,
        )
        assert mr.state == MergeReadinessState.BLOCK
        assert any("BLOCKED" in i for i in mr.blocking_issues)

    def test_blocked_by_pending_task(self):
        cards = [
            TaskCard(
                card_id="c1", title="Fix critical bug",
                card_type=CardType.FIX_TEST,
                state=TaskState.IN_PROGRESS,
                priority=Priority.CRITICAL,
                source=Source.EVAL,
                merge_readiness=MergeReadinessState.BLOCK,
            )
        ]
        mr = evaluate_merge_readiness(
            task_cards=cards,
            risk_alerts=[],
            tests_passed=True,
        )
        assert mr.state == MergeReadinessState.BLOCK

    def test_review_needed_no_codex(self):
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=[],
            tests_passed=True,
            codex_approved=None,
        )
        assert mr.state == MergeReadinessState.REVIEW_NEEDED
        assert mr.review_required is True

    def test_codex_rejected(self):
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=[],
            tests_passed=True,
            codex_approved=False,
        )
        assert mr.review_required is True

    def test_high_risk_changes_recorded(self):
        cards = [
            TaskCard(
                card_id="c1", title="Auth change",
                card_type=CardType.CODE_CHANGE,
                state=TaskState.PENDING,
                priority=Priority.HIGH,
                source=Source.LOOP_KERNEL,
                target_file="src/auth/login.py",
                risk_score=0.8,
                merge_readiness=MergeReadinessState.REVIEW_NEEDED,
            )
        ]
        mr = evaluate_merge_readiness(
            task_cards=cards,
            risk_alerts=[],
            tests_passed=True,
        )
        assert "src/auth/login.py" in mr.high_risk_changes

    def test_pending_cards_counted(self):
        cards = [
            TaskCard(card_id="c1", title="Task 1", card_type=CardType.CODE_CHANGE,
                     state=TaskState.PENDING, priority=Priority.MEDIUM,
                     source=Source.LOOP_KERNEL),
            TaskCard(card_id="c2", title="Task 2", card_type=CardType.CODE_CHANGE,
                     state=TaskState.COMPLETED, priority=Priority.MEDIUM,
                     source=Source.LOOP_KERNEL),
        ]
        mr = evaluate_merge_readiness(cards, [])
        assert mr.pending_task_cards == 1

    def test_all_pass_full_flow(self):
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=[],
            tests_passed=True,
            codex_approved=True,
            branch_name="feature/test",
        )
        assert mr.state == MergeReadinessState.PASS
        assert "pass" in mr.summary.lower()

    def test_non_blocking_issues_still_review(self):
        """Non-blocking issues should set REVIEW_NEEDED."""
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=[],
            tests_passed=None,  # Not known
            codex_approved=None,
        )
        # Neither pass nor block — should be review_needed
        assert mr.state == MergeReadinessState.REVIEW_NEEDED


class TestMergeReadinessToDict:
    def test_dict_serialization(self):
        mr = evaluate_merge_readiness(
            task_cards=[],
            risk_alerts=[],
            tests_passed=True,
            codex_approved=True,
        )
        d = merge_readiness_to_dict(mr)
        assert "state" in d
        assert d["state"] == "pass"
        assert "blocking_issues" in d
        assert "summary" in d
        assert "evaluated_at" in d
