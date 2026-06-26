"""Tests: ProtocolAdapter normalization and legacy protocol detection."""

from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from harness.runtime.protocol_adapter import (
    CANONICAL_PROTOCOL,
    ProtocolAdapter,
    is_legacy_protocol,
)


# ---------------------------------------------------------------------------
# is_legacy_protocol
# ---------------------------------------------------------------------------


def test_is_legacy_protocol_returns_true_for_a2a():
    """harness-a2a/v1.1 is a legacy protocol."""
    assert is_legacy_protocol("harness-a2a/v1.1") is True


def test_is_legacy_protocol_returns_true_for_temp_loop():
    """temp-loop/v1 is a legacy protocol."""
    assert is_legacy_protocol("temp-loop/v1") is True


def test_is_legacy_protocol_returns_false_for_canonical():
    """harness-loop/v1 is NOT a legacy protocol."""
    assert is_legacy_protocol(CANONICAL_PROTOCOL) is False


def test_is_legacy_protocol_handles_unknown():
    """An unknown protocol is treated as legacy (not canonical)."""
    assert is_legacy_protocol("unknown-protocol") is True


# ---------------------------------------------------------------------------
# normalize_temp_loop_v1
# ---------------------------------------------------------------------------


def test_normalize_temp_loop_v1_adds_defaults():
    """temp-loop/v1 envelope gets defaults for missing harness-loop/v1 fields."""
    raw = {
        "protocol": "temp-loop/v1",
        "trace_id": "trace_001",
        "task_id": "task_001",
        "from_agent": "worker",
        "to_agent": "hermes",
        "description": "A temporary task",
        "timestamp": "2026-06-25T10:00:00Z",
    }
    normalized = ProtocolAdapter.normalize_temp_loop_v1(raw)

    # Protocol updated
    assert normalized["protocol"] == CANONICAL_PROTOCOL

    # temp-loop fields removed
    assert "description" not in normalized
    assert "timestamp" not in normalized

    # Defaults added
    assert normalized["objective"] == "A temporary task"
    assert normalized["acceptance_criteria"] == []
    assert normalized["context_refs"] == []
    assert normalized["assigned_skills"] == []
    assert normalized["allowed_actions"] == [
        "read files",
        "edit scoped files",
        "run tests",
        "generate report",
    ]
    assert "requires_human" in normalized
    assert normalized["evidence_refs"] == []
    assert normalized["created_at"] == "2026-06-25T10:00:00Z"


def test_normalize_temp_loop_v1_preserves_existing_fields():
    """Fields already present in the envelope are not overwritten."""
    raw = {
        "protocol": "temp-loop/v1",
        "trace_id": "trace_001",
        "task_id": "task_001",
        "from_agent": "worker",
        "to_agent": "hermes",
        "objective": "Custom objective",
        "acceptance_criteria": ["AC-1", "AC-2"],
        "evidence_refs": ["evidence_1.json"],
    }
    normalized = ProtocolAdapter.normalize_temp_loop_v1(raw)

    assert normalized["protocol"] == CANONICAL_PROTOCOL
    assert normalized["objective"] == "Custom objective"
    assert normalized["acceptance_criteria"] == ["AC-1", "AC-2"]
    assert normalized["evidence_refs"] == ["evidence_1.json"]


# ---------------------------------------------------------------------------
# normalize_a2a_v1_1
# ---------------------------------------------------------------------------


def test_normalize_a2a_v1_1_converts_fields():
    """a2a v1.1 envelope fields are mapped to harness-loop/v1 equivalents."""
    raw = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_a2a_001",
        "task_id": "task_a2a_001",
        "from_agent": "opencode_worker",
        "to_agent": "hermes",
        "status": "completed_for_review",
        "round": 1,
        "changed_files": ["src/main.py"],
        "test_result": {
            "passed": True,
            "command": "pytest",
            "summary": "All good",
            "log_ref": "test_evidence.json",
        },
        "diff_ref": "HEAD~1",
        "acceptance_mapping": [
            {"criterion": "COP-1", "status": "passed", "evidence": "cli.py updated"},
        ],
        "notes": "All COP items implemented",
        "known_risks": [],
        "completed_at": "2026-06-24T14:00:00Z",
    }
    normalized = ProtocolAdapter.normalize_a2a_v1_1(raw)

    # Protocol updated
    assert normalized["protocol"] == CANONICAL_PROTOCOL

    # Fields preserved
    assert normalized["trace_id"] == "trace_a2a_001"
    assert normalized["task_id"] == "task_a2a_001"
    assert normalized["from_agent"] == "opencode_worker"
    assert normalized["to_agent"] == "hermes"
    assert normalized["status"] == "completed_for_review"

    # test_result: log_ref stripped
    assert normalized["test_result"] == {
        "passed": True,
        "command": "pytest",
        "summary": "All good",
    }
    assert "log_ref" not in normalized["test_result"]

    # diff_ref -> code_meaning_report
    assert normalized["code_meaning_report"]["what_changed"] == "HEAD~1"

    # acceptance_mapping + notes -> evidence_refs
    assert "cli.py updated" in normalized["evidence_refs"]
    assert any("note: All COP items implemented" in r for r in normalized["evidence_refs"])

    # a2a-specific fields dropped
    assert "round" not in normalized
    assert "known_risks" not in normalized
    assert "diff_ref" not in normalized
    assert "acceptance_mapping" not in normalized
    assert "notes" not in normalized


def test_normalize_a2a_v1_1_minimal():
    """A minimal a2a envelope is normalized without error."""
    raw = {
        "protocol": "harness-a2a/v1.1",
        "trace_id": "trace_min",
        "task_id": "task_min",
        "from_agent": "worker",
        "to_agent": "hermes",
        "status": "failed",
    }
    normalized = ProtocolAdapter.normalize_a2a_v1_1(raw)

    assert normalized["protocol"] == CANONICAL_PROTOCOL
    assert normalized["status"] == "failed"
    # Default test_result
    assert normalized["test_result"] == {
        "passed": False,
        "command": "",
        "summary": "",
    }
    # Empty evidence_refs
    assert normalized["evidence_refs"] == []
    # code_meaning_report with empty diff_ref
    assert normalized["code_meaning_report"]["what_changed"] == ""
