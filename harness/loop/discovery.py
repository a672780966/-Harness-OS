"""Agent and tool discovery for loop installer."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolInfo:
    name: str
    installed: bool
    version: str | None = None
    path: str | None = None


@dataclass
class AgentInfo:
    name: str
    installed: bool
    version: str | None = None
    path: str | None = None
    has_cli: bool = False
    has_adapter: bool = False


@dataclass
class SystemInfo:
    tools: list[ToolInfo] = field(default_factory=list)
    agents: list[AgentInfo] = field(default_factory=list)
    python_version: str | None = None
    git_version: str | None = None
    platform: str | None = None


def _get_version(cmd: list[str], timeout: int = 10) -> str | None:
    """Run a command and return its first line of output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0][:200]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def detect_tools() -> list[ToolInfo]:
    """Detect common development tools."""
    tools = []
    checks = [
        ("git", ["git", "--version"]),
        ("gh", ["gh", "--version"]),
        ("python3", ["python3", "--version"]),
        ("pip", ["pip", "--version"]),
        ("pytest", ["pytest", "--version"]),
        ("node", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("docker", ["docker", "--version"]),
    ]
    for name, cmd in checks:
        path = shutil.which(name)
        ver = _get_version(cmd) if path else None
        tools.append(ToolInfo(name=name, installed=path is not None, version=ver, path=path))
    return tools


def detect_agents() -> list[AgentInfo]:
    """Detect AI coding agents."""
    agents = []
    checks = [
        ("hermes", ["hermes", "--version"], True),
        ("codex", ["codex", "--version"], True),
        ("claude-code", ["claude", "--version"], True),
        ("opencode", ["opencode", "--version"], True),
        ("harness", ["harness", "copilot", "version", "--json"], True),
    ]
    for name, cmd, has_cli in checks:
        # Map binary name to actual command
        actual_cmd = cmd
        if name == "claude-code":
            actual_cmd = ["claude", "--version"]
        elif name == "harness":
            # Try the local entry point
            actual_cmd = ["python3", "-m", "harness.copilot.cli", "version", "--json"]
        elif name == "hermes":
            # Try both hermes and hermes-agent
            hermes_path = shutil.which("hermes") or shutil.which("hermes-agent")
            if hermes_path:
                actual_cmd = [hermes_path, "--version"]
            else:
                actual_cmd = cmd

        path = shutil.which(name.split("-")[0]) if name != "harness" else (shutil.which("harness") or None)
        if name == "claude-code":
            path = shutil.which("claude")
        if name == "hermes":
            path = shutil.which("hermes") or shutil.which("hermes-agent")

        ver = _get_version(actual_cmd) if (path or name == "harness") else None
        # Special handling for harness copilot
        if name == "harness" and not ver:
            ver = "available via python -m harness.copilot.cli"

        has_adapter = name in ("hermes", "codex", "claude-code", "opencode")
        agents.append(AgentInfo(
            name=name,
            installed=path is not None or name == "harness",
            version=ver,
            path=path,
            has_cli=has_cli and path is not None,
            has_adapter=has_adapter,
        ))
    return agents


def detect_system() -> SystemInfo:
    """Full system detection."""
    import platform
    tools = detect_tools()
    agents = detect_agents()
    python_ver = _get_version(["python3", "--version"])
    git_ver = _get_version(["git", "--version"])
    return SystemInfo(
        tools=tools,
        agents=agents,
        python_version=python_ver,
        git_version=git_ver,
        platform=platform.platform(),
    )


def detect_summary() -> str:
    """Return a human-readable summary of detected tools and agents."""
    sys_info = detect_system()
    lines = ["🔍 Harness Loop Doctor — System Report", ""]
    lines.append("📦 Tools:")
    for t in sys_info.tools:
        icon = "✅" if t.installed else "❌"
        ver = f" ({t.version})" if t.version else ""
        lines.append(f"  {icon} {t.name}{ver}")
    lines.append("")
    lines.append("🤖 AI Agents:")
    for a in sys_info.agents:
        icon = "✅" if a.installed else "❌"
        ver = f" ({a.version})" if a.version else ""
        adapter = " [adapter available]" if a.has_adapter else ""
        lines.append(f"  {icon} {a.name}{ver}{adapter}")
    lines.append("")
    lines.append(f"💻 Platform: {sys_info.platform}")
    return "\n".join(lines)
