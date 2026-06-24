"""Tests for AgentState renderer."""

from harness.copilot.agent_state import AgentState, AgentStateEnum, AgentStateTimeline
from harness.copilot.agent_state.renderer import (
    render_agent_state, render_timeline, render_short,
)
from harness.copilot.agent_state.timeline import summarize_state


class TestRenderer:
    def test_render_idle(self):
        s = AgentState()
        md = render_agent_state(s, format="markdown")
        assert "待命" in md or "idle" in md
        assert "置信度" in md

    def test_render_implementing(self):
        s = AgentState(
            state=AgentStateEnum.IMPLEMENTING.value,
            confidence=0.8,
            source_events=["project_diff_changed"],
            summary="Agent modifying code",
            recommended_action="wait for completion",
            blocking=False,
        )
        md = render_agent_state(s, format="markdown")
        assert "正在修改代码" in md
        assert "80%" in md
        assert "wait for completion" in md

    def test_render_blocked(self):
        s = AgentState(
            state=AgentStateEnum.BLOCKED.value,
            confidence=0.9,
            blocking=True,
            summary="Blocked by review",
        )
        md = render_agent_state(s, format="markdown")
        assert "阻塞" in md or "blocked" in md
        assert "🚫" in md

    def test_render_completed(self):
        s = AgentState(
            state=AgentStateEnum.COMPLETED.value,
            confidence=0.95,
            blocking=False,
            summary="All done",
        )
        md = render_agent_state(s, format="markdown")
        assert "已完成" in md

    def test_render_json(self):
        s = AgentState(
            state=AgentStateEnum.FAILED.value,
            confidence=0.85,
            blocking=True,
        )
        js = render_agent_state(s, format="json")
        import json
        d = json.loads(js)
        assert d["state"] == "failed"
        assert d["blocking"] is True

    def test_render_timeline_empty(self):
        tl = AgentStateTimeline()
        md = render_timeline(tl)
        assert "无 Agent 状态记录" in md

    def test_render_timeline_with_states(self):
        tl = AgentStateTimeline()
        tl.add(AgentState(state=AgentStateEnum.IMPLEMENTING.value))
        tl.add(AgentState(state=AgentStateEnum.COMPLETED.value))
        md = render_timeline(tl)
        assert "时间线" in md
        assert "正在修改代码" in md or "implementing" in md

    def test_render_short(self):
        s = AgentState(
            state=AgentStateEnum.IMPLEMENTING.value,
            confidence=0.7,
        )
        line = render_short(s, color=False)
        assert "Agent 状态" in line
        assert "正在修改代码" in line

    def test_summarize_state(self):
        s = AgentState(state=AgentStateEnum.IDLE.value)
        assert "待命" in summarize_state(s)

        s = AgentState(state=AgentStateEnum.PLANNING.value, recommended_action="分析依赖")
        text = summarize_state(s)
        assert "规划中" in text
        assert "分析依赖" in text
