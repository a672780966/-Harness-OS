"""Loop to Copilot Mapper — transforms LoopArtifacts into Copilot ViewModel objects."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..schemas import (
    AgentExecutionState, AgentPhase, RecentChangeExplanation,
    TaskCard, CardType, TaskState, Priority, Source,
    MergeReadiness, MergeReadinessState, RiskAlert, RiskLevel,
    EvidencePack, EvidenceEntry, VerificationEntry, VerificationMethod,
    now_iso, generate_id,
)
from ..view_models import (
    CopilotDashboardState, ModuleCardViewModel, RecentChangeViewModel,
    MergeReadinessViewModel, TaskCardViewModel, TaskCardListViewModel,
    RiskAlertViewModel, EvidencePackViewModel, SuggestionListViewModel,
    ChangeSuggestionViewModel, WaitingCompanionViewModel,
)
from .loop_artifact_loader import LoopArtifacts
from .eval_mapper import eval_to_repair_task_cards
from .review_mapper import review_to_repair_task_cards
from .repair_history_mapper import repair_history_to_task_cards
from .final_gate_mapper import final_gate_to_readiness


def artifacts_to_dashboard(
    artifacts: LoopArtifacts,
    diff_text: Optional[str] = None,
) -> CopilotDashboardState:
    """Transform loop artifacts into a full dashboard state."""
    state = CopilotDashboardState(
        project_name=artifacts.instance_id or f"Loop Run: {Path(artifacts.run_dir).name}",
        project_root=artifacts.run_dir,
        branch=f"tier_{artifacts.tier}",
        generated_at=now_iso(),
    )

    # Agent execution state from artifacts
    aes = _build_execution_state(artifacts)
    state.agent_phase = aes.phase.value if hasattr(aes.phase, "value") else str(aes.phase)
    state.agent_phase_label = _agent_phase_label(aes.phase)

    # Overall risk
    metrics = artifacts.metrics or {}
    if not metrics.get("final_gate_passed", False) and metrics.get("eval_valid", False):
        state.overall_risk_level = "medium"
        state.risk_color = "yellow"
    elif not metrics.get("eval_valid", False):
        state.overall_risk_level = "high"
        state.risk_color = "red"
    else:
        state.overall_risk_level = "low"
        state.risk_color = "green"

    # Module cards (from instance_id)
    if artifacts.instance_id:
        state.modules = [_build_module_card(artifacts)]
        state.module_count = len(state.modules)

    # Recent change explanation from loop report
    if artifacts.loop_report:
        rce = _loop_report_to_change_explanation(artifacts)
        if rce:
            state.recent_changes = [rce]

    # Merge readiness
    mr = final_gate_to_readiness(artifacts)
    state.readiness = MergeReadinessViewModel.from_kernel(mr) if mr else None

    # Task cards
    all_cards: List[TaskCard] = []

    # Eval-triggered repair cards
    eval_cards = eval_to_repair_task_cards(artifacts)
    all_cards.extend(eval_cards)

    # Review-triggered repair cards
    review_cards = review_to_repair_task_cards(artifacts)
    all_cards.extend(review_cards)

    # Repair history cards
    history_cards = repair_history_to_task_cards(artifacts)
    all_cards.extend(history_cards)

    if all_cards:
        state.task_cards = TaskCardListViewModel(
            cards=[TaskCardViewModel.from_kernel(c) for c in all_cards],
            summary={
                "total_cards": len(all_cards),
                "blocking_count": sum(1 for c in all_cards if c.merge_readiness == MergeReadinessState.BLOCK),
                "by_state": {"pending": sum(1 for c in all_cards if c.state == TaskState.PENDING)},
            },
        )

    # Suggestions
    suggestions = _build_suggestions(artifacts, all_cards)
    if suggestions:
        state.suggestions = SuggestionListViewModel(suggestions=suggestions)

    # Evidence pack
    ep = _build_evidence_pack(artifacts)
    if ep:
        state.evidence = EvidencePackViewModel.from_kernel(ep)

    # Risk alerts (no risk_alerts field on dashboard state, included in task cards)
    _ = _build_risk_alerts(artifacts)  # results already in task cards as risk_alert type

    # Waiting companion placeholder
    state.companion = WaitingCompanionViewModel()

    # --- Agent State (Phase 6B) ---
    from ..agent_state.inference import infer_from_loop_artifacts
    from ..agent_state.timeline import summarize_state
    astate = infer_from_loop_artifacts(artifacts)
    state.agent_state = astate.to_dict()
    state.agent_phase = astate.state
    state.agent_phase_label = summarize_state(astate)
    # ------------------------------

    return state


def _build_execution_state(artifacts: LoopArtifacts) -> AgentExecutionState:
    """Build AgentExecutionState from artifacts."""
    metrics = artifacts.metrics or {}
    run_class = artifacts.run_classification or {}

    phase = AgentPhase.DONE
    if metrics.get("final_gate_passed"):
        phase = AgentPhase.DONE
    elif metrics.get("repair_rounds", 0) > 0:
        phase = AgentPhase.REPAIRING
    elif metrics.get("codex_approved") is False:
        phase = AgentPhase.REVIEWING
    elif metrics.get("eval_valid"):
        phase = AgentPhase.TESTING
    else:
        phase = AgentPhase.IDLE

    return AgentExecutionState(
        phase=phase,
        current_task=artifacts.instance_id,
        task_id=metrics.get("task_id", ""),
        error_count=0 if metrics.get("eval_valid", True) else 1,
    )


def _build_module_card(artifacts: LoopArtifacts) -> ModuleCardViewModel:
    """Build a single module card for the instance."""
    metrics = artifacts.metrics or {}
    risk_level = "medium"
    if metrics.get("final_gate_passed"):
        risk_level = "low"
    elif metrics.get("codex_approved") is False:
        risk_level = "high"
    elif not metrics.get("eval_valid"):
        risk_level = "high"

    return ModuleCardViewModel(
        name=artifacts.instance_id.split("__")[-1] if "__" in artifacts.instance_id else artifacts.instance_id,
        file_count=metrics.get("files_changed", 0),
        risk_level=risk_level,
        risk_color={"critical": "red", "high": "red", "medium": "yellow", "low": "green"}.get(risk_level, "gray"),
        risk_score=0.7 if risk_level == "high" else 0.3 if risk_level == "medium" else 0.1,
        risk_description=_risk_description(risk_level, artifacts.instance_id),
        dependencies=[],
        dependents=[],
        high_risk_files=[],
        primary_language="Python",
    )


def _loop_report_to_change_explanation(artifacts: LoopArtifacts) -> RecentChangeViewModel:
    """Extract change explanation from loop report."""
    metrics = artifacts.metrics or {}
    report = artifacts.loop_report or ""

    # Extract summary from first lines
    lines = report.strip().split("\n")
    summary = lines[0] if lines else "Loop execution"

    # Extract phases from table
    phases: List[str] = []
    in_table = False
    for line in lines:
        if "| Phase |" in line:
            in_table = True
            continue
        if in_table and line.strip().startswith("|"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                phases.append(f"{parts[0]}: {parts[2]} ({parts[3]})")

    intent = "Loop execution completed"
    if metrics.get("final_gate_passed"):
        intent = "Agent 完成循环并获批准，可以准备合并"
    elif metrics.get("codex_approved") is False:
        intent = "Agent 完成执行但 Codex 审查未通过，需要修复后重新审查"
    elif metrics.get("eval_valid"):
        intent = "Agent 执行完成，测试通过，等待审查"
    else:
        intent = "Agent 执行完成，但存在测试问题"

    return RecentChangeViewModel(
        module=artifacts.instance_id or "unknown",
        summary=f"Loop: {metrics.get('stop_reason', 'completed')} ({metrics.get('files_changed', 0)} files, patch: {metrics.get('patch_size_lines', 0)} lines)",
        intent=intent,
        files_changed=[f"Phase run: {p}" for p in phases[:3]],
        lines_changed_str=f"+{metrics.get('patch_size_lines', 0)}",
        has_risks=not metrics.get("final_gate_passed", False),
        risk_warnings=[] if metrics.get("final_gate_passed") else ["Loop not yet fully approved"],
    )


def _build_suggestions(
    artifacts: LoopArtifacts,
    cards: List[TaskCard],
) -> List[ChangeSuggestionViewModel]:
    """Build suggestions from artifacts."""
    suggestions: List[ChangeSuggestionViewModel] = []
    metrics = artifacts.metrics or {}

    if not metrics.get("final_gate_passed", False):
        unapproved_cards = [c for c in cards if c.state != TaskState.COMPLETED]
        if unapproved_cards:
            suggestions.append(ChangeSuggestionViewModel(
                suggestion=f"完成 {len(unapproved_cards)} 个待处理任务卡后再合并",
                reason="Final gate 尚未通过，存在未完成的任务",
                priority_label="🟠 高优先级",
                confidence_label="100%",
                file_path=artifacts.run_dir,
            ))

    if metrics.get("codex_approved") is False:
        suggestions.append(ChangeSuggestionViewModel(
            suggestion="处理 Codex 审查拒绝的原因后再重新提交审查",
            reason="Codex 拒绝了该执行结果，需要修复后重新审查",
            priority_label="🔴 紧急",
            confidence_label="100%",
            file_path="",
        ))

    if not metrics.get("eval_valid", True):
        suggestions.append(ChangeSuggestionViewModel(
            suggestion="检查测试环境并重新运行评估",
            reason="评估环境失败，测试未正确执行",
            priority_label="🔴 紧急",
            confidence_label="100%",
            file_path="",
        ))

    return suggestions


def _build_evidence_pack(artifacts: LoopArtifacts) -> Optional[EvidencePack]:
    """Build evidence pack from artifacts."""
    entries: List[EvidenceEntry] = []
    metrics = artifacts.metrics or {}
    eval_report = artifacts.eval_report or {}
    review_env = artifacts.final_review_envelope or {}

    # Eval evidence
    if eval_report:
        entries.append(EvidenceEntry(
            ref_id=generate_id("ev"),
            evidence_type="test_result",
            file_path="eval_report.json",
            summary=f"Eval: {eval_report.get('tests_passed', '?')}/{eval_report.get('tests_total', '?')} tests passed",
            passed=eval_report.get("eval_valid", False),
            timestamp=eval_report.get("generated_at", ""),
        ))

    # Review evidence
    if review_env:
        entries.append(EvidenceEntry(
            ref_id=generate_id("ev"),
            evidence_type="review_result",
            file_path="review_envelopes/final_review_envelope.json",
            summary=f"Review: {'approved' if review_env.get('approved', review_env.get('passed')) else 'rejected'}",
            passed=bool(review_env.get("approved", review_env.get("passed", False))),
            timestamp=review_env.get("reviewed_at", ""),
        ))

    # Final gate evidence
    if artifacts.final_gate_result:
        fg = artifacts.final_gate_result
        entries.append(EvidenceEntry(
            ref_id=generate_id("ev"),
            evidence_type="audit",
            file_path="final_gate_result.md",
            summary=f"Final gate: {'passed' if fg.get('merge_ready', fg.get('final_gate_passed')) else 'not passed'}",
            passed=bool(fg.get("merge_ready", fg.get("final_gate_passed", False))),
            timestamp="",
        ))

    # Patch evidence
    if artifacts.patch_diff:
        entries.append(EvidenceEntry(
            ref_id=generate_id("ev"),
            evidence_type="patch",
            file_path="patch.diff",
            summary=f"Patch: {metrics.get('patch_size_lines', 0)} lines in {metrics.get('files_changed', 0)} files",
            passed=True,
            timestamp="",
        ))

    packed = EvidencePack(
        pack_id=generate_id("pack"),
        task_id=metrics.get("task_id", ""),
        entries=entries,
        total_entries=len(entries),
        passed_count=sum(1 for e in entries if e.passed is True),
        failed_count=sum(1 for e in entries if e.passed is False),
        generated_at=now_iso(),
    )
    return packed


def _build_risk_alerts(artifacts: LoopArtifacts) -> List[RiskAlert]:
    """Build risk alerts from artifacts."""
    alerts: List[RiskAlert] = []
    metrics = artifacts.metrics or {}

    if not metrics.get("eval_valid", True):
        alerts.append(RiskAlert(
            alert_id=generate_id("risk"),
            title="评估未通过",
            level=RiskLevel.HIGH,
            module=artifacts.instance_id,
            description="Docker 评估失败，测试未正确执行",
            recommendation="检查测试环境配置和 Docker 镜像状态",
            is_blocking=True,
            created_at=now_iso(),
        ))

    if metrics.get("codex_approved") is False:
        alerts.append(RiskAlert(
            alert_id=generate_id("risk"),
            title="Codex 审查拒绝",
            level=RiskLevel.HIGH,
            module=artifacts.instance_id,
            description="Codex 最终审查未通过，存在阻塞性问题需修复",
            recommendation="处理 Codex 指出的问题后重新提交审查",
            is_blocking=True,
            created_at=now_iso(),
        ))

    if metrics.get("repair_rounds", 0) > 0:
        level = RiskLevel.MEDIUM if metrics.get("final_gate_passed") else RiskLevel.HIGH
        alerts.append(RiskAlert(
            alert_id=generate_id("risk"),
            title=f"经历了 {metrics['repair_rounds']} 轮修复",
            level=level,
            module=artifacts.instance_id,
            description=f"该执行经历了 {metrics['repair_rounds']} 轮修复才达到当前状态",
            recommendation="修复历史已保留，建议审查每次修复的变更",
            is_blocking=not metrics.get("final_gate_passed", False),
            created_at=now_iso(),
        ))

    return alerts


def _risk_description(level: str, instance: str) -> str:
    descs = {
        "high": f"⚠️ 高风险 — {instance} 执行存在问题（审查拒绝或评估失败）",
        "medium": f"⚡ 中风险 — {instance} 需关注（存在修复记录或待批准）",
        "low": f"✅ 低风险 — {instance} 执行通过",
    }
    return descs.get(level, f"风险未知 — {instance}")


def _agent_phase_label(phase) -> str:
    phase_str = phase.value if hasattr(phase, "value") else str(phase)
    labels = {
        "idle": "待命",
        "planning": "规划中",
        "implementing": "执行中",
        "testing": "测试中",
        "reviewing": "审查中",
        "repairing": "修复中",
        "waiting": "等待中",
        "done": "已完成",
    }
    return labels.get(phase_str, phase_str)


# Avoid circular import at top level
from pathlib import Path
