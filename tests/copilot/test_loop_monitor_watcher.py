"""Tests for loop monitor watcher — verifies loop artifact change detection."""

import os
import json
import tempfile
import pytest

from harness.copilot.monitor.watcher import LoopWatcher
from harness.copilot.monitor import EventType
from harness.copilot.monitor.snapshot import capture_loop_snapshot, snapshot_diff


class TestLoopWatcherArtifactDetection:
    def test_artifact_appearance_triggers_event(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            w = LoopWatcher(tmpdir)
            w.poll_once()  # first: no artifacts

            # Create eval_report.json
            with open(os.path.join(tmpdir, "eval_report.json"), "w") as f:
                json.dump({"resolved": True, "tests": 45, "passed": 45}, f)

            events = w.poll_once()
            event_types = [e.event_type for e in events]
            assert EventType.EVAL_REPORT_CHANGED.value in event_types

    def test_test_result_appearance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            w = LoopWatcher(tmpdir)
            w.poll_once()

            with open(os.path.join(tmpdir, "test_result.json"), "w") as f:
                json.dump({"passed": 45, "failed": 0}, f)

            events = w.poll_once()
            event_types = [e.event_type for e in events]
            assert EventType.TEST_RESULT_CHANGED.value in event_types

    def test_review_appearance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            w = LoopWatcher(tmpdir)
            w.poll_once()

            with open(os.path.join(tmpdir, "final_review_envelope.json"), "w") as f:
                json.dump({"codex_approved": False, "issues": ["EOF loop"]}, f)

            events = w.poll_once()
            event_types = [e.event_type for e in events]
            assert EventType.REVIEW_RESULT_CHANGED.value in event_types

    def test_final_gate_appearance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            w = LoopWatcher(tmpdir)
            w.poll_once()

            with open(os.path.join(tmpdir, "final_gate_result.md"), "w") as f:
                f.write("# Final Gate: PASS")

            events = w.poll_once()
            event_types = [e.event_type for e in events]
            assert EventType.FINAL_GATE_CHANGED.value in event_types

    def test_loop_report_appearance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            w = LoopWatcher(tmpdir)
            w.poll_once()

            with open(os.path.join(tmpdir, "loop_report.md"), "w") as f:
                f.write("# Loop Report: Complete")

            events = w.poll_once()
            event_types = [e.event_type for e in events]
            assert EventType.LOOP_REPORT_CHANGED.value in event_types

    def test_multiple_artifact_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            w = LoopWatcher(tmpdir)
            w.poll_once()

            # Create multiple artifacts at once
            for fname in ("eval_report.json", "test_result.json", "final_gate_result.md"):
                with open(os.path.join(tmpdir, fname), "w") as f:
                    f.write("{}" if fname.endswith(".json") else "# Gate\n")

            events = w.poll_once()
            # Should detect multiple events
            assert len(events) >= 1

    def test_events_are_readonly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            w = LoopWatcher(tmpdir)
            w.poll_once()

            with open(os.path.join(tmpdir, "eval_report.json"), "w") as f:
                json.dump({"resolved": True}, f)

            events = w.poll_once()
            for e in events:
                assert e.readonly is True


class TestLoopSnapshotDiff:
    def test_snapshot_diff_detects_artifact_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old = capture_loop_snapshot(tmpdir)

            with open(os.path.join(tmpdir, "eval_report.json"), "w") as f:
                json.dump({"resolved": True}, f)

            new = capture_loop_snapshot(tmpdir)
            diffs = snapshot_diff(old, new)
            # Should detect eval_results presence change
            assert any("eval_results" in k for k in diffs)
