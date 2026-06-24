"""Harness Runtime — system checks, version reporting, and doctor CLI.

Usage:
    from harness.runtime import (
        get_version_info,
        format_version,
        run_doctor,
        doctor_summary,
    )
"""

from __future__ import annotations

from .doctor import doctor_summary, run_doctor
from .version import format_version, get_version_info

__all__ = [
    "doctor_summary",
    "format_version",
    "get_version_info",
    "run_doctor",
]
