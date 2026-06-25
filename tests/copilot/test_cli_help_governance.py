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
        # The docstring qualifies with "By default" — that is correct.
        assert "by default all commands are read-only" in lower, (
            "Must qualify the read-only claim with 'by default'"
        )
        # Ensure the unqualified phrase appears only as part of the qualified form.
        for line in _CLI_DOCSTRING.split("\n"):
            stripped = line.strip().lower()
            if stripped.startswith("all commands are read-only"):
                raise AssertionError(
                    "Found unqualified 'all commands are read-only' claim "
                    "(not prefixed by 'by default')"
                )

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
        # The governance section is present with heading or WRITE/NETWORK listings
        assert "governance:" in _CLI_DOCSTRING or (
            "WRITE exceptions" in _CLI_DOCSTRING and "NETWORK" in _CLI_DOCSTRING
        ), "Must have a governance section with WRITE and NETWORK exception docs"


class TestCliDocstringCommandSurface:
    """COP-1: Module docstring lists the registered v1.2+ copilot command surface."""

    def _get_docstring(self) -> str:
        import harness.copilot.cli as cli
        return cli.__doc__ or ""

    def test_docstring_includes_dashboard(self):
        doc = self._get_docstring()
        assert "dashboard" in doc

    def test_docstring_includes_modules(self):
        doc = self._get_docstring()
        assert "modules" in doc

    def test_docstring_includes_task_cards(self):
        doc = self._get_docstring()
        assert "task-cards" in doc or "task_cards" in doc

    def test_docstring_includes_from_loop(self):
        doc = self._get_docstring()
        assert "from-loop" in doc or "from_loop" in doc

    def test_docstring_includes_evidence(self):
        doc = self._get_docstring()
        assert "evidence" in doc

    def test_docstring_includes_repair_cards(self):
        doc = self._get_docstring()
        assert "repair-cards" in doc or "repair_cards" in doc

    def test_docstring_includes_shell(self):
        doc = self._get_docstring()
        assert "shell" in doc

    def test_docstring_includes_shell_from_loop(self):
        doc = self._get_docstring()
        assert "shell-from-loop" in doc or "shell_from_loop" in doc

    def test_docstring_includes_export_task_card(self):
        doc = self._get_docstring()
        assert "export-task-card" in doc or "export_task_card" in doc

    def test_docstring_includes_preview(self):
        doc = self._get_docstring()
        assert "preview" in doc

    def test_docstring_includes_agent_state(self):
        doc = self._get_docstring()
        assert "agent-state" in doc or "agent_state" in doc

    def test_docstring_includes_pr_pack(self):
        doc = self._get_docstring()
        assert "pr-pack" in doc or "pr_pack" in doc

    def test_docstring_includes_pr_comment(self):
        doc = self._get_docstring()
        assert "pr-comment" in doc or "pr_comment" in doc

    def test_docstring_includes_pr_draft(self):
        doc = self._get_docstring()
        assert "pr-draft" in doc or "pr_draft" in doc

    def test_docstring_includes_live_events(self):
        doc = self._get_docstring()
        assert "live-events" in doc or "live_events" in doc

    def test_docstring_includes_live_server(self):
        doc = self._get_docstring()
        assert "live-server" in doc or "live_server" in doc

    def test_docstring_includes_live_dashboard(self):
        doc = self._get_docstring()
        assert "live-dashboard" in doc or "live_dashboard" in doc

    def test_docstring_includes_provider_status(self):
        doc = self._get_docstring()
        assert "provider-status" in doc or "provider_status" in doc

    def test_docstring_includes_loop_doctor(self):
        doc = self._get_docstring()
        assert "loop doctor" in doc

    def test_docstring_includes_loop_suggest(self):
        doc = self._get_docstring()
        assert "loop suggest" in doc

    def test_docstring_includes_loop_setup(self):
        doc = self._get_docstring()
        assert "loop setup" in doc

    def test_docstring_includes_loop_init(self):
        doc = self._get_docstring()
        assert "loop init" in doc

    def test_docstring_includes_loop_run(self):
        doc = self._get_docstring()
        assert "loop run" in doc

    def test_docstring_includes_config_init(self):
        doc = self._get_docstring()
        assert "config init" in doc

    def test_docstring_includes_config_show(self):
        doc = self._get_docstring()
        assert "config show" in doc

    def test_docstring_includes_config_path(self):
        doc = self._get_docstring()
        assert "config path" in doc

    def test_docstring_includes_config_validate(self):
        doc = self._get_docstring()
        assert "config validate" in doc

    def test_docstring_includes_doctor(self):
        doc = self._get_docstring()
        assert "doctor" in doc

    def test_docstring_includes_version(self):
        doc = self._get_docstring()
        assert "version" in doc

    def test_docstring_includes_monitor(self):
        doc = self._get_docstring()
        assert "monitor" in doc

    def test_docstring_includes_monitor_loop(self):
        doc = self._get_docstring()
        assert "monitor-loop" in doc or "monitor_loop" in doc

    def test_docstring_no_stale_sync_reference(self):
        """No stale 'sync' reference in the docstring."""
        doc = self._get_docstring()
        # The word "sync" should only appear in governance context or not at all
        # It should NOT reference a stale "sync" command
        assert "sync" not in doc, "Stale sync reference found in docstring"


class TestCliGovernanceText:
    """COP-2: Governance text states commands are read-only by default and documents WRITE exceptions."""

    def _get_docstring(self) -> str:
        import harness.copilot.cli as cli
        return cli.__doc__ or ""

    def test_readonly_by_default_stated(self):
        doc = self._get_docstring()
        assert "read-only" in doc.lower()

    def test_write_exceptions_listed(self):
        doc = self._get_docstring()
        assert "WRITE" in doc
        assert "pr-pack" in doc
        assert "shell" in doc
        assert "export-task-card" in doc
        assert "loop setup" in doc or "loop init" in doc
        assert "config init" in doc

    def test_network_exceptions_listed(self):
        doc = self._get_docstring()
        assert "NETWORK" in doc
        assert "live-server" in doc
        assert "preview" in doc

    def test_write_network_exception_listed(self):
        doc = self._get_docstring()
        assert "WRITE + NETWORK" in doc or "pr-draft --create" in doc


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
