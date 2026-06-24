"""Inference — infer AgentState from MonitorEvent and LoopArtifacts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import (
    AgentState, AgentStateEnum, AgentStateTimeline,
    infer_severity, state_priority, is_completed_override,
)

from ..monitor import EventType


def infer_from_events(events: List[Dict[str, Any]]) -> AgentStateTimeline:
    """Infer agent state timeline from a list of monitor events.

    Args:
        events: List of MonitorEvent.to_dict() dicts, ordered chronologically.

    Returns:
        AgentStateTimeline with inferred states.
    """
    timeline = AgentStateTimeline()
    if not events:
        return timeline

    # Track best state per position
    for evt in events:
        inferred = _infer_single(evt)
        if inferred is not None:
            timeline.add(inferred)

    # If no explicit state was inferred, keep timeline empty
    return timeline


def infer_latest_from_events(events: List[Dict[str, Any]]) -> AgentState:
    """Infer latest agent state from events using priority resolution."""
    timeline = infer_from_events(events)
    latest = timeline.latest()
    if latest:
        return latest
    return AgentState(state=AgentStateEnum.IDLE.value, summary="无事件 — 状态未知")


def infer_from_loop_artifacts(loop_artifacts: Any) -> AgentState:
    """Infer agent state from a LoopArtifacts object (Phase 3 integration).

    Uses stop_reason, eval results, review results, and final gate.
    """
    if loop_artifacts is None:
        return AgentState(state=AgentStateEnum.IDLE.value, summary="无 Loop artifacts")

    source_events: List[str] = []

    # 1. Check final gate result (highest priority)
    gate = getattr(loop_artifacts, "final_gate_result", None)
    if gate is not None:
        gate_text = ""
        if hasattr(gate, "content"):
            gate_text = gate.content if isinstance(gate.content, str) else str(gate.content)
        elif isinstance(gate, str):
            gate_text = gate
        elif isinstance(gate, dict):
            gate_text = str(gate.get("content", ""))

        gate_pass = "pass" in gate_text.lower() or "true" in gate_text.lower()
        source_events.append("final_gate_result")

        if gate_pass:
            return AgentState(
                state=AgentStateEnum.COMPLETED.value,
                confidence=0.95,
                source_events=source_events,
                summary="Final Gate 已通过，可以准备合并",
                recommended_action="审查合并就绪度后合并",
                severity=infer_severity(AgentStateEnum.COMPLETED.value),
                blocking=False,
            )

    # 2. Check review result
    review = getattr(loop_artifacts, "final_review_envelope", None)
    if review is not None:
        source_events.append("final_review_envelope")
        approved = False
        if hasattr(review, "get"):
            approved = review.get("codex_approved", False)
        if not approved:
            return AgentState(
                state=AgentStateEnum.BLOCKED.value,
                confidence=0.9,
                source_events=source_events,
                summary="Codex 审查拒绝，需要修复 review blocking issue",
                recommended_action="检查 review 意见并修复",
                severity=infer_severity(AgentStateEnum.BLOCKED.value),
                blocking=True,
            )

    # 3. Check eval result
    eval_report = getattr(loop_artifacts, "eval_report", None)
    if eval_report is not None:
        source_events.append("eval_report")
        resolved = False
        tests_passed = 0
        tests_total = 0
        if hasattr(eval_report, "get"):
            resolved = eval_report.get("resolved_official", False) or eval_report.get("resolved", False)
            tests_passed = eval_report.get("tests_passed", 0) or eval_report.get("passed", 0)
            tests_total = eval_report.get("tests_total", 0) or eval_report.get("total", 0)

        if resolved:
            return AgentState(
                state=AgentStateEnum.COMPLETED.value,
                confidence=0.85,
                source_events=source_events,
                summary=f"Eval 通过 ({tests_passed}/{tests_total})",
                recommended_action="",
                severity=infer_severity(AgentStateEnum.COMPLETED.value),
                blocking=False,
            )
        elif tests_total > 0 and tests_passed < tests_total:
            return AgentState(
                state=AgentStateEnum.FAILED.value,
                confidence=0.85,
                source_events=source_events,
                summary=f"测试失败 ({tests_passed}/{tests_total})，需要修复失败测试",
                recommended_action="检查测试输出并修复",
                severity=infer_severity(AgentStateEnum.FAILED.value),
                blocking=True,
            )

    # 4. Check stop_reason from loop report
    loop_report = getattr(loop_artifacts, "loop_report", None)
    if loop_report is not None:
        source_events.append("loop_report")
        stop_reason = ""
        report_text = ""
        if hasattr(loop_report, "content"):
            report_text = loop_report.content if isinstance(loop_report.content, str) else str(loop_report.content)
        elif isinstance(loop_report, str):
            report_text = loop_report

        # Extract stop_reason from report text
        for line in report_text.split("\n"):
            if "stop_reason" in line.lower() or "reason" in line.lower():
                stop_reason = line.strip()
                break

        if "real_loop_complete" in stop_reason:
            return AgentState(
                state=AgentStateEnum.COMPLETED.value,
                confidence=0.95,
                source_events=source_events,
                summary="Loop 运行完成，可以准备合并",
                recommended_action="审查运行结果后合并",
                severity=infer_severity(AgentStateEnum.COMPLETED.value),
                blocking=False,
            )
        if "unresolved" in stop_reason or "failed" in stop_reason:
            return AgentState(
                state=AgentStateEnum.FAILED.value,
                confidence=0.85,
                source_events=source_events,
                summary="Loop 运行未完成，存在未解决的失败",
                recommended_action="检查失败原因并修复",
                severity=infer_severity(AgentStateEnum.FAILED.value),
                blocking=True,
            )
        if "rejected" in stop_reason:
            return AgentState(
                state=AgentStateEnum.BLOCKED.value,
                confidence=0.9,
                source_events=source_events,
                summary="Codex 审查拒绝，Loop 阻塞",
                recommended_action="检查 review 反馈并修复",
                severity=infer_severity(AgentStateEnum.BLOCKED.value),
                blocking=True,
            )

    # 5. Default: check for any event activity
    if source_events:
        return AgentState(
            state=AgentStateEnum.IMPLEMENTING.value,
            confidence=0.5,
            source_events=source_events,
            summary="Agent 正在工作中",
            recommended_action="等待当前任务完成",
            severity=infer_severity(AgentStateEnum.IMPLEMENTING.value),
            blocking=False,
        )

    return AgentState(state=AgentStateEnum.IDLE.value, summary="无活动")


def _infer_single(evt: Dict[str, Any]) -> Optional[AgentState]:
    """Infer agent state from a single monitor event."""
    event_type = evt.get("event_type", "")
    summary = evt.get("summary", "")
    old_val = evt.get("old_value")
    new_val = evt.get("new_value")

    if event_type == EventType.PROJECT_DIFF_CHANGED.value:
        return AgentState(
            state=AgentStateEnum.IMPLEMENTING.value,
            confidence=0.6,
            source_events=[event_type],
            summary="Agent 正在修改代码",
            recommended_action="等待代码修改完成",
            severity=infer_severity(AgentStateEnum.IMPLEMENTING.value),
            blocking=False,
        )

    if event_type == EventType.FILE_CHANGED.value:
        return AgentState(
            state=AgentStateEnum.IMPLEMENTING.value,
            confidence=0.5,
            source_events=[event_type],
            summary="检测到文件变更",
            recommended_action="",
            severity=infer_severity(AgentStateEnum.IMPLEMENTING.value),
            blocking=False,
        )

    if event_type == EventType.TEST_RESULT_CHANGED.value:
        if new_val == "present":
            return AgentState(
                state=AgentStateEnum.TESTING.value,
                confidence=0.7,
                source_events=[event_type],
                summary="Agent 正在运行测试",
                recommended_action="等待测试完成",
                severity=infer_severity(AgentStateEnum.TESTING.value),
                blocking=False,
            )
        return AgentState(
            state=AgentStateEnum.TESTING.value,
            confidence=0.5,
            source_events=[event_type],
            summary="测试状态变更",
            recommended_action="",
            severity=infer_severity(AgentStateEnum.TESTING.value),
            blocking=False,
        )

    if event_type == EventType.EVAL_REPORT_CHANGED.value:
        return AgentState(
            state=AgentStateEnum.TESTING.value,
            confidence=0.7,
            source_events=[event_type],
            summary="Eval 报告已更新",
            recommended_action="检查 eval 结果",
            severity=infer_severity(AgentStateEnum.TESTING.value),
            blocking=False,
        )

    if event_type == EventType.REVIEW_RESULT_CHANGED.value:
        return AgentState(
            state=AgentStateEnum.REVIEWING.value,
            confidence=0.8,
            source_events=[event_type],
            summary="Codex 审查结果已更新",
            recommended_action="检查审查意见",
            severity=infer_severity(AgentStateEnum.REVIEWING.value),
            blocking=False,
        )

    if event_type == EventType.FINAL_GATE_CHANGED.value:
        passed = new_val == "pass" or (isinstance(new_val, str) and "pass" in new_val)
        if passed:
            return AgentState(
                state=AgentStateEnum.COMPLETED.value,
                confidence=0.95,
                source_events=[event_type],
                summary="Final Gate 已通过，可以准备合并",
                recommended_action="审查合并就绪度后合并",
                severity=infer_severity(AgentStateEnum.COMPLETED.value),
                blocking=False,
            )
        return AgentState(
            state=AgentStateEnum.BLOCKED.value,
            confidence=0.85,
            source_events=[event_type],
            summary="Final Gate 未通过，阻塞合并",
            recommended_action="检查 gate 失败原因并修复",
            severity=infer_severity(AgentStateEnum.BLOCKED.value),
            blocking=True,
        )

    if event_type == EventType.LOOP_REPORT_CHANGED.value:
        return AgentState(
            state=AgentStateEnum.REVIEWING.value,
            confidence=0.6,
            source_events=[event_type],
            summary="Loop 运行报告已更新",
            recommended_action="查看 loop 结果",
            severity=infer_severity(AgentStateEnum.REVIEWING.value),
            blocking=False,
        )

    if event_type == EventType.MERGE_READINESS_CHANGED.value:
        if new_val == "block":
            return AgentState(
                state=AgentStateEnum.BLOCKED.value,
                confidence=0.8,
                source_events=[event_type],
                summary="合并就绪度变更为阻塞",
                recommended_action="解决阻塞问题",
                severity=infer_severity(AgentStateEnum.BLOCKED.value),
                blocking=True,
            )
        return AgentState(
            state=AgentStateEnum.COMPLETED.value,
            confidence=0.75,
            source_events=[event_type],
            summary="合并就绪度已更新",
            recommended_action="",
            severity=infer_severity(AgentStateEnum.COMPLETED.value),
            blocking=False,
        )

    if event_type == EventType.TASK_CARD_RECOMMENDED.value:
        return AgentState(
            state=AgentStateEnum.REPAIRING.value,
            confidence=0.6,
            source_events=[event_type],
            summary="检测到待处理任务卡",
            recommended_action="检查推荐任务卡",
            severity=infer_severity(AgentStateEnum.REPAIRING.value),
            blocking=False,
        )

    return None
