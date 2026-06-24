"""Event Schema — Phase 5 Realtime Monitor event types and data structures.

All events are read-only observations of project / loop state changes.
No agent control, no code modification, no external service calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(str, Enum):
    """All supported event types for the realtime monitor."""

    PROJECT_DIFF_CHANGED = "project_diff_changed"
    MODULE_RISK_CHANGED = "module_risk_changed"
    TEST_RESULT_CHANGED = "test_result_changed"
    EVAL_REPORT_CHANGED = "eval_report_changed"
    REVIEW_RESULT_CHANGED = "review_result_changed"
    FINAL_GATE_CHANGED = "final_gate_changed"
    LOOP_REPORT_CHANGED = "loop_report_changed"
    MERGE_READINESS_CHANGED = "merge_readiness_changed"
    TASK_CARD_RECOMMENDED = "task_card_recommended"
    WAITING_COMPANION_NOTICE = "waiting_companion_notice"
    FILE_CHANGED = "file_changed"
    AGENT_STATUS_CHANGED = "agent_status_changed"


class Severity(str, Enum):
    """Severity levels for monitor events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Event ID counter (monotonic, per-session)
_event_counter = [0]


def _next_event_id() -> str:
    _event_counter[0] += 1
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"evt-{ts}-{_event_counter[0]:04d}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z"


@dataclass
class MonitorEvent:
    """A single monitor observation.

    Immutable after creation. All fields are read-only observations.
    """
    event_id: str = ""
    event_type: str = ""
    timestamp: str = ""
    severity: str = Severity.LOW.value
    summary: str = ""
    description: str = ""
    affected_modules: List[str] = field(default_factory=list)
    recommended_action: str = ""
    source_path: str = ""
    old_value: Any = None
    new_value: Any = None
    readonly: bool = True

    @classmethod
    def create(
        cls,
        event_type: str,
        severity: str,
        summary: str,
        *,
        description: str = "",
        affected_modules: Optional[List[str]] = None,
        recommended_action: str = "",
        source_path: str = "",
        old_value: Any = None,
        new_value: Any = None,
    ) -> "MonitorEvent":
        return cls(
            event_id=_next_event_id(),
            event_type=event_type,
            timestamp=_now_iso(),
            severity=severity,
            summary=summary,
            description=description,
            affected_modules=affected_modules or [],
            recommended_action=recommended_action,
            source_path=source_path,
            old_value=old_value,
            new_value=new_value,
            readonly=True,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "summary": self.summary,
            "description": self.description,
            "affected_modules": self.affected_modules,
            "recommended_action": self.recommended_action,
            "source_path": self.source_path,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
            "readonly": self.readonly,
        }


@dataclass
class MonitorSession:
    """Aggregate state of a monitor session."""
    events: List[MonitorEvent] = field(default_factory=list)
    accumulated_summary: Dict[str, int] = field(default_factory=dict)

    def add_event(self, event: MonitorEvent) -> None:
        self.events.append(event)
        et = event.event_type
        self.accumulated_summary[et] = self.accumulated_summary.get(et, 0) + 1

    def latest_events(self, count: int = 10) -> List[MonitorEvent]:
        return self.events[-count:]

    def summary_text(self) -> str:
        parts = [f"共 {len(self.events)} 个事件"]
        for et, cnt in sorted(self.accumulated_summary.items()):
            parts.append(f"{et}: {cnt}")
        return " | ".join(parts)
