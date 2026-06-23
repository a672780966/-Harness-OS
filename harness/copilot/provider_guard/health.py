"""Provider Health State — persistent state tracking for provider reliability.

Stores health state in .harness/runtime/provider_health.json.
Thread-safe for concurrent reads (small race window on write is acceptable).

States:
    unknown       — no canary run yet
    healthy       — last canary succeeded
    degraded      — consecutive failures exceeded threshold
    failed        — canary timeout / error
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .config import DEFAULT_CONFIG, ProviderGuardConfig


RUNTIME_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # harness/copilot/
    "..", "..", ".harness", "runtime",
)
HEALTH_FILE = os.path.join(RUNTIME_DIR, "provider_health.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z"


@dataclass
class ProviderHealthState:
    """Mutable health state for a single provider endpoint."""

    # State: unknown | healthy | degraded | failed
    state: str = "unknown"

    # Provider model identifier
    model: str = ""

    # Timestamps
    last_check_at: str = ""
    last_success_at: str = ""
    last_failure_at: str = ""

    # Failure tracking
    consecutive_failures: int = 0
    total_failures: int = 0
    total_successes: int = 0

    # Last failure detail
    last_failure_type: str = ""       # timeout | connection_error | dns | tls | http_error | unknown
    last_failure_detail: str = ""
    last_failure_has_http_status: bool = False
    last_failure_http_status: Optional[int] = None

    # Error chain
    failure_history: List[Dict[str, Any]] = field(default_factory=list)

    # Diagnosis context
    endpoint_healthcheck: str = ""      # pass | fail
    model_inference_healthcheck: str = ""  # pass | degraded | failed
    failure_type: str = ""              # diagnostic summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "model": self.model,
            "last_check_at": self.last_check_at,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "consecutive_failures": self.consecutive_failures,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "last_failure_type": self.last_failure_type,
            "last_failure_detail": self.last_failure_detail,
            "last_failure_has_http_status": self.last_failure_has_http_status,
            "last_failure_http_status": self.last_failure_http_status,
            "failure_history": self.failure_history[-20:],  # keep last 20
            "endpoint_healthcheck": self.endpoint_healthcheck,
            "model_inference_healthcheck": self.model_inference_healthcheck,
            "failure_type": self.failure_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProviderHealthState:
        return cls(
            state=data.get("state", "unknown"),
            model=data.get("model", ""),
            last_check_at=data.get("last_check_at", ""),
            last_success_at=data.get("last_success_at", ""),
            last_failure_at=data.get("last_failure_at", ""),
            consecutive_failures=data.get("consecutive_failures", 0),
            total_failures=data.get("total_failures", 0),
            total_successes=data.get("total_successes", 0),
            last_failure_type=data.get("last_failure_type", ""),
            last_failure_detail=data.get("last_failure_detail", ""),
            last_failure_has_http_status=data.get("last_failure_has_http_status", False),
            last_failure_http_status=data.get("last_failure_http_status", None),
            failure_history=data.get("failure_history", []),
            endpoint_healthcheck=data.get("endpoint_healthcheck", ""),
            model_inference_healthcheck=data.get("model_inference_healthcheck", ""),
            failure_type=data.get("failure_type", ""),
        )


def _health_file_path() -> str:
    """Return the runtime health file path, creating dir if needed."""
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    return HEALTH_FILE


def load_health_state() -> ProviderHealthState:
    """Load health state from disk. Returns default if missing / corrupt."""
    path = _health_file_path()
    if not os.path.isfile(path):
        return ProviderHealthState()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProviderHealthState.from_dict(data)
    except (json.JSONDecodeError, IOError, TypeError) as e:
        print(f"Warning: failed to load provider health: {e}", file=sys.stderr)
        return ProviderHealthState()


def save_health_state(state: ProviderHealthState) -> None:
    """Write health state to disk."""
    path = _health_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
    except (IOError, TypeError) as e:
        print(f"Warning: failed to save provider health: {e}", file=sys.stderr)


def record_success(state: ProviderHealthState, model: str = "") -> ProviderHealthState:
    """Record a successful canary check."""
    now = _now_iso()
    state.state = "healthy"
    state.model = model or state.model
    state.last_check_at = now
    state.last_success_at = now
    state.consecutive_failures = 0
    state.total_successes += 1
    state.model_inference_healthcheck = "pass"
    state.failure_type = ""
    save_health_state(state)
    return state


def record_failure(
    state: ProviderHealthState,
    model: str = "",
    failure_type: str = "unknown",
    detail: str = "",
    has_http_status: bool = False,
    http_status: Optional[int] = None,
    config: Optional[ProviderGuardConfig] = None,
) -> ProviderHealthState:
    """Record a failed canary check. Marks degraded if consecutive threshold exceeded."""
    cfg = config or DEFAULT_CONFIG
    now = _now_iso()
    state.model = model or state.model
    state.last_check_at = now
    state.last_failure_at = now
    state.consecutive_failures += 1
    state.total_failures += 1
    state.last_failure_type = failure_type
    state.last_failure_detail = detail
    state.last_failure_has_http_status = has_http_status
    state.last_failure_http_status = http_status

    # Append to history
    entry = {
        "timestamp": now,
        "failure_type": failure_type,
        "detail": detail,
        "has_http_status": has_http_status,
        "http_status": http_status,
        "consecutive_failures": state.consecutive_failures,
    }
    state.failure_history.append(entry)

    # Determine state
    if state.consecutive_failures >= cfg.consecutive_failures_to_degrade:
        state.state = "degraded"
        state.model_inference_healthcheck = "degraded"
    else:
        state.state = "failed"
        state.model_inference_healthcheck = "failed"

    state.failure_type = failure_type
    save_health_state(state)
    return state


def reset_health(model: str = "") -> ProviderHealthState:
    """Reset health state to unknown."""
    state = ProviderHealthState(model=model)
    save_health_state(state)
    return state


def is_provider_degraded(state: Optional[ProviderHealthState] = None) -> bool:
    """Return True if provider is in degraded state (no long-implementation allowed)."""
    if state is None:
        state = load_health_state()
    return state.state == "degraded"


def can_proceed_to_long_phase(state: Optional[ProviderHealthState] = None) -> bool:
    """Return True if provider is healthy enough for long implementation tasks."""
    if state is None:
        state = load_health_state()
    return state.state in ("unknown", "healthy")


def health_check_needed(
    state: Optional[ProviderHealthState] = None,
    config: Optional[ProviderGuardConfig] = None,
) -> bool:
    """Return True if a new canary check should be run (cooldown expired)."""
    if state is None:
        state = load_health_state()
    if state.state == "unknown":
        return True
    if state.last_check_at == "":
        return True
    cfg = config or DEFAULT_CONFIG
    try:
        last = datetime.fromisoformat(state.last_check_at)
        now = datetime.now(timezone.utc)
        elapsed = (now - last).total_seconds()
        return elapsed >= cfg.health_check_cooldown_seconds
    except (ValueError, TypeError):
        return True
