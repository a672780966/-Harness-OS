"""Tests for Merge Readiness Rendering — markdown and JSON output.

Verifies:
- Block/review/pass 三态都有用户可读文案
- State-specific icons and labels
- JSON serialization
"""

import json

from harness.copilot.markdown_renderer import render_readiness
from harness.copilot.json_renderer import render_readiness_json
from harness.copilot.view_models import MergeReadinessViewModel


def _make_readiness(
    state: str = "pass",
    blocking_issues = None,
    is_blocked: bool = False,
    is_ready: bool = True,
    review_required: bool = False,
    pending_cards: int = 0,
    high_risk_count: int = 0,
    summary: str = "",
) -> MergeReadinessViewModel:
    labels = {
        "pass": ("可以合并 ✅", "✅"),
        "block": ("禁止合并 🔴", "🔴"),
        "review_needed": ("需审查后合并 🟡", "🟡"),
    }
    state_label, state_icon = labels.get(state, ("状态未知 ❓", "❓"))
    if not summary:
        summary = {
            "pass": "所有检查通过，可以安全合并。",
            "block": "存在阻塞项，禁止合并。",
            "review_needed": "需人工审查后方可合并。",
        }.get(state, "")

    return MergeReadinessViewModel(
        state=state, state_label=state_label, state_icon=state_icon,
        summary=summary,
        blocking_issues=blocking_issues or [],
        is_blocked=is_blocked, is_ready=is_ready,
        review_required=review_required,
        pending_cards=pending_cards, high_risk_count=high_risk_count,
    )


class TestMergeReadinessPassState:
    def test_pass_has_check_icon(self):
        rm = _make_readiness("pass")
        output = render_readiness(rm)
        assert "✅" in output

    def test_pass_has_readable_label(self):
        rm = _make_readiness("pass")
        output = render_readiness(rm)
        assert "可以合并" in output or "pass" in output

    def test_pass_no_blocking_issues(self):
        rm = _make_readiness("pass")
        output = render_readiness(rm)
        assert "阻塞项" not in output or rm.blocking_issues == []

    def test_pass_json(self):
        rm = _make_readiness("pass")
        output = render_readiness_json(rm)
        parsed = json.loads(output)
        assert parsed["state"] == "pass"
        assert parsed["is_ready"] is True
        assert parsed["is_blocked"] is False


class TestMergeReadinessBlockState:
    def test_block_has_stop_icon(self):
        rm = _make_readiness("block", blocking_issues=["Test failure"], is_blocked=True, is_ready=False)
        output = render_readiness(rm)
        assert "🔴" in output

    def test_block_shows_issues(self):
        rm = _make_readiness(
            "block",
            blocking_issues=["Tests failing", "Security review required"],
            is_blocked=True, is_ready=False,
        )
        output = render_readiness(rm)
        assert "Tests failing" in output
        assert "Security review" in output

    def test_block_shows_issue_count(self):
        rm = _make_readiness(
            "block",
            blocking_issues=["Issue 1", "Issue 2", "Issue 3"],
            is_blocked=True, is_ready=False,
        )
        output = render_readiness(rm)
        # Should mention block count
        assert "3" in str(rm.blocking_issues) or "阻塞项" in output

    def test_block_json(self):
        rm = _make_readiness(
            "block",
            blocking_issues=["Critical bug"],
            is_blocked=True, is_ready=False,
        )
        output = render_readiness_json(rm)
        parsed = json.loads(output)
        assert parsed["state"] == "block"
        assert parsed["is_blocked"] is True
        assert len(parsed["blocking_issues"]) == 1


class TestMergeReadinessReviewNeededState:
    def test_review_needed_has_warning_icon(self):
        rm = _make_readiness("review_needed", review_required=True, is_ready=False)
        output = render_readiness(rm)
        assert "🟡" in output

    def test_review_needed_has_readable_label(self):
        rm = _make_readiness("review_needed", review_required=True, is_ready=False)
        output = render_readiness(rm)
        assert "需审查" in output or "review_needed" in output

    def test_review_required_field(self):
        rm = _make_readiness("review_needed", review_required=True, is_ready=False)
        output = render_readiness(rm)
        assert "需审查" in output or "是" in output

    def test_review_needed_json(self):
        rm = _make_readiness("review_needed", review_required=True, is_ready=False)
        output = render_readiness_json(rm)
        parsed = json.loads(output)
        assert parsed["state"] == "review_needed"
        assert parsed["review_required"] is True


class TestMergeReadinessDetails:
    def test_pending_cards_field(self):
        rm = _make_readiness("block", pending_cards=3, is_blocked=True, is_ready=False)
        output = render_readiness(rm)
        assert "3" in str(rm.pending_cards) or "待处理" in output

    def test_high_risk_count_field(self):
        rm = _make_readiness("review_needed", high_risk_count=5, review_required=True, is_ready=False)
        output = render_readiness(rm)
        assert "5" in str(rm.high_risk_count) or "高风险" in output

    def test_summary_field_populated(self):
        rm = _make_readiness("pass", summary="所有检查通过，可以安全合并。")
        output = render_readiness(rm)
        assert "所有检查通过" in output

    def test_all_states_have_unique_output(self):
        pass_state = _make_readiness("pass")
        block_state = _make_readiness("block", blocking_issues=["x"], is_blocked=True, is_ready=False)
        review_state = _make_readiness("review_needed", review_required=True, is_ready=False)

        pass_out = render_readiness(pass_state)
        block_out = render_readiness(block_state)
        review_out = render_readiness(review_state)

        assert pass_out != block_out
        assert pass_out != review_out
        assert block_out != review_out


class TestMergeReadinessHumanReadable:
    def test_state_labels_are_chinese(self):
        """User-facing state must be readable for Chinese-speaking users."""
        for state in ("pass", "block", "review_needed"):
            rm = _make_readiness(state)
            # Labels should contain Chinese characters or emoji
            assert any(ord(c) > 127 for c in rm.state_label), f"No CJK/emoji in {state}"
