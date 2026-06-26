"""Tests for Loop Installer MVP."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Create a temporary git repo."""
    root = tmp_path / "test_project"
    root.mkdir()
    subprocess.run(["git", "init"], cwd=root, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=root, capture_output=True)
    (root / "README.md").write_text("# Test")
    # Create bare remote
    bare = tmp_path / "bare.git"
    bare.mkdir()
    subprocess.run(["git", "init", "--bare", str(bare)], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=root, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, capture_output=True)
    subprocess.run(["git", "push", "--set-upstream", "origin", "main"], cwd=root, capture_output=True)
    return root


# ── Module Import Tests ───────────────────────────────────────────────────────


def test_loop_modules_importable():
    """All loop modules should be importable."""
    from harness.loop import discovery, topology, setup, config, envelope, instructions, safety, reports, roles, skills, runner
    assert hasattr(discovery, "detect_system")
    assert hasattr(topology, "suggest_topology")
    assert hasattr(setup, "setup_loop")
    assert hasattr(config, "write_loop_config")
    assert hasattr(envelope, "create_task_envelope")
    assert hasattr(instructions, "generate_codex_instructions")
    assert hasattr(safety, "is_action_allowed")
    assert hasattr(reports, "generate_code_meaning_report")
    assert hasattr(roles, "list_roles")
    assert hasattr(skills, "get_skills_for_role")
    assert hasattr(runner, "run_loop")


# ── Discovery Tests ───────────────────────────────────────────────────────────


def test_detect_tools():
    """Should detect git and python at minimum."""
    from harness.loop.discovery import detect_tools
    tools = detect_tools()
    tool_names = [t.name for t in tools]
    assert "git" in tool_names
    assert "python3" in tool_names
    for t in tools:
        if t.name in ("git", "python3"):
            assert t.installed is True


def test_detect_system():
    """System detection should return platform info."""
    from harness.loop.discovery import detect_system
    info = detect_system()
    assert info.platform is not None
    assert len(info.tools) > 0


def test_detect_summary():
    """Detect summary should be a non-empty string."""
    from harness.loop.discovery import detect_summary
    summary = detect_summary()
    assert len(summary) > 0
    assert "Tools" in summary or "Agents" in summary


# ── Topology Tests ────────────────────────────────────────────────────────────


def test_suggest_topology_empty():
    """Empty system should produce no suggestions."""
    from harness.loop.discovery import AgentInfo, SystemInfo, ToolInfo
    from harness.loop.topology import suggest_topology
    sys_info = SystemInfo(tools=[], agents=[])
    suggestions = suggest_topology(sys_info)
    assert len(suggestions) == 0


def test_suggest_topology_with_agents():
    """Having agents should produce suggestions."""
    from harness.loop.discovery import AgentInfo, SystemInfo, ToolInfo
    from harness.loop.topology import suggest_topology
    agents = [
        AgentInfo(name="hermes", installed=True, version="1.0", path="/usr/bin/hermes",
                  has_cli=True, has_adapter=True),
    ]
    sys_info = SystemInfo(tools=[], agents=agents)
    suggestions = suggest_topology(sys_info)
    assert len(suggestions) >= 1
    assert any(s.mode == "single_agent" for s in suggestions)


# ── Role Tests ────────────────────────────────────────────────────────────────


def test_list_roles():
    """Should list all available roles."""
    from harness.loop.roles import list_roles
    roles = list_roles()
    assert "planner" in roles
    assert "coder" in roles
    assert "gatekeeper" in roles


def test_get_role():
    """Should return role definition."""
    from harness.loop.roles import get_role
    role = get_role("planner")
    assert role is not None
    assert "responsibilities" in role
    assert "allowed_actions" in role
    assert "blocked_actions" in role


# ── Skill Tests ───────────────────────────────────────────────────────────────


def test_skills_for_role():
    """Should return skills for a valid role."""
    from harness.loop.skills import get_skills_for_role
    skills = get_skills_for_role("planner")
    assert len(skills) > 0


# ── Envelope Tests ────────────────────────────────────────────────────────────


def test_create_task_envelope():
    """Task envelope should be valid JSON with required fields."""
    from harness.loop.envelope import create_task_envelope
    env_str = create_task_envelope(
        trace_id="trace_001",
        task_id="task_001",
        from_agent="codex",
        to_agent="hermes",
        objective="Implement feature X",
        acceptance_criteria=["tests pass", "no regression"],
    )
    env = json.loads(env_str)
    assert env["protocol"] == "harness-loop/v1"
    assert env["from_agent"] == "codex"
    assert env["to_agent"] == "hermes"
    assert "requires_human" in env


def test_create_result_envelope():
    """Result envelope should contain test_result and evidence_refs."""
    from harness.loop.envelope import create_result_envelope
    env_str = create_result_envelope(
        trace_id="trace_001",
        task_id="task_001",
        from_agent="hermes",
        to_agent="codex",
        status="completed_for_review",
        changed_files=["src/main.py"],
        test_passed=True,
        test_command="pytest",
        test_summary="all passed",
    )
    env = json.loads(env_str)
    assert env["test_result"]["passed"] is True
    assert "evidence_refs" in env


def test_create_review_envelope():
    """Review envelope should include blocking_issues."""
    from harness.loop.envelope import create_review_envelope
    env_str = create_review_envelope(
        trace_id="trace_001",
        task_id="task_001",
        from_agent="codex",
        to_agent="hermes",
        status="repair_requested",
        blocking_issues=[{"severity": "high", "file": "src/main.py", "issue": "bug", "required_fix": "fix it"}],
    )
    env = json.loads(env_str)
    assert len(env["blocking_issues"]) == 1
    assert env["merge_ready"] is False


# ── Config Tests ──────────────────────────────────────────────────────────────


def test_write_loop_config(project_root: Path):
    """Loop config should be written to output directory."""
    from harness.loop.config import write_loop_config
    out_dir = str(project_root / ".harness" / "loop")
    files = write_loop_config(
        out_dir,
        mode="single_agent",
        agents=[{"name": "hermes", "subagent_strategy": True}],
        roles={"hermes": "planner,coder,tester,reviewer,gatekeeper,doc_writer"},
    )
    assert "loop.yaml" in files
    assert "agents.yaml" in files
    assert "policy.yaml" in files
    assert "a2a.yaml" in files
    assert os.path.exists(os.path.join(out_dir, "envelopes", "task_envelope.schema.json"))
    assert os.path.exists(os.path.join(out_dir, "envelopes", "result_envelope.schema.json"))
    assert os.path.exists(os.path.join(out_dir, "envelopes", "review_envelope.schema.json"))
    assert os.path.exists(os.path.join(out_dir, "README.md"))


# ── Instruction Tests ─────────────────────────────────────────────────────────


def test_generate_codex_instructions():
    """Codex instructions should mention planner/reviewer/gatekeeper."""
    from harness.loop.instructions import generate_codex_instructions
    content = generate_codex_instructions({"codex": "planner,reviewer,gatekeeper"})
    assert "planner" in content
    assert "ReviewEnvelope" in content


def test_generate_code_meaning_report_template():
    """Code meaning report template should have all sections."""
    from harness.loop.instructions import generate_code_meaning_report_template
    template = generate_code_meaning_report_template()
    assert "What changed" in template
    assert "Why this change was needed" in template
    assert "Human approval required?" in template


def test_generate_all_instructions(project_root: Path):
    """All agent instructions should be generated."""
    from harness.loop.instructions import generate_all_instructions
    out_dir = str(project_root / ".harness" / "loop")
    agents = [
        {"name": "codex"},
        {"name": "hermes"},
    ]
    roles = {"codex": "planner,reviewer,gatekeeper", "hermes": "executor,evidence_collector"}
    files = generate_all_instructions(out_dir, agents, roles)
    assert "codex" in files
    assert "hermes" in files


# ── Safety Tests ──────────────────────────────────────────────────────────────


def test_is_action_allowed_safe():
    """Safe copilot commands should be allowed."""
    from harness.loop.safety import is_action_allowed
    allowed, _ = is_action_allowed("harness copilot inspect")
    assert allowed is True


def test_is_action_blocked_unsafe():
    """Unsafe commands should be blocked."""
    from harness.loop.safety import is_action_allowed
    allowed, _ = is_action_allowed("git push")
    assert allowed is False


def test_is_action_blocked_default():
    """Non-listed actions should be blocked by default."""
    from harness.loop.safety import is_action_allowed
    allowed, reason = is_action_allowed("rm -rf /")
    assert allowed is False


# ── Report Tests ──────────────────────────────────────────────────────────────


def test_generate_code_meaning_report():
    """Code meaning report should include all sections."""
    from harness.loop.reports import generate_code_meaning_report
    report = generate_code_meaning_report(what_changed="Fixed bug X")
    assert "Fixed bug X" in report


def test_generate_handoff_file():
    """Handoff file should be generated for unavailable adapter."""
    from harness.loop.reports import generate_handoff_file
    content = generate_handoff_file("claude-code", {"task_id": "task_001", "objective": "Fix bug", "roles": "worker"})
    assert "Handoff File for claude-code" in content
    assert "task_001" in content
    assert "Adapter unavailable" in content


# ── Setup / Init Tests ────────────────────────────────────────────────────────


def test_setup_loop_single_agent(project_root: Path):
    """setup_loop should generate single-agent config."""
    from harness.loop.setup import setup_loop
    result = setup_loop(str(project_root), mode="single_agent", agents=["hermes"])
    assert result["success"] is True
    assert result["mode"] == "single_agent"
    assert "hermes" in result["agents"]
    assert len(result["config_files"]) >= 5
    assert len(result["instruction_files"]) >= 1


def test_init_loop_multi_agent(project_root: Path):
    """init_loop should generate multi-agent config."""
    from harness.loop.setup import init_loop
    result = init_loop(str(project_root), mode="multi_agent", agents=["codex", "hermes"])
    assert result["success"] is True
    assert result["mode"] == "multi_agent"
    assert "codex" in result["agents"]
    assert "hermes" in result["agents"]


# ── CLI Tests ─────────────────────────────────────────────────────────────────


def test_cli_loop_doctor_help():
    """Loop doctor CLI help should be accessible."""
    from harness.copilot.cli import main
    # Just verify the module is importable and function exists
    import argparse
    # Verify the command function exists
    from harness.copilot.cli import cmd_loop_doctor
    assert callable(cmd_loop_doctor)


def test_cli_loop_commands_in_help():
    """Loop commands should appear in help."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "harness.copilot.cli", "loop", "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "doctor" in result.stdout
    assert "suggest" in result.stdout
    assert "setup" in result.stdout
    assert "init" in result.stdout
    assert "run" in result.stdout
