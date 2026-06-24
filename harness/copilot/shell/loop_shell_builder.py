"""Loop Shell Builder — builds static HTML dashboard from loop artifact run directory.

Consumes Phase 3 Integration Layer output to render a loop-specific dashboard.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .html_renderer import render_loop_html_dashboard


def build_loop_shell(
    loop_run_dir: str,
    output_dir: str,
    title: str = "Harness Code Copilot — Loop Run Dashboard",
) -> Dict[str, Any]:
    """Build a static HTML dashboard from a Hermes Loop run directory.

    Args:
        loop_run_dir: Path to loop run directory (contains loop_report.md, etc.)
        output_dir: Output directory for generated files.
        title: Dashboard page title.

    Returns:
        dict with keys: html_path, json_path, success, error (optional)
    """
    result: Dict[str, Any] = {"success": False}

    # Resolve paths
    run_dir = os.path.abspath(loop_run_dir)
    if not os.path.isdir(run_dir):
        result["error"] = f"Loop run directory '{run_dir}' not found"
        return result

    out_dir = os.path.abspath(output_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Load loop artifacts via integration layer
    try:
        from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
        from harness.copilot.integration.loop_to_copilot_mapper import artifacts_to_dashboard

        artifacts = load_loop_artifacts(run_dir)
        dashboard = artifacts_to_dashboard(artifacts)
    except Exception as e:
        result["error"] = f"Failed to load loop artifacts: {e}"
        return result

    # Generate HTML
    try:
        dashboard_dict = dashboard.to_dict()
        html = render_loop_html_dashboard(dashboard_dict, loop_artifacts=artifacts, title=title)
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

    # Write JSON data
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
