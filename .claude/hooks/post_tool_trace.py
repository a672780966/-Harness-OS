#!/usr/bin/env python3
"""
Harness OS — PostToolUse Trace Hook（resilient version）

保留记录功能，但任何异常不阻塞 Claude Code：
  - 兼容空 stdin、坏 JSON、非 dict payload、非字符串 tool_name
  - 所有异常写入 .claude/hook-errors.log
  - 脚本始终返回 0

Records tool calls to JSONL trace file + observations for continuous learning.
"""

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

TRACE_FILE = Path(".claude/tool-trace.jsonl")
OBSERVATIONS_FILE = Path(".claude/observations.jsonl")
ERROR_LOG = Path(".claude/hook-errors.log")


def _log_error(context: str, exc: BaseException) -> None:
    """Append an error record to the error log; never raises."""
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        entry = json.dumps({
            "timestamp": timestamp,
            "hook": "post_tool_trace",
            "context": context,
            "error": str(exc),
            "traceback": tb,
        }, ensure_ascii=False)
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        # Last resort — stderr is all we have; never raise.
        try:
            print(f"[hook-error] post_tool_trace: {exc}", file=sys.stderr)
        except Exception:
            pass


def _safe_read_stdin() -> str:
    """Read all of stdin; return empty string on any failure."""
    try:
        return sys.stdin.read()
    except Exception as exc:
        _log_error("read stdin", exc)
        return ""


def _safe_parse_json(raw: str) -> dict | None:
    """Parse JSON; return None on empty/malformed input."""
    if not raw or not raw.strip():
        return None
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            _log_error("non-dict payload", TypeError(f"expected dict, got {type(parsed).__name__}"))
            return None
        return parsed
    except json.JSONDecodeError as exc:
        _log_error("malformed JSON", exc)
        return None
    except Exception as exc:
        _log_error("unexpected parse error", exc)
        return None


def _safe_get_str(payload: dict, *keys: str) -> str:
    """Safely pluck a string value; return '' on missing/wrong type."""
    for key in keys:
        val = payload.get(key)
        if isinstance(val, str):
            return val
    return ""


def _safe_get_dict(payload: dict, *keys: str) -> dict:
    """Safely pluck a dict value; return {} on missing/wrong type."""
    for key in keys:
        val = payload.get(key)
        if isinstance(val, dict):
            return val
    return {}


def _append_jsonl(path: Path, obj: dict) -> bool:
    """Atomically append a JSON line to a file; return True on success."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(obj, ensure_ascii=False) + "\n"
        with path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(line)
        return True
    except Exception as exc:
        _log_error(f"write {path.name}", exc)
        return False


def extract_signal(tool_name: str, tool_input: dict) -> str:
    """Extract a compact signal name for pattern learning."""
    parts = [tool_name]
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or ""
        if isinstance(command, str) and command.strip():
            first_word = command.strip().split()[0]
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


def main() -> None:
    # ---- Phase 1: read + parse (never raises) ----
    raw = _safe_read_stdin()
    payload = _safe_parse_json(raw)

    # ---- Phase 2: extract fields (safe defaults for bad input) ----
    tool_name = _safe_get_str(payload, "tool_name", "toolName") if payload else ""
    tool_input = _safe_get_dict(payload, "tool_input", "toolInput") if payload else {}
    session_id = _safe_get_str(payload, "session_id", "sessionId") if payload else "unknown"

    # ---- Phase 3: write trace event ----
    ts = datetime.now(timezone.utc).isoformat()
    trace_event = {
        "timestamp": ts,
        "event": "PostToolUse",
        "payload": payload if payload else {"note": "no input received"},
    }
    _append_jsonl(TRACE_FILE, trace_event)

    # ---- Phase 4: write observation for learning ----
    if tool_name:
        observation = {
            "id": f"obs_{datetime.now().strftime('%y%m%d%H%M%S%f')}",
            "timestamp": ts,
            "type": "tool-call",
            "sessionId": session_id,
            "signal": extract_signal(tool_name, tool_input),
            "context": tool_name,
            "outcome": "unknown",
            "confidence": 0.5,
            "frequency": 1,
        }
        _append_jsonl(OBSERVATIONS_FILE, observation)

    # ---- Phase 5: always respond with continue ----
    try:
        print(json.dumps({"continue": True}))
    except Exception as exc:
        _log_error("print output", exc)
        # Last-ditch: write to stderr so Claude Code sees something
        try:
            print('{"continue": true}', file=sys.stderr)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        _log_error("unhandled top-level", exc)
        # Never let an exception bubble up — always return 0.
    finally:
        sys.exit(0)
