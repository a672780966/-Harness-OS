"""Loop runner — execute a configured loop cycle."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import generate_loop_yaml, generate_policy_yaml
from .discovery import detect_system
from .safety import check_git_status, safety_report
from .topology import suggest_topology


def run_loop(project_root: str, loop_dir: str | None = None) -> dict[str, Any]:
    """Execute a configured loop cycle.
    This is the MVP runner — it runs Harness Copilot commands
    and generates evidence. Full agent orchestration is future work.
    """
    root = Path(project_root)
    loop_path = Path(loop_dir) if loop_dir else root / ".harness" / "loop"
    runs_dir = loop_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = runs_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {
        "timestamp": timestamp,
        "project_root": project_root,
        "steps": [],
    }

    # Step 1: Safety gate
    safety = safety_report(project_root)
    (run_dir / "safety_report.md").write_text(safety, encoding="utf-8")
    results["steps"].append({"step": "safety_gate", "output": "safety_report.md"})

    # Step 2: System detection
    sys_info = detect_system()
    sys_summary = []
    for a in sys_info.agents:
        icon = "✅" if a.installed else "❌"
        sys_summary.append(f"{icon} {a.name}")
    (run_dir / "system_detection.txt").write_text("\n".join(sys_summary), encoding="utf-8")
    results["steps"].append({"step": "system_detection", "output": "system_detection.txt"})

    # Step 3: Run copilot inspect
    try:
        r = subprocess.run(
            ["python3", "-m", "harness.copilot.cli", "inspect", project_root, "--json"],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
        (run_dir / "inspect_output.json").write_text(
            r.stdout if r.stdout else r.stderr, encoding="utf-8"
        )
    except Exception as e:
        (run_dir / "inspect_output.json").write_text(f"Error: {e}", encoding="utf-8")
    results["steps"].append({"step": "inspect", "output": "inspect_output.json"})

    # Step 4: Run copilot readiness
    try:
        r = subprocess.run(
            ["python3", "-m", "harness.copilot.cli", "readiness", project_root, "--format", "json"],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
        (run_dir / "readiness_output.json").write_text(
            r.stdout if r.stdout else r.stderr, encoding="utf-8"
        )
    except Exception as e:
        (run_dir / "readiness_output.json").write_text(f"Error: {e}", encoding="utf-8")
    results["steps"].append({"step": "readiness", "output": "readiness_output.json"})

    # Step 5: Generate summary
    summary = [
        f"# Harness Loop Run — {timestamp}",
        "",
        "## Steps Completed",
    ]
    for step in results["steps"]:
        summary.append(f"- {step['step']}: {step['output']}")
    summary.append("")
    summary.append("## System")
    summary.extend(sys_summary)
    summary.append("")
    worktree_clean = check_git_status(project_root)
    summary.append(f"Worktree: {'✅ clean' if worktree_clean else '❌ dirty'}")
    (run_dir / "run_summary.md").write_text("\n".join(summary), encoding="utf-8")

    results["run_dir"] = str(run_dir)
    results["worktree_clean"] = worktree_clean
    return results
