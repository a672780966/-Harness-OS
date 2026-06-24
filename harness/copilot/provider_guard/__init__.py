"""Provider Reliability Guard — pre-execution health check and degradation policy.

Usage:
    from harness.copilot.provider_guard import (
        check_before_long_phase,
        get_diagnosis_summary,
        is_provider_degraded,
        run_canary_check,
    )

    # At the top of a long Phase:
    guard = check_before_long_phase()
    if not guard["allowed"]:
        print(f"Cannot proceed: {guard['detail']}")
        return

Best practice:
    1. Call `check_before_long_phase()` at the start of each long Phase.
    2. If `allowed=False`, abort the Phase and report degradation.
    3. Use `harness copilot provider-status` for manual inspection.
"""

from __future__ import annotations

from .canary import (
    check_before_long_phase,
    get_diagnosis_summary,
    restore_health,
    run_canary_check,
)
from .config import DEFAULT_CONFIG, ProviderGuardConfig
from .health import (
    ProviderHealthState,
    can_proceed_to_long_phase,
    health_check_needed,
    is_provider_degraded,
    load_health_state,
    record_failure,
    record_success,
    save_health_state,
)

__all__ = [
    "DEFAULT_CONFIG",
    "ProviderGuardConfig",
    "ProviderHealthState",
    "can_proceed_to_long_phase",
    "check_before_long_phase",
    "get_diagnosis_summary",
    "health_check_needed",
    "is_provider_degraded",
    "load_health_state",
    "record_failure",
    "record_success",
    "restore_health",
    "run_canary_check",
    "save_health_state",
]
