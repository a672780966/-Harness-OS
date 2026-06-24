"""JSON Renderer — serialize ViewModels to JSON."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .view_models import (
    CopilotDashboardState, ModuleCardViewModel, RecentChangeViewModel,
    SuggestionListViewModel, TaskCardListViewModel, MergeReadinessViewModel,
    EvidencePackViewModel, WaitingCompanionViewModel,
)


def render_dashboard_json(dashboard: CopilotDashboardState) -> str:
    """Render the full dashboard as pretty JSON."""
    return json.dumps(dashboard.to_dict(), indent=2, ensure_ascii=False)


def render_modules_json(modules: List[ModuleCardViewModel]) -> str:
    """Render module cards as JSON."""
    return json.dumps(
        {"modules": [m.to_dict() for m in modules]},
        indent=2, ensure_ascii=False,
    )


def render_task_cards_json(cards: TaskCardListViewModel) -> str:
    """Render task cards as JSON."""
    return json.dumps(cards.to_dict(), indent=2, ensure_ascii=False)


def render_readiness_json(rm: MergeReadinessViewModel) -> str:
    """Render merge readiness as JSON."""
    return json.dumps(rm.to_dict(), indent=2, ensure_ascii=False)


def render_changes_json(changes: List[RecentChangeViewModel]) -> str:
    """Render recent changes as JSON."""
    return json.dumps(
        {"recent_changes": [c.to_dict() for c in changes]},
        indent=2, ensure_ascii=False,
    )


def is_json_serializable(obj: Any) -> bool:
    """Check if an object is JSON serializable."""
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError, OverflowError):
        return False
