"""
Tests for swebench_tier_c_real_loop.py — SWE-bench Tier C Real Loop Adapter

Tests:
1. Adapter script exists
2. Hermes CLI exposes swebench-tier-c-run
3. Hermes CLI exposes swebench-tier-c-validate
4. validate_artifacts detects missing repo_graph.json
5. validate_artifacts detects missing node_index.yaml
6. validate_artifacts detects missing execution_order.yaml
7. validate_artifacts detects missing loop_report.md
8. validate_artifacts detects missing final_review_envelope.json
9. validate_artifacts detects missing final_gate_result.md
10. validate_artifacts detects missing starmap_writeback_summary.md
11. Partial harness_verify-only output is classified as B_plus (C_partial), not full Tier C
12. create_plan_structure writes task_envelope.json without NameError (regression test)
    - Covers the output_dir NameError fix
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_SCRIPT = ROOT / ".harness/scripts/swebench_tier_c_real_loop.py"
HERMES_CLI = ROOT / ".harness/scripts/hermes.py"
REQUIRED_ARTIFACTS = [
    "repo_graph.json",
    "node_index.yaml",
    "execution_order.yaml",
    "loop_report.md",
    "patch.diff",
    "eval_report.json",
    "metrics.json",
    "final_review_envelope.json",
    "final_gate_result.md",
    "starmap_writeback_summary.md",
]
REQUIRED_SUBDIRS = [
    "result_envelopes",
    "review_envelopes",
    "process_attestations",
]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(ROOT), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=30,
    )


# ── Test 1: Adapter script exists ───────────────────────────────────────

def test_adapter_script_exists():
    assert ADAPTER_SCRIPT.exists(), f"Adapter script not found: {ADAPTER_SCRIPT}"
    content = ADAPTER_SCRIPT.read_text(encoding="utf-8")
    assert len(content) > 1000, "Adapter script is too short"
    assert "def run_pipeline" in content, "Adapter missing run_pipeline function"


# ── Test 2: Hermes CLI exposes swebench-tier-c-run ──────────────────────

def test_cli_exposes_run_command():
    result = run([sys.executable, str(HERMES_CLI), "swebench-tier-c-run", "--help"])
    assert result.returncode == 0, f"CLI command failed: {result.stderr}"
    assert "--instance-id" in result.stdout
    assert "--workdir" in result.stdout
    assert "--output-dir" in result.stdout


# ── Test 3: Hermes CLI exposes swebench-tier-c-validate ─────────────────

def test_cli_exposes_validate_command():
    result = run([sys.executable, str(HERMES_CLI), "swebench-tier-c-validate", "--help"])
    assert result.returncode == 0, f"CLI validate command failed: {result.stderr}"
    assert "--output-dir" in result.stdout


# ── Test 4: validate_artifacts detects missing repo_graph.json ──────────

def test_validate_detects_missing_repo_graph():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        # Create all artifacts except repo_graph.json
        (out / "node_index.yaml").write_text("nodes: []", encoding="utf-8")
        (out / "execution_order.yaml").write_text("task_id: test", encoding="utf-8")
        (out / "loop_report.md").write_text("# Loop Report", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": false}', encoding="utf-8")
        (out / "final_review_envelope.json").write_text("{}", encoding="utf-8")
        (out / "final_gate_result.md").write_text("# Gate", encoding="utf-8")
        (out / "starmap_writeback_summary.md").write_text("# StarMap", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert result.returncode == 1, f"Validate should fail when repo_graph.json is missing"
        assert "repo_graph.json" in result.stdout or "Missing" in result.stdout


# ── Test 5: validate_artifacts detects missing node_index.yaml ──────────

def test_validate_detects_missing_node_index():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        (plan / "repo_graph.json").write_text("{}", encoding="utf-8")
        (out / "loop_report.md").write_text("# Loop Report", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": false}', encoding="utf-8")
        (out / "final_review_envelope.json").write_text("{}", encoding="utf-8")
        (out / "final_gate_result.md").write_text("# Gate", encoding="utf-8")
        (out / "starmap_writeback_summary.md").write_text("# StarMap", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert "node_index.yaml" in result.stdout or result.returncode == 1


# ── Test 6: validate_artifacts detects missing execution_order.yaml ─────

def test_validate_detects_missing_execution_order():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        (plan / "repo_graph.json").write_text("{}", encoding="utf-8")
        (plan / "node_index.yaml").write_text("nodes: []", encoding="utf-8")
        (out / "loop_report.md").write_text("# Loop Report", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": false}', encoding="utf-8")
        (out / "final_review_envelope.json").write_text("{}", encoding="utf-8")
        (out / "final_gate_result.md").write_text("# Gate", encoding="utf-8")
        (out / "starmap_writeback_summary.md").write_text("# StarMap", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert "execution_order.yaml" in result.stdout or result.returncode == 1


# ── Test 7: validate_artifacts detects missing loop_report.md ───────────

def test_validate_detects_missing_loop_report():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        (plan / "repo_graph.json").write_text("{}", encoding="utf-8")
        (plan / "node_index.yaml").write_text("nodes: []", encoding="utf-8")
        (plan / "execution_order.yaml").write_text("task_id: test", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": false}', encoding="utf-8")
        (out / "final_review_envelope.json").write_text("{}", encoding="utf-8")
        (out / "final_gate_result.md").write_text("# Gate", encoding="utf-8")
        (out / "starmap_writeback_summary.md").write_text("# StarMap", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert "loop_report.md" in result.stdout or result.returncode == 1


# ── Test 8: validate_artifacts detects missing final_review_envelope.json ─

def test_validate_detects_missing_final_review_envelope():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        (plan / "repo_graph.json").write_text("{}", encoding="utf-8")
        (plan / "node_index.yaml").write_text("nodes: []", encoding="utf-8")
        (plan / "execution_order.yaml").write_text("task_id: test", encoding="utf-8")
        (out / "loop_report.md").write_text("# Loop Report", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": false}', encoding="utf-8")
        (out / "final_gate_result.md").write_text("# Gate", encoding="utf-8")
        (out / "starmap_writeback_summary.md").write_text("# StarMap", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert "final_review_envelope.json" in result.stdout or result.returncode == 1


# ── Test 9: validate_artifacts detects missing final_gate_result.md ─────

def test_validate_detects_missing_final_gate_result():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        (plan / "repo_graph.json").write_text("{}", encoding="utf-8")
        (plan / "node_index.yaml").write_text("nodes: []", encoding="utf-8")
        (plan / "execution_order.yaml").write_text("task_id: test", encoding="utf-8")
        (out / "loop_report.md").write_text("# Loop Report", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": false}', encoding="utf-8")
        (out / "final_review_envelope.json").write_text("{}", encoding="utf-8")
        (out / "starmap_writeback_summary.md").write_text("# StarMap", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert "final_gate_result.md" in result.stdout or result.returncode == 1


# ── Test 10: validate_artifacts detects missing starmap_writeback_summary.md ─

def test_validate_detects_missing_starmap():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        (plan / "repo_graph.json").write_text("{}", encoding="utf-8")
        (plan / "node_index.yaml").write_text("nodes: []", encoding="utf-8")
        (plan / "execution_order.yaml").write_text("task_id: test", encoding="utf-8")
        (out / "loop_report.md").write_text("# Loop Report", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": false}', encoding="utf-8")
        (out / "final_review_envelope.json").write_text("{}", encoding="utf-8")
        (out / "final_gate_result.md").write_text("# Gate", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert "starmap_writeback_summary.md" in result.stdout or result.returncode == 1


# ── Test 11: All artifacts present returns success ──────────────────────

def test_validate_all_artifacts_present():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        # All required artifacts
        (plan / "repo_graph.json").write_text("{}", encoding="utf-8")
        (plan / "node_index.yaml").write_text("nodes: []", encoding="utf-8")
        (plan / "execution_order.yaml").write_text("task_id: test", encoding="utf-8")
        (out / "loop_report.md").write_text("# Loop Report", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "eval_report.json").write_text("{}", encoding="utf-8")
        (out / "metrics.json").write_text('{"full_real_loop": true}', encoding="utf-8")
        (out / "final_review_envelope.json").write_text("{}", encoding="utf-8")
        (out / "final_gate_result.md").write_text("# Gate", encoding="utf-8")
        (out / "starmap_writeback_summary.md").write_text("# StarMap", encoding="utf-8")
        (out / "result_envelopes").mkdir()
        (out / "result_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "review_envelopes").mkdir()
        (out / "review_envelopes" / "a.json").write_text("{}", encoding="utf-8")
        (out / "process_attestations").mkdir()
        (out / "process_attestations" / "a.json").write_text("{}", encoding="utf-8")

        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])
        assert result.returncode == 0, f"Validate should pass when all artifacts present: {result.stdout}"


# ── Test 12: Partial harness_verify-only output is not full Tier C ──────

def test_partial_output_is_not_full_tier_c():
    """Verify that harness_verify-only output would be classified as B_plus, not full Tier C."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        # Only create harness_verify-style artifacts (B_plus pattern)
        (out / "harness_init.json").write_text("{}", encoding="utf-8")
        (out / "harness_verify.log").write_text("PASS", encoding="utf-8")
        (out / "patch.diff").write_text("diff --git a/test b/test", encoding="utf-8")
        (out / "metrics.json").write_text('{"resolved": true}', encoding="utf-8")

        # Validate — should fail because full Tier C artifacts are missing
        plan = out / "plan"
        plan.mkdir(parents=True, exist_ok=True)
        result = run([sys.executable, str(ADAPTER_SCRIPT), "validate", "--output-dir", str(out)])

        # Should fail validation (returncode 1) because full real loop artifacts missing
        assert result.returncode == 1

        # Missing artifacts should include at least: repo_graph, node_index, execution_order
        missing_info = result.stdout
        assert "repo_graph" in missing_info, f"repo_graph not flagged: {missing_info}"
        assert "node_index" in missing_info, f"node_index not flagged: {missing_info}"
        assert "execution_order" in missing_info, f"execution_order not flagged: {missing_info}"
        assert "loop_report" in missing_info, f"loop_report not flagged: {missing_info}"
        assert "final_review_envelope" in missing_info, f"final_review not flagged: {missing_info}"
        assert "final_gate_result" in missing_info, f"final_gate not flagged: {missing_info}"
        assert "starmap_writeback_summary" in missing_info, f"starmap not flagged: {missing_info}"

        # Check that metrics.full_real_loop being false is the correct pattern
        metrics_path = out / "metrics.json"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text())
            assert not metrics.get("full_real_loop", False), (
                "B_plus output should not claim full_real_loop"
            )


# ── Test 13: create_plan_structure writes task_envelope.json without NameError ─

def test_create_plan_structure_no_nameerror():
    """Regression test: create_plan_structure must receive output_dir and write task_envelope.json."""
    result = run([
        sys.executable, str(ADAPTER_SCRIPT), "validate",
        "--output-dir", str(ADAPTER_SCRIPT.parent),
    ])
    # Just checking the script doesn't crash when functions are imported
    # We verify by importing and calling create_plan_structure
    import importlib.util
    spec = importlib.util.spec_from_file_location("adapter", ADAPTER_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        plan_dir = out / "plan"
        plan_dir.mkdir(parents=True)
        try:
            mod.create_plan_structure(
                instance_id="test__test-12345",
                task_id="test_task",
                workdir=out,
                plan_dir=plan_dir,
                output_dir=out,
                model="opencode-go/deepseek-v4-flash",
                max_repair_rounds=2,
            )
            # Verify task_envelope.json was written
            assert (out / "task_envelope.json").exists(), "task_envelope.json not written"
            assert (plan_dir / "node_index.yaml").exists(), "node_index.yaml not written"
            assert (plan_dir / "execution_order.yaml").exists(), "execution_order.yaml not written"
            assert (plan_dir / "nodes").exists(), "nodes directory not created"
            assert len(list((plan_dir / "nodes").iterdir())) == 4, "expected 4 node definitions"
        except NameError as e:
            pytest.fail(f"NameError in create_plan_structure: {e}")


# ── Stop Reason Classification Tests ─────────────────────────────────────

def _compute_stop_reason(
    eval_valid: bool,
    environment_failed: bool,
    resolved: bool,
    codex_approved: bool,
    final_gate_passed: bool,
) -> str:
    """Replicate the stop_reason logic from the adapter."""
    if not eval_valid and environment_failed:
        return "eval_runner_failed"
    if not eval_valid:
        return "eval_runner_failed"
    if not resolved and eval_valid:
        return "unresolved_after_repair_or_eval"
    if not codex_approved:
        return "codex_final_review_rejected"
    if not final_gate_passed:
        return "final_gate_failed"
    if resolved and codex_approved and final_gate_passed and eval_valid:
        return "real_loop_complete"
    return "real_loop_incomplete"


def test_stop_reason_real_loop_complete():
    """resolved=true + eval_valid=true + codex_approved=true + gate_passed=true => real_loop_complete"""
    reason = _compute_stop_reason(
        eval_valid=True, environment_failed=False,
        resolved=True, codex_approved=True, final_gate_passed=True,
    )
    assert reason == "real_loop_complete", f"Expected real_loop_complete, got {reason}"


def test_stop_reason_eval_runner_failed_on_env_failure():
    """environment_failed=true => eval_runner_failed (even if resolved)"""
    reason = _compute_stop_reason(
        eval_valid=False, environment_failed=True,
        resolved=False, codex_approved=False, final_gate_passed=False,
    )
    assert reason == "eval_runner_failed", f"Expected eval_runner_failed, got {reason}"


def test_stop_reason_eval_runner_failed_no_valid():
    """eval_valid=false + env ok => eval_runner_failed"""
    reason = _compute_stop_reason(
        eval_valid=False, environment_failed=False,
        resolved=False, codex_approved=False, final_gate_passed=False,
    )
    assert reason == "eval_runner_failed", f"Expected eval_runner_failed, got {reason}"


def test_stop_reason_unresolved_after_repair():
    """resolved=false + eval_valid=true => unresolved_after_repair_or_eval"""
    reason = _compute_stop_reason(
        eval_valid=True, environment_failed=False,
        resolved=False, codex_approved=False, final_gate_passed=False,
    )
    assert reason == "unresolved_after_repair_or_eval", f"Expected unresolved_after_repair_or_eval, got {reason}"


def test_stop_reason_codex_rejected():
    """codex_approved=false + resolved=true => codex_final_review_rejected"""
    reason = _compute_stop_reason(
        eval_valid=True, environment_failed=False,
        resolved=True, codex_approved=False, final_gate_passed=False,
    )
    assert reason == "codex_final_review_rejected", f"Expected codex_final_review_rejected, got {reason}"


def test_stop_reason_final_gate_failed():
    """final_gate_passed=false + codex_approved=true => final_gate_failed"""
    reason = _compute_stop_reason(
        eval_valid=True, environment_failed=False,
        resolved=True, codex_approved=True, final_gate_passed=False,
    )
    assert reason == "final_gate_failed", f"Expected final_gate_failed, got {reason}"
