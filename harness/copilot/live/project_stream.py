"""ProjectStream — project live stream adapter.

Produces LiveEvent objects from a project's current state.
Uses existing CopilotDashboardState + AgentState + MonitorEvent.
Read-only. No agent control.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from ..view_models import build_dashboard
from ..monitor import EventType, MonitorEvent, MonitorSession, Severity
from ..agent_state.inference import infer_latest_from_events
from .live_event import LiveEvent, LiveEventSource
from .event_bus import EventBus


def capture_project_live_events(
    project_root: str,
    diff_ref: str = "HEAD~1",
    bus: Optional[EventBus] = None,
) -> List[LiveEvent]:
    """Capture current project state as LiveEvent(s).

    Builds dashboard, infers agent state, checks merge readiness,
    and produces a single consolidated LiveEvent.

    Args:
        project_root: Path to project root.
        diff_ref: Git diff base ref.
        bus: Optional EventBus to publish to.

    Returns:
        List of LiveEvent objects produced.
    """
    events: List[LiveEvent] = []

    if not os.path.isdir(project_root):
        evt = LiveEvent.create(
            source=LiveEventSource.PROJECT,
            event_type="project_error",
            summary=f"Project path not found: {project_root}",
            risk_level="high",
            blocking=True,
        )
        events.append(evt)
        if bus:
            bus.publish(evt)
        return events

    try:
        dashboard = build_dashboard(project_root, diff_ref=diff_ref)
    except Exception as e:
        evt = LiveEvent.create(
            source=LiveEventSource.PROJECT,
            event_type="project_error",
            summary=f"Failed to build dashboard: {e}",
            risk_level="high",
            blocking=True,
        )
        events.append(evt)
        if bus:
            bus.publish(evt)
        return events

    dashboard_dict = dashboard.to_dict()
    agent_state = dashboard_dict.get("agent_state", {})
    readiness = dashboard_dict.get("readiness", {})

    risk_level = dashboard_dict.get("overall_risk_level", "low")
    if readiness and readiness.get("state") == "block":
        risk_level = "critical"

    summary_parts = []
    if agent_state:
        summary_parts.append(f"Agent: {agent_state.get('summary', 'idle')}")
    if readiness:
        summary_parts.append(readiness.get("state_label", ""))
    if dashboard_dict.get("uncommitted_changes", 0) > 0:
        summary_parts.append(f"{dashboard_dict['uncommitted_changes']} uncommitted")

    evt = LiveEvent.create(
        source=LiveEventSource.PROJECT,
        event_type="project_state_update",
        summary=" | ".join(summary_parts) if summary_parts else "Project state captured",
        agent_state=agent_state,
        merge_readiness=readiness,
        risk_level=risk_level,
        recommended_action=agent_state.get("recommended_action", ""),
        blocking=(readiness.get("state") == "block") if readiness else False,
        payload={
            "branch": dashboard_dict.get("branch", ""),
            "project_name": dashboard_dict.get("project_name", ""),
            "uncommitted_changes": dashboard_dict.get("uncommitted_changes", 0),
            "module_count": dashboard_dict.get("module_count", 0),
        },
    )

    events.append(evt)
    if bus:
        bus.publish(evt)

    return events


def monitor_session_to_live_events(
    session: MonitorSession,
    source: str = LiveEventSource.PROJECT,
    bus: Optional[EventBus] = None,
) -> List[LiveEvent]:
    """Convert a MonitorSession's latest events to LiveEvent objects.

    Args:
        session: MonitorSession with accumulated events.
        source: Event source label.
        bus: Optional EventBus to publish to.

    Returns:
        List of LiveEvent objects.
    """
    events: List[LiveEvent] = []

    if not session.events:
        return events

    # Infer agent state from monitor events
    events_dicts = [e.to_dict() for e in session.events]
    astate = infer_latest_from_events(events_dicts)

    for me in session.latest_events(20):
        me_dict = me.to_dict()
        le = LiveEvent.create(
            source=source,
            event_type=me_dict.get("event_type", "unknown"),
            summary=me_dict.get("summary", ""),
            agent_state=astate.to_dict(),
            risk_level=me_dict.get("severity", "low"),
            recommended_action=me_dict.get("recommended_action", ""),
            blocking=(me_dict.get("severity") == "critical"),
            payload={
                "old_value": str(me_dict.get("old_value", "")),
                "new_value": str(me_dict.get("new_value", "")),
                "affected_modules": me_dict.get("affected_modules", []),
            },
        )
        events.append(le)
        if bus:
            bus.publish(le)

    return events
