"""Tests for AgentState inference from monitor events and loop artifacts."""

from harness.copilot.agent_state import AgentStateEnum
from harness.copilot.agent_state.inference import (
    infer_from_events, infer_latest_from_events, infer_from_loop_artifacts,
)
from harness.copilot.monitor import EventType, Severity, MonitorEvent


def _make_evt(event_type: str, summary: str = "", old=None, new=None):
    return MonitorEvent.create(
        event_type=event_type, severity=Severity.LOW.value,
        summary=summary or event_type, old_value=old, new_value=new,
    ).to_dict()


class TestInferFromEvents:
    def test_empty_events(self):
        tl = infer_from_events([])
        assert tl.latest() is None

    def test_project_diff_changed(self):
        events = [_make_evt(EventType.PROJECT_DIFF_CHANGED.value)]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.IMPLEMENTING.value

    def test_final_gate_passed(self):
        events = [_make_evt(EventType.FINAL_GATE_CHANGED.value, new="pass")]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.COMPLETED.value

    def test_final_gate_blocked(self):
        events = [_make_evt(EventType.FINAL_GATE_CHANGED.value, new="block")]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.BLOCKED.value
        assert latest.blocking is True

    def test_review_result(self):
        events = [_make_evt(EventType.REVIEW_RESULT_CHANGED.value)]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.REVIEWING.value

    def test_task_card_recommended(self):
        events = [_make_evt(EventType.TASK_CARD_RECOMMENDED.value)]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.REPAIRING.value

    def test_merge_readiness_blocked(self):
        events = [_make_evt(EventType.MERGE_READINESS_CHANGED.value, new="block")]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.BLOCKED.value

    def test_test_result_changed(self):
        events = [_make_evt(EventType.TEST_RESULT_CHANGED.value, new="present")]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.TESTING.value

    def test_multiple_events_completed_wins(self):
        events = [
            _make_evt(EventType.PROJECT_DIFF_CHANGED.value),
            _make_evt(EventType.FINAL_GATE_CHANGED.value, new="pass"),
        ]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.COMPLETED.value

    def test_multiple_events_blocked_wins(self):
        events = [
            _make_evt(EventType.TEST_RESULT_CHANGED.value),
            _make_evt(EventType.MERGE_READINESS_CHANGED.value, new="block"),
        ]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.BLOCKED.value

    def test_no_match_returns_idle(self):
        events = [{"event_type": "unknown_type", "summary": "x"}]
        latest = infer_latest_from_events(events)
        assert latest.state == AgentStateEnum.IDLE.value


class TestInferFromLoopArtifacts:
    def test_none_artifacts(self):
        state = infer_from_loop_artifacts(None)
        assert state.state == AgentStateEnum.IDLE.value

    def test_completed_gate(self):
        class MockArtifacts:
            final_gate_result = type('obj', (object,), {'content': 'Final Gate: PASS'})

        state = infer_from_loop_artifacts(MockArtifacts)
        assert state.state == AgentStateEnum.COMPLETED.value

    def test_blocked_review(self):
        class MockArtifacts:
            final_review_envelope = {"codex_approved": False}

        state = infer_from_loop_artifacts(MockArtifacts)
        assert state.state == AgentStateEnum.BLOCKED.value

    def test_resolved_eval(self):
        class MockArtifacts:
            eval_report = {"resolved_official": True, "tests_passed": 45, "tests_total": 45}

        state = infer_from_loop_artifacts(MockArtifacts)
        assert state.state == AgentStateEnum.COMPLETED.value

    def test_failed_eval(self):
        class MockArtifacts:
            eval_report = {"resolved_official": False, "tests_passed": 40, "tests_total": 45}

        state = infer_from_loop_artifacts(MockArtifacts)
        assert state.state == AgentStateEnum.FAILED.value
