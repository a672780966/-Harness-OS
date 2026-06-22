"""Project Scanner — scan a local project directory and build file tree."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .schemas import (
    ProjectSemanticMap,
    ModuleCard,
    FileEntry,
    DependencyEdge,
    RiskLevel,
    now_iso,
)


# Directories and files to ignore when scanning
IGNORE_DIRS: Set[str] = {
    ".git", "__pycache__", "node_modules", ".venv", ".tox",
    ".pytest_cache", ".harness", "dist", "build", ".next",
    ".turbo", ".cache", ".nyc_output", "coverage",
}

IGNORE_FILES: Set[str] = {
    ".DS_Store", "*.pyc", "*.pyo", "*.egg-info",
}

HIGH_RISK_PATTERNS: List[str] = [
    "secret", "credential", "password", "token", "key",
    "auth", "permission", "deploy", "prod", "database",
    "migration", ".env", "config/prod",
]


def guess_language(file_path: str) -> str:
    """Guess programming language from file extension."""
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript React", ".jsx": "JavaScript React",
        ".go": "Go", ".rs": "Rust", ".java": "Java",
        ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
        ".cs": "C#", ".rb": "Ruby", ".php": "PHP",
        ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
        ".r": "R", ".m": "MATLAB/Objective-C",
        ".sql": "SQL", ".sh": "Shell", ".bash": "Bash",
        ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
        ".xml": "XML", ".toml": "TOML", ".ini": "INI",
        ".md": "Markdown", ".rst": "reStructuredText",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".vue": "Vue", ".svelte": "Svelte",
        ".dockerfile": "Dockerfile", "Dockerfile": "Dockerfile",
        ".proto": "Protobuf", ".graphql": "GraphQL",
        ".env": "Environment", ".lock": "Lock File",
    }
    _, ext = os.path.splitext(file_path)
    base = os.path.basename(file_path)
    if "Dockerfile" in base:
        return "Dockerfile"
    if base.startswith(".env"):
        return "Environment"
    return ext_map.get(ext, "Unknown")


def compute_file_risk(file_path: str) -> Tuple[float, List[str]]:
    """Compute risk score 0.0–1.0 for a file based on path heuristics."""
    reasons: List[str] = []
    score = 0.0
    lower = file_path.lower()

    # High-risk path keywords
    risk_keywords = {
        "auth": 0.6, "password": 0.8, "secret": 0.8, "credential": 0.9,
        "token": 0.7, "key": 0.5, "deploy": 0.6, "prod": 0.5,
        "database": 0.4, "migration": 0.5, "admin": 0.3,
        "payment": 0.6, "billing": 0.6, "login": 0.4,
        ".env": 0.7, "firewall": 0.5, "cert": 0.5,
        "delete": 0.3, "drop": 0.4, "backup": 0.2,
    }
    for keyword, weight in risk_keywords.items():
        if keyword in lower:
            score = max(score, weight)
            if weight >= 0.5 and keyword not in [r for r in reasons]:
                reasons.append(f"Contains '{keyword}' in path")

    # Configuration files
    config_patterns = ["config", "conf", "setting", ".env", "pyproject.toml",
                        "package.json", "requirements", "docker-compose"]
    for pat in config_patterns:
        if pat in lower and pat not in [r for r in reasons]:
            score = max(score, 0.2)
            reasons.append(f"Configuration file: {pat}")
            break

    return min(score, 1.0), reasons


def split_into_modules(root: str, files: List[str]) -> Dict[str, List[str]]:
    """Group files into modules based on directory depth."""
    modules: Dict[str, List[str]] = {}
    root_path = Path(root).resolve()

    for file_path in files:
        rel = os.path.relpath(file_path, root)
        parts = Path(rel).parts

        # Module = top-level directory, or root-level file → "root"
        if len(parts) <= 1:
            module_name = "root"
        else:
            module_name = parts[0]

        if module_name not in modules:
            modules[module_name] = []
        modules[module_name].append(rel)

    return modules


def scan_project(project_root: str) -> ProjectSemanticMap:
    """Scan a local project and produce a ProjectSemanticMap."""
    root = Path(project_root).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {project_root}")

    # Walk files
    all_files: List[str] = []
    language_counts: Dict[str, int] = {}
    total_lines = 0

    for dirpath, dirnames, filenames in os.walk(str(root)):
        # Modify dirnames in-place to skip ignored dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, str(root))
            # Skip ignored patterns
            if any(fn.endswith(pat.replace("*", "")) for pat in IGNORE_FILES if "*" not in pat):
                continue
            if fn.endswith(".pyc") or fn.startswith("."):
                continue
            all_files.append(fp)

    # Count lines
    for fp in all_files:
        try:
            with open(fp, "r", errors="ignore") as f:
                total_lines += sum(1 for _ in f)
        except (OSError, IOError):
            pass

    # Group into modules
    module_map = split_into_modules(str(root), all_files)

    modules: List[ModuleCard] = []
    for mod_name, mod_files in sorted(module_map.items()):
        file_entries: List[FileEntry] = []
        mod_risk = 0.0
        for rel_fp in mod_files:
            abs_fp = os.path.join(str(root), rel_fp)
            try:
                stat = os.stat(abs_fp)
                lang = guess_language(rel_fp)
                risk, reasons = compute_file_risk(rel_fp)
                mod_risk = max(mod_risk, risk)

                size = stat.st_size
                mtime = str(stat.st_mtime)
                fe = FileEntry(
                    path=rel_fp,
                    language=lang,
                    size_bytes=size,
                    last_modified=mtime,
                    risk_score=risk,
                    risk_reasons=reasons,
                )
                file_entries.append(fe)

                # Count language
                if lang not in language_counts:
                    language_counts[lang] = 0
                language_counts[lang] += 1
            except (OSError, IOError):
                continue

        # Module-level risk
        risk_level = RiskLevel.UNKNOWN
        if mod_risk >= 0.7:
            risk_level = RiskLevel.HIGH
        elif mod_risk >= 0.4:
            risk_level = RiskLevel.MEDIUM
        elif mod_risk >= 0.1:
            risk_level = RiskLevel.LOW

        mc = ModuleCard(
            name=mod_name,
            path=os.path.join(str(root), mod_name) if mod_name != "root" else str(root),
            files=file_entries,
            risk_score=mod_risk,
            risk_level=risk_level,
            description=f"Module: {mod_name} ({len(file_entries)} files)",
        )
        modules.append(mc)

    # Build dependency edges (simple: detect cross-module imports)
    dependency_edges: List[DependencyEdge] = []
    if modules:
        mod_names = {m.name for m in modules}
        for mod in modules:
            for fe in mod.files:
                abs_fp = os.path.join(str(root), fe.path)
                try:
                    with open(abs_fp, "r", errors="ignore") as f:
                        content = f.read()
                except (OSError, IOError):
                    continue
                # Simple import detection
                for target in mod_names:
                    if target == mod.name:
                        continue
                    patterns = [
                        f"import {target}",
                        f"from {target}",
                        f"require('{target}')",
                        f"require(\"{target}\")",
                        f"import '{target}'",
                        f'import "{target}"',
                    ]
                    for pat in patterns:
                        if pat in content:
                            dependency_edges.append(DependencyEdge(
                                source_module=mod.name,
                                target_module=target,
                            ))
                            break

    # Fill in dependents
    for edge in dependency_edges:
        for mod in modules:
            if mod.name == edge.target_module:
                if edge.source_module not in mod.dependents:
                    object.__setattr__(mod, "dependents", list(set(mod.dependents + [edge.source_module])))
            if mod.name == edge.source_module:
                if edge.target_module not in mod.dependencies:
                    object.__setattr__(mod, "dependencies", list(set(mod.dependencies + [edge.target_module])))

    return ProjectSemanticMap(
        project_name=root.name,
        project_root=str(root),
        modules=modules,
        dependency_graph=dependency_edges,
        total_files=len(all_files),
        total_lines=total_lines,
        languages=language_counts,
        scanned_at=now_iso(),
    )


def get_file_count(project_root: str) -> int:
    """Quick file count without building full semantic map."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for fn in filenames:
            if not fn.startswith(".") and not fn.endswith(".pyc"):
                count += 1
    return count


def get_language_breakdown(project_root: str) -> Dict[str, int]:
    """Quick language breakdown without building full map."""
    counts: Dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fn in filenames:
            lang = guess_language(fn)
            counts[lang] = counts.get(lang, 0) + 1
    return counts
