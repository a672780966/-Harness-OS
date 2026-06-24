"""Config validator — validate configuration for safety, completeness, and security.

Returns structured warnings for security-sensitive settings.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .paths import resolve_effective_paths
from .resolver import resolve_config
from .schema import HarnessConfig, SECURITY_SENSITIVE_KEYS


def validate_config(
    config: Optional[HarnessConfig] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate a HarnessConfig, returning issues found.

    Args:
        config: Config to validate. If None, resolves from project_root.
        project_root: Project root (used if config is None).

    Returns:
        dict with keys:
            valid: bool — True if no errors
            errors: list of error strings (blocking)
            warnings: list of warning strings (non-blocking)
            info: list of info strings
            security_issues: list of security-sensitive setting warnings
    """
    if config is None:
        config = resolve_config(project_root=project_root)

    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []
    security_issues: List[str] = []

    # Schema version
    if not isinstance(config.version, int) or config.version < 1:
        errors.append(f"Invalid schema version: {config.version}")

    # Runtime mode validation
    if config.runtime.mode not in ("local", "remote"):
        warnings.append(f"Unknown runtime mode: '{config.runtime.mode}'. Expected 'local' or 'remote'.")

    # Provider mode validation
    valid_provider_modes = ("readonly", "primary", "fallback")
    if config.provider.mode not in valid_provider_modes:
        warnings.append(
            f"Unknown provider mode: '{config.provider.mode}'. "
            f"Expected one of {valid_provider_modes}."
        )

    # Provider timeout sanity
    if config.provider.canary_timeout_seconds < 5:
        warnings.append(
            f"Provider canary timeout ({config.provider.canary_timeout_seconds}s) "
            f"is very low. Recommended minimum: 10s."
        )
    if config.provider.canary_timeout_seconds > 300:
        warnings.append(
            f"Provider canary timeout ({config.provider.canary_timeout_seconds}s) "
            f"is very high. Recommended maximum: 120s."
        )

    # Security checks
    if config.security.save_credentials:
        security_issues.append(
            f"SECURITY: {SECURITY_SENSITIVE_KEYS.get('save_credentials', 'save_credentials enabled')}"
        )
    if config.security.allow_agent_control:
        security_issues.append(
            f"SECURITY: {SECURITY_SENSITIVE_KEYS.get('allow_agent_control', 'allow_agent_control enabled')}"
        )
    if config.runtime.allow_external_api:
        security_issues.append(
            f"SECURITY: {SECURITY_SENSITIVE_KEYS.get('allow_external_api', 'allow_external_api enabled')}"
        )
    if config.provider.long_phase_allowed_when_degraded:
        security_issues.append(
            f"WARNING: {SECURITY_SENSITIVE_KEYS.get('long_phase_allowed_when_degraded', 'long phase while degraded')}"
        )

    # Copilot format
    if config.copilot.default_format not in ("markdown", "json"):
        warnings.append(
            f"Unknown copilot format: '{config.copilot.default_format}'. "
            f"Expected 'markdown' or 'json'."
        )

    # Path checks
    paths = resolve_effective_paths(project_root)
    info.append(f"Global config: {paths['global_config_path']} " +
                ("(exists)" if paths['global_config_exists'] else "(not found)"))
    info.append(f"Project config: {paths['project_config_path']} " +
                ("(exists)" if paths['project_config_exists'] else "(not found)"))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "security_issues": security_issues,
    }
