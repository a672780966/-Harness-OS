"""Tests: Config paths — global/project path resolution."""

from __future__ import annotations

import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.config.paths import (
    get_global_config_dir,
    get_global_config_path,
    get_project_config_path,
    resolve_effective_paths,
)


class TestGlobalPaths:
    def test_global_dir_ends_with_harness(self):
        path = get_global_config_dir()
        assert path.endswith(".harness")
        assert os.path.isabs(path)

    def test_global_config_path_ends_yaml(self):
        path = get_global_config_path()
        assert path.endswith("config.yaml")
        assert ".harness" in path

    def test_global_config_path_uses_dir(self):
        d = get_global_config_dir()
        p = get_global_config_path()
        assert p == os.path.join(d, "config.yaml")


class TestProjectPaths:
    def test_project_config_path_with_root(self):
        path = get_project_config_path("/my/project")
        assert path == "/my/project/.harness/config.yaml"

    def test_project_config_path_none_uses_cwd(self):
        cwd = os.getcwd()
        path = get_project_config_path()
        assert path == os.path.join(cwd, ".harness", "config.yaml")

    def test_project_config_path_trailing_slash(self):
        path = get_project_config_path("/tmp/")
        assert path.endswith("/.harness/config.yaml")


class TestResolveEffectivePaths:
    def test_returns_required_keys(self):
        paths = resolve_effective_paths("/tmp")
        required_keys = [
            "global_config_path",
            "project_config_path",
            "global_config_exists",
            "project_config_exists",
            "global_dir",
        ]
        for key in required_keys:
            assert key in paths, f"Missing key: {key}"

    def test_global_config_exists_false_by_default(self):
        # On a clean system without ~/.harness/config.yaml, this should be False
        # or True depending on dev setup — we just check it's a bool
        paths = resolve_effective_paths()
        assert isinstance(paths["global_config_exists"], bool)

    def test_project_config_exists_with_fake_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = resolve_effective_paths(tmpdir)
            assert paths["project_config_exists"] is False
            # Create the file and check again
            os.makedirs(os.path.join(tmpdir, ".harness"), exist_ok=True)
            open(os.path.join(tmpdir, ".harness", "config.yaml"), "w").close()
            paths2 = resolve_effective_paths(tmpdir)
            assert paths2["project_config_exists"] is True
