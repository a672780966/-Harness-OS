"""Envelope schema validator — validate envelopes against JSON Schema.

Supports two modes:
  - canonical (default): protocol MUST be ``harness-loop/v1``.
  - legacy: any protocol is accepted.

Provides:
  - ``validate_envelope(envelope, mode='canonical')`` — generic validation.
  - ``validate_result_envelope(envelope)`` — backward-compatible legacy wrapper.
  - ``_validate_required_fields`` — per-schema-type required-field check.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CANONICAL_PROTOCOL = "harness-loop/v1"
LEGACY_PROTOCOLS = {"harness-a2a/v1.1", "temp-loop/v1"}

_SCHEMA_CACHE: Optional[Dict[str, Any]] = None


def _get_project_root() -> str:
    """Return the absolute path of the project root."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _schema_path() -> str:
    """Return the absolute path of the result envelope JSON Schema."""
    return os.path.join(
        _get_project_root(), ".harness", "envelopes", "schema", "result_envelope.schema.json"
    )


def load_result_envelope_schema() -> Dict[str, Any]:
    """Load the result_envelope JSON Schema from disk.

    Returns:
        The parsed JSON Schema dict.

    Raises:
        FileNotFoundError: If the schema file is missing.
        json.JSONDecodeError: If the schema file is not valid JSON.
    """
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE
    path = _schema_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Result envelope schema not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


def clear_schema_cache() -> None:
    """Clear the cached schema (useful in tests)."""
    global _SCHEMA_CACHE
    _SCHEMA_CACHE = None


def _detect_schema_type(envelope: Dict[str, Any]) -> str:
    """Detect the schema type based on the envelope's *protocol* field."""
    protocol = envelope.get("protocol", "")
    if protocol == "harness-loop/v1":
        return "loop_v1"
    if protocol == "harness-a2a/v1.1":
        return "a2a_v1_1"
    if protocol == "temp-loop/v1":
        return "temp_loop_v1"
    return "unknown"


def _validate_required_fields(
    envelope: Dict[str, Any],
    schema_type: str = "a2a_v1_1",
) -> Tuple[bool, List[str]]:
    """Fallback: basic required-field check per schema type.

    Used when ``jsonschema`` is not installed, or when the envelope
    protocol does not match the on-disk a2a schema.
    """
    REQUIRED: Dict[str, List[str]] = {
        "loop_v1": [
            "protocol",
            "trace_id",
            "task_id",
            "from_agent",
            "to_agent",
        ],
        "a2a_v1_1": [
            "protocol",
            "trace_id",
            "task_id",
            "status",
            "changed_files",
        ],
        "temp_loop_v1": [
            "protocol",
            "trace_id",
            "task_id",
        ],
    }
    fields = REQUIRED.get(schema_type, REQUIRED["a2a_v1_1"])
    errors = []
    for field in fields:
        if field not in envelope:
            errors.append(f"Missing required field: {field}")
    return (len(errors) == 0, errors)


def validate_envelope(
    envelope: Dict[str, Any],
    mode: str = "canonical",
) -> Tuple[bool, List[str]]:
    """Validate an envelope with protocol-mode enforcement.

    Args:
        envelope: The envelope dict to validate.
        mode:
            ``'canonical'`` (default) — protocol MUST be ``harness-loop/v1``;
            ``'legacy'`` — accept any protocol.

    Returns:
        ``(is_valid, errors)`` tuple.
    """
    protocol = envelope.get("protocol", "")

    # ── Mode enforcement ────────────────────────────────────────────
    if mode == "canonical":
        if protocol != CANONICAL_PROTOCOL:
            return False, [
                f"Canonical mode requires protocol='{CANONICAL_PROTOCOL}', "
                f"got '{protocol}'"
            ]
    # Legacy mode accepts any protocol; no enforcement.

    schema_type = _detect_schema_type(envelope)

    # ── Try full JSON Schema validation (a2a only) ──────────────────
    try:
        import jsonschema  # noqa: PLC0415
    except ImportError:
        return _validate_required_fields(envelope, schema_type)

    try:
        schema = load_result_envelope_schema()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return False, [f"Schema load error: {e}"]

    if schema_type == "a2a_v1_1":
        try:
            jsonschema.validate(instance=envelope, schema=schema)
            return True, []
        except jsonschema.exceptions.ValidationError as e:
            return False, [e.message]
        except Exception as e:
            return False, [str(e)]

    # Non-a2a envelopes: field-level validation (the on-disk schema is
    # a2a-specific and would reject harness-loop/v1's ``const``).
    return _validate_required_fields(envelope, schema_type)


def validate_result_envelope(
    envelope: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Backward-compatible validation of a result envelope (legacy mode).

    Delegates to ``validate_envelope`` with ``mode='legacy'`` so that
    callers that pass ``harness-a2a/v1.1`` envelopes continue to work
    unchanged.
    """
    return validate_envelope(envelope, mode="legacy")
