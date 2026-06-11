#!/usr/bin/env python3
"""
Harness OS — SessionEnd Hook
Persists session state for resumption and cleanup.
Records task progress, pending work, and session summary.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SESSION_FILE = Path(".claude/last-session-state.json")

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "SessionEnd",
        "session_id": payload.get("session_id", ""),
        "turn_count": payload.get("turn_count", 0),
        "status": payload.get("status", "completed"),
        "tool_call_count": payload.get("tool_call_count", 0),
        "summary": "Session completed and state saved for resume",
    }

    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "continue": True,
        "permissionDecision": "allow",
        "permissionDecisionReason": "Session state persisted"
    }))

if __name__ == "__main__":
    main()
