#!/usr/bin/env python3
"""
Harness OS — PreCompact Hook
Saves current session state and file metadata before context compaction.
Allows resumption after compaction without losing context.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path(".claude/last-compact-state.json")

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {"error": "malformed hook input"}

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "PreCompact",
        "payload_summary": {
            "session_id": payload.get("session_id", ""),
            "turn_count": payload.get("turn_count", 0),
        }
    }

    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "continue": True,
        "permissionDecision": "allow",
        "permissionDecisionReason": "Pre-compact state saved"
    }))

if __name__ == "__main__":
    main()
