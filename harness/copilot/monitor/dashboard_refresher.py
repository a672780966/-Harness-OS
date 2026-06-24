"""Dashboard Refresher — optionally regenerate HTML dashboard from monitor events.

Only writes to the --out directory specified by the user.
No writes to project source code, sealed evidence, or git-tracked files.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, Optional

from . import MonitorEvent, MonitorSession


def refresh_dashboard(
    output_dir: str,
    session: MonitorSession,
    project_root: str = "",
    loop_run_dir: str = "",
) -> Dict[str, Any]:
    """Regenerate or update dashboard files with latest monitor state.

    Args:
        output_dir: Dashboard output directory (must exist or be created).
        session: Current monitor session with accumulated events.
        project_root: Project path (for project-based dashboards).
        loop_run_dir: Loop run path (for loop-based dashboards).

    Returns:
        dict with success status and file paths.
    """
    result: Dict[str, Any] = {"success": False}

    out_dir = os.path.abspath(output_dir)
    os.makedirs(out_dir, exist_ok=True)

    # Build monitor state dict
    monitor_state = {
        "monitor_version": "1.0",
        "project_root": project_root,
        "loop_run_dir": loop_run_dir,
        "total_events": len(session.events),
        "event_summary": dict(session.accumulated_summary),
        "latest_events": [e.to_dict() for e in session.latest_events(20)],
    }

    # Write monitor state JSON
    state_path = os.path.join(out_dir, "monitor_state.json")
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(monitor_state, f, indent=2, ensure_ascii=False, default=str)
    except (IOError, TypeError) as e:
        result["error"] = f"Failed to write monitor state: {e}"
        return result

    # Optionally write events log
    events_path = os.path.join(out_dir, "monitor_events.json")
    try:
        with open(events_path, "w", encoding="utf-8") as f:
            json.dump(
                [e.to_dict() for e in session.events],
                f, indent=2, ensure_ascii=False, default=str,
            )
    except (IOError, TypeError) as e:
        result["error"] = f"Failed to write events log: {e}"
        return result

    # If a dashboard already exists, update its embedded JSON data
    index_path = os.path.join(out_dir, "index.html")
    if os.path.isfile(index_path):
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                html = f.read()

            # Replace the dashboard-data script content
            pattern = r'<script id="dashboard-data" type="application/json">\s*.*?\s*</script>'
            new_data = json.dumps(monitor_state, indent=2, ensure_ascii=False)
            replacement = f'<script id="dashboard-data" type="application/json">\n{new_data}\n</script>'
            updated_html = re.sub(pattern, replacement, html, flags=re.DOTALL)

            if updated_html != html:
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(updated_html)
        except (IOError, OSError, re.error) as e:
            result["warning"] = f"Failed to update index.html: {e}"

    result["success"] = True
    result["state_path"] = state_path
    result["events_path"] = events_path
    result["output_dir"] = out_dir
    return result
