"""Tests for Phase 8B — Live dashboard HTML rendering."""
import json
import os

import pytest

from harness.copilot.live.live_html_renderer import render_live_dashboard


class TestLiveDashboardUI:
    """Live dashboard HTML content tests."""

    def test_render_contains_agent_state(self):
        """HTML contains 'Agent 状态' section."""
        html = render_live_dashboard({
            "project_name": "test",
            "branch": "main",
            "agent_state": {"state": "completed", "summary": "All done", "severity": "low"},
            "merge_readiness": {"state": "pass", "state_label": "可以合并", "state_icon": "✅"},
            "risk_level": "low",
            "blocking": False,
            "recommended_action": "",
            "events": [],
        })
        assert "Agent 状态" in html
        assert "🤖" in html

    def test_render_contains_merge_readiness(self):
        """HTML contains '合并就绪度' section."""
        html = render_live_dashboard({
            "project_name": "test",
            "branch": "main",
            "merge_readiness": {"state": "pass", "state_label": "可以合并", "state_icon": "✅"},
        })
        assert "合并就绪度" in html
        assert "🔀" in html

    def test_render_contains_risk_level(self):
        """HTML contains risk level display."""
        html = render_live_dashboard({
            "project_name": "test",
            "risk_level": "high",
            "blocking": True,
        })
        assert "风险等级" in html
        assert "HIGH" in html

    def test_render_contains_blocking_status(self):
        """HTML contains blocking status."""
        html = render_live_dashboard({
            "project_name": "test",
            "blocking": True,
        })
        assert "阻塞状态" in html
        assert "🚫" in html

    def test_render_contains_recommended_action(self):
        """HTML contains recommended action."""
        html = render_live_dashboard({
            "project_name": "test",
            "recommended_action": "请解决阻塞问题",
        })
        assert "建议操作" in html
        assert "请解决阻塞问题" in html

    def test_render_contains_live_event_timeline(self):
        """HTML contains Live Event Timeline section."""
        html = render_live_dashboard({
            "project_name": "test",
            "events": [],
        })
        assert "Live Event Timeline" in html

    def test_render_contains_readonly_badge(self):
        """HTML contains 'Read-only' badge."""
        html = render_live_dashboard({
            "project_name": "test",
        })
        assert "Read-only" in html

    def test_render_contains_local_badge(self):
        """HTML contains 'Local' badge."""
        html = render_live_dashboard({
            "project_name": "test",
        })
        assert "Local" in html

    def test_render_contains_embedded_js(self):
        """HTML contains embedded JavaScript for SSE."""
        html = render_live_dashboard({
            "project_name": "test",
        })
        assert "EventSource" in html
        assert "function" in html

    def test_render_with_initial_events(self):
        """HTML embeds initial events as JSON."""
        events = [
            {"event_id": "e1", "event_type": "project_state_update", "summary": "test"},
        ]
        html = render_live_dashboard({
            "project_name": "test",
            "events": events,
        })
        assert "project_state_update" in html
        assert '"e1"' in html or "'e1'" in html or "e1" in html

    def test_render_contains_dashboard_data(self):
        """HTML contains dashboard-data JSON script."""
        html = render_live_dashboard({
            "project_name": "test",
            "branch": "main",
        })
        assert "dashboard-data" in html
        assert '"project_name": "test"' in html

    def test_render_contains_connection_status(self):
        """HTML contains connection status display."""
        html = render_live_dashboard({
            "project_name": "test",
        })
        assert "连接状态" in html
        assert "conn-status" in html

    def test_render_contains_last_updated(self):
        """HTML contains last-updated timestamp."""
        html = render_live_dashboard({
            "project_name": "test",
        })
        assert "last-updated" in html
        assert "Last updated" in html
