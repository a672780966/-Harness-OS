"""Tests: project scanner file type recognition.

Verifies:
- TypeScript, React TSX, Shell, YAML, Docker files are recognized
- Module risk defaults to LOW instead of UNKNOWN for files with no risk keywords
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.copilot.project_scanner import (
    guess_language,
    compute_file_risk,
    scan_project,
    split_into_modules,
)
from harness.copilot.schemas import RiskLevel


class TestGuessLanguage:
    def test_ts_recognized(self):
        assert guess_language("component.ts") == "TypeScript"

    def test_tsx_recognized(self):
        assert guess_language("Component.tsx") == "TypeScript React"

    def test_jsx_recognized(self):
        assert guess_language("Component.jsx") == "JavaScript React"

    def test_mjs_recognized(self):
        assert guess_language("module.mjs") == "JavaScript"

    def test_sh_recognized(self):
        assert guess_language("deploy.sh") == "Shell"

    def test_bash_recognized(self):
        assert guess_language("build.bash") == "Bash"

    def test_yml_recognized(self):
        assert guess_language("config.yml") == "YAML"

    def test_yaml_recognized(self):
        assert guess_language("config.yaml") == "YAML"

    def test_toml_recognized(self):
        assert guess_language("config.toml") == "TOML"

    def test_dockerfile_recognized(self):
        assert guess_language("Dockerfile") == "Dockerfile"

    def test_dockerfile_in_path(self):
        assert guess_language("docker/Dockerfile") == "Dockerfile"

    def test_env_recognized(self):
        assert guess_language(".env") == "Environment"

    def test_env_example_recognized(self):
        assert guess_language(".env.example") == "Environment"

    def test_ini_recognized(self):
        assert guess_language("setup.ini") == "INI"

    def test_unknown_fallback(self):
        assert guess_language("random.xyz") == "Unknown"

    def test_no_extension(self):
        assert guess_language("Makefile") == "Unknown"

    def test_lock_file(self):
        assert guess_language("package-lock.json") == "JSON"


class TestFileTypeScanIntegration:
    """Integration tests: scan a temp project with various file types."""

    def _create_temp_project(self, files: Dict[str, str]) -> str:
        """Create a temp dir with given files and content."""
        tmpdir = tempfile.mkdtemp()
        for rel_path, content in files.items():
            full = os.path.join(tmpdir, rel_path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w") as f:
                f.write(content)
        return tmpdir

    def test_typescript_module_identified(self):
        """Project with .ts files shows TypeScript language."""
        tmpdir = self._create_temp_project({
            "src/component.ts": "export const x = 1;",
            "src/App.tsx": "export const App = () => <div/>;",
            "package.json": "{}",
        })
        sem_map = scan_project(tmpdir)
        lang = sem_map.languages
        assert "TypeScript" in lang, f"TypeScript not in languages: {lang}"
        assert "TypeScript React" in lang, f"TypeScript React not in languages: {lang}"

    def test_shell_module_identified(self):
        """Project with .sh files shows Shell language."""
        tmpdir = self._create_temp_project({
            "scripts/build.sh": "echo build",
            "scripts/deploy.sh": "echo deploy",
            "docker-compose.yml": "version: '3'",
        })
        sem_map = scan_project(tmpdir)
        lang = sem_map.languages
        assert "Shell" in lang, f"Shell not in languages: {lang}"
        assert "YAML" in lang, f"YAML not in languages: {lang}"

    def test_module_risk_defaults_to_low(self):
        """Module with files but no risk keywords defaults to LOW, not UNKNOWN."""
        tmpdir = self._create_temp_project({
            "examples/data.json": '{"key": "value"}',
            "examples/result.json": '{"status": "ok"}',
            "docs/readme.md": "# Project",
            "config/settings.yml": "key: value",
        })
        sem_map = scan_project(tmpdir)
        for mod in sem_map.modules:
            # All modules should have at least LOW risk (not UNKNOWN)
            assert mod.risk_level != RiskLevel.UNKNOWN, (
                f"Module '{mod.name}' has UNKNOWN risk despite having files"
            )

    def test_python_module_still_high_risk_detected(self):
        """High-risk files still get HIGH risk level."""
        tmpdir = self._create_temp_project({
            "backend/deploy.py": "# deploy script",
            "backend/auth.py": "# auth module",
        })
        sem_map = scan_project(tmpdir)
        backend = next((m for m in sem_map.modules if m.name == "backend"), None)
        assert backend is not None
        assert backend.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM), (
            f"Backend module risk {backend.risk_level} should be HIGH or MEDIUM"
        )

    def test_scan_ignores_dot_dirs(self):
        """Dot directories are ignored during scanning."""
        tmpdir = self._create_temp_project({
            "src/main.py": "print('hello')",
            ".venv/lib/site-packages/pkg/__init__.py": "",
            "__pycache__/model.cpython-311.pyc": "",
        })
        sem_map = scan_project(tmpdir)
        # Should only have 1 file (src/main.py)
        assert sem_map.total_files == 1, (
            f"Expected 1 file, got {sem_map.total_files}"
        )
