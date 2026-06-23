"""Tests for Phase 8A — Loop live stream adapter."""
import json
import os

import pytest

from harness.copilot.live.loop_stream import capture_loop_live_events
from harness.copilot.live.live_event import LiveEventSource


class TestLoopLiveStream:
    """Loop stream tests."""

    def test_nonexistent_path_returns_error(self):
        """Non-existent loop path returns error event."""
        events = capture_loop_live_events("/nonexistent/loop/run/dir")
        assert len(events) >= 1
        assert events[0].event_type == "loop_error"
        assert events[0].blocking is True
        assert events[0].source == LiveEventSource.LOOP

    def test_event_has_required_fields(self):
        """Loop error event has expected structure."""
        events = capture_loop_live_events("/tmp/nonexistent_loop_run_xyz")
        evt = events[0]
        d = evt.to_dict()
        assert "event_id" in d
        assert "timestamp" in d
        assert "source" in d
        assert "event_type" in d
        assert "agent_state" in d
        assert "merge_readiness" in d
        assert "risk_level" in d
        assert "summary" in d
        assert "blocking" in d
        assert "readonly" in d
        assert d["readonly"] is True

    def test_error_event_json_serializable(self):
        """Error event is JSON serializable."""
        events = capture_loop_live_events("/tmp/nonexistent_loop")
        js = json.dumps([e.to_dict() for e in events], ensure_ascii=False, default=str)
        parsed = json.loads(js)
        assert parsed[0]["event_type"] == "loop_error"
        assert parsed[0]["readonly"] is True

    def test_source_constant(self):
        """Source is 'loop'."""
        events = capture_loop_live_events("/tmp/fake_loop_path_12345")
        assert events[0].source == "loop"

    def test_multiple_calls_return_consistent_structure(self):
        """Multiple calls produce consistent event structure."""
        e1 = capture_loop_live_events("/tmp/fake_1")
        e2 = capture_loop_live_events("/tmp/fake_2")
        keys1 = set(e1[0].to_dict().keys())
        keys2 = set(e2[0].to_dict().keys())
        assert keys1 == keys2
