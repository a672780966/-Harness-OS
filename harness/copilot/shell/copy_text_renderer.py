"""Copy Text Renderer — export task cards as copyable text and markdown.

Supports:
- Copyable plain text for task cards
- Markdown export for task cards
- Acceptance criteria, blocking status, scope limits included
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def render_task_card_copy_text(card: Dict[str, Any]) -> str:
    """Render a single task card as copyable plain text.

    Args:
        card: Task card dict (from TaskCardViewModel.to_dict())

    Returns:
        Plain text suitable for copying to clipboard.
    """
    title = card.get("title", "任务卡")
    card_type = card.get("card_type", "task")
    state = card.get("state", "pending")
    priority = card.get("priority_label", "")
    module = card.get("module", "")
    target_file = card.get("target_file", "")
    description = card.get("description", "")
    is_blocking = card.get("is_blocking", False)
    risk_label = card.get("risk_label", "")

    lines = [
        "=" * 60,
        f"  任务卡: {title}",
        "=" * 60,
        f"  类型: {card_type}",
        f"  状态: {state}",
        f"  优先级: {priority}",
        f"  风险: {risk_label}",
        f"  阻塞合并: {'是' if is_blocking else '否'}",
        f"  模块: {module}" if module else "",
        f"  目标文件: {target_file}" if target_file else "",
        "-" * 60,
        f"  说明:",
        f"  {description}",
        "-" * 60,
        "  验收标准:",
    ]

    # Add acceptance criteria based on card type
    acceptance = _acceptance_criteria(card_type, card)
    for i, criteria in enumerate(acceptance, 1):
        lines.append(f"    {i}. {criteria}")

    if is_blocking:
        lines.append("")
        lines.append("  ⛔ 阻塞合并 — 完成后方可合并")

    lines.append("=" * 60)
    return "\n".join(line for line in lines if line)


def export_task_card_markdown(card: Dict[str, Any]) -> str:
    """Export a single task card as markdown.

    Args:
        card: Task card dict

    Returns:
        Markdown string suitable for saving to .md file.
    """
    title = card.get("title", "任务卡")
    card_type = card.get("card_type", "task")
    state = card.get("state", "pending")
    priority = card.get("priority_label", "")
    module = card.get("module", "")
    target_file = card.get("target_file", "")
    description = card.get("description", "")
    is_blocking = card.get("is_blocking", False)
    risk_label = card.get("risk_label", "")

    lines = [
        f"# 任务卡: {title}",
        "",
        f"- **类型**: `{card_type}`",
        f"- **状态**: {state}",
        f"- **优先级**: {priority}",
        f"- **风险**: {risk_label}",
        f"- **阻塞合并**: {'是 🚫' if is_blocking else '否 ✅'}",
    ]
    if module:
        lines.append(f"- **模块**: `{module}`")
    if target_file:
        lines.append(f"- **目标文件**: `{target_file}`")

    lines.extend([
        "",
        "## 说明",
        "",
        description,
        "",
        "## 验收标准",
        "",
    ])

    acceptance = _acceptance_criteria(card_type, card)
    for criteria in acceptance:
        lines.append(f"- [ ] {criteria}")

    if is_blocking:
        lines.extend([
            "",
            "> ⛔ **阻塞合并** — 此任务完成后方可合并",
        ])

    lines.append("")
    lines.append("---")
    lines.append("*由 Harness Code Copilot 生成*")

    return "\n".join(lines)


def _acceptance_criteria(card_type: str, card: Dict[str, Any]) -> List[str]:
    """Get acceptance criteria for a card type."""
    type_criteria = {
        "fix_test": [
            "全部测试通过",
            "禁止重构无关模块",
            "仅修改指定范围内的文件",
        ],
        "fix_review": [
            "处理所有 Codex 阻塞性问题",
            "限制修改范围，禁止扩大改动",
            "需要重新运行 eval 验证",
            "需要重新进行 Codex review",
        ],
        "risk_alert": [
            "审查高风险文件变更",
            "确认修改不会引入安全问题",
            "必要时添加测试覆盖",
        ],
        "merge_check": [
            "确认无未解决 blocking issues",
            "审查所有高风险文件变更",
            "确认测试全部通过",
        ],
        "code_change": [
            "变更范围不超出指定模块",
            "添加或更新对应测试",
            "通过项目现有测试套件",
        ],
        "evidence": [
            "确认证据完整性 (SHA256)",
            "确认证据时间戳未过期",
        ],
        "companion": [
            "占位卡片 — 无实际操作项",
        ],
    }
    return type_criteria.get(card_type, ["完成卡所述任务", "通过项目测试"])


def export_all_task_cards_markdown(cards: List[Dict[str, Any]]) -> str:
    """Export all task cards as a single markdown document."""
    sections = ["# 任务卡列表", ""]
    for i, card in enumerate(cards, 1):
        md = export_task_card_markdown(card)
        sections.append(f"## {i}. {card.get('title', '任务卡')}")
        sections.append("")
        sections.append(md.split("---")[0].strip())  # strip footer
        sections.append("")
        sections.append("---")
        sections.append("")

    sections.append("*由 Harness Code Copilot 生成*")
    return "\n".join(sections)
