from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_connector_script_exists():
    assert (ROOT / ".harness/scripts/hermes_connector.py").exists()


def test_examples_still_validate():
    examples = [
        ("task", ".harness/envelopes/examples/task_example.json"),
        ("result", ".harness/envelopes/examples/result_example.json"),
        ("review", ".harness/envelopes/examples/review_example.json"),
        ("repair", ".harness/envelopes/examples/repair_example.json"),
        ("final-acceptance", ".harness/envelopes/examples/final_acceptance_example.json"),
    ]
    for kind, path in examples:
        proc = run([sys.executable, ".harness/scripts/validate_envelope.py", kind, path])
        assert proc.returncode == 0, proc.stderr + proc.stdout


def test_invalid_task_rejected_by_validator(tmp_path):
    invalid = tmp_path / "bad_task.json"
    invalid.write_text(json.dumps({"protocol": "harness-a2a/v1.1"}), encoding="utf-8")
    proc = run([sys.executable, ".harness/scripts/validate_envelope.py", "task", str(invalid)])
    assert proc.returncode != 0


def test_connector_help():
    proc = run([sys.executable, ".harness/scripts/hermes_connector.py", "--help"])
    assert proc.returncode == 0
    assert "Hermes local A2A Connector" in proc.stdout
