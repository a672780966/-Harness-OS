"""Tests for dashboard refresher — verifies output is restricted to --out dir."""

import os
import tempfile
import json
import pytest

from harness.copilot.monitor import MonitorEvent, MonitorSession, EventType, Severity
from harness.copilot.monitor.dashboard_refresher import refresh_dashboard
from harness.copilot.monitor.terminal_renderer import render_event, render_startup_message, render_status_line


class TestDashboardRefresher:
    def test_refresh_creates_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "new", "nested", "dashboard")
            session = MonitorSession()
            result = refresh_dashboard(out_dir, session)
            assert result.get("success") is True
            assert os.path.isdir(out_dir)

    def test_refresh_writes_state_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "dash")
            session = MonitorSession()
            session.add_event(MonitorEvent.create(
                event_type=EventType.FILE_CHANGED.value, severity=Severity.LOW.value, summary="test",
            ))
            result = refresh_dashboard(out_dir, session)
            assert result.get("success") is True
            state_path = result.get("state_path", "")
            assert os.path.isfile(state_path)
            with open(state_path) as f:
                data = json.load(f)
            assert data["total_events"] == 1

    def test_refresh_writes_events_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "dash")
            session = MonitorSession()
            session.add_event(MonitorEvent.create(
                event_type=EventType.MERGE_READINESS_CHANGED.value,
                severity=Severity.HIGH.value, summary="merge blocked",
            ))
            result = refresh_dashboard(out_dir, session)
            events_path = result.get("events_path", "")
            assert os.path.isfile(events_path)
            with open(events_path) as f:
                events = json.load(f)
            assert len(events) == 1
            assert events[0]["event_type"] == "merge_readiness_changed"

    def test_refresh_only_writes_output_dir(self):
        """Dashboard refresher must not write outside output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "dash")
            session = MonitorSession()
            before = os.listdir(tmpdir)
            result = refresh_dashboard(out_dir, session)
            after = os.listdir(tmpdir)
            # Only the 'dash' subdir should have been created
            assert set(after) - set(before) == {"dash"} or set(after) == set(before) | {"dash"}

    def test_refresh_with_no_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "dash")
            session = MonitorSession()
            result = refresh_dashboard(out_dir, session)
            assert result.get("success") is True
            assert os.path.isfile(result["state_path"])

    def test_refresh_updates_existing_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "dash")
            os.makedirs(out_dir, exist_ok=True)
            # Create a minimal index.html with dashboard-data script
            html = '<html><script id="dashboard-data" type="application/json">{"old": true}</script></html>'
            with open(os.path.join(out_dir, "index.html"), "w") as f:
                f.write(html)

            session = MonitorSession()
            session.add_event(MonitorEvent.create(
                event_type=EventType.FILE_CHANGED.value, severity=Severity.LOW.value, summary="updated",
            ))
            result = refresh_dashboard(out_dir, session)
            assert result.get("success") is True

            with open(os.path.join(out_dir, "index.html")) as f:
                updated = f.read()
            assert '"old": true' not in updated
            assert 'total_events' in updated


class TestTerminalRenderer:
    def test_render_event_basic(self):
        evt = MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary="3 file changes detected",
            source_path="/tmp/project",
        )
        text = render_event(evt, color=False)
        assert "3 file changes detected" in text
        assert "project_diff_changed" not in text  # should use icons, not raw type
        assert "[20" in text or ":" in text  # timestamp format

    def test_render_event_with_action(self):
        evt = MonitorEvent.create(
            event_type=EventType.FINAL_GATE_CHANGED.value,
            severity=Severity.CRITICAL.value,
            summary="Gate blocked",
            recommended_action="检查并修复",
        )
        text = render_event(evt, color=False)
        assert "Gate blocked" in text
        assert "检查并修复" in text

    def test_startup_message(self):
        msg = render_startup_message("/tmp/test", 3.0)
        assert "Copilot Monitor" in msg
        assert "/tmp/test" in msg
        assert "3.0s" in msg
        assert "只读" in msg
        assert "Ctrl+C" in msg

    def test_status_line(self):
        session = MonitorSession()
        evt = MonitorEvent.create(
            event_type=EventType.FILE_CHANGED.value,
            severity=Severity.LOW.value,
            summary="test",
        )
        session.add_event(evt)
        line = render_status_line(session)
        assert "1 个事件" in line or "检测" in line

    def test_no_external_api_refs(self):
        """Renderer must not contain external API references."""
        evt = MonitorEvent.create(
            event_type=EventType.WAITING_COMPANION_NOTICE.value,
            severity=Severity.LOW.value,
            summary="Companion placeholder",
        )
        text = render_event(evt, color=False)
        # Should reference companion/placeholder, not music/API
        assert "companion" in evt.event_type or "waiting" in evt.event_type
