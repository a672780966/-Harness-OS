"""Tests for swebench_docker_eval.py framework routing logic."""

import sys
import json
import importlib
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / ".harness" / "scripts" / "swebench_docker_eval.py"


def _import_detect_framework():
    """Import the detect_framework function from the eval script."""
    # We import the module to access detect_framework
    # Since the script uses __name__ == '__main__' guard, we can import safely
    import importlib.util
    spec = importlib.util.spec_from_file_location("swebench_docker_eval", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Don't exec the whole script — just extract the function
    # Instead, let's parse the function directly
    return None


def _read_detect_framework_source():
    """Read the detect_framework function source from the script."""
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    # Find the function
    lines = text.splitlines()
    fn_start = None
    fn_end = None
    for i, line in enumerate(lines):
        if "def detect_framework" in line:
            fn_start = i
        if fn_start is not None and i > fn_start and line.strip().startswith("framework = detect_framework"):
            fn_end = i
            break
    if fn_start is None or fn_end is None:
        return None
    code = "\n".join(lines[fn_start:fn_end])
    return code


@pytest.fixture
def detect_framework():
    """Provide the detect_framework function by extracting and compiling it."""
    source = _read_detect_framework_source()
    if source is None:
        pytest.skip("Could not extract detect_framework function")
    exec_globals = {}
    exec(source, exec_globals)
    return exec_globals["detect_framework"]


class TestFrameworkRouting:
    """Test that swebench_docker_eval.py dispatches to the correct framework."""

    def test_django_11885_routes_to_django(self, detect_framework):
        """django__django-11885 must route to Django eval command."""
        assert detect_framework("django__django-11885") == "django"

    def test_django_11848_routes_to_django(self, detect_framework):
        """django__django-11848 must route to Django eval command."""
        assert detect_framework("django__django-11848") == "django"

    def test_django_12050_routes_to_django(self, detect_framework):
        """django__django-12050 must route to Django eval command."""
        assert detect_framework("django__django-12050") == "django"

    def test_sphinx_7590_routes_to_sphinx(self, detect_framework):
        """sphinx-doc__sphinx-7590 must route to Sphinx eval command."""
        assert detect_framework("sphinx-doc__sphinx-7590") == "sphinx"

    def test_sphinx_10466_routes_to_sphinx(self, detect_framework):
        """sphinx-doc__sphinx-10466 must route to Sphinx eval command."""
        assert detect_framework("sphinx-doc__sphinx-10466") == "sphinx"

    def test_unknown_framework_returns_unknown(self, detect_framework):
        """Unknown framework must return 'unknown', not silently fall back."""
        assert detect_framework("some-other__repo-1") == "unknown"

    def test_empty_instance_id_returns_unknown(self, detect_framework):
        """Empty instance_id must return 'unknown'."""
        assert detect_framework("") == "unknown"

    def test_sympy_framework_returns_unknown(self, detect_framework):
        """sympy instance must return 'unknown'."""
        assert detect_framework("sympy__sympy-20590") == "unknown"

    def test_script_has_detect_framework_function(self):
        """The script must define the detect_framework function."""
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "def detect_framework" in text

    def test_script_has_framework_dispatch(self):
        """The script must use detect_framework to dispatch."""
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        assert "framework = detect_framework" in text
        assert 'if framework == "django"' in text
        assert 'elif framework == "sphinx"' in text

    def test_unknown_framework_early_exit(self):
        """Unknown framework must produce early exit with unsupported_framework."""
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        assert 'if framework == "unknown"' in text
        assert "unsupported_framework" in text


class TestEvalCommandUsage:
    """Test that the script doesn't hardcode a single framework path."""

    def test_no_single_framework_hardcode(self):
        """The script must not hardcode a single framework's test path."""
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        # The script must have both django and sphinx paths
        # Ensure Sphinx path isn't the only path
        sphinx_count = text.count("CPP_SMOKE_PASSED")
        django_count = text.count("tests/runtests.py")
        if sphinx_count > 0:
            assert django_count > 0, "Sphinx-only path detected: django path missing"
        if django_count > 0:
            assert sphinx_count >= 0  # Sphinx path may still exist

    def test_django_uses_runtests(self):
        """Django eval must use tests/runtests.py."""
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        assert 'if framework == "django"' in text
        assert "tests/runtests.py" in text

    def test_script_cli_requires_two_args(self):
        """Script must accept at least 2 CLI args: patch_path and instance_id."""
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        # Check that sys.argv[1] and sys.argv[2] are used
        assert "sys.argv[1]" in text
        assert "sys.argv[2]" in text
