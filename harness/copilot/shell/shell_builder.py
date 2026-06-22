"""Shell Builder — builds static HTML dashboard from a project path.

Read-only: scans project, builds CopilotDashboardState, renders to HTML.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .html_renderer import render_html_dashboard


def build_project_shell(
    project_path: str,
    output_dir: str,
    diff_ref: str = "HEAD~1",
    title: str = "Harness Code Copilot Dashboard",
) -> Dict[str, Any]:
    """Build a complete static HTML dashboard for a project.

    Args:
        project_path: Path to project root.
        output_dir: Output directory for generated files.
        diff_ref: Git diff base ref.
        title: Dashboard page title.

    Returns:
        dict with keys: html_path, json_path, success, error (optional)
    """
    result: Dict[str, Any] = {"success": False}

    # Resolve paths
    project_root = os.path.abspath(project_path)
    if not os.path.isdir(project_root):
        result["error"] = f"Project path '{project_root}' is not a directory"
        return result

    out_dir = os.path.abspath(output_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Build dashboard state
    try:
        from harness.copilot.view_models import build_dashboard
        dashboard = build_dashboard(project_root, diff_ref=diff_ref)
    except Exception as e:
        result["error"] = f"Failed to build dashboard: {e}"
        return result

    # Generate HTML
    try:
        dashboard_dict = dashboard.to_dict()
        html = render_html_dashboard(dashboard_dict, title=title)
    except Exception as e:
        result["error"] = f"Failed to render HTML: {e}"
        return result

    # Write HTML
    html_path = os.path.join(out_dir, "index.html")
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
    except IOError as e:
        result["error"] = f"Failed to write HTML: {e}"
        return result

    # Write JSON data alongside
    json_path = os.path.join(out_dir, "dashboard.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dashboard_dict, f, indent=2, ensure_ascii=False, default=str)
    except (IOError, TypeError) as e:
        result["error"] = f"Failed to write JSON: {e}"
        return result

    result["success"] = True
    result["html_path"] = html_path
    result["json_path"] = json_path
    result["output_dir"] = out_dir
    result["dashboard"] = dashboard_dict
    return result
