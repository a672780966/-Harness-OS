"""Tests for Phase 7 — PR Pack building from project data."""
import os
import json

import pytest

from harness.copilot.pr_integration.pr_pack import build_pr_pack, _build_summary


class TestPrPack:
    """PR pack built from project path."""

    def test_build_pr_pack_returns_dict(self):
        """build_pr_pack returns a dict with required keys."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        assert isinstance(pack, dict)
        assert "pack_version" in pack
        assert "project_name" in pack
        assert "summary" in pack
        assert "agent_state" in pack
        assert "readiness" in pack
        assert "risk_checklist" in pack
        assert "modules" in pack
        assert "reviewer_actions" in pack
        assert "readonly" in pack
        assert pack["readonly"] is True
        assert pack["no_external_api"] is True

    def test_pr_pack_has_risk_checklist(self):
        """Risk checklist has all 7 categories."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        checklist = pack.get("risk_checklist", [])
        assert len(checklist) >= 7
        ids = [c["id"] for c in checklist]
        for rid in ["db_migration", "auth_permission", "destructive_change",
                     "test_coverage_gap", "external_service", "config_secret", "new_dependency"]:
            assert rid in ids

    def test_pr_pack_has_reviewer_actions(self):
        """Reviewer actions list is present."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        actions = pack.get("reviewer_actions", [])
        assert isinstance(actions, list)
        # Should have at least merge state action
        assert any(a.get("category") in ("ready_to_merge", "merge_blocker", "review_required") for a in actions)

    def test_pr_pack_summary_is_string(self):
        """Summary is a non-empty string."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        assert isinstance(pack["summary"], str)
        assert len(pack["summary"]) > 0

    def test_pr_pack_json_serializable(self):
        """PR pack is JSON serializable."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        js = json.dumps(pack, indent=2, ensure_ascii=False, default=str)
        parsed = json.loads(js)
        assert parsed["project_name"] == pack["project_name"]

    def test_build_summary_with_data(self):
        """_build_summary returns a meaningful string."""
        dashboard_dict = {
            "project_name": "test_project",
            "branch": "main",
            "agent_state": {"summary": "All good", "state": "completed"},
            "readiness": {"state_label": "可以合并"},
            "modules": [{"name": "core"}],
            "recent_changes": [{"files_changed": ["file1.py", "file2.py"]}],
        }
        summary = _build_summary(dashboard_dict)
        assert "test_project" in summary
        assert "main" in summary
        assert "All good" in summary
