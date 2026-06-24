from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_external_tools_files_exist():
    assert (ROOT / ".harness/external-tools/external_tools.yaml").exists()
    assert (ROOT / ".harness/external-tools/understand-anything/INVOCATION.md").exists()
    assert (ROOT / ".harness/external-tools/superlog/INVOCATION.md").exists()
    assert (ROOT / ".harness/external-tools/TOOL_CALL_MATRIX.md").exists()


def test_external_tool_run_dirs_exist():
    assert (ROOT / ".harness/external-tools/runs/understand-anything").exists()
    assert (ROOT / ".harness/external-tools/runs/superlog").exists()


def test_external_tools_checker_runs():
    proc = subprocess.run(
        [sys.executable, ".harness/scripts/hermes_external_tools.py", "check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    assert "understand_anything" in data
    assert "superlog" in data
    assert data["understand_anything"]["mode"] == "external_direct_call"
    assert data["superlog"]["mode"] == "external_direct_call"
    assert data["superlog"]["full_stack_started"] is False


def test_config_files_updated():
    tools_yaml = (ROOT / ".harness/config/tools.yaml").read_text(encoding="utf-8")
    assert "integration_level: \"external_direct_call\"" in tools_yaml
    assert "understand_anything" in tools_yaml
    assert "superlog" in tools_yaml

    agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "External Tool Invocation Baseline" in agents_md

    claude_md = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "External Tool Usage for Claude Code" in claude_md
