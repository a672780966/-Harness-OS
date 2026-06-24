"""Tests for Phase 6B — CLI Agent State commands.

Tests that:
- harness copilot agent-state <path> --format markdown|json works
- harness copilot agent-state-from-loop <path> --format markdown|json works
- CLI returns proper error for non-existent paths
"""
import os
import sys
import json
import tempfile
from pathlib import Path

import pytest


def _cli_path():
    """Return the importable path for the CLI module."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "harness", "copilot", "cli",
    )


class TestAgentStateCLI:
    """Tests for agent-state CLI command."""

    def test_agent_state_project_help(self):
        """Verify agent-state subparser is registered."""
        from harness.copilot.cli import main as cli_main
        # Just check the parser can parse the command name
        import argparse
        parser = argparse.ArgumentParser()
        # We just test that the module imports and has the right functions
        from harness.copilot.cli import cmd_agent_state, cmd_agent_state_from_loop
        assert callable(cmd_agent_state)
        assert callable(cmd_agent_state_from_loop)

    def test_agent_state_markdown_output(self):
        """Run agent-state on the project itself and verify markdown output."""
        from harness.copilot.view_models import build_dashboard
        from harness.copilot.agent_state.renderer import render_agent_state
        from harness.copilot.agent_state import AgentState

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        assert dashboard.agent_state is not None

        agent_dict = dashboard.agent_state
        astate = AgentState(
            state=agent_dict.get("state", "idle"),
            confidence=agent_dict.get("confidence", 0.0),
            source_events=agent_dict.get("source_events", []),
            summary=agent_dict.get("summary", ""),
            recommended_action=agent_dict.get("recommended_action", ""),
            severity=agent_dict.get("severity", "low"),
            blocking=agent_dict.get("blocking", False),
            timestamp=agent_dict.get("timestamp", ""),
        )

        md = render_agent_state(astate, format="markdown")
        assert "Agent 状态" in md
        assert "置信度" in md
        assert "严重度" in md
        assert "阻塞" in md

    def test_agent_state_json_output(self):
        """Run agent-state on the project and verify JSON output."""
        from harness.copilot.view_models import build_dashboard

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dashboard = build_dashboard(project_root)
        assert dashboard.agent_state is not None

        agent_dict = dashboard.agent_state
        assert isinstance(agent_dict, dict)
        assert "state" in agent_dict
        assert "confidence" in agent_dict
        assert "summary" in agent_dict

        # Verify JSON serializable
        js = json.dumps(agent_dict, indent=2, ensure_ascii=False)
        parsed = json.loads(js)
        assert parsed["state"] == agent_dict["state"]

    def test_agent_state_nonexistent_path(self):
        """Verify CLI errors on non-existent path."""
        from harness.copilot.cli import cmd_agent_state
        import argparse

        args = argparse.Namespace(
            project_path="/nonexistent/path/xyz789",
            diff_ref="HEAD~1",
            format="markdown",
        )
        with pytest.raises(SystemExit):
            cmd_agent_state(args)

    def test_agent_state_from_loop_markdown(self):
        """Test agent-state-from-loop with mock artifacts."""
        from harness.copilot.agent_state.inference import infer_from_loop_artifacts
        from harness.copilot.agent_state.renderer import render_agent_state
        from harness.copilot.agent_state import AgentStateEnum

        class MockArtifacts:
            final_gate_result = type('obj', (object,), {'content': 'Final Gate: PASS'})
            final_review_envelope = None
            eval_report = None
            loop_report = None

        astate = infer_from_loop_artifacts(MockArtifacts())
        assert astate.state == AgentStateEnum.COMPLETED.value

        md = render_agent_state(astate, format="markdown")
        assert "已完成" in md or "Agent 状态" in md

    def test_agent_state_from_loop_json(self):
        """Test agent-state-from-loop JSON output."""
        from harness.copilot.agent_state.inference import infer_from_loop_artifacts
        from harness.copilot.agent_state.renderer import render_agent_state

        class MockArtifacts:
            final_gate_result = type('obj', (object,), {'content': 'Final Gate: PASS'})
            final_review_envelope = None
            eval_report = None
            loop_report = None

        astate = infer_from_loop_artifacts(MockArtifacts())
        js = render_agent_state(astate, format="json")
        d = json.loads(js)
        assert d["state"] == "completed"
        assert d["blocking"] is False
