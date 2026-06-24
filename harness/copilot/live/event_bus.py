"""EventBus — in-process pub/sub event bus for live events.

Thread-safe. Local-only. No external services.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional

from .live_event import LiveEvent

# Type alias for event subscribers
EventCallback = Callable[[LiveEvent], None]


class EventBus:
    """Simple in-process event bus.

    Supports multiple subscribers. Events are delivered synchronously.
    Thread-safe for publish and subscribe.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: List[EventCallback] = []
        self._events: List[LiveEvent] = []
        self._max_events: int = 1000

    @property
    def max_events(self) -> int:
        return self._max_events

    @max_events.setter
    def max_events(self, value: int) -> None:
        self._max_events = max(1, value)

    def subscribe(self, callback: EventCallback) -> None:
        """Register a subscriber callback.

        Args:
            callback: Called with each published LiveEvent.
        """
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: EventCallback) -> None:
        """Remove a subscriber callback."""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def publish(self, event: LiveEvent) -> None:
        """Publish a LiveEvent to all subscribers.

        Args:
            event: The event to publish.
        """
        with self._lock:
            self._events.append(event)
            # Trim to max
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]
            # Snapshot subscribers
            subs = list(self._subscribers)

        # Deliver outside lock to avoid deadlocks
        for cb in subs:
            try:
                cb(event)
            except Exception:
                pass  # Subscriber error must not break the bus

    def get_events(self, count: Optional[int] = None) -> List[LiveEvent]:
        """Get recent events.

        Args:
            count: Number of recent events to return (default: all).

        Returns:
            List of LiveEvent objects, newest last.
        """
        with self._lock:
            if count is not None and count < len(self._events):
                return list(self._events[-count:])
            return list(self._events)

    def clear(self) -> None:
        """Clear all stored events."""
        with self._lock:
            self._events.clear()

    def subscriber_count(self) -> int:
        """Return number of active subscribers."""
        with self._lock:
            return len(self._subscribers)


# Module-level singleton for convenience
_default_bus = EventBus()


def get_default_bus() -> EventBus:
    """Get the module-level default EventBus instance."""
    return _default_bus
