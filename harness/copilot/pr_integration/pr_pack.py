"""PR Pack — build and export local PR/MR review pack.

Read-only. Consumes existing Copilot data structures:
  - CopilotDashboardState (from build_dashboard)
  - LoopArtifacts (from load_loop_artifacts)
  - AgentState
  - RiskAlerts
  - TaskCards
  - MergeReadiness
  - EvidencePack

No external API calls. No auto-comment. No merge.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ..schemas import (
    MergeReadinessState,
    now_iso,
)
from ..view_models import (
    CopilotDashboardState,
    build_dashboard,
)
from ..markdown_renderer import render_changes, render_modules
from .risk_checklist import build_risk_checklist, render_checklist_markdown, render_checklist_json
from .reviewer_actions import build_reviewer_actions, render_actions_markdown, render_actions_json
from .pr_comment_renderer import render_pr_comment, render_summary_section


def build_pr_pack(
    project_root: str,
    diff_ref: str = "HEAD~1",
) -> Dict[str, Any]:
    """Build PR pack from a project path.

    Args:
        project_root: Path to project root.
        diff_ref: Git diff base ref.

    Returns:
        dict with full PR pack data.
    """
    dashboard = build_dashboard(project_root, diff_ref=diff_ref)
    return _pack_from_dashboard(dashboard, project_root)


def build_pr_pack_from_loop(
    loop_run_dir: str,
) -> Dict[str, Any]:
    """Build PR pack from a loop run directory.

    Args:
        loop_run_dir: Path to loop run directory.

    Returns:
        dict with full PR pack data.
    """
    from ..integration.loop_artifact_loader import load_loop_artifacts
    from ..integration.loop_to_copilot_mapper import artifacts_to_dashboard

    artifacts = load_loop_artifacts(loop_run_dir)
    dashboard = artifacts_to_dashboard(artifacts)
    return _pack_from_dashboard(dashboard, loop_run_dir, artifacts)


def _pack_from_dashboard(
    dashboard: CopilotDashboardState,
    source_path: str,
    loop_artifacts: Any = None,
) -> Dict[str, Any]:
    """Convert dashboard state to PR pack dict."""
    dashboard_dict = dashboard.to_dict()

    # Build risk checklist
    risk_alerts = _extract_risk_alerts(dashboard_dict)
    changed_files = _extract_changed_files(dashboard_dict)
    high_risk_modules = _extract_high_risk_modules(dashboard_dict)
    risk_checklist = build_risk_checklist(
        risk_alerts=risk_alerts,
        changed_files=changed_files,
        high_risk_modules=high_risk_modules,
    )

    # Build reviewer actions
    readiness = dashboard_dict.get("readiness", {})
    blocking_issues = readiness.get("blocking_issues", [])
    pending_cards = 0
    task_cards = dashboard_dict.get("task_cards", {})
    if task_cards:
        pending_cards = len(task_cards.get("cards", []))
    evidence = dashboard_dict.get("evidence", {})
    evidence_total = evidence.get("total", 0) if evidence else 0

    reviewer_actions = build_reviewer_actions(
        merge_state=readiness.get("state"),
        blocking_issues=blocking_issues,
        pending_cards=pending_cards,
        high_risk_count=readiness.get("high_risk_count", 0),
        evidence_total=evidence_total,
        agent_state=dashboard_dict.get("agent_state"),
        risk_checklist=risk_checklist,
    )

    # Build summary
    summary = _build_summary(dashboard_dict)

    # Evidence files (from loop artifacts or derived)
    evidence_files = _extract_evidence_files(loop_artifacts)

    pack = {
        "pack_version": "1.0",
        "generated_at": dashboard_dict.get("generated_at", now_iso()),
        "project_name": dashboard_dict.get("project_name", ""),
        "project_root": dashboard_dict.get("project_root", ""),
        "branch": dashboard_dict.get("branch", "unknown"),
        "source_path": source_path,
        "summary": summary,
        "agent_state": dashboard_dict.get("agent_state", {}),
        "readiness": readiness,
        "risk_checklist": risk_checklist,
        "modules": dashboard_dict.get("modules", []),
        "recent_changes": dashboard_dict.get("recent_changes", []),
        "task_cards": task_cards,
        "evidence": evidence,
        "evidence_files": evidence_files,
        "reviewer_actions": reviewer_actions,
        "readonly": True,
        "no_external_api": True,
    }

    return pack


def export_pr_pack(
    pack: Dict[str, Any],
    output_dir: str,
) -> Dict[str, Any]:
    """Export a PR pack to individual markdown files + JSON.

    Args:
        pack: PR pack dictionary from build_pr_pack().
        output_dir: Output directory for generated files.

    Returns:
        dict with success status and file paths.
    """
    result = {"success": False, "files": []}

    out_dir = os.path.abspath(output_dir)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except (OSError, PermissionError) as e:
        result["error"] = f"Cannot create output directory: {e}"
        return result

    file_map = {
        "pr_summary.md": _render_summary_md(pack),
        "merge_readiness_comment.md": _render_readiness_md(pack),
        "risk_checklist.md": render_checklist_markdown(pack.get("risk_checklist", [])),
        "agent_state_summary.md": _render_agent_state_md(pack),
        "changed_modules.md": _render_modules_md(pack),
        "task_cards.md": _render_task_cards_md(pack),
        "evidence_pack.md": _render_evidence_md(pack),
        "reviewer_actions.md": render_actions_markdown(pack.get("reviewer_actions", [])),
    }

    for filename, content in file_map.items():
        filepath = os.path.join(out_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            result["files"].append(filepath)
        except IOError as e:
            result["error"] = f"Failed to write {filename}: {e}"
            return result

    # Write combined JSON
    json_path = os.path.join(out_dir, "pr_pack.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(pack, f, indent=2, ensure_ascii=False, default=str)
        result["files"].append(json_path)
    except (IOError, TypeError) as e:
        result["error"] = f"Failed to write JSON: {e}"
        return result

    result["success"] = True
    result["output_dir"] = out_dir
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_summary(dashboard_dict: Dict[str, Any]) -> str:
    """Generate a concise PR summary from dashboard data."""
    parts = []
    name = dashboard_dict.get("project_name", "")
    branch = dashboard_dict.get("branch", "")
    changes = dashboard_dict.get("recent_changes", [])
    modules = dashboard_dict.get("modules", [])
    agent = dashboard_dict.get("agent_state", {})
    readiness = dashboard_dict.get("readiness", {})

    if name:
        parts.append(f"项目: {name}")
    if branch:
        parts.append(f"分支: {branch}")
    if agent:
        parts.append(f"Agent: {agent.get('summary', 'unknown')}")
    if readiness:
        parts.append(f"合并: {readiness.get('state_label', 'unknown')}")
    if modules:
        parts.append(f"变更模块: {len(modules)}")
    if changes:
        total_files = sum(len(c.get("files_changed", [])) for c in changes)
        parts.append(f"变更文件: ~{total_files}")

    return " | ".join(parts) if parts else "无可用摘要"


def _extract_risk_alerts(dashboard_dict: Dict[str, Any]) -> list:
    """Extract risk alert objects from dashboard task cards."""
    task_cards = dashboard_dict.get("task_cards", {})
    if not task_cards:
        return []
    cards = task_cards.get("cards", [])
    alerts = []
    for card in cards:
        if card.get("card_type") == "risk_alert":
            alerts.append(type("RiskAlert", (), {
                "title": card.get("title", ""),
                "level": type("Level", (), {"value": "high"})(),
                "module": card.get("module", ""),
                "is_blocking": card.get("is_blocking", False),
            })())
    return alerts


def _extract_changed_files(dashboard_dict: Dict[str, Any]) -> List[str]:
    """Extract list of changed file paths."""
    files = []
    changes = dashboard_dict.get("recent_changes", [])
    for ch in changes:
        files.extend(ch.get("files_changed", []))
    return files


def _extract_high_risk_modules(dashboard_dict: Dict[str, Any]) -> List[str]:
    """Extract list of high-risk module names."""
    modules = dashboard_dict.get("modules", [])
    high_risk = []
    for mod in modules:
        if mod.get("risk_level") in ("high", "critical"):
            high_risk.append(mod.get("name", ""))
    return high_risk


def _extract_evidence_files(loop_artifacts: Any) -> List[str]:
    """Extract evidence file paths from loop artifacts."""
    if loop_artifacts is None:
        return []

    files = []
    for attr in ["eval_report", "final_review_envelope", "final_gate_result", "patch_diff", "loop_report"]:
        val = getattr(loop_artifacts, attr, None)
        if val is not None:
            files.append(attr)
    return files


def _render_summary_md(pack: Dict[str, Any]) -> str:
    """Render PR summary markdown file."""
    summary = pack.get("summary", "无可用摘要")
    return f"""# PR 变更摘要

**项目**: {pack.get('project_name', 'Unknown')}
**分支**: `{pack.get('branch', 'unknown')}`
**生成时间**: {pack.get('generated_at', '')}

{summary}

---

*Harness Code Copilot — PR Pack Exporter (只读)*
"""


def _render_readiness_md(pack: Dict[str, Any]) -> str:
    """Render merge readiness comment markdown."""
    readiness = pack.get("readiness", {})
    lines = ["# 合并就绪度评估", ""]
    if not readiness:
        lines.append("无合并就绪度数据。")
        return "\n".join(lines)
    lines.append(f"{readiness.get('state_icon', '❓')} **状态**: {readiness.get('state_label', '未知')}")
    lines.append(f"  - {readiness.get('summary', '')}")
    for issue in readiness.get("blocking_issues", []):
        lines.append(f"  - 🚫 {issue}")
    lines.append("")
    lines.append(f"**审查要求**: {'需要' if readiness.get('review_required', False) else '无需'}")
    lines.append(f"**待处理卡**: {readiness.get('pending_cards', 0)}")
    lines.append(f"**高风险文件**: {readiness.get('high_risk_count', 0)}")
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _render_agent_state_md(pack: Dict[str, Any]) -> str:
    """Render agent state summary markdown."""
    agent = pack.get("agent_state", {})
    lines = ["# Agent 状态摘要", ""]
    if not agent:
        lines.append("无 Agent 状态数据。")
        return "\n".join(lines)
    icon_map = {
        "idle": "💤", "planning": "📋", "implementing": "🔧",
        "testing": "🧪", "repairing": "🔨", "reviewing": "👁️",
        "waiting_for_user": "⏳", "completed": "✅", "failed": "❌", "blocked": "🚫",
    }
    icon = icon_map.get(agent.get("state", ""), "❓")
    lines.append(f"{icon} **状态**: {agent.get('summary', '未知')}")
    lines.append(f"- **置信度**: {agent.get('confidence', 0):.0%}")
    lines.append(f"- **严重度**: {agent.get('severity', 'low')}")
    lines.append(f"- **阻塞合并**: {'是 🚫' if agent.get('blocking', False) else '否 ✅'}")
    if agent.get("source_events"):
        lines.append(f"- **触发事件**: {', '.join(agent['source_events'][:5])}")
    if agent.get("recommended_action"):
        lines.append(f"- **建议操作**: {agent['recommended_action']}")
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _render_modules_md(pack: Dict[str, Any]) -> str:
    """Render changed modules markdown."""
    modules = pack.get("modules", [])
    lines = ["# 变更模块", ""]
    if not modules:
        lines.append("无模块数据。")
        return "\n".join(lines)
    for mod in modules:
        name = mod.get("name", "unknown")
        risk_level = mod.get("risk_level", "unknown")
        file_count = mod.get("file_count", 0)
        high_risk = mod.get("high_risk_files", [])
        lines.append(f"### {name}")
        lines.append(f"- **文件数**: {file_count}")
        lines.append(f"- **风险**: {risk_level}")
        for hrf in high_risk:
            lines.append(f"  - ⚠ `{hrf.get('path', '')}` (score: {hrf.get('score', 0):.1f})")
        lines.append("")
    return "\n".join(lines)


def _render_task_cards_md(pack: Dict[str, Any]) -> str:
    """Render task cards markdown."""
    task_cards = pack.get("task_cards", {})
    lines = ["# 任务卡", ""]
    if not task_cards:
        lines.append("无任务卡。")
        return "\n".join(lines)
    cards = task_cards.get("cards", [])
    if not cards:
        lines.append("无待处理任务卡。")
        return "\n".join(lines)
    for card in cards:
        title = card.get("title", "")
        priority = card.get("priority_label", "")
        card_type = card.get("card_type", "task")
        is_blocking = card.get("is_blocking", False)
        prefix = "🔴 " if is_blocking else "📋 "
        lines.append(f"{prefix}**{title}**")
        lines.append(f"  - 类型: {card_type} | 优先级: {priority}")
        if card.get("module"):
            lines.append(f"  - 模块: `{card['module']}`")
        if card.get("target_file"):
            lines.append(f"  - 文件: `{card['target_file']}`")
        if card.get("description"):
            desc = card["description"][:200]
            lines.append(f"  - 说明: {desc}")
        lines.append("")
    return "\n".join(lines)


def _render_evidence_md(pack: Dict[str, Any]) -> str:
    """Render evidence pack markdown."""
    evidence = pack.get("evidence", {})
    evidence_files = pack.get("evidence_files", [])
    lines = ["# 证据包", ""]
    if evidence:
        lines.append(f"- **包 ID**: `{evidence.get('pack_id', '')}`")
        lines.append(f"- **总证据数**: {evidence.get('total', 0)}")
        lines.append(f"- **通过**: {evidence.get('passed', 0)}")
        lines.append(f"- **失败**: {evidence.get('failed', 0)}")
        lines.append("")
    if evidence_files:
        lines.append("### 证据文件")
        for ef in evidence_files:
            lines.append(f"- `{ef}`")
        lines.append("")
    if not evidence and not evidence_files:
        lines.append("无可用证据。")
    return "\n".join(lines)
