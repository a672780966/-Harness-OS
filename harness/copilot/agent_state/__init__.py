"""Agent State — Phase 6 Agent State Machine Lite schema and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStateEnum(str, Enum):
    """All supported agent lifecycle states."""
    IDLE = "idle"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REPAIRING = "repairing"
    REVIEWING = "reviewing"
    WAITING_FOR_USER = "waiting_for_user"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class StateSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Priority order for conflict resolution (higher = wins)
_STATE_PRIORITY: Dict[str, int] = {
    AgentStateEnum.BLOCKED.value: 100,
    AgentStateEnum.FAILED.value: 90,
    AgentStateEnum.REPAIRING.value: 80,
    AgentStateEnum.REVIEWING.value: 70,
    AgentStateEnum.TESTING.value: 60,
    AgentStateEnum.IMPLEMENTING.value: 50,
    AgentStateEnum.PLANNING.value: 40,
    AgentStateEnum.WAITING_FOR_USER.value: 30,
    AgentStateEnum.COMPLETED.value: 20,
    AgentStateEnum.IDLE.value: 10,
}

# Completed states that can override lower-priority inference
_COMPLETED_OVERRIDE_STATES = {
    AgentStateEnum.COMPLETED.value,
}


def state_priority(state: str) -> int:
    return _STATE_PRIORITY.get(state, 0)


def is_completed_override(state: str) -> bool:
    return state in _COMPLETED_OVERRIDE_STATES


@dataclass
class AgentState:
    """Inferred agent lifecycle state.

    All fields are read-only observations. No agent control.
    """
    state: str = AgentStateEnum.IDLE.value
    confidence: float = 0.0
    source_events: List[str] = field(default_factory=list)
    summary: str = ""
    recommended_action: str = ""
    severity: str = StateSeverity.LOW.value
    blocking: bool = False
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "confidence": round(self.confidence, 2),
            "source_events": self.source_events,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
            "severity": self.severity,
            "blocking": self.blocking,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentStateTimeline:
    """Ordered timeline of agent states."""
    states: List[AgentState] = field(default_factory=list)

    def add(self, agent_state: AgentState) -> None:
        self.states.append(agent_state)

    def latest(self) -> Optional[AgentState]:
        return self.states[-1] if self.states else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "states": [s.to_dict() for s in self.states],
            "latest": self.states[-1].to_dict() if self.states else None,
        }


def infer_severity(state: str) -> str:
    """Map state to display severity."""
    mapping = {
        AgentStateEnum.BLOCKED.value: StateSeverity.CRITICAL.value,
        AgentStateEnum.FAILED.value: StateSeverity.HIGH.value,
        AgentStateEnum.REPAIRING.value: StateSeverity.HIGH.value,
        AgentStateEnum.REVIEWING.value: StateSeverity.MEDIUM.value,
        AgentStateEnum.TESTING.value: StateSeverity.MEDIUM.value,
        AgentStateEnum.IMPLEMENTING.value: StateSeverity.LOW.value,
        AgentStateEnum.PLANNING.value: StateSeverity.LOW.value,
        AgentStateEnum.WAITING_FOR_USER.value: StateSeverity.MEDIUM.value,
        AgentStateEnum.COMPLETED.value: StateSeverity.LOW.value,
        AgentStateEnum.IDLE.value: StateSeverity.LOW.value,
    }
    return mapping.get(state, StateSeverity.LOW.value)
