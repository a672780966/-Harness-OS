#!/usr/bin/env python3
"""
Harness OS — 开发期 PostToolUse Trace Hook（非产品功能）

用于在开发 Harness OS 期间记录 AI 助手的工具调用。
不会随 Harness OS 分发给用户。

Records all tool calls to a JSONL trace file for observability.
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
