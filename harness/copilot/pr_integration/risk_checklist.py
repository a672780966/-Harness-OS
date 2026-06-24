"""Risk Checklist — generate structured risk checklist from project analysis.

Checks for common risk categories:
- Database / migration risk
- Auth / permission risk
- Destructive / deletion risk
- Test coverage gaps
- External service / API call risk
- Configuration / secret risk
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..schemas import RiskLevel, RiskAlert


RISK_CHECKLIST_TEMPLATE = [
    {
        "id": "db_migration",
        "label": "数据库/迁移",
        "description": "检查是否包含数据库 schema 变更、数据迁移或 SQL 修改",
        "icon": "🗄️",
    },
    {
        "id": "auth_permission",
        "label": "权限/认证",
        "description": "检查是否涉及认证逻辑、权限控制、角色或 CORS 变更",
        "icon": "🔐",
    },
    {
        "id": "destructive_change",
        "label": "删除/破坏性修改",
        "description": "检查是否存在文件删除、API 签名变更或破坏性重构",
        "icon": "⚠️",
    },
    {
        "id": "test_coverage_gap",
        "label": "测试覆盖缺口",
        "description": "检查变更是否缺少对应测试覆盖",
        "icon": "🧪",
    },
    {
        "id": "external_service",
        "label": "外部服务/API",
        "description": "检查是否引入新的外部服务调用或 API 依赖",
        "icon": "🌐",
    },
    {
        "id": "config_secret",
        "label": "配置/密钥",
        "description": "检查是否修改了配置文件、环境变量或硬编码密钥",
        "icon": "🔑",
    },
    {
        "id": "new_dependency",
        "label": "新增依赖",
        "description": "检查是否新增了第三方依赖或包引用",
        "icon": "📦",
    },
]


def build_risk_checklist(
    risk_alerts: Optional[List[RiskAlert]] = None,
    changed_files: Optional[List[str]] = None,
    high_risk_modules: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Build a checked/unchecked risk checklist from analysis data.

    Args:
        risk_alerts: Existing risk alerts from RiskClassifier.
        changed_files: List of file paths changed.
        high_risk_modules: List of high-risk module names.

    Returns:
        List of checklist items with checked/unchecked status.
    """
    checklist: List[Dict[str, Any]] = []

    # Collect risk text from alerts
    alert_texts: List[str] = []
    if risk_alerts:
        for ra in risk_alerts:
            title = ra.title if hasattr(ra, "title") else str(ra)
            level = ra.level.value if hasattr(ra.level, "value") else str(getattr(ra, "level", ""))
            alert_texts.append(f"{title} ({level})")

    # Collect file paths for keyword matching
    file_text = " ".join(changed_files or [])
    module_text = " ".join(high_risk_modules or [])

    for item in RISK_CHECKLIST_TEMPLATE:
        checked = _check_risk(item["id"], alert_texts, file_text, module_text, risk_alerts)
        checklist.append({
            "id": item["id"],
            "label": item["label"],
            "description": item["description"],
            "icon": item["icon"],
            "checked": checked,
            "matched": _check_risk_detail(item["id"], alert_texts, file_text, module_text, risk_alerts),
        })

    return checklist


def _check_risk(
    risk_id: str,
    alert_texts: List[str],
    file_text: str,
    module_text: str,
    risk_alerts: Optional[List[RiskAlert]] = None,
) -> bool:
    """Check if a risk category is relevant."""
    keywords = _risk_keywords(risk_id)
    combined = " ".join(alert_texts) + " " + file_text + " " + module_text
    for kw in keywords:
        if kw.lower() in combined.lower():
            return True

    # Check alert levels for high/critical
    if risk_alerts:
        for ra in risk_alerts:
            level = ra.level.value if hasattr(ra.level, "value") else ""
            if level in ("critical", "high"):
                if risk_id in ("destructive_change", "test_coverage_gap"):
                    return True

    return False


def _check_risk_detail(
    risk_id: str,
    alert_texts: List[str],
    file_text: str,
    module_text: str,
    risk_alerts: Optional[List[RiskAlert]] = None,
) -> str:
    """Return a detail string explaining why a risk was flagged."""
    matches: List[str] = []
    keywords = _risk_keywords(risk_id)
    for kw in keywords:
        if kw.lower() in file_text.lower():
            matches.append(kw)

    if risk_alerts:
        for ra in risk_alerts:
            title = ra.title if hasattr(ra, "title") else str(ra)
            combined = " ".join(alert_texts)
            for kw in keywords:
                if kw.lower() in combined.lower():
                    if title not in matches:
                        matches.append(title)

    return "; ".join(matches[:3]) if matches else ""


def _risk_keywords(risk_id: str) -> List[str]:
    """Get keywords for a risk category."""
    keyword_map = {
        "db_migration": ["database", "migration", "sql", "schema", "db_", "alembic"],
        "auth_permission": ["auth", "login", "password", "token", "oauth", "permission", "rbac", "cors", "csrf", "session"],
        "destructive_change": ["delete", "remove", "deprecat", "breaking", "rename", "refactor"],
        "test_coverage_gap": ["test", "spec", "unittest", "pytest", "coverage"],
        "external_service": ["api", "http", "webhook", "callback", "client", "request"],
        "config_secret": ["config", ".env", "secret", "credential", "key", "cert", "pem"],
        "new_dependency": ["package.json", "requirements", "pyproject", "gemfile", "cargo"],
    }
    return keyword_map.get(risk_id, [])


def render_checklist_markdown(checklist: List[Dict[str, Any]]) -> str:
    """Render risk checklist as markdown."""
    lines = ["## Risk Checklist", ""]
    for item in checklist:
        checkbox = "[x]" if item["checked"] else "[ ]"
        icon = item["icon"]
        label = item["label"]
        detail = item.get("matched", "")
        if detail:
            lines.append(f"- {icon} {checkbox} **{label}** — {detail}")
        else:
            lines.append(f"- {icon} {checkbox} {label}")
    lines.append("")
    return "\n".join(lines)


def render_checklist_json(checklist: List[Dict[str, Any]]) -> str:
    """Render risk checklist as JSON."""
    import json
    return json.dumps({"risk_checklist": checklist}, indent=2, ensure_ascii=False)
