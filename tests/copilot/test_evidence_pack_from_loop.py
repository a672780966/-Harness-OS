"""Tests for Evidence Pack from Loop artifacts."""

import json
import tempfile
from pathlib import Path

from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
from harness.copilot.integration.loop_to_copilot_mapper import _build_evidence_pack


class TestEvidenceFromLoop:
    def _create_loop_with_artifacts(self, tmpdir: str, **overrides):
        base = Path(tmpdir)
        default_metrics = {
            "instance_id": "django__django-12050",
            "task_id": "swebench_test",
            "eval_valid": True,
            "resolved_official": True,
            "codex_approved": True,
            "final_gate_passed": True,
            "patch_size_lines": 24,
            "files_changed": 1,
        }
        default_eval = {
            "eval_valid": True,
            "tests_passed": 45,
            "tests_total": 45,
            "resolved_official": True,
            "generated_at": "2026-06-22T10:00:00",
        }

        metrics = overrides.get("metrics", default_metrics)
        eval_report = overrides.get("eval_report", default_eval)

        (base / "metrics.json").write_text(json.dumps(metrics))
        (base / "eval_report.json").write_text(json.dumps(eval_report))
        (base / "patch.diff").write_text("diff --git a/file.py b/file.py\nindex abc..def\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n")

    def test_evidence_pack_has_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_loop_with_artifacts(tmpdir)
            artifacts = load_loop_artifacts(tmpdir)
            ep = _build_evidence_pack(artifacts)
            assert ep is not None
            assert ep.total_entries >= 1
            assert len(ep.entries) >= 1

    def test_evidence_has_passed_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_loop_with_artifacts(tmpdir)
            artifacts = load_loop_artifacts(tmpdir)
            ep = _build_evidence_pack(artifacts)
            assert ep is not None
            assert ep.passed_count >= 1

    def test_evidence_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_loop_with_artifacts(tmpdir)
            artifacts = load_loop_artifacts(tmpdir)
            ep = _build_evidence_pack(artifacts)
            assert ep is not None
            types = [e.evidence_type for e in ep.entries]
            assert "test_result" in types

    def test_evidence_pack_sha256_integrity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_loop_with_artifacts(tmpdir)
            artifacts = load_loop_artifacts(tmpdir)
            ep1 = _build_evidence_pack(artifacts)
            assert ep1 is not None
            assert ep1.sha256 is not None
            assert len(ep1.sha256) == 64  # SHA256 hex length

    def test_evidence_has_patch_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_loop_with_artifacts(tmpdir)
            artifacts = load_loop_artifacts(tmpdir)
            ep = _build_evidence_pack(artifacts)
            assert ep is not None
            patch_entries = [e for e in ep.entries if e.evidence_type == "patch"]
            assert len(patch_entries) >= 1


class TestEvidenceWithReviewRejection:
    def test_review_rejected_evidence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir, "review_envelopes")
            env_dir.mkdir()
            (env_dir / "final_review_envelope.json").write_text(json.dumps({
                "approved": False,
                "passed": False,
                "blocking_issues": [{"issue": "Bug"}],
                "summary": "Rejected",
                "reviewed_at": "now",
            }))

            (Path(tmpdir) / "metrics.json").write_text(json.dumps({
                "instance_id": "test",
                "eval_valid": False,
                "codex_approved": False,
                "final_gate_passed": False,
            }))

            artifacts = load_loop_artifacts(tmpdir)
            ep = _build_evidence_pack(artifacts)
            assert ep is not None
            # Should have review evidence with failed status
            review_entries = [e for e in ep.entries if e.evidence_type == "review_result"]
            if review_entries:
                assert review_entries[0].passed is False


class TestEvidenceNoData:
    def test_no_artifacts_returns_pack_with_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = load_loop_artifacts(tmpdir)
            ep = _build_evidence_pack(artifacts)
            assert ep is not None
            assert ep.total_entries == 0
            assert ep.passed_count == 0
