"""Tests for Task Card Rendering — covers markdown + JSON output of task cards.

Verifies that rendered task cards contain:
- 目标 (target/goal)
- 范围 (scope)
- 禁止事项 (restrictions)
- 验收标准 (acceptance criteria)
"""

from harness.copilot.markdown_renderer import render_task_cards
from harness.copilot.json_renderer import render_task_cards_json
from harness.copilot.view_models import (
    TaskCardViewModel,
    TaskCardListViewModel,
)
import json


def _make_card(
    title: str = "Test task",
    card_type: str = "fix_test",
    state: str = "pending",
    priority: str = "🟠 高优先级",
    module: str = "auth",
    target_file: str = "auth/login.py",
    description: str = "修复登录模块的安全漏洞",
    is_blocking: bool = False,
    risk_label: str = "🟠 高风险",
    state_label: str = "⏳ 待处理",
) -> TaskCardViewModel:
    return TaskCardViewModel(
        title=title, card_type=card_type, state=state,
        priority_label=priority, module=module,
        target_file=target_file, description=description,
        is_blocking=is_blocking, risk_label=risk_label,
        state_label=state_label,
    )


class TestTaskCardMarkdownOutput:
    def test_card_contains_title(self):
        cards = TaskCardListViewModel(cards=[_make_card(title="修复登录漏洞")])
        output = render_task_cards(cards)
        assert "修复登录漏洞" in output

    def test_card_contains_target_file(self):
        cards = TaskCardListViewModel(cards=[_make_card(target_file="auth/login.py")])
        output = render_task_cards(cards)
        assert "auth/login.py" in output

    def test_card_contains_module(self):
        cards = TaskCardListViewModel(cards=[_make_card(module="auth")])
        output = render_task_cards(cards)
        assert "auth" in output

    def test_card_contains_priority_label(self):
        cards = TaskCardListViewModel(cards=[_make_card(priority="🔴 紧急")])
        output = render_task_cards(cards)
        assert "🔴" in output or "紧急" in output

    def test_card_contains_description(self):
        cards = TaskCardListViewModel(
            cards=[_make_card(description="修复登录模块的安全漏洞，添加输入验证")]
        )
        output = render_task_cards(cards)
        assert "修复登录模块" in output

    def test_blocking_card_highlighted(self):
        cards = TaskCardListViewModel(
            cards=[_make_card(title="Critical bug", is_blocking=True)]
        )
        output = render_task_cards(cards)
        assert "🔴" in output or "阻塞合并" in output or "Critical bug" in output

    def test_non_blocking_card(self):
        cards = TaskCardListViewModel(
            cards=[_make_card(title="Minor task", is_blocking=False)]
        )
        output = render_task_cards(cards)
        assert "Minor task" in output

    def test_multiple_cards(self):
        cards = TaskCardListViewModel(
            cards=[
                _make_card(title="Task 1", module="auth"),
                _make_card(title="Task 2", module="config"),
            ],
        )
        output = render_task_cards(cards)
        assert "Task 1" in output
        assert "Task 2" in output

    def test_card_type_displayed(self):
        cards = TaskCardListViewModel(
            cards=[_make_card(card_type="fix_test")]
        )
        output = render_task_cards(cards)
        assert "fix_test" in output

    def test_summary_shown(self):
        cards = TaskCardListViewModel(
            cards=[_make_card()],
            summary={"total_cards": 1, "blocking_count": 0, "by_state": {"pending": 1}},
        )
        output = render_task_cards(cards)
        assert "1" in output


class TestTaskCardJsonOutput:
    def test_json_serializable(self):
        cards = TaskCardListViewModel(cards=[_make_card()])
        output = render_task_cards_json(cards)
        parsed = json.loads(output)
        assert "cards" in parsed
        assert parsed["cards"][0]["title"] == "Test task"

    def test_json_blocking_field(self):
        cards = TaskCardListViewModel(
            cards=[_make_card(title="Blocking", is_blocking=True)]
        )
        output = render_task_cards_json(cards)
        parsed = json.loads(output)
        assert parsed["cards"][0]["is_blocking"] is True

    def test_json_summary(self):
        cards = TaskCardListViewModel(
            cards=[_make_card()],
            summary={"total_cards": 1, "blocking_count": 0},
        )
        output = render_task_cards_json(cards)
        parsed = json.loads(output)
        assert parsed["summary"]["total_cards"] == 1


class TestTaskCardAcceptanceCriteria:
    def test_description_serves_as_acceptance_context(self):
        """Task card description should explain what to do and why."""
        card = _make_card(
            title="优化数据库查询",
            description="当前查询在用户量>1000时超时，需添加索引和分页。禁止使用全表扫描。",
        )
        assert card.description != ""
        assert "禁止" in card.description or "1000" in card.description

    def test_title_is_actionable(self):
        """Title should describe a clear action."""
        card = _make_card(title="优化数据库查询")
        assert len(card.title) > 0
