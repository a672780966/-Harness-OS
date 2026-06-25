"""Harness Runtime — system checks, version reporting, doctor CLI,
envelope validation, and protocol normalization.

Usage:
    from harness.runtime import (
        get_version_info,
        format_version,
        run_doctor,
        doctor_summary,
        validate_envelope,
        validate_result_envelope,
        load_result_envelope_schema,
        clear_schema_cache,
        ProtocolAdapter,
        is_legacy_protocol,
    )
"""

from __future__ import annotations

from .doctor import doctor_summary, run_doctor
from .envelope_validator import (
    clear_schema_cache,
    load_result_envelope_schema,
    validate_envelope,
    validate_result_envelope,
)
from .protocol_adapter import ProtocolAdapter, is_legacy_protocol
from .version import format_version, get_version_info

__all__ = [
    "clear_schema_cache",
    "doctor_summary",
    "format_version",
    "get_version_info",
    "is_legacy_protocol",
    "load_result_envelope_schema",
    "ProtocolAdapter",
    "run_doctor",
    "validate_envelope",
    "validate_result_envelope",
]
