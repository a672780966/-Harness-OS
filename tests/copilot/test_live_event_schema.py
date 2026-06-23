"""Tests for Phase 8A — LiveEvent schema."""
import json

from harness.copilot.live.live_event import LiveEvent, LiveEventSource


class TestLiveEventSchema:
    """LiveEvent schema tests."""

    def test_create_default(self):
        """LiveEvent.create returns a valid event."""
        evt = LiveEvent.create(
            source=LiveEventSource.PROJECT,
            event_type="test_event",
            summary="Test event",
        )
        assert evt.event_id.startswith("live-")
        assert evt.source == "project"
        assert evt.event_type == "test_event"
        assert evt.summary == "Test event"
        assert evt.readonly is True
        assert evt.blocking is False

    def test_to_dict(self):
        """to_dict returns a JSON-serializable dict."""
        evt = LiveEvent.create(
            source=LiveEventSource.PROJECT,
            event_type="test",
            summary="test",
            agent_state={"state": "completed", "confidence": 0.95},
            risk_level="low",
            blocking=False,
        )
        d = evt.to_dict()
        assert d["event_type"] == "test"
        assert d["agent_state"]["state"] == "completed"
        assert d["readonly"] is True
        assert d["source"] == "project"
        assert "event_id" in d
        assert "timestamp" in d

    def test_json_serializable(self):
        """LiveEvent is JSON serializable."""
        evt = LiveEvent.create(
            source=LiveEventSource.LOOP,
            event_type="loop_update",
            summary="Loop completed",
            agent_state={"state": "completed"},
            merge_readiness={"state": "pass", "state_label": "可以合并"},
            risk_level="low",
            blocking=False,
            payload={"instance_id": "test_123"},
        )
        js = json.dumps(evt.to_dict(), ensure_ascii=False, default=str)
        parsed = json.loads(js)
        assert parsed["event_type"] == "loop_update"
        assert parsed["source"] == "loop"
        assert parsed["payload"]["instance_id"] == "test_123"

    def test_from_dict(self):
        """from_dict restores a LiveEvent."""
        original = LiveEvent.create(
            source=LiveEventSource.PROJECT,
            event_type="test",
            summary="roundtrip",
            agent_state={"state": "blocked", "blocking": True},
        )
        d = original.to_dict()
        restored = LiveEvent.from_dict(d)
        assert restored.event_id == original.event_id
        assert restored.source == original.source
        assert restored.agent_state["state"] == "blocked"

    def test_source_constants(self):
        """Source constants exist."""
        assert LiveEventSource.PROJECT == "project"
        assert LiveEventSource.LOOP == "loop"

    def test_event_id_is_unique(self):
        """Each event gets a unique ID."""
        e1 = LiveEvent.create(source="project", event_type="t", summary="s")
        e2 = LiveEvent.create(source="project", event_type="t", summary="s")
        assert e1.event_id != e2.event_id

    def test_blocking_event(self):
        """Blocking events are marked correctly."""
        evt = LiveEvent.create(
            source=LiveEventSource.PROJECT,
            event_type="merge_blocked",
            summary="Merge blocked",
            blocking=True,
            risk_level="critical",
        )
        assert evt.blocking is True
        assert evt.risk_level == "critical"
