"""Tests for HTML rendering — verify all ViewModel types render correctly."""

from __future__ import annotations

import pytest

from harness.copilot.shell.html_renderer import (
    render_html_dashboard,
    render_loop_html_dashboard,
)
from harness.copilot.shell.static_assets import DASHBOARD_CSS


class TestStaticAssets:
    def test_css_is_non_empty(self):
        assert len(DASHBOARD_CSS) > 500
        assert ":root" in DASHBOARD_CSS
        assert "body" in DASHBOARD_CSS

    def test_css_contains_critical_selectors(self):
        required = [".header", ".section", ".tab-btn", ".task-card", ".readiness-card"]
        for sel in required:
            assert sel in DASHBOARD_CSS, f"Missing CSS selector: {sel}"


class TestHtmlRenderer:
    def test_empty_dashboard_renders(self):
        """Minimal dashboard should render without errors."""
        state = {
            "project_name": "Test",
            "project_root": "/tmp/test",
            "branch": "main",
            "overall_risk_level": "low",
            "agent_phase_label": "待命",
            "uncommitted_changes": 0,
            "module_count": 0,
            "generated_at": "2026-06-22T00:00:00",
            "modules": [],
            "recent_changes": [],
            "suggestions": None,
            "task_cards": None,
            "readiness": None,
            "evidence": None,
            "companion": None,
        }
        html = render_html_dashboard(state)
        assert "<!DOCTYPE html>" in html
        assert "Test" in html
        assert "</html>" in html
        assert "DASHBOARD_CSS" not in html  # Should be inlined
        assert len(html) > 200

    def test_full_dashboard_renders(self):
        """Dashboard with all sections should render completely."""
        state = {
            "project_name": "FullTest",
            "project_root": "/tmp/full",
            "branch": "feature/test",
            "overall_risk_level": "medium",
            "risk_color": "yellow",
            "agent_phase": "idle",
            "agent_phase_label": "待命",
            "uncommitted_changes": 3,
            "module_count": 2,
            "generated_at": "2026-06-22T12:00:00",
            "modules": [
                {
                    "name": "core",
                    "file_count": 15,
                    "risk_level": "low",
                    "risk_color": "green",
                    "risk_score": 0.2,
                    "risk_description": "✅ 低风险 — core 模块变更安全。",
                    "dependencies": [],
                    "dependents": ["api"],
                    "high_risk_files": [],
                    "primary_language": "Python",
                },
                {
                    "name": "api",
                    "file_count": 8,
                    "risk_level": "high",
                    "risk_color": "red",
                    "risk_score": 0.7,
                    "risk_description": "⚠️ 高风险 — api 模块包含敏感文件或大范围变更，建议重点审查。",
                    "dependencies": ["core"],
                    "dependents": [],
                    "high_risk_files": [
                        {"path": "api/auth.py", "score": 0.85, "reasons": ["认证逻辑"]},
                    ],
                    "primary_language": "Python",
                },
            ],
            "recent_changes": [
                {
                    "module": "core",
                    "summary": "Add new database models",
                    "intent": "功能实现",
                    "files_changed": ["core/models.py", "core/db.py"],
                    "lines_changed_str": "+150/-20",
                    "has_risks": False,
                    "risk_warnings": [],
                },
            ],
            "suggestions": {
                "suggestions": [
                    {
                        "suggestion": "Add unit tests for new models",
                        "reason": "New models lack test coverage",
                        "priority_label": "🟡 中优先级",
                        "confidence_label": "85%",
                        "file_path": "core/models.py",
                    },
                ],
            },
            "task_cards": {
                "cards": [
                    {
                        "title": "测试修复 — django-11848",
                        "card_type": "fix_test",
                        "state": "pending",
                        "priority_label": "🟠 高优先级",
                        "module": "django",
                        "target_file": "django/db/models/deletion.py",
                        "description": "测试通过率: 42/45，失败测试: 3 个",
                        "is_blocking": True,
                        "risk_label": "🔴 极高风险",
                    },
                    {
                        "title": "Review fix for EOF handling",
                        "card_type": "fix_review",
                        "state": "pending",
                        "priority_label": "🔴 紧急",
                        "module": "sphinx",
                        "target_file": "sphinx/domains/c.py",
                        "description": "Codex 审查拒绝: 输入结束时无限循环",
                        "is_blocking": True,
                        "risk_label": "🔴 极高风险",
                    },
                ],
            },
            "readiness": {
                "state": "block",
                "state_label": "禁止合并 🔴",
                "state_icon": "🔴",
                "summary": "存在 2 个 blocking issues",
                "blocking_issues": [
                    "测试失败: django-11848 (42/45)",
                    "Codex review 拒绝: sphinx-7590",
                ],
                "is_blocked": True,
                "is_ready": False,
                "review_required": True,
                "pending_cards": 2,
                "high_risk_count": 1,
            },
            "evidence": {
                "pack_id": "ep_20260622_001",
                "total": 4,
                "passed": 2,
                "failed": 2,
                "integrity_hash": "abc123def456",
            },
            "companion": {
                "is_active": False,
                "mode": "idle",
                "status_text": "等待中",
                "waiting_since": "",
            },
        }
        html = render_html_dashboard(state)
        assert "<!DOCTYPE html>" in html
        assert "FullTest" in html
        assert "禁止合并" in html
        assert "fix_test" in html
        assert "fix_review" in html
        assert "测试修复" in html
        assert "等待陪伴" in html
        assert "django-11848" in html
        assert "sphinx-7590" in html

        # Verify read-only footer
        assert "无外部服务" in html
        assert "无自动修改" in html
        assert "仅供查看" in html

    def test_json_data_embedded(self):
        """JSON data should be embedded in script tag."""
        state = {
            "project_name": "JSON Test",
            "project_root": "/tmp/j",
            "branch": "main",
            "overall_risk_level": "low",
            "agent_phase_label": "待命",
            "uncommitted_changes": 0,
            "module_count": 0,
            "generated_at": "now",
            "modules": [],
            "recent_changes": [],
        }
        html = render_html_dashboard(state)
        assert 'id="dashboard-data"' in html
        assert "application/json" in html

    def test_loop_dashboard_includes_loop_detail(self):
        """Loop dashboard should have loop-detail tab."""
        state = {
            "project_name": "Loop",
            "project_root": "/tmp/l",
            "branch": "main",
            "overall_risk_level": "low",
            "agent_phase_label": "待命",
            "uncommitted_changes": 0,
            "module_count": 0,
            "generated_at": "now",
            "modules": [],
            "recent_changes": [],
        }

        class MockArtifacts:
            run_dir = "/tmp/loop-run"
            load_errors = []
            metrics = {"tests": 45, "passed": 43}

            def to_dict(self):
                return {
                    "metrics": self.metrics,
                    "eval_report": {},
                    "test_result": {},
                }

        html = render_loop_html_dashboard(state, loop_artifacts=MockArtifacts())
        assert "<!DOCTYPE html>" in html
        assert "Loop详情" in html
        assert "/tmp/loop-run" in html


class TestHtmlStructure:
    def test_html_starts_with_doctype(self):
        state = {"project_name": "T", "branch": "m", "overall_risk_level": "low",
                 "agent_phase_label": "x", "uncommitted_changes": 0, "module_count": 0,
                 "generated_at": "n", "project_root": "", "modules": [], "recent_changes": []}
        html = render_html_dashboard(state)
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_html_has_tab_navigation(self):
        state = {"project_name": "Tabs", "branch": "m", "overall_risk_level": "low",
                 "agent_phase_label": "x", "uncommitted_changes": 0, "module_count": 1,
                 "generated_at": "n", "project_root": "",
                 "modules": [{"name": "m1", "file_count": 1, "risk_level": "low", "risk_color": "green",
                              "risk_score": 0, "risk_description": "safe", "dependencies": [], "dependents": [],
                              "high_risk_files": [], "primary_language": "Py"}],
                 "recent_changes": []}
        html = render_html_dashboard(state)
        assert 'data-tab="overview"' in html
        assert 'data-tab="modules"' in html
