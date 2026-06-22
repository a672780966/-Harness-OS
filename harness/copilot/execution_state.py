"""Execution State — agent execution state machine and tracking."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .schemas import AgentExecutionState, AgentPhase, now_iso


# Allowed phase transitions
PHASE_TRANSITIONS: Dict[AgentPhase, List[AgentPhase]] = {
    AgentPhase.IDLE: [AgentPhase.PLANNING, AgentPhase.WAITING],
    AgentPhase.PLANNING: [AgentPhase.IMPLEMENTING, AgentPhase.IDLE, AgentPhase.WAITING],
    AgentPhase.IMPLEMENTING: [AgentPhase.TESTING, AgentPhase.REPAIRING, AgentPhase.IDLE, AgentPhase.WAITING],
    AgentPhase.TESTING: [AgentPhase.REPAIRING, AgentPhase.REVIEWING, AgentPhase.IDLE, AgentPhase.WAITING],
    AgentPhase.REVIEWING: [AgentPhase.REPAIRING, AgentPhase.DONE, AgentPhase.IDLE, AgentPhase.WAITING],
    AgentPhase.REPAIRING: [AgentPhase.TESTING, AgentPhase.IMPLEMENTING, AgentPhase.IDLE, AgentPhase.WAITING],
    AgentPhase.WAITING: [AgentPhase.PLANNING, AgentPhase.IMPLEMENTING, AgentPhase.IDLE],
    AgentPhase.DONE: [AgentPhase.IDLE, AgentPhase.PLANNING],
}


def validate_transition(current: AgentPhase, next_phase: AgentPhase) -> bool:
    """Check if a phase transition is valid."""
    allowed = PHASE_TRANSITIONS.get(current, [])
    return next_phase in allowed


class ExecutionStateMachine:
    """Lightweight state machine for agent execution phases."""

    def __init__(self) -> None:
        self._state = AgentExecutionState()

    @property
    def state(self) -> AgentExecutionState:
        return self._state

    def transition_to(
        self,
        phase: AgentPhase,
        task: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> AgentExecutionState:
        """Attempt a phase transition. Records history on change."""
        if not validate_transition(self._state.phase, phase):
            raise ValueError(
                f"Invalid transition: {self._state.phase.value} → {phase.value}"
            )

        history_entry = {
            "from_phase": self._state.phase.value,
            "to_phase": phase.value,
            "task": self._state.current_task,
            "timestamp": now_iso(),
        }

        self._state = AgentExecutionState(
            phase=phase,
            current_task=task or self._state.current_task,
            task_id=task_id or self._state.task_id,
            started_at=now_iso(),
            elapsed_seconds=0.0,
            phase_history=self._state.phase_history + [history_entry],
            error_count=self._state.error_count,
            warnings=list(self._state.warnings),
        )
        return self._state

    def set_task(self, task: str, task_id: Optional[str] = None) -> AgentExecutionState:
        """Set the current task without changing phase."""
        self._state = AgentExecutionState(
            phase=self._state.phase,
            current_task=task,
            task_id=task_id or self._state.task_id,
            started_at=self._state.started_at,
            elapsed_seconds=self._state.elapsed_seconds,
            phase_history=list(self._state.phase_history),
            error_count=self._state.error_count,
            warnings=list(self._state.warnings),
        )
        return self._state

    def add_warning(self, warning: str) -> AgentExecutionState:
        """Add a warning without changing state."""
        new_warnings = list(self._state.warnings) + [warning]
        self._state = AgentExecutionState(
            phase=self._state.phase,
            current_task=self._state.current_task,
            task_id=self._state.task_id,
            started_at=self._state.started_at,
            elapsed_seconds=self._state.elapsed_seconds,
            phase_history=list(self._state.phase_history),
            error_count=self._state.error_count,
            warnings=new_warnings,
        )
        return self._state

    def increment_error(self) -> AgentExecutionState:
        """Increment error counter."""
        self._state = AgentExecutionState(
            phase=self._state.phase,
            current_task=self._state.current_task,
            task_id=self._state.task_id,
            started_at=self._state.started_at,
            elapsed_seconds=self._state.elapsed_seconds,
            phase_history=list(self._state.phase_history),
            error_count=self._state.error_count + 1,
            warnings=list(self._state.warnings),
        )
        return self._state

    def reset(self) -> AgentExecutionState:
        """Reset to idle."""
        self._state = AgentExecutionState()
        return self._state

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "phase": self._state.phase.value,
            "current_task": self._state.current_task,
            "task_id": self._state.task_id,
            "started_at": self._state.started_at,
            "elapsed_seconds": self._state.elapsed_seconds,
            "phase_history": self._state.phase_history,
            "error_count": self._state.error_count,
            "warnings": self._state.warnings,
        }


def estimate_elapsed(started_at: Optional[str]) -> float:
    """Estimate elapsed seconds from an ISO timestamp."""
    if not started_at:
        return 0.0
    try:
        from datetime import datetime
        start = datetime.fromisoformat(started_at)
        now = datetime.now(start.tzinfo if start.tzinfo else None)
        return (now - start).total_seconds()
    except (ValueError, TypeError):
        return 0.0
