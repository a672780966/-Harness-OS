"""Suggestion Engine — generate precise next change suggestions."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .schemas import (
    ProjectSemanticMap,
    ModuleCard,
    ChangeSuggestion,
    Priority,
    now_iso,
)
from .diff_analyzer import parse_diff, diff_file_list
from .risk_classifier import classify_file_risk


def _extract_functions(file_path: str, content: str) -> List[str]:
    """Extract function/class names from source code (basic regex)."""
    functions: List[str] = []
    ext = Path(file_path).suffix.lower()

    if ext == ".py":
        patterns = [
            r"^def\s+(\w+)\s*\(",           # Python functions
            r"^async\s+def\s+(\w+)\s*\(",     # Python async functions
            r"^class\s+(\w+)\s*[\(:]",        # Python classes
        ]
    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        patterns = [
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
            r"(?:export\s+)?(?:async\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(?.*\)\s*(?::[^=]+)?\s*=>",
            r"(?:export\s+)?class\s+(\w+)\s*[\(:]",
            r"(?:export\s+)?default\s+(?:function|class)\s+(\w+)",
        ]
    elif ext in (".go",):
        patterns = [
            r"^func\s+(\w+)\s*\(",          # Go functions
            r"^func\s+\([^)]+\)\s+(\w+)\s*\(",  # Go methods
        ]
    else:
        patterns = [
            r"(?:def|function|fn|fun)\s+(\w+)\s*\(",
            r"^class\s+(\w+)\s*[\(:]",
        ]

    for pattern in patterns:
        for match in re.finditer(pattern, content, re.MULTILINE):
            functions.append(match.group(1))

    return functions


def _find_todo_comments(file_path: str, content: str) -> List[str]:
    """Find TODO/FIXME/HACK comments."""
    todos: List[str] = []
    for i, line in enumerate(content.split("\n"), 1):
        stripped = line.strip()
        if re.search(r"(TODO|FIXME|HACK|XXX|BUG|WORKAROUND)", stripped, re.IGNORECASE):
            todos.append(f"L{i}: {stripped.strip()[:120]}")
    return todos


def _find_test_coverage_gaps(
    sem_map: ProjectSemanticMap,
) -> List[Dict[str, Any]]:
    """Find source files without corresponding test files.

    Only source-code file extensions are considered.
    Documentation, config, data, and lock files are excluded.
    """
    gaps: List[Dict[str, Any]] = []

    # Extensions that CAN have unit tests
    SOURCE_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        ".go", ".rs", ".java", ".rb", ".php", ".cs", ".swift",
        ".kt", ".scala", ".c", ".cpp", ".h", ".hpp",
    }

    # Extensions that should NEVER trigger a "missing test" suggestion
    NON_SOURCE_EXTENSIONS = {
        ".md", ".mdx", ".rst", ".txt", ".log",
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
        ".xml", ".html", ".css", ".scss", ".less",
        ".sh", ".bash", ".zsh", ".ps1", ".bat",
        ".lock", ".svg", ".png", ".jpg", ".ico",
        ".env", ".env.example", ".dockerfile",
        ".gitignore", ".gitkeep", ".editorconfig",
        ".prettierrc", ".eslintrc", ".babelrc",
        ".npmrc", ".yarnrc",
    }

    test_suffixes = {"_test", ".test.", "_spec.", ".spec.", "_tests"}

    source_files: Set[str] = set()
    test_files: Set[str] = set()

    for mod in sem_map.modules:
        for fe in mod.files:
            lower = fe.path.lower()
            ext = Path(lower).suffix
            # Skip non-source files
            if ext in NON_SOURCE_EXTENSIONS:
                continue
            # Also skip files like "CLAUDE.md", "Dockerfile" without recognizable ext
            base = Path(lower).name
            if base in ("claude.md", "codex-cloud-handoff.md", "readme.md",
                        "license", "changelog", "contributing", "makefile",
                        "dockerfile", "docker-compose.yml", "docker-compose.yaml"):
                continue
            if any(s in lower for s in test_suffixes) or "/test" in lower or "/tests" in lower:
                test_files.add(fe.path)
            elif ext in SOURCE_EXTENSIONS or not ext:
                source_files.add(fe.path)

    for sf in sorted(source_files):
        p = Path(sf)
        stem = p.stem
        # Check for matching test files
        has_test = False
        for tf in test_files:
            if stem in tf or p.name.replace(".", "_") in tf:
                has_test = True
                break
        if not has_test and not sf.startswith("."):
            gaps.append({
                "file": sf,
                "suggestion": f"Add tests for {sf}",
            })

    return gaps


def _find_recently_changed_files(
    sem_map: ProjectSemanticMap,
    diff_text: Optional[str] = None,
) -> List[str]:
    """Find files that were recently changed."""
    if diff_text:
        return diff_file_list(diff_text)
    return []


def generate_suggestions(
    project_root: str,
    sem_map: ProjectSemanticMap,
    diff_text: Optional[str] = None,
    max_suggestions: int = 10,
) -> List[ChangeSuggestion]:
    """Generate next change suggestions based on project analysis."""
    suggestions: List[ChangeSuggestion] = []

    # 1. Test coverage gaps
    gaps = _find_test_coverage_gaps(sem_map)
    for gap in gaps[:3]:
        sug = ChangeSuggestion(
            file_path=gap["file"],
            module=_guess_module(gap["file"]),
            suggestion=gap["suggestion"],
            reason="Test coverage gap — add tests for untested source file",
            confidence=0.6,
            priority=Priority.MEDIUM,
        )
        suggestions.append(sug)

    # 2. Scan for TODO/FIXME in recently changed files only (limit reads)
    recent_files = _find_recently_changed_files(sem_map, diff_text)
    max_file_reads = 20
    file_read_count = 0
    for rf in recent_files:
        if file_read_count >= max_file_reads:
            break
        abs_path = os.path.join(project_root, rf)
        if not os.path.isfile(abs_path):
            continue

        # Skip large files (>100KB) to avoid slow reads
        try:
            if os.path.getsize(abs_path) > 100 * 1024:
                continue
        except OSError:
            continue

        try:
            with open(abs_path, "r", errors="ignore") as f:
                content = f.read()
            file_read_count += 1
        except (OSError, IOError):
            continue

        functions = _extract_functions(rf, content)
        todos = _find_todo_comments(rf, content)

        if todos:
            mod = _guess_module(rf)
            func = functions[0] if functions else None
            sug = ChangeSuggestion(
                file_path=rf,
                function=func,
                module=mod,
                suggestion=f"Resolve TODO/FIXME: {todos[0][:100]}",
                reason=f"Found {len(todos)} TODO/FIXME items in recently changed file",
                confidence=0.5,
                priority=Priority.LOW,
                evidence_refs=[t[:80] for t in todos[:3]],
            )
            suggestions.append(sug)

    # 3. High-risk files need review
    for mod in sem_map.modules:
        for fe in mod.files:
            if fe.risk_score >= 0.7 and fe.path in recent_files:
                sug = ChangeSuggestion(
                    file_path=fe.path,
                    module=mod.name,
                    suggestion=f"Review high-risk file {fe.path}",
                    reason=f"File has elevated risk score ({fe.risk_score:.1f})",
                    confidence=0.8,
                    priority=Priority.HIGH,
                )
                suggestions.append(sug)

    # 4. Dependency awareness
    for mod in sem_map.modules:
        if mod.name in [c.module for c in suggestions]:
            continue
        if len(mod.files) > 20 and mod.dependencies:
            # Large module with dependencies — suggest modularization
            sug = ChangeSuggestion(
                file_path=mod.path,
                module=mod.name,
                suggestion=f"Consider splitting '{mod.name}' into smaller modules",
                reason=f"Module has {len(mod.files)} files and {len(mod.dependencies)} dependencies",
                confidence=0.3,
                priority=Priority.LOW,
            )
            suggestions.append(sug)

    return suggestions[:max_suggestions]


def _guess_module(file_path: str) -> str:
    """Guess module name from file path."""
    parts = Path(file_path).parts
    if len(parts) >= 2:
        return parts[0]
    return "root"


def quick_suggestions(
    project_root: str,
    sem_map: ProjectSemanticMap,
    diff_text: Optional[str] = None,
) -> str:
    """Quick text summary of suggestions (for CLI)."""
    suggestions = generate_suggestions(project_root, sem_map, diff_text)
    if not suggestions:
        return "No specific suggestions at this time."

    lines = ["Next change suggestions:", ""]
    for sug in suggestions:
        priority_tag = {
            Priority.CRITICAL: "🔴",
            Priority.HIGH: "🟠",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "⚪",
        }.get(sug.priority, "⚪")
        lines.append(
            f"  {priority_tag} [{sug.priority.value}] {sug.suggestion[:100]}"
        )
        if sug.file_path:
            lines.append(f"       File: {sug.file_path}")
        if sug.confidence:
            lines.append(f"       Confidence: {sug.confidence:.0%}")
    return "\n".join(lines)
