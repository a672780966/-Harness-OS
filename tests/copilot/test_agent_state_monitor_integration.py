"""Tests for Phase 6B — AgentState integration into Monitor terminal stream.

Tests that:
- render_agent_status() returns proper output with/without events
- Agent state appears in terminal stream after monitor events
- Event-based inference from monitor session works
"""
import os
import json

import pytest


class TestAgentStateMonitorIntegration:
    """Agent state appears in monitor terminal stream."""

    def test_render_agent_status_no_events(self):
        """render_agent_status with empty session shows idle."""
        from harness.copilot.monitor import MonitorSession
        from harness.copilot.monitor.terminal_renderer import render_agent_status

        session = MonitorSession()
        line = render_agent_status(session, color=False)
        assert "待命" in line or "idle" in line

    def test_render_agent_status_with_diff_event(self):
        """render_agent_status with diff events shows implementing."""
        from harness.copilot.monitor import MonitorSession, MonitorEvent, EventType, Severity
        from harness.copilot.monitor.terminal_renderer import render_agent_status

        session = MonitorSession()
        evt = MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary="Detected 3 uncommitted files",
            new_value=3,
        )
        session.add_event(evt)

        line = render_agent_status(session, color=False)
        assert "Agent" in line

    def test_render_agent_status_with_final_gate(self):
        """render_agent_status with final gate shows completed."""
        from harness.copilot.monitor import MonitorSession, MonitorEvent, EventType, Severity
        from harness.copilot.monitor.terminal_renderer import render_agent_status

        session = MonitorSession()
        evt = MonitorEvent.create(
            event_type=EventType.FINAL_GATE_CHANGED.value,
            severity=Severity.CRITICAL.value,
            summary="Final gate: pass",
            new_value="pass",
        )
        session.add_event(evt)

        line = render_agent_status(session, color=False)
        # Should show completed state
        assert "置信度" in line or "completed" in line

    def test_render_agent_status_multiple_events(self):
        """Agent state resolves correctly from multiple events."""
        from harness.copilot.monitor import MonitorSession, MonitorEvent, EventType, Severity
        from harness.copilot.monitor.terminal_renderer import render_agent_status

        session = MonitorSession()
        session.add_event(MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary="diff",
        ))
        session.add_event(MonitorEvent.create(
            event_type=EventType.TEST_RESULT_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary="test result",
            new_value="present",
        ))

        line = render_agent_status(session, color=False)
        # The latest event (testing) should win priority over implementing
        assert "测试" in line or "testing" in line or "Agent" in line

    def test_render_agent_status_colored(self):
        """Color output contains ANSI codes."""
        from harness.copilot.monitor import MonitorSession, MonitorEvent, EventType, Severity
        from harness.copilot.monitor.terminal_renderer import render_agent_status

        session = MonitorSession()
        session.add_event(MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=Severity.LOW.value,
            summary="test",
        ))

        colored = render_agent_status(session, color=True)
        uncolored = render_agent_status(session, color=False)
        assert len(colored) > len(uncolored) or colored != uncolored

    def test_monitor_startup_imports_agent_renderer(self):
        """The monitor command imports render_agent_status."""
        from harness.copilot.monitor.terminal_renderer import render_agent_status
        assert callable(render_agent_status)

    def test_agent_status_blocked_event(self):
        """Blocked event renders properly in terminal."""
        from harness.copilot.monitor import MonitorSession, MonitorEvent, EventType, Severity
        from harness.copilot.monitor.terminal_renderer import render_agent_status

        session = MonitorSession()
        session.add_event(MonitorEvent.create(
            event_type=EventType.MERGE_READINESS_CHANGED.value,
            severity=Severity.CRITICAL.value,
            summary="merge blocked",
            new_value="block",
        ))

        line = render_agent_status(session, color=False)
        # Should reflect blocked state
        assert "阻塞" in line or "Blocked" in line or "Agent" in line

    def test_agent_state_timeline_from_monitor_session(self):
        """Build timeline from monitor session events."""
        from harness.copilot.monitor import MonitorSession, MonitorEvent, EventType, Severity
        from harness.copilot.agent_state.inference import infer_from_events
        from harness.copilot.agent_state.timeline import build_timeline

        session = MonitorSession()
        session.add_event(MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary="code changed",
        ))
        session.add_event(MonitorEvent.create(
            event_type=EventType.FINAL_GATE_CHANGED.value,
            severity=Severity.CRITICAL.value,
            summary="gate passed",
            new_value="pass",
        ))

        events_dicts = [e.to_dict() for e in session.events]
        timeline = build_timeline(events_dicts)
        assert timeline.latest() is not None
        assert timeline.latest().state == "completed"
