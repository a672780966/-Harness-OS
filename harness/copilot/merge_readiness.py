"""Merge Readiness — evaluate whether changes are ready to merge."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import (
    MergeReadiness,
    MergeReadinessState,
    TaskCard,
    RiskAlert,
    VerificationMethod,
    now_iso,
)


def evaluate_merge_readiness(
    task_cards: List[TaskCard],
    risk_alerts: List[RiskAlert],
    tests_passed: Optional[bool] = None,
    codex_approved: Optional[bool] = None,
    branch_name: Optional[str] = None,
) -> MergeReadiness:
    """Evaluate merge readiness from task cards, alerts, and test results."""
    blocking_issues: List[str] = []
    pending_cards = 0
    high_risk_files: List[str] = []
    review_required = False

    # Check task cards
    for card in task_cards:
        if card.state.value in ("pending", "in_progress"):
            pending_cards += 1
            if card.merge_readiness == MergeReadinessState.BLOCK:
                blocking_issues.append(
                    f"BLOCKED: {card.title} "
                    f"(priority={card.priority.value})"
                )

        if card.risk_score >= 0.7:
            if card.target_file:
                high_risk_files.append(card.target_file)

    # Check risk alerts
    for alert in risk_alerts:
        if alert.is_blocking:
            blocking_issues.append(
                f"BLOCKED: {alert.title} "
                f"(level={alert.level.value})"
            )
        if alert.file_path and alert.file_path not in high_risk_files:
            high_risk_files.append(alert.file_path)

    # Test results
    if tests_passed is False:
        blocking_issues.append("Tests are failing")
    elif tests_passed is None:
        review_required = True
        blocking_issues.append("Test results not yet available")

    # Codex approval
    if codex_approved is False:
        blocking_issues.append("Codex review rejected")
        review_required = True
    elif codex_approved is None:
        review_required = True
        blocking_issues.append("Codex approval pending")

    # Determine state
    if blocking_issues and any("BLOCKED" in i for i in blocking_issues):
        state = MergeReadinessState.BLOCK
    elif blocking_issues:
        # Non-blocking issues still require review
        state = MergeReadinessState.REVIEW_NEEDED
        review_required = True
    elif pending_cards > 0:
        state = MergeReadinessState.REVIEW_NEEDED
        review_required = True
    else:
        state = MergeReadinessState.PASS

    # Build summary
    summary_parts: List[str] = []
    if state == MergeReadinessState.PASS:
        summary_parts.append("All checks passed — ready to merge.")
    elif state == MergeReadinessState.BLOCK:
        summary_parts.append(f"Merge blocked: {len(blocking_issues)} blocking issue(s).")
    else:
        summary_parts.append("Merge requires review.")

    if pending_cards > 0:
        summary_parts.append(f"{pending_cards} task card(s) still pending.")
    if high_risk_files:
        summary_parts.append(f"{len(high_risk_files)} high-risk file(s) detected.")
    if review_required:
        summary_parts.append("Human review recommended.")

    return MergeReadiness(
        state=state,
        blocking_issues=blocking_issues,
        review_required=review_required,
        tests_passed=tests_passed,
        codex_approved=codex_approved,
        high_risk_changes=high_risk_files,
        pending_task_cards=pending_cards,
        summary=" ".join(summary_parts),
        evaluated_at=now_iso(),
    )


def merge_readiness_to_dict(mr: MergeReadiness) -> Dict[str, Any]:
    """Serialize MergeReadiness to a dict (for CLI output)."""
    return {
        "state": mr.state.value,
        "blocking_issues": mr.blocking_issues,
        "review_required": mr.review_required,
        "tests_passed": mr.tests_passed,
        "codex_approved": mr.codex_approved,
        "high_risk_changes": mr.high_risk_changes,
        "pending_task_cards": mr.pending_task_cards,
        "summary": mr.summary,
        "evaluated_at": mr.evaluated_at,
    }
