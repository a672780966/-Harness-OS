"""Evidence Pack — build evidence packs from loop artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import (
    EvidencePack,
    EvidenceEntry,
    TaskCard,
    VerificationEntry,
    now_iso,
    generate_id,
    to_json,
)


def build_from_task_cards(
    cards: List[TaskCard],
    pack_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> EvidencePack:
    """Build an evidence pack from task card verification entries."""
    entries: List[EvidenceEntry] = []
    passed = 0
    failed = 0

    for card in cards:
        for ver in card.evidence:
            is_passed = ver.status == "passed"
            entry = EvidenceEntry(
                ref_id=generate_id("ev"),
                evidence_type=ver.method.value if hasattr(ver.method, "value") else str(ver.method),
                file_path=ver.artifact_path,
                summary=ver.summary or f"{card.title}: {ver.status}",
                passed=is_passed,
                timestamp=ver.timestamp or now_iso(),
            )
            entries.append(entry)
            if is_passed:
                passed += 1
            else:
                failed += 1

    return EvidencePack(
        pack_id=pack_id or generate_id("pack"),
        task_id=task_id,
        entries=entries,
        total_entries=len(entries),
        passed_count=passed,
        failed_count=failed,
        generated_at=now_iso(),
    )


def build_from_directory(
    evidence_dir: str,
    pack_id: Optional[str] = None,
) -> Optional[EvidencePack]:
    """Build an evidence pack by scanning a directory for evidence artifacts."""
    ev_dir = Path(evidence_dir)
    if not ev_dir.is_dir():
        return None

    entries: List[EvidenceEntry] = []
    supported_exts = {".json", ".md", ".txt", ".xml", ".html", ".log", ".yaml", ".yml"}

    for root, _dirs, files in os.walk(str(ev_dir)):
        for fn in sorted(files):
            fp = os.path.join(root, fn)
            ext = Path(fn).suffix.lower()
            rel = os.path.relpath(fp, str(ev_dir))

            if ext in supported_exts or fn.startswith("test_") or "result" in fn.lower():
                # Determine evidence type from filename/path
                ev_type = "artifact"
                if "test" in fn.lower() or "result" in fn.lower():
                    ev_type = "test_result"
                elif "review" in fn.lower():
                    ev_type = "review_result"
                elif "patch" in fn.lower() or "diff" in fn.lower():
                    ev_type = "patch"
                elif "audit" in fn.lower():
                    ev_type = "audit"

                # Check if test passed (heuristic)
                passed = None
                if ev_type == "test_result":
                    try:
                        content = Path(fp).read_text(encoding="utf-8", errors="ignore")
                        passed = "passed" in content.lower() or "ok" in content.lower()
                        if "failed" in content.lower():
                            passed = False
                    except (OSError, IOError):
                        pass

                entry = EvidenceEntry(
                    ref_id=generate_id("ev"),
                    evidence_type=ev_type,
                    file_path=rel,
                    summary=f"{ev_type}: {fn}",
                    passed=passed,
                    timestamp=now_iso(),
                )
                entries.append(entry)

    passed_count = sum(1 for e in entries if e.passed is True)
    failed_count = sum(1 for e in entries if e.passed is False)

    return EvidencePack(
        pack_id=pack_id or generate_id("pack"),
        entries=entries,
        total_entries=len(entries),
        passed_count=passed_count,
        failed_count=failed_count,
        generated_at=now_iso(),
    )


def build_minimal(
    test_summary: str,
    test_passed: bool,
    review_status: Optional[str] = None,
) -> EvidencePack:
    """Build a minimal evidence pack from key results."""
    entries = [
        EvidenceEntry(
            ref_id=generate_id("ev"),
            evidence_type="test_result",
            summary=test_summary,
            passed=test_passed,
            timestamp=now_iso(),
        )
    ]

    if review_status:
        entries.append(EvidenceEntry(
            ref_id=generate_id("ev"),
            evidence_type="review_result",
            summary=review_status,
            passed=review_status.lower() == "approved",
            timestamp=now_iso(),
        ))

    return EvidencePack(
        pack_id=generate_id("pack"),
        entries=entries,
        total_entries=len(entries),
        passed_count=1 if test_passed else 0,
        failed_count=0 if test_passed else 1,
        generated_at=now_iso(),
    )


def evidence_pack_to_json(ep: EvidencePack, indent: int = 2) -> str:
    """Serialize evidence pack to JSON."""
    return to_json(ep, indent=indent)


def save_evidence_pack(ep: EvidencePack, output_dir: str) -> Optional[str]:
    """Save evidence pack to a JSON file."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"evidence_pack_{ep.pack_id}.json"
    path.write_text(evidence_pack_to_json(ep))
    return str(path)


def verify_pack_hash(ep: EvidencePack, expected_hash: str) -> bool:
    """Verify evidence pack content hash."""
    return ep.sha256 == expected_hash
