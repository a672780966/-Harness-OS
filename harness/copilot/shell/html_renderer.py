"""HTML Renderer — render ViewModels to self-contained HTML dashboard sections.

Produces a single-page static HTML file with embedded CSS.
All sections rendered as tabbed panels with copy-export support.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .static_assets import DASHBOARD_CSS


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _risk_badge_html(level: str) -> str:
    return f'<span class="risk-badge {_escape_html(level.lower())}">{_escape_html(level.upper())}</span>'


def _section_html(section_id: str, title: str, icon: str, body: str) -> str:
    return f"""<div class="section">
  <div class="section-header">{icon} {_escape_html(title)}</div>
  <div class="section-body">
{body}
  </div>
</div>"""


def _readiness_card_html(state: str, state_icon: str, state_label: str, summary: str, blocking_issues: List[str]) -> str:
    css_class = "pass" if state == "pass" else "block" if state == "block" else "review_needed"
    issues_html = ""
    if blocking_issues:
        items = "".join(f'<div class="issue-item">⚠ {_escape_html(i)}</div>' for i in blocking_issues)
        issues_html = f'<div class="issues-list">{items}</div>'
    return f"""<div class="readiness-card {css_class}">
  <div class="icon">{_escape_html(state_icon)}</div>
  <div>
    <div class="status">{_escape_html(state_label)}</div>
    <div class="summary">{_escape_html(summary)}</div>
    {issues_html}
  </div>
</div>"""


def _project_home_html(dashboard_state: Dict[str, Any]) -> str:
    """Render project home / header section."""
    name = dashboard_state.get("project_name", "Unknown")
    root = dashboard_state.get("project_root", "")
    branch = dashboard_state.get("branch", "unknown")
    agent_label = dashboard_state.get("agent_phase_label", "待命")
    uncommitted = dashboard_state.get("uncommitted_changes", 0)
    module_count = dashboard_state.get("module_count", 0)
    risk_level = dashboard_state.get("overall_risk_level", "unknown")
    gen_at = dashboard_state.get("generated_at", "")

    return f"""<div class="header">
  <h1>Harness Code Copilot Dashboard</h1>
  <div class="meta">
    <span>📁 {_escape_html(name)}</span>
    <span>🔀 {_escape_html(branch)}</span>
    <span>🤖 {_escape_html(agent_label)}</span>
    <span>📄 {uncommitted} 未提交</span>
    <span>🧩 {module_count} 模块</span>
    <span>{_risk_badge_html(risk_level)}</span>
  </div>
  {f'<div style="margin-top:8px;font-size:12px;color:var(--text-muted)">生成: {_escape_html(gen_at)} | 路径: <code>{_escape_html(root)}</code></div>' if root else ''}
</div>"""


def _stat_card_html(value: str, label: str, color: str = "") -> str:
    style = f' style="color:{color}"' if color else ""
    return f'<div class="stat-card"><div class="value"{style}>{_escape_html(value)}</div><div class="label">{_escape_html(label)}</div></div>'


def _overview_stats_html(dashboard_state: Dict[str, Any]) -> str:
    """Render overview stat cards."""
    mr = dashboard_state.get("readiness")
    task_cards = dashboard_state.get("task_cards")
    evidence = dashboard_state.get("evidence")

    total_modules = str(dashboard_state.get("module_count", 0))
    uncommitted = str(dashboard_state.get("uncommitted_changes", 0))
    total_cards = "0"
    if task_cards and isinstance(task_cards, dict):
        cards = task_cards.get("cards", [])
        total_cards = str(len(cards))

    evidence_total = "0"
    if evidence and isinstance(evidence, dict):
        evidence_total = str(evidence.get("total", 0))

    grid = "".join([
        _stat_card_html(total_modules, "模块"),
        _stat_card_html(uncommitted, "未提交文件", "var(--accent-orange)"),
        _stat_card_html(total_cards, "任务卡"),
        _stat_card_html(evidence_total, "证据条目", "var(--accent-cyan)"),
    ])
    return f'<div class="grid-4" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px">{grid}</div>'


def _modules_section_html(modules: List[Dict[str, Any]]) -> str:
    """Render module cards."""
    if not modules:
        return _section_html("modules", "模块卡片", "🧩", "<p style='color:var(--text-muted)'>无模块数据</p>")

    cards_html = ""
    for mod in modules:
        name = mod.get("name", "unknown")
        file_count = mod.get("file_count", 0)
        primary_lang = mod.get("primary_language", "Unknown")
        risk_level = mod.get("risk_level", "unknown")
        risk_desc = mod.get("risk_description", "")
        deps = mod.get("dependencies", [])
        dependents = mod.get("dependents", [])
        hr_files = mod.get("high_risk_files", [])

        hr_html = ""
        if hr_files:
            items = "".join(
                f'<div class="hr-file">📄 {_escape_html(hf.get("path", ""))} (风险分: {hf.get("score", 0):.1f})</div>'
                for hf in hr_files
            )
            hr_html = f'<div class="hr-files"><strong>高风险文件:</strong>{items}</div>'

        deps_text = ", ".join(deps[:8]) + ("..." if len(deps) > 8 else "") if deps else "无"
        dep_text = ", ".join(dependents[:8]) + ("..." if len(dependents) > 8 else "") if dependents else "无"

        cards_html += f"""<div class="module-card">
  <div class="module-name">
    <span>{_escape_html(name)}</span>
    <span>{_risk_badge_html(risk_level)}</span>
  </div>
  <div class="module-details">
    <p>📄 {file_count} 文件 | 🗣 {_escape_html(primary_lang)}</p>
    <p>{_escape_html(risk_desc)}</p>
    <p>⬅ 依赖: {_escape_html(deps_text)}</p>
    <p>➡ 被依赖: {_escape_html(dep_text)}</p>
    {hr_html}
  </div>
</div>"""

    return _section_html("modules", "模块卡片", "🧩", cards_html)


def _changes_section_html(changes: List[Dict[str, Any]]) -> str:
    """Render recent changes."""
    if not changes:
        return ""

    items = ""
    for ch in changes:
        module = ch.get("module", "?")
        summary = ch.get("summary", "")
        intent = ch.get("intent", "")
        files = ch.get("files_changed", [])
        lines_str = ch.get("lines_changed_str", "")
        risk_warnings = ch.get("risk_warnings", [])

        risks_html = "".join(f'<div class="issue-item" style="color:var(--accent-orange);font-size:12px">⚠ {_escape_html(r)}</div>' for r in risk_warnings) if risk_warnings else ""
        files_text = ", ".join(files[:5]) + ("..." if len(files) > 5 else "") if files else "无"

        items += f"""<div class="change-item">
  <div class="change-module">{_escape_html(module)}</div>
  <div class="change-summary">{_escape_html(summary)}</div>
  <span class="change-intent">{_escape_html(intent)}</span>
  <span style="margin-left:8px;font-size:12px;color:var(--text-muted)">📄 {_escape_html(files_text)} | {_escape_html(lines_str)}</span>
  {risks_html}
</div>"""

    return _section_html("changes", "最近修改", "📝", items)


def _suggestions_section_html(suggestions_data: Any) -> str:
    """Render suggestions."""
    if not suggestions_data:
        return ""

    if isinstance(suggestions_data, dict):
        suggestions_list = suggestions_data.get("suggestions", [])
    elif hasattr(suggestions_data, "suggestions"):
        suggestions_list = [s.to_dict() if hasattr(s, "to_dict") else s for s in suggestions_data.suggestions]
    else:
        suggestions_list = []

    if not suggestions_list:
        return ""

    items = ""
    for s in suggestions_list:
        if hasattr(s, "to_dict"):
            s = s.to_dict()
        text = s.get("suggestion", "")
        reason = s.get("reason", "")
        priority = s.get("priority_label", "")
        confidence = s.get("confidence_label", "")
        file_path = s.get("file_path", "")

        items += f"""<div class="suggestion-item">
  <div class="sugg-text">{_escape_html(text)}</div>
  <div class="sugg-reason">📌 {_escape_html(reason)}</div>
  <div style="font-size:12px;color:var(--text-muted);margin-top:4px">
    <span>{_escape_html(priority)}</span> | <span>置信度: {_escape_html(confidence)}</span>
    {f'| <code>{_escape_html(file_path)}</code>' if file_path else ''}
  </div>
</div>"""

    return _section_html("suggestions", "建议", "💡", items)


def _task_cards_section_html(task_cards_data: Any) -> str:
    """Render task cards with copy/export support."""
    if not task_cards_data:
        return ""

    if isinstance(task_cards_data, dict):
        cards = task_cards_data.get("cards", [])
    elif hasattr(task_cards_data, "cards"):
        cards = [c.to_dict() if hasattr(c, "to_dict") else c for c in task_cards_data.cards]
    else:
        cards = []

    if not cards:
        return _section_html("task-cards", "任务卡", "📋", "<p style='color:var(--text-muted)'>无待处理任务卡</p>")

    items = ""
    for card in cards:
        if hasattr(card, "to_dict"):
            card = card.to_dict()
        title = card.get("title", "")
        card_type = card.get("card_type", "task")
        state = card.get("state", "pending")
        priority = card.get("priority_label", "")
        module = card.get("module", "")
        target_file = card.get("target_file", "")
        description = card.get("description", "")
        is_blocking = card.get("is_blocking", False)
        risk_label = card.get("risk_label", "")

        blocking_cls = "blocking" if is_blocking else ""
        items += f"""<div class="task-card {blocking_cls}">
  <div class="tc-header">
    <div class="tc-title">{_escape_html(title)}</div>
    <div class="tc-type">{_escape_html(card_type)}</div>
  </div>
  <div class="tc-desc">{_escape_html(description)}</div>
  <div class="tc-meta">
    <span>{_escape_html(priority)}</span>
    {f'<span>🧩 {_escape_html(module)}</span>' if module else ''}
    {f'<span>📄 <code>{_escape_html(target_file)}</code></span>' if target_file else ''}
    <span>{'🚫 阻塞合并' if is_blocking else '✅ 非阻塞'}</span>
    <span>{_escape_html(risk_label)}</span>
  </div>
</div>"""

    return _section_html("task-cards", "任务卡", "📋", items)


def _readiness_section_html(readiness_data: Any) -> str:
    """Render merge readiness."""
    if not readiness_data:
        return ""

    if hasattr(readiness_data, "to_dict"):
        readiness_data = readiness_data.to_dict()
    elif not isinstance(readiness_data, dict):
        return ""

    state = readiness_data.get("state", "unknown")
    state_icon = readiness_data.get("state_icon", "❓")
    state_label = readiness_data.get("state_label", "未知")
    summary = readiness_data.get("summary", "")
    blocking_issues = readiness_data.get("blocking_issues", [])
    review_required = readiness_data.get("review_required", False)
    pending_cards = readiness_data.get("pending_cards", 0)
    high_risk_count = readiness_data.get("high_risk_count", 0)

    body = _readiness_card_html(state, state_icon, state_label, summary, blocking_issues)
    body += f"""<div class="grid-3" style="margin-top:12px">
  {_stat_card_html('需要审查' if review_required else '无需审查', '审查要求', 'var(--accent-orange)' if review_required else 'var(--accent-green)')}
  {_stat_card_html(str(pending_cards), '待处理卡', 'var(--accent-orange)' if pending_cards > 0 else 'var(--accent-green)')}
  {_stat_card_html(str(high_risk_count), '高风险文件', 'var(--accent-red)' if high_risk_count > 0 else 'var(--accent-green)')}
</div>"""

    return _section_html("readiness", "合并就绪度", "🔀", body)


def _evidence_section_html(evidence_data: Any) -> str:
    """Render evidence pack."""
    if not evidence_data:
        return ""

    if hasattr(evidence_data, "to_dict"):
        evidence_data = evidence_data.to_dict()
    elif not isinstance(evidence_data, dict):
        return ""

    pack_id = evidence_data.get("pack_id", "unknown")
    total = evidence_data.get("total", 0)
    passed = evidence_data.get("passed", 0)
    failed = evidence_data.get("failed", 0)
    integrity_hash = evidence_data.get("integrity_hash", "")

    body = f"""<div class="evidence-grid">
  <div class="evidence-stat"><div class="ev-value">{total}</div><div class="ev-label">总计</div></div>
  <div class="evidence-stat pass"><div class="ev-value">{passed}</div><div class="ev-label">通过</div></div>
  <div class="evidence-stat fail"><div class="ev-value">{failed}</div><div class="ev-label">失败</div></div>
  <div class="evidence-stat"><div class="ev-value" style="font-size:14px;word-break:break-all">{_escape_html(integrity_hash[:16])}...</div><div class="ev-label">SHA256</div></div>
</div>
<div style="margin-top:12px;font-size:12px;color:var(--text-muted)">
  <code>Pack: {_escape_html(pack_id)}</code>
</div>"""

    return _section_html("evidence", "证据包", "🔐", body)


def _agent_state_section_html(agent_state_data: Any) -> str:
    """Render agent lifecycle state section."""
    if not agent_state_data:
        return ""
    if hasattr(agent_state_data, "to_dict"):
        agent_state_data = agent_state_data.to_dict()
    elif not isinstance(agent_state_data, dict):
        return ""

    state = agent_state_data.get("state", "idle")
    confidence = agent_state_data.get("confidence", 0.0)
    summary = agent_state_data.get("summary", "")
    severity = agent_state_data.get("severity", "low")
    blocking = agent_state_data.get("blocking", False)
    source_events = agent_state_data.get("source_events", [])
    recommended_action = agent_state_data.get("recommended_action", "")

    icon_map = {
        "idle": "💤", "planning": "📋", "implementing": "🔧",
        "testing": "🧪", "repairing": "🔨", "reviewing": "👁️",
        "waiting_for_user": "⏳", "completed": "✅", "failed": "❌", "blocked": "🚫",
    }
    icon = icon_map.get(state, "❓")
    blocking_text = "是 🚫" if blocking else "否 ✅"
    events_text = ", ".join(source_events[:5]) if source_events else "—"
    action_text = _escape_html(recommended_action) if recommended_action else "—"

    body = f"""<div class="agent-state-card">
  <div class="as-header">
    <span class="as-icon">{icon}</span>
    <span class="as-state-name">{_escape_html(state.upper())}</span>
    <span class="as-severity severity-{_escape_html(severity)}">{_escape_html(severity.upper())}</span>
  </div>
  <div class="as-summary">{_escape_html(summary)}</div>
  <div class="as-details">
    <div class="detail-row"><span class="detail-label">置信度</span><span class="detail-value">{confidence:.0%}</span></div>
    <div class="detail-row"><span class="detail-label">严重度</span><span class="detail-value">{_escape_html(severity)}</span></div>
    <div class="detail-row"><span class="detail-label">阻塞合并</span><span class="detail-value">{blocking_text}</span></div>
    <div class="detail-row"><span class="detail-label">触发事件</span><span class="detail-value">{_escape_html(events_text)}</span></div>
    <div class="detail-row"><span class="detail-label">建议操作</span><span class="detail-value">{action_text}</span></div>
  </div>
</div>"""

    return _section_html("agent-state", "Agent 状态", "🤖", body)


def _companion_section_html(companion_data: Any) -> str:
    """Render waiting companion placeholder."""
    if not companion_data:
        return ""

    if hasattr(companion_data, "to_dict"):
        companion_data = companion_data.to_dict()
    elif not isinstance(companion_data, dict):
        return ""

    is_active = companion_data.get("is_active", False)
    status_text = companion_data.get("status_text", "等待中")
    mode = companion_data.get("mode", "idle")
    waiting_since = companion_data.get("waiting_since", "")

    status_class = "active" if is_active else "idle"
    extra = ""
    if waiting_since:
        extra = f'<p>开始: {_escape_html(waiting_since)}</p>'

    body = f"""<div class="companion-placeholder">
  <div class="companion-icon">⏳</div>
  <div>
    <span class="status-dot {status_class}"></span>
    <strong>{_escape_html(status_text)}</strong>
    <span style="color:var(--text-muted);font-size:13px;margin-left:8px">({_escape_html(mode)})</span>
  </div>
  <p>等待陪伴模式尚未接入音乐服务。当前仅显示 Agent / 项目状态提醒占位。</p>
  <p style="font-size:12px;color:var(--text-muted);margin-top:4px">仅占位 — 无音乐 API · 无音频播放 · 无凭据 · 无下载缓存</p>
  {extra}
</div>"""

    return _section_html("companion", "等待陪伴", "⏳", body)


def _loop_detail_section_html(loop_artifacts: Any) -> str:
    """Render loop run detail section (from-loop specific)."""
    if not loop_artifacts:
        return ""

    # Loop artifacts is a raw data object; extract summary
    run_dir = ""
    load_errors = []

    if hasattr(loop_artifacts, "run_dir"):
        run_dir = loop_artifacts.run_dir
    if hasattr(loop_artifacts, "load_errors"):
        load_errors = loop_artifacts.load_errors

    metrics_summary = ""
    if hasattr(loop_artifacts, "metrics"):
        m = loop_artifacts.metrics
        if m:
            if hasattr(m, "to_dict"):
                m = m.to_dict()
            if isinstance(m, dict):
                metrics_summary = " | ".join(f"{k}: {v}" for k, v in list(m.items())[:6])

    errors_text = ""
    if load_errors:
        items = "".join(f'<div class="issue-item">⚠ {_escape_html(str(e))}</div>' for e in load_errors)
        errors_text = f'<div style="margin-top:8px"><strong>加载错误:</strong>{items}</div>'

    # Check what artifacts were loaded
    artifact_keys = []
    if hasattr(loop_artifacts, "to_dict"):
        ad = loop_artifacts.to_dict()
        artifact_keys = [k for k, v in ad.items() if v is not None and k != "load_errors"]
    elif isinstance(loop_artifacts, dict):
        artifact_keys = [k for k, v in loop_artifacts.items() if v is not None and k != "load_errors"]

    body = f"""<div class="detail-row"><div class="detail-label">运行目录</div><div class="detail-value"><code>{_escape_html(run_dir)}</code></div></div>
<div class="detail-row"><div class="detail-label">已加载 Artifacts</div><div class="detail-value">{_escape_html(", ".join(artifact_keys[:10])) if artifact_keys else "无"}</div></div>
<div class="detail-row"><div class="detail-label">Metrics</div><div class="detail-value">{_escape_html(metrics_summary) if metrics_summary else "无"}</div></div>
<div class="detail-row"><div class="detail-label">加载错误</div><div class="detail-value">{str(len(load_errors))}</div></div>
{errors_text}"""

    return _section_html("loop-detail", "Loop 运行详情", "🔄", body)


def _tab_nav_html(sections: List[str]) -> str:
    """Render tab navigation."""
    icons = {
        "overview": "📊",
        "agent-state": "🤖",
        "modules": "🧩",
        "changes": "📝",
        "suggestions": "💡",
        "task-cards": "📋",
        "readiness": "🔀",
        "evidence": "🔐",
        "loop-detail": "🔄",
        "companion": "⏳",
    }
    labels = {
        "overview": "概览",
        "agent-state": "Agent状态",
        "modules": "模块",
        "changes": "变更",
        "suggestions": "建议",
        "task-cards": "任务卡",
        "readiness": "合并就绪",
        "evidence": "证据",
        "loop-detail": "Loop详情",
        "companion": "等待陪伴",
    }

    buttons = ""
    for sid in sections:
        icon = icons.get(sid, "📌")
        label = labels.get(sid, sid)
        active = 'active' if sid == sections[0] else ''
        buttons += f'<button class="tab-btn {active}" data-tab="{sid}">{icon} {label}</button>'

    return f'<div class="tabs">{buttons}</div>'


def _tab_script_html(sections: List[str]) -> str:
    """Render JavaScript for tab switching."""
    return """<script>
(function() {
  var btns = document.querySelectorAll('.tab-btn');
  btns.forEach(function(btn) {
    btn.addEventListener('click', function() {
      btns.forEach(function(b) { b.classList.remove('active'); });
      document.querySelectorAll('.tab-content').forEach(function(t) { t.classList.remove('active'); });
      btn.classList.add('active');
      var tab = document.getElementById('tab-' + btn.getAttribute('data-tab'));
      if (tab) tab.classList.add('active');
    });
  });
  // Copy button handler
  document.querySelectorAll('.copy-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var target = document.getElementById(btn.getAttribute('data-target'));
      if (target) {
        var text = target.textContent;
        navigator.clipboard.writeText(text).then(function() {
          btn.textContent = '已复制!';
          setTimeout(function() { btn.textContent = '复制'; }, 2000);
        });
      }
    });
  });
})();
</script>"""


def _data_json_script(data: Dict[str, Any]) -> str:
    """Embed full JSON data for programmatic consumption."""
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        escaped = json_str.replace("</script>", "<\\/script>").replace("<!--", "<\\!--")
        return f"""<script id="dashboard-data" type="application/json">
{escaped}
</script>"""
    except (TypeError, ValueError):
        return ""


# ==============================================================================
# Public API
# ==============================================================================

def render_html_dashboard(
    dashboard_state: Dict[str, Any],
    title: str = "Harness Code Copilot Dashboard",
) -> str:
    """Render a complete self-contained HTML dashboard page.

    Args:
        dashboard_state: dict from CopilotDashboardState.to_dict()
        title: Page title.

    Returns:
        Complete HTML string with embedded CSS and JS.
    """
    sections_order = [
        "overview", "agent-state", "modules", "changes", "suggestions",
        "task-cards", "readiness", "evidence", "companion",
    ]
    return _build_html(dashboard_state, title, sections_order)


def render_loop_html_dashboard(
    dashboard_state: Dict[str, Any],
    loop_artifacts: Any = None,
    title: str = "Harness Code Copilot — Loop Run Dashboard",
) -> str:
    """Render a loop artifact dashboard with extra loop detail section.

    Args:
        dashboard_state: dict from CopilotDashboardState.to_dict()
        loop_artifacts: Raw LoopArtifacts object (optional, for detail section).
        title: Page title.

    Returns:
        Complete HTML string with embedded CSS and JS.
    """
    sections_order = [
        "overview", "agent-state", "loop-detail", "modules", "changes",
        "task-cards", "readiness", "evidence", "companion",
    ]
    return _build_html(dashboard_state, title, sections_order, loop_artifacts=loop_artifacts)


def _build_html(
    dashboard_state: Dict[str, Any],
    title: str,
    sections_order: List[str],
    loop_artifacts: Any = None,
) -> str:
    """Build the full HTML document."""
    # Render each section
    sections_html = {}
    overview_body = _project_home_html(dashboard_state) + _overview_stats_html(dashboard_state)
    if dashboard_state.get("readiness"):
        overview_body += _readiness_card_html(
            dashboard_state["readiness"].get("state", "unknown"),
            dashboard_state["readiness"].get("state_icon", "❓"),
            dashboard_state["readiness"].get("state_label", "未知"),
            dashboard_state["readiness"].get("summary", ""),
            dashboard_state["readiness"].get("blocking_issues", []),
        )

    sections_html["overview"] = f'<div class="section">{overview_body}</div>'
    sections_html["modules"] = _modules_section_html(dashboard_state.get("modules", []))
    sections_html["changes"] = _changes_section_html(dashboard_state.get("recent_changes", []))
    sections_html["suggestions"] = _suggestions_section_html(dashboard_state.get("suggestions"))
    sections_html["task-cards"] = _task_cards_section_html(dashboard_state.get("task_cards"))
    sections_html["readiness"] = _readiness_section_html(dashboard_state.get("readiness"))
    sections_html["evidence"] = _evidence_section_html(dashboard_state.get("evidence"))
    sections_html["companion"] = _companion_section_html(dashboard_state.get("companion"))

    if dashboard_state.get("agent_state"):
        sections_html["agent-state"] = _agent_state_section_html(dashboard_state.get("agent_state"))
    else:
        sections_html["agent-state"] = ""

    if loop_artifacts:
        sections_html["loop-detail"] = _loop_detail_section_html(loop_artifacts)
    else:
        sections_html["loop-detail"] = ""

    # Build tab content
    tab_contents = ""
    for sid in sections_order:
        html = sections_html.get(sid, "")
        active = " active" if sid == sections_order[0] else ""
        tab_contents += f'<div id="tab-{sid}" class="tab-content{active}">\n{html}\n</div>\n'

    # Navigation (only sections with content)
    active_sections = [s for s in sections_order if sections_html.get(s, "").strip()]
    tab_nav = _tab_nav_html(active_sections)
    tab_script = _tab_script_html(active_sections)
    data_json = _data_json_script(dashboard_state)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_escape_html(title)}</title>
<style>
{DASHBOARD_CSS}
</style>
</head>
<body>
<div class="container">

{tab_nav}
{tab_contents}

{data_json}

</div>
<div class="footer">
Harness Code Copilot — Read-only Local Dashboard &middot; 无外部服务 &middot; 无自动修改 &middot; 仅供查看
</div>
{tab_script}
</body>
</html>"""
