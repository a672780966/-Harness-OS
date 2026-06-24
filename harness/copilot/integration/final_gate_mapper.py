"""Final Gate Mapper — maps final gate result to MergeReadiness.

Key mappings:
  final_gate_passed: true  → user_state: 可以准备合并, risk_label: low_or_reviewed
  final_gate_passed: false → user_state: 暂不建议合并
    reasons: tests_failed, codex_review_rejected, high_risk_changes, evidence_incomplete
"""

from __future__ import annotations

from typing import Optional

from ..schemas import (
    MergeReadiness, MergeReadinessState, now_iso,
)
from .loop_artifact_loader import LoopArtifacts


def final_gate_to_readiness(artifacts: LoopArtifacts) -> Optional[MergeReadiness]:
    """Map final gate result to MergeReadiness."""
    metrics = artifacts.metrics or {}
    run_class = artifacts.run_classification or {}
    fg_result = artifacts.final_gate_result or {}
    eval_report = artifacts.eval_report or {}
    review_env = artifacts.final_review_envelope or {}

    # Gather all signals
    final_gate_passed = _field(fg_result, "final_gate_passed",
                          _field(metrics, "final_gate_passed", False))

    merge_ready = _field(fg_result, "merge_ready",
                   _field(metrics, "merge_ready", False))

    eval_valid = _field(eval_report, "eval_valid",
                  _field(metrics, "eval_valid", False))

    codex_approved = _field(metrics, "codex_approved",
                      _field(review_env, "approved",
                        _field(review_env, "passed", None)))

    tests_passed = eval_report.get("tests_passed", 0)
    tests_total = eval_report.get("tests_total", 0)
    resolved_official = _field(eval_report, "resolved_official",
                          _field(metrics, "resolved_official", None))

    stop_reason = _field(metrics, "stop_reason",
                   _field(run_class, "stop_reason", ""))

    mock_used = _field(metrics, "mock_used",
                 _field(run_class, "mock_used", False))

    # Build blocking issues
    blocking_issues: list[str] = []

    if final_gate_passed and merge_ready:
        # ✅ Pass
        summary_parts = ["✅ Final Gate 已通过，可以准备合并。"]

        if mock_used:
            summary_parts.append("注意：mock_used=true，执行结果可能存在模拟成分。")

        return MergeReadiness(
            state=MergeReadinessState.PASS,
            blocking_issues=[],
            review_required=False,
            tests_passed=True,
            codex_approved=True if codex_approved is not False else False,
            high_risk_changes=[],
            pending_task_cards=0,
            summary=" ".join(summary_parts),
            evaluated_at=now_iso(),
        )

    # ❌ Block or Review Needed
    if not eval_valid:
        blocking_issues.append("tests_failed: 评估未通过或环境失败")

    if codex_approved is False:
        blocking_issues.append("codex_review_rejected: Codex 审查拒绝")

    if resolved_official is False:
        blocking_issues.append("tests_failed: 官方评估未通过")

    if eval_valid and resolved_official is not False and codex_approved is not False:
        # Partial pass — needs review
        state = MergeReadinessState.REVIEW_NEEDED
        summary = "执行已基本通过，但 Final Gate 尚未正式批准。需要人工审查后决定是否合并。"
    else:
        state = MergeReadinessState.BLOCK
        summary = f"暂不建议合并。存在 {len(blocking_issues)} 个阻塞项。"

    if stop_reason:
        blocking_issues.append(f"停止原因: {stop_reason}")

    summary_parts = [summary]
    if blocking_issues:
        summary_parts.append(f"阻塞项: {'; '.join(blocking_issues[:3])}")
        if len(blocking_issues) > 3:
            summary_parts.append(f"... 还有 {len(blocking_issues) - 3} 项")

    return MergeReadiness(
        state=state,
        blocking_issues=blocking_issues,
        review_required=(state != MergeReadinessState.PASS),
        tests_passed=eval_valid if eval_valid else False,
        codex_approved=codex_approved,
        high_risk_changes=[],
        pending_task_cards=0,
        summary=" ".join(summary_parts),
        evaluated_at=now_iso(),
    )


def _field(d: Optional[dict], key: str, default=None):
    if d is None:
        return default
    return d.get(key, default)
