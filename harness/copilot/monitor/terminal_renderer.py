"""Terminal Renderer — render monitor events to user-readable terminal output.

No external dependencies. All output via print() to stdout/stderr.
"""

from __future__ import annotations

from typing import List, Optional

from . import MonitorEvent, Severity, EventType


_ANSI_RESET = "\033[0m"
_ANSI_RED = "\033[91m"
_ANSI_GREEN = "\033[92m"
_ANSI_YELLOW = "\033[93m"
_ANSI_BLUE = "\033[94m"
_ANSI_CYAN = "\033[96m"
_ANSI_GRAY = "\033[90m"
_ANSI_BOLD = "\033[1m"


def _severity_color(severity: str) -> str:
    return {
        Severity.CRITICAL.value: _ANSI_RED,
        Severity.HIGH.value: _ANSI_YELLOW,
        Severity.MEDIUM.value: _ANSI_BLUE,
        Severity.LOW.value: _ANSI_GRAY,
    }.get(severity, _ANSI_GRAY)


def _severity_icon(severity: str) -> str:
    return {
        Severity.CRITICAL.value: "🔴",
        Severity.HIGH.value: "🟠",
        Severity.MEDIUM.value: "🟡",
        Severity.LOW.value: "✅",
    }.get(severity, "❓")


def _event_icon(event_type: str) -> str:
    icons = {
        EventType.PROJECT_DIFF_CHANGED.value: "📝",
        EventType.FILE_CHANGED.value: "📄",
        EventType.MODULE_RISK_CHANGED.value: "⚠️",
        EventType.TEST_RESULT_CHANGED.value: "🧪",
        EventType.EVAL_REPORT_CHANGED.value: "📊",
        EventType.REVIEW_RESULT_CHANGED.value: "👁️",
        EventType.FINAL_GATE_CHANGED.value: "🚧",
        EventType.LOOP_REPORT_CHANGED.value: "📋",
        EventType.MERGE_READINESS_CHANGED.value: "🔀",
        EventType.TASK_CARD_RECOMMENDED.value: "📌",
        EventType.WAITING_COMPANION_NOTICE.value: "⏳",
        EventType.AGENT_STATUS_CHANGED.value: "🤖",
    }
    return icons.get(event_type, "📌")


def render_event(event: MonitorEvent, color: bool = True) -> str:
    """Render a single monitor event as a terminal line.

    Args:
        event: The event to render.
        color: Whether to use ANSI color codes.

    Returns:
        Formatted terminal line (no trailing newline).
    """
    timestamp = event.timestamp[11:19] if len(event.timestamp) >= 19 else event.timestamp
    icon = _event_icon(event.event_type)
    sev_icon = _severity_icon(event.severity)
    summary = event.summary

    if color:
        sev_color = _severity_color(event.severity)
        action = f" → {event.recommended_action}" if event.recommended_action else ""
        return (
            f"{_ANSI_GRAY}[{timestamp}]{_ANSI_RESET} "
            f"{icon} {sev_color}{sev_icon}{_ANSI_RESET} "
            f"{_ANSI_BOLD}{summary}{_ANSI_RESET}{action}"
        )
    else:
        action = f" → {event.recommended_action}" if event.recommended_action else ""
        return f"[{timestamp}] {icon} {sev_icon} {summary}{action}"


def render_event_detailed(event: MonitorEvent, color: bool = True) -> str:
    """Render event with full details (multi-line)."""
    lines = [render_event(event, color)]

    if event.description:
        if color:
            lines.append(f"  {_ANSI_GRAY}{event.description}{_ANSI_RESET}")
        else:
            lines.append(f"  {event.description}")

    if event.affected_modules:
        modules = ", ".join(event.affected_modules[:5])
        if color:
            lines.append(f"  {_ANSI_CYAN}模块: {modules}{_ANSI_RESET}")
        else:
            lines.append(f"  模块: {modules}")

    if event.recommended_action:
        if color:
            lines.append(f"  {_ANSI_GREEN}建议: {event.recommended_action}{_ANSI_RESET}")
        else:
            lines.append(f"  建议: {event.recommended_action}")

    return "\n".join(lines)


def render_session_header(session_summary: str) -> str:
    """Render a monitoring session header line."""
    return f"{_ANSI_BOLD}{_ANSI_CYAN}📡 Copilot Monitor — {session_summary}{_ANSI_RESET}"


def render_startup_message(project: str, interval: float) -> str:
    """Render startup message when monitor starts."""
    return (
        f"{_ANSI_GREEN}✅{_ANSI_RESET} "
        f"{_ANSI_BOLD}Harness Copilot Monitor 已启动{_ANSI_RESET}\n"
        f"  项目: {project}\n"
        f"  轮询间隔: {interval}s\n"
        f"  只读: 是 | 外部 API: 无 | Agent 控制: 无\n"
        f"  按 {_ANSI_YELLOW}Ctrl+C{_ANSI_RESET} 停止监控"
    )


def render_status_line(session) -> str:
    """Render a one-line status summary."""
    events_since_start = len(session.events)
    return (
        f"{_ANSI_GRAY}[{session.events[-1].timestamp[11:19] if session.events else '--:--:--'}]{_ANSI_RESET} "
        f"监控中 · 已检测 {events_since_start} 个事件 · "
        f"{_ANSI_GREEN}Ctrl+C{_ANSI_RESET} 停止"
    )


def render_agent_status(session, color: bool = True) -> str:
    """Render inferred agent lifecycle state from the monitor session.

    Args:
        session: MonitorSession with accumulated events.
        color: Whether to use ANSI color codes.

    Returns:
        One-line agent status string.
    """
    from ..agent_state.inference import infer_latest_from_events
    from ..agent_state.timeline import summarize_state

    if not session.events:
        if color:
            return f"{_ANSI_GRAY}💤 Agent 状态: 待命 (无事件){_ANSI_RESET}"
        return "💤 Agent 状态: 待命 (无事件)"

    events_dicts = [e.to_dict() for e in session.events]
    astate = infer_latest_from_events(events_dicts)
    summary = summarize_state(astate)
    icon = {
        "idle": "💤", "planning": "📋", "implementing": "🔧",
        "testing": "🧪", "repairing": "🔨", "reviewing": "👁️",
        "waiting_for_user": "⏳", "completed": "✅", "failed": "❌", "blocked": "🚫",
    }.get(astate.state, "❓")

    if color:
        severity_color = {
            "low": _ANSI_GRAY,
            "medium": _ANSI_YELLOW,
            "high": _ANSI_RED,
            "critical": _ANSI_RED + _ANSI_BOLD,
        }.get(astate.severity, _ANSI_GRAY)
        return (
            f"{_ANSI_BOLD}{icon} Agent{_ANSI_RESET} "
            f"{severity_color}{summary}{_ANSI_RESET} "
            f"{_ANSI_GRAY}(置信度: {astate.confidence:.0%}){_ANSI_RESET}"
        )
    return f"{icon} Agent: {summary} (置信度: {astate.confidence:.0%})"
