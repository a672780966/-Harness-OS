"""Renderer — render AgentState to user-facing markdown and JSON."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import AgentState, AgentStateEnum, AgentStateTimeline
from .timeline import summarize_state


def render_agent_state(state: AgentState, format: str = "markdown") -> str:
    """Render a single AgentState to a user-facing string.

    Args:
        state: The agent state to render.
        format: "markdown" or "json".

    Returns:
        Formatted string.
    """
    if format == "json":
        import json
        return json.dumps(state.to_dict(), indent=2, ensure_ascii=False)

    # Markdown
    icon = _state_icon(state.state)
    summary = summarize_state(state)

    lines = [
        f"{icon} **Agent 状态**: {summary}",
        f"   - 置信度: {state.confidence:.0%}",
        f"   - 严重度: {state.severity}",
        f"   - 阻塞合并: {'是 🚫' if state.blocking else '否 ✅'}",
    ]
    if state.state in ("idle", "unknown", "") or not state.source_events:
        lines.append("")
        lines.append(
            "   > 📌 当前未检测到活动中的 Agent loop、测试结果或代码变更事件。"
        )
        lines.append(
            "   > 对于 clean clone / 只读扫描项目，idle 是预期状态。"
        )
    if state.source_events:
        lines.append(f"   - 触发事件: {', '.join(state.source_events[:5])}")
    if state.recommended_action:
        lines.append(f"   - 建议操作: {state.recommended_action}")

    return "\n".join(lines)


def render_timeline(timeline: AgentStateTimeline, format: str = "markdown") -> str:
    """Render a full state timeline.

    Args:
        timeline: The timeline to render.
        format: "markdown" or "json".

    Returns:
        Formatted string.
    """
    if format == "json":
        import json
        return json.dumps(timeline.to_dict(), indent=2, ensure_ascii=False)

    if not timeline.states:
        return "无 Agent 状态记录"

    lines = ["## Agent 状态时间线", ""]
    for i, state in enumerate(timeline.states, 1):
        icon = _state_icon(state.state)
        summary = summarize_state(state)
        ts = state.timestamp[11:19] if len(state.timestamp) >= 19 else state.timestamp
        lines.append(f"**{i}. {ts}** {icon} {summary}")
        if state.recommended_action:
            lines.append(f"   → {state.recommended_action}")
        lines.append("")

    return "\n".join(lines)


def render_short(state: AgentState, color: bool = True) -> str:
    """Render a one-line terminal-friendly status.

    Args:
        state: The agent state.
        color: Whether to include ANSI color codes.

    Returns:
        One-line status string.
    """
    icon = _state_icon(state.state)
    summary = summarize_state(state)
    if color:
        return f"{icon} Agent 状态：{summary}"
    return f"Agent 状态: {summary}"


def _state_icon(state: str) -> str:
    icons = {
        AgentStateEnum.IDLE.value: "💤",
        AgentStateEnum.PLANNING.value: "📋",
        AgentStateEnum.IMPLEMENTING.value: "🔧",
        AgentStateEnum.TESTING.value: "🧪",
        AgentStateEnum.REPAIRING.value: "🔨",
        AgentStateEnum.REVIEWING.value: "👁️",
        AgentStateEnum.WAITING_FOR_USER.value: "⏳",
        AgentStateEnum.COMPLETED.value: "✅",
        AgentStateEnum.FAILED.value: "❌",
        AgentStateEnum.BLOCKED.value: "🚫",
    }
    return icons.get(state, "❓")
