from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fresh_audit_skill_exists():
    assert (ROOT / ".harness/skills/claude-code-fresh-audit/SKILL.md").exists()


def test_review_sessions_config_exists():
    assert (ROOT / ".harness/config/review_sessions.yaml").exists()


def test_review_sessions_has_require_fresh_session():
    import yaml
    with (ROOT / ".harness/config/review_sessions.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    first = data["first_round_review"]
    assert first["require_fresh_session"] is True
    assert first["forbid_implementation_context_reuse"] is True
    assert first["review_only"] is True


def test_fresh_audit_script_help():
    proc = subprocess.run(
        [sys.executable, ".harness/scripts/hermes_claude_fresh_audit.py", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0
    assert "Fresh Audit" in proc.stdout or "fresh" in proc.stdout.lower() or "prepare" in proc.stdout


def test_fresh_audit_prompt_template_exists():
    assert (ROOT / ".harness/workers/claude-code-audit/prompts/FRESH_AUDIT_PROMPT_TEMPLATE.md").exists()


def test_fresh_audit_registered_in_skill_registry():
    import yaml
    with (ROOT / ".harness/skills/skill_registry.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "claude_code_fresh_audit" in data.get("skills", {})
    skill = data["skills"]["claude_code_fresh_audit"]
    assert skill.get("enabled") is True
    assert "Must start a fresh Claude Code session" in str(skill.get("rules", []))


def test_fresh_audit_registered_in_tools_yaml():
    import yaml
    with (ROOT / ".harness/config/tools.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "claude_code_fresh_auditor" in data.get("tools", {})
    tool = data["tools"]["claude_code_fresh_auditor"]
    assert tool["session_policy"]["require_fresh_session"] is True
    assert tool["permissions"]["can_edit_code"] is False


def test_fresh_audit_cli_command_help():
    proc = subprocess.run(
        [sys.executable, ".harness/scripts/hermes.py", "claude-fresh-audit-prepare", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0
    assert "task-envelope" in proc.stdout or "TASK_ENVELOPE" in proc.stdout
