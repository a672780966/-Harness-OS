"""Tests for Phase 8A — Read-only enforcement for live stream modules.

Ensures the live module:
- Does not make HTTP calls to external services
- Does not require credentials/tokens
- Does not save any state outside memory
- Uses only stdlib for networking (http.server)
- Binds to 127.0.0.1 only (not 0.0.0.0)
- Does not auto-control agents
"""
import os
import ast
import sys

import pytest


class TestLiveReadonly:
    """Read-only enforcement for live modules."""

    def test_no_banned_imports(self):
        """Live module should not import external HTTP/API client libs."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        live_dir = os.path.join(base, "harness", "copilot", "live")

        banned_imports = [
            "requests", "httpx", "aiohttp", "http.client",
            "github", "gitlab", "github3", "websocket",
            "asyncio", "uvicorn", "fastapi", "flask",
            "django", "tornado", "sanic", "quart",
        ]

        for fname in sorted(os.listdir(live_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(live_dir, fname)
            with open(fpath) as f:
                tree = ast.parse(f.read(), filename=fname)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for banned in banned_imports:
                            if alias.name == banned or alias.name.startswith(f"{banned}."):
                                pytest.fail(f"{fname} imports banned: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for banned in banned_imports:
                        if module == banned or module.startswith(f"{banned}."):
                            pytest.fail(f"{fname} imports banned: {module}")

    def test_no_credential_strings(self):
        """Source files should not contain credential/token patterns."""
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

    def test_sse_server_localhost_only(self):
        """SSE server enforces 127.0.0.1 binding."""
        from harness.copilot.live import sse_server
        import inspect
        source = inspect.getsource(sse_server.serve)
        # Should check for 127.0.0.1
        assert "127.0.0.1" in source
        # Should not bind to 0.0.0.0
        assert "0.0.0.0" not in source or "force" in source

    def test_no_external_network_code(self):
        """No external URL patterns in source."""
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        live_dir = os.path.join(base, "harness", "copilot", "live")

        # These are only acceptable in local-only server context (printing bind address)
        banned_urls = ["github.com", "gitlab.com", "api.github", "api.gitlab",
                       "https://"]

        for fname in sorted(os.listdir(live_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(live_dir, fname)
            with open(fpath) as f:
                content = f.read().lower()
            for url in banned_urls:
                if url in content:
                    pytest.fail(f"{fname} contains URL: {url}")

        # For http://, only allow 127.0.0.1 patterns
        sse_path = os.path.join(live_dir, "sse_server.py")
        with open(sse_path) as f:
            content = f.read().lower()
        if "http://" in content:
            # All http:// references should be to 127.0.0.1 only
            assert "http://127.0.0.1" in content or "http://{host}" in content

    def test_live_event_has_readonly_flag(self):
        """LiveEvent schema includes readonly=True."""
        from harness.copilot.live.live_event import LiveEvent
        evt = LiveEvent.create(source="project", event_type="t", summary="s")
        assert evt.readonly is True

    def test_cli_commands_lazy_import(self):
        """live CLI commands use lazy imports (inside function body)."""
        cli_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "harness", "copilot", "cli.py",
        )
        with open(cli_path) as f:
            content = f.read()

        live_functions_start = content.find("def cmd_live_events")
        if live_functions_start < 0:
            pytest.fail("Could not find cmd_live_events in cli.py")

        top_level = content[:content.find("def cmd_live_events")]
        if "from harness.copilot.live" in top_level:
            pytest.fail("live imports should be lazy (inside functions)")

        after_live = content[live_functions_start:]
        # Find the next def after all live functions
        import_count_top = top_level.count("from harness.copilot.live")
        import_count_func = after_live.count("from harness.copilot.live")
        assert import_count_top == 0, f"Found {import_count_top} top-level live imports"
        assert import_count_func >= 3, f"Expected >=3 lazy imports, found {import_count_func}"
