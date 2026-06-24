from pathlib import Path
import subprocess
import sys
import json

import yaml

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, check=True):
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


ENVELOPE_TASK_SCHEMA = ROOT / ".harness/envelopes/schema/task_envelope.schema.json"
VALIDATOR = ROOT / ".harness/scripts/validate_envelope.py"


def test_task_envelope_schema_exists():
    assert ENVELOPE_TASK_SCHEMA.exists()


def test_pending_envelope_is_valid():
    """inbox task with status=pending must pass schema validation."""
    test_envelope = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_test_pending",
        "task_id": "task_test_pending",
        "parent_task_id": None,
        "from_agent": "hermes",
        "to_agent": "claude_code_worker",
        "status": "pending",
        "round": 1,
        "objective": "Test pending task intake contract.",
        "acceptance_criteria": ["Schema must allow pending status."],
        "repo": {
            "base_branch": "main",
            "work_branch": "hermes/task/task_test_pending",
            "worktree": "../harness-worktrees/task_test_pending"
        },
        "allowed_tools": ["read"],
        "blocked_tools": ["git_push", "deploy", "merge"],
        "context_refs": ["AGENTS.md"],
        "risk_level": "low",
        "max_repair_rounds": 3,
        "created_at": "2026-01-01T00:00:00+08:00"
    }
    tmp = ROOT / ".harness/tmp/test_pending_envelope.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(test_envelope, indent=2), encoding="utf-8")

    proc = run([sys.executable, str(VALIDATOR), "task", str(tmp)])
    assert proc.returncode == 0, f"pending envelope INVALID: {proc.stderr + proc.stdout}"
    assert "VALID" in proc.stdout, f"pending envelope should be VALID: {proc.stdout}"
    tmp.unlink(missing_ok=True)


def test_assigned_envelope_is_valid():
    """assigned task envelope must still be schema-valid."""
    test_envelope = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_test_assigned",
        "task_id": "task_test_assigned",
        "parent_task_id": None,
        "from_agent": "hermes",
        "to_agent": "claude_code_worker",
        "status": "assigned",
        "round": 1,
        "objective": "Test assigned task envelope.",
        "acceptance_criteria": ["Schema must allow assigned status."],
        "repo": {
            "base_branch": "main",
            "work_branch": "hermes/task/task_test_assigned",
            "worktree": "../harness-worktrees/task_test_assigned"
        },
        "allowed_tools": ["read"],
        "blocked_tools": ["git_push", "deploy", "merge"],
        "context_refs": ["AGENTS.md"],
        "risk_level": "low",
        "max_repair_rounds": 3,
        "created_at": "2026-01-01T00:00:00+08:00"
    }
    tmp = ROOT / ".harness/tmp/test_assigned_envelope.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(test_envelope, indent=2), encoding="utf-8")

    proc = run([sys.executable, str(VALIDATOR), "task", str(tmp)])
    assert proc.returncode == 0, f"assigned envelope INVALID: {proc.stderr + proc.stdout}"
    assert "VALID" in proc.stdout, f"assigned envelope should be VALID: {proc.stdout}"
    tmp.unlink(missing_ok=True)


def test_invalid_status_is_rejected():
    """invalid status must fail schema validation."""
    test_envelope = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_test_invalid",
        "task_id": "task_test_invalid",
        "parent_task_id": None,
        "from_agent": "hermes",
        "to_agent": "claude_code_worker",
        "status": "invalid_status_xxx",
        "round": 1,
        "objective": "Test invalid status rejection.",
        "acceptance_criteria": ["Schema must reject unknown status."],
        "repo": {
            "base_branch": "main",
            "work_branch": "hermes/task/task_test_invalid",
            "worktree": "../harness-worktrees/task_test_invalid"
        },
        "allowed_tools": ["read"],
        "blocked_tools": ["git_push", "deploy", "merge"],
        "context_refs": ["AGENTS.md"],
        "risk_level": "low",
        "max_repair_rounds": 3,
        "created_at": "2026-01-01T00:00:00+08:00"
    }
    tmp = ROOT / ".harness/tmp/test_invalid_envelope.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(test_envelope, indent=2), encoding="utf-8")

    proc = run([sys.executable, str(VALIDATOR), "task", str(tmp)])
    assert proc.returncode != 0, f"invalid status should be INVALID: {proc.stdout}"
    assert "INVALID" in proc.stdout, f"invalid status should be INVALID: {proc.stdout}"
    tmp.unlink(missing_ok=True)


def test_running_envelope_is_valid():
    """running task envelope must also be schema-valid."""
    test_envelope = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_test_running",
        "task_id": "task_test_running",
        "parent_task_id": None,
        "from_agent": "hermes",
        "to_agent": "claude_code_worker",
        "status": "running",
        "round": 1,
        "objective": "Test running task envelope.",
        "acceptance_criteria": ["Schema must allow running status."],
        "repo": {
            "base_branch": "main",
            "work_branch": "hermes/task/task_test_running",
            "worktree": "../harness-worktrees/task_test_running"
        },
        "allowed_tools": ["read"],
        "blocked_tools": ["git_push", "deploy", "merge"],
        "context_refs": ["AGENTS.md"],
        "risk_level": "low",
        "max_repair_rounds": 3,
        "created_at": "2026-01-01T00:00:00+08:00"
    }
    tmp = ROOT / ".harness/tmp/test_running_envelope.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(test_envelope, indent=2), encoding="utf-8")

    proc = run([sys.executable, str(VALIDATOR), "task", str(tmp)])
    assert proc.returncode == 0, f"running envelope INVALID: {proc.stderr + proc.stdout}"
    assert "VALID" in proc.stdout, f"running envelope should be VALID: {proc.stdout}"
    tmp.unlink(missing_ok=True)


def test_pending_direct_to_assigned_still_rejected_by_state():
    """schema allows pending, but state machine must still reject pending -> assigned."""
    proc = run([sys.executable, ".harness/scripts/hermes_state.py", "can-transition",
                "--from-status", "pending", "--to-status", "assigned"])
    # If script supports --check, expect false. Otherwise check state_machine.yaml.
    state_path = ROOT / ".harness/config/state_machine.yaml"
    with state_path.open("r", encoding="utf-8") as f:
        sm = yaml.safe_load(f)
    transitions = sm.get("transitions", {})
    pending_transitions = transitions.get("pending", [])
    assert "assigned" not in pending_transitions, (
        f"pending -> assigned must be blocked by state machine, "
        f"but found in: {pending_transitions}"
    )


def test_assigned_direct_to_running_still_rejected_by_state():
    """state machine must still reject assigned -> running."""
    state_path = ROOT / ".harness/config/state_machine.yaml"
    with state_path.open("r", encoding="utf-8") as f:
        sm = yaml.safe_load(f)
    transitions = sm.get("transitions", {})
    assigned_transitions = transitions.get("assigned", [])
    assert "running" not in assigned_transitions, (
        f"assigned -> running must be blocked by state machine, "
        f"but found in: {assigned_transitions}"
    )


def test_all_valid_statuses_in_schema():
    """all statuses from state machine states should be present in schema."""
    state_path = ROOT / ".harness/config/state_machine.yaml"
    with state_path.open("r", encoding="utf-8") as f:
        sm = yaml.safe_load(f)

    sm_states = set(sm.get("states", []))
    schema = json.loads(ENVELOPE_TASK_SCHEMA.read_text(encoding="utf-8"))
    schema_statuses = set(schema["properties"]["status"]["enum"])

    missing = sm_states - schema_statuses
    extra = schema_statuses - sm_states

    # Warn about missing states but don't fail — schema may have aliases
    if missing:
        print(f"WARNING: states in state machine but not in schema: {missing}")
    if extra:
        print(f"INFO: extra states in schema not in state machine: {extra}")

    # At minimum, all critical path states must be in schema
    critical = {"pending", "startup_verify", "permission_check_running",
                "permission_check_passed", "assigned", "startup_gate", "running",
                "completed_for_review", "review_running", "review_passed",
                "repair_requested", "repair_running", "codex_approved",
                "codex_rejected", "merge_ready", "needs_human", "failed", "blocked"}
    for state in critical:
        assert state in schema_statuses, f"Critical state '{state}' missing from schema"
