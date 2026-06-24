"""LoopStream — loop live stream adapter.

Produces LiveEvent objects from loop artifact state.
Uses existing LoopArtifacts + AgentState inference.
Read-only. No agent control.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from ..agent_state.inference import infer_from_loop_artifacts
from ..integration.loop_artifact_loader import load_loop_artifacts
from ..integration.loop_to_copilot_mapper import artifacts_to_dashboard
from .live_event import LiveEvent, LiveEventSource
from .event_bus import EventBus


def capture_loop_live_events(
    loop_run_dir: str,
    bus: Optional[EventBus] = None,
) -> List[LiveEvent]:
    """Capture current loop artifact state as LiveEvent(s).

    Loads loop artifacts, infers agent state, checks readiness,
    and produces a single consolidated LiveEvent.

    Args:
        loop_run_dir: Path to loop run directory.
        bus: Optional EventBus to publish to.

    Returns:
        List of LiveEvent objects produced.
    """
    events: List[LiveEvent] = []

    if not os.path.isdir(loop_run_dir):
        evt = LiveEvent.create(
            source=LiveEventSource.LOOP,
            event_type="loop_error",
            summary=f"Loop run directory not found: {loop_run_dir}",
            risk_level="high",
            blocking=True,
        )
        events.append(evt)
        if bus:
            bus.publish(evt)
        return events

    try:
        artifacts = load_loop_artifacts(loop_run_dir)
    except Exception as e:
        evt = LiveEvent.create(
            source=LiveEventSource.LOOP,
            event_type="loop_error",
            summary=f"Failed to load loop artifacts: {e}",
            risk_level="high",
            blocking=True,
        )
        events.append(evt)
        if bus:
            bus.publish(evt)
        return events

    # Infer agent state
    astate = infer_from_loop_artifacts(artifacts)
    astate_dict = astate.to_dict()

    # Build dashboard for readiness
    try:
        dashboard = artifacts_to_dashboard(artifacts)
        dashboard_dict = dashboard.to_dict()
        readiness = dashboard_dict.get("readiness", {})
        evidence = dashboard_dict.get("evidence", {})
    except Exception:
        readiness = {}
        evidence = {}

    risk_level = "low"
    if astate.state in ("blocked", "failed"):
        risk_level = "critical"
    elif astate.state in ("repairing",):
        risk_level = "high"

    summary = f"Loop: {astate.summary or 'state captured'}"

    evt = LiveEvent.create(
        source=LiveEventSource.LOOP,
        event_type="loop_state_update",
        summary=summary,
        agent_state=astate_dict,
        merge_readiness=readiness,
        risk_level=risk_level,
        recommended_action=astate.recommended_action or "",
        blocking=astate.blocking,
        payload={
            "run_dir": loop_run_dir,
            "instance_id": getattr(artifacts, "instance_id", ""),
            "tier": getattr(artifacts, "tier", ""),
            "load_errors": len(getattr(artifacts, "load_errors", [])),
            "evidence_present": bool(evidence),
        },
    )

    events.append(evt)
    if bus:
        bus.publish(evt)

    return events
