"""Tests for JSON Renderer — verifies JSON serialization of ViewModels."""

import json

from harness.copilot.json_renderer import (
    render_dashboard_json,
    render_modules_json,
    render_task_cards_json,
    render_readiness_json,
    render_changes_json,
    is_json_serializable,
)
from harness.copilot.view_models import (
    CopilotDashboardState,
    ModuleCardViewModel,
    TaskCardViewModel,
    TaskCardListViewModel,
    MergeReadinessViewModel,
    RecentChangeViewModel,
    EvidencePackViewModel,
    WaitingCompanionViewModel,
)


class TestRenderDashboardJson:
    def test_returns_valid_json(self):
        state = CopilotDashboardState(
            project_name="test-proj",
            project_root="/tmp",
            branch="main",
            overall_risk_level="low",
        )
        output = render_dashboard_json(state)
        parsed = json.loads(output)
        assert parsed["project_name"] == "test-proj"
        assert parsed["branch"] == "main"
        assert parsed["overall_risk_level"] == "low"

    def test_includes_all_top_level_keys(self):
        state = CopilotDashboardState(project_name="p")
        output = render_dashboard_json(state)
        parsed = json.loads(output)
        required_keys = [
            "project_name", "project_root", "branch",
            "overall_risk_level", "risk_color",
            "agent_phase", "agent_phase_label",
            "uncommitted_changes", "module_count",
            "generated_at", "modules", "recent_changes",
            "suggestions", "task_cards", "readiness",
            "evidence", "companion",
        ]
        for key in required_keys:
            assert key in parsed, f"Missing key: {key}"

    def test_with_nested_viewmodels(self):
        state = CopilotDashboardState(
            project_name="test",
            modules=[
                ModuleCardViewModel(
                    name="src", file_count=2, risk_level="low",
                    risk_color="green", risk_score=0.0,
                    risk_description="safe", dependencies=[],
                    dependents=[], high_risk_files=[], primary_language="Python",
                ),
            ],
            readiness=MergeReadinessViewModel(
                state="pass", state_label="可以合并 ✅", state_icon="✅",
                summary="OK", blocking_issues=[],
                is_blocked=False, is_ready=True, review_required=False,
                pending_cards=0, high_risk_count=0,
            ),
        )
        output = render_dashboard_json(state)
        parsed = json.loads(output)
        assert len(parsed["modules"]) == 1
        assert parsed["readiness"]["state"] == "pass"


class TestRenderModulesJson:
    def test_returns_valid_json(self):
        modules = [
            ModuleCardViewModel(
                name="auth", file_count=3, risk_level="high",
                risk_color="red", risk_score=0.8,
                risk_description="Auth risk", dependencies=["db"],
                dependents=["api"], high_risk_files=[],
                primary_language="Python",
            ),
        ]
        output = render_modules_json(modules)
        parsed = json.loads(output)
        assert "modules" in parsed
        assert parsed["modules"][0]["name"] == "auth"
        assert parsed["modules"][0]["risk_level"] == "high"


class TestRenderTaskCardsJson:
    def test_returns_valid_json(self):
        cards = TaskCardListViewModel(
            cards=[
                TaskCardViewModel(
                    title="Fix bug", card_type="fix_test",
                    state="pending", priority_label="紧急",
                    module="auth", target_file="", description="",
                    is_blocking=True, risk_label="高风险", state_label="待处理",
                ),
            ],
            summary={"total_cards": 1, "blocking_count": 1},
        )
        output = render_task_cards_json(cards)
        parsed = json.loads(output)
        assert "cards" in parsed
        assert len(parsed["cards"]) == 1
        assert parsed["cards"][0]["is_blocking"] is True


class TestRenderReadinessJson:
    def test_returns_valid_json(self):
        rm = MergeReadinessViewModel(
            state="block", state_label="禁止合并 🔴", state_icon="🔴",
            summary="Blocked", blocking_issues=["Test failure"],
            is_blocked=True, is_ready=False, review_required=True,
            pending_cards=1, high_risk_count=2,
        )
        output = render_readiness_json(rm)
        parsed = json.loads(output)
        assert parsed["state"] == "block"
        assert parsed["is_blocked"] is True
        assert len(parsed["blocking_issues"]) == 1


class TestRenderChangesJson:
    def test_returns_valid_json(self):
        changes = [
            RecentChangeViewModel(
                module="auth", summary="Changed auth",
                intent="Bug 修复", files_changed=["auth.py"],
                lines_changed_str="+5/-0", has_risks=False,
                risk_warnings=[],
            ),
        ]
        output = render_changes_json(changes)
        parsed = json.loads(output)
        assert "recent_changes" in parsed
        assert parsed["recent_changes"][0]["module"] == "auth"


class TestIsJsonSerializable:
    def test_basic_types(self):
        assert is_json_serializable({"key": "value"}) is True
        assert is_json_serializable([1, 2, 3]) is True
        assert is_json_serializable("string") is True
        assert is_json_serializable(42) is True

    def test_complex_types(self):
        assert is_json_serializable({
            "modules": [
                {"name": "src", "files": [{"path": "main.py", "risk": 0.0}]}
            ],
            "nested": {"deep": {"deeper": [1, 2, 3]}},
        }) is True

    def test_non_serializable(self):
        """A set is not JSON serializable."""
        assert is_json_serializable({1, 2, 3}) is False
