"""Safety policy enforcement for loop installer."""

from __future__ import annotations

import subprocess
from pathlib import Path


ALLOWED_ACTIONS = {
    "read files",
    "git status",
    "git diff",
    "git log",
    "pytest",
    "harness copilot inspect",
    "harness copilot readiness",
    "harness copilot task-card",
    "harness copilot pr-draft",
    "write .harness/loop/runs/",
    "write docs/*_report.md",
}

BLOCKED_ACTIONS = {
    "git push",
    "git push --tags",
    "git tag",
    "git merge",
    "git reset",
    "git clean",
    "rm",
    "delete files",
    "modify .env",
    "modify secrets",
    "deploy",
    "upload dist/*.tar.gz",
    "upload *.zip",
    "upload *.tgz",
    "rewrite history",
}


def is_action_allowed(action: str) -> tuple[bool, str]:
    """Check if an action is allowed by safety policy.
    Returns (allowed, reason).
    """
    if action in BLOCKED_ACTIONS:
        return False, f"Action '{action}' is blocked: requires human approval"
    if action in ALLOWED_ACTIONS:
        return True, f"Action '{action}' is auto-allowed"
    # Default: non-listed actions are blocked
    return False, f"Action '{action}' is not in the allow list"


def check_git_status(project_root: str) -> bool:
    """Check if working tree is clean."""
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=project_root, capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip() == ""


def check_blocked_files(project_root: str) -> list[str]:
    """Check for blocked large files in the working tree."""
    blocked = []
    patterns = ["*.tar.gz", "*.zip", "*.tgz", "__pycache__/", "*.pyc"]
    for pattern in patterns:
        if pattern.endswith("/"):
            path = Path(project_root) / pattern.rstrip("/")
            if path.exists():
                blocked.append(pattern)
        elif pattern.startswith("*."):
            for f in Path(project_root).rglob(pattern):
                blocked.append(str(f))
    return blocked


def safety_report(project_root: str) -> str:
    """Generate a human-readable safety report."""
    lines = ["🛡️ Safety Gate Report", ""]

    clean = check_git_status(project_root)
    lines.append(f"Worktree clean: {'✅' if clean else '❌'}")

    blocked_files = check_blocked_files(project_root)
    if blocked_files:
        lines.append(f"Blocked files: ❌ ({len(blocked_files)} found)")
        for f in blocked_files[:5]:
            lines.append(f"  - {f}")
    else:
        lines.append("Blocked files: ✅ none")

    lines.append("")
    lines.append("Allowed actions:")
    for a in sorted(ALLOWED_ACTIONS):
        lines.append(f"  ✅ {a}")

    lines.append("")
    lines.append("Blocked actions (require human):")
    for a in sorted(BLOCKED_ACTIONS):
        lines.append(f"  🚫 {a}")

    return "\n".join(lines)
