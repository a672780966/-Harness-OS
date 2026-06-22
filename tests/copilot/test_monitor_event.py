"""Tests for monitor event schema."""

from harness.copilot.monitor import MonitorEvent, MonitorSession, EventType, Severity


class TestMonitorEventSchema:
    def test_create_minimal(self):
        evt = MonitorEvent.create(
            event_type=EventType.PROJECT_DIFF_CHANGED.value,
            severity=Severity.LOW.value,
            summary="Minimal event",
        )
        assert evt.event_id.startswith("evt-")
        assert evt.event_type == "project_diff_changed"
        assert evt.timestamp
        assert evt.severity == "low"
        assert evt.summary == "Minimal event"
        assert evt.readonly is True
        assert evt.affected_modules == []
        assert evt.source_path == ""

    def test_create_full(self):
        evt = MonitorEvent.create(
            event_type=EventType.FINAL_GATE_CHANGED.value,
            severity=Severity.CRITICAL.value,
            summary="Gate blocked",
            description="Final gate result changed to blocked",
            affected_modules=["core", "api"],
            recommended_action="审查并修复问题",
            source_path="/tmp/project",
            old_value="pass",
            new_value="block",
        )
        assert evt.event_type == "final_gate_changed"
        assert evt.severity == "critical"
        assert evt.affected_modules == ["core", "api"]
        assert evt.recommended_action == "审查并修复问题"
        assert evt.source_path == "/tmp/project"

    def test_to_dict(self):
        evt = MonitorEvent.create(
            event_type=EventType.TEST_RESULT_CHANGED.value,
            severity=Severity.MEDIUM.value,
            summary="Tests updated",
        )
        d = evt.to_dict()
        assert d["event_type"] == "test_result_changed"
        assert d["severity"] == "medium"
        assert d["readonly"] is True
        assert "event_id" in d
        assert "timestamp" in d
        assert "summary" in d

    def test_severity_values(self):
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"

    def test_event_type_values(self):
        types = [e.value for e in EventType]
        assert "project_diff_changed" in types
        assert "module_risk_changed" in types
        assert "test_result_changed" in types
        assert "eval_report_changed" in types
        assert "review_result_changed" in types
        assert "final_gate_changed" in types
        assert "loop_report_changed" in types
        assert "merge_readiness_changed" in types
        assert "task_card_recommended" in types
        assert "waiting_companion_notice" in types
        assert "file_changed" in types
        assert "agent_status_changed" in types


class TestMonitorSession:
    def test_empty_session(self):
        s = MonitorSession()
        assert s.events == []
        assert s.summary_text() == "共 0 个事件"

    def test_add_event(self):
        s = MonitorSession()
        evt = MonitorEvent.create(
            event_type=EventType.FILE_CHANGED.value,
            severity=Severity.LOW.value,
            summary="file changed",
        )
        s.add_event(evt)
        assert len(s.events) == 1
        assert s.accumulated_summary.get("file_changed") == 1

    def test_latest_events(self):
        s = MonitorSession()
        for i in range(15):
            evt = MonitorEvent.create(
                event_type=EventType.FILE_CHANGED.value,
                severity=Severity.LOW.value,
                summary=f"event {i}",
            )
            s.add_event(evt)
        latest = s.latest_events(5)
        assert len(latest) == 5
        assert "event 14" in latest[-1].summary

    def test_summary_text(self):
        s = MonitorSession()
        s.add_event(MonitorEvent.create(
            event_type=EventType.FILE_CHANGED.value, severity=Severity.LOW.value, summary="a",
        ))
        s.add_event(MonitorEvent.create(
            event_type=EventType.FILE_CHANGED.value, severity=Severity.LOW.value, summary="b",
        ))
        s.add_event(MonitorEvent.create(
            event_type=EventType.MERGE_READINESS_CHANGED.value, severity=Severity.HIGH.value, summary="c",
        ))
        summary = s.summary_text()
        assert "共 3 个事件" in summary
        assert "file_changed: 2" in summary
        assert "merge_readiness_changed: 1" in summary
