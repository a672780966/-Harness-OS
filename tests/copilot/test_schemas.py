"""Tests for Copilot Kernel Layer — Core Schemas."""

import json
from dataclasses import asdict
from harness.copilot.schemas import (
    CardType, TaskState, Priority, Source, RiskLevel, AgentPhase,
    MergeReadinessState, VerificationMethod,
    FileEntry, ModuleCard, ProjectSemanticMap, DependencyEdge,
    AgentExecutionState, DiffEntry, RecentChangeExplanation,
    ChangeSuggestion, TaskCard, VerificationEntry, RiskAlert,
    MergeReadiness, EvidenceEntry, EvidencePack,
    to_json, from_json, now_iso, generate_id,
)


class TestEnums:
    def test_card_type_values(self):
        assert CardType.FIX_TEST.value == "fix_test"
        assert CardType.FIX_REVIEW.value == "fix_review"
        assert CardType.CODE_CHANGE.value == "code_change"
        assert CardType.RISK_ALERT.value == "risk_alert"
        assert CardType.MERGE_CHECK.value == "merge_check"
        assert CardType.EVIDENCE.value == "evidence"
        assert CardType.COMPANION.value == "companion"

    def test_task_state_values(self):
        assert TaskState.PENDING.value == "pending"
        assert TaskState.IN_PROGRESS.value == "in_progress"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.BLOCKED.value == "blocked"

    def test_priority_values(self):
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"

    def test_risk_level_values(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.UNKNOWN.value == "unknown"

    def test_agent_phase_values(self):
        assert AgentPhase.IDLE.value == "idle"
        assert AgentPhase.PLANNING.value == "planning"
        assert AgentPhase.DONE.value == "done"

    def test_merge_readiness_values(self):
        assert MergeReadinessState.PASS.value == "pass"
        assert MergeReadinessState.BLOCK.value == "block"
        assert MergeReadinessState.REVIEW_NEEDED.value == "review_needed"

    def test_verification_method_values(self):
        assert VerificationMethod.DOCKER_EVAL.value == "docker_eval"
        assert VerificationMethod.CODEX_REVIEW.value == "codex_review"
        assert VerificationMethod.MANUAL.value == "manual"


class TestDataClasses:
    def test_file_entry_creation(self):
        fe = FileEntry(
            path="src/main.py",
            language="Python",
            size_bytes=1024,
            last_modified="2026-06-22T07:00:00",
        )
        assert fe.path == "src/main.py"
        assert fe.language == "Python"
        assert fe.size_bytes == 1024
        assert fe.risk_score == 0.0
        assert fe.risk_reasons == []

    def test_file_entry_with_risk(self):
        fe = FileEntry(
            path="config/.env.prod",
            language="Environment",
            size_bytes=200,
            last_modified="2026-06-22",
            risk_score=0.8,
            risk_reasons=["Contains 'secret' in path"],
        )
        assert fe.risk_score == 0.8
        assert len(fe.risk_reasons) == 1

    def test_module_card(self):
        mc = ModuleCard(
            name="auth",
            path="/project/auth",
            files=[FileEntry(path="auth/login.py", language="Python", size_bytes=500, last_modified="now")],
            risk_score=0.5,
            risk_level=RiskLevel.MEDIUM,
        )
        assert mc.name == "auth"
        assert mc.risk_level == RiskLevel.MEDIUM
        assert len(mc.files) == 1
        assert mc.dependencies == []

    def test_project_semantic_map(self):
        psm = ProjectSemanticMap(
            project_name="test-project",
            project_root="/tmp/test",
            languages={"Python": 10, "TypeScript": 5},
            total_files=15,
            total_lines=5000,
        )
        assert psm.project_name == "test-project"
        assert psm.languages["Python"] == 10
        assert psm.modules == []

    def test_agent_execution_state_default(self):
        aes = AgentExecutionState()
        assert aes.phase == AgentPhase.IDLE
        assert aes.current_task is None
        assert aes.error_count == 0
        assert aes.warnings == []

    def test_diff_entry(self):
        de = DiffEntry(
            file_path="src/main.py",
            change_type="modified",
            lines_added=10,
            lines_removed=3,
            hunks=2,
        )
        assert de.file_path == "src/main.py"
        assert de.lines_added == 10

    def test_recent_change_explanation(self):
        rce = RecentChangeExplanation(
            module="auth",
            summary="Added login endpoint",
            files_changed=["auth/views.py"],
            lines_added=50,
            lines_removed=0,
            intent="Add user login functionality",
        )
        assert rce.module == "auth"
        assert rce.intent == "Add user login functionality"

    def test_change_suggestion(self):
        cs = ChangeSuggestion(
            file_path="src/main.py",
            function="login",
            module="auth",
            suggestion="Add input validation",
            reason="Missing validation",
            confidence=0.85,
            priority=Priority.HIGH,
        )
        assert cs.function == "login"
        assert cs.confidence == 0.85
        assert cs.priority == Priority.HIGH

    def test_task_card_full(self):
        tc = TaskCard(
            card_id="card_001",
            title="Fix test failure",
            card_type=CardType.FIX_TEST,
            state=TaskState.IN_PROGRESS,
            priority=Priority.CRITICAL,
            source=Source.EVAL,
            module="auth",
            target_file="auth/test_login.py",
            description="The login test is failing",
            blocking_issues=["Test timeout"],
            merge_readiness=MergeReadinessState.BLOCK,
        )
        assert tc.card_id == "card_001"
        assert tc.card_type == CardType.FIX_TEST
        assert tc.state == TaskState.IN_PROGRESS
        assert tc.priority == Priority.CRITICAL
        assert len(tc.blocking_issues) == 1

    def test_risk_alert_blocking(self):
        ra = RiskAlert(
            alert_id="risk_001",
            title="Secret exposed in config",
            level=RiskLevel.CRITICAL,
            file_path="config/.env",
            is_blocking=True,
        )
        assert ra.alert_id == "risk_001"
        assert ra.is_blocking is True
        assert ra.level == RiskLevel.CRITICAL

    def test_merge_readiness_block(self):
        mr = MergeReadiness(
            state=MergeReadinessState.BLOCK,
            blocking_issues=["Tests failing"],
            tests_passed=False,
        )
        assert mr.state == MergeReadinessState.BLOCK
        assert mr.tests_passed is False
        assert len(mr.blocking_issues) == 1

    def test_evidence_entry(self):
        ee = EvidenceEntry(
            ref_id="ev_001",
            evidence_type="test_result",
            summary="All tests passed",
            passed=True,
        )
        assert ee.passed is True
        assert ee.evidence_type == "test_result"

    def test_evidence_pack_sha256(self):
        ep = EvidencePack(
            pack_id="pack_001",
            entries=[
                EvidenceEntry(ref_id="ev_1", evidence_type="test", summary="pass", passed=True, timestamp="now"),
            ],
            passed_count=1,
        )
        h = ep.sha256
        assert len(h) == 64  # SHA256 hex
        assert isinstance(h, str)


class TestSerialization:
    def test_to_json_dataclass(self):
        fe = FileEntry(path="test.py", language="Python", size_bytes=100, last_modified="now")
        j = to_json(fe)
        d = json.loads(j)
        assert d["path"] == "test.py"
        assert d["language"] == "Python"

    def test_to_json_with_enum(self):
        tc = TaskCard(
            card_id="c1", title="test", card_type=CardType.FIX_TEST,
        )
        j = to_json(tc)
        d = json.loads(j)
        assert d["card_type"] == "fix_test"
        assert d["state"] == "pending"

    def test_task_card_envelope_roundtrip(self):
        tc = TaskCard(
            card_id="c1",
            title="Test card",
            card_type=CardType.CODE_CHANGE,
            state=TaskState.PENDING,
            priority=Priority.HIGH,
            source=Source.LOOP_KERNEL,
            merge_readiness=MergeReadinessState.REVIEW_NEEDED,
        )
        envelope = tc.to_envelope()
        assert "task_envelope" in envelope
        assert envelope["task_envelope"]["card_type"] == "code_change"

        restored = TaskCard.from_envelope(envelope)
        assert restored.card_id == "c1"
        assert restored.card_type == CardType.CODE_CHANGE
        assert restored.priority == Priority.HIGH

    def test_evidence_pack_serialize(self):
        ep = EvidencePack(
            pack_id="pack_1",
            entries=[
                EvidenceEntry(ref_id="e1", evidence_type="test", summary="ok", passed=True, timestamp="now"),
            ],
            total_entries=1,
            passed_count=1,
        )
        j = to_json(ep)
        d = json.loads(j)
        assert d["pack_id"] == "pack_1"
        assert d["total_entries"] == 1


class TestUtility:
    def test_now_iso_format(self):
        ts = now_iso()
        assert "T" in ts
        assert ts.endswith("+00:00") or "+" in ts or "Z" in ts

    def test_generate_id_format(self):
        cid = generate_id("card")
        assert cid.startswith("card_")
        assert len(cid) > 5

        rid = generate_id("risk")
        assert rid.startswith("risk_")

    def test_generate_id_uniqueness(self):
        ids = {generate_id("test") for _ in range(100)}
        assert len(ids) == 100
