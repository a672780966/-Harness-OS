"""Tests for monitor watcher — project and loop poll-based monitoring."""

import os
import tempfile
import pytest

from harness.copilot.monitor import MonitorEvent, MonitorSession, EventType, Severity
from harness.copilot.monitor.watcher import ProjectWatcher, LoopWatcher


class TestProjectWatcher:
    def test_init(self):
        w = ProjectWatcher("/tmp", interval=5.0)
        assert w.project_root == "/tmp"
        assert w.interval == 5.0
        assert w.session is not None
        assert w._previous_snapshot is None

    def test_poll_once_first_call_no_events(self):
        w = ProjectWatcher("/tmp")
        events = w.poll_once()
        assert events == []
        assert w._previous_snapshot is not None

    def test_poll_once_returns_events_on_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            import subprocess
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.name", "T"], cwd=tmpdir, capture_output=True, timeout=5)
            fpath = os.path.join(tmpdir, "a.py")
            with open(fpath, "w") as f:
                f.write("# v1")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True, timeout=5)

            w = ProjectWatcher(tmpdir)
            w.poll_once()  # first: no events

            # Now change a file
            with open(fpath, "w") as f:
                f.write("# v2")

            events = w.poll_once()
            # Should detect file changes
            event_types = [e.event_type for e in events]
            assert EventType.PROJECT_DIFF_CHANGED.value in event_types or EventType.FILE_CHANGED.value in event_types

    def test_callback_fired(self):
        received = []

        def cb(evt):
            received.append(evt)

        with tempfile.TemporaryDirectory() as tmpdir:
            import subprocess
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.name", "T"], cwd=tmpdir, capture_output=True, timeout=5)
            with open(os.path.join(tmpdir, "a.py"), "w") as f:
                f.write("# v1")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True, timeout=5)

            w = ProjectWatcher(tmpdir, on_event=cb)
            w.poll_once()  # first: snapshot only
            assert len(received) == 0

            with open(os.path.join(tmpdir, "a.py"), "w") as f:
                f.write("# v2")
            w.poll_once()
            assert len(received) >= 1

    def test_run_max_polls(self):
        w = ProjectWatcher("/tmp", interval=0.1)
        w.run(max_polls=2)
        # Should have polled twice without error
        assert w._running is False or w._previous_snapshot is not None

    def test_stop(self):
        w = ProjectWatcher("/tmp")
        w.stop()
        assert w._running is False

    def test_events_are_readonly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            import subprocess
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "config", "user.name", "T"], cwd=tmpdir, capture_output=True, timeout=5)
            with open(os.path.join(tmpdir, "a.py"), "w") as f:
                f.write("# v1")
            subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True, timeout=5)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True, timeout=5)

            w = ProjectWatcher(tmpdir)
            w.poll_once()
            with open(os.path.join(tmpdir, "a.py"), "w") as f:
                f.write("# v2")
            events = w.poll_once()
            for e in events:
                assert e.readonly is True


class TestLoopWatcher:
    def test_init(self):
        w = LoopWatcher("/tmp/loop", interval=5.0)
        assert w.loop_run_dir == "/tmp/loop"
        assert w.interval == 5.0

    def test_poll_once_first_call_no_events(self):
        w = LoopWatcher("/tmp")
        events = w.poll_once()
        assert events == []

    def test_poll_once_nonexistent_dir(self):
        w = LoopWatcher("/nonexistent/loop")
        w.poll_once()  # no crash
        events = w.poll_once()  # second call
        assert isinstance(events, list)

    def test_run_max_polls(self):
        w = LoopWatcher("/tmp", interval=0.1)
        w.run(max_polls=2)
        assert w._running is False or w._previous_snapshot is not None

    def test_stop(self):
        w = LoopWatcher("/tmp")
        w.stop()
        assert w._running is False
