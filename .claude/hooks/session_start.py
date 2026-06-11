#!/usr/bin/env python3
"""
Harness OS — SessionStart Hook
Loads previous session context and detects project state on new session.
Checks for active tasks, pending approvals, and uncommitted changes.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LAST_COMPACT = Path(".claude/last-compact-state.json")
LAST_SESSION = Path(".claude/last-session-state.json")

def get_git_status():
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5, cwd="."
        )
        return result.stdout.strip() or "(clean)"
    except Exception:
        return "(unknown)"

def get_active_tasks():
    tasks_dir = Path(".project/tasks/active")
    if tasks_dir.exists():
        tasks = list(tasks_dir.glob("*.json"))
        return [t.stem for t in tasks]
    return []

def get_pending_approvals():
    approvals_dir = Path(".project/reports/approvals")
    if approvals_dir.exists():
        pending = []
        for f in approvals_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                if data.get("status") == "pending":
                    pending.append(f.stem)
            except Exception:
                pass
        return pending
    return []

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    session_info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "SessionStart",
        "project_state": {
            "git_status": get_git_status(),
            "active_tasks": get_active_tasks(),
            "pending_approvals": get_pending_approvals(),
        },
        "previous_state": None,
    }

    # Load previous session state if available
    if LAST_COMPACT.exists():
        try:
            session_info["previous_state"] = json.loads(LAST_COMPACT.read_text())
        except Exception:
            pass

    # Save current session state
    Path(".claude").mkdir(parents=True, exist_ok=True)
    with open(".claude/current-session-state.json", "w", encoding="utf-8") as f:
        json.dump(session_info, f, ensure_ascii=False, indent=2)

    # Build output message with context summary
    active = session_info["project_state"]["active_tasks"]
    pending = session_info["project_state"]["pending_approvals"]

    notes = []
    if active:
        notes.append(f"Active tasks: {', '.join(active)}")
    if pending:
        notes.append(f"Pending approvals: {', '.join(pending)}")
    if session_info["previous_state"]:
        notes.append("Previous session state found — session is resumable")

    context_summary = "; ".join(notes) if notes else "Clean session start"

    print(json.dumps({
        "continue": True,
        "permissionDecision": "allow",
        "permissionDecisionReason": f"Session context loaded: {context_summary}",
        "context_summary": context_summary,
    }))

if __name__ == "__main__":
    main()
