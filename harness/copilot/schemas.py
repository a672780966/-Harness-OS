"""Harness Code Copilot — Core Data Schemas.

All Kernel Layer data structures as frozen dataclasses with JSON serialization.
Compatible with future A2A / Agent envelope interop.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CardType(str, Enum):
    FIX_TEST = "fix_test"
    FIX_REVIEW = "fix_review"
    CODE_CHANGE = "code_change"
    RISK_ALERT = "risk_alert"
    MERGE_CHECK = "merge_check"
    EVIDENCE = "evidence"
    COMPANION = "companion"


class TaskState(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Source(str, Enum):
    EVAL = "eval"
    REVIEW = "review"
    USER = "user"
    LOOP_KERNEL = "loop_kernel"


class MergeReadinessState(str, Enum):
    PASS = "pass"
    BLOCK = "block"
    REVIEW_NEEDED = "review_needed"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class AgentPhase(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    REPAIRING = "repairing"
    WAITING = "waiting"
    DONE = "done"


class VerificationMethod(str, Enum):
    DOCKER_EVAL = "docker_eval"
    CODEX_REVIEW = "codex_review"
    MANUAL = "manual"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FileEntry:
    """A single file within a module."""
    path: str                           # Relative path from project root
    language: str                       # Extension-based language guess
    size_bytes: int                     # File size
    last_modified: str                  # ISO 8601 timestamp
    risk_score: float = 0.0             # 0.0 (safe) — 1.0 (critical)
    risk_reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DependencyEdge:
    """A dependency from one module to another."""
    source_module: str
    target_module: str
    dep_type: str = "import"            # import, reference, config, test


@dataclass(frozen=True)
class ModuleCard:
    """A single module in the project."""
    name: str                           # Module identifier
    path: str                           # Directory path
    files: List[FileEntry] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    change_count_7d: int = 0
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    description: str = ""


@dataclass(frozen=True)
class ProjectSemanticMap:
    """Top-level structural map of a project."""
    project_name: str
    project_root: str
    modules: List[ModuleCard] = field(default_factory=list)
    dependency_graph: List[DependencyEdge] = field(default_factory=list)
    total_files: int = 0
    total_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)    # lang → file count
    scanned_at: str = ""


@dataclass(frozen=True)
class AgentExecutionState:
    """Current execution state of the agent working on the project."""
    phase: AgentPhase = AgentPhase.IDLE
    current_task: Optional[str] = None
    task_id: Optional[str] = None
    started_at: Optional[str] = None
    elapsed_seconds: float = 0.0
    phase_history: List[Dict[str, Any]] = field(default_factory=list)
    error_count: int = 0
    warnings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DiffEntry:
    """A single changed file from a git diff."""
    file_path: str
    change_type: str                    # added, modified, deleted, renamed
    lines_added: int = 0
    lines_removed: int = 0
    hunks: int = 0
    diff_summary: str = ""


@dataclass(frozen=True)
class ModuleDiffSummary:
    """Diff entries grouped by module."""
    module_name: str
    entries: List[DiffEntry] = field(default_factory=list)
    total_added: int = 0
    total_removed: int = 0
    risk_impact: RiskLevel = RiskLevel.UNKNOWN


@dataclass(frozen=True)
class RecentChangeExplanation:
    """Natural-language explanation of recent changes."""
    module: str
    summary: str                        # NL summary of what changed
    files_changed: List[str] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0
    intent: str = ""                    # What the change was trying to do
    risks: List[str] = field(default_factory=list)
    generated_at: str = ""


@dataclass(frozen=True)
class ChangeSuggestion:
    """A precise suggestion for the next change."""
    file_path: str
    function: Optional[str] = None
    module: str = ""
    suggestion: str = ""                # What to change
    reason: str = ""                    # Why this change
    confidence: float = 0.0             # 0.0 — 1.0
    priority: Priority = Priority.MEDIUM
    evidence_refs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class VerificationEntry:
    """Verification result for a task card."""
    method: VerificationMethod
    status: str                         # passed, failed, skipped, pending
    summary: str = ""
    artifact_path: Optional[str] = None
    timestamp: str = ""


@dataclass(frozen=True)
class TaskCard:
    """An agent task card — the core unit of work in the Copilot."""
    card_id: str
    title: str
    card_type: CardType
    state: TaskState = TaskState.PENDING
    priority: Priority = Priority.MEDIUM
    source: Source = Source.LOOP_KERNEL
    module: Optional[str] = None
    target_file: Optional[str] = None
    target_function: Optional[str] = None
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    evidence: List[VerificationEntry] = field(default_factory=list)
    risk_score: float = 0.0
    merge_readiness: MergeReadinessState = MergeReadinessState.REVIEW_NEEDED
    blocking_issues: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_envelope(self) -> Dict[str, Any]:
        """Serialize to A2A-compatible envelope dict."""
        d = asdict(self)
        d["card_type"] = self.card_type.value
        d["state"] = self.state.value
        d["priority"] = self.priority.value
        d["source"] = self.source.value
        d["merge_readiness"] = self.merge_readiness.value
        d["evidence"] = [asdict(e) for e in self.evidence]
        return {"task_envelope": d}

    @classmethod
    def from_envelope(cls, envelope: Dict[str, Any]) -> "TaskCard":
        """Deserialize from envelope dict."""
        d = envelope.get("task_envelope", envelope)
        d["card_type"] = CardType(d["card_type"])
        d["state"] = TaskState(d["state"])
        d["priority"] = Priority(d["priority"])
        d["source"] = Source(d["source"])
        d["merge_readiness"] = MergeReadinessState(d["merge_readiness"])
        evs = []
        for e in d.get("evidence", []):
            e["method"] = VerificationMethod(e["method"])
            evs.append(VerificationEntry(**e))
        d["evidence"] = evs
        return cls(**d)


@dataclass(frozen=True)
class RiskAlert:
    """A risk alert for a specific file or module."""
    alert_id: str
    title: str
    level: RiskLevel = RiskLevel.MEDIUM
    module: Optional[str] = None
    file_path: Optional[str] = None
    description: str = ""
    affected_lines: Optional[str] = None
    recommendation: str = ""
    is_blocking: bool = False
    created_at: str = ""


@dataclass(frozen=True)
class MergeReadiness:
    """Evaluated merge readiness for the project/feature."""
    state: MergeReadinessState = MergeReadinessState.REVIEW_NEEDED
    blocking_issues: List[str] = field(default_factory=list)
    review_required: bool = True
    tests_passed: Optional[bool] = None
    codex_approved: Optional[bool] = None
    high_risk_changes: List[str] = field(default_factory=list)
    pending_task_cards: int = 0
    summary: str = ""
    evaluated_at: str = ""


@dataclass(frozen=True)
class EvidenceEntry:
    """A single piece of evidence in a pack."""
    ref_id: str
    evidence_type: str                  # test_result, review_result, patch, audit
    file_path: Optional[str] = None
    summary: str = ""
    passed: Optional[bool] = None
    timestamp: str = ""


@dataclass(frozen=True)
class EvidencePack:
    """Collected evidence from a loop execution."""
    pack_id: str
    task_id: Optional[str] = None
    entries: List[EvidenceEntry] = field(default_factory=list)
    total_entries: int = 0
    passed_count: int = 0
    failed_count: int = 0
    generated_at: str = ""

    @property
    def sha256(self) -> str:
        """Content hash for integrity verification."""
        raw = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def to_json(obj: Any, indent: int = 2) -> str:
    """Serialize any dataclass to JSON with enum support."""
    return json.dumps(obj, indent=indent, cls=_CopilotEncoder)


def from_json(cls: type, text: str):
    """Deserialize JSON into a dataclass."""
    d = json.loads(text)
    return _from_dict(cls, d)


def _from_dict(cls: type, d: dict):
    """Recursive dict-to-dataclass conversion."""
    if hasattr(cls, "__dataclass_fields__"):
        field_types = {f.name: f.type for f in cls.__dataclass_fields__.values()}
        kwargs = {}
        for key, value in d.items():
            if key in field_types:
                ft = field_types[key]
                # Handle List types
                origin = getattr(ft, "__origin__", None)
                if origin is list and isinstance(value, list):
                    args = getattr(ft, "__args__", [Any])
                    if args:
                        kwargs[key] = [_from_dict(args[0], v) if isinstance(v, dict) else v for v in value]
                elif origin is dict and isinstance(value, dict):
                    kwargs[key] = value
                elif isinstance(value, dict):
                    kwargs[key] = _from_dict(ft, value)
                else:
                    kwargs[key] = value
        return cls(**kwargs)
    return d


class _CopilotEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        return super().default(o)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def now_iso() -> str:
    """Current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def generate_id(prefix: str = "card") -> str:
    """Generate a unique ID."""
    raw = f"{prefix}-{datetime.now(timezone.utc).timestamp()}"
    return f"{prefix}_{hashlib.md5(raw.encode()).hexdigest()[:12]}"
