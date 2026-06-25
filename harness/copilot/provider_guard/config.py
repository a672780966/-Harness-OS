"""Provider Reliability Guard — configuration and policy.

Defines the timeout, retry, and canary policy for the provider reliability guard.
All values are read-only constants; override via env vars for runtime tuning.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional


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
    long_phase_allowed_when_degraded: bool = False

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
            long_phase_allowed_when_degraded=(
                os.environ.get("HARNESS_PROVIDER_LONG_PHASE_ALLOWED_WHEN_DEGRADED", "").lower()
                in ("true", "yes", "1")
            ),
        )

    @classmethod
    def from_harness_config(cls, provider_cfg: Any) -> ProviderGuardConfig:
        """Build from a harness.config.schema.ProviderConfig instance.

        Precedence (highest to lowest):
          1. Environment variable overrides (HARNESS_PROVIDER_*)
          2. HarnessConfig ProviderConfig values
          3. Built-in defaults
        """
        # Start with built-in defaults
        cfg = cls()
        if provider_cfg is not None:
            cfg = cls(
                connect_timeout_seconds=float(
                    getattr(provider_cfg, "connect_timeout_seconds", cfg.connect_timeout_seconds)
                ),
                read_timeout_seconds=float(
                    getattr(provider_cfg, "read_timeout_seconds", cfg.read_timeout_seconds)
                ),
                max_retries=int(getattr(provider_cfg, "max_retries", cfg.max_retries)),
                retry_backoff=str(getattr(provider_cfg, "retry_backoff", cfg.retry_backoff)),
                retry_jitter=bool(getattr(provider_cfg, "retry_jitter", cfg.retry_jitter)),
                minimal_canary_prompt=str(
                    getattr(provider_cfg, "minimal_canary_prompt", cfg.minimal_canary_prompt)
                ),
                canary_max_tokens=int(
                    getattr(provider_cfg, "canary_max_tokens", cfg.canary_max_tokens)
                ),
                canary_timeout_seconds=float(
                    getattr(provider_cfg, "canary_timeout_seconds", cfg.canary_timeout_seconds)
                ),
                consecutive_failures_to_degrade=int(
                    getattr(provider_cfg, "consecutive_failures_to_degrade",
                            cfg.consecutive_failures_to_degrade)
                ),
                health_check_cooldown_seconds=float(
                    getattr(provider_cfg, "health_check_cooldown_seconds",
                            cfg.health_check_cooldown_seconds)
                ),
                long_phase_allowed_when_degraded=bool(
                    getattr(provider_cfg, "long_phase_allowed_when_degraded",
                            cfg.long_phase_allowed_when_degraded)
                ),
            )
        # Apply env overrides (highest precedence)
        env_connect = os.environ.get("HARNESS_PROVIDER_CONNECT_TIMEOUT")
        env_read = os.environ.get("HARNESS_PROVIDER_READ_TIMEOUT")
        env_retries = os.environ.get("HARNESS_PROVIDER_MAX_RETRIES")
        env_canary_timeout = os.environ.get("HARNESS_PROVIDER_CANARY_TIMEOUT")
        env_canary_tokens = os.environ.get("HARNESS_PROVIDER_CANARY_MAX_TOKENS")
        env_long_phase = os.environ.get("HARNESS_PROVIDER_LONG_PHASE_ALLOWED_WHEN_DEGRADED")
        if any([env_connect, env_read, env_retries,
                env_canary_timeout, env_canary_tokens, env_long_phase]):
            cfg = cls(
                connect_timeout_seconds=float(env_connect) if env_connect else cfg.connect_timeout_seconds,
                read_timeout_seconds=float(env_read) if env_read else cfg.read_timeout_seconds,
                max_retries=int(env_retries) if env_retries else cfg.max_retries,
                retry_backoff=cfg.retry_backoff,
                retry_jitter=cfg.retry_jitter,
                minimal_canary_prompt=cfg.minimal_canary_prompt,
                canary_max_tokens=int(env_canary_tokens) if env_canary_tokens else cfg.canary_max_tokens,
                canary_timeout_seconds=float(env_canary_timeout) if env_canary_timeout else cfg.canary_timeout_seconds,
                consecutive_failures_to_degrade=cfg.consecutive_failures_to_degrade,
                health_check_cooldown_seconds=cfg.health_check_cooldown_seconds,
                long_phase_allowed_when_degraded=(
                    env_long_phase.lower() in ("true", "yes", "1")
                ) if env_long_phase else cfg.long_phase_allowed_when_degraded,
            )
        return cfg

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


# Module-level singleton — load once, use everywhere.
DEFAULT_CONFIG: ProviderGuardConfig = ProviderGuardConfig.from_env()
