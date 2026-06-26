"""Protocol adapter — normalize envelopes across protocol versions.

Provides:
- ProtocolAdapter class for normalizing temp-loop/v1 and harness-a2a/v1.1
  envelopes to the canonical harness-loop/v1 format.
- is_legacy_protocol() to distinguish legacy protocols from canonical.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

CANONICAL_PROTOCOL = "harness-loop/v1"
LEGACY_PROTOCOLS: set[str] = {"harness-a2a/v1.1", "temp-loop/v1"}


def is_legacy_protocol(protocol: str) -> bool:
    """Return True if *protocol* is a known legacy protocol.

    Canonical (non-legacy) protocol is ``harness-loop/v1``.
    """
    return protocol != CANONICAL_PROTOCOL


class ProtocolAdapter:
    """Normalize envelopes from legacy protocols to harness-loop/v1."""

    @staticmethod
    def normalize_temp_loop_v1(envelope: dict[str, Any]) -> dict[str, Any]:
        """Convert a temp-loop/v1 envelope to harness-loop/v1.

        temp-loop/v1 is a minimal scaffolding envelope that may lack
        several harness-loop/v1 fields.  Missing optional fields are
        filled with sensible defaults.
        """
        normalized = deepcopy(envelope)
        normalized["protocol"] = CANONICAL_PROTOCOL

        # Map temp-loop specific fields to harness-loop equivalents
        if "objective" not in normalized:
            normalized["objective"] = normalized.get("description", "")
        if "acceptance_criteria" not in normalized:
            normalized["acceptance_criteria"] = []
        if "context_refs" not in normalized:
            normalized["context_refs"] = []
        if "assigned_skills" not in normalized:
            normalized["assigned_skills"] = []
        if "allowed_actions" not in normalized:
            normalized["allowed_actions"] = [
                "read files",
                "edit scoped files",
                "run tests",
                "generate report",
            ]
        if "requires_human" not in normalized:
            normalized["requires_human"] = [
                "merge PR",
                "push tag",
                "force push",
                "deploy",
            ]
        if "evidence_refs" not in normalized:
            normalized["evidence_refs"] = []
        if "created_at" not in normalized:
            normalized["created_at"] = normalized.get("timestamp", "")

        # Remove temp-loop specific fields that don't exist in loop/v1
        normalized.pop("description", None)
        normalized.pop("timestamp", None)

        return normalized

    @staticmethod
    def normalize_a2a_v1_1(envelope: dict[str, Any]) -> dict[str, Any]:
        """Convert a harness-a2a/v1.1 envelope to harness-loop/v1.

        The a2a v1.1 schema uses ``test_result.log_ref``,
        ``diff_ref``, ``acceptance_mapping``, ``notes``, and
        ``known_risks``.  These are mapped to harness-loop/v1
        equivalents where possible.
        """
        normalized = deepcopy(envelope)
        normalized["protocol"] = CANONICAL_PROTOCOL

        # Ensure test_result has the loop/v1 shape
        test_result = normalized.get("test_result", {})
        if isinstance(test_result, dict):
            # Preserve the 3 loop/v1 fields; drop legacy log_ref
            loop_test_result: dict[str, Any] = {
                "passed": test_result.get("passed", False),
                "command": test_result.get("command", ""),
                "summary": test_result.get("summary", ""),
            }
            normalized["test_result"] = loop_test_result

        # Map diff_ref -> code_meaning_report if not already present
        if "code_meaning_report" not in normalized:
            diff_ref = normalized.pop("diff_ref", None)
            normalized["code_meaning_report"] = {
                "what_changed": str(diff_ref or ""),
                "why_changed": "",
                "impact": "",
                "risk": "",
                "tests": "",
            }

        # Map acceptance_mapping + notes -> evidence_refs
        evidence_refs: list[str] = []
        acceptance_mapping = normalized.pop("acceptance_mapping", [])
        if acceptance_mapping:
            for item in acceptance_mapping if isinstance(acceptance_mapping, list) else []:
                if isinstance(item, dict) and item.get("evidence"):
                    evidence_refs.append(str(item["evidence"]))
        notes = normalized.pop("notes", None)
        if notes:
            evidence_refs.append(f"note: {notes}")
        normalized["evidence_refs"] = evidence_refs or normalized.get("evidence_refs", [])

        # Drop a2a-specific fields that have no loop/v1 equivalent
        normalized.pop("known_risks", None)
        normalized.pop("round", None)

        return normalized
