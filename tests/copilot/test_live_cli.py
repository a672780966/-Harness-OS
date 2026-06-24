"""Tests for Phase 8A — Live event CLI commands."""
import os
import json

import pytest

from harness.copilot.live.live_event import LiveEvent
from harness.copilot.live.event_bus import EventBus
from harness.copilot.live.project_stream import capture_project_live_events
from harness.copilot.live.renderer import render_events_json


class TestLiveCLI:
    """Live CLI tests."""

    def test_cli_functions_importable(self):
        """CLI command functions are importable."""
        from harness.copilot.cli import (
            cmd_live_events, cmd_live_events_from_loop, cmd_live_server,
        )
        assert callable(cmd_live_events)
        assert callable(cmd_live_events_from_loop)
        assert callable(cmd_live_server)

    def test_live_events_json_output(self):
        """capture_project_live_events produces JSON-printable output."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        events = capture_project_live_events(project_root)
        js = render_events_json(events)
        parsed = json.loads(js)
        assert "events" in parsed
        assert "total" in parsed
        assert parsed["total"] >= 1
        assert parsed["events"][0]["readonly"] is True

    def test_live_events_from_loop_cli_import(self):
        """live-events-from-loop CLI path validation works."""
        import argparse
        from harness.copilot.cli import cmd_live_events_from_loop
        args = argparse.Namespace(loop_run_dir="/nonexistent_loop_dir_xyz")
        with pytest.raises(SystemExit):
            cmd_live_events_from_loop(args)

    def test_event_bus_with_project_stream(self):
        """EventBus can be populated by project stream."""
        bus = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        capture_project_live_events(project_root, bus=bus)

        assert len(received) >= 1
        assert received[0].source == "project"

    def test_renderer_formats(self):
        """Renderer produces valid JSON."""
        evt = LiveEvent.create(source="project", event_type="test", summary="x")
        from harness.copilot.live.renderer import render_event_json, render_events_json, render_event_terminal

        js = render_event_json(evt)
        parsed = json.loads(js)
        assert parsed["event_type"] == "test"

        js_list = render_events_json([evt])
        parsed_list = json.loads(js_list)
        assert parsed_list["total"] == 1

        terminal = render_event_terminal(evt, color=False)
        assert "test" in terminal or "x" in terminal
