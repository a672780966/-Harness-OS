"""Harness Code Copilot — Local HTML MVP Shell.

Phase 4: Read-only static HTML dashboard for project and loop artifacts.
No external services, no agent control, no code modification.
"""

from __future__ import annotations

from .html_renderer import render_html_dashboard, render_loop_html_dashboard
from .shell_builder import build_project_shell
from .loop_shell_builder import build_loop_shell
from .copy_text_renderer import export_task_card_markdown, render_task_card_copy_text
from .preview_server import serve_preview

__all__ = [
    "render_html_dashboard",
    "render_loop_html_dashboard",
    "build_project_shell",
    "build_loop_shell",
    "export_task_card_markdown",
    "render_task_card_copy_text",
    "serve_preview",
]
