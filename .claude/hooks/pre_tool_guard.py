#!/usr/bin/env python3
"""
Harness OS — PreToolUse Guard Hook

Intercepts Bash/Write/Edit/MultiEdit tool calls and checks against:
- Dangerous shell command patterns
- Protected file paths

Follows the hook constraints from Harness OS CLAUDE.md §5-6.
"""

import json
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


def deny(reason: str):
    print(json.dumps({
        "continue": False,
        "permissionDecision": "deny",
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

        for pattern in DANGEROUS_BASH_PATTERNS:
            if pattern in normalized:
                deny(f"Dangerous bash command requires explicit human approval: {pattern}")

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
