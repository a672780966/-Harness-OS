"""Provider Reliability Guard — configuration and policy.

Defines the timeout, retry, and canary policy for the provider reliability guard.
All values are read-only constants; override via env vars for runtime tuning.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ProviderGuardConfig:
    """Provider reliability guard configuration.

    All timeouts in seconds. Can be overridden via environment variables:

        HARNESS_PROVIDER_CONNECT_TIMEOUT
        HARNESS_PROVIDER_READ_TIMEOUT
        HARNESS_PROVIDER_MAX_RETRIES
        HARNESS_PROVIDER_CANARY_TIMEOUT
        HARNESS_PROVIDER_CANARY_MAX_TOKENS
    """

    # Connection / read timeouts
    connect_timeout_seconds: float = 10.0
    read_timeout_seconds: float = 90.0

    # Retry policy
    max_retries: int = 3
    retry_backoff: str = "exponential"  # "exponential" | "linear" | "constant"
    retry_jitter: bool = True

    # Canary prompt
    minimal_canary_prompt: str = "OK"
    canary_max_tokens: int = 10
    canary_timeout_seconds: float = 45.0

    # Degradation policy
    consecutive_failures_to_degrade: int = 2
    health_check_cooldown_seconds: float = 120.0

    @classmethod
    def from_env(cls) -> ProviderGuardConfig:
        """Build config with optional env var overrides."""
        return cls(
            connect_timeout_seconds=float(
                os.environ.get("HARNESS_PROVIDER_CONNECT_TIMEOUT", cls.connect_timeout_seconds)
            ),
            read_timeout_seconds=float(
                os.environ.get("HARNESS_PROVIDER_READ_TIMEOUT", cls.read_timeout_seconds)
            ),
            max_retries=int(
                os.environ.get("HARNESS_PROVIDER_MAX_RETRIES", cls.max_retries)
            ),
            canary_timeout_seconds=float(
                os.environ.get("HARNESS_PROVIDER_CANARY_TIMEOUT", cls.canary_timeout_seconds)
            ),
            canary_max_tokens=int(
                os.environ.get("HARNESS_PROVIDER_CANARY_MAX_TOKENS", cls.canary_max_tokens)
            ),
        )

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
        }


# Module-level singleton — load once, use everywhere.
DEFAULT_CONFIG: ProviderGuardConfig = ProviderGuardConfig.from_env()
