"""Loop topology recommendation based on detected agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .discovery import AgentInfo, SystemInfo


@dataclass
class LoopTopology:
    name: str
    mode: str  # single_agent or multi_agent
    agents: list[dict[str, Any]]
    roles: dict[str, str]
    description: str


def suggest_topology(sys_info: SystemInfo) -> list[LoopTopology]:
    """Recommend loop topologies based on detected agents."""
    suggestions = []
    agent_names = [a.name for a in sys_info.agents if a.installed]
    installed = set(agent_names)

    # Single-agent options
    for agent in ["claude-code", "codex", "opencode", "hermes"]:
        if agent in installed:
            suggestions.append(LoopTopology(
                name=f"single_{agent}",
                mode="single_agent",
                agents=[{"name": agent, "subagent_strategy": True}],
                roles={
                    agent: "planner,coder,tester,reviewer,gatekeeper,doc_writer",
                },
                description=f"Single-agent loop using {agent} with internal sub-agent roles.",
            ))

    # Multi-agent options
    multi_configs = [
        (["codex", "hermes"], "Codex → Hermes loop"),
        (["codex", "hermes", "claude-code"], "Codex + Hermes + Claude Code full loop"),
        (["codex", "hermes", "opencode"], "Codex + Hermes + OpenCode loop"),
        (["codex", "hermes", "claude-code", "opencode"], "Full 4-agent loop"),
    ]
    for agents, desc in multi_configs:
        if all(a in installed for a in agents):
            roles = {}
            for a in agents:
                if a == "codex":
                    roles[a] = "planner,reviewer,gatekeeper"
                elif a == "hermes":
                    roles[a] = "executor,evidence_collector"
                elif a == "claude-code":
                    roles[a] = "implementation_worker"
                elif a == "opencode":
                    roles[a] = "alternative_worker,reviewer"
            suggestions.append(LoopTopology(
                name="_".join(agents),
                mode="multi_agent",
                agents=[{"name": a} for a in agents],
                roles=roles,
                description=desc,
            ))

    return suggestions


def suggest_summary(sys_info: SystemInfo) -> str:
    """Generate a human-readable topology suggestion."""
    suggestions = suggest_topology(sys_info)
    lines = ["🤖 Harness Loop Suggest — Recommended Topologies", ""]
    if not suggestions:
        lines.append("No AI coding agents detected. Install at least one:")
        lines.append("  - codex (npm install -g @openai/codex)")
        lines.append("  - claude-code (npm install -g @anthropic-ai/claude-code)")
        lines.append("  - opencode (npm install -g opencode)")
        lines.append("  - hermes (pip install hermes-agent)")
        return "\n".join(lines)

    for i, s in enumerate(suggestions, 1):
        lines.append(f"{i}. {s.name}")
        lines.append(f"   Mode: {s.mode}")
        lines.append(f"   {s.description}")
        lines.append(f"   Agents: {', '.join(a['name'] for a in s.agents)}")
        lines.append(f"   Roles: {s.roles}")
        lines.append("")

    lines.append("Run 'harness loop setup' to configure.")
    return "\n".join(lines)
