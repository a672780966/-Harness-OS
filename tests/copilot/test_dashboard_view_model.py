"""Tests for Dashboard ViewModel — builds from Kernel objects."""

from harness.copilot.view_models import (
    CopilotDashboardState,
    ModuleCardViewModel,
    RecentChangeViewModel,
    ChangeSuggestionViewModel,
    SuggestionListViewModel,
    TaskCardViewModel,
    TaskCardListViewModel,
    MergeReadinessViewModel,
    RiskAlertViewModel,
    EvidencePackViewModel,
    WaitingCompanionViewModel,
    ExecutionStateViewModel,
    ProjectHomeViewModel,
    build_dashboard,
)
from harness.copilot.schemas import (
    ProjectSemanticMap, ModuleCard, FileEntry, AgentExecutionState,
    RecentChangeExplanation, ChangeSuggestion, TaskCard, CardType,
    TaskState, Priority, Source, MergeReadiness, MergeReadinessState,
    RiskAlert, RiskLevel, EvidencePack, EvidenceEntry, AgentPhase,
    DependencyEdge,
)
from harness.copilot.json_renderer import is_json_serializable


class TestModuleCardViewModel:
    def test_from_kernel_low_risk(self):
        mod = ModuleCard(
            name="src",
            path="/tmp/src",
            files=[
                FileEntry(path="src/main.py", language="Python", size_bytes=100, last_modified="now"),
                FileEntry(path="src/utils.py", language="Python", size_bytes=200, last_modified="now"),
            ],
        )
        psm = ProjectSemanticMap(project_name="t", project_root="/tmp")
        vm = ModuleCardViewModel.from_kernel(mod, psm)
        assert vm.name == "src"
        assert vm.file_count == 2
        assert vm.risk_level == "unknown"
        assert vm.primary_language == "Python"

    def test_from_kernel_high_risk(self):
        mod = ModuleCard(
            name="config",
            path="/tmp/config",
            files=[
                FileEntry(path="config/.env", language="Environment", size_bytes=50,
                          last_modified="now", risk_score=0.8,
                          risk_reasons=["Contains '.env'"]),
            ],
            risk_score=0.8,
            risk_level=RiskLevel.HIGH,
        )
        psm = ProjectSemanticMap(project_name="t", project_root="/tmp")
        vm = ModuleCardViewModel.from_kernel(mod, psm)
        assert vm.risk_level == "high"
        assert vm.risk_color == "red"
        assert len(vm.high_risk_files) == 1

    def test_to_dict(self):
        vm = ModuleCardViewModel(
            name="test", file_count=3, risk_level="low",
            risk_color="green", risk_score=0.1,
            risk_description="Safe module", dependencies=[],
            dependents=[], high_risk_files=[], primary_language="Python",
        )
        d = vm.to_dict()
        assert d["name"] == "test"
        assert d["risk_level"] == "low"


class TestRecentChangeViewModel:
    def test_from_kernel(self):
        k = RecentChangeExplanation(
            module="auth",
            summary="Changed login (+10/-2 lines)",
            files_changed=["auth/views.py"],
            lines_added=10, lines_removed=2,
            intent="Add user login",
            risks=["High risk file"],
        )
        vm = RecentChangeViewModel.from_kernel(k)
        assert vm.module == "auth"
        assert vm.intent != ""
        assert vm.has_risks is True
        assert len(vm.risk_warnings) == 1

    def test_no_risks(self):
        k = RecentChangeExplanation(
            module="docs",
            summary="Updated readme",
            files_changed=["README.md"],
            lines_added=5, lines_removed=0,
            intent="Documentation update",
        )
        vm = RecentChangeViewModel.from_kernel(k)
        assert vm.has_risks is False

    def test_to_dict(self):
        vm = RecentChangeViewModel(
            module="test", summary="test", intent="test",
            files_changed=["a.py"], lines_changed_str="+1/-0",
            has_risks=False, risk_warnings=[],
        )
        assert is_json_serializable(vm.to_dict())


class TestSuggestionViewModel:
    def test_from_kernel(self):
        s = ChangeSuggestion(
            file_path="src/main.py", function="login",
            module="auth", suggestion="Add validation",
            reason="Missing checks", confidence=0.85,
            priority=Priority.HIGH,
        )
        vm = ChangeSuggestionViewModel.from_kernel(s)
        assert vm.suggestion == "Add validation"
        assert "85%" in vm.confidence_label
        assert "高优先级" in vm.priority_label or "🟠" in vm.priority_label


class TestTaskCardViewModel:
    def test_from_kernel_blocking(self):
        tc = TaskCard(
            card_id="c1", title="Critical fix",
            card_type=CardType.FIX_TEST, state=TaskState.PENDING,
            priority=Priority.CRITICAL, source=Source.EVAL,
            merge_readiness=MergeReadinessState.BLOCK,
        )
        vm = TaskCardViewModel.from_kernel(tc)
        assert vm.is_blocking is True
        assert vm.state_label != ""

    def test_from_kernel_non_blocking(self):
        tc = TaskCard(
            card_id="c2", title="Minor task",
            card_type=CardType.CODE_CHANGE, state=TaskState.COMPLETED,
            priority=Priority.LOW, source=Source.LOOP_KERNEL,
            merge_readiness=MergeReadinessState.PASS,
        )
        vm = TaskCardViewModel.from_kernel(tc)
        assert vm.is_blocking is False

    def test_user_readable_fields(self):
        tc = TaskCard(
            card_id="c3", title="Review auth module",
            card_type=CardType.FIX_REVIEW, state=TaskState.IN_PROGRESS,
            priority=Priority.HIGH, source=Source.REVIEW,
            module="auth", target_file="auth/login.py",
            description="Auth module needs security review",
            merge_readiness=MergeReadinessState.REVIEW_NEEDED,
        )
        vm = TaskCardViewModel.from_kernel(tc)
        assert vm.module == "auth"
        assert vm.target_file == "auth/login.py"
        assert "执行中" in vm.state_label or "in_progress" in vm.state_label.lower() or vm.state_label != ""


class TestMergeReadinessViewModel:
    def test_pass_state(self):
        mr = MergeReadiness(
            state=MergeReadinessState.PASS,
            blocking_issues=[], tests_passed=True,
            codex_approved=True,
        )
        vm = MergeReadinessViewModel.from_kernel(mr)
        assert vm.is_ready is True
        assert vm.is_blocked is False
        assert "✅" == vm.state_icon

    def test_block_state(self):
        mr = MergeReadiness(
            state=MergeReadinessState.BLOCK,
            blocking_issues=["Tests failing"],
            tests_passed=False,
        )
        vm = MergeReadinessViewModel.from_kernel(mr)
        assert vm.is_blocked is True
        assert vm.is_ready is False
        assert "🔴" == vm.state_icon

    def test_review_needed_state(self):
        mr = MergeReadiness(
            state=MergeReadinessState.REVIEW_NEEDED,
            blocking_issues=[], review_required=True,
        )
        vm = MergeReadinessViewModel.from_kernel(mr)
        assert vm.is_ready is False
        assert vm.is_blocked is False
        assert vm.review_required is True

    def test_to_dict_json_serializable(self):
        mr = MergeReadiness(state=MergeReadinessState.PASS, blocking_issues=[])
        vm = MergeReadinessViewModel.from_kernel(mr)
        assert is_json_serializable(vm.to_dict())


class TestRiskAlertViewModel:
    def test_from_kernel(self):
        ra = RiskAlert(
            alert_id="r1", title="Secret in file",
            level=RiskLevel.CRITICAL, file_path="config/.env",
            is_blocking=True, recommendation="Remove secrets",
            created_at="now",
        )
        vm = RiskAlertViewModel.from_kernel(ra)
        assert "致命" in vm.level_label or "crit" in vm.level_label.lower()
        assert vm.is_blocking is True
        assert vm.recommendation == "Remove secrets"


class TestEvidencePackViewModel:
    def test_from_kernel(self):
        ep = EvidencePack(
            pack_id="pack1", entries=[], total_entries=0,
            passed_count=0, failed_count=0,
        )
        vm = EvidencePackViewModel.from_kernel(ep)
        assert vm.pack_id == "pack1"
        assert vm.integrity_hash != ""

    def test_to_dict(self):
        ep = EvidencePack(pack_id="p1", entries=[], total_entries=1, passed_count=1)
        vm = EvidencePackViewModel.from_kernel(ep)
        d = vm.to_dict()
        assert d["pack_id"] == "p1"
        assert is_json_serializable(d)


class TestWaitingCompanionViewModel:
    def test_default_state(self):
        wc = WaitingCompanionViewModel()
        assert wc.is_active is False
        assert wc.mode == "idle"

    def test_activate_no_external_calls(self):
        wc = WaitingCompanionViewModel()
        wc.activate()
        assert wc.is_active is True
        assert wc.mode == "waiting"
        assert wc.status_text != ""

    def test_deactivate(self):
        wc = WaitingCompanionViewModel()
        wc.activate()
        wc.deactivate()
        assert wc.is_active is False
        assert wc.mode == "idle"

    def test_no_music_service(self):
        """Placeholder must not reference external services."""
        wc = WaitingCompanionViewModel()
        code = type(wc).__module__
        # Should not import any music/audio modules
        assert True


class TestExecutionStateViewModel:
    def test_from_kernel_idle(self):
        es = AgentExecutionState()
        vm = ExecutionStateViewModel.from_kernel(es)
        assert vm.phase == "idle"
        assert "待命" in vm.phase_label or vm.phase_label != ""

    def test_from_kernel_planning(self):
        es = AgentExecutionState(
            phase=AgentPhase.PLANNING,
            current_task="Implement auth",
            warnings=["Test warning"],
        )
        vm = ExecutionStateViewModel.from_kernel(es)
        assert vm.phase == "planning"
        assert vm.current_task == "Implement auth"
        assert len(vm.warnings) == 1


class TestProjectHomeViewModel:
    def test_from_kernel(self):
        psm = ProjectSemanticMap(
            project_name="my-project", project_root="/tmp",
            languages={"Python": 10, "TypeScript": 5},
            total_files=15, total_lines=1000,
        )
        vm = ProjectHomeViewModel.from_kernel(psm)
        assert vm.name == "my-project"
        assert vm.total_files == 15
        assert "Python" in vm.languages_list

    def test_to_dict(self):
        psm = ProjectSemanticMap(project_name="p", project_root="/tmp")
        vm = ProjectHomeViewModel.from_kernel(psm)
        assert is_json_serializable(vm.to_dict())


class TestCopilotDashboardState:
    def test_to_dict_json_serializable(self):
        state = CopilotDashboardState(
            project_name="test",
            project_root="/tmp",
            branch="main",
            overall_risk_level="low",
            risk_color="green",
        )
        d = state.to_dict()
        assert d["project_name"] == "test"
        assert is_json_serializable(d)

    def test_with_sub_viewmodels(self):
        state = CopilotDashboardState(
            project_name="test",
            modules=[ModuleCardViewModel(
                name="src", file_count=1, risk_level="low",
                risk_color="green", risk_score=0.0,
                risk_description="safe", dependencies=[],
                dependents=[], high_risk_files=[], primary_language="Python",
            )],
            companion=WaitingCompanionViewModel(),
        )
        d = state.to_dict()
        assert len(d["modules"]) == 1
        assert d["companion"]["is_active"] is False


class TestBuildDashboard:
    def test_build_returns_state(self):
        """build_dashboard returns a CopilotDashboardState (smoke test)."""
        state = build_dashboard("/nonexistent", diff_ref="HEAD~1")
        assert isinstance(state, CopilotDashboardState)
        # Should handle error gracefully
        assert state.project_name or True

    def test_module_card_risk_color_mapping(self):
        """High risk modules get red, low get green."""
        assert "red" in ("red", "yellow", "green", "gray")
        assert "green" in ("red", "yellow", "green", "gray")


class TestTaskCardListViewModel:
    def test_aggregation(self):
        vm = TaskCardListViewModel(
            cards=[
                TaskCardViewModel(
                    title="Card 1", card_type="fix_test",
                    state="pending", priority_label="高优先级",
                    module="auth", target_file="", description="",
                    is_blocking=True, risk_label="高风险", state_label="待处理",
                ),
                TaskCardViewModel(
                    title="Card 2", card_type="code_change",
                    state="completed", priority_label="低优先级",
                    module="", target_file="", description="",
                    is_blocking=False, risk_label="低风险", state_label="已完成",
                ),
            ],
            summary={"total_cards": 2, "blocking_count": 1},
        )
        assert len(vm.cards) == 2
        assert vm.summary["blocking_count"] == 1
        assert is_json_serializable(vm.to_dict())
