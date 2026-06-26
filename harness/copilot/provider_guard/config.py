"""Provider Reliability Guard — configuration and policy.

Defines the timeout, retry, and canary policy for the provider reliability guard.
All values are read-only constants; override via env vars for runtime tuning.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from harness.config.schema import HarnessConfig, ProviderConfig


_PROVIDER_DEFAULTS = ProviderConfig()

@dataclass(frozen=True)
class ProviderGuardConfig:
    """Provider reliability guard configuration.

    All timeouts in seconds. Can be overridden via environment variables:

        HARNESS_PROVIDER_CONNECT_TIMEOUT
        HARNESS_PROVIDER_READ_TIMEOUT
        HARNESS_PROVIDER_MAX_RETRIES
        HARNESS_PROVIDER_CANARY_TIMEOUT
        HARNESS_PROVIDER_CANARY_MAX_TOKENS
        HARNESS_PROVIDER_LONG_PHASE_ALLOWED_WHEN_DEGRADED
    """

    # Connection / read timeouts
    connect_timeout_seconds: float = _PROVIDER_DEFAULTS.connect_timeout_seconds
    read_timeout_seconds: float = _PROVIDER_DEFAULTS.read_timeout_seconds

    # Retry policy
    max_retries: int = _PROVIDER_DEFAULTS.max_retries
    retry_backoff: str = _PROVIDER_DEFAULTS.retry_backoff  # "exponential" | "linear" | "constant"
    retry_jitter: bool = _PROVIDER_DEFAULTS.retry_jitter

    # Canary prompt
    minimal_canary_prompt: str = "OK"
    canary_max_tokens: int = 10
    canary_timeout_seconds: float = _PROVIDER_DEFAULTS.canary_timeout_seconds

    # Degradation policy
    consecutive_failures_to_degrade: int = 2
    health_check_cooldown_seconds: float = 120.0
    long_phase_allowed_when_degraded: bool = _PROVIDER_DEFAULTS.long_phase_allowed_when_degraded

    @classmethod
    def from_env(cls) -> ProviderGuardConfig:
        """Build config with optional env var overrides."""
        return cls.from_provider_config(
            _PROVIDER_DEFAULTS,
            connect_timeout_seconds=float(
                os.environ.get("HARNESS_PROVIDER_CONNECT_TIMEOUT", cls.connect_timeout_seconds)
            ),
            read_timeout_seconds=float(
                os.environ.get("HARNESS_PROVIDER_READ_TIMEOUT", cls.read_timeout_seconds)
            ),
            max_retries=int(
                os.environ.get("HARNESS_PROVIDER_MAX_RETRIES", cls.max_retries)
            ),
            retry_backoff=os.environ.get("HARNESS_PROVIDER_RETRY_BACKOFF", cls.retry_backoff),
            retry_jitter=_parse_bool(
                os.environ.get("HARNESS_PROVIDER_RETRY_JITTER"),
                default=cls.retry_jitter,
            ),
            canary_timeout_seconds=float(
                os.environ.get("HARNESS_PROVIDER_CANARY_TIMEOUT", cls.canary_timeout_seconds)
            ),
            canary_max_tokens=int(
                os.environ.get("HARNESS_PROVIDER_CANARY_MAX_TOKENS", cls.canary_max_tokens)
            ),
            long_phase_allowed_when_degraded=_parse_bool(
                os.environ.get("HARNESS_PROVIDER_LONG_PHASE_ALLOWED_WHEN_DEGRADED"),
                default=cls.long_phase_allowed_when_degraded,
            ),
        )

    @classmethod
    def from_harness_config(cls, config: HarnessConfig) -> ProviderGuardConfig:
        """Build guard config from the canonical HarnessConfig provider section."""
        return cls.from_provider_config(config.provider)

    @classmethod
    def from_provider_config(
        cls,
        provider: ProviderConfig,
        **overrides: Any,
    ) -> ProviderGuardConfig:
        """Build guard config from HarnessConfig.provider with runtime overrides."""
        values = {
            "connect_timeout_seconds": provider.connect_timeout_seconds,
            "read_timeout_seconds": provider.read_timeout_seconds,
            "max_retries": provider.max_retries,
            "retry_backoff": provider.retry_backoff,
            "retry_jitter": provider.retry_jitter,
            "minimal_canary_prompt": cls.minimal_canary_prompt,
            "canary_max_tokens": cls.canary_max_tokens,
            "canary_timeout_seconds": provider.canary_timeout_seconds,
            "consecutive_failures_to_degrade": cls.consecutive_failures_to_degrade,
            "health_check_cooldown_seconds": cls.health_check_cooldown_seconds,
            "long_phase_allowed_when_degraded": provider.long_phase_allowed_when_degraded,
        }
        values.update(overrides)
        return cls(**values)

    def to_dict(self) -> dict:
        """Serialise config for display / logging."""
        return {
            "connect_timeout_seconds": self.connect_timeout_seconds,
            "read_timeout_seconds": self.read_timeout_seconds,
            "max_retries": self.max_retries,
            "retry_backoff": self.retry_backoff,
            "retry_jitter": self.retry_jitter,
            "minimal_canary_prompt": repr(self.minimal_canary_prompt),
            "canary_max_tokens": self.canary_max_tokens,
            "canary_timeout_seconds": self.canary_timeout_seconds,
            "consecutive_failures_to_degrade": self.consecutive_failures_to_degrade,
            "health_check_cooldown_seconds": self.health_check_cooldown_seconds,
            "long_phase_allowed_when_degraded": self.long_phase_allowed_when_degraded,
        }

def _parse_bool(value: Any, default: bool = False) -> bool:
    """Parse bool-like values from env/config compatibility surfaces."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1", "on")
    return default


# Module-level singleton — load once, use everywhere.
DEFAULT_CONFIG: ProviderGuardConfig = ProviderGuardConfig.from_env()
