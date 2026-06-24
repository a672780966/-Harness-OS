"""Tests for AgentState schema."""

from harness.copilot.agent_state import (
    AgentState, AgentStateEnum, AgentStateTimeline,
    StateSeverity, infer_severity,
)


class TestAgentStateSchema:
    def test_default_state(self):
        s = AgentState()
        assert s.state == AgentStateEnum.IDLE.value
        assert s.confidence == 0.0
        assert s.source_events == []
        assert s.blocking is False

    def test_full_state(self):
        s = AgentState(
            state=AgentStateEnum.IMPLEMENTING.value,
            confidence=0.8,
            source_events=["project_diff_changed"],
            summary="Agent modifying code",
            recommended_action="wait",
            severity=StateSeverity.LOW.value,
            blocking=False,
        )
        assert s.state == "implementing"
        assert s.confidence == 0.8
        assert s.summary == "Agent modifying code"

    def test_to_dict(self):
        s = AgentState(state=AgentStateEnum.BLOCKED.value, confidence=0.9, blocking=True)
        d = s.to_dict()
        assert d["state"] == "blocked"
        assert d["confidence"] == 0.9
        assert d["blocking"] is True
        assert "timestamp" in d

    def test_enum_values(self):
        assert AgentStateEnum.IDLE.value == "idle"
        assert AgentStateEnum.PLANNING.value == "planning"
        assert AgentStateEnum.IMPLEMENTING.value == "implementing"
        assert AgentStateEnum.TESTING.value == "testing"
        assert AgentStateEnum.REPAIRING.value == "repairing"
        assert AgentStateEnum.REVIEWING.value == "reviewing"
        assert AgentStateEnum.WAITING_FOR_USER.value == "waiting_for_user"
        assert AgentStateEnum.COMPLETED.value == "completed"
        assert AgentStateEnum.FAILED.value == "failed"
        assert AgentStateEnum.BLOCKED.value == "blocked"

    def test_10_states(self):
        assert len(AgentStateEnum) == 10

    def test_severity_inference(self):
        assert infer_severity(AgentStateEnum.BLOCKED.value) == StateSeverity.CRITICAL.value
        assert infer_severity(AgentStateEnum.FAILED.value) == StateSeverity.HIGH.value
        assert infer_severity(AgentStateEnum.COMPLETED.value) == StateSeverity.LOW.value
        assert infer_severity(AgentStateEnum.IDLE.value) == StateSeverity.LOW.value


class TestAgentStateTimeline:
    def test_empty(self):
        tl = AgentStateTimeline()
        assert tl.latest() is None
        assert tl.states == []

    def test_add(self):
        tl = AgentStateTimeline()
        tl.add(AgentState(state=AgentStateEnum.IMPLEMENTING.value))
        tl.add(AgentState(state=AgentStateEnum.COMPLETED.value))
        assert len(tl.states) == 2
        last = tl.latest()
        assert last is not None
        assert last.state == AgentStateEnum.COMPLETED.value

    def test_to_dict(self):
        tl = AgentStateTimeline()
        tl.add(AgentState(state=AgentStateEnum.IDLE.value))
        d = tl.to_dict()
        assert len(d["states"]) == 1
        assert d["latest"]["state"] == "idle"
