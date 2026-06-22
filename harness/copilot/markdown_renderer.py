"""Markdown Renderer — render ViewModels to user-friendly markdown."""

from __future__ import annotations

from typing import List

from .view_models import (
    CopilotDashboardState, ModuleCardViewModel, RecentChangeViewModel,
    SuggestionListViewModel, TaskCardViewModel, TaskCardListViewModel,
    MergeReadinessViewModel, RiskAlertViewModel, EvidencePackViewModel,
    WaitingCompanionViewModel,
)


def render_dashboard(dashboard: CopilotDashboardState) -> str:
    """Render the full dashboard as markdown."""
    lines: List[str] = []

    lines.append(f"# Harness Code Copilot Dashboard — {dashboard.project_name}")
    lines.append("")
    lines.append("## 当前项目状态")
    lines.append("")
    lines.append(f"- **项目**: {dashboard.project_name}")
    lines.append(f"- **路径**: `{dashboard.project_root}`")
    lines.append(f"- **分支**: `{dashboard.branch}`")
    lines.append(f"- **Agent 状态**: {dashboard.agent_phase_label}")
    lines.append(f"- **未提交变更**: {dashboard.uncommitted_changes} 个文件")
    lines.append(f"- **模块数**: {dashboard.module_count}")
    lines.append(f"- **整体风险**: {_render_risk_badge(dashboard.overall_risk_level)}")
    lines.append("")

    # Merge readiness
    if dashboard.readiness:
        lines.append(_render_readiness_section(dashboard.readiness))
        lines.append("")

    # Recent changes
    if dashboard.recent_changes:
        lines.append(_render_changes_section(dashboard.recent_changes))
        lines.append("")

    # Modules
    if dashboard.modules:
        lines.append(_render_modules_section(dashboard.modules))
        lines.append("")

    # Suggestions
    if dashboard.suggestions and dashboard.suggestions.suggestions:
        lines.append(_render_suggestions_section(dashboard.suggestions))
        lines.append("")

    # Task cards
    if dashboard.task_cards and dashboard.task_cards.cards:
        lines.append(_render_task_cards_section(dashboard.task_cards))
        lines.append("")

    # Evidence
    if dashboard.evidence:
        lines.append(_render_evidence_section(dashboard.evidence))
        lines.append("")

    # Companion placeholder
    if dashboard.companion:
        lines.append(_render_companion_section(dashboard.companion))
        lines.append("")

    lines.append("---")
    lines.append(f"*生成时间: {dashboard.generated_at}*")

    return "\n".join(lines)


def render_modules(modules: List[ModuleCardViewModel]) -> str:
    """Render module cards as markdown."""
    lines = ["# 模块卡片", ""]
    for mod in modules:
        lines.append(f"## {mod.name}")
        lines.append("")
        lines.append(f"- **文件数**: {mod.file_count}")
        lines.append(f"- **主语言**: {mod.primary_language}")
        lines.append(f"- **风险**: {_render_risk_badge(mod.risk_level)} — {mod.risk_description}")
        if mod.dependencies:
            lines.append(f"- **依赖**: {', '.join(mod.dependencies)}")
        if mod.dependents:
            lines.append(f"- **被依赖**: {', '.join(mod.dependents)}")
        if mod.high_risk_files:
            lines.append(f"- **高风险文件**:")
            for hf in mod.high_risk_files:
                reasons = "; ".join(hf.get("reasons", []))
                lines.append(f"  - `{hf['path']}` (风险分: {hf['score']:.1f}) {reasons}")
        lines.append("")
    return "\n".join(lines)


def render_task_cards(cards: TaskCardListViewModel) -> str:
    """Render task cards as markdown."""
    lines = ["# 推荐任务卡", ""]
    if cards.summary:
        s = cards.summary
        lines.append(f"**总计**: {s.get('total_cards', 0)} 张 | "
                     f"待处理: {s.get('by_state', {}).get('pending', 0)} | "
                     f"阻塞数: {s.get('blocking_count', 0)}")
        lines.append("")

    for card in cards.cards:
        if card.is_blocking:
            prefix = "🔴 "
        elif card.card_type == "risk_alert":
            prefix = "⚠️ "
        else:
            prefix = "📋 "

        lines.append(f"{prefix}**{card.title}**")
        lines.append(f"  - 类型: {card.card_type} | 优先级: {card.priority_label} | 状态: {card.state_label}")
        if card.module:
            lines.append(f"  - 模块: `{card.module}`")
        if card.target_file:
            lines.append(f"  - 目标文件: `{card.target_file}`")
        if card.description:
            # Truncate long descriptions
            desc = card.description[:200] + "..." if len(card.description) > 200 else card.description
            lines.append(f"  - 说明: {desc}")
        if card.is_blocking:
            lines.append(f"  - ⛔ 阻塞合并")
        lines.append("")

    return "\n".join(lines)


def render_readiness(rm: MergeReadinessViewModel) -> str:
    """Render merge readiness as markdown."""
    return _render_readiness_section(rm)


def render_changes(changes: List[RecentChangeViewModel]) -> str:
    """Render recent changes as markdown."""
    return _render_changes_section(changes)


def render_evidence(ep: EvidencePackViewModel) -> str:
    """Render evidence pack as markdown."""
    return _render_evidence_section(ep)


def render_companion(wc: WaitingCompanionViewModel) -> str:
    """Render waiting companion as markdown."""
    return _render_companion_section(wc)


# ---------------------------------------------------------------------------
# Internal section renderers
# ---------------------------------------------------------------------------

def _render_risk_badge(level: str) -> str:
    badges = {
        "critical": "🔴 极高",
        "high": "🟠 高",
        "medium": "🟡 中",
        "low": "✅ 低",
    }
    return badges.get(level, f"❓ {level}")


def _render_readiness_section(rm: MergeReadinessViewModel) -> str:
    lines = ["## 合并就绪度", ""]
    lines.append(f"{rm.state_icon} **状态**: {rm.state_label}")
    lines.append(f"  - {rm.summary}")
    if rm.blocking_issues:
        lines.append(f"  - **阻塞项** ({len(rm.blocking_issues)}):")
        for issue in rm.blocking_issues[:5]:
            lines.append(f"    - {issue}")
        if len(rm.blocking_issues) > 5:
            lines.append(f"    - ... 还有 {len(rm.blocking_issues) - 5} 项")
    lines.append(f"  - 需审查: {'是' if rm.review_required else '否'}")
    lines.append(f"  - 待处理任务卡: {rm.pending_cards}")
    lines.append(f"  - 高风险文件数: {rm.high_risk_count}")
    return "\n".join(lines)


def _render_changes_section(changes: List[RecentChangeViewModel]) -> str:
    lines = ["## 最近修改", ""]
    for change in changes:
        if change.has_risks:
            icon = "⚠️ "
        else:
            icon = "📝 "
        lines.append(f"{icon}**{change.module}** — {change.summary}")
        lines.append(f"  - 意图: {change.intent}")
        if change.files_changed:
            files_str = ", ".join(change.files_changed[:5])
            if len(change.files_changed) > 5:
                files_str += f" ... 共 {len(change.files_changed)} 个文件"
            lines.append(f"  - 涉及文件: `{files_str}`")
        if change.risk_warnings:
            for warn in change.risk_warnings[:3]:
                lines.append(f"  - ⚠ {warn}")
        lines.append("")
    return "\n".join(lines)


def _render_modules_section(modules: List[ModuleCardViewModel]) -> str:
    lines = ["## 重点模块", ""]
    # Sort by risk level: critical > high > medium > low
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}
    sorted_mods = sorted(modules, key=lambda m: risk_order.get(m.risk_level, 5))

    for mod in sorted_mods:
        if mod.risk_level in ("critical", "high"):
            icon = "🔴 "
        elif mod.risk_level == "medium":
            icon = "🟡 "
        else:
            icon = "✅ "

        lines.append(f"{icon}**{mod.name}** — {mod.file_count} 文件")
        lines.append(f"  - 风险: {_render_risk_badge(mod.risk_level)}")
        if mod.dependencies:
            lines.append(f"  - 依赖: {', '.join(mod.dependencies[:5])}")
        if mod.high_risk_files:
            for hf in mod.high_risk_files:
                lines.append(f"  - ⚠ `{hf['path']}`")
        lines.append("")
    return "\n".join(lines)


def _render_suggestions_section(suggestions: SuggestionListViewModel) -> str:
    lines = ["## 下一步建议", ""]
    for sug in suggestions.suggestions:
        lines.append(f"- {sug.priority_label}: {sug.suggestion}")
        lines.append(f"  - 原因: {sug.reason}")
        if sug.file_path:
            lines.append(f"  - 文件: `{sug.file_path}`")
        lines.append("")
    return "\n".join(lines)


def _render_task_cards_section(cards: TaskCardListViewModel) -> str:
    return render_task_cards(cards)


def _render_evidence_section(ep: EvidencePackViewModel) -> str:
    lines = ["## 证据包", ""]
    lines.append(f"- **包 ID**: `{ep.pack_id}`")
    lines.append(f"- **总证据数**: {ep.total}")
    lines.append(f"- **通过**: {ep.passed}")
    lines.append(f"- **失败**: {ep.failed}")
    lines.append(f"- **完整性校验**: `{ep.integrity_hash[:16]}...`")
    return "\n".join(lines)


def _render_companion_section(wc: WaitingCompanionViewModel) -> str:
    lines = ["## 等待陪伴", ""]
    if wc.is_active:
        lines.append(f"🔄 **{wc.status_text}**")
        if wc.waiting_since:
            lines.append(f"  - 自: {wc.waiting_since}")
        lines.append("  - 🎵 等待陪伴模式已激活（音乐服务未接入）")
    else:
        lines.append("⚪ Agent 待命中。等待陪伴模式未激活。")
    return "\n".join(lines)
