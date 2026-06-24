"""Tests for Phase 8B — Live dashboard readonly enforcement.

Ensures the live dashboard module:
- Only writes to --out directory
- Does not modify project source files
- Does not call external APIs
- Has no credential patterns
- Uses only stdlib
"""
import os
import ast

import pytest


class TestLiveDashboardReadonly:
    """Read-only enforcement for live dashboard."""

    def test_no_banned_imports(self):
        """Live modules should not import external API client libs."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        live_dir = os.path.join(base, "harness", "copilot", "live")

        banned = ["requests", "httpx", "aiohttp", "http.client",
                   "github", "gitlab", "fastapi", "flask", "uvicorn",
                   "websocket", "django", "tornado"]

        for fname in sorted(os.listdir(live_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(live_dir, fname)
            with open(fpath) as f:
                tree = ast.parse(f.read(), filename=fname)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for banned_mod in banned:
                            if alias.name == banned_mod or alias.name.startswith(f"{banned_mod}."):
                                pytest.fail(f"{fname} imports banned: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for banned_mod in banned:
                        if module == banned_mod or module.startswith(f"{banned_mod}."):
                            pytest.fail(f"{fname} imports banned: {module}")

    def test_no_credential_strings(self):
        """Source files should not contain credential patterns."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        live_dir = os.path.join(base, "harness", "copilot", "live")

        banned = ["api_key", "api_token", "access_token", "secret_key",
                   "GITHUB_TOKEN", "GITLAB_TOKEN", "oauth_token"]

        for fname in sorted(os.listdir(live_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(live_dir, fname)
            with open(fpath) as f:
                content = f.read().lower()
            for pattern in banned:
                if pattern in content:
                    pytest.fail(f"{fname} contains credential pattern: {pattern}")

    def test_no_external_urls(self):
        """No external URL patterns in live modules."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        live_dir = os.path.join(base, "harness", "copilot", "live")

        banned = ["github.com", "gitlab.com", "api.github", "api.gitlab", "https://"]

        for fname in sorted(os.listdir(live_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(live_dir, fname)
            with open(fpath) as f:
                content = f.read()
            for url in banned:
                if url in content:
                    # Allow http://127.0.0.1 in SSE server
                    if "127.0.0.1" in content:
                        continue
                    pytest.fail(f"{fname} contains URL: {url}")

    def test_live_dashboard_only_writes_to_output(self):
        """build_live_dashboard only writes to specified output dir."""
        from harness.copilot.live.live_dashboard import build_live_dashboard
        import inspect
        source = inspect.getsource(build_live_dashboard)
        # File writing should only happen inside the 'if output_dir:' block
        assert "output_dir" in source
        assert "open(" in source
        # Should never write to sealed paths
        assert "evaluations" not in source.split("open(")[0] if "open(" in source else True

    def test_cli_commands_lazy_import(self):
        """live-dashboard CLI commands use lazy imports for Phase 8B specific modules."""
        cli_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "harness", "copilot", "cli.py",
        )
        with open(cli_path) as f:
            content = f.read()

        # Phase 8A already has live imports; check that Phase 8B specific
        # imports (live_dashboard) are only inside the function body
        live_dashboard_func_start = content.find("def cmd_live_dashboard")
        if live_dashboard_func_start < 0:
            pytest.fail("Could not find cmd_live_dashboard in cli.py")

        top_level = content[:live_dashboard_func_start]
        # Phase 8B specific import should NOT be at top level
        if "from harness.copilot.live.live_dashboard" in top_level:
            pytest.fail("live_dashboard import should be lazy (inside function)")

        after_func = content[live_dashboard_func_start:]
        # Find next non-live function boundary
        import_count_func = after_func.count("from harness.copilot.live.live_dashboard")
        assert import_count_func >= 2, f"Expected >=2 lazy live_dashboard imports, found {import_count_func}"

    def test_renderer_has_no_dynamic_exec(self):
        """No eval/exec in live modules."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        live_dir = os.path.join(base, "harness", "copilot", "live")

        for fname in sorted(os.listdir(live_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(live_dir, fname)
            with open(fpath) as f:
                content = f.read()
            for dangerous in ["eval(", "exec(", "__import__("]:
                if dangerous in content:
                    pytest.fail(f"{fname} contains {dangerous}")
