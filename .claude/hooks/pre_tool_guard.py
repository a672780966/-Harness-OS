#!/usr/bin/env python3
"""
Harness OS — PreToolUse Guard Hook (fail-closed)

Intercepts tool calls and checks against dangerous patterns and protected paths.
Fail-closed (GOV3-07): any parse error, exception, or unknown state → deny/needs_approval.
"""

import json
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ERROR_LOG = Path(".claude/hook-errors.log")


def _log_error(context: str, exc: BaseException) -> None:
    """Log error without raising."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        entry = json.dumps({"timestamp": ts, "hook": "pre_tool_guard", "context": context, "error": str(exc), "traceback": tb})
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


def fail_closed(reason: str):
    """Default response on any error — never allow when uncertain (GOV3-07)."""
    print(json.dumps({"continue": False, "permissionDecision": "deny", "permissionDecisionReason": reason}))
    sys.exit(0)


def deny(reason: str):
    print(json.dumps({"continue": False, "permissionDecision": "deny", "permissionDecisionReason": reason}))
    sys.exit(0)


def needs_approval(reason: str):
    print(json.dumps({"continue": False, "permissionDecision": "needs_approval", "permissionDecisionReason": reason}))
    sys.exit(0)


def allow(reason: str = "allowed by pre_tool_guard"):
    print(json.dumps({"continue": True, "permissionDecision": "allow", "permissionDecisionReason": reason}))
    sys.exit(0)


PROTECTED_PATHS = [
    ".env", ".env.local", ".env.production",
    "secrets", "credentials", ".git",
    "id_rsa", "id_ed25519", ".pem", ".key",
]

DANGEROUS_BASH_PATTERNS = [
    "rm -rf", "sudo ", "chmod 777", "chown ",
    "git push", "git reset --hard", "git clean -fd",
    "npm publish", "pnpm publish", "docker push",
    "kubectl delete", "terraform apply", "terraform destroy",
    # PowerShell patterns
    "remove-item", "ri ", "net user", "net localgroup",
    "stop-process", "kill ", "start-process",
    "invoke-expression", "iex ", "invoke-webrequest",
    "iwr ", "new-item -type", "set-content",
]


def main():
    # Phase 1: Read stdin (fail-closed on failure)
    try:
        raw = sys.stdin.read()
    except Exception as exc:
        _log_error("stdin read", exc)
        fail_closed("Failed to read hook input")

    # Phase 2: Parse JSON (fail-closed on bad input)
    if not raw or not raw.strip():
        fail_closed("Empty hook input")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _log_error("json parse", exc)
        fail_closed("Malformed JSON in hook input")

    if not isinstance(payload, dict):
        fail_closed(f"Expected dict payload, got {type(payload).__name__}")

    # Phase 3: Extract fields with type-safe defaults
    try:
        tool_name = ""
        raw_name = payload.get("tool_name") or payload.get("toolName") or ""
        if isinstance(raw_name, str):
            tool_name = raw_name

        tool_input = {}
        raw_input = payload.get("tool_input") or payload.get("toolInput") or {}
        if isinstance(raw_input, dict):
            tool_input = raw_input
    except Exception as exc:
        _log_error("field extraction", exc)
        fail_closed("Failed to extract tool fields")

    # Phase 4: Evaluate (wrap in try/except — fail-closed on any exception)
    try:
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if not isinstance(command, str):
                command = str(command) if command else ""
            normalized = command.lower()

            for pattern in DANGEROUS_BASH_PATTERNS:
                if pattern in normalized:
                    deny(f"Dangerous bash command requires explicit human approval: {pattern}")

            allow("Bash command passed basic guard")

        elif tool_name in ("Write", "Edit", "MultiEdit", "WriteFile"):
            path_value = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("filePath") or ""
            path_text = str(path_value)

            for protected in PROTECTED_PATHS:
                if protected in path_text:
                    deny(f"Protected path cannot be modified by default: {protected}")

            allow("File write/edit passed basic guard")

        else:
            # Unknown tool — deny per fail-closed (GOV3-07)
            deny(f"Unknown tool in pre_tool_guard: {tool_name}")

    except Exception as exc:
        _log_error(f"guard eval ({tool_name})", exc)
        fail_closed(f"Guard evaluation failed: {exc}")


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        _log_error("top-level", exc)
        fail_closed("Unhandled hook error")
