"""Tests: risk classifier deduplication and merge readiness stability.

Verifies:
- Same risk alert does not generate duplicate blocking issues
- priority/level mixed fields don't cause duplication
- Different risk types still generate separate blocking issues
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.copilot.schemas import (
    CardType,
    MergeReadinessState,
    RiskAlert,
    RiskLevel,
    TaskCard,
    TaskState,
    Priority,
    Source,
    now_iso,
    generate_id,
)
from harness.copilot.merge_readiness import evaluate_merge_readiness
from harness.copilot.task_card import from_risk_alerts


def _make_alert(title: str, module: str, level: RiskLevel,
                is_blocking: bool = True) -> RiskAlert:
    return RiskAlert(
        alert_id=generate_id("risk"),
        title=title,
        level=level,
        module=module,
        file_path=f"some/{module}/file.py",
        description=f"Risk: {title}",
        recommendation="Review",
        is_blocking=is_blocking,
        created_at=now_iso(),
    )


def _make_card(title: str, blocking: bool = False) -> TaskCard:
    return TaskCard(
        card_id=generate_id("risk"),
        title=title,
        card_type=CardType.RISK_ALERT,
        state=TaskState.PENDING,
        priority=Priority.HIGH,
        source=Source.LOOP_KERNEL,
        module="test",
        description=f"Card: {title}",
        acceptance_criteria=["Resolve"],
        merge_readiness=MergeReadinessState.BLOCK if blocking else MergeReadinessState.REVIEW_NEEDED,
        blocking_issues=[title] if blocking else [],
        created_at=now_iso(),
        updated_at=now_iso(),
    )


class TestRiskDeduplication:
    def test_duplicate_alert_no_duplicate_blocking(self):
        """Same alert appearing in both task cards and risk alerts
        generates only one blocking issue."""
        alerts = [
            _make_alert("High-risk changes in 'openclaw-plugins'", "openclaw-plugins", RiskLevel.HIGH),
        ]
        cards = from_risk_alerts(alerts)
        mr = evaluate_merge_readiness(task_cards=cards, risk_alerts=alerts)
        issues = [i for i in mr.blocking_issues if "openclaw-plugins" in i]
        assert len(issues) == 1, (
            f"Expected 1 blocking issue for 'openclaw-plugins', got {len(issues)}: {issues}"
        )

    def test_priority_and_level_not_duplicated(self):
        """Blocking issue for same module doesn't appear both as
        (priority=high) and (level=high)."""
        alerts = [
            _make_alert("High-risk changes in 'scripts'", "scripts", RiskLevel.HIGH),
        ]
        cards = from_risk_alerts(alerts)
        mr = evaluate_merge_readiness(task_cards=cards, risk_alerts=alerts)
        # Should have exactly 1 scripts-related blocking issue
        scripts_issues = [i for i in mr.blocking_issues if "scripts" in i]
        assert len(scripts_issues) == 1, (
            f"Expected 1 scripts issue, got {len(scripts_issues)}: {scripts_issues}"
        )

    def test_different_risks_retained(self):
        """Two genuinely different risks should each produce their own blocking issue."""
        alerts = [
            _make_alert("High-risk changes in 'openclaw-plugins'", "openclaw-plugins", RiskLevel.HIGH),
            _make_alert("Critical: verify-deploy.sh", "scripts", RiskLevel.CRITICAL),
        ]
        cards = from_risk_alerts(alerts)
        mr = evaluate_merge_readiness(
            task_cards=cards, risk_alerts=alerts,
            tests_passed=True,  # avoid "Test results not yet available" noise
        )
        risk_issues = [i for i in mr.blocking_issues if "BLOCKED" in i]
        assert len(risk_issues) == 2, (
            f"Expected 2 distinct blocking issues, got {len(risk_issues)}: {risk_issues}"
        )

    def test_same_title_different_module_not_deduped(self):
        """Same alert title in different modules are separate risks."""
        alerts = [
            _make_alert("High-risk changes in 'openclaw-plugins'", "openclaw-plugins", RiskLevel.HIGH),
            _make_alert("High-risk changes in 'scripts'", "scripts", RiskLevel.HIGH),
        ]
        cards = from_risk_alerts(alerts)
        mr = evaluate_merge_readiness(
            task_cards=cards, risk_alerts=alerts,
            tests_passed=True,
        )
        risk_issues = [i for i in mr.blocking_issues if "BLOCKED" in i]
        assert len(risk_issues) == 2

    def test_duplicate_across_cards_and_alerts(self):
        """When same risk produces both a TaskCard blocking issue
        AND a RiskAlert, only one blocking issue appears."""
        alert = _make_alert("Critical: verify-deploy.sh", "scripts", RiskLevel.CRITICAL)
        card = _make_card("Critical: verify-deploy.sh", blocking=True)
        mr = evaluate_merge_readiness(
            task_cards=[card],
            risk_alerts=[alert],
        )
        verify_issues = [i for i in mr.blocking_issues if "verify-deploy" in i]
        assert len(verify_issues) == 1, (
            f"Expected 1 verify-deploy issue, got {len(verify_issues)}: {verify_issues}"
        )
