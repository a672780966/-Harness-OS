"""Snapshot — capture project state for diff-based monitoring.

Read-only: captures git status, file changes, module risks, and loop artifacts.
No side effects, no external service calls.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectSnapshot:
    """A point-in-time snapshot of project monitoring state."""
    timestamp: str = ""
    git_branch: str = ""
    git_commit: str = ""
    git_status: List[str] = field(default_factory=list)
    git_diff_stat: List[Dict[str, Any]] = field(default_factory=list)
    uncommitted_count: int = 0
    file_hashes: Dict[str, str] = field(default_factory=dict)  # path → md5
    module_risks: Dict[str, float] = field(default_factory=dict)  # module → risk_score
    total_risk_score: float = 0.0
    merge_readiness_state: str = "unknown"
    task_card_count: int = 0
    blocking_card_count: int = 0

    # Loop artifact fields
    eval_results: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None
    review_results: Optional[Dict[str, Any]] = None
    final_gate: Optional[Dict[str, Any]] = None
    loop_report: Optional[str] = None


def capture_project_snapshot(project_root: str) -> ProjectSnapshot:
    """Capture current project state for monitoring.

    Args:
        project_root: Absolute path to project directory.

    Returns:
        ProjectSnapshot with current state.
    """
    if not os.path.isdir(project_root):
        return ProjectSnapshot(timestamp="error: not a directory")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z"
    snap = ProjectSnapshot(timestamp=now)

    # Git branch
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=project_root,
        )
        if result.returncode == 0:
            snap.git_branch = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        snap.git_branch = "not-a-git-repo"

    # Git commit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=project_root,
        )
        if result.returncode == 0:
            snap.git_commit = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Git status
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5, cwd=project_root,
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            snap.git_status = lines
            snap.uncommitted_count = len(lines)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Git diff stat
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=5, cwd=project_root,
        )
        if result.returncode == 0 and result.stdout.strip():
            snap.git_diff_stat = _parse_diff_stat(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Hashes for changed files
    for status_line in snap.git_status:
        parts = status_line.split()
        if len(parts) >= 2:
            fpath = parts[-1]  # filename is last part
            full_path = os.path.join(project_root, fpath)
            if os.path.isfile(full_path):
                snap.file_hashes[fpath] = _file_md5(full_path)

    return snap


def capture_loop_snapshot(loop_run_dir: str) -> ProjectSnapshot:
    """Capture current loop artifact state.

    Args:
        loop_run_dir: Path to loop run directory.

    Returns:
        ProjectSnapshot with loop-specific fields populated.
    """
    snap = ProjectSnapshot(timestamp="")

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z"
    snap.timestamp = now

    if not os.path.isdir(loop_run_dir):
        return snap

    # File hashes of key artifacts
    artifact_files = [
        "eval_report.json", "test_result.json", "final_review_envelope.json",
        "final_gate_result.md", "loop_report.md", "metrics.json",
        "run_classification.json",
    ]
    for af in artifact_files:
        fpath = os.path.join(loop_run_dir, af)
        if os.path.isfile(fpath):
            snap.file_hashes[af] = _file_md5(fpath)

    # Load JSON artifacts
    snap.eval_results = _load_json(os.path.join(loop_run_dir, "eval_report.json"))
    snap.test_results = _load_json(os.path.join(loop_run_dir, "test_result.json"))
    snap.review_results = _load_json(os.path.join(loop_run_dir, "final_review_envelope.json"))

    # Load final gate
    gate_path = os.path.join(loop_run_dir, "final_gate_result.md")
    if os.path.isfile(gate_path):
        try:
            with open(gate_path, "r", encoding="utf-8") as f:
                snap.final_gate = {"content": f.read()[:200], "path": gate_path}
        except (IOError, OSError):
            pass

    # Load loop report
    report_path = os.path.join(loop_run_dir, "loop_report.md")
    if os.path.isfile(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                snap.loop_report = f.read()[:500]
        except (IOError, OSError):
            pass

    return snap


def _file_md5(fpath: str) -> str:
    """Compute MD5 hash of a file."""
    try:
        h = hashlib.md5()
        with open(fpath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (IOError, OSError):
        return ""


def _load_json(fpath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file, return None on failure."""
    if not os.path.isfile(fpath):
        return None
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return None


def _parse_diff_stat(text: str) -> List[Dict[str, Any]]:
    """Parse git diff --stat output into structured data."""
    entries = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or "changed" in line or "file changed" in line:
            continue
        # Format: "file.py | 5 +-"
        if "|" in line:
            parts = [p.strip() for p in line.split("|", 1)]
            fname = parts[0]
            rest = parts[1] if len(parts) > 1 else ""
            entries.append({"file": fname, "stat": rest})
    return entries


def snapshot_diff(
    old: ProjectSnapshot,
    new: ProjectSnapshot,
) -> Dict[str, Any]:
    """Compute diff between two snapshots.

    Returns dict with changes in each category.
    """
    diffs: Dict[str, Any] = {}

    # Git branch change
    if old.git_branch != new.git_branch:
        diffs["branch_changed"] = {"old": old.git_branch, "new": new.git_branch}

    # Status change
    old_status = set(old.git_status)
    new_status = set(new.git_status)
    if old_status != new_status:
        added = new_status - old_status
        removed = old_status - new_status
        diffs["git_status_changed"] = {
            "added": list(added)[:20],
            "removed": list(removed)[:20],
            "old_count": old.uncommitted_count,
            "new_count": new.uncommitted_count,
        }

    # File hash changes
    changed_files = {}
    for fpath, new_hash in new.file_hashes.items():
        old_hash = old.file_hashes.get(fpath)
        if old_hash and old_hash != new_hash:
            changed_files[fpath] = {"old": old_hash[:8], "new": new_hash[:8]}
    new_files = set(new.file_hashes.keys()) - set(old.file_hashes.keys())
    if new_files:
        diffs["new_files"] = list(new_files)
    if changed_files:
        diffs["changed_files"] = changed_files

    # Module risk changes
    risk_changes = {}
    all_modules = set(old.module_risks.keys()) | set(new.module_risks.keys())
    for mod in all_modules:
        old_r = old.module_risks.get(mod, 0.0)
        new_r = new.module_risks.get(mod, 0.0)
        if abs(old_r - new_r) > 0.01:
            risk_changes[mod] = {"old": old_r, "new": new_r}
    if risk_changes:
        diffs["module_risk_changed"] = risk_changes

    # Merge readiness change
    if old.merge_readiness_state != new.merge_readiness_state:
        diffs["merge_readiness_changed"] = {
            "old": old.merge_readiness_state,
            "new": new.merge_readiness_state,
        }

    # Task card changes
    if old.task_card_count != new.task_card_count or old.blocking_card_count != new.blocking_card_count:
        diffs["task_cards_changed"] = {
            "old_total": old.task_card_count,
            "new_total": new.task_card_count,
            "old_blocking": old.blocking_card_count,
            "new_blocking": new.blocking_card_count,
        }

    # JSON artifact changes (hash-based)
    for key in ("eval_results", "test_results", "review_results", "final_gate", "loop_report"):
        old_val = getattr(old, key, None)
        new_val = getattr(new, key, None)
        if (old_val is None) != (new_val is None):
            diffs[f"{key}_presence_changed"] = {
                "old": "present" if old_val is not None else "absent",
                "new": "present" if new_val is not None else "absent",
            }

    return diffs
