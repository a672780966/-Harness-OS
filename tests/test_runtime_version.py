"""Tests: Runtime version — version info gathering and formatting."""

from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.runtime.version import (
    HARDCODED_VERSION,
    _get_git_tag,
    _get_git_commit,
    _get_git_branch,
    get_version_info,
    format_version,
)


class TestGitHelpers:
    def test_get_git_tag_returns_string_or_none(self):
        result = _get_git_tag()
        # In a git repo, may return a tag or None — just ensure type is correct
        assert result is None or isinstance(result, str)

    def test_get_git_commit_returns_string_or_none(self):
        result = _get_git_commit()
        # We're in a git repo, so should get a hash
        assert result is None or (isinstance(result, str) and len(result) >= 7)

    def test_get_git_branch_returns_string_or_none(self):
        result = _get_git_branch()
        assert result is None or isinstance(result, str)


class TestGetVersionInfo:
    def test_version_info_has_required_keys(self):
        info = get_version_info()
        for key in ("version", "git_tag", "git_commit", "git_branch", "hardcoded_version"):
            assert key in info, f"Missing key: {key}"

    def test_version_info_hardcoded_present(self):
        info = get_version_info()
        assert info["hardcoded_version"] == HARDCODED_VERSION

    def test_version_info_version_not_empty(self):
        info = get_version_info()
        assert len(info["version"]) > 0

    def test_version_info_git_commit_present_in_repo(self):
        info = get_version_info()
        # We're in a git repo, so commit should be available
        assert info["git_commit"] != "", "Expected git commit in a git repo"


class TestFormatVersion:
    def test_format_version_from_info(self):
        info = {
            "version": "1.0.0",
            "git_tag": "v1.0.0",
            "git_commit": "abc1234",
            "git_branch": "main",
            "hardcoded_version": "1.0.0-dev",
        }
        result = format_version(info)
        assert "Harness Copilot" in result
        assert "1.0.0" in result
        assert "abc1234" in result
        assert "main" in result

    def test_format_version_no_info_calls_get(self):
        # Should not crash when called with no args
        result = format_version()
        assert "Harness Copilot" in result

    def test_format_version_minimal(self):
        info = {
            "version": "0.0.1",
            "git_tag": "",
            "git_commit": "",
            "git_branch": "",
            "hardcoded_version": "0.0.1-dev",
        }
        result = format_version(info)
        assert "Harness Copilot" in result
        assert "0.0.1" in result
        # No git info, so no commit/branch in output
        assert "commit" not in result
