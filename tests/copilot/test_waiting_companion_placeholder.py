"""Tests for Waiting Companion Placeholder.

Verifies:
- Is a pure placeholder — no external service calls
- Can be activated/deactivated without side effects
- JSON serializable
- Markdown renderable
"""

import json

from harness.copilot.view_models import WaitingCompanionViewModel
from harness.copilot.markdown_renderer import render_companion
from harness.copilot.json_renderer import render_dashboard_json
from harness.copilot.view_models import CopilotDashboardState


class TestWaitingCompanionPlaceholder:
    def test_default_state(self):
        wc = WaitingCompanionViewModel()
        assert wc.is_active is False
        assert wc.mode == "idle"
        assert wc.status_text == "等待中"

    def test_activate_changes_state(self):
        wc = WaitingCompanionViewModel()
        wc.activate()
        assert wc.is_active is True
        assert wc.mode == "waiting"
        assert wc.status_text == "等待 Agent 执行中"

    def test_activate_sets_timestamp(self):
        wc = WaitingCompanionViewModel()
        wc.activate()
        assert wc.waiting_since != ""

    def test_deactivate_resets_state(self):
        wc = WaitingCompanionViewModel()
        wc.activate()
        wc.deactivate()
        assert wc.is_active is False
        assert wc.mode == "idle"
        assert wc.status_text == "待命"

    def test_multiple_activate_deactivate_cycles(self):
        wc = WaitingCompanionViewModel()
        for _ in range(3):
            wc.activate()
            assert wc.is_active is True
            wc.deactivate()
            assert wc.is_active is False

    def test_no_external_music_service(self):
        """Must not reference any external music platform."""
        wc = WaitingCompanionViewModel()
        wc.activate()
        # No attributes like spotify, apple_music, playlist, etc.
        attrs = dir(wc)
        music_keywords = ["spotify", "apple", "playlist", "soundcloud", "music_service", "api_key"]
        for kw in music_keywords:
            assert not any(kw in a.lower() for a in attrs), f"Found music service ref: {kw}"

    def test_no_audio_playback(self):
        """Must not have any playback capability."""
        wc = WaitingCompanionViewModel()
        playback_attrs = ["play", "stop", "pause", "volume", "audio", "sound"]
        for attr in playback_attrs:
            assert not hasattr(wc, attr), f"Found playback attr: {attr}"

    def test_to_dict(self):
        wc = WaitingCompanionViewModel()
        d = wc.to_dict()
        assert d["is_active"] is False
        assert d["mode"] == "idle"

    def test_to_dict_after_activation(self):
        wc = WaitingCompanionViewModel()
        wc.activate()
        d = wc.to_dict()
        assert d["is_active"] is True
        assert d["mode"] == "waiting"

    def test_json_serializable(self):
        wc = WaitingCompanionViewModel()
        d = wc.to_dict()
        json.dumps(d)  # No error

    def test_in_dashboard_state(self):
        """Companion can be embedded in dashboard."""
        state = CopilotDashboardState(
            project_name="test",
            companion=WaitingCompanionViewModel(),
        )
        d = state.to_dict()
        assert d["companion"]["is_active"] is False

    def test_activated_in_dashboard(self):
        state = CopilotDashboardState(project_name="test")
        wc = WaitingCompanionViewModel()
        wc.activate()
        state.companion = wc
        d = state.to_dict()
        assert d["companion"]["is_active"] is True

    def test_markdown_renderer_no_external_refs(self):
        """Markdown output must mention no external service."""
        wc = WaitingCompanionViewModel()
        wc.activate()
        output = render_companion(wc)
        # Should explicitly state music service is not connected
        assert "音乐服务未接入" in output

    def test_markdown_inactive(self):
        wc = WaitingCompanionViewModel()
        output = render_companion(wc)
        assert "待命" in output or "等待陪伴" in output

    def test_not_a_music_player(self):
        """The name and purpose must not imply music player."""
        assert WaitingCompanionViewModel.__name__ != "MusicPlayer"
        assert WaitingCompanionViewModel.__name__ != "AudioService"
