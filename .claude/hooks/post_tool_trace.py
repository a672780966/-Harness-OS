#!/usr/bin/env python3
"""
Harness OS — PostToolUse Trace Hook

Records all tool calls to a JSONL trace file for observability.
Follows the Observability constraints from Harness OS CLAUDE.md §5.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRACE_FILE = Path(".claude/tool-trace.jsonl")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {"error": "malformed hook input"}

    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "PostToolUse",
        "payload": payload,
    }

    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(json.dumps({
        "continue": True
    }))


if __name__ == "__main__":
    main()
