"""Tests for Phase 6B — AgentState integration into HTML Shell pages.

Tests that:
- render_html_dashboard() includes agent-state section when data present
- render_loop_html_dashboard() includes agent-state section
- Agent state card HTML contains expected fields
"""
import json
import os

import pytest


class TestAgentStateShellIntegration:
    """Agent state appears in HTML shell pages."""

    def test_project_html_has_agent_state_section(self):
        """render_html_dashboard output includes agent-state tab content."""
        from harness.copilot.shell.html_renderer import render_html_dashboard
        from harness.copilot.view_models import build_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        dashboard_dict = dashboard.to_dict()

        html = render_html_dashboard(dashboard_dict, title="Test Dashboard")
        assert "agent-state" in html
        assert "🤖" in html  # Agent state icon in tab nav

    def test_project_html_agent_state_card(self):
        """HTML contains agent state card with summary."""
        from harness.copilot.shell.html_renderer import render_html_dashboard
        from harness.copilot.view_models import build_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        dashboard_dict = dashboard.to_dict()

        html = render_html_dashboard(dashboard_dict, title="Test")
        if dashboard.agent_state:
            assert "as-summary" in html
            assert "as-header" in html
            assert "as-details" in html

    def test_loop_html_has_agent_state_section(self):
        """render_loop_html_dashboard output includes agent-state tab."""
        from harness.copilot.shell.html_renderer import render_loop_html_dashboard
        from harness.copilot.integration.loop_to_copilot_mapper import artifacts_to_dashboard

        class MockArtifactsFull:
            instance_id = "test__mock"
            run_dir = "/tmp/mock_run"
            tier = "B"
            metrics = {}
            loop_report = None
            eval_report = None
            final_review_envelope = None
            final_gate_result = None
            patch_diff = None
            load_errors = []
            run_classification = {}
            repair_rounds = []
            review_repair_rounds = []
            repair_result = None

        dashboard = artifacts_to_dashboard(MockArtifactsFull())
        dashboard_dict = dashboard.to_dict()

        html = render_loop_html_dashboard(dashboard_dict, loop_artifacts=MockArtifactsFull(), title="Loop Test")
        assert "agent-state" in html
        assert "Agent" in html

    def test_loop_html_agent_state_content(self):
        """Loop HTML agent state shows inference result."""
        from harness.copilot.shell.html_renderer import render_loop_html_dashboard

        class MockWithGateFull:
            instance_id = "test__gate"
            run_dir = "/tmp/mock_gate"
            tier = "B"
            metrics = {"final_gate_passed": True}
            loop_report = ""
            eval_report = None
            final_review_envelope = None
            final_gate_result = {"content": "Final Gate: PASS", "merge_ready": True, "final_gate_passed": True}
            patch_diff = None
            load_errors = []
            run_classification = {}
            repair_rounds = []
            review_repair_rounds = []
            repair_result = None

        from harness.copilot.integration.loop_to_copilot_mapper import artifacts_to_dashboard
        dashboard = artifacts_to_dashboard(MockWithGateFull())
        dashboard_dict = dashboard.to_dict()

        html = render_loop_html_dashboard(dashboard_dict, loop_artifacts=MockWithGateFull(), title="Gate Test")
        assert "agent-state" in html

    def test_html_data_json_includes_agent_state(self):
        """Embedded dashboard-data JSON includes agent_state."""
        from harness.copilot.shell.html_renderer import render_html_dashboard
        from harness.copilot.view_models import build_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        dashboard_dict = dashboard.to_dict()

        html = render_html_dashboard(dashboard_dict)
        # The dashboard-data script contains the full JSON
        assert 'id="dashboard-data"' in html
        # agent_state should be embedded
        assert '"agent_state"' in html

    def test_project_html_agent_state_tab_order(self):
        """agent-state tab appears after overview in tab nav."""
        from harness.copilot.shell.html_renderer import render_html_dashboard
        from harness.copilot.view_models import build_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        dashboard_dict = dashboard.to_dict()

        html = render_html_dashboard(dashboard_dict)
        # The tab buttons appear in order; agent-state should be after overview
        overview_idx = html.find('data-tab="overview"')
        agent_state_idx = html.find('data-tab="agent-state"')
        assert overview_idx >= 0
        assert agent_state_idx >= 0
        assert agent_state_idx > overview_idx
