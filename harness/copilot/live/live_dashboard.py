"""Live Dashboard — orchestrate live dashboard generation.

Captures current project/loop state as LiveEvents, builds initial dashboard
state, and renders the HTML page.

Read-only. Local-only. No external API.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ..view_models import build_dashboard
from ..agent_state.inference import infer_from_loop_artifacts
from ..integration.loop_artifact_loader import load_loop_artifacts
from ..integration.loop_to_copilot_mapper import artifacts_to_dashboard
from .project_stream import capture_project_live_events
from .loop_stream import capture_loop_live_events
from .event_bus import EventBus
from .live_html_renderer import render_live_dashboard


def build_live_dashboard(
    project_root: str,
    diff_ref: str = "HEAD~1",
    output_dir: str = "",
) -> Dict[str, Any]:
    """Build a live dashboard for a project.

    Captures current state, generates LiveEvents, renders HTML.

    Args:
        project_root: Path to project root.
        diff_ref: Git diff base ref.
        output_dir: Output directory for HTML file (optional).

    Returns:
        dict with success status, html_path, and initial_state.
    """
    result: Dict[str, Any] = {"success": False}

    if not os.path.isdir(project_root):
        result["error"] = f"Project path not found: {project_root}"
        return result

    # Capture live events
    events = capture_project_live_events(project_root, diff_ref=diff_ref)

    # Build initial state from events (use latest for cards, all for timeline)
    initial_state = _build_initial_state(events, project_root)

    # Render HTML
    try:
        html = render_live_dashboard(initial_state)
    except Exception as e:
        result["error"] = f"Failed to render HTML: {e}"
        return result

    # Write to file if output_dir specified
    if output_dir:
        out_dir = os.path.abspath(output_dir)
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as e:
            result["error"] = f"Cannot create output directory: {e}"
            return result

        # Write HTML
        html_path = os.path.join(out_dir, "index.html")
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
        except IOError as e:
            result["error"] = f"Failed to write HTML: {e}"
            return result

        # Write dashboard state JSON
        json_path = os.path.join(out_dir, "dashboard_state.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(initial_state, f, indent=2, ensure_ascii=False, default=str)
        except (IOError, TypeError) as e:
            result["error"] = f"Failed to write JSON: {e}"
            return result

        result["html_path"] = html_path
        result["json_path"] = json_path
        result["output_dir"] = out_dir

    result["success"] = True
    result["initial_state"] = initial_state
    return result


def build_live_dashboard_from_loop(
    loop_run_dir: str,
    output_dir: str = "",
) -> Dict[str, Any]:
    """Build a live dashboard from a loop run directory.

    Args:
        loop_run_dir: Path to loop run directory.
        output_dir: Output directory for HTML file (optional).

    Returns:
        dict with success status, html_path, and initial_state.
    """
    result: Dict[str, Any] = {"success": False}

    if not os.path.isdir(loop_run_dir):
        result["error"] = f"Loop run directory not found: {loop_run_dir}"
        return result

    # Capture live events
    events = capture_loop_live_events(loop_run_dir)

    # Build initial state
    initial_state = _build_loop_initial_state(events, loop_run_dir)

    # Render HTML
    try:
        html = render_live_dashboard(initial_state)
    except Exception as e:
        result["error"] = f"Failed to render HTML: {e}"
        return result

    # Write to file if output_dir specified
    if output_dir:
        out_dir = os.path.abspath(output_dir)
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as e:
            result["error"] = f"Cannot create output directory: {e}"
            return result

        html_path = os.path.join(out_dir, "index.html")
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
        except IOError as e:
            result["error"] = f"Failed to write HTML: {e}"
            return result

        json_path = os.path.join(out_dir, "dashboard_state.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(initial_state, f, indent=2, ensure_ascii=False, default=str)
        except (IOError, TypeError) as e:
            result["error"] = f"Failed to write JSON: {e}"
            return result

        result["html_path"] = html_path
        result["json_path"] = json_path
        result["output_dir"] = out_dir

    result["success"] = True
    result["initial_state"] = initial_state
    return result


def _build_initial_state(
    events: List[Any],
    project_root: str,
) -> Dict[str, Any]:
    """Build initial dashboard state dict from LiveEvents."""
    state: Dict[str, Any] = {
        "project_name": os.path.basename(project_root),
        "branch": "",
        "generated_at": "",
        "agent_state": {},
        "merge_readiness": {},
        "risk_level": "low",
        "blocking": False,
        "recommended_action": "",
        "events": [],
    }

    if events:
        latest = events[-1]
        state["agent_state"] = latest.agent_state
        state["merge_readiness"] = latest.merge_readiness
        state["risk_level"] = latest.risk_level
        state["blocking"] = latest.blocking
        state["recommended_action"] = latest.recommended_action
        state["generated_at"] = latest.timestamp
        state["branch"] = latest.payload.get("branch", "")
        state["project_name"] = latest.payload.get("project_name", state["project_name"])
        state["events"] = [e.to_dict() for e in events]

    # Fallback: try dashboard for more info
    if not state.get("branch") or not state.get("agent_state"):
        try:
            dashboard = build_dashboard(project_root)
            d = dashboard.to_dict()
            if not state.get("branch"):
                state["branch"] = d.get("branch", "")
            if not state.get("agent_state"):
                state["agent_state"] = d.get("agent_state", {})
                state["merge_readiness"] = d.get("readiness", {})
        except Exception:
            pass

    return state


def _build_loop_initial_state(
    events: List[Any],
    loop_run_dir: str,
) -> Dict[str, Any]:
    """Build initial dashboard state dict from loop LiveEvents."""
    state: Dict[str, Any] = {
        "project_name": os.path.basename(os.path.dirname(loop_run_dir)),
        "branch": "",
        "generated_at": "",
        "agent_state": {},
        "merge_readiness": {},
        "risk_level": "low",
        "blocking": False,
        "recommended_action": "",
        "events": [],
    }

    if events:
        latest = events[-1]
        state["agent_state"] = latest.agent_state
        state["merge_readiness"] = latest.merge_readiness
        state["risk_level"] = latest.risk_level
        state["blocking"] = latest.blocking
        state["recommended_action"] = latest.recommended_action
        state["generated_at"] = latest.timestamp
        state["project_name"] = latest.payload.get("instance_id", state["project_name"])
        state["branch"] = f"tier_{latest.payload.get('tier', '?')}"
        state["events"] = [e.to_dict() for e in events]

    return state
