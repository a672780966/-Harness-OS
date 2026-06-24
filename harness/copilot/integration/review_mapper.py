"""Review Mapper — maps review envelope results to repair task cards.

Key mapping:
  codex_approved: false → Review Finding Repair Task Card
  Blocking issues → task card with rejection reasons
"""

from __future__ import annotations

from typing import List, Optional

from ..schemas import (
    TaskCard, CardType, TaskState, Priority, Source,
    MergeReadinessState, VerificationEntry, VerificationMethod,
    now_iso, generate_id,
)
from .loop_artifact_loader import LoopArtifacts


def review_to_repair_task_cards(artifacts: LoopArtifacts) -> List[TaskCard]:
    """Generate repair task cards from review rejection.

    When codex_approved is false, generates a Review Finding Repair Task Card.

    Task card must contain:
    - review 拒绝原因
    - 目标模块
    - 限制修改范围
    - 禁止扩大改动
    - 验收标准
    - 需要重新 eval
    - 需要重新 review
    """
    cards: List[TaskCard] = []
    metrics = artifacts.metrics or {}
    review_env = artifacts.final_review_envelope or {}
    run_class = artifacts.run_classification or {}

    # Check multiple sources for review rejection
    codex_approved = _get_field(metrics, "codex_approved", None)
    if codex_approved is None:
        codex_approved = _get_field(review_env, "approved",
                                     _get_field(review_env, "passed", None))

    final_gate_passed = _get_field(metrics, "final_gate_passed", None)
    stop_reason = _get_field(metrics, "stop_reason",
                              _get_field(run_class, "stop_reason", ""))

    is_rejected = codex_approved is False
    is_review_blocked = stop_reason and "review" in str(stop_reason).lower()

    if not is_rejected and not is_review_blocked:
        return cards

    # Extract blocking issues
    blocking_issues_list: List[str] = []
    raw_issues = review_env.get("blocking_issues", [])
    if raw_issues:
        for issue in raw_issues:
            if isinstance(issue, dict):
                text = issue.get("issue", issue.get("summary", str(issue)))
                blocking_issues_list.append(text)
            else:
                blocking_issues_list.append(str(issue))

    summary = review_env.get("summary", "Codex 审查未通过")
    if not blocking_issues_list and summary:
        blocking_issues_list.append(summary)

    if not blocking_issues_list:
        blocking_issues_list.append("Codex 审查拒绝（无详细原因）")

    # Build acceptance criteria
    acceptance = [
        "处理所有 Codex 指出的阻塞性问题",
        "限制修改范围，仅修复审查发现的问题",
        "禁止扩大改动范围",
        "禁止重构无关模块",
        "修复后需要重新运行评估（eval）",
        "修复后需要重新提交 Codex 审查（review）",
    ]

    # Build description
    desc_parts = [
        f"审查结果: {'拒绝' if is_rejected else '阻塞中'}",
        f"实例: {artifacts.instance_id or 'unknown'}",
        f"Tier: {artifacts.tier or 'unknown'}",
        "",
        "拒绝原因:",
    ]
    for issue in blocking_issues_list[:3]:
        desc_parts.append(f"  - {issue[:300]}")
    if len(blocking_issues_list) > 3:
        desc_parts.append(f"  ... 还有 {len(blocking_issues_list) - 3} 项")

    card = TaskCard(
        card_id=generate_id("review"),
        title=f"Codex 审查拒绝 — 需要修复 — {artifacts.instance_id or 'unknown'}",
        card_type=CardType.FIX_REVIEW,
        state=TaskState.PENDING,
        priority=Priority.CRITICAL,
        source=Source.REVIEW,
        module=artifacts.instance_id,
        target_file="",  # Not file-specific for review issues
        description="\n".join(desc_parts),
        acceptance_criteria=acceptance,
        evidence=[
            VerificationEntry(
                method=VerificationMethod.CODEX_REVIEW,
                status="failed",
                summary=summary[:200],
                artifact_path="review_envelopes/final_review_envelope.json",
                timestamp=review_env.get("reviewed_at", ""),
            ),
        ],
        risk_score=0.85,
        merge_readiness=MergeReadinessState.BLOCK,
        blocking_issues=blocking_issues_list[:5],
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    cards.append(card)

    return cards


def _get_field(d: Optional[dict], key: str, default=None):
    """Safely get a field from a dict."""
    if d is None:
        return default
    return d.get(key, default)
