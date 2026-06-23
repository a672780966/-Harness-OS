"""Static CSS assets for the local HTML dashboard.

Single embedded stylesheet; no external dependencies.
"""

DASHBOARD_CSS = """/* Harness Code Copilot Dashboard — Dark Theme */
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;
  --border: #30363d;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --text-muted: #6e7681;
  --accent-blue: #58a6ff;
  --accent-green: #3fb950;
  --accent-red: #f85149;
  --accent-orange: #d29922;
  --accent-purple: #bc8cff;
  --accent-cyan: #39d2c0;
  --pass-color: #3fb950;
  --block-color: #f85149;
  --review-color: #d29922;
  --code-bg: #1c2128;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  padding: 0;
}

.container { max-width: 1200px; margin: 0 auto; padding: 24px; }

/* Header */
.header {
  padding: 32px 0 24px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}

.header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.header .meta {
  color: var(--text-secondary);
  font-size: 14px;
}

.header .meta span { margin-right: 20px; }

/* Risk badges */
.risk-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}
.risk-badge.low { background: #1b362a; color: var(--accent-green); }
.risk-badge.medium { background: #3b2e0f; color: var(--accent-orange); }
.risk-badge.high, .risk-badge.critical { background: #3b1a18; color: var(--accent-red); }
.risk-badge.unknown { background: var(--bg-tertiary); color: var(--text-muted); }

/* Section */
.section {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
}

.section-header {
  padding: 16px 20px;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-body { padding: 16px 20px; }

/* Merge readiness card */
.readiness-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.readiness-card .icon { font-size: 36px; }
.readiness-card .status { font-size: 20px; font-weight: 600; }
.readiness-card .summary { font-size: 14px; color: var(--text-secondary); }

.readiness-card.pass { background: #1b362a; border: 1px solid #2d6a3f; }
.readiness-card.block { background: #3b1a18; border: 1px solid #6b2a26; }
.readiness-card.review_needed { background: #3b2e0f; border: 1px solid #6b5516; }

/* Issues list */
.issues-list { margin-top: 12px; }
.issue-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 14px;
  color: var(--accent-red);
}

/* Grids */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
@media (max-width: 768px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }

/* Stat cards */
.stat-card {
  background: var(--bg-tertiary);
  border-radius: 6px;
  padding: 16px;
  text-align: center;
}
.stat-card .value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}
.stat-card .label {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
}

/* Module card */
.module-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}
.module-card .module-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.module-card .module-details { font-size: 13px; color: var(--text-secondary); }
.module-card .module-details p { margin: 4px 0; }
.module-card .hr-files { margin-top: 8px; }
.module-card .hr-file {
  padding: 4px 8px;
  background: var(--bg-secondary);
  border-radius: 3px;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
  margin-bottom: 2px;
}

/* Change item */
.change-item {
  padding: 12px;
  border-bottom: 1px solid var(--border);
}
.change-item:last-child { border-bottom: none; }
.change-item .change-module {
  font-weight: 600;
  margin-bottom: 4px;
}
.change-item .change-summary { font-size: 14px; color: var(--text-secondary); }
.change-item .change-intent {
  display: inline-block;
  padding: 2px 6px;
  font-size: 11px;
  border-radius: 3px;
  background: var(--bg-tertiary);
  color: var(--accent-blue);
  margin-top: 4px;
}

/* Task card */
.task-card {
  background: var(--bg-tertiary);
  border-left: 4px solid var(--accent-blue);
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}
.task-card.blocking { border-left-color: var(--accent-red); }
.task-card .tc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}
.task-card .tc-title { font-size: 16px; font-weight: 600; }
.task-card .tc-type {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  background: var(--accent-blue);
  color: #fff;
}
.task-card.blocking .tc-type { background: var(--accent-red); }
.task-card .tc-desc { font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; }
.task-card .tc-meta { font-size: 12px; color: var(--text-muted); }
.task-card .tc-meta span { margin-right: 12px; }

/* Suggestion */
.suggestion-item {
  padding: 12px;
  border-bottom: 1px solid var(--border);
}
.suggestion-item:last-child { border-bottom: none; }
.suggestion-item .sugg-text { font-size: 14px; margin-bottom: 4px; }
.suggestion-item .sugg-reason { font-size: 13px; color: var(--text-secondary); }

/* Evidence */
.evidence-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.evidence-stat {
  text-align: center;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
}
.evidence-stat .ev-value { font-size: 24px; font-weight: 700; }
.evidence-stat .ev-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; }
.evidence-stat.pass .ev-value { color: var(--accent-green); }
.evidence-stat.fail .ev-value { color: var(--accent-red); }

/* Companion placeholder */
.companion-placeholder {
  text-align: center;
  padding: 32px;
  color: var(--text-muted);
}
.companion-placeholder .companion-icon { font-size: 48px; margin-bottom: 12px; }
.companion-placeholder p { font-size: 14px; margin-top: 8px; }

/* Code blocks */
code, pre {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12px;
}
pre {
  background: var(--code-bg);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Tab navigation */
.tabs {
  display: flex;
  gap: 4px;
  padding: 0 0 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.tab-btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s;
}
.tab-btn:hover { background: var(--bg-tertiary); color: var(--text-primary); }
.tab-btn.active {
  background: var(--accent-blue);
  color: #fff;
  border-color: var(--accent-blue);
}

.tab-content { display: none; }
.tab-content.active { display: block; }

/* Footer */
.footer {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  font-size: 12px;
  border-top: 1px solid var(--border);
  margin-top: 24px;
}

/* Copy button */
.copy-btn {
  float: right;
  padding: 4px 10px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
}
.copy-btn:hover { background: var(--accent-blue); color: #fff; }

/* Waiting status indicator */
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.active { background: var(--accent-green); animation: pulse 2s infinite; }
.status-dot.idle { background: var(--text-muted); }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Export box */
.export-box {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  margin-top: 8px;
}
.export-box pre {
  max-height: 200px;
  overflow-y: auto;
}

/* Detail label/value */
.detail-row {
  display: flex;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}
.detail-row:last-child { border-bottom: none; }
.detail-label {
  flex: 0 0 180px;
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 13px;
}
.detail-value { flex: 1; font-size: 13px; }

/* Agent State Card */
.agent-state-card {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 20px;
}
.agent-state-card .as-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.agent-state-card .as-icon { font-size: 32px; }
.agent-state-card .as-state-name {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}
.agent-state-card .as-severity {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}
.agent-state-card .as-severity.severity-low { background: #1b362a; color: var(--accent-green); }
.agent-state-card .as-severity.severity-medium { background: #3b2e0f; color: var(--accent-orange); }
.agent-state-card .as-severity.severity-high { background: #3b1a18; color: var(--accent-red); }
.agent-state-card .as-severity.severity-critical { background: #4a0f0d; color: #ff7777; }
.agent-state-card .as-summary {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
}
.agent-state-card .as-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 20px;
}
.agent-state-card .as-details .detail-row {
  display: flex;
  padding: 6px 0;
  border-bottom: none;
}
.agent-state-card .as-details .detail-label {
  flex: 0 0 80px;
  font-weight: 500;
  color: var(--text-muted);
  font-size: 12px;
}
.agent-state-card .as-details .detail-value {
  flex: 1;
  font-size: 13px;
}
@media (max-width: 600px) {
  .agent-state-card .as-details { grid-template-columns: 1fr; }
}
"""

__all__ = ["DASHBOARD_CSS"]
