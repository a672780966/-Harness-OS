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
import re
from typing import Any, Dict, Optional

from .schema import HarnessConfig, ProviderConfig, WorkspaceConfig, RuntimeConfig, CopilotConfig, SecurityConfig
from .loader import load_config_file, _parse_raw
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
    global_cfg = load_config_file(global_path)
    config = config.merge(global_cfg)

    # 3. Project config
    if project_root:
        project_path = get_project_config_path(project_root)
        project_cfg = load_config_file(project_path)
        config = config.merge(project_cfg)

    # 4. Environment variables
    env_overrides = _load_env_overrides()
    if env_overrides:
        env_cfg = _parse_raw(env_overrides)
        config = config.merge(env_cfg)

    # 5. CLI overrides (highest priority)
    if cli_overrides:
        cli_cfg = _parse_raw(cli_overrides)
        config = config.merge(cli_cfg)

    return config
