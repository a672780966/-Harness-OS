"""A2A envelope generation for loop installer."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any


def create_task_envelope(
    trace_id: str,
    task_id: str,
    from_agent: str,
    to_agent: str,
    objective: str,
    acceptance_criteria: list[str],
    context_refs: list[str] | None = None,
    assigned_skills: list[str] | None = None,
) -> str:
    """Generate a TaskEnvelope JSON string."""
    envelope: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "trace_id": trace_id,
        "task_id": task_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "objective": objective,
        "acceptance_criteria": acceptance_criteria,
        "context_refs": context_refs or [],
        "assigned_skills": assigned_skills or [],
        "allowed_actions": [
            "read files",
            "edit scoped files",
            "run tests",
            "generate report",
        ],
        "requires_human": [
            "merge PR",
            "push tag",
            "force push",
            "rewrite history",
            "deploy",
        ],
        "created_at": datetime.now().astimezone().isoformat(),
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def create_result_envelope(
    trace_id: str,
    task_id: str,
    from_agent: str,
    to_agent: str,
    status: str,
    changed_files: list[str],
    test_passed: bool,
    test_command: str,
    test_summary: str,
    evidence_refs: list[str] | None = None,
    code_meaning: dict[str, str] | None = None,
) -> str:
    """Generate a ResultEnvelope JSON string."""
    envelope: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "trace_id": trace_id,
        "task_id": task_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "status": status,
        "changed_files": changed_files,
        "test_result": {
            "passed": test_passed,
            "command": test_command,
            "summary": test_summary,
        },
        "evidence_refs": evidence_refs or [],
        "code_meaning_report": code_meaning or {
            "what_changed": "",
            "why_changed": "",
            "impact": "",
            "risk": "",
            "tests": "",
        },
        "completed_at": datetime.now().astimezone().isoformat(),
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def create_review_envelope(
    trace_id: str,
    task_id: str,
    from_agent: str,
    to_agent: str,
    status: str,
    blocking_issues: list[dict[str, str]] | None = None,
    required_fixes: list[str] | None = None,
    merge_ready: bool = False,
) -> str:
    """Generate a ReviewEnvelope JSON string."""
    envelope: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "trace_id": trace_id,
        "task_id": task_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "status": status,
        "blocking_issues": blocking_issues or [],
        "required_fixes": required_fixes or [],
        "merge_ready": merge_ready,
        "reviewed_at": datetime.now().astimezone().isoformat(),
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def create_repair_envelope(
    trace_id: str,
    task_id: str,
    from_agent: str,
    to_agent: str,
    repair_round: int,
    blocking_issues: list[dict[str, str]] | None = None,
    focus_instructions: str = "",
) -> str:
    """Generate a RepairEnvelope JSON string (harness-loop/v1)."""
    envelope: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "trace_id": trace_id,
        "task_id": task_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "envelope_type": "repair",
        "repair_round": repair_round,
        "blocking_issues": blocking_issues or [],
        "focus_instructions": focus_instructions,
        "created_at": datetime.now().astimezone().isoformat(),
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def create_final_evidence_envelope(
    trace_id: str,
    task_id: str,
    from_agent: str,
    to_agent: str,
    status: str,
    evidence_refs: list[str] | None = None,
    final_report: str = "",
) -> str:
    """Generate a FinalEvidenceEnvelope JSON string (harness-loop/v1)."""
    envelope: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "trace_id": trace_id,
        "task_id": task_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "envelope_type": "final_evidence",
        "status": status,
        "evidence_refs": evidence_refs or [],
        "final_report": final_report,
        "completed_at": datetime.now().astimezone().isoformat(),
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def create_audit_event(
    trace_id: str,
    task_id: str,
    actor: str,
    action: str,
    payload: dict[str, Any] | None = None,
    payload_ref: str | None = None,
) -> str:
    """Generate an AuditEvent JSON string (harness-loop/v1)."""
    envelope: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "trace_id": trace_id,
        "task_id": task_id,
        "actor": actor,
        "action": action,
        "envelope_type": "audit_event",
        "payload": payload or {},
        "payload_ref": payload_ref or "",
        "timestamp": datetime.now().astimezone().isoformat(),
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def create_state_transition(
    trace_id: str,
    task_id: str,
    from_state: str,
    to_state: str,
    reason: str = "",
) -> str:
    """Generate a StateTransition JSON string (harness-loop/v1)."""
    envelope: dict[str, Any] = {
        "protocol": "harness-loop/v1",
        "trace_id": trace_id,
        "task_id": task_id,
        "envelope_type": "state_transition",
        "from_state": from_state,
        "to_state": to_state,
        "reason": reason,
        "timestamp": datetime.now().astimezone().isoformat(),
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)
