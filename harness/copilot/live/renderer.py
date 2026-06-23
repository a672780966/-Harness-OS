"""Renderer — render LiveEvent to user-facing outputs.

Supports JSON output (primary format for live stream).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .live_event import LiveEvent


def render_event_json(event: LiveEvent, indent: int = 2) -> str:
    """Render a single LiveEvent as JSON string.

    Args:
        event: The event to render.
        indent: JSON indent level.

    Returns:
        JSON string.
    """
    return json.dumps(event.to_dict(), indent=indent, ensure_ascii=False, default=str)


def render_events_json(events: List[LiveEvent], indent: int = 2) -> str:
    """Render a list of LiveEvents as a JSON array.

    Args:
        events: List of events.
        indent: JSON indent level.

    Returns:
        JSON string.
    """
    return json.dumps(
        {"events": [e.to_dict() for e in events], "total": len(events)},
        indent=indent, ensure_ascii=False, default=str,
    )


def render_event_terminal(event: LiveEvent, color: bool = True) -> str:
    """Render a single LiveEvent as a terminal-friendly line.

    Args:
        event: The event to render.
        color: Whether to use ANSI color codes (no-op for now).

    Returns:
        One-line status string.
    """
    ts = event.timestamp[11:19] if len(event.timestamp) >= 19 else event.timestamp
    icon_map = {
        "project_state_update": "📡",
        "loop_state_update": "🔄",
        "project_error": "❌",
        "loop_error": "❌",
    }
    icon = icon_map.get(event.event_type, "📌")
    blocking_flag = " 🚫" if event.blocking else ""
    return f"[{ts}] {icon} {event.summary}{blocking_flag}"
