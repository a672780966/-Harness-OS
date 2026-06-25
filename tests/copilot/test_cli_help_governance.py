"""Tests: CLI help governance — docstring command catalog and read-only claims.

Verifies COP-1 and COP-2 requirements:
- Module docstring lists 36+ argparse-registered copilot commands.
- No unqualified all-commands-read-only claim.
- Explicit opt-in write/network exceptions documented.
"""

from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.copilot import cli


_CLI_DOCSTRING = cli.__doc__ or ""


class TestCLIGovernanceDocstring:
    def test_docstring_exists(self):
        assert _CLI_DOCSTRING, "CLI module must have a docstring"

    def test_no_unqualified_read_only_claim(self):
        """COP-2: No blanket 'All commands are read-only' claim."""
        lower = _CLI_DOCSTRING.lower()
        assert "all commands are read-only" not in lower, (
            "Must not claim all commands are read-only unconditionally"
        )
        assert "are read-only by default" in lower or (
            "read-only by default" in lower
        ), "Should say 'read-only by default'"

    def test_read_only_by_default_qualified(self):
        """COP-2: Documented as read-only by default with exceptions."""
        assert "(WRITE)" in _CLI_DOCSTRING or "WRITE" in _CLI_DOCSTRING, (
            "Should document WRITE opt-in operations"
        )
        assert "(NETWORK)" in _CLI_DOCSTRING or "NETWORK" in _CLI_DOCSTRING, (
            "Should document NETWORK opt-in operations"
        )

    def test_write_operations_listed(self):
        """COP-2: Key write operations are explicitly documented."""
        assert "pr-draft" in _CLI_DOCSTRING, "pr-draft should be documented"
        assert "config init" in _CLI_DOCSTRING, "config init should be documented"
        assert "loop setup" in _CLI_DOCSTRING, "loop setup should be documented"
        assert "loop init" in _CLI_DOCSTRING, "loop init should be documented"
        assert "loop run" in _CLI_DOCSTRING, "loop run should be documented"

    def test_network_operations_listed(self):
        """COP-2: Network operations are explicitly documented."""
        assert "live-server" in _CLI_DOCSTRING, "live-server should be documented"
        assert "preview" in _CLI_DOCSTRING, "preview should be documented"

    def test_at_least_36_commands_documented(self):
        """COP-1: Docstring catalogs 36+ commands."""
        lines = _CLI_DOCSTRING.split("\n")
        # Count lines starting with "  harness copilot" or "  harness copilot"
        cmd_lines = [
            l.strip() for l in lines
            if l.strip().startswith("harness copilot") and not l.strip().startswith("harness copilot #")
        ]
        assert len(cmd_lines) >= 36, (
            f"Expected >=36 command lines in docstring, got {len(cmd_lines)}"
        )

    def test_core_read_only_commands_present(self):
        """COP-1: Core read-only commands must appear."""
        core = [
            "inspect",
            "diff-summary",
            "task-card",
            "readiness",
            "agent-state",
            "pr-pack",
            "pr-comment",
            "live-events",
            "live-dashboard",
            "provider-status",
            "config show",
            "config path",
            "config validate",
            "doctor",
            "version",
            "dashboard",
            "modules",
        ]
        for cmd in core:
            assert cmd in _CLI_DOCSTRING, f"Expected '{cmd}' in docstring"

    def test_config_subcommands_documented(self):
        """COP-1: All config subcommands are listed."""
        for sub in ("show", "path", "validate", "init"):
            assert f"config {sub}" in _CLI_DOCSTRING, (
                f"Expected 'config {sub}' in docstring"
            )

    def test_loop_subcommands_documented(self):
        """COP-1: Loop subcommands are listed."""
        for sub in ("doctor", "suggest", "setup", "init", "run"):
            assert f"loop {sub}" in _CLI_DOCSTRING, (
                f"Expected 'loop {sub}' in docstring"
            )

    def test_docstring_mentions_governance(self):
        """Docstring has governance context about read-only/write/network."""
        lower = _CLI_DOCSTRING.lower()
        assert "read-only" in lower
        assert "opt-in" in lower or "explicit" in lower


class TestCLIArgparseRegistrations:
    """Verify argparse has >=36 registered commands (COP-1)."""

    def test_at_least_36_parsers_registered(self):
        """At least 36 add_parser calls in cli.py."""
        import ast
        with open(cli.__file__) as f:
            tree = ast.parse(f.read())
        count = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_parser"
        )
        assert count >= 36, (
            f"Expected >=36 argparse add_parser calls, got {count}"
        )
