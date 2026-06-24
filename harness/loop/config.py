"""Loop configuration generation."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def generate_loop_yaml(
    mode: str,
    agents: list[dict[str, Any]],
    roles: dict[str, str],
) -> str:
    """Generate loop.yaml content."""
    config: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "mode": mode,
        "agents": agents,
        "roles": roles,
        "policy": {
            "auto_allow": [
                "read files",
                "git status",
                "git diff",
                "git log",
                "pytest",
                "harness copilot inspect",
                "harness copilot readiness",
                "harness copilot task-card",
                "harness copilot pr-draft",
                "write .harness/loop/runs/",
                "write docs/*_report.md",
            ],
            "human_required": [
                "git push",
                "git push --tags",
                "git tag",
                "git merge",
                "git reset",
                "git clean",
                "rm",
                "delete files",
                "modify .env",
                "modify secrets",
                "deploy",
                "upload dist/*.tar.gz",
                "upload *.zip",
                "upload *.tgz",
                "rewrite history",
            ],
        },
        "max_repair_rounds": 3,
        "require_code_meaning_report": True,
    }
    return yaml.dump(config, default_flow_style=False, sort_keys=False)


def generate_agents_yaml(agents: list[dict[str, Any]]) -> str:
    """Generate agents.yaml content."""
    config = {"agents": []}
    for a in agents:
        entry: dict[str, Any] = {
            "name": a["name"],
            "role": a.get("role", "worker"),
        }
        if a.get("subagent_strategy"):
            entry["subagent_strategy"] = True
        if a.get("instructions"):
            entry["instructions"] = a["instructions"]
        config["agents"].append(entry)
    return yaml.dump(config, default_flow_style=False, sort_keys=False)


def generate_policy_yaml() -> str:
    """Generate policy.yaml content."""
    policy = {
        "version": "1",
        "safety": {
            "auto_allow": [
                {"action": "read files", "reason": "required for analysis"},
                {"action": "git status", "reason": "required for state awareness"},
                {"action": "git diff", "reason": "required for review"},
                {"action": "git log", "reason": "required for context"},
                {"action": "pytest", "reason": "required for verification"},
                {"action": "harness copilot inspect", "reason": "local copilot"},
                {"action": "harness copilot readiness", "reason": "local copilot"},
                {"action": "harness copilot task-card", "reason": "local copilot"},
                {"action": "harness copilot pr-draft", "reason": "local copilot"},
                {"action": "write .harness/loop/runs/", "reason": "run output"},
                {"action": "write docs/*_report.md", "reason": "documentation"},
            ],
            "blocked": [
                {"action": "git push", "reason": "requires human approval"},
                {"action": "git push --tags", "reason": "requires human approval"},
                {"action": "git tag", "reason": "requires human approval"},
                {"action": "git merge", "reason": "requires human approval"},
                {"action": "git reset --hard", "reason": "destructive"},
                {"action": "git clean -fdx", "reason": "destructive"},
                {"action": "rm -rf", "reason": "destructive"},
                {"action": "delete files outside scope", "reason": "safety"},
                {"action": "modify .env", "reason": "secrets exposure"},
                {"action": "deploy", "reason": "requires human approval"},
                {"action": "upload large archives", "reason": "GitHub size limit"},
                {"action": "rewrite history", "reason": "irreversible"},
            ],
        },
    }
    return yaml.dump(policy, default_flow_style=False, sort_keys=False)


def generate_a2a_yaml() -> str:
    """Generate A2A envelope protocol config."""
    config = {
        "protocol": "harness-loop/v1",
        "envelope_types": {
            "task": {
                "required_fields": [
                    "protocol", "trace_id", "task_id",
                    "from_agent", "to_agent",
                    "objective", "acceptance_criteria",
                ],
            },
            "result": {
                "required_fields": [
                    "protocol", "trace_id", "task_id",
                    "from_agent", "to_agent",
                    "status", "changed_files",
                    "test_result", "evidence_refs",
                ],
            },
            "review": {
                "required_fields": [
                    "protocol", "trace_id", "task_id",
                    "from_agent", "to_agent",
                    "status", "blocking_issues",
                ],
            },
        },
    }
    return yaml.dump(config, default_flow_style=False, sort_keys=False)


def generate_roles_yaml(roles: dict[str, str]) -> str:
    """Generate roles.yaml content."""
    config = {"roles": {}}
    for agent_name, role_str in roles.items():
        config["roles"][agent_name] = {
            "primary_role": role_str.split(",")[0],
            "all_roles": role_str.split(","),
        }
    return yaml.dump(config, default_flow_style=False, sort_keys=False)


def write_loop_config(output_dir: str, mode: str, agents: list[dict[str, Any]], roles: dict[str, str]) -> dict[str, str]:
    """Write all loop configuration files to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    files = {
        "loop.yaml": generate_loop_yaml(mode, agents, roles),
        "agents.yaml": generate_agents_yaml(agents),
        "roles.yaml": generate_roles_yaml(roles),
        "policy.yaml": generate_policy_yaml(),
        "a2a.yaml": generate_a2a_yaml(),
    }

    written = {}
    for filename, content in files.items():
        path = out / filename
        path.write_text(content, encoding="utf-8")
        written[filename] = str(path)

    # Create envelopes directory with schemas
    env_dir = out / "envelopes"
    env_dir.mkdir(parents=True, exist_ok=True)

    # Task envelope schema
    task_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["protocol", "trace_id", "task_id", "from_agent", "to_agent",
                      "objective", "acceptance_criteria"],
        "properties": {
            "protocol": {"type": "string", "const": "harness-loop/v1"},
            "trace_id": {"type": "string"},
            "task_id": {"type": "string"},
            "from_agent": {"type": "string"},
            "to_agent": {"type": "string"},
            "objective": {"type": "string"},
            "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
            "context_refs": {"type": "array", "items": {"type": "string"}},
            "assigned_skills": {"type": "array", "items": {"type": "string"}},
            "allowed_actions": {"type": "array", "items": {"type": "string"}},
            "requires_human": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }
    (env_dir / "task_envelope.schema.json").write_text(
        json.dumps(task_schema, indent=2) + "\n", encoding="utf-8"
    )

    result_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["protocol", "trace_id", "task_id", "from_agent", "to_agent",
                      "status", "changed_files", "test_result"],
        "properties": {
            "protocol": {"type": "string", "const": "harness-loop/v1"},
            "trace_id": {"type": "string"},
            "task_id": {"type": "string"},
            "from_agent": {"type": "string"},
            "to_agent": {"type": "string"},
            "status": {"type": "string"},
            "changed_files": {"type": "array", "items": {"type": "string"}},
            "test_result": {
                "type": "object",
                "properties": {
                    "passed": {"type": "boolean"},
                    "command": {"type": "string"},
                    "summary": {"type": "string"},
                },
            },
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
            "code_meaning_report": {
                "type": "object",
                "properties": {
                    "what_changed": {"type": "string"},
                    "why_changed": {"type": "string"},
                    "impact": {"type": "string"},
                    "risk": {"type": "string"},
                    "tests": {"type": "string"},
                },
            },
        },
        "additionalProperties": False,
    }
    (env_dir / "result_envelope.schema.json").write_text(
        json.dumps(result_schema, indent=2) + "\n", encoding="utf-8"
    )

    review_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["protocol", "trace_id", "task_id", "from_agent", "to_agent",
                      "status", "blocking_issues"],
        "properties": {
            "protocol": {"type": "string", "const": "harness-loop/v1"},
            "trace_id": {"type": "string"},
            "task_id": {"type": "string"},
            "from_agent": {"type": "string"},
            "to_agent": {"type": "string"},
            "status": {"type": "string"},
            "blocking_issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string"},
                        "file": {"type": "string"},
                        "issue": {"type": "string"},
                        "required_fix": {"type": "string"},
                    },
                },
            },
            "required_fixes": {"type": "array", "items": {"type": "string"}},
            "merge_ready": {"type": "boolean"},
        },
        "additionalProperties": False,
    }
    (env_dir / "review_envelope.schema.json").write_text(
        json.dumps(review_schema, indent=2) + "\n", encoding="utf-8"
    )

    # Create runs directory
    (out / "runs").mkdir(parents=True, exist_ok=True)

    # Create README
    readme = """# Harness Loop

This directory was generated by `harness loop init`.

## Structure

- `loop.yaml` — loop topology and policy
- `agents.yaml` — agent registry
- `roles.yaml` — role assignments
- `policy.yaml` — safety policy
- `a2a.yaml` — A2A envelope protocol config
- `envelopes/` — JSON schemas for A2A envelopes
- `instructions/` — agent-native instruction files
- `runs/` — run output directory

## Safety

High-risk actions require human approval:
- git push, git merge, git reset
- delete files, modify .env, deploy
- upload large archives, rewrite history
"""
    (out / "README.md").write_text(readme, encoding="utf-8")
    written["README.md"] = str(out / "README.md")

    return written
