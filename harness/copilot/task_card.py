"""Task Card Generator — create structured Task Cards from analysis results."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import (
    CardType,
    TaskCard,
    TaskState,
    Priority,
    Source,
    MergeReadinessState,
    VerificationEntry,
    VerificationMethod,
    RecentChangeExplanation,
    RiskAlert,
    ChangeSuggestion,
    now_iso,
    generate_id,
)
from .risk_classifier import RiskLevel


def from_risk_alerts(
    alerts: List[RiskAlert],
    max_cards: int = 10,
) -> List[TaskCard]:
    """Generate task cards from risk alerts."""
    cards: List[TaskCard] = []

    for alert in alerts:
        card_type = CardType.RISK_ALERT
        priority = Priority.HIGH
        if alert.level in (RiskLevel.CRITICAL,):
            priority = Priority.CRITICAL
        elif alert.level == RiskLevel.HIGH:
            priority = Priority.HIGH
        elif alert.level == RiskLevel.MEDIUM:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW

        card = TaskCard(
            card_id=generate_id("risk"),
            title=alert.title,
            card_type=card_type,
            state=TaskState.PENDING if alert.is_blocking else TaskState.PENDING,
            priority=priority,
            source=Source.LOOP_KERNEL,
            module=alert.module,
            target_file=alert.file_path,
            description=alert.description,
            acceptance_criteria=[f"Review and resolve: {alert.title}"],
            risk_score=0.5,
            merge_readiness=MergeReadinessState.BLOCK if alert.is_blocking else MergeReadinessState.REVIEW_NEEDED,
            blocking_issues=[alert.title] if alert.is_blocking else [],
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    return cards[:max_cards]


def from_change_explanations(
    explanations: List[RecentChangeExplanation],
    max_cards: int = 10,
) -> List[TaskCard]:
    """Generate review task cards from change explanations."""
    cards: List[TaskCard] = []

    for expl in explanations:
        card = TaskCard(
            card_id=generate_id("review"),
            title=f"Review changes in '{expl.module}'",
            card_type=CardType.FIX_REVIEW,
            state=TaskState.PENDING,
            priority=Priority.MEDIUM if not expl.risks else Priority.HIGH,
            source=Source.LOOP_KERNEL,
            module=expl.module,
            description=expl.summary,
            acceptance_criteria=[
                f"Review {len(expl.files_changed)} file(s) in {expl.module}",
                f"Verify intent: {expl.intent}",
            ],
            risk_score=0.4 if expl.risks else 0.1,
            merge_readiness=MergeReadinessState.REVIEW_NEEDED,
            blocking_issues=expl.risks[:3],
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    return cards[:max_cards]


def from_suggestions(
    suggestions: List[ChangeSuggestion],
    max_cards: int = 10,
) -> List[TaskCard]:
    """Generate task cards from change suggestions."""
    cards: List[TaskCard] = []

    for sug in suggestions:
        card_type = CardType.CODE_CHANGE
        if "test" in sug.suggestion.lower():
            card_type = CardType.FIX_TEST

        state = TaskState.PENDING
        if sug.confidence < 0.4:
            state = TaskState.PENDING  # Low confidence = still pending investigation

        card = TaskCard(
            card_id=generate_id("sug"),
            title=sug.suggestion[:100],
            card_type=card_type,
            state=state,
            priority=sug.priority,
            source=Source.LOOP_KERNEL,
            module=sug.module,
            target_file=sug.file_path,
            target_function=sug.function,
            description=f"{sug.suggestion}\n\nReason: {sug.reason}",
            acceptance_criteria=[f"Implement: {sug.suggestion[:80]}"],
            risk_score=0.3,
            merge_readiness=MergeReadinessState.REVIEW_NEEDED,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        cards.append(card)

    return cards[:max_cards]


def from_verification(
    test_name: str,
    status: str,
    module: Optional[str] = None,
    file_path: Optional[str] = None,
) -> TaskCard:
    """Generate a task card from a test/verification result."""
    if status == "failed":
        card_type = CardType.FIX_TEST
        priority = Priority.HIGH
        state = TaskState.PENDING
        merge_state = MergeReadinessState.BLOCK
    else:
        card_type = CardType.EVIDENCE
        priority = Priority.LOW
        state = TaskState.COMPLETED
        merge_state = MergeReadinessState.PASS

    return TaskCard(
        card_id=generate_id("verify"),
        title=f"{'Fix: ' if status == 'failed' else ''}{test_name}",
        card_type=card_type,
        state=state,
        priority=priority,
        source=Source.EVAL,
        module=module,
        target_file=file_path,
        description=f"Verification: {test_name} → {status}",
        acceptance_criteria=[f"{test_name} passes"],
        evidence=[
            VerificationEntry(
                method=VerificationMethod.DOCKER_EVAL,
                status=status,
                summary=f"{test_name}: {status}",
            )
        ],
        risk_score=0.7 if status == "failed" else 0.0,
        merge_readiness=merge_state,
        blocking_issues=[f"{test_name} failed"] if status == "failed" else [],
        created_at=now_iso(),
        updated_at=now_iso(),
    )


def generate_summary(cards: List[TaskCard]) -> Dict[str, Any]:
    """Generate aggregate summary from list of task cards."""
    total = len(cards)
    by_type: Dict[str, int] = {}
    by_state: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    block_count = 0

    for card in cards:
        ct = card.card_type.value if hasattr(card.card_type, "value") else str(card.card_type)
        by_type[ct] = by_type.get(ct, 0) + 1

        st = card.state.value if hasattr(card.state, "value") else str(card.state)
        by_state[st] = by_state.get(st, 0) + 1

        pr = card.priority.value if hasattr(card.priority, "value") else str(card.priority)
        by_priority[pr] = by_priority.get(pr, 0) + 1

        if card.merge_readiness in (MergeReadinessState.BLOCK, "block"):
            block_count += 1

    return {
        "total_cards": total,
        "by_type": by_type,
        "by_state": by_state,
        "by_priority": by_priority,
        "blocking_count": block_count,
        "summary_line": (
            f"{total} cards: {by_state.get('pending', 0)} pending, "
            f"{by_state.get('completed', 0)} completed, "
            f"{block_count} blocking"
        ),
    }
