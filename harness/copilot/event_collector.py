"""Event Collector — collect project events (git, fs, agent status)."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schemas import now_iso, generate_id


def get_git_log(
    project_root: str,
    max_count: int = 20,
    since_days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Get recent git log entries."""
    try:
        cmd = ["git", "log", f"--max-count={max_count}",
               "--format=%H|%an|%ae|%ai|%s"]
        if since_days:
            cmd.insert(1, f"--since={since_days}.days")
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=15,
            cwd=project_root,
        )
        if result.returncode != 0:
            return [{"error": result.stderr.strip()}]

        entries = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) == 5:
                entries.append({
                    "commit_hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "date": parts[3],
                    "message": parts[4],
                })
        return entries
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return [{"error": str(e)}]


def get_git_diff(
    project_root: str,
    base_ref: str = "HEAD~1",
    target_ref: str = "HEAD",
) -> Optional[str]:
    """Get git diff between two refs."""
    try:
        result = subprocess.run(
            ["git", "diff", base_ref, target_ref],
            capture_output=True, text=True, timeout=15,
            cwd=project_root,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def get_git_diff_stat(
    project_root: str,
    base_ref: str = "HEAD~1",
    target_ref: str = "HEAD",
) -> List[Dict[str, Any]]:
    """Get git diff stat (file-level)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", base_ref, target_ref],
            capture_output=True, text=True, timeout=15,
            cwd=project_root,
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.strip().split("\n")
        stats = []
        for line in lines:
            if "changed" in line or "insertion" in line:
                continue
            if not line.strip():
                continue
            stats.append({"raw": line.strip()})
        return stats
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []


def get_git_branch(project_root: str) -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
            cwd=project_root,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return "unknown"


def get_git_status(project_root: str) -> List[str]:
    """Get git status --short output."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5,
            cwd=project_root,
        )
        if result.returncode == 0:
            return [l for l in result.stdout.strip().split("\n") if l.strip()]
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []


def get_recent_files_changed(project_root: str, since_commits: int = 5) -> List[str]:
    """Get list of files changed in recent commits."""
    try:
        result = subprocess.run(
            ["git", "diff", f"HEAD~{since_commits}", "HEAD", "--name-only"],
            capture_output=True, text=True, timeout=15,
            cwd=project_root,
        )
        if result.returncode == 0:
            return [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []


def get_project_last_commit(project_root: str) -> Optional[str]:
    """Get the most recent commit date for the project."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ai"],
            capture_output=True, text=True, timeout=5,
            cwd=project_root,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def is_git_repo(project_root: str) -> bool:
    """Check if project_root is a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, timeout=5,
            cwd=project_root,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
