"""Cross-owner falsifiers for multistage cashflow conservation.

The replay algorithm cannot import the optimizer or its SciPy matrices.
Fixtures are mathematical examples, not market-return or risk forecasts.
"""

from __future__ import annotations

import copy
import json
import math
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from ordivon_capital.portfolio.multistage_policy import (
    InformationNode,
    MultistageProblem,
    solve_multistage,
)
from ordivon_capital.research.independent_policy_replay import (
    EconomicReplayMismatch,
    replay_multistage_json,
)


def _payload(problem: MultistageProblem) -> dict:
    solution = solve_multistage(problem)
    # Precisely emulate the public JSON consumer, not a private object path.
    return json.loads(
        json.dumps(
            {
                "problem": asdict(problem),
                "solution": asdict(solution),
            }
        )
    )


def _two_months_with_liabilities() -> MultistageProblem:
    return MultistageProblem(
        gamma=2,
        nodes=(
            InformationNode(
                id="root",
                parent=None,
                t=0,
                conditional_probability=1.0,
                initial_margin=(0.5,),
                turnover_cost=(0.005,),
            ),
            InformationNode(
                id="up",
                parent="root",
                t=1,
                conditional_probability=0.5,
                risky_gross=(1.12,),
                cash_gross=1.01,
                debt_gross=1.03,
                maintenance=(0.35,),
                initial_margin=(0.5,),
                turnover_cost=(0.005,),
            ),
            InformationNode(
                id="down",
                parent="root",
                t=1,
                conditional_probability=0.5,
                risky_gross=(0.92,),
                cash_gross=1.01,
                debt_gross=1.03,
                maintenance=(0.35,),
                initial_margin=(0.5,),
                turnover_cost=(0.005,),
            ),
            InformationNode(
                id="up_exit",
                parent="up",
                t=2,
                conditional_probability=1.0,
                risky_gross=(1.1,),
                cash_gross=1.01,
                debt_gross=1.03,
                maintenance=(0.35,),
                terminal=True,
            ),
            InformationNode(
                id="down_exit",
                parent="down",
                t=2,
                conditional_probability=1.0,
                risky_gross=(0.95,),
                cash_gross=1.01,
                debt_gross=1.03,
                maintenance=(0.35,),
                terminal=True,
            ),
        ),
        node_outflow_after_contribution_r={
            "root": 0.10,
            "up": 0.15,
            "down": 0.15,
        },
        terminal_liabilities_r={
            "up_exit": 0.4,
            "down_exit": 0.4,
        },
    )


def test_economic_replay_respects_dated_cashflow_and_terminal_liability() -> None:
    payload = _payload(_two_months_with_liabilities())
    evidence = replay_multistage_json(**payload)
    assert evidence["terminal_node_count"] == 2
    assert evidence["decision_node_count"] == 3
    assert evidence["max_identity_residual_r"] < 1e-6
    assert evidence["minimum_collateral_surplus_r"] >= -1e-6
    assert evidence["effects"] == "NONE_NO_BROKER_NO_ACCOUNTING"


@pytest.mark.parametrize(
    ("path", "injection", "message"),
    [
        (("terminal_distribution", "up_exit", "terminalR"), 3.0, "terminalR"),
        (("node_decisions_r", "root", "postTradeEquityR"), 0.1, "postTradeEquityR"),
        (("node_decisions_r", "up", "tradeCostR"), 0.3, "tradeCostR"),
        (("node_decisions_r", "down", "debtR"), 0.25, "budget"),
        (("terminal_distribution", "down_exit", "obligationR"), 0.3, "obligationR"),
    ],
)
def test_replay_detects_forged_cashflow_or_profit(
    path: tuple[str, ...], injection: float, message: str
) -> None:
    payload = _payload(_two_months_with_liabilities())
    corrupted = copy.deepcopy(payload)
    target = corrupted["solution"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] += injection
    with pytest.raises(EconomicReplayMismatch, match=message):
        replay_multistage_json(**corrupted)


def test_replay_detects_hidden_extra_monthly_contribution() -> None:
    payload = _payload(_two_months_with_liabilities())
    payload["problem"]["node_outflow_after_contribution_r"]["up"] = 0.0
    with pytest.raises(EconomicReplayMismatch, match="budget"):
        replay_multistage_json(**payload)


def test_independent_bisection_one_period_log_utility_checks_optimality_gap() -> None:
    """Independent strict concavity in one dimension, no SciPy or model LP proof.

    Set margin=1 and borrowing cost greater than cash, eliminating profitable
    borrowing from this symmetric two-state no-fee fixture.
    For x in [0,1], U(x) = .5 log(1 - .5 x) + .5 log(1 + .6 x).
    The derivative is strictly decreasing, so bisection brackets the global
    optimum in the admissible unlevered single-asset subset.
    """
    problem = MultistageProblem(
        gamma=1.0,
        nodes=(
            InformationNode(
                id="root",
                parent=None,
                t=0,
                conditional_probability=1.0,
                initial_margin=(1.0,),
                turnover_cost=(0.0,),
            ),
            InformationNode(
                id="down",
                parent="root",
                t=1,
                conditional_probability=0.5,
                risky_gross=(0.5,),
                cash_gross=1.0,
                debt_gross=1.10,
                maintenance=(0.5,),
                terminal=True,
            ),
            InformationNode(
                id="up",
                parent="root",
                t=1,
                conditional_probability=0.5,
                risky_gross=(1.6,),
                cash_gross=1.0,
                debt_gross=1.10,
                maintenance=(0.5,),
                terminal=True,
            ),
        ),
    )
    payload = _payload(problem)
    evidence = replay_multistage_json(**payload)
    assert evidence["max_identity_residual_r"] < 1e-6
    low, high = 0.0, 1.0
    for _ in range(80):
        middle = (low + high) / 2
        derivative = -0.25 / (1 - 0.5 * middle) + 0.3 / (1 + 0.6 * middle)
        if derivative > 0:
            low = middle
        else:
            high = middle
    x_star = (low + high) / 2
    true_optimal_utility = 0.5 * math.log(1 - 0.5 * x_star) + 0.5 * math.log(1 + 0.6 * x_star)
    solved = payload["solution"]
    assert solved["root_risky_r"][0] == pytest.approx(x_star, abs=1e-5)
    assert solved["expected_utility"] <= true_optimal_utility + 1e-7
    assert (
        true_optimal_utility - solved["expected_utility"]
        <= solved["concavity_global_utility_gap_upper"] + 1e-7
    )


def test_replay_stands_apart_from_optimizer_gap_claim() -> None:
    payload = _payload(_two_months_with_liabilities())
    # Older receipts have no typed proof field; preserve numeric-only replay.
    payload["solution"].pop("optimality_evidence")
    payload["solution"]["concavity_global_utility_gap_upper"] = 0.0
    audit = replay_multistage_json(**payload)
    assert audit["standing"].endswith("NOT_OPTIMALITY_CERTIFICATE")
    assert audit["reported_numeric_gap_not_independently_certified"] == 0.0


def test_real_replay_cli_reads_frozen_solver_pair(tmp_path) -> None:
    """Actual module consumer roundtrip rather than an internal-function-only test."""
    payload = _payload(_two_months_with_liabilities())
    pair = tmp_path / "frozen-solver-pair.json"
    pair.write_text(json.dumps(payload), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_capital.research.independent_policy_replay",
            "--input",
            str(pair),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    receipt = json.loads(result.stdout)
    assert receipt["decision_node_count"] == 3
    assert receipt["terminal_node_count"] == 2
    assert len(receipt["input_sha256"]) == 64
    payload["solution"]["terminal_distribution"]["up_exit"]["terminalR"] += 5
    pair.write_text(json.dumps(payload), encoding="utf-8")
    rejected = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_capital.research.independent_policy_replay",
            "--input",
            str(pair),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert rejected.returncode != 0
    assert "terminalR" in rejected.stderr


@pytest.mark.parametrize(
    "field", ["duplicate_obligation", "duplicate_solution", "integer_terminal"]
)
def test_independent_replay_rejects_ambiguous_source_bytes(tmp_path, field):
    payload = _payload(_two_months_with_liabilities())
    if field == "integer_terminal":
        payload["problem"]["nodes"][-1]["terminal"] = 1
    raw = json.dumps(payload)
    if field == "duplicate_obligation":
        raw = raw.replace('"up_exit": 0.4', '"up_exit": 100, "up_exit": 0.4')
    elif field == "duplicate_solution":
        raw = raw.replace('"root_cash_r":', '"root_cash_r": 100, "root_cash_r":')
    pair = tmp_path / "ambiguous.json"
    pair.write_text(raw, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_capital.research.independent_policy_replay",
            "--input",
            str(pair),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert result.returncode != 0, result.stdout
    assert not result.stdout


def test_replay_does_not_promote_unknown_or_conflicting_gap_evidence():
    payload = _payload(_two_months_with_liabilities())
    claim = payload["solution"]["optimality_evidence"]
    audit = replay_multistage_json(**payload)
    assert audit["reported_optimality_evidence_standing"] == claim["standing"]
    assert (
        audit["reported_canonical_gap_upper_not_independently_certified"]
        == claim["certified_canonical_gap_upper"]
    )
    claim["numerical_tangent_gap_estimate"] = (
        payload["solution"]["concavity_global_utility_gap_upper"] + 1.0
    )
    with pytest.raises(EconomicReplayMismatch, match="inconsistent numerical gap"):
        replay_multistage_json(**payload)
    claim.update(
        numerical_tangent_gap_estimate=payload["solution"]["concavity_global_utility_gap_upper"],
        standing="UNKNOWN",
        certified_canonical_gap_upper=0.0,
        dual_proposal=None,
    )
    with pytest.raises(EconomicReplayMismatch, match="UNKNOWN cannot carry"):
        replay_multistage_json(**payload)


@pytest.mark.parametrize("gamma", (0.9999999999999999, 1.0000000000000002, 1.000000000001))
def test_independent_replay_preserves_deterministic_ce_near_log_limit(gamma):
    problem = MultistageProblem(
        gamma,
        (
            InformationNode("root", None, 0, 1.0, initial_margin=(1.0,), turnover_cost=(0.0,)),
            InformationNode(
                "leaf",
                "root",
                1,
                1.0,
                risky_gross=(0.4,),
                cash_gross=0.5,
                debt_gross=0.6,
                maintenance=(0.3,),
                terminal=True,
            ),
        ),
    )
    payload = _payload(problem)
    assert payload["solution"]["certainty_equivalent_terminal_r"] == pytest.approx(0.5)
    assert replay_multistage_json(**payload)["max_identity_residual_r"] < 1e-6


@pytest.mark.parametrize("gamma", (0.9999999999999999, 1.0, 1.0000000000000002))
def test_independent_ce_log_limit_with_nonidentical_wealth_and_admitted_mass_error(gamma):
    from ordivon_capital.research.independent_policy_replay import _ce

    # The normalized geometric mean is exactly 1 when these weights agree.
    # A tiny allowed total-mass error must not be amplified by 1/(1-gamma).
    assert _ce([(0.50000000001, 0.25), (0.50000000001, 4.0)], gamma) == pytest.approx(
        1.0, abs=1e-14
    )


def test_independent_ce_harmonic_mean_and_extreme_log_range():
    from ordivon_capital.research.independent_policy_replay import _ce

    assert _ce([(0.5, 1.0), (0.5, 4.0)], 2.0) == pytest.approx(1.6)
    assert _ce([(0.5, 1e-200), (0.5, 1e200)], 1.0) == pytest.approx(1.0)
    assert _ce([(0.5, 1e-200), (0.5, 1e200)], 1e300) == pytest.approx(1e-200, rel=1e-14, abs=0)


def _actual_repaired_payload():
    problem = MultistageProblem(
        2.0,
        (
            InformationNode("root", None, 0, 1.0, initial_margin=(1.0,), turnover_cost=(0.0,)),
            InformationNode(
                "leaf",
                "root",
                1,
                1.0,
                risky_gross=(1.125,),
                cash_gross=1.0,
                debt_gross=1.1,
                maintenance=(0.3,),
                terminal=True,
            ),
        ),
    )
    solution = solve_multistage(problem, witness_repair_max_change_r=2**-40)
    assert solution.optimality_evidence.standing == "UNKNOWN"
    assert solution.witness_repair.standing == "VERIFIED_DISTINCT_CANONICAL_WITNESS"
    return json.loads(json.dumps({"problem": asdict(problem), "solution": asdict(solution)}))


def test_replay_keeps_repaired_witness_separate_from_original_evidence():
    payload = _actual_repaired_payload()
    audit = replay_multistage_json(**payload)
    assert audit["reported_optimality_evidence_standing"] == "UNKNOWN"
    assert audit["reported_canonical_gap_upper_not_independently_certified"] is None
    assert (
        audit["reported_repair_standing_not_independently_certified"]
        == "VERIFIED_DISTINCT_CANONICAL_WITNESS"
    )
    assert (
        audit["reported_repaired_witness_gap_not_independently_certified"]
        == payload["solution"]["witness_repair"]["canonical_evidence"][
            "certified_canonical_gap_upper"
        ]
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "source_evidence",
        "delta",
        "budget",
        "source_hash",
        "repaired_hash",
        "policy_shape",
        "unknown_with_proof",
        "estimate",
    ),
)
def test_replay_rejects_contradictory_repair_projections(mutation):
    payload = _actual_repaired_payload()
    repair = payload["solution"]["witness_repair"]
    if mutation == "source_evidence":
        repair["source_evidence"]["reason"] = "FORGED"
    elif mutation == "delta":
        repair["max_observed_change_r"] = 0.0
    elif mutation == "budget":
        repair["max_change_r"] = 0.0
    elif mutation == "source_hash":
        repair["source_policy_sha256"] = "0" * 64
    elif mutation == "repaired_hash":
        repair["repaired_policy_sha256"] = "0" * 64
    elif mutation == "policy_shape":
        repair["repaired_policy"] = {}
    elif mutation == "unknown_with_proof":
        repair["standing"] = "UNKNOWN"
    elif mutation == "estimate":
        repair["canonical_evidence"]["numerical_tangent_gap_estimate"] += 1.0
    with pytest.raises(EconomicReplayMismatch, match="repair"):
        replay_multistage_json(**payload)


def test_replay_reports_unknown_repair_without_upgrading_original():
    payload = _actual_repaired_payload()
    repair = payload["solution"]["witness_repair"]
    repair.update(
        standing="UNKNOWN",
        reason="NO_CERTIFIED_WITNESS_WITHIN_SEARCH_BUDGET",
        repaired_policy=None,
        repaired_policy_sha256=None,
        max_observed_change_r=None,
        contraction_exponent=None,
        canonical_evidence=None,
    )
    audit = replay_multistage_json(**payload)
    assert audit["reported_repair_standing_not_independently_certified"] == "UNKNOWN"
    assert audit["reported_repaired_witness_gap_not_independently_certified"] is None
    assert audit["reported_optimality_evidence_standing"] == "UNKNOWN"
