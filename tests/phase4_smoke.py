#!/usr/bin/env python3
"""Phase 4 smoke test - verify all CLI commands work."""

import os
import sys
import json
import tempfile

# Add project to path
REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, REPO_ROOT)


def test_copy_text_renderer():
    """Test copy text renderer can produce exportable task card text."""
    from harness.copilot.shell.copy_text_renderer import (
        render_task_card_copy_text,
        export_task_card_markdown,
        export_all_task_cards_markdown,
    )
    card = {
        "title": "Test Card",
        "card_type": "fix_test",
        "state": "pending",
        "priority_label": "High",
        "module": "test_mod",
        "target_file": "test.py",
        "description": "Test description",
        "is_blocking": True,
        "risk_label": "High",
    }
    copy_text = render_task_card_copy_text(card)
    assert "Test Card" in copy_text
    assert "fix_test" in copy_text
    assert "⛔ 阻塞合并" in copy_text
    assert "验收标准" in copy_text
    assert "全部测试通过" in copy_text
    print("PASS: copy_text_renderer")


def test_export_markdown():
    """Test markdown export produces valid markdown."""
    from harness.copilot.shell.copy_text_renderer import export_task_card_markdown
    card = {
        "title": "Review Fix",
        "card_type": "fix_review",
        "state": "pending",
        "priority_label": "Critical",
        "module": "sphinx",
        "target_file": "c.py",
        "description": "Fix infinite loop",
        "is_blocking": True,
        "risk_label": "High",
    }
    md = export_task_card_markdown(card)
    assert "# 任务卡: Review Fix" in md
    assert "fix_review" in md
    assert "由 Harness Code Copilot 生成" in md
    print("PASS: export_task_card_markdown")


def test_html_renderer():
    """Test HTML renderer produces valid self-contained HTML."""
    from harness.copilot.shell.html_renderer import render_html_dashboard
    state = {
        "project_name": "SmokeTest",
        "project_root": "/tmp",
        "branch": "main",
        "overall_risk_level": "low",
        "agent_phase_label": "待命",
        "uncommitted_changes": 1,
        "module_count": 2,
        "generated_at": "now",
        "modules": [{
            "name": "core", "file_count": 10, "risk_level": "low",
            "risk_color": "green", "risk_score": 0.1,
            "risk_description": "safe", "dependencies": [],
            "dependents": [], "high_risk_files": [],
            "primary_language": "Python",
        }],
        "recent_changes": [{
            "module": "core", "summary": "Fix bug",
            "intent": "Bug修复", "files_changed": ["core/main.py"],
            "lines_changed_str": "+5/-3", "has_risks": False,
            "risk_warnings": [],
        }],
        "task_cards": {"cards": [{
            "title": "Fix Test", "card_type": "fix_test",
            "state": "pending", "priority_label": "High",
            "module": "m", "target_file": "f.py",
            "description": "desc", "is_blocking": True,
            "risk_label": "High",
        }]},
        "readiness": {
            "state": "pass", "state_label": "可以合并 ✅",
            "state_icon": "✅", "summary": "一切正常",
            "blocking_issues": [], "is_blocked": False,
            "is_ready": True, "review_required": False,
            "pending_cards": 0, "high_risk_count": 0,
        },
        "evidence": {
            "pack_id": "ep1", "total": 4, "passed": 4,
            "failed": 0, "integrity_hash": "abc",
        },
        "companion": {
            "is_active": False, "mode": "idle",
            "status_text": "等待中", "waiting_since": "",
        },
    }
    html = render_html_dashboard(state)
    assert "<!DOCTYPE html>" in html
    assert "SmokeTest" in html
    assert "可以合并" in html
    assert "等待陪伴" in html
    assert "无外部服务" in html
    assert "无自动修改" in html
    assert 'id="dashboard-data"' in html
    print("PASS: html_renderer")


def test_loop_html_renderer():
    """Test loop HTML renderer produces valid HTML."""
    from harness.copilot.shell.html_renderer import render_loop_html_dashboard
    state = {"project_name": "LoopTest", "project_root": "/tmp",
             "branch": "tier_C", "overall_risk_level": "medium",
             "agent_phase_label": "执行中", "uncommitted_changes": 0,
             "module_count": 1, "generated_at": "now",
             "modules": [], "recent_changes": []}

    class MockArtifacts:
        run_dir = "/tmp/loop"
        load_errors = []
        metrics = {"tests": 45, "passed": 43}
        def to_dict(self): return {"metrics": self.metrics}

    html = render_loop_html_dashboard(state, loop_artifacts=MockArtifacts())
    assert "<!DOCTYPE html>" in html
    assert "Loop详情" in html or "Loop" in html
    print("PASS: loop_html_renderer")


def test_shell_builder_nonexistent():
    """Test shell builder handles errors gracefully."""
    from harness.copilot.shell.shell_builder import build_project_shell
    result = build_project_shell("/nonexistent/path", "/tmp/out")
    assert not result.get("success")
    assert "error" in result
    print("PASS: shell_builder error handling")


def test_loop_shell_builder_nonexistent():
    """Test loop shell builder handles errors gracefully."""
    from harness.copilot.shell.loop_shell_builder import build_loop_shell
    result = build_loop_shell("/nonexistent/loop", "/tmp/out")
    assert not result.get("success")
    assert "error" in result
    print("PASS: loop_shell_builder error handling")


def test_cli_commands_exist():
    """Test all Phase 4 CLI commands are registered."""
    from harness.copilot.cli import (
        cmd_shell, cmd_shell_from_loop,
        cmd_export_task_card, cmd_preview,
    )
    assert callable(cmd_shell)
    assert callable(cmd_shell_from_loop)
    assert callable(cmd_export_task_card)
    assert callable(cmd_preview)
    print("PASS: CLI commands registered")


def test_static_assets():
    """Test CSS assets are non-empty and contain critical styles."""
    from harness.copilot.shell.static_assets import DASHBOARD_CSS
    assert len(DASHBOARD_CSS) > 1000
    assert ".tab-btn" in DASHBOARD_CSS
    assert ".task-card" in DASHBOARD_CSS
    assert ".readiness-card" in DASHBOARD_CSS
    assert ".companion-placeholder" in DASHBOARD_CSS
    print("PASS: static_assets")


def test_preview_server_exists():
    """Test preview server module can be imported."""
    from harness.copilot.shell.preview_server import serve_preview
    assert callable(serve_preview)
    print("PASS: preview_server import")


def test_export_all_cards():
    """Test exporting all cards at once."""
    from harness.copilot.shell.copy_text_renderer import export_all_task_cards_markdown
    cards = [
        {"title": "A", "card_type": "fix_test", "state": "p", "priority_label": "H",
         "module": "m", "target_file": "f", "description": "d", "is_blocking": True,
         "risk_label": "H"},
        {"title": "B", "card_type": "fix_review", "state": "p", "priority_label": "C",
         "module": "m", "target_file": "f", "description": "d", "is_blocking": True,
         "risk_label": "H"},
    ]
    md = export_all_task_cards_markdown(cards)
    assert "# 任务卡列表" in md
    assert "## 1." in md
    assert "## 2." in md
    assert "由 Harness Code Copilot 生成" in md
    print("PASS: export_all_task_cards_markdown")


if __name__ == "__main__":
    tests = [
        test_copy_text_renderer,
        test_export_markdown,
        test_html_renderer,
        test_loop_html_renderer,
        test_shell_builder_nonexistent,
        test_loop_shell_builder_nonexistent,
        test_cli_commands_exist,
        test_static_assets,
        test_preview_server_exists,
        test_export_all_cards,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{'='*40}")
    print(f"Phase 4 Smoke: {passed} passed, {failed} failed, {len(tests)} total")
    if failed > 0:
        sys.exit(1)
