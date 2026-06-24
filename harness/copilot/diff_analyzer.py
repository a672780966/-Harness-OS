"""Diff Analyzer — parse and analyze git diffs for module mapping."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .schemas import (
    ProjectSemanticMap,
    DiffEntry,
    ModuleDiffSummary,
    RiskLevel,
)


def parse_diff(diff_text: str) -> List[DiffEntry]:
    """Parse raw git diff text into DiffEntry objects."""
    entries: List[DiffEntry] = []
    current_file: Optional[str] = None
    lines_added = 0
    lines_removed = 0
    hunks = 0

    for line in diff_text.split("\n"):
        # Detect file header
        diff_header = re.match(r"^diff --git a/(.+) b/(.+)$", line)
        if diff_header:
            # Save previous file
            if current_file:
                entries.append(DiffEntry(
                    file_path=current_file,
                    change_type=_classify_change(lines_added, lines_removed),
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    hunks=hunks,
                    diff_summary=f"{lines_added}+/{lines_removed}- changes",
                ))
            current_file = diff_header.group(2)
            lines_added = 0
            lines_removed = 0
            hunks = 0
            continue

        # Count hunks
        if line.startswith("@@"):
            hunks += 1
            continue

        # Count added/removed lines
        if line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    # Last file
    if current_file:
        entries.append(DiffEntry(
            file_path=current_file,
            change_type=_classify_change(lines_added, lines_removed),
            lines_added=lines_added,
            lines_removed=lines_removed,
            hunks=hunks,
            diff_summary=f"{lines_added}+/{lines_removed}- changes",
        ))

    return entries


def _classify_change(added: int, removed: int) -> str:
    if added > 0 and removed == 0:
        return "added"
    elif removed > 0 and added == 0:
        return "deleted"
    elif added > 0 and removed > 0:
        return "modified"
    return "unknown"


def group_diff_by_module(
    entries: List[DiffEntry],
    sem_map: ProjectSemanticMap,
) -> List[ModuleDiffSummary]:
    """Group diff entries by module from the semantic map."""
    module_map: Dict[str, List[DiffEntry]] = {}

    for entry in entries:
        # Find which module this file belongs to
        assigned = False
        for mod in sem_map.modules:
            for fe in mod.files:
                if fe.path == entry.file_path or entry.file_path.endswith("/" + fe.path):
                    if mod.name not in module_map:
                        module_map[mod.name] = []
                    module_map[mod.name].append(entry)
                    assigned = True
                    break
            if assigned:
                break

        if not assigned:
            # Try prefix matching
            parts = Path(entry.file_path).parts
            if parts:
                prefix = parts[0]
                if prefix not in module_map:
                    module_map[prefix] = []
                module_map[prefix].append(entry)

    results: List[ModuleDiffSummary] = []
    for mod_name, mod_entries in module_map.items():
        total_added = sum(e.lines_added for e in mod_entries)
        total_removed = sum(e.lines_removed for e in mod_entries)

        # Calculate risk impact
        risk = RiskLevel.LOW
        if total_added + total_removed > 200:
            risk = RiskLevel.HIGH
        elif total_added + total_removed > 50:
            risk = RiskLevel.MEDIUM

        # Check for high-risk files
        for e in mod_entries:
            lower = e.file_path.lower()
            for kw in ["auth", "secret", "password", "token", "deploy", "database", "payment"]:
                if kw in lower:
                    risk = RiskLevel.HIGH
                    break

        results.append(ModuleDiffSummary(
            module_name=mod_name,
            entries=mod_entries,
            total_added=total_added,
            total_removed=total_removed,
            risk_impact=risk,
        ))

    return results


def diff_file_list(diff_text: str) -> List[str]:
    """Extract list of changed files from diff text."""
    files: List[str] = []
    for line in diff_text.split("\n"):
        m = re.match(r"^diff --git a/.+ b/(.+)$", line)
        if m:
            files.append(m.group(1))
    return files


def simple_diff_stats(diff_text: str) -> Dict:
    """Quick diff stats without full parsing."""
    files = diff_file_list(diff_text)
    added = len(re.findall(r"^\+", diff_text, re.MULTILINE))
    removed = len(re.findall(r"^-", diff_text, re.MULTILINE))
    # Don't count +++/--- headers
    added -= len(re.findall(r"^\+\+\+", diff_text, re.MULTILINE))
    removed -= len(re.findall(r"^---", diff_text, re.MULTILINE))
    return {
        "files_changed": len(files),
        "lines_added": max(0, added),
        "lines_removed": max(0, removed),
        "file_list": files,
    }
