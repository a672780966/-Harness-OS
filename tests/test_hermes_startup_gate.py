from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_startup_gate_script_exists():
    assert (ROOT / ".harness/scripts/hermes_startup_gate.py").exists()


def test_startup_check_command():
    proc = run([sys.executable, ".harness/scripts/hermes.py", "startup-check"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    assert "all_configs_loaded" in data
    assert "startup_gate_enabled" in data
    assert data["startup_gate_enabled"] is True


def test_startup_gate_blocks_illegal_transitions():
    """Verify the state machine no longer allows pending→assigned or assigned→running."""
    import yaml
    cfg_path = ROOT / ".harness/config/state_machine.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    transitions = cfg.get("transitions", {})
    assert "assigned" not in transitions.get("pending", []), \
        "pending→assigned is illegal and must be removed"
    assert "running" not in transitions.get("assigned", []), \
        "assigned→running is illegal and must be removed"
    assert "startup_verify" in transitions.get("pending", []), \
        "pending→startup_verify must exist"
    assert "startup_gate" in transitions.get("assigned", []), \
        "assigned→startup_gate must exist"
    assert "running" in transitions.get("startup_gate", []), \
        "startup_gate→running must exist"


def test_startup_report_generated():
    proc = run([sys.executable, ".harness/scripts/hermes_startup_gate.py", "generate-report"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    data = json.loads(proc.stdout)
    assert "report_id" in data
    assert data["status"] == "passed"
    assert "report_path" in data
    report_path = Path(data["report_path"])
    assert report_path.exists()
