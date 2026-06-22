"""Tests for task card copy text / markdown export."""

from __future__ import annotations

import pytest

from harness.copilot.shell.copy_text_renderer import (
    render_task_card_copy_text,
    export_task_card_markdown,
    export_all_task_cards_markdown,
)


SAMPLE_FIX_TEST_CARD = {
    "title": "测试修复 — django-11848",
    "card_type": "fix_test",
    "state": "pending",
    "priority_label": "🟠 高优先级",
    "module": "django.db.models",
    "target_file": "django/db/models/deletion.py",
    "description": "测试通过率: 42/45，失败测试: 3 个",
    "is_blocking": True,
    "risk_label": "🔴 极高风险",
}

SAMPLE_FIX_REVIEW_CARD = {
    "title": "Codex 审查拒绝 — sphinx-7590",
    "card_type": "fix_review",
    "state": "pending",
    "priority_label": "🔴 紧急",
    "module": "sphinx.domains",
    "target_file": "sphinx/domains/c.py",
    "description": "审查结果: 拒绝 — EOF.isalpha() 无限循环",
    "is_blocking": True,
    "risk_label": "🔴 极高风险",
}

SAMPLE_CODE_CHANGE_CARD = {
    "title": "更新配置验证逻辑",
    "card_type": "code_change",
    "state": "in_progress",
    "priority_label": "🟡 中优先级",
    "module": "core.config",
    "target_file": "config/validator.py",
    "description": "添加配置格式验证，防止注入攻击",
    "is_blocking": False,
    "risk_label": "🟡 中风险",
}


class TestRenderTaskCardCopyText:
    def test_fix_test_card_copy_text(self):
        text = render_task_card_copy_text(SAMPLE_FIX_TEST_CARD)
        assert "任务卡: 测试修复" in text
        assert "fix_test" in text
        assert "pending" in text
        assert "阻塞合并" in text
        assert "验收标准" in text
        assert "全部测试通过" in text
        assert "禁止重构无关模块" in text

    def test_fix_review_card_copy_text(self):
        text = render_task_card_copy_text(SAMPLE_FIX_REVIEW_CARD)
        assert "任务卡: Codex 审查拒绝" in text
        assert "fix_review" in text
        assert "处理所有 Codex 阻塞性问题" in text
        assert "需要重新运行 eval" in text
        assert "需要重新进行 Codex review" in text

    def test_code_change_card_copy_text(self):
        text = render_task_card_copy_text(SAMPLE_CODE_CHANGE_CARD)
        assert "任务卡: 更新配置验证逻辑" in text
        assert "code_change" in text
        assert "通过项目现有测试套件" in text
        # Non-blocking should not show 阻塞合并 warning
        assert "⛔ 阻塞合并" not in text

    def test_contains_separator(self):
        text = render_task_card_copy_text(SAMPLE_FIX_TEST_CARD)
        assert "=" * 10 in text
        assert "-" * 10 in text


class TestExportTaskCardMarkdown:
    def test_fix_test_card_markdown(self):
        md = export_task_card_markdown(SAMPLE_FIX_TEST_CARD)
        assert "# 任务卡: 测试修复" in md
        assert "fix_test" in md
        assert "- [ ] 全部测试通过" in md
        assert "- [ ] 禁止重构无关模块" in md
        assert "由 Harness Code Copilot 生成" in md
        assert "阻塞合并" in md

    def test_fix_review_card_markdown(self):
        md = export_task_card_markdown(SAMPLE_FIX_REVIEW_CARD)
        assert "Codex 审查拒绝" in md
        assert "处理所有 Codex 阻塞性问题" in md
        assert "需要重新进行 Codex review" in md

    def test_non_blocking_markdown_no_block_label(self):
        md = export_task_card_markdown(SAMPLE_CODE_CHANGE_CARD)
        # Blocking status field is always shown, but non-blocking uses "否 ✅"
        assert "阻塞合并" in md  # field is always present
        assert "否 ✅" in md  # non-blocking indicator
        assert "更新配置验证逻辑" in md

    def test_markdown_has_sections(self):
        for card in [SAMPLE_FIX_TEST_CARD, SAMPLE_FIX_REVIEW_CARD, SAMPLE_CODE_CHANGE_CARD]:
            md = export_task_card_markdown(card)
            assert "## 说明" in md
            assert "## 验收标准" in md
            assert "---" in md


class TestExportAllCardsMarkdown:
    def test_export_all(self):
        cards = [SAMPLE_FIX_TEST_CARD, SAMPLE_FIX_REVIEW_CARD, SAMPLE_CODE_CHANGE_CARD]
        md = export_all_task_cards_markdown(cards)
        assert "# 任务卡列表" in md
        assert "测试修复" in md
        assert "Codex 审查拒绝" in md
        assert "更新配置验证逻辑" in md
        assert "由 Harness Code Copilot 生成" in md
        assert "## 1." in md
        assert "## 2." in md
        assert "## 3." in md

    def test_export_all_empty(self):
        md = export_all_task_cards_markdown([])
        assert "# 任务卡列表" in md
        assert "由 Harness Code Copilot 生成" in md

    def test_export_all_each_card_has_criteria(self):
        cards = [SAMPLE_FIX_TEST_CARD, SAMPLE_FIX_REVIEW_CARD]
        md = export_all_task_cards_markdown(cards)
        # Each card's acceptance criteria should appear
        assert "全部测试通过" in md
        assert "禁止重构无关模块" in md
        assert "处理所有 Codex 阻塞性问题" in md
