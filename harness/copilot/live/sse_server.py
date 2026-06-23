"""SSEServer — local-only HTTP/SSE server skeleton.

Uses stdlib http.server. Binds to 127.0.0.1 only.
No external network access. Read-only.

Endpoints:
  GET /events   — SSE stream of live events
  GET /latest   — Latest N events as JSON
  GET /health   — Health check
"""
from __future__ import annotations

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional

from .event_bus import EventBus, get_default_bus
from .live_event import LiveEvent


class SSEHandler(BaseHTTPRequestHandler):
    """HTTP request handler for live event SSE stream.

    Binds to 127.0.0.1 only. No external access.
    """

    # Shared event bus reference (set by serve function)
    event_bus: EventBus = get_default_bus()

    def do_GET(self) -> None:
        if self.path == "/events":
            self._handle_sse()
        elif self.path.startswith("/latest"):
            self._handle_latest()
        elif self.path == "/health":
            self._handle_health()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def _handle_sse(self) -> None:
        """Stream events as Server-Sent Events."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Send existing events
        for evt in self.event_bus.get_events():
            data = json.dumps(evt.to_dict(), ensure_ascii=False, default=str)
            self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
            self.wfile.flush()

        # Subscribe for new events
        last_event_count = len(self.event_bus.get_events())

        # Poll for new events (simplified approach without async)
        # In real use, this would use a queue. For the skeleton,
        # we poll the event bus.
        try:
            while not getattr(self.server, "_stop", False):
                current_events = self.event_bus.get_events()
                if len(current_events) > last_event_count:
                    for evt in current_events[last_event_count:]:
                        data = json.dumps(evt.to_dict(), ensure_ascii=False, default=str)
                        self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    last_event_count = len(current_events)
                time.sleep(0.5)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _handle_latest(self) -> None:
        """Return latest events as JSON."""
        try:
            count_str = self.path.split("?count=")[-1] if "?count=" in self.path else "10"
            count = max(1, min(100, int(count_str)))
        except (ValueError, IndexError):
            count = 10

        events = self.event_bus.get_events(count=count)
        data = json.dumps(
            {"events": [e.to_dict() for e in events], "total": len(events)},
            indent=2, ensure_ascii=False, default=str,
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))

    def _handle_health(self) -> None:
        """Health check endpoint."""
        data = json.dumps({
            "status": "ok",
            "readonly": True,
            "subscribers": self.event_bus.subscriber_count(),
            "total_events": len(self.event_bus.get_events()),
            "local_only": True,
        }, indent=2)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default HTTP server logging."""
        pass


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    event_bus: Optional[EventBus] = None,
    once: bool = False,
) -> None:
    """Start the local SSE server.

    Args:
        host: Bind address (default: 127.0.0.1).
        port: Listen port (default: 8765).
        event_bus: EventBus instance (default: module-level singleton).
        once: If True, serve one request then stop.
    """
    if host != "127.0.0.1":
        print("Warning: only 127.0.0.1 is allowed for local-only server. Forcing 127.0.0.1.", file=sys.stderr)
        host = "127.0.0.1"

    if event_bus is not None:
        SSEHandler.event_bus = event_bus

    server = HTTPServer((host, port), SSEHandler)
    server._stop = False

    print(f"📡 Live Event Server starting on http://{host}:{port}", file=sys.stderr)
    print(f"   Endpoints:", file=sys.stderr)
    print(f"   GET http://{host}:{port}/events   — SSE stream", file=sys.stderr)
    print(f"   GET http://{host}:{port}/latest   — Latest events (JSON)", file=sys.stderr)
    print(f"   GET http://{host}:{port}/health   — Health check", file=sys.stderr)
    print(f"   Local-only: yes | External API: no | Read-only: yes", file=sys.stderr)
    print(file=sys.stderr)

    try:
        if once:
            # Handle one request then stop
            server.handle_request()
        else:
            server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nServer stopped.", file=sys.stderr)
    finally:
        server.server_close()
