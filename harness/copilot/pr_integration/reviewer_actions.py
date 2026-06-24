"""Reviewer Actions — generate structured reviewer action items.

Action items are derived from:
- Task cards (blocking, pending)
- Merge readiness state
- Risk alerts
- Agent state
- Evidence gaps
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_reviewer_actions(
    merge_state: Optional[str] = None,
    blocking_issues: Optional[List[str]] = None,
    pending_cards: int = 0,
    high_risk_count: int = 0,
    evidence_total: int = 0,
    agent_state: Optional[Dict[str, Any]] = None,
    risk_checklist: Optional[List[Dict[str, Any]]] = None,
    task_cards: Optional[List[Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate reviewer action items from analysis data.

    Args:
        merge_state: Merge readiness state (pass/block/review_needed).
        blocking_issues: List of blocking issue descriptions.
        pending_cards: Number of pending task cards.
        high_risk_count: Number of high-risk files.
        evidence_total: Total evidence entries.
        agent_state: Agent state dict.
        risk_checklist: Risk checklist items.
        task_cards: Task card objects.

    Returns:
        List of action items with priority, action, and reasoning.
    """
    actions: List[Dict[str, Any]] = []

    # 1. Merge state actions
    if merge_state == "block":
        actions.append({
            "priority": "🔴 紧急",
            "action": "解决阻塞问题后再合并",
            "reasoning": f"合并就绪度为 block，存在 {len(blocking_issues or [])} 个阻塞项",
            "category": "merge_blocker",
        })
    elif merge_state == "review_needed":
        actions.append({
            "priority": "🟠 高优先级",
            "action": "审查全部变更后再合并",
            "reasoning": "合并就绪度为 review_needed，需要人工审查确认",
            "category": "review_required",
        })
    else:
        actions.append({
            "priority": "✅ 正常",
            "action": "合并已就绪，建议最终检查后合并",
            "reasoning": "合并就绪度为 pass，无阻塞项",
            "category": "ready_to_merge",
        })

    # 2. Blocking issues
    if blocking_issues:
        for issue in (blocking_issues[:5]):
            actions.append({
                "priority": "🔴 紧急",
                "action": f"处理阻塞问题: {issue}",
                "reasoning": "该问题阻止安全合并",
                "category": "blocking_issue",
            })

    # 3. Pending task cards
    if pending_cards > 0:
        actions.append({
            "priority": "🟠 高优先级",
            "action": f"完成 {pending_cards} 个待处理任务卡",
            "reasoning": f"仍有 {pending_cards} 张任务卡处于待处理状态",
            "category": "pending_tasks",
        })

    # 4. High-risk files
    if high_risk_count > 0:
        actions.append({
            "priority": "🟠 高优先级",
            "action": f"审查 {high_risk_count} 个高风险文件的变更",
            "reasoning": "高风险文件包含敏感逻辑修改",
            "category": "high_risk_review",
        })

    # 5. Agent state actions
    if agent_state:
        astate = agent_state.get("state", "")
        blocking = agent_state.get("blocking", False)
        if blocking:
            actions.append({
                "priority": "🔴 紧急",
                "action": f"Agent 状态为阻塞 ({astate})，解决 Agent 阻塞原因",
                "reasoning": agent_state.get("summary", "Agent 报告阻塞状态"),
                "category": "agent_blocked",
            })

        action_priority = "🟡 中优先级" if astate in ("implementing", "testing") else "✅ 正常"
        actions.append({
            "priority": action_priority,
            "action": f"确认 Agent 最终状态 ({agent_state.get('summary', '')})",
            "reasoning": f"Agent 置信度: {agent_state.get('confidence', 0):.0%}",
            "category": "agent_acknowledge",
        })

    # 6. Risk checklist items
    if risk_checklist:
        checked_items = [r for r in risk_checklist if r.get("checked")]
        if checked_items:
            actions.append({
                "priority": "🟡 中优先级",
                "action": f"审查 {len(checked_items)} 个标记的风险项",
                "reasoning": "风险检查清单中有标记需要关注的项目",
                "category": "risk_review",
            })

    # 7. Evidence gaps
    if evidence_total == 0:
        actions.append({
            "priority": "🟠 高优先级",
            "action": "缺少证据包，建议补充测试结果和审查记录",
            "reasoning": "没有可用的证据条目，PR 缺少验证材料",
            "category": "evidence_gap",
        })

    return actions


def render_actions_markdown(actions: List[Dict[str, Any]]) -> str:
    """Render action items as markdown checklist."""
    lines = ["## Reviewer Action Items", ""]
    if not actions:
        lines.append("无待处理的 Reviewer 操作。")
        lines.append("")
        return "\n".join(lines)

    for action in actions:
        lines.append(f"- {action['priority']}: {action['action']}")
        lines.append(f"  - *{action['reasoning']}*")
        lines.append("")

    return "\n".join(lines)


def render_actions_json(actions: List[Dict[str, Any]]) -> str:
    """Render action items as JSON."""
    import json
    return json.dumps({"reviewer_actions": actions}, indent=2, ensure_ascii=False)
