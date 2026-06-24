"""Tests for Task Card Generator."""

from harness.copilot.task_card import (
    from_risk_alerts,
    from_change_explanations,
    from_suggestions,
    from_verification,
    generate_summary,
)
from harness.copilot.schemas import (
    RiskAlert, RiskLevel, CardType, TaskState, Priority,
    RecentChangeExplanation, ChangeSuggestion, MergeReadinessState,
)


class TestFromRiskAlerts:
    def test_empty_alerts(self):
        cards = from_risk_alerts([])
        assert cards == []

    def test_critical_alert(self):
        alerts = [
            RiskAlert(
                alert_id="r1", title="Critical issue",
                level=RiskLevel.CRITICAL, is_blocking=True,
                created_at="now",
            )
        ]
        cards = from_risk_alerts(alerts)
        assert len(cards) == 1
        assert cards[0].card_type == CardType.RISK_ALERT
        assert cards[0].priority == Priority.CRITICAL
        assert cards[0].merge_readiness == MergeReadinessState.BLOCK

    def test_high_alert(self):
        alerts = [
            RiskAlert(
                alert_id="r2", title="High risk",
                level=RiskLevel.HIGH, is_blocking=False,
                created_at="now",
            )
        ]
        cards = from_risk_alerts(alerts)
        assert len(cards) == 1
        assert cards[0].priority == Priority.HIGH
        assert cards[0].merge_readiness == MergeReadinessState.REVIEW_NEEDED

    def test_alert_with_file_path(self):
        alerts = [
            RiskAlert(
                alert_id="r3", title="Secret in config",
                level=RiskLevel.CRITICAL,
                file_path="config/.env",
                is_blocking=True,
                created_at="now",
            )
        ]
        cards = from_risk_alerts(alerts)
        assert cards[0].target_file == "config/.env"

    def test_multiple_alerts_max_cards(self):
        alerts = [
            RiskAlert(alert_id=f"r{i}", title=f"Alert {i}",
                      level=RiskLevel.MEDIUM, created_at="now")
            for i in range(20)
        ]
        cards = from_risk_alerts(alerts, max_cards=5)
        assert len(cards) == 5


class TestFromChangeExplanations:
    def test_empty(self):
        cards = from_change_explanations([])
        assert cards == []

    def test_single_explanation(self):
        exps = [
            RecentChangeExplanation(
                module="auth",
                summary="Added login feature (+50/-0 lines)",
                files_changed=["auth/views.py", "auth/models.py"],
                lines_added=50,
                lines_removed=0,
                intent="Add user login",
            )
        ]
        cards = from_change_explanations(exps)
        assert len(cards) == 1
        assert cards[0].card_type == CardType.FIX_REVIEW
        assert cards[0].module == "auth"

    def test_explanation_with_risks(self):
        exps = [
            RecentChangeExplanation(
                module="config",
                summary="Changed .env",
                files_changed=["config/.env"],
                lines_added=2,
                lines_removed=1,
                intent="Update config",
                risks=[".env contains secrets"],
            )
        ]
        cards = from_change_explanations(exps)
        assert cards[0].priority == Priority.HIGH  # Has risks


class TestFromSuggestions:
    def test_empty(self):
        cards = from_suggestions([])
        assert cards == []

    def test_suggestion(self):
        sugs = [
            ChangeSuggestion(
                file_path="src/main.py",
                function="login",
                module="auth",
                suggestion="Add input validation",
                reason="Missing validation",
                confidence=0.85,
                priority=Priority.HIGH,
            )
        ]
        cards = from_suggestions(sugs)
        assert len(cards) == 1
        assert cards[0].card_type == CardType.CODE_CHANGE
        assert cards[0].priority == Priority.HIGH

    def test_test_suggestion(self):
        sugs = [
            ChangeSuggestion(
                file_path="src/main.py",
                suggestion="Add tests for main module",
                reason="No test coverage",
                confidence=0.7,
                priority=Priority.MEDIUM,
            )
        ]
        cards = from_suggestions(sugs)
        assert cards[0].card_type == CardType.FIX_TEST  # "test" in suggestion


class TestFromVerification:
    def test_failed_test(self):
        card = from_verification("test_login", "failed", module="auth")
        assert card.card_type == CardType.FIX_TEST
        assert card.priority == Priority.HIGH
        assert card.state == TaskState.PENDING
        assert card.merge_readiness == MergeReadinessState.BLOCK

    def test_passed_test(self):
        card = from_verification("test_login", "passed", module="auth")
        assert card.card_type == CardType.EVIDENCE
        assert card.state == TaskState.COMPLETED
        assert card.merge_readiness == MergeReadinessState.PASS
        assert card.priority == Priority.LOW


class TestGenerateSummary:
    def test_empty_cards(self):
        summary = generate_summary([])
        assert summary["total_cards"] == 0
        assert summary["blocking_count"] == 0

    def test_with_cards(self):
        from harness.copilot.task_card import from_risk_alerts
        alerts = [
            RiskAlert(alert_id="r1", title="Blocking", level=RiskLevel.CRITICAL,
                      is_blocking=True, created_at="now"),
            RiskAlert(alert_id="r2", title="Non-blocking", level=RiskLevel.LOW,
                      is_blocking=False, created_at="now"),
        ]
        cards = from_risk_alerts(alerts)
        summary = generate_summary(cards)
        assert summary["total_cards"] == 2
        assert summary["blocking_count"] >= 1
        assert "pending" in summary["summary_line"]
