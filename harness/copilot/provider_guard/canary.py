"""Provider Canary — minimal provider health check orchestration.

The canary is a lightweight mechanism that tests whether the provider is
responsive before a long-running Phase begins.

Since Hermes / OpenCode owns the actual API call channel, this module
provides:
  - The canary runner (attempts a subprocess call if a provider CLI is
    available, otherwise returns the persisted health state).
  - The guard interface that Phase scripts import to decide whether to
    proceed.
  - CLI-level status reporting.

State transitions:
    unknown --[canary OK]--> healthy
    unknown --[canary fail]--> failed
    failed  --[canary OK]--> healthy
    failed  --[2nd consecutive fail]--> degraded
    degraded --[canary OK]--> healthy
"""

from __future__ import annotations

import subprocess
import sys
import time
from typing import Any, Dict, Optional, Tuple

from .config import DEFAULT_CONFIG, ProviderGuardConfig
from .health import (
    ProviderHealthState,
    can_proceed_to_long_phase,
    health_check_needed,
    is_provider_degraded,
    load_health_state,
    record_failure,
    record_success,
    reset_health,
    save_health_state,
)


def get_diagnosis_summary(
    state: Optional[ProviderHealthState] = None,
    guard_config: Optional[ProviderGuardConfig] = None,
) -> Dict[str, Any]:
    """Return a complete diagnosis / health summary dict."""
    if state is None:
        state = load_health_state()
    cfg = guard_config or DEFAULT_CONFIG
    return {
        "provider_health_state": state.state,
        "model": state.model,
        "endpoint_healthcheck": state.endpoint_healthcheck or "unknown",
        "model_inference_healthcheck": state.model_inference_healthcheck or "unknown",
        "failure_type": state.failure_type or "none",
        "consecutive_failures": state.consecutive_failures,
        "last_check_at": state.last_check_at,
        "last_success_at": state.last_success_at,
        "last_failure_at": state.last_failure_at,
        "last_failure_detail": state.last_failure_detail[:200] if state.last_failure_detail else "",
        "last_failure_has_http_status": state.last_failure_has_http_status,
        "last_failure_http_status": state.last_failure_http_status,
        "degraded": is_provider_degraded(state),
        "can_proceed_to_long_phase": can_proceed_to_long_phase(state, config=cfg),
        "long_phase_allowed_when_degraded": cfg.long_phase_allowed_when_degraded,
        "guard_config": cfg.to_dict(),
    }


def run_canary_check(
    model: str = "opencode-go/deepseek-v4-flash",
    config: Optional[ProviderGuardConfig] = None,
) -> Tuple[bool, str, ProviderHealthState]:
    """Execute a minimal provider canary check.

    This is the mechanism that Hermes calls before starting a long Phase.

    The actual canary is delegated to a subprocess call against the
    provider's minimal inference endpoint.  If no provider CLI is
    available, the function checks the persisted health state instead.

    Returns:
        (success: bool, detail: str, state: ProviderHealthState)
    """
    cfg = config or DEFAULT_CONFIG
    state = load_health_state()

    # --- Phase guard: no check if recently succeeded ---
    if not health_check_needed(state, cfg):
        if state.state == "healthy":
            return (True, "Recent health check still valid (cooldown)", state)
        # If degraded or failed, always re-check

    # --- Attempt minimal canary via provider CLI ---
    success, detail, output = _attempt_canary_call(cfg)

    if success:
        state = record_success(state, model=model)
        return (True, f"Canary OK: {detail}", state)
    else:
        state = record_failure(
            state,
            model=model,
            failure_type=_classify_failure(detail),
            detail=detail,
        )
        return (False, f"Canary FAILED: {detail}", state)


def _attempt_canary_call(
    config: ProviderGuardConfig,
) -> Tuple[bool, str, str]:
    """Try a minimal provider inference call via subprocess.

    Attempts (in order):
      1. `opencode run --model <model> --prompt "OK" --max-tokens 10`
      2. Falls back to persisted health state if CLI unavailable.

    Returns (success, detail, output).
    """
    # Check if opencode CLI is available
    try:
        r = subprocess.run(
            ["which", "opencode"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            # No CLI — fall back to persisted state
            return _fallback_to_persisted_state()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return _fallback_to_persisted_state()

    # Build a minimal inference command
    cmd = [
        "opencode", "run",
        "--model", "opencode-go/deepseek-v4-flash",
        "--prompt", config.minimal_canary_prompt,
        "--max-tokens", str(config.canary_max_tokens),
        "--temperature", "0",
    ]

    try:
        start = time.monotonic()
        r = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=config.canary_timeout_seconds,
        )
        elapsed = time.monotonic() - start

        if r.returncode == 0:
            output = (r.stdout or "").strip()
            if "OK" in output.upper() or r.returncode == 0:
                return (True, f"responded in {elapsed:.1f}s", output[:200])
            else:
                return (True, f"responded in {elapsed:.1f}s (unexpected output)", output[:200])
        else:
            stderr = (r.stderr or "").strip()
            return (False, f"exit={r.returncode} stderr={stderr[:200]}", stderr)
    except subprocess.TimeoutExpired:
        return (False, f"timeout after {config.canary_timeout_seconds}s", "")
    except FileNotFoundError as e:
        return _fallback_to_persisted_state()
    except PermissionError as e:
        return _fallback_to_persisted_state()
    except OSError as e:
        return (False, f"OS error: {e}", str(e))


def _fallback_to_persisted_state() -> Tuple[bool, str, str]:
    """Fallback: report persisted health state when CLI is unavailable."""
    state = load_health_state()
    if state.state == "healthy":
        return (True, "persisted state: healthy", "no-cli-fallback")
    elif state.state == "unknown":
        return (False, "no provider CLI available and no prior health state", "no-cli-fallback")
    else:
        return (False, f"persisted state: {state.state}, last failure: {state.last_failure_type}", "no-cli-fallback")


def _classify_failure(detail: str) -> str:
    """Classify failure type from detail string."""
    d = detail.lower()
    if "timeout" in d:
        return "timeout"
    if "dns" in d or "name resolution" in d:
        return "dns"
    if "tls" in d or "ssl" in d or "certificate" in d:
        return "tls"
    if "reset" in d or "connection reset" in d or "broken pipe" in d:
        return "connection_reset"
    if "proxy" in d:
        return "proxy_error"
    if "socket" in d or "closed" in d:
        return "socket_closed"
    if "connection" in d:
        return "connection_error"
    if "http" in d or "status" in d:
        return "http_error"
    return "unknown"


def check_before_long_phase(
    model: str = "",
    config: Optional[ProviderGuardConfig] = None,
) -> Dict[str, Any]:
    """Check provider health before starting a long implementation Phase.

    This is the main entrypoint for Phase scripts.  Call it at the top
    of any long Phase.  Returns a dict with:

        allowed: bool  — True if it's safe to proceed
        degraded: bool — True if provider is degraded
        state: str     — current health state
        detail: str    — human-readable explanation
    """
    cfg = config or DEFAULT_CONFIG
    state = load_health_state()

    if is_provider_degraded(state):
        if cfg.long_phase_allowed_when_degraded:
            return {
                "allowed": True,
                "degraded": True,
                "state": state.state,
                "model": state.model,
                "detail": (
                    f"Provider is DEGRADED but long_phase_allowed_when_degraded=True. "
                    f"Consecutive failures: {state.consecutive_failures}."
                ),
            }
        return {
            "allowed": False,
            "degraded": True,
            "state": state.state,
            "model": state.model,
            "detail": (
                f"Provider is DEGRADED (state={state.state}, "
                f"consecutive_failures={state.consecutive_failures}). "
                f"Only status queries allowed. Run `harness copilot provider-status` for details."
            ),
        }

    if state.state == "failed":
        return {
            "allowed": False,
            "degraded": False,
            "state": state.state,
            "model": state.model,
            "detail": (
                f"Provider check FAILED (state={state.state}, "
                f"failure_type={state.failure_type}). "
                f"Run `harness copilot provider-status` for details."
            ),
        }

    if state.state == "healthy":
        return {
            "allowed": True,
            "degraded": False,
            "state": state.state,
            "model": state.model,
            "detail": f"Provider healthy. Last success: {state.last_success_at}",
        }

    # unknown — try a canary
    success, detail, new_state = run_canary_check(model=model, config=cfg)
    if success:
        return {
            "allowed": True,
            "degraded": False,
            "state": new_state.state,
            "model": new_state.model,
            "detail": f"Canary passed: {detail}",
        }
    else:
        return {
            "allowed": False,
            "degraded": new_state.state == "degraded",
            "state": new_state.state,
            "model": new_state.model,
            "detail": f"Canary failed: {detail}",
        }


def restore_health(model: str = "") -> ProviderHealthState:
    """Reset health state to unknown (force re-check on next guard call)."""
    return reset_health(model=model)
