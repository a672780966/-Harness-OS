"""Tests: Config validator — safety, completeness, security checks."""

from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.config.schema import HarnessConfig
from harness.config.validator import validate_config


class TestValidateConfigDefaults:
    def test_default_config_is_valid(self):
        cfg = HarnessConfig.defaults()
        result = validate_config(cfg)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_default_config_no_security_issues(self):
        cfg = HarnessConfig.defaults()
        result = validate_config(cfg)
        assert len(result["security_issues"]) == 0

    def test_default_config_has_info(self):
        cfg = HarnessConfig.defaults()
        result = validate_config(cfg)
        assert len(result["info"]) >= 2  # global + project config paths


class TestValidateSecurity:
    def test_save_credentials_triggers_security(self):
        cfg = HarnessConfig.defaults()
        cfg.security.save_credentials = True
        result = validate_config(cfg)
        assert len(result["security_issues"]) >= 1
        assert "SECURITY" in result["security_issues"][0]

    def test_allow_agent_control_triggers_security(self):
        cfg = HarnessConfig.defaults()
        cfg.security.allow_agent_control = True
        result = validate_config(cfg)
        issues = " ".join(result["security_issues"])
        assert "SECURITY" in issues or "save_credentials" in issues or "allow_agent_control" in issues

    def test_allow_external_api_triggers_security(self):
        cfg = HarnessConfig.defaults()
        cfg.runtime.allow_external_api = True
        result = validate_config(cfg)
        assert any("SECURITY" in s for s in result["security_issues"])

    def test_long_phase_when_degraded_triggers_security(self):
        cfg = HarnessConfig.defaults()
        cfg.provider.long_phase_allowed_when_degraded = True
        result = validate_config(cfg)
        assert any("WARNING" in s or "SECURITY" in s for s in result["security_issues"])


class TestValidateWarnings:
    def test_bad_runtime_mode_warns(self):
        cfg = HarnessConfig.defaults()
        cfg.runtime.mode = "invalid_mode"
        result = validate_config(cfg)
        assert any("runtime mode" in w for w in result["warnings"])

    def test_bad_provider_mode_warns(self):
        cfg = HarnessConfig.defaults()
        cfg.provider.mode = "invalid_provider"
        result = validate_config(cfg)
        assert any("provider mode" in w for w in result["warnings"])

    def test_low_canary_timeout_warns(self):
        cfg = HarnessConfig.defaults()
        cfg.provider.canary_timeout_seconds = 1
        result = validate_config(cfg)
        assert any("canary timeout" in w for w in result["warnings"])

    def test_high_canary_timeout_warns(self):
        cfg = HarnessConfig.defaults()
        cfg.provider.canary_timeout_seconds = 600
        result = validate_config(cfg)
        assert any("canary timeout" in w for w in result["warnings"])

    def test_bad_copilot_format_warns(self):
        cfg = HarnessConfig.defaults()
        cfg.copilot.default_format = "xml"
        result = validate_config(cfg)
        assert any("copilot format" in w for w in result["warnings"])


class TestValidateErrors:
    def test_bad_schema_version_errors(self):
        cfg = HarnessConfig.defaults()
        cfg.version = -1
        result = validate_config(cfg)
        assert len(result["errors"]) >= 1
        assert "schema version" in result["errors"][0].lower()

    def test_non_int_version_errors(self):
        cfg = HarnessConfig.defaults()
        cfg.version = "abc"  # type: ignore
        result = validate_config(cfg)
        assert len(result["errors"]) >= 1
