"""Harness Code Copilot — Live Event Stream Core (Phase 8A).

Local-only event bus + SSE server for live dashboard data.
Read-only. No external API. No agent control.

Modules:
  live_event.py     — LiveEvent schema
  event_bus.py      — In-process pub/sub event bus
  project_stream.py — Project live stream adapter
  loop_stream.py    — Loop live stream adapter
  sse_server.py     — Local-only HTTP/SSE server skeleton
  renderer.py       — LiveEvent to JSON rendering
  live_dashboard.py — Live dashboard orchestrator
  live_html_renderer.py — Live dashboard HTML template
  static_live_assets.py — Live dashboard CSS and JS assets
"""
