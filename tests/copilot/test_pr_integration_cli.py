"""Tests for Phase 7 — PR integration CLI commands."""
import os
import sys
import json
import tempfile

import pytest

from harness.copilot.pr_integration.pr_pack import build_pr_pack, export_pr_pack


class TestPrIntegrationCLI:
    """CLI command structure and basic functionality."""

    def test_pr_pack_functions_exist(self):
        """The module exposes expected functions."""
        from harness.copilot.pr_integration.pr_pack import (
            build_pr_pack, build_pr_pack_from_loop, export_pr_pack,
        )
        assert callable(build_pr_pack)
        assert callable(build_pr_pack_from_loop)
        assert callable(export_pr_pack)

    def test_cli_parsers_registered(self):
        """CLI subparsers for Phase 7 commands are registered."""
        from harness.copilot.cli import main as cli_main
        from harness.copilot.cli import cmd_pr_pack, cmd_pr_pack_from_loop
        from harness.copilot.cli import cmd_pr_comment, cmd_pr_comment_from_loop
        assert callable(cmd_pr_pack)
        assert callable(cmd_pr_pack_from_loop)
        assert callable(cmd_pr_comment)
        assert callable(cmd_pr_comment_from_loop)

    def test_export_pr_pack_creates_files(self):
        """export_pr_pack creates expected files."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_pr_pack(pack, tmpdir)
            assert result["success"] is True
            file_count = len(result["files"])
            # Should have 9 files (8 md + 1 json)
            assert file_count >= 9

    def test_export_files_content(self):
        """Each exported file has non-empty content."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_pr_pack(pack, tmpdir)
            for fp in result["files"]:
                with open(fp) as f:
                    content = f.read()
                assert len(content) > 0, f"Empty file: {fp}"

    def test_export_json_valid(self):
        """Exported pr_pack.json is valid JSON."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_pr_pack(pack, tmpdir)
            json_path = [f for f in result["files"] if f.endswith(".json")][0]
            with open(json_path) as f:
                parsed = json.load(f)
            assert "pack_version" in parsed
            assert "project_name" in parsed

    def test_cli_pr_comment_imports(self):
        """pr-comment function imports work."""
        from harness.copilot.pr_integration.pr_comment_renderer import render_pr_comment
        from harness.copilot.pr_integration.pr_pack import build_pr_pack
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        md = render_pr_comment(pack, format="markdown")
        assert "PR Review Pack" in md

    def test_export_fails_on_bad_path(self):
        """export_pr_pack fails gracefully on unwritable path."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pack = build_pr_pack(project_root)
        result = export_pr_pack(pack, "/")
        assert result["success"] is False
