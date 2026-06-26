"""Config resolver — resolve effective configuration from multiple sources.

Priority (highest to lowest):
  1. CLI args (passed as dict)
  2. Environment variables (HARNESS_* prefix)
  3. Project config (.harness/config.yaml)
  4. Global config (~/.harness/config.yaml)
  5. Built-in defaults (hardcoded in schema.py)
"""

from __future__ import annotations

import os
import sys
import re
from typing import Any, Dict, Optional

from .schema import HarnessConfig, ProviderConfig, WorkspaceConfig, RuntimeConfig, CopilotConfig, SecurityConfig
from .loader import _parse_file, _parse_raw
from .paths import get_global_config_path, get_project_config_path


# Environment variable prefix
_ENV_PREFIX = "HARNESS_"


def _env_to_key(env_name: str) -> Optional[str]:
    """Convert HARNESS_WORKSPACE_ROOT to workspace.root.

    Returns None if not a valid HARNESS_ prefixed variable.
    """
    if not env_name.startswith(_ENV_PREFIX):
        return None
    rest = env_name[len(_ENV_PREFIX):]
    # Split on first underscore to get section
    parts = rest.lower().split("_", 1)
    if len(parts) < 2:
        return None
    section, key = parts
    return f"{section}.{key}"


def _load_env_overrides() -> Dict[str, Any]:
    """Load configuration overrides from environment variables.

    Maps HARNESS_<SECTION>_<KEY> to a nested dict structure.
    Example: HARNESS_PROVIDER_MODE=readonly → {"provider": {"mode": "readonly"}}
    """
    overrides: Dict[str, Any] = {}
    for env_name, env_value in os.environ.items():
        if not env_name.startswith(_ENV_PREFIX):
            continue
        key_path = _env_to_key(env_name)
        if key_path is None:
            continue
        section, key = key_path.split(".", 1)
        if section not in overrides:
            overrides[section] = {}
        # Convert string "true"/"false" to bool
        if env_value.lower() in ("true", "yes", "1"):
            overrides[section][key] = True
        elif env_value.lower() in ("false", "no", "0"):
            overrides[section][key] = False
        else:
            # Try numeric conversion
            try:
                overrides[section][key] = int(env_value)
            except ValueError:
                try:
                    overrides[section][key] = float(env_value)
                except ValueError:
                    overrides[section][key] = env_value
    return overrides


def resolve_config(
    project_root: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> HarnessConfig:
    """Resolve the effective configuration from all sources.

    Args:
        project_root: Project root directory for project-level config.
        cli_overrides: Dict of CLI-provided overrides in raw format
            (e.g. {"provider": {"mode": "readonly"}}).

    Returns:
        The fully resolved HarnessConfig.
    """
    # 1. Built-in defaults (lowest priority)
    config = HarnessConfig.defaults()

    # 2. Global config
    global_path = get_global_config_path()
    config = _merge_config_file(config, global_path)

    # 3. Project config
    if project_root:
        project_path = get_project_config_path(project_root)
        config = _merge_config_file(config, project_path)

    # 4. Environment variables
    env_overrides = _load_env_overrides()
    if env_overrides:
        config = _merge_raw_override(config, env_overrides)

    # 5. CLI overrides (highest priority)
    if cli_overrides:
        config = _merge_raw_override(config, cli_overrides)

    return config


def _merge_config_file(config: HarnessConfig, file_path: str) -> HarnessConfig:
    """Merge only explicitly present keys from a config file."""
    if not os.path.isfile(file_path):
        return config

    try:
        raw = _parse_file(file_path)
    except Exception as e:
        print(f"Warning: failed to parse config '{file_path}': {e}", file=sys.stderr)
        return config

    return _merge_raw_override(config, raw)


def _merge_raw_override(config: HarnessConfig, raw: Dict[str, Any]) -> HarnessConfig:
    """Merge raw config while preserving lower-priority values for absent keys.

    ``load_config_file`` returns a fully defaulted HarnessConfig, which is
    correct for single-file loading but not for priority resolution: absent keys
    in a higher-priority source must not reset values from lower-priority
    sources. This resolver therefore applies only keys that are explicitly
    present in the raw source.
    """
    parsed = _parse_raw(raw)

    if "version" in raw:
        config.version = parsed.version

    for section in ("workspace", "runtime", "provider", "copilot", "security"):
        raw_section = raw.get(section)
        if not isinstance(raw_section, dict):
            continue
        target_section = getattr(config, section)
        parsed_section = getattr(parsed, section)
        for key in raw_section:
            if hasattr(target_section, key):
                setattr(target_section, key, getattr(parsed_section, key))

    return config
