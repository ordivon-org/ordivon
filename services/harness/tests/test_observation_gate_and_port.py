"""The public Harness composition must depend on a Port, not a SQLite class."""

from __future__ import annotations

from inspect import signature

from ordivon_harness.agent_run import HarnessToolBridgeFactory
from ordivon_harness.ordivon.loop import RunBudget


def test_bridge_factory_accepts_existing_owner_neutral_continuity_port() -> None:
    continuity = signature(HarnessToolBridgeFactory.build).parameters["continuity"]
    assert continuity.annotation == "HarnessRunContinuityStore"
    assert continuity.annotation != "SQLiteHarnessRunContinuityStore"


def test_observation_gate_contract_exact_boundary_and_priority() -> None:
    budget = RunBudget(
        max_model_calls=4,
        max_tool_calls=4,
        max_observation_bytes=2048,
        max_wall_time_ms=6000,
        max_no_progress_turns=2,
        max_observation_only_turns=3,
    )
    assert budget.observation_gate_reason(
        no_progress_turns=1, observation_only_turns=2
    ) is None
    assert budget.observation_gate_reason(
        no_progress_turns=2, observation_only_turns=3
    ) == (
        "external observation gate closed after "
        "2 consecutive turns without a mutation, check, "
        "materially new bounded observation, or conclusion"
    )
    assert budget.observation_gate_reason(
        no_progress_turns=0, observation_only_turns=3
    ) == (
        "external observation gate closed after "
        "3 consecutive observation-only turns without a mutation, check, or conclusion"
    )
    disabled = RunBudget(
        max_model_calls=4,
        max_tool_calls=4,
        max_observation_bytes=2048,
        max_wall_time_ms=6000,
        max_no_progress_turns=0,
        max_observation_only_turns=0,
    )
    assert disabled.observation_gate_reason(
        no_progress_turns=10_000, observation_only_turns=10_000
    ) is None
