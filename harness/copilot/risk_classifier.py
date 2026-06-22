"""Risk Classifier — classify file/module change risk based on heuristics."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .schemas import (
    RiskLevel,
    RiskAlert,
    ProjectSemanticMap,
    ModuleDiffSummary,
    DiffEntry,
    now_iso,
    generate_id,
)


# High-risk path keywords and their weights
RISK_PATTERNS: Dict[str, float] = {
    # Security
    "auth": 0.7, "login": 0.6, "password": 0.9, "credential": 0.9,
    "secret": 0.9, "token": 0.8, "oauth": 0.7, "saml": 0.7,
    "permission": 0.5, "rbac": 0.5, "cors": 0.4, "csrf": 0.6,
    "encrypt": 0.7, "decrypt": 0.7, "hash": 0.5,
    # Data
    "database": 0.6, "migration": 0.5, "schema": 0.5, "sql": 0.5,
    "payment": 0.8, "billing": 0.8, "pricing": 0.4,
    "personal": 0.7, "privacy": 0.7, "gdpr": 0.8, "pii": 0.9,
    # Infrastructure
    "deploy": 0.7, "prod": 0.6, "docker": 0.4, "kubernetes": 0.5,
    "config": 0.3, ".env": 0.8, "firewall": 0.6, "proxy": 0.4,
    # Destructive
    "delete": 0.5, "drop": 0.6, "truncate": 0.6, "remove": 0.3,
    "archive": 0.3, "backup": 0.3,
    # Network
    "network": 0.3, "api_key": 0.9, "webhook": 0.4,
    "certificate": 0.6, "ssl": 0.6, "tls": 0.6,
}


def classify_file_risk(file_path: str) -> Tuple[float, List[str]]:
    """Classify risk for a single file path (0.0–1.0)."""
    reasons: List[str] = []
    score = 0.0
    lower = file_path.lower()
    parts = Path(lower).parts

    for keyword, weight in RISK_PATTERNS.items():
        if keyword in lower:
            if weight > score:
                score = weight
            if keyword not in [r for r in reasons]:
                reasons.append(f"Contains security/infra keyword: '{keyword}'")

    # Extension-based risk
    ext = Path(file_path).suffix.lower()
    risky_exts = {".env": 0.5, ".pem": 0.6, ".key": 0.7, ".cer": 0.5}
    if ext in risky_exts:
        score = max(score, risky_exts[ext])
        reasons.append(f"Risky file extension: {ext}")

    # Path depth-based (config/deep nesting = more risk)
    depth = len(parts)
    if depth > 6:
        score = max(score, 0.2)
        reasons.append("Deeply nested path (maintenance risk)")

    return min(score, 1.0), reasons


def classify_diff_risk(
    entry: DiffEntry,
) -> Tuple[float, List[str]]:
    """Classify risk for a diff entry."""
    score, reasons = classify_file_risk(entry.file_path)

    # Large changes = higher risk
    total_changes = entry.lines_added + entry.lines_removed
    if total_changes > 500:
        score = max(score, 0.7)
        reasons.append(f"Large change ({total_changes} lines)")
    elif total_changes > 200:
        score = max(score, 0.5)
        reasons.append(f"Substantial change ({total_changes} lines)")
    elif total_changes > 50:
        score = max(score, 0.2)

    # Deleting files
    if entry.change_type == "deleted":
        score = max(score, 0.4)
        reasons.append("File deletion")

    # Many hunks = complex change
    if entry.hunks > 5:
        score = max(score, 0.3)
        reasons.append(f"Complex change ({entry.hunks} hunks)")

    return min(score, 1.0), reasons


def generate_risk_alerts(
    diff_summaries: List[ModuleDiffSummary],
    sem_map: Optional[ProjectSemanticMap] = None,
) -> List[RiskAlert]:
    """Generate risk alerts from module diff summaries."""
    alerts: List[RiskAlert] = []

    for summary in diff_summaries:
        if summary.risk_impact == RiskLevel.HIGH:
            alerts.append(RiskAlert(
                alert_id=generate_id("risk"),
                title=f"High-risk changes in '{summary.module_name}'",
                level=RiskLevel.HIGH,
                module=summary.module_name,
                description=(
                    f"Module '{summary.module_name}' has {summary.total_added}+/"
                    f"{summary.total_removed}- changes classified as high risk."
                ),
                recommendation="Request additional review for this module.",
                is_blocking=True,
                created_at=now_iso(),
            ))

        # Per-file alerts
        for entry in summary.entries:
            risk_score, reasons = classify_diff_risk(entry)
            if risk_score >= 0.7:
                alerts.append(RiskAlert(
                    alert_id=generate_id("risk"),
                    title=f"Critical: {Path(entry.file_path).name}",
                    level=RiskLevel.CRITICAL,
                    module=summary.module_name,
                    file_path=entry.file_path,
                    description=f"File '{entry.file_path}' has critical risk score ({risk_score:.1f}).",
                    recommendation="Requires human review before merge.",
                    is_blocking=True,
                    created_at=now_iso(),
                ))
            elif risk_score >= 0.5:
                alerts.append(RiskAlert(
                    alert_id=generate_id("risk"),
                    title=f"High risk: {Path(entry.file_path).name}",
                    level=RiskLevel.HIGH,
                    module=summary.module_name,
                    file_path=entry.file_path,
                    description=(
                        f"File '{entry.file_path}' flagged: {', '.join(reasons)}"
                    ),
                    recommendation="Review carefully before merge.",
                    is_blocking=False,
                    created_at=now_iso(),
                ))

    return alerts


def get_risk_level(score: float) -> RiskLevel:
    """Convert numeric score to RiskLevel."""
    if score >= 0.8:
        return RiskLevel.CRITICAL
    elif score >= 0.5:
        return RiskLevel.HIGH
    elif score >= 0.2:
        return RiskLevel.MEDIUM
    elif score > 0:
        return RiskLevel.LOW
    return RiskLevel.UNKNOWN
