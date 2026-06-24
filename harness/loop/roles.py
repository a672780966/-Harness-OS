"""Role definitions for loop installer."""

from __future__ import annotations

from typing import Any

ROLE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "planner": {
        "responsibilities": [
            "break down objective into task nodes",
            "define acceptance criteria for each node",
            "order nodes by dependency",
            "identify cross-module impact",
        ],
        "allowed_actions": [
            "read files",
            "list directory",
            "read specifications",
        ],
        "blocked_actions": [
            "edit files",
            "run tests",
            "merge",
        ],
    },
    "coder": {
        "responsibilities": [
            "implement minimal diff for assigned task node",
            "reuse existing patterns and modules",
            "add inline comments for complex logic",
            "run tests after implementation",
        ],
        "allowed_actions": [
            "read files",
            "edit scoped files",
            "run tests",
            "generate reports",
        ],
        "blocked_actions": [
            "merge PR",
            "push tags",
            "rewrite history",
            "delete files outside scope",
        ],
    },
    "tester": {
        "responsibilities": [
            "run existing tests for affected modules",
            "summarize failures with evidence",
            "identify regression risk",
        ],
        "allowed_actions": [
            "read files",
            "run tests",
            "generate test reports",
        ],
        "blocked_actions": [
            "edit code",
            "merge",
        ],
    },
    "reviewer": {
        "responsibilities": [
            "review diff for correctness",
            "detect risk and bloat",
            "check edge cases",
            "verify acceptance criteria are met",
        ],
        "allowed_actions": [
            "read files",
            "git diff",
            "git log",
        ],
        "blocked_actions": [
            "edit code",
            "run tests",
            "merge",
        ],
    },
    "doc_writer": {
        "responsibilities": [
            "summarize code meaning in a report",
            "update docs if interface changed",
            "generate code_meaning_report.md",
        ],
        "allowed_actions": [
            "read files",
            "write docs/*_report.md",
            "write .harness/loop/runs/",
        ],
        "blocked_actions": [
            "edit source code",
            "run tests",
            "merge",
        ],
    },
    "gatekeeper": {
        "responsibilities": [
            "enforce 'no test no done' rule",
            "enforce 'no evidence no merge' rule",
            "require human for high-risk actions",
            "verify all acceptance criteria are met",
        ],
        "allowed_actions": [
            "read files",
            "git status",
            "git diff",
            "read test results",
            "read evidence",
        ],
        "blocked_actions": [
            "edit code",
            "merge without human approval",
            "push tags",
            "delete evidence",
        ],
    },
    "executor": {
        "responsibilities": [
            "inspect project files",
            "run tests and collect results",
            "collect git state (diff, status, log)",
            "generate evidence artifacts",
            "enforce safety gate",
        ],
        "allowed_actions": [
            "read files",
            "git status/diff/log",
            "run tests",
            "harness copilot inspect",
            "harness copilot readiness",
            "harness copilot task-card",
            "harness copilot pr-draft",
            "write .harness/loop/runs/",
            "write docs/*_report.md",
        ],
        "blocked_actions": [
            "git push",
            "git merge",
            "git reset",
            "git clean",
            "rm",
            "delete files",
            "modify .env",
            "deploy",
        ],
    },
    "evidence_collector": {
        "responsibilities": [
            "collect all evidence after a task completes",
            "verify integrity of changed files",
            "generate ResultEnvelope with evidence refs",
            "archive run logs",
        ],
        "allowed_actions": [
            "read files",
            "git diff",
            "git log",
            "write .harness/loop/runs/",
        ],
        "blocked_actions": [
            "edit code",
            "merge",
            "push",
        ],
    },
    "implementation_worker": {
        "responsibilities": [
            "implement assigned task nodes",
            "repair failed tasks based on review feedback",
            "explain code meaning in a report",
            "run tests or explain why not possible",
        ],
        "allowed_actions": [
            "read files",
            "edit scoped files",
            "run tests",
            "generate code_meaning_report.md",
        ],
        "blocked_actions": [
            "merge",
            "push tags",
            "edit files outside scope",
            "delete evidence",
        ],
    },
    "alternative_worker": {
        "responsibilities": [
            "alternative implementation for comparison",
            "cross-check primary worker results",
            "second review of diffs",
        ],
        "allowed_actions": [
            "read files",
            "git diff",
            "write review reports",
        ],
        "blocked_actions": [
            "merge",
            "overwrite primary worker evidence",
            "push",
        ],
    },
}


def get_role(name: str) -> dict[str, Any] | None:
    """Get a role definition by name."""
    return ROLE_DEFINITIONS.get(name)


def list_roles() -> list[str]:
    """List all available role names."""
    return list(ROLE_DEFINITIONS.keys())
