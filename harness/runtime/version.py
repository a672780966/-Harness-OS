"""Runtime version — report Harness Copilot version information.

Reads from:
  1. Git tag (latest tag on current branch)
  2. Git commit (fallback)
  3. HARDCODED_VERSION constant (last resort)
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Dict, Optional

from .doctor import run_doctor

# Bump this when making significant releases
HARDCODED_VERSION = "1.3.0-dev"


def _get_git_tag() -> Optional[str]:
    """Get the most recent git tag on the current branch."""
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _get_git_commit() -> Optional[str]:
    """Get the current git commit short hash."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _get_git_branch() -> Optional[str]:
    """Get the current git branch name."""
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def get_version_info() -> Dict[str, Any]:
    """Gather version information from all available sources."""
    tag = _get_git_tag()
    commit = _get_git_commit()
    branch = _get_git_branch()

    # Prefer tag, then version from tag, then hardcoded
    display_version = tag or HARDCODED_VERSION

    return {
        "version": display_version,
        "git_tag": tag or "",
        "git_commit": commit or "",
        "git_branch": branch or "",
        "hardcoded_version": HARDCODED_VERSION,
    }


def format_version(version_info: Optional[Dict[str, Any]] = None) -> str:
    """Format version info as a user-friendly string."""
    if version_info is None:
        version_info = get_version_info()

    parts = [f"Harness Copilot v{version_info['version']}"]
    if version_info.get("git_commit"):
        parts.append(f"(commit: {version_info['git_commit']}")
        if version_info.get("git_branch"):
            parts[-1] += f" | branch: {version_info['git_branch']}"
        parts[-1] += ")"
    return " ".join(parts)
