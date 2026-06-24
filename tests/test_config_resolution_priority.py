"""Tests: Config resolution priority — CLI > Env > Project > Global > Defaults."""

from __future__ import annotations

import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.config.resolver import resolve_config, _load_env_overrides
from harness.config.loader import write_default_global_config


class TestEnvOverrides:
    def test_env_section_key_parsing(self):
        key = _load_env_overrides.__code__  # check _env_to_key logic
        from harness.config.resolver import _env_to_key
        assert _env_to_key("HARNESS_PROVIDER_MODE") == "provider.mode"
        assert _env_to_key("HARNESS_RUNTIME_READONLY_DEFAULT") == "runtime.readonly_default"

    def test_not_harness_prefix_returns_none(self):
        from harness.config.resolver import _env_to_key
        assert _env_to_key("OTHER_VAR") is None
        assert _env_to_key("HARNESS") is None  # no underscore after prefix

    def test_env_bool_conversion(self):
        os.environ["HARNESS_PROVIDER_MODE"] = "fallback"
        try:
            overrides = _load_env_overrides()
            assert overrides.get("provider", {}).get("mode") == "fallback"
        finally:
            del os.environ["HARNESS_PROVIDER_MODE"]


class TestResolutionPriority:
    def test_defaults_used_without_files(self):
        cfg = resolve_config()
        assert cfg.runtime.readonly_default is True
        assert cfg.security.save_credentials is False

    def test_env_overrides_defaults(self):
        os.environ["HARNESS_RUNTIME_MODE"] = "remote"
        try:
            cfg = resolve_config()
            assert cfg.runtime.mode == "remote"
        finally:
            del os.environ["HARNESS_RUNTIME_MODE"]

    def test_env_bool_override(self):
        os.environ["HARNESS_RUNTIME_READONLY_DEFAULT"] = "false"
        try:
            cfg = resolve_config()
            assert cfg.runtime.readonly_default is False
        finally:
            del os.environ["HARNESS_RUNTIME_READONLY_DEFAULT"]

    def test_cli_overrides_env(self):
        os.environ["HARNESS_PROVIDER_MODE"] = "fallback"
        try:
            cfg = resolve_config(cli_overrides={"provider": {"mode": "readonly"}})
            # CLI should win
            assert cfg.provider.mode == "readonly"
        finally:
            del os.environ["HARNESS_PROVIDER_MODE"]

    def test_env_bool_false(self):
        os.environ["HARNESS_SECURITY_SAVE_CREDENTIALS"] = "true"
        try:
            cfg = resolve_config()
            assert cfg.security.save_credentials is True
        finally:
            del os.environ["HARNESS_SECURITY_SAVE_CREDENTIALS"]

    def test_project_config_overrides_global(self):
        """Test that project config overrides global config.

        This test creates both global and project config files and
        verifies the project-level value wins.
        """
        from harness.config.paths import get_global_config_path, get_project_config_path

        tmpdir = tempfile.mkdtemp()
        orig_expand = os.path.expanduser
        try:
            # Mock ~ to point at tempdir
            os.path.expanduser = lambda p: p.replace("~", tmpdir) if p.startswith("~") else p

            # Write global config
            os.makedirs(os.path.join(tmpdir, ".harness"), exist_ok=True)
            with open(os.path.join(tmpdir, ".harness", "config.yaml"), "w") as f:
                f.write("provider:\n  mode: readonly\n")

            # Write project config
            proj_dir = os.path.join(tmpdir, "myproject")
            os.makedirs(os.path.join(proj_dir, ".harness"), exist_ok=True)
            with open(os.path.join(proj_dir, ".harness", "config.yaml"), "w") as f:
                f.write("provider:\n  mode: fallback\n")

            cfg = resolve_config(project_root=proj_dir)
            assert cfg.provider.mode == "fallback", (
                f"Expected fallback from project config, got {cfg.provider.mode}"
            )
        finally:
            os.path.expanduser = orig_expand
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
