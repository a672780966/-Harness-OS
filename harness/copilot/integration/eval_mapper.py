"""Eval Mapper — maps eval results to repair task cards."""

from __future__ import annotations

from typing import List

from ..schemas import (
    TaskCard, CardType, TaskState, Priority, Source,
    MergeReadinessState, VerificationEntry, VerificationMethod,
    now_iso, generate_id,
)
from .loop_artifact_loader import LoopArtifacts


def eval_to_repair_task_cards(artifacts: LoopArtifacts) -> List[TaskCard]:
    """Generate repair task cards from eval failures.

    When:
      eval_valid: true
      resolved_official: false

    Produces:
      Test Failure Repair Task Card with:
      - 失败测试摘要
      - 受影响模块
      - 建议先修测试失败
      - 禁止重构无关模块
      - 重新运行测试命令
    """
    cards: List[TaskCard] = []
    eval_report = artifacts.eval_report or {}
    metrics = artifacts.metrics or {}

    if not eval_report:
        return cards

    eval_valid = eval_report.get("eval_valid", metrics.get("eval_valid", False))
    resolved_official = eval_report.get(
        "resolved_official",
        metrics.get("resolved_official", None),
    )
    tests_passed = eval_report.get("tests_passed", 0)
    tests_total = eval_report.get("tests_total", 0)
    tests_failed = eval_report.get("tests_failed", 0)
    failure_reason = eval_report.get("failure_reason", metrics.get("stop_reason", ""))

    # Scenario 1: Eval valid but official evaluation failed
    if eval_valid and not resolved_official:
        description_parts = [
            f"测试通过率: {tests_passed}/{tests_total}",
            f"失败测试: {tests_failed} 个",
        ]
        if failure_reason:
            description_parts.append(f"失败原因: {failure_reason}")
        if artifacts.eval_stderr:
            description_parts.append(f"错误输出: {artifacts.eval_stderr[:200]}")

        card = TaskCard(
            card_id=generate_id("eval"),
            title=f"修复测试失败 — {artifacts.instance_id or 'unknown'}",
            card_type=CardType.FIX_TEST,
            state=TaskState.PENDING,
            priority=Priority.HIGH,
            source=Source.EVAL,
            module=artifacts.instance_id,
            description="\n".join(description_parts),
            acceptance_criteria=[
                f"重新运行测试并达到 {tests_total}/{tests_total} 通过",
                f"仅修复测试失败，禁止重构无关模块",
                f"不得扩大修改范围",
            ],
            evidence=[
                VerificationEntry(
                    method=VerificationMethod.DOCKER_EVAL,
                    status="failed" if not resolved_official else "passed",
                    summary=f"Official eval: {tests_passed}/{tests_total} pass",
                    artifact_path="eval_report.json",
                    timestamp=eval_report.get("generated_at", ""),
                ),
            ],
            risk_score=0.7,
            merge_readiness=MergeReadinessState.BLOCK,
            blocking_issues=[f"Official eval failed: {tests_failed} test(s) not passing"],
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    # Scenario 2: Environment failed
    env_failed = eval_report.get("environment_failed", False)
    if env_failed:
        card = TaskCard(
            card_id=generate_id("eval"),
            title=f"修复测试环境 — {artifacts.instance_id or 'unknown'}",
            card_type=CardType.FIX_TEST,
            state=TaskState.BLOCKED,
            priority=Priority.CRITICAL,
            source=Source.EVAL,
            module=artifacts.instance_id,
            description="评估环境失败，测试无法运行。请检查 Docker 镜像和环境配置。",
            acceptance_criteria=[
                "Docker 评估环境可正常启动",
                "测试可正常执行",
            ],
            evidence=[],
            risk_score=0.9,
            merge_readiness=MergeReadinessState.BLOCK,
            blocking_issues=["评估环境故障"],
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    # Scenario 3: Tests failed (eval valid but tests < total)
    if eval_valid and tests_failed > 0:
        card = TaskCard(
            card_id=generate_id("eval"),
            title=f"测试未全部通过 ({tests_passed}/{tests_total}) — {artifacts.instance_id or 'unknown'}",
            card_type=CardType.FIX_TEST,
            state=TaskState.PENDING,
            priority=Priority.HIGH,
            source=Source.EVAL,
            module=artifacts.instance_id,
            description=f"{tests_failed} 个测试未通过。建议先定位失败原因，仅修复相关代码。",
            acceptance_criteria=[
                f"全部 {tests_total} 个测试通过",
                "禁止重构无关模块",
                "禁止扩大修改范围",
            ],
            evidence=[
                VerificationEntry(
                    method=VerificationMethod.DOCKER_EVAL,
                    status="failed",
                    summary=f"{tests_passed}/{tests_total} passed",
                    artifact_path="eval_report.json",
                    timestamp=eval_report.get("generated_at", ""),
                ),
            ],
            risk_score=0.7,
            merge_readiness=MergeReadinessState.BLOCK,
            blocking_issues=[f"{tests_failed} test(s) failed"],
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    return cards
