"""Static CSS and JS assets for the live dashboard HTML page.

Single embedded stylesheet. No external dependencies.
"""
LIVE_DASHBOARD_CSS = """/* Harness Copilot Live Dashboard — Dark Theme */
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
  --card-bg: #1c2128;
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

.header {
  padding: 24px 0 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.header h1 { font-size: 24px; font-weight: 600; }
.header-badges { display: flex; gap: 8px; flex-wrap: wrap; }
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.badge-local { background: #1b362a; color: var(--accent-green); border: 1px solid #2d6a3f; }
.badge-readonly { background: #1b2d3b; color: var(--accent-blue); border: 1px solid #1f5480; }
.badge-live { background: #3b2e0f; color: var(--accent-orange); border: 1px solid #6b5516; animation: pulse 2s infinite; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
@media (max-width: 768px) { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  min-height: 80px;
}
.card-header {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.card-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

/* Agent State Card */
.agent-state-card .as-main {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}
.agent-state-card .as-icon { font-size: 40px; }
.agent-state-card .as-text { font-size: 16px; font-weight: 500; }
.agent-state-card .as-severity {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.as-severity.low { background: #1b362a; color: var(--accent-green); }
.as-severity.medium { background: #3b2e0f; color: var(--accent-orange); }
.as-severity.high { background: #3b1a18; color: var(--accent-red); }
.as-severity.critical { background: #4a0f0d; color: #ff7777; }

/* Readiness Card */
.readiness-card .rc-value { font-size: 22px; font-weight: 700; }
.readiness-card.pass .rc-value { color: var(--accent-green); }
.readiness-card.block .rc-value { color: var(--accent-red); }
.readiness-card.review_needed .rc-value { color: var(--accent-orange); }

/* Risk Level */
.risk-level.low { color: var(--accent-green); }
.risk-level.medium { color: var(--accent-orange); }
.risk-level.high, .risk-level.critical { color: var(--accent-red); }

/* Blocking status */
.blocking-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
}
.blocking-badge.blocked { background: #3b1a18; color: var(--accent-red); }
.blocking-badge.ok { background: #1b362a; color: var(--accent-green); }

/* Event Timeline */
.timeline {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 6px;
}
.timeline-item {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.timeline-item:last-child { border-bottom: none; }
.timeline-item .tl-time {
  color: var(--text-muted);
  flex-shrink: 0;
  min-width: 70px;
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 11px;
}
.timeline-item .tl-icon { flex-shrink: 0; }
.timeline-item .tl-text { flex: 1; word-break: break-word; }
.timeline-item.blocking { background: #3b1a1822; }
.timeline-item:hover { background: var(--bg-tertiary); }

/* Timestamp */
.timestamp {
  font-size: 12px;
  color: var(--text-muted);
  text-align: right;
  padding: 8px 0;
}

/* Connection status */
.conn-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.conn-status.connected { background: #1b362a; color: var(--accent-green); }
.conn-status.disconnected { background: #3b1a18; color: var(--accent-red); }
.conn-status .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.conn-status.connected .dot { background: var(--accent-green); }
.conn-status.disconnected .dot { background: var(--accent-red); }

/* Recommended Action */
.action-box {
  padding: 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 14px;
  border-left: 4px solid var(--accent-blue);
}

/* Stat cards */
.stat-card {
  background: var(--bg-tertiary);
  border-radius: 6px;
  padding: 16px;
  text-align: center;
}
.stat-card .value { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
.stat-card .label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; }

/* Scrollbar */
.timeline::-webkit-scrollbar { width: 6px; }
.timeline::-webkit-scrollbar-track { background: var(--bg-secondary); }
.timeline::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Footer */
.footer {
  text-align: center;
  padding: 24px;
  color: var(--text-muted);
  font-size: 12px;
  border-top: 1px solid var(--border);
  margin-top: 24px;
}
"""

LIVE_DASHBOARD_JS = """
(function() {
  var container = document.getElementById('live-events');
  var counter = document.getElementById('event-count');
  var connStatus = document.getElementById('conn-status');
  var lastUpdated = document.getElementById('last-updated');
  var count = 0;

  function updateTime() {
    if (lastUpdated) {
      lastUpdated.textContent = new Date().toISOString().slice(11, 19);
    }
    if (counter) counter.textContent = count;
  }

  function renderEvent(evt) {
    var item = document.createElement('div');
    item.className = 'timeline-item';
    if (evt.blocking) item.classList.add('blocking');

    var ts = (evt.timestamp || '').slice(11, 19) || '';
    var timeDiv = document.createElement('div');
    timeDiv.className = 'tl-time';
    timeDiv.textContent = ts;

    var icons = {
      'project_state_update': '📡',
      'loop_state_update': '🔄',
      'project_error': '❌',
      'loop_error': '❌'
    };
    var iconSpan = document.createElement('span');
    iconSpan.className = 'tl-icon';
    iconSpan.textContent = icons[evt.event_type] || '📌';

    var textSpan = document.createElement('span');
    textSpan.className = 'tl-text';
    textSpan.textContent = evt.summary || evt.event_type;

    item.appendChild(timeDiv);
    item.appendChild(iconSpan);
    item.appendChild(textSpan);
    container.appendChild(item);
    container.scrollTop = container.scrollHeight;

    count++;
    updateTime();
  }

  function trySSE() {
    var es = null;
    try {
      es = new EventSource('/events');
    } catch(e) { return false; }

    es.onopen = function() {
      if (connStatus) {
        connStatus.className = 'conn-status connected';
        connStatus.innerHTML = '<span class="dot"></span> 已连接';
      }
    };

    es.onmessage = function(e) {
      try {
        var evt = JSON.parse(e.data);
        renderEvent(evt);
      } catch(err) {}
    };

    es.onerror = function() {
      if (connStatus) {
        connStatus.className = 'conn-status disconnected';
        connStatus.innerHTML = '<span class="dot"></span> 已断开';
      }
      es.close();
    };
    return true;
  }

  function tryFetch() {
    fetch('/latest')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.events) {
          data.events.forEach(function(evt) { renderEvent(evt); });
        }
      })
      .catch(function() {});
  }

  // Attempt SSE; fallback to polling
  if (!trySSE()) {
    tryFetch();
    setInterval(tryFetch, 5000);
  }

  // Update dashboard-state.json data
  function refreshState() {
    fetch('/latest?count=1')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.events && data.events.length > 0) {
          var latest = data.events[data.events.length - 1];
          updateCards(latest);
        }
      })
      .catch(function() {});
  }

  function updateCards(evt) {
    if (!evt) return;
    var as = evt.agent_state || {};
    var mr = evt.merge_readiness || {};

    var stateEl = document.getElementById('as-state');
    var severityEl = document.getElementById('as-severity');
    if (stateEl && as.summary) stateEl.textContent = as.summary;
    if (severityEl && as.severity) {
      severityEl.textContent = as.severity.toUpperCase();
      severityEl.className = 'as-severity ' + as.severity;
    }

    var mrStateEl = document.getElementById('mr-state');
    var mrIconEl = document.getElementById('mr-icon');
    if (mrStateEl && mr.state_label) mrStateEl.textContent = mr.state_label;
    if (mrIconEl && mr.state_icon) mrIconEl.textContent = mr.state_icon;

    var blockingEl = document.getElementById('blocking-status');
    if (blockingEl) {
      if (evt.blocking) {
        blockingEl.className = 'blocking-badge blocked';
        blockingEl.textContent = '🚫 已阻塞';
      } else {
        blockingEl.className = 'blocking-badge ok';
        blockingEl.textContent = '✅ 正常';
      }
    }

    var riskEl = document.getElementById('risk-level');
    if (riskEl && evt.risk_level) {
      riskEl.textContent = evt.risk_level.toUpperCase();
      riskEl.className = 'risk-level ' + evt.risk_level;
    }

    var actionEl = document.getElementById('recommended-action');
    if (actionEl) {
      actionEl.textContent = evt.recommended_action || '无待处理操作';
    }
  }

  // Initial poll after 1 second
  setTimeout(function() {
    refreshState();
    setInterval(refreshState, 3000);
  }, 1000);
})();
"""
