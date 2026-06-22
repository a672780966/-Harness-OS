"""Tests for Project Scanner module."""

import os
import tempfile
from pathlib import Path
from harness.copilot.project_scanner import (
    scan_project,
    guess_language,
    compute_file_risk,
    split_into_modules,
    get_file_count,
    get_language_breakdown,
)
from harness.copilot.schemas import ProjectSemanticMap, RiskLevel


class TestGuessLanguage:
    def test_python(self):
        assert guess_language("main.py") == "Python"
        assert guess_language("src/utils.py") == "Python"

    def test_typescript(self):
        assert guess_language("index.ts") == "TypeScript"
        assert guess_language("component.tsx") == "TypeScript React"

    def test_javascript(self):
        assert guess_language("app.js") == "JavaScript"
        assert guess_language("component.jsx") == "JavaScript React"

    def test_go(self):
        assert guess_language("server.go") == "Go"

    def test_unknown(self):
        assert guess_language("file.xyz") == "Unknown"

    def test_dockerfile(self):
        assert guess_language("Dockerfile") == "Dockerfile"
        assert guess_language("docker/Dockerfile.prod") == "Dockerfile"

    def test_env(self):
        assert guess_language(".env") == "Environment"
        assert guess_language(".env.prod") == "Environment"


class TestComputeFileRisk:
    def test_no_risk(self):
        score, reasons = compute_file_risk("src/utils/helper.py")
        assert score == 0.0
        assert reasons == []

    def test_auth_risk(self):
        score, reasons = compute_file_risk("src/auth/login.py")
        assert score >= 0.5
        assert any("auth" in r.lower() for r in reasons)

    def test_secret_risk(self):
        score, reasons = compute_file_risk("config/secrets.yaml")
        assert score >= 0.7

    def test_payment_risk(self):
        score, reasons = compute_file_risk("src/payment/processor.py")
        assert score >= 0.5

    def test_config_file_risk(self):
        score, reasons = compute_file_risk(".env.production")
        assert score >= 0.2

    def test_database_risk(self):
        score, reasons = compute_file_risk("src/database/migrations/001.py")
        assert score >= 0.4


class TestSplitIntoModules:
    def test_root_level_file(self):
        files = ["/tmp/proj/README.md"]
        modules = split_into_modules("/tmp/proj", files)
        assert "root" in modules
        assert "README.md" in modules["root"]

    def test_top_level_dir_module(self):
        files = ["/tmp/proj/src/main.py", "/tmp/proj/src/utils.py", "/tmp/proj/tests/test_main.py"]
        modules = split_into_modules("/tmp/proj", files)
        assert "src" in modules
        assert "tests" in modules
        assert len(modules["src"]) == 2
        assert len(modules["tests"]) == 1

    def test_nested_files(self):
        files = ["/tmp/proj/src/auth/login.py", "/tmp/proj/src/auth/views.py"]
        modules = split_into_modules("/tmp/proj", files)
        assert "src" in modules
        assert modules["src"] == ["src/auth/login.py", "src/auth/views.py"]


class TestScanProject:
    def test_scan_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sem_map = scan_project(tmpdir)
            assert isinstance(sem_map, ProjectSemanticMap)
            assert sem_map.total_files == 0
            assert sem_map.modules == []

    def test_scan_with_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            Path(tmpdir, "README.md").write_text("# Project")
            Path(tmpdir, "src").mkdir()
            Path(tmpdir, "src", "main.py").write_text("def main():\n    pass\n")
            Path(tmpdir, "src", "auth.py").write_text("class Auth:\n    pass\n")
            Path(tmpdir, "tests").mkdir()
            Path(tmpdir, "tests", "test_main.py").write_text("def test_main():\n    pass\n")

            sem_map = scan_project(tmpdir)
            assert sem_map.total_files >= 3
            assert len(sem_map.modules) >= 2

            # Check module names
            module_names = {m.name for m in sem_map.modules}
            assert "src" in module_names
            assert "tests" in module_names or "root" in module_names

    def test_scan_ignores_node_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "node_modules").mkdir()
            Path(tmpdir, "node_modules", "lodash.js").write_text("// large lib")
            Path(tmpdir, "src").mkdir()
            Path(tmpdir, "src", "main.js").write_text("console.log('hi')")

            sem_map = scan_project(tmpdir)
            # node_modules should be skipped
            src = [m for m in sem_map.modules if m.name == "src"]
            assert len(src) == 1
            assert len(src[0].files) == 1

    def test_scan_language_counting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "main.py").write_text("x = 1")
            Path(tmpdir, "app.ts").write_text("let x = 1")
            Path(tmpdir, "style.css").write_text("body {}")

            sem_map = scan_project(tmpdir)
            assert "Python" in sem_map.languages
            assert "TypeScript" in sem_map.languages
            assert "CSS" in sem_map.languages

    def test_scan_invalid_directory(self):
        try:
            scan_project("/nonexistent/path")
            assert False, "Should have raised"
        except (NotADirectoryError, FileNotFoundError, OSError):
            pass


class TestGetFileCount:
    def test_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.py").write_text("")
            Path(tmpdir, "sub").mkdir()
            Path(tmpdir, "sub", "b.py").write_text("")
            count = get_file_count(tmpdir)
            assert count == 2

    def test_ignores_node_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.py").write_text("")
            Path(tmpdir, "node_modules").mkdir()
            Path(tmpdir, "node_modules", "big.js").write_text("")
            count = get_file_count(tmpdir)
            assert count == 1


class TestLanguageBreakdown:
    def test_breakdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.py").write_text("")
            Path(tmpdir, "b.py").write_text("")
            Path(tmpdir, "c.ts").write_text("")
            langs = get_language_breakdown(tmpdir)
            assert langs.get("Python") == 2
            assert langs.get("TypeScript") == 1
