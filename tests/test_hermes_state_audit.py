from __future__ import annotations

import importlib.util
import json
import os
import shutil
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_state_machine() -> dict:
    with (ROOT / ".harness/config/state_machine.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_audit_event_creation_and_validation():
    audit = load_module(ROOT / ".harness/scripts/hermes_audit.py", "hermes_audit_test")

    event = audit.create_event(
        trace_id="trace_test_001",
        task_id="task_test_001",
        actor="hermes",
        event_type="task_created",
        from_status=None,
        to_status="pending",
        payload_ref=".harness/state/task_state.json",
    )

    audit.validate_event(event)
    assert event["event_id"].startswith("evt_")
    assert event["span_id"].startswith("span_")
    assert event["trace_id"] == "trace_test_001"


def test_secret_redaction():
    audit = load_module(ROOT / ".harness/scripts/hermes_audit.py", "hermes_audit_redact_test")
    redacted = audit.redact_text("DEEPSEEK_API_KEY=abc123456789SECRET")
    assert "DEEPSEEK_API_KEY=" not in redacted or "[REDACTED_SECRET]" in redacted


# ── State machine contract tests ──────────────────────────────────────────


def test_valid_transitions_from_state_machine():
    """Validate transitions that are explicitly defined in state_machine.yaml."""
    state = load_module(ROOT / ".harness/scripts/hermes_state.py", "hermes_state_config_test")
    cfg = load_state_machine()

    # Every transition listed in yaml must be accepted by hermes_state.
    for from_state, to_list in cfg["transitions"].items():
        for to_state in to_list:
            assert state.can_transition(from_state, to_state) is True, (
                f"hermes_state rejected a valid transition: {from_state} -> {to_state}"
            )


def test_pending_cannot_directly_assign():
    """pending must go through startup_verify/permission_check before assigned."""
    state = load_module(ROOT / ".harness/scripts/hermes_state.py", "hermes_state_pending_assign")
    assert state.can_transition("pending", "assigned") is False, (
        "pending -> assigned must be rejected: startup gate required"
    )


def test_assigned_cannot_directly_run():
    """assigned must go through startup_gate + permission_check before running."""
    state = load_module(ROOT / ".harness/scripts/hermes_state.py", "hermes_state_assigned_run")
    assert state.can_transition("assigned", "running") is False, (
        "assigned -> running must be rejected: startup gate + permission check required"
    )


def test_startup_and_permission_path_exists():
    """The new startup→permission_check→assigned path must be reachable."""
    cfg = load_state_machine()
    transitions = cfg["transitions"]

    assert "pending" in transitions

    pending_next = set(transitions["pending"])

    # At least one startup/check state must be reachable from pending.
    assert any(
        item in pending_next
        for item in {
            "startup_verify",
            "startup_check_running",
            "startup_gate",
            "permission_check_running",
        }
    ), "pending must connect to a startup or permission gate state"

    # Direct old shortcuts must not exist.
    assert "assigned" not in pending_next, "pending -> assigned is a bypass and must not exist"


def test_full_startup_and_permission_flow():
    """Verify the intended happy path: pending → startup_verify → permission_check_running → permission_check_passed → assigned → startup_gate → running."""
    state = load_module(ROOT / ".harness/scripts/hermes_state.py", "hermes_state_full_flow")

    expected_flow = [
        ("pending", "startup_verify"),
        ("startup_verify", "permission_check_running"),
        ("permission_check_running", "permission_check_passed"),
        ("permission_check_passed", "assigned"),
        ("assigned", "startup_gate"),
        ("startup_gate", "running"),
    ]

    for from_state, to_state in expected_flow:
        assert state.can_transition(from_state, to_state) is True, (
            f"Expected valid transition: {from_state} -> {to_state}"
        )


def test_terminal_states_are_terminal():
    """Terminal states should not have outgoing transitions (or only to blocked/needs_human)."""
    cfg = load_state_machine()
    terminal = cfg.get("terminal", [])
    transitions = cfg.get("transitions", {})

    for term in terminal:
        if term in transitions:
            term_next = set(transitions[term])
            blocked_or_human = {"blocked", "needs_human"}
            allowed = term_next - blocked_or_human
            assert len(allowed) == 0, (
                f"Terminal state '{term}' has non-blocked/human transitions: {allowed}"
            )


def test_invalid_transition_rejected():
    state = load_module(ROOT / ".harness/scripts/hermes_state.py", "hermes_state_invalid_test")
    try:
        state.assert_transition_allowed("pending", "merged")
    except ValueError as exc:
        assert "Invalid transition" in str(exc)
    else:
        raise AssertionError("Invalid transition was not rejected")
