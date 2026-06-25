"""Tests: Config loader — YAML parsing, defaults, error handling."""

from __future__ import annotations

import json
import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.config.schema import HarnessConfig
from harness.config.loader import load_config_file, write_default_global_config, _parse_raw


class TestLoadConfigFile:
    def test_missing_file_returns_defaults(self):
        cfg = load_config_file("/nonexistent/path/config.yaml")
        assert isinstance(cfg, HarnessConfig)
        assert cfg.security.save_credentials is False

    def test_load_empty_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{}")
            path = f.name
        try:
            cfg = load_config_file(path)
            assert isinstance(cfg, HarnessConfig)
            assert cfg.runtime.readonly_default is True
        finally:
            os.unlink(path)

    def test_load_yaml_config(self):
        raw = {
            "workspace": {"root": "/custom/workspace"},
            "security": {"save_credentials": False},
        }
        content = _yaml_dump(raw)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            cfg = load_config_file(path)
            assert cfg.workspace.root == "/custom/workspace"
            assert cfg.runtime.readonly_default is True  # from defaults
        finally:
            os.unlink(path)

    def test_load_json_config(self):
        data = json.dumps({
            "runtime": {"mode": "remote"},
            "provider": {"mode": "fallback"},
        })
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            cfg = load_config_file(path)
            assert cfg.runtime.mode == "remote"
            assert cfg.provider.mode == "fallback"
            assert cfg.security.save_credentials is False  # default
        finally:
            os.unlink(path)

    def test_bad_yaml_returns_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("{{{bad: yaml: file}}}")
            path = f.name
        try:
            cfg = load_config_file(path)
            assert isinstance(cfg, HarnessConfig)
        finally:
            os.unlink(path)


class TestWriteDefaultConfig:
    def test_write_default_creates_file(self):
        tmpdir = tempfile.mkdtemp()
        orig_expand = os.path.expanduser
        try:
            os.path.expanduser = lambda p: os.path.join(tmpdir, ".harness")
            path = write_default_global_config()
            assert os.path.isfile(path)
            with open(path) as f:
                content = f.read()
            assert "readonly_default: true" in content or "readonly_default" in content
        finally:
            os.path.expanduser = orig_expand
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_write_default_exists_raises(self):
        tmpdir = tempfile.mkdtemp()
        orig_expand = os.path.expanduser
        try:
            os.path.expanduser = lambda p: os.path.join(tmpdir, ".harness")
            write_default_global_config()  # first write
            import pytest
            with pytest.raises(FileExistsError):
                write_default_global_config()  # second write without force
        finally:
            os.path.expanduser = orig_expand
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestParseRaw:
    def test_empty_dict(self):
        cfg = _parse_raw({})
        assert cfg.runtime.readonly_default is True

    def test_security_overrides(self):
        cfg = _parse_raw({"security": {"save_credentials": True}})
        assert cfg.security.save_credentials is True

    def test_bad_section_ignored(self):
        cfg = _parse_raw({"nonexistent": {"foo": "bar"}})
        assert cfg.runtime.readonly_default is True

    def test_provider_timeout_retry_parsed(self):
        """Provider timeout/retry fields are parsed correctly."""
        cfg = _parse_raw({
            "provider": {
                "connect_timeout_seconds": 5.0,
                "read_timeout_seconds": 30.0,
                "max_retries": 7,
                "retry_backoff": "linear",
                "retry_jitter": False,
                "canary_timeout_seconds": 60.0,
                "long_phase_allowed_when_degraded": True,
            }
        })
        assert cfg.provider.connect_timeout_seconds == 5.0
        assert cfg.provider.read_timeout_seconds == 30.0
        assert cfg.provider.max_retries == 7
        assert cfg.provider.retry_backoff == "linear"
        assert cfg.provider.retry_jitter is False
        assert cfg.provider.canary_timeout_seconds == 60.0
        assert cfg.provider.long_phase_allowed_when_degraded is True

    def test_provider_defaults_when_missing(self):
        """Missing provider fields use defaults."""
        cfg = _parse_raw({"provider": {}})
        assert cfg.provider.connect_timeout_seconds == 10.0
        assert cfg.provider.max_retries == 3
        assert cfg.provider.retry_backoff == "exponential"
        assert cfg.provider.retry_jitter is True
        assert cfg.provider.long_phase_allowed_when_degraded is False

    def test_load_json_config_provider_fields(self):
        """JSON config with provider timeout/retry fields is parsed."""
        import json, tempfile
        data = json.dumps({
            "provider": {
                "connect_timeout_seconds": 15.0,
                "read_timeout_seconds": 120.0,
                "max_retries": 5,
                "retry_backoff": "exponential",
                "retry_jitter": True,
                "long_phase_allowed_when_degraded": False,
            }
        })
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            cfg = load_config_file(path)
            assert cfg.provider.connect_timeout_seconds == 15.0
            assert cfg.provider.read_timeout_seconds == 120.0
            assert cfg.provider.max_retries == 5
            assert cfg.provider.long_phase_allowed_when_degraded is False
        finally:
            os.unlink(path)


def _yaml_dump(data: dict, indent: int = 0) -> str:
    """Simple YAML-like dumper for test data."""
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{'  ' * indent}{key}:")
            lines.append(_yaml_dump(value, indent + 1))
        elif isinstance(value, bool):
            lines.append(f"{'  ' * indent}{key}: {str(value).lower()}")
        else:
            lines.append(f"{'  ' * indent}{key}: {value}")
    return "\n".join(lines)
