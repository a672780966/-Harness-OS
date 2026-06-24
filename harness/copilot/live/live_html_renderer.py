"""Live HTML Renderer — render live dashboard as self-contained HTML page.

Produces a single-page static HTML file with embedded CSS, JS, and SSE client.
No external dependencies. Local-only.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .static_live_assets import LIVE_DASHBOARD_CSS, LIVE_DASHBOARD_JS


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_live_dashboard(
    initial_state: Dict[str, Any],
    title: str = "Harness Copilot — Live Dashboard",
) -> str:
    """Render a complete self-contained live dashboard HTML page.

    Args:
        initial_state: Dict with keys: project_name, branch, agent_state,
                      merge_readiness, events (list of LiveEvent dicts).
        title: Page title.

    Returns:
        Complete HTML string with embedded CSS and JS.
    """
    project_name = _escape_html(initial_state.get("project_name", "Unknown"))
    branch = _escape_html(initial_state.get("branch", "unknown"))
    generated_at = _escape_html(initial_state.get("generated_at", ""))

    # Initial agent state
    agent_state = initial_state.get("agent_state", {})
    as_state = _escape_html(agent_state.get("summary", "待命"))
    as_severity = agent_state.get("severity", "low")
    icon_map = {
        "idle": "💤", "planning": "📋", "implementing": "🔧",
        "testing": "🧪", "repairing": "🔨", "reviewing": "👁️",
        "waiting_for_user": "⏳", "completed": "✅", "failed": "❌", "blocked": "🚫",
    }
    as_icon = icon_map.get(agent_state.get("state", ""), "❓")

    # Initial merge readiness
    readiness = initial_state.get("merge_readiness", {})
    mr_state = _escape_html(readiness.get("state_label", "未知"))
    mr_icon = readiness.get("state_icon", "❓")
    mr_class = readiness.get("state", "unknown")

    # Risk level
    risk_level = initial_state.get("risk_level", "low")

    # Blocking
    blocking = initial_state.get("blocking", False)

    # Recommended action
    recommended_action = _escape_html(initial_state.get("recommended_action", "")) or "无待处理操作"

    # Initial events JSON for fallback
    initial_events = initial_state.get("events", [])
    events_json = json.dumps(initial_events, ensure_ascii=False, default=str)
    dashboard_data = json.dumps(initial_state, indent=2, ensure_ascii=False, default=str)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_escape_html(title)}</title>
<style>
{LIVE_DASHBOARD_CSS}
</style>
</head>
<body>
<div class="container">

<!-- Header -->
<div class="header">
  <div>
    <h1>📡 {_escape_html(project_name)}</h1>
    <div style="font-size:13px;color:var(--text-muted);margin-top:4px">
      🔀 <code>{branch}</code>
    </div>
  </div>
  <div class="header-badges">
    <span class="badge badge-local">🏠 Local</span>
    <span class="badge badge-readonly">🔒 Read-only</span>
    <span class="badge badge-live" id="live-badge">🔴 Live</span>
  </div>
</div>

<!-- Status Grid -->
<div class="grid-4" style="margin-bottom:20px">

  <!-- Agent State -->
  <div class="card agent-state-card">
    <div class="card-header">🤖 Agent 状态</div>
    <div class="as-main">
      <div class="as-icon">{as_icon}</div>
      <div>
        <div class="as-text" id="as-state">{as_state}</div>
        <span class="as-severity {as_severity}" id="as-severity">{as_severity.upper()}</span>
      </div>
    </div>
  </div>

  <!-- Merge Readiness -->
  <div class="card readiness-card {mr_class}">
    <div class="card-header">🔀 合并就绪度</div>
    <div>
      <span id="mr-icon" style="font-size:24px">{mr_icon}</span>
      <span class="rc-value" id="mr-state">{mr_state}</span>
    </div>
  </div>

  <!-- Risk Level -->
  <div class="card">
    <div class="card-header">⚠️ 风险等级</div>
    <div class="risk-level {risk_level}" id="risk-level" style="font-size:28px;font-weight:700">
      {risk_level.upper()}
    </div>
  </div>

  <!-- Blocking Status -->
  <div class="card">
    <div class="card-header">🚫 阻塞状态</div>
    <div>
      <span class="blocking-badge {'blocked' if blocking else 'ok'}" id="blocking-status">
        {'🚫 已阻塞' if blocking else '✅ 正常'}
      </span>
    </div>
  </div>

</div>

<!-- Recommended Action & Connection Status -->
<div class="grid-2" style="margin-bottom:20px">
  <div class="card">
    <div class="card-header">💡 建议操作</div>
    <div class="action-box" id="recommended-action">{recommended_action}</div>
  </div>
  <div class="card">
    <div class="card-header">📡 连接状态</div>
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      <span class="conn-status disconnected" id="conn-status">
        <span class="dot"></span> 连接中...
      </span>
      <span style="font-size:12px;color:var(--text-muted)">
        事件数: <strong id="event-count">{len(initial_events)}</strong>
      </span>
    </div>
  </div>
</div>

<!-- Event Timeline -->
<div class="card" style="margin-bottom:20px">
  <div class="card-header">📋 Live Event Timeline</div>
  <div class="timeline" id="live-events">
    <div id="no-events" style="padding:16px;color:var(--text-muted);text-align:center">
      等待事件...
    </div>
  </div>
  <div class="timestamp">
    Last updated: <span id="last-updated">{generated_at[11:19] if len(generated_at) >= 19 else '--:--:--'}</span>
  </div>
</div>

<!-- Footer -->
<div class="footer">
  Harness Copilot — Live Dashboard &middot; Local-only &middot; Read-only &middot; 无外部服务 &middot; 无 Agent 控制
</div>

<!-- Embedded data -->
<script id="dashboard-data" type="application/json">
{dashboard_data}
</script>

<!-- Initial events as fallback -->
<script id="initial-events" type="application/json">
{events_json}
</script>

<!-- Live dashboard JS -->
<script>
{LIVE_DASHBOARD_JS}
</script>

</div>
</body>
</html>"""
