"""Watcher — poll-based project monitor with snapshot diff and event classification.

Runs a monitoring loop that captures snapshots, detects changes, classifies events,
and outputs to terminal (and optionally refreshes HTML dashboard).
Read-only: no file writes except to --out dashboard directory.
"""

from __future__ import annotations

import time
import sys
from typing import Any, Callable, Dict, List, Optional

from . import MonitorEvent, MonitorSession, EventType, Severity
from .snapshot import (
    ProjectSnapshot,
    capture_project_snapshot,
    capture_loop_snapshot,
    snapshot_diff,
)


EventCallback = Callable[[MonitorEvent], None]


class ProjectWatcher:
    """Poll-based project monitor.

    Captures snapshots at intervals, diff against previous, generates events.
    Supports terminal output and optional dashboard refresh callback.
    """

    def __init__(
        self,
        project_root: str,
        interval: float = 3.0,
        on_event: Optional[EventCallback] = None,
    ):
        self.project_root = project_root
        self.interval = interval
        self.on_event = on_event or _null_callback
        self.session = MonitorSession()
        self._previous_snapshot: Optional[ProjectSnapshot] = None
        self._running = False

    def poll_once(self) -> List[MonitorEvent]:
        """Capture one snapshot, diff against previous, return new events."""
        snap = capture_project_snapshot(self.project_root)
        events: List[MonitorEvent] = []

        if self._previous_snapshot is None:
            # First snapshot: no diff, just store
            self._previous_snapshot = snap
            return events

        diffs = snapshot_diff(self._previous_snapshot, snap)

        # Generate events from diffs
        events.extend(_diff_to_events(diffs, self.project_root))

        # Update previous
        self._previous_snapshot = snap

        # Record events in session
        for evt in events:
            self.session.add_event(evt)
            self.on_event(evt)

        return events

    def run(self, max_polls: Optional[int] = None) -> None:
        """Run the monitoring loop.

        Args:
            max_polls: If set, stop after this many polls (for testing).
        """
        self._running = True
        polls = 0

        try:
            while self._running:
                events = self.poll_once()
                polls += 1

                if max_polls is not None and polls >= max_polls:
                    break

                if events:
                    pass  # Callback already fired per-event

                time.sleep(self.interval)

        except KeyboardInterrupt:
            self._running = False

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False


class LoopWatcher:
    """Poll-based loop artifact monitor.

    Watches a loop run directory for artifact changes.
    """

    def __init__(
        self,
        loop_run_dir: str,
        interval: float = 3.0,
        on_event: Optional[EventCallback] = None,
    ):
        self.loop_run_dir = loop_run_dir
        self.interval = interval
        self.on_event = on_event or _null_callback
        self.session = MonitorSession()
        self._previous_snapshot: Optional[ProjectSnapshot] = None
        self._running = False

    def poll_once(self) -> List[MonitorEvent]:
        """Capture one snapshot, diff against previous, return new events."""
        snap = capture_loop_snapshot(self.loop_run_dir)
        events: List[MonitorEvent] = []

        if self._previous_snapshot is None:
            self._previous_snapshot = snap
            return events

        diffs = snapshot_diff(self._previous_snapshot, snap)
        events.extend(_loop_diff_to_events(diffs, self.loop_run_dir))

        self._previous_snapshot = snap

        for evt in events:
            self.session.add_event(evt)
            self.on_event(evt)

        return events

    def run(self, max_polls: Optional[int] = None) -> None:
        """Run the monitoring loop."""
        self._running = True
        polls = 0

        try:
            while self._running:
                events = self.poll_once()
                polls += 1

                if max_polls is not None and polls >= max_polls:
                    break

                if events:
                    pass

                time.sleep(self.interval)

        except KeyboardInterrupt:
            self._running = False

    def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False


def _null_callback(event: MonitorEvent) -> None:
    """Default no-op callback."""


def _diff_to_events(diffs: Dict[str, Any], source: str) -> List[MonitorEvent]:
    """Convert snapshot diffs to monitor events."""
    events: List[MonitorEvent] = []

    if "git_status_changed" in diffs:
        sc = diffs["git_status_changed"]
        added = sc.get("added", [])
        removed = sc.get("removed", [])
        total_change = len(added) + len(removed)
        severity = Severity.MEDIUM.value if total_change > 0 else Severity.LOW.value

        affected = []
        for line in added + removed:
            parts = line.split()
            if len(parts) >= 2:
                affected.append(parts[-1])

        events.append(MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=severity,
            summary=f"检测到 {sc['new_count']} 个未提交文件 (上次: {sc['old_count']})",
            description=f"新增 {len(added)} 个变更，移除 {len(removed)} 个变更",
            affected_modules=affected[:10],
            source_path=source,
            old_value=sc["old_count"],
            new_value=sc["new_count"],
        ))

    if "changed_files" in diffs:
        cf = diffs["changed_files"]
        events.append(MonitorEvent.create(
            event_type=EventType.FILE_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary=f"{len(cf)} 个文件内容发生变化",
            description=f"文件: {', '.join(list(cf.keys())[:5])}",
            affected_modules=list(cf.keys())[:10],
            source_path=source,
        ))

    if "module_risk_changed" in diffs:
        rc = diffs["module_risk_changed"]
        # Check if any risk increased
        increased = {m: v for m, v in rc.items() if v.get("new", 0) > v.get("old", 0)}
        severity = Severity.HIGH.value if increased else Severity.LOW.value
        events.append(MonitorEvent.create(
            event_type=EventType.MODULE_RISK_CHANGED.value,
            severity=severity,
            summary=f"{len(rc)} 个模块风险评分变化",
            description=f"升高: {', '.join(increased.keys())}" if increased else "风险降低",
            affected_modules=list(rc.keys()),
            source_path=source,
        ))

    if "merge_readiness_changed" in diffs:
        mc = diffs["merge_readiness_changed"]
        is_block = mc.get("new") == "block"
        severity = Severity.CRITICAL.value if is_block else Severity.MEDIUM.value
        events.append(MonitorEvent.create(
            event_type=EventType.MERGE_READINESS_CHANGED.value,
            severity=severity,
            summary=f"合并状态变更: {mc['old']} → {mc['new']}",
            description="阻塞合并" if is_block else "状态更新",
            source_path=source,
            old_value=mc["old"],
            new_value=mc["new"],
        ))

    if "task_cards_changed" in diffs:
        tc = diffs["task_cards_changed"]
        new_blocking = tc.get("new_blocking", 0)
        severity = Severity.HIGH.value if new_blocking > 0 else Severity.LOW.value
        events.append(MonitorEvent.create(
            event_type=EventType.TASK_CARD_RECOMMENDED.value,
            severity=severity,
            summary=f"任务卡变更: {tc['new_total']} 张 (阻塞: {new_blocking})",
            description=f"新增 {tc['new_total'] - tc['old_total']} 张",
            source_path=source,
            old_value=tc["old_total"],
            new_value=tc["new_total"],
        ))

    return events


def _loop_diff_to_events(diffs: Dict[str, Any], source: str) -> List[MonitorEvent]:
    """Convert loop snapshot diffs to monitor events."""
    events: List[MonitorEvent] = []

    if "file_hash_changed" in diffs or "new_files" in diffs or "changed_files" in diffs:
        # Generic artifact change
        pass

    if "eval_results_presence_changed" in diffs:
        ec = diffs["eval_results_presence_changed"]
        events.append(MonitorEvent.create(
            event_type=EventType.EVAL_REPORT_CHANGED.value,
            severity=Severity.HIGH.value,
            summary=f"Eval 报告: {ec['old']} → {ec['new']}",
            source_path=source,
        ))

    if "test_results_presence_changed" in diffs:
        tc = diffs["test_results_presence_changed"]
        events.append(MonitorEvent.create(
            event_type=EventType.TEST_RESULT_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary=f"测试结果: {tc['old']} → {tc['new']}",
            source_path=source,
        ))

    if "review_results_presence_changed" in diffs:
        rc = diffs["review_results_presence_changed"]
        events.append(MonitorEvent.create(
            event_type=EventType.REVIEW_RESULT_CHANGED.value,
            severity=Severity.HIGH.value,
            summary=f"Codex review: {rc['old']} → {rc['new']}",
            source_path=source,
        ))

    if "final_gate_presence_changed" in diffs:
        fc = diffs["final_gate_presence_changed"]
        events.append(MonitorEvent.create(
            event_type=EventType.FINAL_GATE_CHANGED.value,
            severity=Severity.CRITICAL.value,
            summary=f"Final Gate: {fc['old']} → {fc['new']}",
            source_path=source,
        ))

    if "loop_report_presence_changed" in diffs:
        lc = diffs["loop_report_presence_changed"]
        events.append(MonitorEvent.create(
            event_type=EventType.LOOP_REPORT_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary=f"Loop 报告: {lc['old']} → {lc['new']}",
            source_path=source,
        ))

    return events
