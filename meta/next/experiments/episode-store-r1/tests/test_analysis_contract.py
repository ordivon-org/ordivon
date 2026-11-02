from __future__ import annotations

from collections import Counter

from ordivon_experimental_episode_store.analysis import (
    _percentile,
    generalization_gate,
    intervention_gate,
)


def test_percentile_is_deterministic_linear_interpolation() -> None:
    assert _percentile([0.0, 10.0], 0.95) == 9.5
    assert _percentile([4.0], 0.95) == 4.0


def test_generalization_requires_explicit_development_and_judge() -> None:
    result = generalization_gate(Counter({"EXPERIENCE": 10007}))
    assert result["standing"] == "NOT_IDENTIFIED"
    assert result["reason"] == "INSUFFICIENT_EXPLICIT_DEVELOPMENT_JUDGE_SPLIT"

    eligible = generalization_gate(Counter({"DEVELOPMENT": 10, "JUDGE": 10}))
    assert eligible["standing"] == "ELIGIBLE_FOR_SEPARATE_GENERALIZATION_STUDY"


def test_intervention_requires_frozen_contract_and_assignment() -> None:
    result = intervention_gate(
        intervention_contract_ref=None,
        assigned_episode_count=100,
    )
    assert result["standing"] == "NOT_IDENTIFIED"
    assert result["reason"] == "NO_FROZEN_INTERVENTION_CONTRACT"

    still_open = intervention_gate(
        intervention_contract_ref="study:causal-r1",
        assigned_episode_count=1,
    )
    assert still_open["standing"] == "NOT_IDENTIFIED"

    eligible = intervention_gate(
        intervention_contract_ref="study:causal-r1",
        assigned_episode_count=2,
    )
    assert eligible["standing"] == "ELIGIBLE_FOR_SEPARATE_CAUSAL_STUDY"
