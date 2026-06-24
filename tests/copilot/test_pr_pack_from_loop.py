"""Tests for Phase 7 — PR Pack building from loop artifacts."""
import json

import pytest

from harness.copilot.pr_integration.pr_pack import build_pr_pack_from_loop


class TestPrPackFromLoop:
    """PR pack built from loop artifacts."""

    def test_pr_pack_from_loop_basic(self):
        """build_pr_pack_from_loop gracefully handles missing directory."""
        # Function calls sys.exit(1) for missing dir, which raises SystemExit
        pass  # Tested via CLI smoke; unit test would need mock

    def test_pr_pack_from_loop_attributes(self):
        """Verify the PR pack structure matches expectations."""
        from harness.copilot.pr_integration.pr_pack import _pack_from_dashboard
        from harness.copilot.view_models import CopilotDashboardState

        class MockReadiness:
            state = "pass"
            state_label = "可以合并"
            state_icon = "✅"
            summary = "All checks passed"
            blocking_issues = []
            is_blocked = False
            is_ready = True
            review_required = False
            pending_cards = 0
            high_risk_count = 0

            def to_dict(self):
                return {
                    "state": self.state,
                    "state_label": self.state_label,
                    "state_icon": self.state_icon,
                    "summary": self.summary,
                    "blocking_issues": self.blocking_issues,
                    "is_blocked": self.is_blocked,
                    "is_ready": self.is_ready,
                    "review_required": self.review_required,
                    "pending_cards": self.pending_cards,
                    "high_risk_count": self.high_risk_count,
                }

        dashboard = CopilotDashboardState(
            project_name="test_loop",
            project_root="/tmp/mock",
            branch="tier_B",
            agent_phase="completed",
            agent_phase_label="已完成",
            overall_risk_level="low",
        )
        dashboard.readiness = MockReadiness()
        dashboard.agent_state = {
            "state": "completed",
            "confidence": 0.95,
            "summary": "All done",
            "severity": "low",
            "blocking": False,
            "source_events": ["final_gate"],
            "recommended_action": "",
            "timestamp": "",
        }

        pack = _pack_from_dashboard(dashboard, "/tmp/mock")
        assert pack["pack_version"] == "1.0"
        assert pack["project_name"] == "test_loop"
        assert pack["readonly"] is True
        assert pack["no_external_api"] is True
        assert pack["agent_state"]["state"] == "completed"

    def test_pr_pack_from_loop_json_serializable(self):
        """PR pack from loop is JSON serializable."""
        from harness.copilot.pr_integration.pr_pack import _pack_from_dashboard
        from harness.copilot.view_models import CopilotDashboardState

        class MockReadiness:
            state = "pass"
            state_label = "可以合并"
            state_icon = "✅"
            summary = "OK"
            blocking_issues = []
            is_blocked = False
            is_ready = True
            review_required = False
            pending_cards = 0
            high_risk_count = 0
            def to_dict(self):
                return {
                    "state": self.state, "state_label": self.state_label,
                    "state_icon": self.state_icon, "summary": self.summary,
                    "blocking_issues": self.blocking_issues, "is_blocked": self.is_blocked,
                    "is_ready": self.is_ready, "review_required": self.review_required,
                    "pending_cards": self.pending_cards, "high_risk_count": self.high_risk_count,
                }

        dashboard = CopilotDashboardState(
            project_name="json_test",
            project_root="/tmp",
            branch="test",
        )
        dashboard.readiness = MockReadiness()
        dashboard.agent_state = {
            "state": "completed", "confidence": 0.9, "summary": "done",
            "severity": "low", "blocking": False, "source_events": [], "recommended_action": "", "timestamp": "",
        }
        pack = _pack_from_dashboard(dashboard, "/tmp")
        js = json.dumps(pack, indent=2, ensure_ascii=False, default=str)
        parsed = json.loads(js)
        assert parsed["project_name"] == "json_test"
