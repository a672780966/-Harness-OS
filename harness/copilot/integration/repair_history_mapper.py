"""Repair History Mapper — maps repair round history to task card lineage."""

from __future__ import annotations

from typing import List

from ..schemas import (
    TaskCard, CardType, TaskState, Priority, Source,
    MergeReadinessState, VerificationEntry, VerificationMethod,
    now_iso, generate_id,
)
from .loop_artifact_loader import LoopArtifacts


def repair_history_to_task_cards(artifacts: LoopArtifacts) -> List[TaskCard]:
    """Generate task cards documenting repair round history.

    Creates one card per repair round, showing:
    - Round number
    - Whether it was eval-triggered or review-triggered
    - Outcome (passed/failed)
    """
    cards: List[TaskCard] = []
    metrics = artifacts.metrics or {}

    total_rounds = metrics.get("repair_rounds", 0)
    if total_rounds == 0 and not artifacts.repair_rounds and not artifacts.review_repair_rounds:
        return cards

    # Eval-triggered repair rounds
    for round_data in artifacts.repair_rounds:
        round_name = round_data.get("round_name", "unknown")
        result = round_data.get("test_result", {}) or round_data.get("eval_report", {})
        passed = result.get("tests_passed", 0) if result else 0
        total = result.get("tests_total", 0) if result else 0
        eval_valid = result.get("eval_valid", False) if result else False

        state = TaskState.COMPLETED if eval_valid else TaskState.BLOCKED
        merge_state = MergeReadinessState.PASS if eval_valid else MergeReadinessState.BLOCK
        priority = Priority.MEDIUM if eval_valid else Priority.HIGH

        card = TaskCard(
            card_id=generate_id("repair"),
            title=f"修复回合 {round_name} (Eval-triggered)",
            card_type=CardType.FIX_TEST,
            state=state,
            priority=priority,
            source=Source.EVAL,
            module=artifacts.instance_id,
            description=(
                f"修复回合 {round_name}: "
                f"测试结果 {passed}/{total} 通过"
                f"{' ✅' if eval_valid else ' ❌'}"
            ),
            acceptance_criteria=[
                f"修复回合 {round_name} 完成",
            ],
            evidence=[
                VerificationEntry(
                    method=VerificationMethod.DOCKER_EVAL,
                    status="passed" if eval_valid else "failed",
                    summary=f"Round {round_name}: {passed}/{total} pass",
                    artifact_path=f"repair_rounds/{round_name}/",
                    timestamp="",
                ),
            ],
            risk_score=0.5 if not eval_valid else 0.2,
            merge_readiness=merge_state,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    # Review-triggered repair rounds
    for round_data in artifacts.review_repair_rounds:
        round_name = round_data.get("round_name", "unknown")

        card = TaskCard(
            card_id=generate_id("repair"),
            title=f"修复回合 {round_name} (Review-triggered)",
            card_type=CardType.FIX_REVIEW,
            state=TaskState.COMPLETED,
            priority=Priority.HIGH,
            source=Source.REVIEW,
            module=artifacts.instance_id,
            description=f"审查触发的修复回合 {round_name}：已处理 Codex 指出的问题。",
            acceptance_criteria=[
                f"审查修复 {round_name} 完成",
                "需要重新运行评估",
                "需要重新提交审查",
            ],
            evidence=[
                VerificationEntry(
                    method=VerificationMethod.CODEX_REVIEW,
                    status="passed",
                    summary=f"Review-repair round {round_name}",
                    artifact_path=f"review_repair/{round_name}/",
                    timestamp="",
                ),
            ],
            risk_score=0.4,
            merge_readiness=MergeReadinessState.REVIEW_NEEDED,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    return cards
