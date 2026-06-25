"""Tests: Runtime result_envelope schema validation with canonical/legacy modes."""

from __future__ import annotations

import json
import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.runtime.envelope_validator import (
    CANONICAL_PROTOCOL,
    _schema_path,
    clear_schema_cache,
    load_result_envelope_schema,
    validate_envelope,
    validate_result_envelope,
)


# ===================================================================
# Schema file / load tests (unchanged)
# ===================================================================


def test_schema_file_exists():
    """result_envelope.schema.json exists at expected path."""
    path = _schema_path()
    assert os.path.isfile(path), f"Schema not found: {path}"


def test_schema_loads_valid_json():
    """Schema file is valid JSON."""
    schema = load_result_envelope_schema()
    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert schema["title"] == "Harness A2A Result Envelope"


def test_clear_schema_cache():
    """clear_schema_cache resets the cached schema."""
    schema = load_result_envelope_schema()
    assert schema is not None
    clear_schema_cache()
    schema2 = load_result_envelope_schema()
    assert schema2 is not None


def test_schema_has_required_definitions():
    """Schema contains all expected required fields."""
    schema = load_result_envelope_schema()
    required = schema.get("required", [])
    for field in [
        "protocol",
        "trace_id",
        "task_id",
        "status",
        "changed_files",
        "test_result",
        "acceptance_mapping",
        "completed_at",
    ]:
        assert field in required, f"Required field '{field}' not in schema"


# ===================================================================
# Existing envelope tests — updated to harness-loop/v1
# ===================================================================


def test_valid_envelope_passes():
    """A valid harness-loop/v1 envelope passes validation (legacy mode)."""
    envelope = {
        "protocol": "harness-loop/v1",
        "trace_id": "trace_test_001",
        "task_id": "task_test_001",
        "from_agent": "opencode_worker",
        "to_agent": "hermes",
        "status": "completed_for_review",
        "changed_files": ["test/file.py"],
        "test_result": {
            "passed": True,
            "command": "pytest tests/",
            "summary": "All tests passed",
        },
        "evidence_refs": [],
        "code_meaning_report": {
            "what_changed": "",
            "why_changed": "",
            "impact": "",
            "risk": "",
            "tests": "",
        },
        "completed_at": "2026-06-24T14:00:00Z",
    }
    is_valid, errors = validate_result_envelope(envelope)
    assert is_valid, f"Expected valid envelope but got errors: {errors}"
    assert len(errors) == 0


def test_invalid_envelope_missing_required_field():
    """Missing required fields fail validation."""
    envelope = {
        "protocol": "harness-loop/v1",
    }
    is_valid, errors = validate_result_envelope(envelope)
    assert not is_valid
    assert len(errors) > 0


def test_invalid_envelope_bad_status():
    """Invalid status in legacy mode fails JSON schema validation."""
    # Use a2a protocol so JSON schema validation (with enum) is triggered
    envelope = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_test_001",
        "task_id": "task_test_001",
        "from_agent": "opencode_worker",
        "to_agent": "hermes",
        "status": "invalid_status",
        "round": 1,
        "changed_files": [],
        "test_result": {
            "passed": True,
            "command": "pytest",
            "summary": "",
            "log_ref": "",
        },
        "diff_ref": "HEAD",
        "acceptance_mapping": [],
        "notes": "",
        "known_risks": [],
        "completed_at": "2026-06-24T14:00:00Z",
    }
    is_valid, errors = validate_result_envelope(envelope)
    assert not is_valid
    assert len(errors) > 0


def test_invalid_envelope_wrong_protocol():
    """Wrong protocol in canonical mode is rejected."""
    envelope = {
        "protocol": "wrong-protocol",
        "trace_id": "trace_test_001",
        "task_id": "task_test_001",
        "from_agent": "opencode_worker",
        "to_agent": "hermes",
        "status": "completed_for_review",
        "changed_files": [],
        "test_result": {
            "passed": True,
            "command": "pytest",
            "summary": "",
        },
        "completed_at": "2026-06-24T14:00:00Z",
    }
    is_valid, errors = validate_envelope(envelope, mode="canonical")
    assert not is_valid
    assert len(errors) > 0


def test_invalid_envelope_empty_envelope():
    """Empty dict fails validation."""
    is_valid, errors = validate_result_envelope({})
    assert not is_valid
    assert len(errors) > 0


def test_valid_envelope_minimal():
    """A minimal but valid harness-loop/v1 envelope passes."""
    envelope = {
        "protocol": "harness-loop/v1",
        "trace_id": "trace_minimal_001",
        "task_id": "task_minimal_001",
        "from_agent": "worker",
        "to_agent": "hermes",
        "status": "failed",
        "changed_files": [],
        "test_result": {
            "passed": False,
            "command": "pytest",
            "summary": "Tests failed",
        },
        "evidence_refs": [],
        "code_meaning_report": {
            "what_changed": "",
            "why_changed": "",
            "impact": "",
            "risk": "",
            "tests": "",
        },
        "completed_at": "",
    }
    is_valid, errors = validate_result_envelope(envelope)
    assert is_valid, f"Expected valid envelope but got errors: {errors}"


# ===================================================================
# New tests: canonical / legacy mode protocol enforcement
# ===================================================================


def test_canonical_rejects_a2a_v1_1():
    """Canonical mode rejects harness-a2a/v1.1 protocol."""
    envelope = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_001",
        "task_id": "task_001",
        "from_agent": "worker",
        "to_agent": "hermes",
    }
    is_valid, errors = validate_envelope(envelope, mode="canonical")
    assert not is_valid
    assert any("harness-loop/v1" in err for err in errors)


def test_canonical_rejects_temp_loop_v1():
    """Canonical mode rejects temp-loop/v1 protocol."""
    envelope = {
        "protocol": "temp-loop/v1",
        "trace_id": "trace_001",
        "task_id": "task_001",
        "from_agent": "worker",
        "to_agent": "hermes",
    }
    is_valid, errors = validate_envelope(envelope, mode="canonical")
    assert not is_valid
    assert any("harness-loop/v1" in err for err in errors)


def test_canonical_rejects_unknown_protocol():
    """Canonical mode rejects an unknown/non-loop protocol."""
    envelope = {
        "protocol": "some-other-protocol",
        "trace_id": "trace_001",
        "task_id": "task_001",
    }
    is_valid, errors = validate_envelope(envelope, mode="canonical")
    assert not is_valid
    assert any("harness-loop/v1" in err for err in errors)


def test_legacy_accepts_a2a_v1_1():
    """Legacy mode accepts harness-a2a/v1.1 envelopes."""
    envelope = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_legacy_001",
        "task_id": "task_legacy_001",
        "from_agent": "worker",
        "to_agent": "hermes",
    }
    # Legacy mode passes protocol check; will fail field validation
    # but NOT on protocol rejection.
    is_valid, errors = validate_envelope(envelope, mode="legacy")
    # It may fail on missing fields (a2a requires status, changed_files)
    # but the key assertion is that it's NOT rejected for protocol.
    protocol_errors = [e for e in errors if "protocol" in e.lower()]
    assert all(
        "reject" not in e.lower() and "harness-loop/v1" not in e
        for e in protocol_errors
    )


def test_legacy_accepts_temp_loop_v1():
    """Legacy mode accepts temp-loop/v1 envelopes."""
    envelope = {
        "protocol": "temp-loop/v1",
        "trace_id": "trace_temp_001",
        "task_id": "task_temp_001",
        "from_agent": "worker",
        "to_agent": "hermes",
    }
    is_valid, errors = validate_envelope(envelope, mode="legacy")
    # Not rejected on protocol
    protocol_errors = [e for e in errors if "protocol" in e.lower()]
    assert all(
        "reject" not in e.lower() and "harness-loop/v1" not in e
        for e in protocol_errors
    )


def test_canonical_accepts_valid_loop_v1():
    """Canonical mode accepts a valid harness-loop/v1 envelope."""
    envelope = {
        "protocol": "harness-loop/v1",
        "trace_id": "trace_canon_001",
        "task_id": "task_canon_001",
        "from_agent": "hermes",
        "to_agent": "worker",
        "status": "in_progress",
        "changed_files": [],
        "test_result": {
            "passed": True,
            "command": "pytest",
            "summary": "ok",
        },
        "evidence_refs": [],
        "code_meaning_report": {
            "what_changed": "",
            "why_changed": "",
            "impact": "",
            "risk": "",
            "tests": "",
        },
        "completed_at": "",
    }
    is_valid, errors = validate_envelope(envelope, mode="canonical")
    assert is_valid, f"Expected valid envelope but got errors: {errors}"
