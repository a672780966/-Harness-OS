#!/usr/bin/env python3
"""
Harness OS — 开发期 PostToolUse Trace Hook（非产品功能）

用于在开发 Harness OS 期间记录 AI 助手的工具调用。
不会随 Harness OS 分发给用户。

Records all tool calls to a JSONL trace file for observability.
Also captures observations for continuous learning (signal extraction).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TRACE_FILE = Path(".claude/tool-trace.jsonl")
OBSERVATIONS_FILE = Path(".claude/observations.jsonl")


def extract_signal(tool_name: str, tool_input: dict) -> str:
    """Extract a compact signal name from a tool call for pattern learning."""
    parts = [tool_name]
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("command", "")
        if isinstance(command, str) and command:
            first_word = command.strip().split()[0] if command.strip() else ""
            if len(first_word) < 30:
                parts.append(first_word)

        file_path = (
            tool_input.get("file_path")
            or tool_input.get("filePath")
            or tool_input.get("path")
            or ""
        )
        if isinstance(file_path, str) and file_path:
            ext = Path(file_path).suffix
            if ext:
                parts.append(ext)

    return ":".join(part for part in parts if part)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {"error": "malformed hook input"}

    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)

    tool_name = payload.get("tool_name") or payload.get("toolName") or ""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    session_id = payload.get("session_id") or payload.get("sessionId") or "unknown"

    # Write trace event
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "PostToolUse",
        "payload": payload,
    }

    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # Write observation for continuous learning
    if tool_name:
        observation = {
            "id": f"obs_{datetime.now().strftime('%y%m%d%H%M%S%f')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "tool-call",
            "sessionId": session_id,
            "signal": extract_signal(tool_name, tool_input),
            "context": tool_name,
            "outcome": "unknown",
            "confidence": 0.5,
            "frequency": 1,
        }

        with OBSERVATIONS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")

    print(json.dumps({
        "continue": True
    }))


if __name__ == "__main__":
    main()
