"""Change Explainer — generate natural language explanations of recent changes."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .schemas import (
    ProjectSemanticMap,
    DiffEntry,
    RecentChangeExplanation,
    ModuleDiffSummary,
    now_iso,
)
from .diff_analyzer import parse_diff, group_diff_by_module
from .risk_classifier import classify_diff_risk


def _summarize_intent(file_path: str, added: int, removed: int) -> str:
    """Heuristic intent detection from file path and diff stats."""
    lower = file_path.lower()
    name = Path(file_path).stem

    if "test" in lower or "spec" in lower or "_test" in lower:
        return "Adding or updating tests"
    if "fix" in name.lower() or "bug" in name.lower():
        return "Bug fix"
    if "refactor" in name.lower() or "clean" in name.lower():
        return "Code refactoring"
    if "doc" in lower or "readme" in name.lower():
        return "Documentation update"
    if "config" in name.lower() or lower.endswith(".env"):
        return "Configuration change"
    if "migration" in lower or "migrate" in lower:
        return "Database migration"
    if "style" in name.lower() or "format" in name.lower():
        return "Code style / formatting"
    if "feat" in name.lower() or "feature" in name.lower():
        return "Feature implementation"
    if "deprecat" in name.lower():
        return "Deprecation handling"
    if "upgrade" in name.lower() or "bump" in name.lower():
        return "Dependency upgrade"

    # Generic by operation size
    if added > 0 and removed > 0:
        return "Code modification (mixed add/remove)"
    elif added > 0:
        return "New code addition"
    elif removed > 0:
        return "Code removal"
    return "Code change"


def _summarize_change(
    entries: List[DiffEntry],
    total_added: int,
    total_removed: int,
) -> str:
    """Generate a summary sentence."""
    file_count = len(entries)
    files_word = "file" if file_count == 1 else "files"

    if total_added > 0 and total_removed > 0:
        return (
            f"Changed {file_count} {files_word} "
            f"(+{total_added}/-{total_removed} lines)"
        )
    elif total_added > 0:
        return (
            f"Added {total_added} lines across {file_count} {files_word}"
        )
    elif total_removed > 0:
        return (
            f"Removed {total_removed} lines across {file_count} {files_word}"
        )
    return f"Modified {file_count} {files_word}"


def explain_diff(
    diff_text: str,
    sem_map: Optional[ProjectSemanticMap] = None,
) -> List[RecentChangeExplanation]:
    """Generate explanations from raw git diff text."""
    entries = parse_diff(diff_text)

    if sem_map:
        summaries = group_diff_by_module(entries, sem_map)
    else:
        # Group by top-level directory
        module_groups: Dict[str, List[DiffEntry]] = {}
        for entry in entries:
            parts = Path(entry.file_path).parts
            mod = parts[0] if len(parts) > 1 else "root"
            if mod not in module_groups:
                module_groups[mod] = []
            module_groups[mod].append(entry)
        summaries = []
        for mod_name, mod_entries in module_groups.items():
            summaries.append(ModuleDiffSummary(
                module_name=mod_name,
                entries=mod_entries,
                total_added=sum(e.lines_added for e in mod_entries),
                total_removed=sum(e.lines_removed for e in mod_entries),
            ))

    explanations: List[RecentChangeExplanation] = []
    for summary in summaries:
        files_changed = [e.file_path for e in summary.entries]

        # Detect intent from the most significant file
        primary_file = max(summary.entries, key=lambda e: e.lines_added + e.lines_removed)
        intent = _summarize_intent(
            primary_file.file_path,
            primary_file.lines_added,
            primary_file.lines_removed,
        )

        # Collect risks
        risks: List[str] = []
        for entry in summary.entries:
            score, reasons = classify_diff_risk(entry)
            if score >= 0.5:
                risk_str = f"{entry.file_path}: {', '.join(reasons)}"
                risks.append(risk_str)

        explanations.append(RecentChangeExplanation(
            module=summary.module_name,
            summary=_summarize_change(
                summary.entries,
                summary.total_added,
                summary.total_removed,
            ),
            files_changed=files_changed,
            lines_added=summary.total_added,
            lines_removed=summary.total_removed,
            intent=intent,
            risks=risks,
            generated_at=now_iso(),
        ))

    return explanations


def quick_explain(
    diff_text: str,
    max_files: int = 10,
) -> str:
    """Quick one-paragraph explanation (for CLI)."""
    explanations = explain_diff(diff_text)
    if not explanations:
        return "No changes detected."

    total_files = sum(len(e.files_changed) for e in explanations)
    total_added = sum(e.lines_added for e in explanations)
    total_removed = sum(e.lines_removed for e in explanations)

    lines = [
        f"Recent changes: {total_files} files, +{total_added}/-{total_removed} lines.",
    ]

    for expl in explanations[:5]:  # Max 5 modules
        lines.append(f"\n  [{expl.module}] {expl.summary}")
        if expl.intent:
            lines.append(f"    Intent: {expl.intent}")
        if expl.risks:
            for risk in expl.risks[:3]:
                lines.append(f"    ⚠ {risk}")

    if len(explanations) > 5:
        lines.append(f"\n  ... and {len(explanations) - 5} more modules")

    return "\n".join(lines)
