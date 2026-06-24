"""Tests: Config schema, defaults, and security-sensitive key detection."""

from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.config.schema import (
    HarnessConfig,
    ProviderConfig,
    WorkspaceConfig,
    RuntimeConfig,
    CopilotConfig,
    SecurityConfig,
    SECURITY_SENSITIVE_KEYS,
    SCHEMA_VERSION,
)


class TestSchemaDefaults:
    def test_default_version(self):
        assert HarnessConfig.defaults().version == SCHEMA_VERSION

    def test_default_readonly(self):
        cfg = HarnessConfig.defaults()
        assert cfg.runtime.readonly_default is True

    def test_default_no_external_api(self):
        cfg = HarnessConfig.defaults()
        assert cfg.runtime.allow_external_api is False

    def test_default_no_save_credentials(self):
        cfg = HarnessConfig.defaults()
        assert cfg.security.save_credentials is False

    def test_default_no_agent_control(self):
        cfg = HarnessConfig.defaults()
        assert cfg.security.allow_agent_control is False

    def test_default_provider_mode_readonly(self):
        cfg = HarnessConfig.defaults()
        assert cfg.provider.mode == "readonly"

    def test_default_long_phase_disabled_when_degraded(self):
        cfg = HarnessConfig.defaults()
        assert cfg.provider.long_phase_allowed_when_degraded is False

    def test_default_format_markdown(self):
        cfg = HarnessConfig.defaults()
        assert cfg.copilot.default_format == "markdown"


class TestSecuritySensitiveKeys:
    def test_save_credentials_in_keys(self):
        assert "save_credentials" in SECURITY_SENSITIVE_KEYS

    def test_allow_agent_control_in_keys(self):
        assert "allow_agent_control" in SECURITY_SENSITIVE_KEYS

    def test_allow_external_api_in_keys(self):
        assert "allow_external_api" in SECURITY_SENSITIVE_KEYS


class TestConfigMerge:
    def test_merge_overrides_workspace(self):
        base = HarnessConfig.defaults()
        override = HarnessConfig.defaults()
        override.workspace.root = "/custom/path"
        merged = base.merge(override)
        assert merged.workspace.root == "/custom/path"

    def test_merge_preserves_defaults(self):
        base = HarnessConfig.defaults()
        override = HarnessConfig.defaults()
        merged = base.merge(override)
        assert merged.copilot.default_format == "markdown"
        assert merged.security.save_credentials is False

    def test_merge_partial_provider(self):
        base = HarnessConfig.defaults()
        base.provider.mode = "fallback"
        override = HarnessConfig.defaults()
        merged = base.merge(override)
        # Override wins (defaults are considered set values)
        assert merged.provider.mode == "readonly"

    def test_merge_partial_provider_override_wins(self):
        base = HarnessConfig.defaults()
        override = HarnessConfig.defaults()
        override.provider.mode = "fallback"
        merged = base.merge(override)
        # Override value wins
        assert merged.provider.mode == "fallback"
