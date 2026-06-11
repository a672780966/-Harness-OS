#!/usr/bin/env python3
"""
Harness OS — 开发期 PreToolUse Guard Hook（非产品功能）

用于在开发 Harness OS 期间保护 AI 助手不误操作。
不会随 Harness OS 分发给用户。

Intercepts Bash/Write/Edit/MultiEdit tool calls and checks against:
- Dangerous shell command patterns
- Protected file paths
- Dev server running outside tmux (blocks)
- Git push without review reminder
"""

import json
import re
import sys
from pathlib import Path

PROTECTED_PATHS = [
    ".env",
    ".env.local",
    ".env.production",
    "secrets",
    "credentials",
    ".git",
]

DANGEROUS_BASH_PATTERNS = [
    "rm -rf",
    "sudo ",
    "chmod 777",
    "chown ",
    "git push",
    "git reset --hard",
    "git clean -fd",
    "npm publish",
    "pnpm publish",
    "docker push",
    "kubectl delete",
    "terraform apply",
    "terraform destroy",
]

DEV_SERVER_PATTERNS = [
    r"npm run dev",
    r"pnpm dev",
    r"pnpm run dev",
    r"yarn dev",
    r"npm start",
    r"pnpm start",
]


def deny(reason: str):
    print(json.dumps({
        "continue": False,
        "permissionDecision": "deny",
        "permissionDecisionReason": reason
    }))
    sys.exit(0)


def needs_approval(reason: str):
    print(json.dumps({
        "continue": False,
        "permissionDecision": "needs_approval",
        "permissionDecisionReason": reason
    }))
    sys.exit(0)


def allow(reason: str = "allowed by pre_tool_guard"):
    print(json.dumps({
        "continue": True,
        "permissionDecision": "allow",
        "permissionDecisionReason": reason
    }))
    sys.exit(0)


def is_dev_server_command(command: str) -> bool:
    """Detect dev server startup commands that should run in tmux."""
    normalized = command.lower().strip()
    for pattern in DEV_SERVER_PATTERNS:
        if re.search(pattern, normalized):
            return True
    return False


def is_git_push(command: str) -> bool:
    """Detect git push to warn about review."""
    normalized = command.lower().strip()
    return normalized.startswith("git push") or "git push " in normalized


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        deny("Malformed hook input")

    tool_name = payload.get("tool_name") or payload.get("toolName") or ""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        normalized = command.lower()

        # Check dangerous patterns
        for pattern in DANGEROUS_BASH_PATTERNS:
            if pattern in normalized:
                deny(f"Dangerous bash command requires explicit human approval: {pattern}")

        # Detect dev server commands
        if is_dev_server_command(command):
            needs_approval("Dev server commands should run in tmux to persist across sessions")

        # Warn on git push
        if is_git_push(command):
            allow(f"Git push detected — please review changes before push: {command[:60]}")

        allow("Bash command passed basic guard")

    if tool_name in ["Write", "Edit", "MultiEdit"]:
        path_value = (
            tool_input.get("file_path")
            or tool_input.get("path")
            or tool_input.get("filePath")
            or ""
        )

        path_text = str(path_value)

        for protected in PROTECTED_PATHS:
            if protected in path_text:
                deny(f"Protected path cannot be modified by default: {protected}")

        allow("File write/edit passed basic guard")

    allow("No specific guard matched")


if __name__ == "__main__":
    main()
