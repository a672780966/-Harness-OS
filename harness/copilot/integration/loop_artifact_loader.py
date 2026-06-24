"""Loop Artifact Loader — reads Hermes Loop artifacts from a run directory."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LoopArtifacts:
    """All loaded artifacts from a loop run directory."""
    run_dir: str
    instance_id: str = ""
    tier: str = ""

    # Core artifacts
    eval_report: Optional[Dict[str, Any]] = None
    test_result: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    run_classification: Optional[Dict[str, Any]] = None
    final_gate_result: Optional[Dict[str, Any]] = None
    loop_report: Optional[str] = None
    starmap_writeback: Optional[str] = None

    # Envelopes
    task_envelope: Optional[Dict[str, Any]] = None
    final_review_envelope: Optional[Dict[str, Any]] = None
    result_envelope: Optional[Dict[str, Any]] = None
    final_gate_envelope: Optional[Dict[str, Any]] = None

    # Attestations
    process_attestations: List[Dict[str, Any]] = field(default_factory=list)

    # Diffs
    patch_diff: Optional[str] = None
    patch_final_diff: Optional[str] = None

    # Repair rounds
    repair_rounds: List[Dict[str, Any]] = field(default_factory=list)

    # Review repair
    review_repair_rounds: List[Dict[str, Any]] = field(default_factory=list)

    # Agent output
    agent_stdout: Optional[str] = None
    eval_stdout: Optional[str] = None
    eval_stderr: Optional[str] = None

    # Errors
    load_errors: List[str] = field(default_factory=list)


def load_loop_artifacts(run_dir: str) -> LoopArtifacts:
    """Load all artifacts from a loop run directory."""
    artifacts = LoopArtifacts(run_dir=run_dir)
    base = Path(run_dir)

    if not base.is_dir():
        artifacts.load_errors.append(f"Not a directory: {run_dir}")
        return artifacts

    # Extract instance_id and tier from path
    parts = base.parts
    for i, p in enumerate(parts):
        if p.startswith("runs/") or p == "runs":
            continue
        if "__" in p and i > 0:
            artifacts.instance_id = p
        if p.startswith("tier_"):
            artifacts.tier = p.replace("tier_", "").replace("_full", "").replace("_governed", "")

    # Load JSON files
    _load_json(artifacts, base, "eval_report.json")
    _load_json(artifacts, base, "test_result.json")
    _load_json(artifacts, base, "metrics.json")
    _load_json(artifacts, base, "run_classification.json")
    _load_json(artifacts, base, "task_envelope.json")
    _load_json(artifacts, base, "eval_command.json")

    # Load markdown/text
    artifacts.final_gate_result = _load_markdown_as_dict(base / "final_gate_result.md")
    artifacts.loop_report = _load_text(base / "loop_report.md")
    artifacts.starmap_writeback = _load_text(base / "starmap_writeback_summary.md")

    # Load review envelopes
    review_env_dir = base / "review_envelopes"
    if review_env_dir.is_dir():
        for f in sorted(review_env_dir.iterdir()):
            if f.suffix == ".json":
                data = _safe_load_json(f)
                if data:
                    if "final" in f.stem.lower():
                        artifacts.final_review_envelope = data
                    else:
                        # Store as generic envelope
                        pass

    # Load result envelopes
    result_env_dir = base / "result_envelopes"
    if result_env_dir.is_dir():
        for f in sorted(result_env_dir.iterdir()):
            if f.suffix == ".json":
                data = _safe_load_json(f)
                if data:
                    if "final" in f.stem.lower():
                        artifacts.final_gate_envelope = data
                    elif "result" in f.stem.lower():
                        artifacts.result_envelope = data

    # Load process attestations
    attest_dir = base / "process_attestations"
    if attest_dir.is_dir():
        for f in sorted(attest_dir.iterdir()):
            if f.suffix == ".json":
                data = _safe_load_json(f)
                if data:
                    artifacts.process_attestations.append(data)

    # Load patches
    artifacts.patch_diff = _load_text(base / "patch.diff")
    artifacts.patch_final_diff = _load_text(base / "patch_final.diff")

    # Load repair rounds
    repair_dir = base / "repair_rounds"
    if repair_dir.is_dir():
        _load_repair_rounds(artifacts, repair_dir)

    # Load review repair rounds
    review_repair_dir = base / "review_repair"
    if review_repair_dir.is_dir():
        _load_repair_rounds(artifacts, review_repair_dir, is_review_repair=True)

    # Load agent/eval output
    artifacts.agent_stdout = _load_text(base / "agent_stdout.log", max_lines=100)
    artifacts.eval_stdout = _load_text(base / "eval_stdout.txt", max_lines=100)
    artifacts.eval_stderr = _load_text(base / "eval_stderr.txt", max_lines=50)

    # Try to extract instance_id from metrics if not in path
    if not artifacts.instance_id and artifacts.metrics:
        artifacts.instance_id = artifacts.metrics.get("instance_id", "")

    return artifacts


def _load_json(artifacts: LoopArtifacts, base: Path, filename: str) -> None:
    """Load a JSON file into the appropriate artifacts field."""
    fp = base / filename
    data = _safe_load_json(fp)
    if data is None:
        return
    key = filename.replace(".json", "")
    if hasattr(artifacts, key):
        setattr(artifacts, key, data)


def _safe_load_json(fp: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None on failure."""
    if not fp.is_file():
        return None
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, IOError) as e:
        return None


def _load_text(fp: Path, max_lines: int = 0) -> Optional[str]:
    """Load a text file, optionally limiting lines."""
    if not fp.is_file():
        return None
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
        if max_lines > 0:
            lines = text.strip().split("\n")
            text = "\n".join(lines[:max_lines])
            if len(lines) > max_lines:
                text += f"\n... (truncated, {len(lines)} lines total)"
        return text
    except (OSError, IOError):
        return None


def _load_markdown_as_dict(fp: Path) -> Optional[Dict[str, Any]]:
    """Parse a structured markdown table (like final_gate_result.md) into a dict."""
    text = _load_text(fp)
    if not text:
        return None

    result: Dict[str, Any] = {"raw_text": text}
    for line in text.split("\n"):
        # Parse table rows like: | eval_valid | ✅ | true |
        if line.strip().startswith("|") and "✅" in line or "❌" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                key = parts[0].strip().lower().replace(" ", "_")
                value = parts[-1].strip()
                # Convert known values
                if value == "true":
                    value = True
                elif value == "false":
                    value = False
                result[key] = value

        # Parse key-value lines like: **merge_ready**: true
        if "**: " in line:
            k, v = line.split("**: ", 1)
            key = k.strip().strip("*").strip().lower().replace(" ", "_")
            value = v.strip()
            if value == "true":
                value = True
            elif value == "false":
                value = False
            result[key] = value

    return result


def _load_repair_rounds(
    artifacts: LoopArtifacts,
    rounds_dir: Path,
    is_review_repair: bool = False,
) -> None:
    """Load repair round artifacts."""
    for round_dir in sorted(rounds_dir.iterdir()):
        if not round_dir.is_dir():
            continue
        round_data: Dict[str, Any] = {
            "round_name": round_dir.name,
            "patch": _load_text(round_dir / "patch_repair.diff"),
            "stdout": _load_text(round_dir / "repair_stdout.log", max_lines=100),
            "stderr": _load_text(round_dir / "repair_stderr.log", max_lines=50),
            "prompt": _load_text(round_dir / "repair_prompt.md"),
            "eval_report": _safe_load_json(round_dir / "eval_report.json"),
            "test_result": _safe_load_json(round_dir / "test_result.json"),
            "result_envelope": _safe_load_json(round_dir / "result_envelope.json"),
        }
        if is_review_repair:
            artifacts.review_repair_rounds.append(round_data)
        else:
            artifacts.repair_rounds.append(round_data)
