"""Config paths — resolve global and project config file locations.

Global:  ~/.harness/config.yaml
Project: <project_root>/.harness/config.yaml
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def get_global_config_dir() -> str:
    """Return the global .harness config directory (~/.harness)."""
    return os.path.expanduser("~/.harness")


def get_global_config_path() -> str:
    """Return the global config file path (~/.harness/config.yaml)."""
    return os.path.join(get_global_config_dir(), "config.yaml")


def get_project_config_path(project_root: Optional[str] = None) -> str:
    """Return the project-level config file path.

    If project_root is None, uses the current working directory.
    """
    root = project_root or os.getcwd()
    return os.path.join(root, ".harness", "config.yaml")


def resolve_effective_paths(project_root: Optional[str] = None) -> dict:
    """Return all relevant config paths in priority order.

    Returns:
        dict with keys: global_config_path, project_config_path,
        global_config_exists, project_config_exists, global_dir
    """
    global_path = get_global_config_path()
    project_path = get_project_config_path(project_root)
    return {
        "global_config_path": global_path,
        "project_config_path": project_path,
        "global_config_exists": os.path.isfile(global_path),
        "project_config_exists": os.path.isfile(project_path),
        "global_dir": get_global_config_dir(),
    }
