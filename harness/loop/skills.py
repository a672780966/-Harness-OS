"""Skill assignments for loop installer roles."""

from __future__ import annotations

from typing import Any

SKILL_ASSIGNMENTS: dict[str, list[str]] = {
    "planner": [
        "break_down_objective",
        "define_acceptance_criteria",
        "order_task_nodes",
        "identify_cross_module_impact",
    ],
    "coder": [
        "implement_minimal_diff",
        "reuse_existing_patterns",
        "add_inline_comments",
        "run_tests_after_implementation",
    ],
    "tester": [
        "run_existing_tests",
        "summarize_failures",
        "identify_regression_risk",
    ],
    "reviewer": [
        "review_diff_correctness",
        "detect_risk_and_bloat",
        "check_edge_cases",
        "verify_acceptance_criteria",
    ],
    "doc_writer": [
        "summarize_code_meaning",
        "update_docs_on_interface_change",
        "generate_code_meaning_report",
    ],
    "gatekeeper": [
        "enforce_no_test_no_done",
        "enforce_no_evidence_no_merge",
        "require_human_for_high_risk",
        "verify_all_acceptance_criteria",
    ],
    "executor": [
        "inspect_project_files",
        "run_tests_and_collect",
        "collect_git_state",
        "generate_evidence_artifacts",
        "enforce_safety_gate",
    ],
    "evidence_collector": [
        "collect_evidence_after_task",
        "verify_integrity",
        "generate_result_envelope",
        "archive_run_logs",
    ],
    "implementation_worker": [
        "implement_task_node",
        "repair_failed_task",
        "explain_code_meaning",
        "run_tests_or_explain",
    ],
    "alternative_worker": [
        "alternative_implementation",
        "cross_check_primary",
        "second_review_diff",
    ],
}


def get_skills_for_role(role: str) -> list[str]:
    """Get skills assigned to a role."""
    return SKILL_ASSIGNMENTS.get(role, [])


def generate_skills_yaml(role_assignments: dict[str, list[str]]) -> str:
    """Generate skills.yaml content from role assignments."""
    lines = ["# Harness Loop — Skill Assignments", ""]
    for role, skills in role_assignments.items():
        lines.append(f"{role}:")
        for s in skills:
            lines.append(f"  - {s}")
        lines.append("")
    return "\n".join(lines)
