"""Tests: CLI documentation and governance claims (COP-1, COP-2).

Verifies that the CLI module docstring accurately lists the registered
v1.2+ command surface and that the governance section accurately describes
read-only defaults and WRITE/NETWORK exceptions.
"""

from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)


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
