"""Timeline — build and manage agent state timelines from events."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import AgentState, AgentStateEnum, AgentStateTimeline, state_priority, is_completed_override
from .inference import infer_from_events, infer_latest_from_events


def build_timeline(
    events: List[Dict[str, Any]],
    max_states: int = 50,
) -> AgentStateTimeline:
    """Build a deduplicated agent state timeline from monitor events.

    Merges consecutive identical states to keep timeline compact.

    Args:
        events: Chronological list of MonitorEvent.to_dict().
        max_states: Maximum states to retain.

    Returns:
        AgentStateTimeline with merged states.
    """
    raw_timeline = infer_from_events(events)
    if not raw_timeline.states:
        return raw_timeline

    merged = AgentStateTimeline()
    for state in raw_timeline.states:
        last = merged.latest()
        if last is None or last.state != state.state:
            merged.add(state)

    # Trim to max
    if len(merged.states) > max_states:
        merged.states = merged.states[-max_states:]

    return merged


def resolve_conflict(
    current: AgentState,
    incoming: AgentState,
) -> AgentState:
    """Resolve conflict between two agent states using priority rules.

    Higher-priority states win. Completed states can override lower
    priority states if the completed inference has high confidence.
    """
    if current.state == incoming.state:
        return current  # No conflict

    # Completed override: if incoming is completed with high confidence
    if (is_completed_override(incoming.state)
            and incoming.confidence >= 0.8
            and not is_completed_override(current.state)):
        return incoming

    # Priority-based resolution
    curr_prio = state_priority(current.state)
    in_prio = state_priority(incoming.state)

    if in_prio > curr_prio:
        return incoming
    return current


def summarize_state(state: AgentState) -> str:
    """Generate a one-line user-readable summary of an agent state."""
    labels = {
        AgentStateEnum.IDLE.value: "待命",
        AgentStateEnum.PLANNING.value: "规划中",
        AgentStateEnum.IMPLEMENTING.value: "正在修改代码",
        AgentStateEnum.TESTING.value: "正在运行测试",
        AgentStateEnum.REPAIRING.value: "正在修复问题",
        AgentStateEnum.REVIEWING.value: "审查中",
        AgentStateEnum.WAITING_FOR_USER.value: "等待用户操作",
        AgentStateEnum.COMPLETED.value: "已完成",
        AgentStateEnum.FAILED.value: "失败",
        AgentStateEnum.BLOCKED.value: "阻塞",
    }
    label = labels.get(state.state, state.state)
    if state.recommended_action:
        return f"{label} — {state.recommended_action}"
    return label
