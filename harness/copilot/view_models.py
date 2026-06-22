"""ViewModels — UX layer data structures that consume Kernel objects
and produce user-facing semantic summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schemas import (
    ProjectSemanticMap, ModuleCard, AgentExecutionState, AgentPhase,
    RecentChangeExplanation, ChangeSuggestion, TaskCard, MergeReadiness,
    MergeReadinessState, RiskAlert, RiskLevel, EvidencePack,
    now_iso,
)
from .project_scanner import scan_project
from .event_collector import get_git_diff, get_git_branch, is_git_repo, get_git_status
from .diff_analyzer import parse_diff, group_diff_by_module
from .change_explainer import explain_diff
from .risk_classifier import generate_risk_alerts
from .task_card import from_risk_alerts, from_change_explanations, from_suggestions, generate_summary
from .suggestion_engine import generate_suggestions
from .merge_readiness import evaluate_merge_readiness
from .evidence_pack import build_from_task_cards


# ---------------------------------------------------------------------------
# Copilot Dashboard State — aggregates all sub-ViewModels
# ---------------------------------------------------------------------------

@dataclass
class CopilotDashboardState:
    """Aggregate dashboard state — one object to render."""
    project_name: str = ""
    project_root: str = ""
    branch: str = "unknown"
    overall_risk_level: str = "unknown"
    risk_color: str = "gray"
    agent_phase: str = "idle"
    agent_phase_label: str = "待命"
    uncommitted_changes: int = 0
    module_count: int = 0
    generated_at: str = ""

    # Sub-ViewModels
    modules: List["ModuleCardViewModel"] = field(default_factory=list)
    recent_changes: List["RecentChangeViewModel"] = field(default_factory=list)
    suggestions: "SuggestionListViewModel | None" = None
    task_cards: "TaskCardListViewModel | None" = None
    readiness: "MergeReadinessViewModel | None" = None
    evidence: "EvidencePackViewModel | None" = None
    companion: "WaitingCompanionViewModel | None" = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_root": self.project_root,
            "branch": self.branch,
            "overall_risk_level": self.overall_risk_level,
            "risk_color": self.risk_color,
            "agent_phase": self.agent_phase,
            "agent_phase_label": self.agent_phase_label,
            "uncommitted_changes": self.uncommitted_changes,
            "module_count": self.module_count,
            "generated_at": self.generated_at,
            "modules": [m.to_dict() for m in self.modules],
            "recent_changes": [c.to_dict() for c in self.recent_changes],
            "suggestions": self.suggestions.to_dict() if self.suggestions else None,
            "task_cards": self.task_cards.to_dict() if self.task_cards else None,
            "readiness": self.readiness.to_dict() if self.readiness else None,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "companion": self.companion.to_dict() if self.companion else None,
        }


def build_dashboard(project_root: str, diff_ref: str = "HEAD~1") -> CopilotDashboardState:
    """Build the full dashboard from a project path."""
    state = CopilotDashboardState(
        project_root=project_root,
        generated_at=now_iso(),
    )

    # Scan project
    try:
        sem_map = scan_project(project_root)
    except Exception as e:
        state.project_name = str(e)
        return state

    state.project_name = sem_map.project_name
    state.module_count = len(sem_map.modules)

    # Git info
    if is_git_repo(project_root):
        state.branch = get_git_branch(project_root)
        state.uncommitted_changes = len(get_git_status(project_root))
    else:
        state.branch = "not a git repo"

    # Agent phase (hardcoded to idle for now — real agent state comes from Loop Kernel)
    state.agent_phase = AgentPhase.IDLE.value
    state.agent_phase_label = "待命"

    # Module ViewModels
    for mod in sem_map.modules:
        state.modules.append(ModuleCardViewModel.from_kernel(mod, sem_map))

    # Overall risk
    high_risk = [m for m in state.modules if m.risk_level in ("critical", "high")]
    if high_risk:
        state.overall_risk_level = "high"
        state.risk_color = "red"
    elif any(m.risk_level == "medium" for m in state.modules):
        state.overall_risk_level = "medium"
        state.risk_color = "yellow"
    else:
        state.overall_risk_level = "low"
        state.risk_color = "green"

    # Diff analysis
    diff_text = get_git_diff(project_root, base_ref=diff_ref)
    if diff_text:
        explanations = explain_diff(diff_text, sem_map)
        state.recent_changes = [
            RecentChangeViewModel.from_kernel(e) for e in explanations
        ]

        # Risk alerts
        entries = parse_diff(diff_text)
        summaries = group_diff_by_module(entries, sem_map)
        alerts = generate_risk_alerts(summaries, sem_map)

        # Task cards
        risk_cards = from_risk_alerts(alerts)
        change_cards = from_change_explanations(explanations)
        suggestions_data = generate_suggestions(project_root, sem_map, diff_text)
        suggestion_cards = from_suggestions(suggestions_data)

        all_cards = risk_cards + change_cards + suggestion_cards
        card_summary = generate_summary(all_cards)
        state.task_cards = TaskCardListViewModel(
            cards=[TaskCardViewModel.from_kernel(c) for c in all_cards],
            summary=card_summary,
        )

        # Suggestions
        state.suggestions = SuggestionListViewModel(
            suggestions=[ChangeSuggestionViewModel.from_kernel(s) for s in suggestions_data],
        )

        # Merge readiness
        mr = evaluate_merge_readiness(
            task_cards=all_cards,
            risk_alerts=alerts,
            branch_name=state.branch,
        )
        state.readiness = MergeReadinessViewModel.from_kernel(mr)

        # Evidence pack
        ep = build_from_task_cards(all_cards)
        state.evidence = EvidencePackViewModel.from_kernel(ep)

    # Waiting companion placeholder
    state.companion = WaitingCompanionViewModel()

    return state


# ---------------------------------------------------------------------------
# Module Card ViewModel
# ---------------------------------------------------------------------------

@dataclass
class ModuleCardViewModel:
    name: str
    file_count: int
    risk_level: str             # critical / high / medium / low / unknown
    risk_color: str             # red / yellow / green / gray
    risk_score: float
    risk_description: str       # user-readable risk explanation
    dependencies: List[str]
    dependents: List[str]
    high_risk_files: List[Dict[str, Any]]
    primary_language: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "file_count": self.file_count,
            "risk_level": self.risk_level,
            "risk_color": self.risk_color,
            "risk_score": self.risk_score,
            "risk_description": self.risk_description,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "high_risk_files": self.high_risk_files,
            "primary_language": self.primary_language,
        }

    @classmethod
    def from_kernel(cls, mod: ModuleCard, sem_map: ProjectSemanticMap) -> "ModuleCardViewModel":
        risk_level = mod.risk_level.value if hasattr(mod.risk_level, "value") else str(mod.risk_level)
        risk_color = _risk_color(risk_level)
        risk_desc = _risk_description(risk_level, mod.name)

        hr_files = [
            {"path": f.path, "score": f.risk_score, "reasons": f.risk_reasons}
            for f in mod.files if f.risk_score >= 0.5
        ]

        langs = {f.language for f in mod.files}
        primary_lang = max(set(langs), key=list(langs).count) if langs else "Unknown"

        return cls(
            name=mod.name,
            file_count=len(mod.files),
            risk_level=risk_level,
            risk_color=risk_color,
            risk_score=mod.risk_score,
            risk_description=risk_desc,
            dependencies=mod.dependencies if mod.dependencies else [],
            dependents=mod.dependents if mod.dependents else [],
            high_risk_files=hr_files,
            primary_language=primary_lang,
        )


# ---------------------------------------------------------------------------
# Recent Change ViewModel
# ---------------------------------------------------------------------------

@dataclass
class RecentChangeViewModel:
    module: str
    summary: str
    intent: str
    files_changed: List[str]
    lines_changed_str: str
    has_risks: bool
    risk_warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "summary": self.summary,
            "intent": self.intent,
            "files_changed": self.files_changed,
            "lines_changed_str": self.lines_changed_str,
            "has_risks": self.has_risks,
            "risk_warnings": self.risk_warnings,
        }

    @classmethod
    def from_kernel(cls, k: RecentChangeExplanation) -> "RecentChangeViewModel":
        return cls(
            module=k.module,
            summary=k.summary,
            intent=_intent_label(k.intent),
            files_changed=k.files_changed,
            lines_changed_str=f"+{k.lines_added}/-{k.lines_removed}",
            has_risks=len(k.risks) > 0,
            risk_warnings=k.risks if k.risks else [],
        )


# ---------------------------------------------------------------------------
# Change Suggestion ViewModel
# ---------------------------------------------------------------------------

@dataclass
class ChangeSuggestionViewModel:
    suggestion: str
    reason: str
    priority_label: str
    confidence_label: str
    file_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion": self.suggestion,
            "reason": self.reason,
            "priority_label": self.priority_label,
            "confidence_label": self.confidence_label,
            "file_path": self.file_path,
        }

    @classmethod
    def from_kernel(cls, s: ChangeSuggestion) -> "ChangeSuggestionViewModel":
        priority_label = _priority_label(s.priority)
        confidence_label = f"{s.confidence:.0%}" if s.confidence else "未知"
        return cls(
            suggestion=s.suggestion,
            reason=s.reason,
            priority_label=priority_label,
            confidence_label=confidence_label,
            file_path=s.file_path,
        )


@dataclass
class SuggestionListViewModel:
    suggestions: List[ChangeSuggestionViewModel] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"suggestions": [s.to_dict() for s in self.suggestions]}


# ---------------------------------------------------------------------------
# Task Card ViewModel
# ---------------------------------------------------------------------------

@dataclass
class TaskCardViewModel:
    title: str
    card_type: str
    state: str
    priority_label: str
    module: str
    target_file: str
    description: str
    is_blocking: bool
    risk_label: str
    state_label: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "card_type": self.card_type,
            "state": self.state,
            "priority_label": self.priority_label,
            "module": self.module,
            "target_file": self.target_file,
            "description": self.description,
            "is_blocking": self.is_blocking,
            "risk_label": self.risk_label,
            "state_label": self.state_label,
        }

    @classmethod
    def from_kernel(cls, tc: TaskCard) -> "TaskCardViewModel":
        return cls(
            title=tc.title,
            card_type=tc.card_type.value if hasattr(tc.card_type, "value") else str(tc.card_type),
            state=tc.state.value if hasattr(tc.state, "value") else str(tc.state),
            priority_label=_priority_label(tc.priority),
            module=tc.module or "",
            target_file=tc.target_file or "",
            description=tc.description,
            is_blocking=(
                tc.merge_readiness == MergeReadinessState.BLOCK
                or (hasattr(tc.merge_readiness, "value") and tc.merge_readiness.value == "block")
            ),
            risk_label=_risk_label(tc.risk_score),
            state_label=_state_label(tc.state),
        )


@dataclass
class TaskCardListViewModel:
    cards: List[TaskCardViewModel] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cards": [c.to_dict() for c in self.cards],
            "summary": self.summary,
        }


# ---------------------------------------------------------------------------
# Merge Readiness ViewModel
# ---------------------------------------------------------------------------

@dataclass
class MergeReadinessViewModel:
    state: str
    state_label: str
    state_icon: str
    summary: str
    blocking_issues: List[str]
    is_blocked: bool
    is_ready: bool
    review_required: bool
    pending_cards: int
    high_risk_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "state_label": self.state_label,
            "state_icon": self.state_icon,
            "summary": self.summary,
            "blocking_issues": self.blocking_issues,
            "is_blocked": self.is_blocked,
            "is_ready": self.is_ready,
            "review_required": self.review_required,
            "pending_cards": self.pending_cards,
            "high_risk_count": self.high_risk_count,
        }

    @classmethod
    def from_kernel(cls, mr: MergeReadiness) -> "MergeReadinessViewModel":
        state = mr.state.value if hasattr(mr.state, "value") else str(mr.state)
        state_label, state_icon = _readiness_display(state)

        return cls(
            state=state,
            state_label=state_label,
            state_icon=state_icon,
            summary=mr.summary,
            blocking_issues=mr.blocking_issues,
            is_blocked=(state == "block"),
            is_ready=(state == "pass"),
            review_required=mr.review_required,
            pending_cards=mr.pending_task_cards,
            high_risk_count=len(mr.high_risk_changes),
        )


# ---------------------------------------------------------------------------
# Risk Alert ViewModel
# ---------------------------------------------------------------------------

@dataclass
class RiskAlertViewModel:
    title: str
    module: str
    file_path: str
    level_label: str
    level_color: str
    is_blocking: bool
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "module": self.module,
            "file_path": self.file_path,
            "level_label": self.level_label,
            "level_color": self.level_color,
            "is_blocking": self.is_blocking,
            "recommendation": self.recommendation,
        }

    @classmethod
    def from_kernel(cls, ra: RiskAlert) -> "RiskAlertViewModel":
        level = ra.level.value if hasattr(ra.level, "value") else str(ra.level)
        return cls(
            title=ra.title,
            module=ra.module or "",
            file_path=ra.file_path or "",
            level_label=_level_label(level),
            level_color=_risk_color(level),
            is_blocking=ra.is_blocking,
            recommendation=ra.recommendation,
        )


# ---------------------------------------------------------------------------
# Evidence Pack ViewModel
# ---------------------------------------------------------------------------

@dataclass
class EvidencePackViewModel:
    pack_id: str
    total: int
    passed: int
    failed: int
    integrity_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "integrity_hash": self.integrity_hash,
        }

    @classmethod
    def from_kernel(cls, ep: EvidencePack) -> "EvidencePackViewModel":
        return cls(
            pack_id=ep.pack_id,
            total=ep.total_entries,
            passed=ep.passed_count,
            failed=ep.failed_count,
            integrity_hash=ep.sha256,
        )


# ---------------------------------------------------------------------------
# Waiting Companion ViewModel (placeholder — no external services)
# ---------------------------------------------------------------------------

@dataclass
class WaitingCompanionViewModel:
    """Pure placeholder. No music service, no external API, no playback."""
    is_active: bool = False
    mode: str = "idle"
    status_text: str = "等待中"
    waiting_since: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_active": self.is_active,
            "mode": self.mode,
            "status_text": self.status_text,
            "waiting_since": self.waiting_since,
        }

    def activate(self) -> None:
        """Activate companion mode (no external calls)."""
        self.is_active = True
        self.mode = "waiting"
        self.status_text = "等待 Agent 执行中"
        self.waiting_since = now_iso()

    def deactivate(self) -> None:
        """Deactivate companion mode."""
        self.is_active = False
        self.mode = "idle"
        self.status_text = "待命"


# ---------------------------------------------------------------------------
# Execution State ViewModel
# ---------------------------------------------------------------------------

@dataclass
class ExecutionStateViewModel:
    phase: str
    phase_label: str
    current_task: str
    warnings: List[str]
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "phase_label": self.phase_label,
            "current_task": self.current_task,
            "warnings": self.warnings,
            "error_count": self.error_count,
        }

    @classmethod
    def from_kernel(cls, es: AgentExecutionState) -> "ExecutionStateViewModel":
        return cls(
            phase=es.phase.value if hasattr(es.phase, "value") else str(es.phase),
            phase_label=_agent_phase_label(es.phase),
            current_task=es.current_task or "",
            warnings=list(es.warnings),
            error_count=es.error_count,
        )


# ---------------------------------------------------------------------------
# Project Home ViewModel
# ---------------------------------------------------------------------------

@dataclass
class ProjectHomeViewModel:
    name: str
    root: str
    branch: str
    total_files: int
    total_lines: int
    module_count: int
    languages_list: List[str]
    risk_level: str
    uncommitted_changes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "root": self.root,
            "branch": self.branch,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "module_count": self.module_count,
            "languages_list": self.languages_list,
            "risk_level": self.risk_level,
            "uncommitted_changes": self.uncommitted_changes,
        }

    @classmethod
    def from_kernel(cls, sem_map: ProjectSemanticMap) -> "ProjectHomeViewModel":
        branch = "not a git repo"
        uncommitted = 0
        if is_git_repo(sem_map.project_root):
            branch = get_git_branch(sem_map.project_root)
            uncommitted = len(get_git_status(sem_map.project_root))

        langs = sorted(sem_map.languages.keys(), key=lambda k: -sem_map.languages[k])[:5]

        risk = "low"
        for mod in sem_map.modules:
            rl = mod.risk_level.value if hasattr(mod.risk_level, "value") else str(mod.risk_level)
            if rl in ("critical", "high"):
                risk = "high"
                break
            if rl == "medium":
                risk = "medium"

        return cls(
            name=sem_map.project_name,
            root=sem_map.project_root,
            branch=branch,
            total_files=sem_map.total_files,
            total_lines=sem_map.total_lines,
            module_count=len(sem_map.modules),
            languages_list=langs,
            risk_level=risk,
            uncommitted_changes=uncommitted,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _risk_color(level: str) -> str:
    return {"critical": "red", "high": "red", "medium": "yellow", "low": "green"}.get(level, "gray")


def _risk_description(level: str, module: str) -> str:
    descriptions = {
        "critical": f"⚠️ 极高风险 — {module} 模块包含安全、密钥或支付相关文件，需人工审查后方可合并。",
        "high": f"⚠️ 高风险 — {module} 模块包含敏感文件或大范围变更，建议重点审查。",
        "medium": f"⚡ 中等风险 — {module} 模块需关注，建议检查变更范围。",
        "low": f"✅ 低风险 — {module} 模块变更安全。",
    }
    return descriptions.get(level, f"风险未知 — {module}")


def _intent_label(intent: str) -> str:
    """Map raw intent to user-friendly label."""
    if not intent:
        return "未知变更"
    mapping = {
        "Adding or updating tests": "测试用例变更",
        "Bug fix": "Bug 修复",
        "Code refactoring": "代码重构",
        "Documentation update": "文档更新",
        "Configuration change": "配置变更",
        "Database migration": "数据库迁移",
        "Code style / formatting": "代码风格调整",
        "Feature implementation": "功能实现",
        "Deprecation handling": "废弃处理",
        "Dependency upgrade": "依赖升级",
        "Code modification (mixed add/remove)": "代码修改（混合）",
        "New code addition": "新增代码",
        "Code removal": "代码删除",
        "Code change": "代码变更",
    }
    return mapping.get(intent, intent)


def _priority_label(priority) -> str:
    p = priority.value if hasattr(priority, "value") else str(priority)
    labels = {"critical": "🔴 紧急", "high": "🟠 高优先级", "medium": "🟡 中优先级", "low": "⚪ 低优先级"}
    return labels.get(p, p)


def _risk_label(score: float) -> str:
    if score >= 0.8:
        return "🔴 极高风险"
    elif score >= 0.5:
        return "🟠 高风险"
    elif score >= 0.2:
        return "🟡 中风险"
    return "✅ 低风险"


def _state_label(state) -> str:
    s = state.value if hasattr(state, "value") else str(state)
    labels = {"pending": "⏳ 待处理", "in_progress": "🔄 执行中", "completed": "✅ 已完成", "blocked": "🚫 已阻塞"}
    return labels.get(s, s)


def _readiness_display(state: str):
    displays = {
        "pass": ("可以合并 ✅", "✅"),
        "block": ("禁止合并 🔴", "🔴"),
        "review_needed": ("需审查后合并 🟡", "🟡"),
    }
    return displays.get(state, ("状态未知 ❓", "❓"))


def _level_label(level: str) -> str:
    labels = {"critical": "🔴 致命", "high": "🟠 高", "medium": "🟡 中", "low": "✅ 低", "unknown": "❓ 未知"}
    return labels.get(level, level)


def _agent_phase_label(phase) -> str:
    p = phase.value if hasattr(phase, "value") else str(phase)
    labels = {
        "idle": "待命",
        "planning": "规划中",
        "implementing": "执行中",
        "testing": "测试中",
        "reviewing": "审查中",
        "repairing": "修复中",
        "waiting": "等待中",
        "done": "已完成",
    }
    return labels.get(p, p)
