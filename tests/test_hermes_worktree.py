from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_hermes_worktree_script_exists():
    assert (ROOT / ".harness/scripts/hermes_worktree.py").exists()


def test_hermes_worktree_safe_task_id():
    import importlib.util
    spec = importlib.util.spec_from_file_location("wt", ROOT / ".harness/scripts/hermes_worktree.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.safe_task_id("task_abc") == "task_abc"
    try:
        m.safe_task_id("../bad")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe task_id should be rejected")
