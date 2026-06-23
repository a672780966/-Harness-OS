"""Tests for Phase 8A — EventBus."""
from harness.copilot.live.event_bus import EventBus
from harness.copilot.live.live_event import LiveEvent


class TestEventBus:
    """EventBus tests."""

    def test_subscribe_and_publish(self):
        """Published events are delivered to subscribers."""
        bus = EventBus()
        received = []

        def cb(event):
            received.append(event)

        bus.subscribe(cb)
        evt = LiveEvent.create(source="project", event_type="test", summary="hello")
        bus.publish(evt)
        assert len(received) == 1
        assert received[0].event_id == evt.event_id

    def test_multiple_subscribers(self):
        """All subscribers receive events."""
        bus = EventBus()
        r1, r2 = [], []

        bus.subscribe(lambda e: r1.append(e))
        bus.subscribe(lambda e: r2.append(e))
        bus.publish(LiveEvent.create(source="project", event_type="t", summary="s"))
        assert len(r1) == 1
        assert len(r2) == 1

    def test_unsubscribe(self):
        """Unsubscribed callbacks stop receiving events."""
        bus = EventBus()
        received = []

        def cb(event):
            received.append(event)

        bus.subscribe(cb)
        evt1 = LiveEvent.create(source="project", event_type="t", summary="a")
        bus.publish(evt1)
        bus.unsubscribe(cb)
        evt2 = LiveEvent.create(source="project", event_type="t", summary="b")
        bus.publish(evt2)
        assert len(received) == 1

    def test_get_events(self):
        """get_events returns published events."""
        bus = EventBus()
        evt1 = LiveEvent.create(source="project", event_type="t", summary="a")
        evt2 = LiveEvent.create(source="loop", event_type="t", summary="b")
        bus.publish(evt1)
        bus.publish(evt2)
        events = bus.get_events()
        assert len(events) == 2
        assert events[0].event_id == evt1.event_id

    def test_get_events_count(self):
        """get_events limits correctly."""
        bus = EventBus()
        for i in range(5):
            bus.publish(LiveEvent.create(source="project", event_type="t", summary=str(i)))
        assert len(bus.get_events(count=3)) == 3
        assert len(bus.get_events(count=10)) == 5

    def test_clear(self):
        """clear removes all events."""
        bus = EventBus()
        bus.publish(LiveEvent.create(source="project", event_type="t", summary="x"))
        bus.clear()
        assert len(bus.get_events()) == 0

    def test_subscriber_count(self):
        """subscriber_count returns correct count."""
        bus = EventBus()
        assert bus.subscriber_count() == 0
        bus.subscribe(lambda e: None)
        assert bus.subscriber_count() == 1
        bus.subscribe(lambda e: None)
        assert bus.subscriber_count() == 2

    def test_max_events_enforced(self):
        """Old events are trimmed when max_events is exceeded."""
        bus = EventBus()
        bus.max_events = 3
        for i in range(5):
            bus.publish(LiveEvent.create(source="project", event_type="t", summary=str(i)))
        assert len(bus.get_events()) == 3

    def test_get_default_bus(self):
        """Default bus singleton is accessible."""
        from harness.copilot.live.event_bus import get_default_bus
        bus = get_default_bus()
        assert bus is not None
        assert isinstance(bus, EventBus)

    def test_subscriber_error_does_not_break_bus(self):
        """A failing subscriber doesn't prevent other subscribers."""
        bus = EventBus()
        received = []

        def failing_cb(event):
            raise ValueError("Intentional failure")

        def good_cb(event):
            received.append(event)

        bus.subscribe(failing_cb)
        bus.subscribe(good_cb)
        bus.publish(LiveEvent.create(source="project", event_type="t", summary="x"))
        assert len(received) == 1
