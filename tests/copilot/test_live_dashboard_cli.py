"""Tests for Phase 8B — Live dashboard CLI commands."""
import os
import json

import pytest

from harness.copilot.live.live_dashboard import build_live_dashboard, build_live_dashboard_from_loop


class TestLiveDashboardCLI:
    """Live dashboard CLI tests."""

    def test_cli_functions_importable(self):
        """CLI command functions are importable."""
        from harness.copilot.cli import cmd_live_dashboard, cmd_live_dashboard_from_loop
        assert callable(cmd_live_dashboard)
        assert callable(cmd_live_dashboard_from_loop)

    def test_build_live_dashboard_returns_dict(self):
        """build_live_dashboard returns a result dict."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = build_live_dashboard(project_root)
        assert result["success"] is True
        assert "initial_state" in result
        assert "agent_state" in result["initial_state"]
        assert "events" in result["initial_state"]

    def test_build_live_dashboard_has_events(self):
        """Live dashboard has at least one initial event."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = build_live_dashboard(project_root)
        assert len(result["initial_state"]["events"]) >= 1

    def test_build_live_dashboard_html_contains_key_sections(self):
        """Generated HTML contains all required sections."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = build_live_dashboard(project_root, output_dir="/tmp/_phase8b_test/")
        assert result["success"] is True
        assert "html_path" in result
        with open(result["html_path"]) as f:
            html = f.read()
        assert "Agent 状态" in html
        assert "合并就绪度" in html
        assert "Live Event Timeline" in html
        assert "Read-only" in html
        assert "Local" in html

    def test_build_live_dashboard_writes_files(self):
        """build_live_dashboard writes HTML and JSON files."""
        import tempfile
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_live_dashboard(project_root, output_dir=tmpdir)
            assert result["success"] is True
            assert os.path.isfile(result["html_path"])
            assert os.path.isfile(result["json_path"])

    def test_build_live_dashboard_json_valid(self):
        """Written JSON is valid."""
        import tempfile
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_live_dashboard(project_root, output_dir=tmpdir)
            with open(result["json_path"]) as f:
                data = json.load(f)
            assert "agent_state" in data
            assert "events" in data

    def test_build_from_loop_nonexistent(self):
        """build_live_dashboard_from_loop with bad path fails gracefully."""
        result = build_live_dashboard_from_loop("/tmp/nonexistent_loop_xyz")
        assert result["success"] is False
        assert "error" in result
