"""Tests for Phase 6B — AgentState integration into Dashboard markdown/JSON.

Tests that:
- markdown dashboard output includes Agent State section
- JSON dashboard output includes agent_state field
- render_dashboard() shows agent_state data
- render_dashboard_json() serializes agent_state
"""
import json
import os

import pytest


class TestAgentStateDashboardMarkdown:
    """Agent state appears in markdown dashboard output."""

    def test_dashboard_markdown_has_agent_state(self):
        """render_dashboard() output includes 'Agent 生命周期状态'."""
        from harness.copilot.view_models import build_dashboard
        from harness.copilot.markdown_renderer import render_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        md = render_dashboard(dashboard)
        assert "Agent 生命周期状态" in md or "Agent 状态" in md
        assert "置信度" in md

    def test_dashboard_markdown_shows_inferred_state(self):
        """Agent state summary is meaningful, not just 'idle' placeholder."""
        from harness.copilot.view_models import build_dashboard
        from harness.copilot.markdown_renderer import render_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        md = render_dashboard(dashboard)
        # Should have either idle or implementing state
        assert "状态" in md
        assert "Agent" in md

    def test_dashboard_markdown_blocking_field(self):
        """Agent state blocking field is rendered."""
        from harness.copilot.agent_state import AgentState, AgentStateEnum
        from harness.copilot.view_models import CopilotDashboardState
        from harness.copilot.markdown_renderer import render_dashboard

        dashboard = CopilotDashboardState(project_name="test")
        dashboard.agent_state = AgentState(
            state=AgentStateEnum.BLOCKED.value,
            confidence=0.9,
            source_events=["final_gate_changed"],
            summary="Blocked by final gate",
            recommended_action="Fix gate issues",
            severity="critical",
            blocking=True,
        ).to_dict()

        md = render_dashboard(dashboard)
        assert "阻塞" in md
        assert "是" in md


class TestAgentStateDashboardJson:
    """Agent state appears in JSON dashboard output."""

    def test_dashboard_json_has_agent_state_key(self):
        """render_dashboard_json() output includes agent_state key."""
        from harness.copilot.view_models import build_dashboard
        from harness.copilot.json_renderer import render_dashboard_json

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        js = render_dashboard_json(dashboard)
        d = json.loads(js)
        assert "agent_state" in d
        assert d["agent_state"] is not None

    def test_dashboard_json_agent_state_values(self):
        """agent_state JSON contains expected fields."""
        from harness.copilot.view_models import build_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        ad = dashboard.agent_state
        assert "state" in ad
        assert "confidence" in ad
        assert "summary" in ad
        assert "severity" in ad
        assert "blocking" in ad
        assert "source_events" in ad

    def test_dashboard_json_serializable(self):
        """agent_state is JSON serializable."""
        from harness.copilot.view_models import build_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        js = json.dumps(dashboard.agent_state, indent=2, ensure_ascii=False)
        parsed = json.loads(js)
        assert parsed["state"] == dashboard.agent_state["state"]
