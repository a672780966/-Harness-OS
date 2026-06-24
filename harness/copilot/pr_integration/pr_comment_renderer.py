"""PR Comment Renderer — render PR review pack as inline markdown comment.

Produces a single self-contained PR comment that can be copied to GitHub/GitLab.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .risk_checklist import render_checklist_markdown, build_risk_checklist
from .reviewer_actions import render_actions_markdown, build_reviewer_actions


def render_pr_comment(
    pr_pack: Dict[str, Any],
    format: str = "markdown",
) -> str:
    """Render the full PR comment.

    Args:
        pr_pack: Dictionary from build_pr_pack() or build_pr_pack_from_loop().
        format: "markdown" or "json".

    Returns:
        Formatted PR comment string.
    """
    if format == "json":
        return _render_comment_json(pr_pack)
    return _render_comment_markdown(pr_pack)


def _render_comment_markdown(pack: Dict[str, Any]) -> str:
    """Render a complete PR comment in markdown."""
    lines: List[str] = []

    # Header
    lines.append("## 🤖 Harness Copilot PR Review Pack")
    lines.append("")
    lines.append(f"**项目**: {pack.get('project_name', 'Unknown')}")
    lines.append(f"**分支**: `{pack.get('branch', 'unknown')}`")
    lines.append(f"**生成时间**: {pack.get('generated_at', '')}")
    lines.append("---")
    lines.append("")

    # Summary
    summary = pack.get("summary", "")
    if summary:
        lines.append(f"### 变更摘要")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Agent State
    agent_state = pack.get("agent_state", {})
    if agent_state:
        lines.append("### 🤖 Agent 状态")
        lines.append("")
        astate = agent_state.get("state", "idle")
        icon_map = {
            "idle": "💤", "planning": "📋", "implementing": "🔧",
            "testing": "🧪", "repairing": "🔨", "reviewing": "👁️",
            "waiting_for_user": "⏳", "completed": "✅", "failed": "❌", "blocked": "🚫",
        }
        icon = icon_map.get(astate, "❓")
        summary_text = agent_state.get("summary", "无状态")
        confidence = agent_state.get("confidence", 0)
        blocking = agent_state.get("blocking", False)
        lines.append(f"{icon} **{summary_text}**")
        lines.append(f"  - 置信度: {confidence:.0%}")
        lines.append(f"  - 严重度: {agent_state.get('severity', 'low')}")
        lines.append(f"  - 阻塞合并: {'是 🚫' if blocking else '否 ✅'}")
        if agent_state.get("recommended_action"):
            lines.append(f"  - 建议操作: {agent_state['recommended_action']}")
        lines.append("")

    # Merge Readiness
    readiness = pack.get("readiness", {})
    if readiness:
        lines.append("### 🔀 合并就绪度")
        lines.append("")
        state = readiness.get("state", "unknown")
        state_icon = readiness.get("state_icon", "❓")
        state_label = readiness.get("state_label", "未知")
        summary_text = readiness.get("summary", "")
        lines.append(f"{state_icon} **状态**: {state_label}")
        if summary_text:
            lines.append(f"  - {summary_text}")
        for issue in readiness.get("blocking_issues", []):
            lines.append(f"  - 🚫 {issue}")
        lines.append(f"  - 需审查: {'是' if readiness.get('review_required', False) else '否'}")
        lines.append(f"  - 待处理卡: {readiness.get('pending_cards', 0)}")
        lines.append(f"  - 高风险文件: {readiness.get('high_risk_count', 0)}")
        lines.append("")

    # Risk Checklist
    checklist = pack.get("risk_checklist", [])
    if checklist:
        lines.append(render_checklist_markdown(checklist))
        lines.append("")

    # Changed Modules
    modules = pack.get("modules", [])
    if modules:
        lines.append("### 🧩 变更模块")
        lines.append("")
        for mod in modules:
            name = mod.get("name", "unknown")
            risk_level = mod.get("risk_level", "unknown")
            file_count = mod.get("file_count", 0)
            high_risk = mod.get("high_risk_files", [])
            risk_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "✅"}.get(risk_level, "❓")
            lines.append(f"- {risk_icon} **{name}** — {file_count} 文件, 风险: {risk_level}")
            for hrf in high_risk[:3]:
                lines.append(f"  - ⚠ `{hrf.get('path', '')}` (score: {hrf.get('score', 0):.1f})")
        lines.append("")

    # Task Cards
    task_cards = pack.get("task_cards", {})
    if task_cards:
        cards = task_cards.get("cards", [])
        if cards:
            lines.append("### 📋 任务卡")
            lines.append("")
            for card in cards[:8]:
                title = card.get("title", "")
                priority = card.get("priority_label", "")
                is_blocking = card.get("is_blocking", False)
                prefix = "🔴 " if is_blocking else "📋 "
                lines.append(f"- {prefix}**{title}** ({priority})")
            if len(cards) > 8:
                lines.append(f"  - ... 还有 {len(cards) - 8} 张任务卡")
            lines.append("")

    # Evidence
    evidence = pack.get("evidence", {})
    if evidence:
        lines.append("### 🔐 证据包")
        lines.append("")
        lines.append(f"- **总证据数**: {evidence.get('total', 0)}")
        lines.append(f"- **通过**: {evidence.get('passed', 0)}")
        lines.append(f"- **失败**: {evidence.get('failed', 0)}")
        lines.append(f"- **包 ID**: `{evidence.get('pack_id', '')}`")
        lines.append("")

        # Evidence files
        evidence_files = pack.get("evidence_files", [])
        if evidence_files:
            lines.append("#### 证据文件清单")
            lines.append("")
            for ef in evidence_files:
                lines.append(f"- `{ef}`")
            lines.append("")

    # Reviewer Actions
    actions = pack.get("reviewer_actions", [])
    if actions:
        lines.append(render_actions_markdown(actions))
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Harness Code Copilot — 只读本地分析 · 无外部 API 调用 · 无自动修改*")
    lines.append("")

    return "\n".join(lines)


def _render_comment_json(pack: Dict[str, Any]) -> str:
    """Render the PR pack as JSON."""
    import json
    return json.dumps(pack, indent=2, ensure_ascii=False)


def render_summary_section(pack: Dict[str, Any]) -> str:
    """Render just the summary section."""
    summary = pack.get("summary", "")
    if not summary:
        # Auto-generate summary from pack data
        parts = []
        agent = pack.get("agent_state", {})
        if agent:
            parts.append(f"Agent 状态: {agent.get('summary', 'unknown')}")
        readiness = pack.get("readiness", {})
        if readiness:
            parts.append(f"合并就绪: {readiness.get('state_label', 'unknown')}")
        modules = pack.get("modules", [])
        if modules:
            parts.append(f"涉及 {len(modules)} 个模块")
        return " | ".join(parts)
    return summary
