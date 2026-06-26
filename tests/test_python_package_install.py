"""Smoke tests for Python package installation and basic CLI functionality."""

import subprocess
import sys


class TestPackageInstall:
    """Verify the package can be imported and basic metadata is correct."""

    def test_import_harness(self):
        """harness package can be imported."""
        import harness  # noqa: F401

    def test_import_copilot_cli(self):
        """harness.copilot.cli module can be imported."""
        import harness.copilot.cli  # noqa: F401

    def test_import_version(self):
        """harness.runtime.version module can be imported."""
        import harness.runtime.version  # noqa: F401

    def test_import_doctor(self):
        """harness.runtime.doctor module can be imported."""
        import harness.runtime.doctor  # noqa: F401

    def test_import_config_schema(self):
        """harness.config.schema module can be imported."""
        import harness.config.schema  # noqa: F401


class TestCLISmoke:
    """Verify basic CLI commands exit cleanly."""

    def test_version_json(self):
        result = subprocess.run(
            [sys.executable, "-m", "harness.copilot.cli", "version", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"version --json failed: {result.stderr}"
        assert "v1.4" in result.stdout

    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "harness.copilot.cli", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, f"--help failed: {result.stderr}"
        assert "version" in result.stdout
        assert "doctor" in result.stdout
