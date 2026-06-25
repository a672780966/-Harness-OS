"""Config schema — YAML-backed structured configuration for Harness Copilot.

Schema versioning ensures backward compatibility.
All security-sensitive fields default to OFF.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional


# Current schema version
SCHEMA_VERSION: int = 1


@dataclass
class ProviderConfig:
    """Provider / model configuration section.

    Tunables map to the ProviderGuardConfig in
    harness/copilot/provider_guard/config.py.  The schema is the
    single source of truth; ProviderGuardConfig provides env-var
    overrides for runtime-only use.
    """

    mode: str = "readonly"  # readonly | primary | fallback
    primary: str = "opencode-go/deepseek-v4-flash"
    fallback: str = "opencode/deepseek-v4-flash-free"

    # Timeouts (seconds)
    connect_timeout_seconds: float = 10.0
    read_timeout_seconds: float = 90.0
    canary_timeout_seconds: float = 45.0

    # Retry policy
    max_retries: int = 3
    retry_backoff: str = "exponential"  # exponential | linear | constant
    retry_jitter: bool = True

    # Degradation policy
    long_phase_allowed_when_degraded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "primary": self.primary,
            "fallback": self.fallback,
            "connect_timeout_seconds": self.connect_timeout_seconds,
            "read_timeout_seconds": self.read_timeout_seconds,
            "canary_timeout_seconds": self.canary_timeout_seconds,
            "max_retries": self.max_retries,
            "retry_backoff": self.retry_backoff,
            "retry_jitter": self.retry_jitter,
            "long_phase_allowed_when_degraded": self.long_phase_allowed_when_degraded,
        }


@dataclass
class WorkspaceConfig:
    """Workspace / file paths section."""

    root: str = "~/harness-workspace"
    dogfood_root: str = "~/dogfood"
    demo_output_root: str = ".harness/copilot_demo"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root": self.root,
            "dogfood_root": self.dogfood_root,
            "demo_output_root": self.demo_output_root,
        }


@dataclass
class RuntimeConfig:
    """Runtime behaviour section."""

    mode: str = "local"  # local | remote
    os_hint: str = ""    # auto-detected if empty
    readonly_default: bool = True
    allow_external_api: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "os_hint": self.os_hint,
            "readonly_default": self.readonly_default,
            "allow_external_api": self.allow_external_api,
        }


@dataclass
class CopilotConfig:
    """Copilot feature toggles section."""

    default_format: str = "markdown"
    include_live_dashboard: bool = True
    include_pr_pack: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "default_format": self.default_format,
            "include_live_dashboard": self.include_live_dashboard,
            "include_pr_pack": self.include_pr_pack,
        }


@dataclass
class SecurityConfig:
    """Security / safety section.

    WARNING: Changing these defaults is strongly discouraged.
    Only allow_agent_control should ever be set to True in controlled
    automation environments.
    """

    save_credentials: bool = False
    allow_agent_control: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "save_credentials": self.save_credentials,
            "allow_agent_control": self.allow_agent_control,
        }


@dataclass
class HarnessConfig:
    """Top-level Harness configuration envelope.

    Always has a version field for forward compatibility.
    """

    version: int = SCHEMA_VERSION
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    copilot: CopilotConfig = field(default_factory=CopilotConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)

    @classmethod
    def defaults(cls) -> HarnessConfig:
        """Return the canonical default configuration (built-in)."""
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "workspace": self.workspace.to_dict(),
            "runtime": self.runtime.to_dict(),
            "provider": self.provider.to_dict(),
            "copilot": self.copilot.to_dict(),
            "security": self.security.to_dict(),
        }

    def merge(self, override: HarnessConfig) -> HarnessConfig:
        """Merge another config into this one (override wins)."""
        merged = HarnessConfig.defaults()
        merged.version = max(self.version, override.version)
        merged.workspace = _merge_dataclass(self.workspace, override.workspace)
        merged.runtime = _merge_dataclass(self.runtime, override.runtime)
        merged.provider = _merge_dataclass(self.provider, override.provider)
        merged.copilot = _merge_dataclass(self.copilot, override.copilot)
        merged.security = _merge_dataclass(self.security, override.security)
        return merged


def _merge_dataclass(base: Any, override: Any) -> Any:
    """Merge two dataclass instances of the same type.

    Non-None / non-empty values from override replace base values.
    """
    cls = type(base)
    kwargs = {}
    for f in fields(cls):
        base_val = getattr(base, f.name)
        over_val = getattr(override, f.name)
        # Use override value if it's meaningfully set (not None, not empty string/empty list)
        if over_val is not None and over_val != "" and over_val != []:
            kwargs[f.name] = over_val
        else:
            kwargs[f.name] = base_val
    return cls(**kwargs)


# Security-sensitive keys that trigger validation warnings
SECURITY_SENSITIVE_KEYS: Dict[str, str] = {
    "save_credentials": "Enabling save_credentials stores API tokens on disk.",
    "allow_agent_control": "Enabling allow_agent_control permits automatic code modification.",
    "allow_external_api": "Enabling allow_external_api makes network requests.",
    "long_phase_allowed_when_degraded": "Running long phases while provider is degraded may hang.",
}
