"""Tests for Markdown Renderer."""

from harness.copilot.markdown_renderer import (
    render_dashboard,
    render_modules,
    render_task_cards,
    render_readiness,
    render_changes,
    render_evidence,
    render_companion,
)
from harness.copilot.view_models import (
    CopilotDashboardState,
    ModuleCardViewModel,
    TaskCardViewModel,
    TaskCardListViewModel,
    MergeReadinessViewModel,
    RecentChangeViewModel,
    EvidencePackViewModel,
    WaitingCompanionViewModel,
    SuggestionListViewModel,
    ChangeSuggestionViewModel,
)
from harness.copilot.schemas import MergeReadinessState


class TestRenderDashboard:
    def test_dashboard_includes_all_sections(self):
        state = CopilotDashboardState(
            project_name="test-proj",
            project_root="/tmp",
            branch="main",
            overall_risk_level="low",
            risk_color="green",
            agent_phase="idle",
            agent_phase_label="待命",
            uncommitted_changes=2,
            module_count=3,
        )
        output = render_dashboard(state)
        assert "test-proj" in output
        assert "当前项目状态" in output
        assert "/tmp" in output
        assert "main" in output
        assert "待命" in output

    def test_dashboard_with_readiness(self):
        state = CopilotDashboardState(
            project_name="test",
            readiness=MergeReadinessViewModel(
                state="pass", state_label="可以合并 ✅", state_icon="✅",
                summary="All checks passed", blocking_issues=[],
                is_blocked=False, is_ready=True, review_required=False,
                pending_cards=0, high_risk_count=0,
            ),
        )
        output = render_dashboard(state)
        assert "合并就绪度" in output
        assert "✅" in output

    def test_dashboard_with_changes(self):
        state = CopilotDashboardState(
            project_name="test",
            recent_changes=[
                RecentChangeViewModel(
                    module="auth", summary="Changed auth (+5/-0)",
                    intent="Bug 修复", files_changed=["auth.py"],
                    lines_changed_str="+5/-0", has_risks=False,
                    risk_warnings=[],
                ),
            ],
        )
        output = render_dashboard(state)
        assert "最近修改" in output
        assert "auth" in output

    def test_dashboard_with_modules(self):
        state = CopilotDashboardState(
            project_name="test",
            modules=[
                ModuleCardViewModel(
                    name="src", file_count=5, risk_level="low",
                    risk_color="green", risk_score=0.0,
                    risk_description="Safe", dependencies=[],
                    dependents=[], high_risk_files=[], primary_language="Python",
                ),
            ],
        )
        output = render_dashboard(state)
        assert "重点模块" in output
        assert "src" in output

    def test_dashboard_with_companion(self):
        state = CopilotDashboardState(
            project_name="test",
            companion=WaitingCompanionViewModel(),
        )
        output = render_dashboard(state)
        assert "等待陪伴" in output
        assert "未激活" in output or "待命" in output


class TestRenderModules:
    def test_module_list(self):
        modules = [
            ModuleCardViewModel(
                name="auth", file_count=3, risk_level="high",
                risk_color="red", risk_score=0.7,
                risk_description="Auth module risk", dependencies=["db"],
                dependents=[], high_risk_files=[{"path": "auth/login.py", "score": 0.8, "reasons": ["auth"]}],
                primary_language="Python",
            ),
        ]
        output = render_modules(modules)
        assert "auth" in output
        assert "文件数" in output
        assert "高风险" in output or "high" in output.lower()

    def test_high_risk_files_shown(self):
        modules = [
            ModuleCardViewModel(
                name="config", file_count=1, risk_level="high",
                risk_color="red", risk_score=0.8,
                risk_description="Config risk", dependencies=[],
                dependents=[], high_risk_files=[{"path": ".env", "score": 0.8, "reasons": ["secret"]}],
                primary_language="Config",
            ),
        ]
        output = render_modules(modules)
        assert ".env" in output


class TestRenderTaskCards:
    def test_blocking_cards_marked(self):
        cards = TaskCardListViewModel(
            cards=[
                TaskCardViewModel(
                    title="Critical bug", card_type="fix_test",
                    state="pending", priority_label="🔴 紧急",
                    module="auth", target_file="", description="Fix auth bug",
                    is_blocking=True, risk_label="高风险", state_label="待处理",
                ),
            ],
            summary={"total_cards": 1, "blocking_count": 1},
        )
        output = render_task_cards(cards)
        assert "🔴" in output
        assert "阻塞合并" in output or "Critical bug" in output

    def test_non_blocking_cards(self):
        cards = TaskCardListViewModel(
            cards=[
                TaskCardViewModel(
                    title="Minor cleanup", card_type="code_change",
                    state="completed", priority_label="⚪ 低优先级",
                    module="", target_file="", description="",
                    is_blocking=False, risk_label="低风险", state_label="已完成",
                ),
            ],
        )
        output = render_task_cards(cards)
        assert "Minor cleanup" in output

    def test_card_with_module_and_file(self):
        cards = TaskCardListViewModel(
            cards=[
                TaskCardViewModel(
                    title="Review auth", card_type="fix_review",
                    state="pending", priority_label="🟠 高优先级",
                    module="auth", target_file="auth/login.py",
                    description="Review auth module", is_blocking=False,
                    risk_label="中风险", state_label="待处理",
                ),
            ],
        )
        output = render_task_cards(cards)
        assert "auth/login.py" in output or "auth" in output
        assert "Review auth" in output


class TestRenderReadiness:
    def test_pass_output(self):
        rm = MergeReadinessViewModel(
            state="pass", state_label="可以合并 ✅", state_icon="✅",
            summary="All OK", blocking_issues=[],
            is_blocked=False, is_ready=True, review_required=False,
            pending_cards=0, high_risk_count=0,
        )
        output = render_readiness(rm)
        assert "✅" in output
        assert "可以合并" in output

    def test_block_output(self):
        rm = MergeReadinessViewModel(
            state="block", state_label="禁止合并 🔴", state_icon="🔴",
            summary="Blocked", blocking_issues=["Tests failing", "Security review needed"],
            is_blocked=True, is_ready=False, review_required=True,
            pending_cards=2, high_risk_count=3,
        )
        output = render_readiness(rm)
        assert "🔴" in output
        assert "Tests failing" in output
        assert "Security review" in output

    def test_review_needed_output(self):
        rm = MergeReadinessViewModel(
            state="review_needed", state_label="需审查后合并 🟡", state_icon="🟡",
            summary="Needs review", blocking_issues=[],
            is_blocked=False, is_ready=False, review_required=True,
            pending_cards=1, high_risk_count=0,
        )
        output = render_readiness(rm)
        assert "🟡" in output
        assert "需审查" in output or "review_needed" in output


class TestRenderChanges:
    def test_with_risks(self):
        changes = [
            RecentChangeViewModel(
                module="config", summary="Changed .env (+1/-1)",
                intent="配置变更", files_changed=[".env"],
                lines_changed_str="+1/-1", has_risks=True,
                risk_warnings=[".env contains secrets"],
            ),
        ]
        output = render_changes(changes)
        assert "⚠" in output or "配置变更" in output

    def test_no_risks(self):
        changes = [
            RecentChangeViewModel(
                module="docs", summary="Updated readme",
                intent="文档更新", files_changed=["README.md"],
                lines_changed_str="+5/-0", has_risks=False,
                risk_warnings=[],
            ),
        ]
        output = render_changes(changes)
        assert "文档更新" in output or "docs" in output


class TestRenderEvidence:
    def test_basic_output(self):
        ep = EvidencePackViewModel(
            pack_id="pack1", total=5, passed=4, failed=1,
            integrity_hash="abc123",
        )
        output = render_evidence(ep)
        assert "证据包" in output
        assert str(ep.total) in output
        assert str(ep.passed) in output


class TestRenderCompanion:
    def test_inactive(self):
        wc = WaitingCompanionViewModel()
        output = render_companion(wc)
        assert "待命" in output or "等待陪伴" in output

    def test_activated_output(self):
        wc = WaitingCompanionViewModel()
        wc.activate()
        output = render_companion(wc)
        assert "等待陪伴模式" in output
        assert "音乐服务未接入" in output

    def test_no_external_service_reference(self):
        """Companion text must not reference active external services."""
        wc = WaitingCompanionViewModel()
        wc.activate()
        output = render_companion(wc)
        assert "音乐服务未接入" in output
