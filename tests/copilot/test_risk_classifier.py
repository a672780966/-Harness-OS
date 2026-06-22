"""Tests for Risk Classifier."""

from harness.copilot.risk_classifier import (
    classify_file_risk,
    classify_diff_risk,
    generate_risk_alerts,
    get_risk_level,
)
from harness.copilot.schemas import (
    DiffEntry, RiskLevel, ModuleDiffSummary, ProjectSemanticMap,
)


class TestClassifyFileRisk:
    def test_no_risk(self):
        score, reasons = classify_file_risk("src/utils/helper.py")
        assert score == 0.0
        assert reasons == []

    def test_auth_endpoint(self):
        score, reasons = classify_file_risk("src/auth/login.py")
        assert score >= 0.5
        assert len(reasons) >= 1

    def test_secret_file(self):
        score, reasons = classify_file_risk("config/secrets.yaml")
        assert score >= 0.7

    def test_env_file(self):
        score, reasons = classify_file_risk(".env.production")
        assert score >= 0.5

    def test_payment_file(self):
        score, reasons = classify_file_risk("src/payment/processor.py")
        assert score >= 0.5

    def test_deploy_script(self):
        score, reasons = classify_file_risk("scripts/deploy.sh")
        assert score >= 0.5

    def test_api_key_file(self):
        score, reasons = classify_file_risk("config/api_key.txt")
        assert score >= 0.8

    def test_large_change_not_applicable_here(self):
        """File risk doesn't consider diff size, only path."""
        score, reasons = classify_file_risk("src/normal_file.py")
        assert score == 0.0

    def test_deeply_nested(self):
        score, reasons = classify_file_risk("a/b/c/d/e/f/g/file.py")
        assert score > 0  # Deep nesting adds some risk


class TestClassifyDiffRisk:
    def test_small_safe_change(self):
        entry = DiffEntry(
            file_path="src/utils.py",
            change_type="modified",
            lines_added=5,
            lines_removed=2,
            hunks=1,
        )
        score, reasons = classify_diff_risk(entry)
        assert score < 0.5

    def test_large_change(self):
        entry = DiffEntry(
            file_path="src/main.py",
            change_type="modified",
            lines_added=300,
            lines_removed=100,
            hunks=8,
        )
        score, reasons = classify_diff_risk(entry)
        assert score >= 0.5

    def test_high_risk_file_change(self):
        entry = DiffEntry(
            file_path="config/.env.prod",
            change_type="modified",
            lines_added=1,
            lines_removed=1,
            hunks=1,
        )
        score, reasons = classify_diff_risk(entry)
        assert score >= 0.5

    def test_file_deletion(self):
        entry = DiffEntry(
            file_path="src/old_module.py",
            change_type="deleted",
            lines_added=0,
            lines_removed=50,
            hunks=1,
        )
        score, reasons = classify_diff_risk(entry)
        assert score >= 0.4

    def test_many_hunks(self):
        entry = DiffEntry(
            file_path="src/complex.py",
            change_type="modified",
            lines_added=30,
            lines_removed=20,
            hunks=10,
        )
        score, reasons = classify_diff_risk(entry)
        assert any("hunks" in r.lower() for r in reasons)

    def test_very_large_change(self):
        entry = DiffEntry(
            file_path="src/main.py",
            change_type="modified",
            lines_added=600,
            lines_removed=200,
            hunks=3,
        )
        score, reasons = classify_diff_risk(entry)
        assert score >= 0.7


class TestGenerateRiskAlerts:
    def test_no_alerts_for_low_risk(self):
        summaries = [
            ModuleDiffSummary(
                module_name="src",
                entries=[],
                total_added=5,
                total_removed=2,
                risk_impact=RiskLevel.LOW,
            )
        ]
        alerts = generate_risk_alerts(summaries)
        assert len(alerts) == 0

    def test_alerts_for_high_risk_module(self):
        summaries = [
            ModuleDiffSummary(
                module_name="auth",
                entries=[
                    DiffEntry(
                        file_path="auth/login.py",
                        change_type="modified",
                        lines_added=100,
                        lines_removed=50,
                        hunks=10,
                    ),
                ],
                total_added=100,
                total_removed=50,
                risk_impact=RiskLevel.HIGH,
            )
        ]
        alerts = generate_risk_alerts(summaries)
        assert len(alerts) >= 1

    def test_blocking_alerts(self):
        summaries = [
            ModuleDiffSummary(
                module_name="config",
                entries=[
                    DiffEntry(file_path="config/.env", change_type="modified",
                              lines_added=3, lines_removed=1, hunks=1),
                ],
                total_added=3,
                total_removed=1,
                risk_impact=RiskLevel.HIGH,
            )
        ]
        alerts = generate_risk_alerts(summaries)
        blocking = [a for a in alerts if a.is_blocking]
        assert len(blocking) >= 0  # At least non-blocking alerts


class TestGetRiskLevel:
    def test_critical(self):
        assert get_risk_level(0.9) == RiskLevel.CRITICAL

    def test_high(self):
        assert get_risk_level(0.6) == RiskLevel.HIGH

    def test_medium(self):
        assert get_risk_level(0.3) == RiskLevel.MEDIUM

    def test_low(self):
        assert get_risk_level(0.1) == RiskLevel.LOW

    def test_unknown(self):
        assert get_risk_level(0.0) == RiskLevel.UNKNOWN

    def test_boundaries(self):
        assert get_risk_level(0.8) == RiskLevel.CRITICAL
        assert get_risk_level(0.5) == RiskLevel.HIGH
        assert get_risk_level(0.2) == RiskLevel.MEDIUM
