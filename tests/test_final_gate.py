from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_final_review_schema_exists():
    assert (ROOT / ".harness/envelopes/schema/final_review_envelope.schema.json").exists()


def test_codex_review_config_exists():
    assert (ROOT / ".harness/config/codex_advanced_review.yaml").exists()


def test_final_merge_gate_config_exists():
    assert (ROOT / ".harness/config/final_merge_gate.yaml").exists()


def test_final_gate_script_exists():
    assert (ROOT / ".harness/scripts/hermes_final_gate.py").exists()


def test_final_gate_prompt_exists():
    assert (ROOT / ".harness/review/codex-advanced/prompts/CODEX_ADVANCED_REVIEW_PROMPT_TEMPLATE.md").exists()


def test_final_merge_gate_hard_blocks():
    with (ROOT / ".harness/config/final_merge_gate.yaml").open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["mode"]["dry_run_only"] is True
    assert data["mode"]["real_merge_enabled"] is False
    assert data["mode"]["push_enabled"] is False
    assert data["mode"]["deploy_enabled"] is False
    assert data["hard_blocks"]["no_test_no_merge"] is True
    assert data["hard_blocks"]["failed_test_no_merge"] is True
    assert data["hard_blocks"]["no_review_no_merge"] is True
    assert data["hard_blocks"]["no_codex_approval_no_merge"] is True
    assert data["hard_blocks"]["blocking_issue_no_merge"] is True
    assert data["hard_blocks"]["no_direct_main_write"] is True


def test_final_gate_script_help():
    proc = subprocess.run(
        [sys.executable, ".harness/scripts/hermes_final_gate.py", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0
    assert "Final Merge Gate" in proc.stdout or "Codex Advanced Review" in proc.stdout


def test_final_gate_cli_commands():
    for cmd in ["codex-advanced-review", "final-merge-gate-dry-run"]:
        proc = subprocess.run(
            [sys.executable, ".harness/scripts/hermes.py", cmd, "--help"],
            cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        assert proc.returncode == 0, f"{cmd} --help failed"
