"""Tests: Runtime doctor — system prerequisite checks."""

from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.runtime.doctor import (
    _check_python,
    _check_git,
    _check_pytest,
    _check_os,
    run_doctor,
    doctor_summary,
)


class TestPythonCheck:
    def test_python_version_ok(self):
        result = _check_python()
        assert result["name"] == "python"
        assert result["ok"] is True  # We're running Python 3.11
        assert "3." in result["detail"]


class TestGitCheck:
    def test_git_available(self):
        result = _check_git()
        assert result["name"] == "git"
        # Git should be available in this environment
        assert isinstance(result["ok"], bool)
        assert isinstance(result["detail"], str)


class TestPytestCheck:
    def test_pytest_available(self):
        result = _check_pytest()
        assert result["name"] == "pytest"
        assert isinstance(result["ok"], bool)


class TestOSCheck:
    def test_os_returns_required_keys(self):
        result = _check_os()
        assert result["name"] == "os"
        assert "os_hint" in result
        assert result["os_hint"] in ("linux", "macos", "wsl2", "windows-native", "unknown")
        assert isinstance(result["ok"], bool)

    def test_os_detail_is_string(self):
        result = _check_os()
        assert isinstance(result["detail"], str)
        assert len(result["detail"]) > 0


class TestRunDoctor:
    def test_run_doctor_quiet_returns_list(self):
        results = run_doctor(quiet=True)
        assert isinstance(results, list)
        assert len(results) >= 7  # At least 7 checks

    def test_run_doctor_results_have_required_keys(self):
        results = run_doctor(quiet=True)
        for r in results:
            assert "name" in r
            assert "ok" in r
            assert "detail" in r
            assert isinstance(r["ok"], bool)
            assert isinstance(r["name"], str)

    def test_run_doctor_contains_expected_checks(self):
        results = run_doctor(quiet=True)
        names = [r["name"] for r in results]
        for expected in ("python", "git", "pytest", "os", "opencode"):
            assert expected in names, f"Missing check: {expected}"


class TestDoctorSummary:
    def test_summary_returns_string(self):
        summary = doctor_summary([])
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summary_includes_header(self):
        summary = doctor_summary([])
        assert "Harness Runtime Doctor" in summary

    def test_summary_all_ok(self):
        results = [
            {"name": "test1", "ok": True, "detail": "ok", "hint": ""},
            {"name": "test2", "ok": True, "detail": "ok", "hint": ""},
        ]
        summary = doctor_summary(results)
        assert "All checks passed" in summary

    def test_summary_issues_found(self):
        results = [
            {"name": "test1", "ok": True, "detail": "ok", "hint": ""},
            {"name": "test2", "ok": False, "detail": "fail", "hint": "install it"},
        ]
        summary = doctor_summary(results)
        assert "issue(s) found" in summary
        assert "test2" in summary
        assert "install it" in summary
