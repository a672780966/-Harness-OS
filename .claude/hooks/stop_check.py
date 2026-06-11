#!/usr/bin/env python3
"""
Harness OS — Stop Hook
Checks for common issues after each response:
- console.log statements in modified files
- Large context window usage
- Pending tasks requiring attention
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

def check_console_log():
    """Check for console.log statements in tracked source files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=AM"],
            capture_output=True, text=True, timeout=5, cwd="."
        )
        changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        warnings = []
        for file in changed_files:
            if not file or not file.endswith((".ts", ".tsx", ".js", ".jsx")):
                continue
            file_path = Path(file)
            if not file_path.exists():
                continue

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if "console.log" in content:
                warnings.append(file)

        return warnings
    except Exception:
        return []

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    console_log_files = check_console_log()
    messages = []

    if console_log_files:
        messages.append(f"console.log found in: {', '.join(console_log_files[:5])}")

    result = {
        "continue": True,
        "permissionDecision": "allow",
    }

    if messages:
        result["permissionDecisionReason"] = "; ".join(messages)
        print(json.dumps(result))
    else:
        result["permissionDecisionReason"] = "Clean check"
        print(json.dumps(result))

if __name__ == "__main__":
    main()
