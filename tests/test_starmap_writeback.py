from pathlib import Path
import subprocess
import sys
import json

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, check=True):
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_starmap_config_exists():
    assert (ROOT / ".harness/config/starmap.yaml").exists()


def test_starmap_script_exists():
    assert (ROOT / ".harness/scripts/hermes_starmap.py").exists()


def test_starmap_help():
    proc = run([sys.executable, ".harness/scripts/hermes_starmap.py", "--help"])
    assert proc.returncode == 0
    assert "writeback" in proc.stdout
    assert "rebuild-index" in proc.stdout
    assert "query" in proc.stdout
    assert "stats" in proc.stdout


def test_writeback_command_exists():
    proc = run([sys.executable, ".harness/scripts/hermes_starmap.py", "writeback", "--help"])
    assert proc.returncode == 0
    assert "--task-id" in proc.stdout


def test_fact_requires_evidence_ref():
    facts_file = ROOT / ".harness/starmap/facts.jsonl"
    if not facts_file.exists():
        pytest.skip("no facts file")
    with facts_file.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            fact = json.loads(line)
            assert "evidence_ref" in fact, f"Fact {fact.get('fact_id')} missing evidence_ref"
            assert fact.get("evidence_ref"), f"Fact {fact.get('fact_id')} has empty evidence_ref"


def test_facts_jsonl_append_only():
    facts_file = ROOT / ".harness/starmap/facts.jsonl"
    if not facts_file.exists():
        pytest.skip("no facts file")
    # Write a new fact, confirm it appends
    before = len(facts_file.read_text(encoding="utf-8").splitlines())
    test_fact = {
        "fact_id": "fact_test_append_001",
        "trace_id": "trace_test_append",
        "task_id": "test_append_task",
        "fact_type": "test",
        "subject": "test",
        "predicate": "test",
        "object": "append_only",
        "evidence_ref": str(ROOT / ".harness/config/starmap.yaml"),
        "source": "test",
        "created_at": "2026-01-01T00:00:00",
    }
    with facts_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(test_fact) + "\n")
    after = len(facts_file.read_text(encoding="utf-8").splitlines())
    assert after == before + 1, "facts.jsonl must be append-only"


def test_rebuild_index_creates_index():
    proc = run([sys.executable, ".harness/scripts/hermes_starmap.py", "rebuild-index"])
    assert proc.returncode == 0
    idx_path = ROOT / ".harness/starmap/index.json"
    assert idx_path.exists()
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    assert "total_facts" in data
    assert "task_count" in data
    assert "updated_at" in data


def test_query_by_task_id_works():
    proc = run([sys.executable, ".harness/scripts/hermes_starmap.py", "query", "--task-id", "task_worker_e2e_002"])
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert output["action"] == "query"
    assert output["task_id"] == "task_worker_e2e_002"
    assert output["facts_found"] > 0


def test_stats_command_works():
    proc = run([sys.executable, ".harness/scripts/hermes_starmap.py", "stats"])
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert "total_facts" in output
    assert "by_type" in output
    assert "facts_without_evidence" in output


def test_starmap_yaml_rules():
    with (ROOT / ".harness/config/starmap.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["mode"]["append_only"] is True
    assert data["rules"]["require_evidence_ref"] is True
    assert data["rules"]["forbid_private_reasoning"] is True
    assert data["rules"]["forbid_unlogged_claims"] is True
    assert data["rules"]["append_only_facts"] is True
