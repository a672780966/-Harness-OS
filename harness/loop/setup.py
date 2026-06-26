"""Loop setup — interactive and non-interactive setup."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .config import write_loop_config
from .discovery import detect_system
from .instructions import generate_all_instructions, generate_code_meaning_report_template
from .safety import safety_report
from .topology import suggest_topology


def setup_loop(
    project_root: str,
    mode: str = "single_agent",
    agents: list[str] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Set up a loop configuration in the project.

    Args:
        project_root: Path to project root.
        mode: 'single_agent' or 'multi_agent'.
        agents: List of agent names to use. If None, auto-detect.
        output_dir: Output directory for loop config. Default: .harness/loop
    """
    root = Path(project_root)
    if not root.is_dir():
        return {"success": False, "error": f"Not a directory: {project_root}"}

    out = Path(output_dir) if output_dir else root / ".harness" / "loop"

    # Auto-detect system
    sys_info = detect_system()
    installed_agents = [a.name for a in sys_info.agents if a.installed]

    # Determine which agents to use
    if agents:
        selected_agents = agents
    elif installed_agents:
        selected_agents = installed_agents[:2]  # Use up to 2 detected agents
    else:
        selected_agents = ["hermes"]  # Fallback

    # Determine mode and roles
    if mode == "single_agent" or len(selected_agents) == 1:
        actual_mode = "single_agent"
        agent_name = selected_agents[0]
        agent_list = [{"name": agent_name, "subagent_strategy": True}]
        roles = {
            agent_name: "planner,coder,tester,reviewer,gatekeeper,doc_writer",
        }
    else:
        actual_mode = "multi_agent"
        agent_list = [{"name": a} for a in selected_agents]
        roles = {}
        for a in selected_agents:
            if a == "codex":
                roles[a] = "planner,reviewer,gatekeeper"
            elif a == "hermes":
                roles[a] = "executor,evidence_collector"
            elif a == "claude-code":
                roles[a] = "implementation_worker"
            elif a == "opencode":
                roles[a] = "alternative_worker,reviewer"
            else:
                roles[a] = "worker"

    # Write loop config
    config_files = write_loop_config(str(out), actual_mode, agent_list, roles)

    # Generate agent instructions
    instruction_files = generate_all_instructions(str(out), agent_list, roles)

    # Generate Code Meaning Report template
    cmr_template = generate_code_meaning_report_template()
    (out / "templates").mkdir(parents=True, exist_ok=True)
    (out / "templates" / "code_meaning_report.md").write_text(cmr_template, encoding="utf-8")

    # Generate safety report for reference
    safe = safety_report(project_root)
    (out / "safety_reference.md").write_text(safe, encoding="utf-8")

    return {
        "success": True,
        "output_dir": str(out),
        "mode": actual_mode,
        "agents": selected_agents,
        "roles": roles,
        "config_files": list(config_files.keys()),
        "instruction_files": list(instruction_files.keys()),
        "has_templates": True,
    }


def init_loop(
    project_root: str,
    mode: str = "single_agent",
    agents: list[str] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Non-interactive loop initialization (same logic as setup)."""
    return setup_loop(project_root, mode=mode, agents=agents, output_dir=output_dir)
