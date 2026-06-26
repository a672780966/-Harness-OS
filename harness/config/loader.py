"""Config loader — load YAML config files into HarnessConfig dataclass.

Supports:
  - YAML parsing with PyYAML (preferred) or JSON fallback
  - Schema version validation
  - Partial configs (missing sections use defaults)
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional, Tuple

from .schema import (
    HarnessConfig,
    WorkspaceConfig,
    RuntimeConfig,
    ProviderConfig,
    CopilotConfig,
    SecurityConfig,
    SCHEMA_VERSION,
)


def load_config_file(file_path: str) -> HarnessConfig:
    """Load a single config file, returning a HarnessConfig.

    Missing file → returns default config (no error).
    Invalid content → prints warning, returns default config.
    """
    if not os.path.isfile(file_path):
        return HarnessConfig.defaults()

    try:
        raw = _parse_file(file_path)
    except Exception as e:
        print(f"Warning: failed to parse config '{file_path}': {e}", file=sys.stderr)
        return HarnessConfig.defaults()

    return _parse_raw(raw)


def _parse_file(file_path: str) -> Dict[str, Any]:
    """Parse a YAML or JSON file into a dict."""
    ext = os.path.splitext(file_path)[1].lower()
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if ext in (".yaml", ".yml"):
        # Try PyYAML first, fall back to JSON
        try:
            import yaml
            parsed = yaml.safe_load(content)
            if isinstance(parsed, dict):
                return parsed
            return {}
        except ImportError:
            # No PyYAML — try strict YAML-by-JSON subset
            return _parse_as_json_strict(content)
        except Exception:
            return {}
    elif ext == ".json":
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
            return {}
        except json.JSONDecodeError:
            return {}
    else:
        # No extension — try YAML, then JSON
        try:
            import yaml
            parsed = yaml.safe_load(content)
            if isinstance(parsed, dict):
                return parsed
        except (ImportError, Exception):
            pass
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {}


def _parse_as_json_strict(content: str) -> Dict[str, Any]:
    """Strict JSON parsing for when PyYAML is not available."""
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _parse_bool(value: Any, default: bool = False) -> bool:
    """Robust boolean parsing from config-sourced values.

    Handles bool, int, and string representations.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return default


def _parse_raw(raw: Dict[str, Any]) -> HarnessConfig:
    """Convert a raw dict (from YAML/JSON) into a HarnessConfig."""
    cfg = HarnessConfig.defaults()

    # Version guard
    ver = raw.get("version", 1)
    if not isinstance(ver, int) or ver > SCHEMA_VERSION:
        print(
            f"Warning: config version {ver} > schema version {SCHEMA_VERSION}. "
            f"Trying forward-compatible load.",
            file=sys.stderr,
        )
    cfg.version = ver if isinstance(ver, int) else SCHEMA_VERSION

    # Workspace
    ws = raw.get("workspace", {})
    if isinstance(ws, dict):
        cfg.workspace = WorkspaceConfig(
            root=str(ws.get("root", cfg.workspace.root)),
            dogfood_root=str(ws.get("dogfood_root", cfg.workspace.dogfood_root)),
            demo_output_root=str(ws.get("demo_output_root", cfg.workspace.demo_output_root)),
        )

    # Runtime
    rt = raw.get("runtime", {})
    if isinstance(rt, dict):
        cfg.runtime = RuntimeConfig(
            mode=str(rt.get("mode", cfg.runtime.mode)),
            os_hint=str(rt.get("os_hint", cfg.runtime.os_hint)),
            readonly_default=_parse_bool(rt.get("readonly_default", cfg.runtime.readonly_default)),
            allow_external_api=_parse_bool(rt.get("allow_external_api", cfg.runtime.allow_external_api)),
        )

    # Provider
    pr = raw.get("provider", {})
    if isinstance(pr, dict):
        cfg.provider = ProviderConfig(
            mode=str(pr.get("mode", cfg.provider.mode)),
            primary=str(pr.get("primary", cfg.provider.primary)),
            fallback=str(pr.get("fallback", cfg.provider.fallback)),
            connect_timeout_seconds=float(
                pr.get("connect_timeout_seconds", cfg.provider.connect_timeout_seconds)
            ),
            read_timeout_seconds=float(
                pr.get("read_timeout_seconds", cfg.provider.read_timeout_seconds)
            ),
            canary_timeout_seconds=float(
                pr.get("canary_timeout_seconds", cfg.provider.canary_timeout_seconds)
            ),
            max_retries=int(
                pr.get("max_retries", cfg.provider.max_retries)
            ),
            retry_backoff=str(
                pr.get("retry_backoff", cfg.provider.retry_backoff)
            ),
            retry_jitter=_parse_bool(
                pr.get("retry_jitter", cfg.provider.retry_jitter)
            ),
            long_phase_allowed_when_degraded=_parse_bool(
                pr.get("long_phase_allowed_when_degraded", cfg.provider.long_phase_allowed_when_degraded)
            ),
        )

    # Copilot
    cp = raw.get("copilot", {})
    if isinstance(cp, dict):
        cfg.copilot = CopilotConfig(
            default_format=str(cp.get("default_format", cfg.copilot.default_format)),
            include_live_dashboard=_parse_bool(cp.get("include_live_dashboard", cfg.copilot.include_live_dashboard)),
            include_pr_pack=_parse_bool(cp.get("include_pr_pack", cfg.copilot.include_pr_pack)),
        )

    # Security
    sc = raw.get("security", {})
    if isinstance(sc, dict):
        cfg.security = SecurityConfig(
            save_credentials=_parse_bool(sc.get("save_credentials", cfg.security.save_credentials)),
            allow_agent_control=_parse_bool(sc.get("allow_agent_control", cfg.security.allow_agent_control)),
        )

    return cfg


def write_default_global_config(force: bool = False) -> str:
    """Write the default config to ~/.harness/config.yaml.

    Args:
        force: Overwrite existing file if True.

    Returns:
        Path to the written file.

    Raises:
        FileExistsError: If config already exists and force=False.
    """
    from .paths import get_global_config_path
    path = get_global_config_path()
    if os.path.isfile(path) and not force:
        raise FileExistsError(f"Config already exists: {path}")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    cfg = HarnessConfig.defaults()
    content = _render_yaml(cfg.to_dict())
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _render_yaml(data: Dict[str, Any]) -> str:
    """Render a dict as user-friendly YAML.

    Tries PyYAML with default_flow_style=False for readability.
    Falls back to manual rendering.
    """
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except ImportError:
        pass
    # Manual fallback
    lines = [_manual_yaml_dump(data)]
    return "\n".join(lines)


def _manual_yaml_dump(data: Dict[str, Any], indent: int = 0) -> str:
    """Simple manual YAML renderer."""
    parts = []
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            parts.append(f"{prefix}{key}:")
            parts.append(_manual_yaml_dump(value, indent + 1))
        elif isinstance(value, bool):
            parts.append(f"{prefix}{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            parts.append(f"{prefix}{key}:")
            for item in value:
                parts.append(f"{prefix}- {item}")
        else:
            parts.append(f"{prefix}{key}: {value}")
    return "\n".join(parts)
