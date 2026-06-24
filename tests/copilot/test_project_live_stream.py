"""Tests for Phase 8A — Project live stream adapter."""
import json
import os

import pytest

from harness.copilot.live.project_stream import (
    capture_project_live_events,
    monitor_session_to_live_events,
)
from harness.copilot.live.live_event import LiveEventSource
from harness.copilot.monitor import MonitorSession, MonitorEvent, EventType, Severity


class TestProjectLiveStream:
    """Project stream tests."""

    def test_capture_project_live_events_returns_list(self):
        """capture_project_live_events returns a list with at least one event."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        events = capture_project_live_events(project_root)
        assert isinstance(events, list)
        assert len(events) >= 1
        evt = events[0]
        assert evt.event_type == "project_state_update"
        assert evt.source == LiveEventSource.PROJECT
        assert evt.readonly is True

    def test_project_event_has_agent_state(self):
        """Captured project event includes agent state."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        events = capture_project_live_events(project_root)
        evt = events[0]
        assert "state" in evt.agent_state
        assert "confidence" in evt.agent_state

    def test_project_event_json_serializable(self):
        """Project live event is JSON serializable."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        events = capture_project_live_events(project_root)
        js = json.dumps([e.to_dict() for e in events], ensure_ascii=False, default=str)
        parsed = json.loads(js)
        assert parsed[0]["source"] == "project"

    def test_project_event_has_payload(self):
        """Project event payload contains branch and project info."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        events = capture_project_live_events(project_root)
        evt = events[0]
        assert "branch" in evt.payload
        assert "project_name" in evt.payload
        assert "uncommitted_changes" in evt.payload

    def test_nonexistent_path_returns_error(self):
        """Non-existent project path returns error event."""
        events = capture_project_live_events("/nonexistent/path/xyz789")
        assert len(events) >= 1
        assert events[0].event_type == "project_error"
        assert events[0].blocking is True

    def test_monitor_session_to_live_events_empty(self):
        """Empty monitor session returns empty list."""
        session = MonitorSession()
        events = monitor_session_to_live_events(session)
        assert events == []

    def test_monitor_session_to_live_events(self):
        """Monitor session events are converted to LiveEvents."""
        session = MonitorSession()
        session.add_event(MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary="code changed",
        ))
        events = monitor_session_to_live_events(session)
        assert len(events) >= 1
        assert events[0].source == LiveEventSource.PROJECT
