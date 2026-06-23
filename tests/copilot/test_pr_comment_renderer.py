"""Tests for Phase 7 — PR comment renderer."""
import json
import os

import pytest

from harness.copilot.pr_integration.pr_comment_renderer import (
    render_pr_comment, render_summary_section,
)
from harness.copilot.pr_integration.pr_pack import build_pr_pack


class TestPrCommentRenderer:
    """PR comment rendering tests."""

    def test_render_comment_markdown(self):
        """render_pr_comment with markdown format returns proper string."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        md = render_pr_comment(pack, format="markdown")
        assert "Harness Copilot PR Review Pack" in md
        assert "###" in md
        assert "Agent" in md or "变更" in md

    def test_render_comment_json(self):
        """render_pr_comment with json format returns serializable JSON."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        js = render_pr_comment(pack, format="json")
        parsed = json.loads(js)
        assert parsed["project_name"] == pack["project_name"]

    def test_render_comment_contains_agent_state(self):
        """Markdown comment includes Agent State section."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        md = render_pr_comment(pack, format="markdown")
        assert "Agent 状态" in md or "🤖" in md

    def test_render_comment_contains_readiness(self):
        """Markdown comment includes Merge Readiness section."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        md = render_pr_comment(pack, format="markdown")
        assert "合并就绪度" in md or "🔀" in md

    def test_render_comment_contains_risk_checklist(self):
        """Markdown comment includes Risk Checklist."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        md = render_pr_comment(pack, format="markdown")
        assert "Risk Checklist" in md or "风险" in md

    def test_render_comment_contains_reviewer_actions(self):
        """Markdown comment includes Reviewer Actions."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        md = render_pr_comment(pack, format="markdown")
        assert "Reviewer Action" in md or "操作" in md

    def test_render_summary_section(self):
        """render_summary_section returns a non-empty string."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        summary = render_summary_section(pack)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_render_comment_readonly_footer(self):
        """Footer confirms read-only."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        md = render_pr_comment(pack, format="markdown")
        assert "只读" in md
        assert "外部 API" in md
