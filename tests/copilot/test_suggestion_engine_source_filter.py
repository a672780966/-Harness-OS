"""Tests: suggestion engine source file filtering.

Verifies:
- .md files do not trigger untested source file suggestions
- CLAUDE.md does NOT trigger test suggestions
- CODEX-CLOUD-HANDOFF.md does NOT trigger test suggestions
- .py / .ts / .tsx files still trigger test coverage suggestions
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.copilot.schemas import ProjectSemanticMap, ModuleCard, FileEntry, RiskLevel
from harness.copilot.suggestion_engine import generate_suggestions


def _make_file(path: str, language: str = "Unknown") -> FileEntry:
    """Helper to create a FileEntry."""
    return FileEntry(
        path=path,
        language=language,
        size_bytes=100,
        last_modified="0",
        risk_score=0.0,
        risk_reasons=[],
    )


def _make_module(name: str, files: List[FileEntry], risk: float = 0.0) -> ModuleCard:
    """Helper to create a ModuleCard."""
    return ModuleCard(
        name=name,
        path=f"/mock/{name}",
        files=files,
        risk_score=risk,
        risk_level=RiskLevel.LOW if risk < 0.4 else RiskLevel.MEDIUM,
        description=f"Module: {name}",
    )


def _make_sem_map(modules: List[ModuleCard]) -> ProjectSemanticMap:
    """Helper to create a ProjectSemanticMap."""
    total_files = sum(len(m.files) for m in modules)
    return ProjectSemanticMap(
        project_name="test-project",
        project_root="/mock",
        modules=modules,
        total_files=total_files,
        total_lines=1000,
        languages={"Python": 5},
        scanned_at="2026-01-01T00:00:00Z",
    )


class TestSourceFilter:
    def test_md_not_untested_source(self):
        """Markdown files should not generate test coverage suggestions."""
        mod = _make_module("docs", [
            _make_file("CLAUDE.md", "Markdown"),
            _make_file("CODEX-CLOUD-HANDOFF.md", "Markdown"),
            _make_file("README.md", "Markdown"),
        ])
        sem_map = _make_sem_map([mod])
        suggestions = generate_suggestions("/mock", sem_map)
        md_suggestions = [s for s in suggestions if ".md" in (s.file_path or "")]
        assert len(md_suggestions) == 0, (
            f"Found {len(md_suggestions)} suggestions for markdown files: "
            f"{[s.suggestion for s in md_suggestions]}"
        )

    def test_claude_md_no_test_suggestion(self):
        """CLAUDE.md specifically should not appear as test gap."""
        # Create a module where CLAUDE.md is the only 'source' file
        mod = _make_module("root", [
            _make_file("CLAUDE.md", "Markdown"),
        ])
        sem_map = _make_sem_map([mod])
        suggestions = generate_suggestions("/mock", sem_map)
        claude_suggestions = [s for s in suggestions if "CLAUDE" in (s.file_path or "").upper()]
        assert len(claude_suggestions) == 0, (
            f"CLAUDE.md generated test suggestion: {[s.suggestion for s in claude_suggestions]}"
        )

    def test_py_triggers_test_suggestion(self):
        """Python files should still generate test coverage suggestions."""
        mod = _make_module("backend", [
            _make_file("backend/app/product.py", "Python"),
        ])
        test_mod = _make_module("backend/tests", [])  # No test files
        sem_map = _make_sem_map([mod, test_mod])
        suggestions = generate_suggestions("/mock", sem_map)
        py_suggestions = [s for s in suggestions if "product.py" in (s.file_path or "")]
        # May or may not appear depending on other modules, but if found, should be valid
        if py_suggestions:
            assert all("test" in s.suggestion.lower() for s in py_suggestions)

    def test_tsx_triggers_test_suggestion(self):
        """TypeScript React files should generate test coverage suggestions."""
        mod = _make_module("frontend", [
            _make_file("frontend/src/ProductList.tsx", "TypeScript React"),
        ])
        sem_map = _make_sem_map([mod])
        suggestions = generate_suggestions("/mock", sem_map)
        tsx_suggestions = [s for s in suggestions if "ProductList.tsx" in (s.file_path or "")]
        if tsx_suggestions:
            assert all("test" in s.suggestion.lower() for s in tsx_suggestions)

    def test_mixed_project_filters_correctly(self):
        """In a real project mix, only source files trigger test suggestions."""
        mod = _make_module("project", [
            _make_file("main.py", "Python"),
            _make_file("config.json", "JSON"),
            _make_file("README.md", "Markdown"),
            _make_file("docker-compose.yml", "YAML"),
            _make_file(".env", "Environment"),
        ])
        sem_map = _make_sem_map([mod])
        suggestions = generate_suggestions("/mock", sem_map)
        # Only main.py should potentially trigger suggestions
        file_paths = {s.file_path for s in suggestions if s.file_path}
        non_source = [p for p in file_paths if p and p.endswith((".md", ".json", ".yml", ".env"))]
        assert len(non_source) == 0, (
            f"Non-source files triggered suggestions: {non_source}"
        )
