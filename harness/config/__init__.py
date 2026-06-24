"""Harness Config — global and project-level configuration management.

Usage:
    from harness.config import (
        HarnessConfig,
        resolve_config,
        validate_config,
        write_default_global_config,
    )
"""

from __future__ import annotations

from .loader import load_config_file, write_default_global_config
from .paths import (
    get_global_config_dir,
    get_global_config_path,
    get_project_config_path,
    resolve_effective_paths,
)
from .resolver import resolve_config
from .schema import (
    HarnessConfig,
    ProviderConfig,
    RuntimeConfig,
    SecurityConfig,
    WorkspaceConfig,
    CopilotConfig,
    SCHEMA_VERSION,
)
from .validator import validate_config

__all__ = [
    "HarnessConfig",
    "ProviderConfig",
    "RuntimeConfig",
    "SecurityConfig",
    "WorkspaceConfig",
    "CopilotConfig",
    "SCHEMA_VERSION",
    "get_global_config_dir",
    "get_global_config_path",
    "get_project_config_path",
    "load_config_file",
    "resolve_config",
    "resolve_effective_paths",
    "validate_config",
    "write_default_global_config",
]
