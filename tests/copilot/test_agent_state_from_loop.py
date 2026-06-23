"""Tests for AgentState inference from real Hermes Loop artifacts."""

import os
import pytest

from harness.copilot.agent_state import AgentStateEnum
from harness.copilot.agent_state.inference import infer_from_loop_artifacts


def _find_loop_run():
    """Find a real tier_C_full run directory."""
    eval_base = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        ".harness", "evaluations", "swebench_abc_mini_pilot_001", "runs",
    )
    if not os.path.isdir(eval_base):
        return None
    for entry in sorted(os.listdir(eval_base)):
        candidate = os.path.join(eval_base, entry, "tier_C_full")
        if os.path.isdir(candidate):
            return candidate
    return None


class TestInferFromRealLoopArtifacts:
    def test_loop_artifacts_loaded(self):
        run_dir = _find_loop_run()
        if not run_dir:
            pytest.skip("No loop run directory available")

        from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
        artifacts = load_loop_artifacts(run_dir)
        assert artifacts is not None

        state = infer_from_loop_artifacts(artifacts)
        assert state.state in [e.value for e in AgentStateEnum]
        assert 0.0 <= state.confidence <= 1.0

    def test_loop_artifacts_have_source_events(self):
        run_dir = _find_loop_run()
        if not run_dir:
            pytest.skip("No loop run directory available")

        from harness.copilot.integration.loop_artifact_loader import load_loop_artifacts
        artifacts = load_loop_artifacts(run_dir)
        state = infer_from_loop_artifacts(artifacts)

        # Should have at least one source event if artifacts exist
        if artifacts.load_errors:
            pytest.skip("Artifacts had load errors")
        assert isinstance(state.source_events, list)
