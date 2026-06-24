"""LiveEvent — Phase 8A Event Stream Core Schema.

Bundles MonitorEvent, AgentState, MergeReadiness, and risk data
into a single JSON-serializable live event record.

Read-only. No external API. No agent control.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


_event_counter = [0]


def _next_id() -> str:
    _event_counter[0] += 1
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:18]
    return f"live-{ts}-{_event_counter[0]:04d}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.")[:23] + "Z"


@dataclass
class LiveEvent:
    """Single live event record aggregating all monitor state.

    All fields are read-only observations. No agent control.
    JSON-serializable via to_dict().
    """
    event_id: str = ""
    timestamp: str = ""
    source: str = ""  # "project" | "loop"
    event_type: str = ""  # inherited from MonitorEvent EventType
    agent_state: Dict[str, Any] = field(default_factory=dict)
    merge_readiness: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"
    summary: str = ""
    recommended_action: str = ""
    blocking: bool = False
    readonly: bool = True
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        source: str,
        event_type: str,
        summary: str,
        *,
        agent_state: Optional[Dict[str, Any]] = None,
        merge_readiness: Optional[Dict[str, Any]] = None,
        risk_level: str = "low",
        recommended_action: str = "",
        blocking: bool = False,
        payload: Optional[Dict[str, Any]] = None,
    ) -> "LiveEvent":
        return cls(
            event_id=_next_id(),
            timestamp=_now_iso(),
            source=source,
            event_type=event_type,
            agent_state=agent_state or {},
            merge_readiness=merge_readiness or {},
            risk_level=risk_level,
            summary=summary,
            recommended_action=recommended_action,
            blocking=blocking,
            readonly=True,
            payload=payload or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "event_type": self.event_type,
            "agent_state": self.agent_state,
            "merge_readiness": self.merge_readiness,
            "risk_level": self.risk_level,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
            "blocking": self.blocking,
            "readonly": self.readonly,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LiveEvent":
        return cls(
            event_id=d.get("event_id", ""),
            timestamp=d.get("timestamp", ""),
            source=d.get("source", ""),
            event_type=d.get("event_type", ""),
            agent_state=d.get("agent_state", {}),
            merge_readiness=d.get("merge_readiness", {}),
            risk_level=d.get("risk_level", "low"),
            summary=d.get("summary", ""),
            recommended_action=d.get("recommended_action", ""),
            blocking=d.get("blocking", False),
            readonly=d.get("readonly", True),
            payload=d.get("payload", {}),
        )


class LiveEventSource:
    """Constants for LiveEvent source field."""
    PROJECT = "project"
    LOOP = "loop"
