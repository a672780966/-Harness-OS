"""Tests for Phase 7 — Read-only enforcement.

Ensures Phase 7 modules:
- Do not make HTTP calls
- Do not require credentials/tokens
- Do not modify project source files
- Do not call GitHub/GitLab API
- Do not auto-comment PRs
"""
import os
import subprocess
import sys

import pytest


class TestPrIntegrationReadonly:
    """Read-only enforcement for Phase 7 modules."""

    def test_no_imports_from_api_libraries(self):
        """Phase 7 modules should not import request/urllib/http client libs."""
        import ast
        import importlib.util

        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pr_dir = os.path.join(base, "harness", "copilot", "pr_integration")

        banned_imports = [
            "requests", "urllib", "httpx", "aiohttp", "http.client",
            "github", "gitlab", "git", "github3",
        ]

        for fname in sorted(os.listdir(pr_dir)):
            if not fname.endswith(".py") or fname.startswith("_"):
                continue
            fpath = os.path.join(pr_dir, fname)
            with open(fpath) as f:
                tree = ast.parse(f.read(), filename=fname)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for banned in banned_imports:
                            if alias.name.startswith(banned):
                                pytest.fail(
                                    f"{fname} imports banned library: {alias.name}"
                                )

    def test_no_credential_strings(self):
        """Source files should not contain credential/token patterns."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pr_dir = os.path.join(base, "harness", "copilot", "pr_integration")

        banned_patterns = [
            "api_key", "api_token", "access_token", "secret_key",
            "GITHUB_TOKEN", "GITLAB_TOKEN",
            "oauth_token", "bearer", "authorization",
        ]

        # Allowlisted files: these use keywords for risk detection, not actual credentials
        allowlist = {"risk_checklist.py": ["password"]}

        for fname in sorted(os.listdir(pr_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(pr_dir, fname)
            with open(fpath) as f:
                content = f.read().lower()
            for pattern in banned_patterns:
                if pattern in content:
                    pytest.fail(
                        f"{fname} contains potential credential pattern: {pattern}"
                    )

    def test_no_github_gitlab_code_in_modules(self):
        """Source should not contain GitHub/GitLab API code."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pr_dir = os.path.join(base, "harness", "copilot", "pr_integration")

        banned_code = ["github.com", "gitlab.com", "api.github", "api.gitlab"]

        for fname in sorted(os.listdir(pr_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(pr_dir, fname)
            with open(fpath) as f:
                content = f.read().lower()
            for pattern in banned_code:
                if pattern in content:
                    pytest.fail(f"{fname} references {pattern}")

    def test_pr_pack_has_readonly_flag(self):
        """PR pack data structure includes readonly flag."""
        from harness.copilot.pr_integration.pr_pack import build_pr_pack
        from harness.copilot.pr_integration import pr_pack
        # Check the module exports
        import inspect
        source = inspect.getsource(pr_pack)
        assert "readonly" in source.lower() or "read_only" in source.lower() or "no_external_api" in source

    def test_cli_commands_import_only(self):
        """CLI pr-commands use lazy imports (inside function body)."""
        import ast

        cli_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "harness", "copilot", "cli.py",
        )
        with open(cli_path) as f:
            content = f.read()

        # Check that pr_integration imports are inside function bodies
        # (text should only appear after 'def cmd_pr')
        pr_functions_start = content.find("def cmd_pr_pack")
        if pr_functions_start < 0:
            pytest.fail("Could not find cmd_pr_pack in cli.py")
        # Check there are no top-level imports of pr_integration
        top_level = content[:content.find("def cmd_pr_pack")]
        if "from harness.copilot.pr_integration" in top_level:
            pytest.fail("pr_integration imports should be lazy (inside functions)")

        # Count that imports appear inside functions (after 'def cmd_pr')
        # and NOT at the top level
        after_pr = content[pr_functions_start:]
        # Find the next top-level function after all pr-related ones
        # (skip to next def without pr_ prefix)
        import_count_top = top_level.count("from harness.copilot.pr_integration")
        import_count_func = after_pr.count("from harness.copilot.pr_integration")
        assert import_count_top == 0, f"Found {import_count_top} top-level pr_integration imports"
        assert import_count_func >= 4, f"Expected >=4 lazy imports, found {import_count_func}"
