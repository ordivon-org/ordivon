"""Economic consumers for normalized monthly 1r nonanticipative scenario trees.

All test input numbers are synthetic finite mathematical fixtures, NOT
investment risk budgets, historical forecasts, or brokerage facts.
"""
from __future__ import annotations

import pytest

from ordivon_capital.portfolio.algebraic_policy import (
    AlgebraicPolicyError,
    OnePeriodProblem,
    Scenario,
    solve_one_period,
)
from ordivon_capital.portfolio.multistage_policy import (
    InformationNode,
    MultistageProblem,
    solve_multistage,
)


def root(*, margin: float = .4, cost: float = 0) -> InformationNode:
    return InformationNode(
        id="root", parent=None, t=0, conditional_probability=1,
        initial_margin=(margin,), turnover_cost=(cost,),
    )


def terminal(
    id: str, parent: str, t: int, probability: float, gross: float,
    *, cash: float = 1, debt: float = 1.01,
    maintenance: float = .3, label: str = "",
) -> InformationNode:
    return InformationNode(
        id=id, parent=parent, t=t, conditional_probability=probability,
        risky_gross=(gross,), cash_gross=cash, debt_gross=debt,
        maintenance=(maintenance,), terminal=True, observed_label=label,
    )


def test_information_tree_is_a_pure_reusable_financial_contract() -> None:
    from ordivon_capital.portfolio.information_tree import (
        InformationNode as CanonicalInformationNode,
    )
    from ordivon_capital.portfolio.information_tree import (
        MultistageProblem as CanonicalMultistageProblem,
    )
    from ordivon_capital.portfolio.information_tree import (
        validate_information_tree,
    )
    from ordivon_capital.portfolio.multistage_policy import _validate_tree

    # Current research callers still use the established Portfolio module
    # types; the new specification is identity-equal, not a shadow model.
    assert CanonicalInformationNode is InformationNode
    assert CanonicalMultistageProblem is MultistageProblem
    assert _validate_tree is validate_information_tree
    problem = MultistageProblem(
        gamma=2.0,
        nodes=(
            root(),
            terminal("lower", "root", 1, 0.4, 0.85),
            terminal("upper", "root", 1, 0.6, 1.12),
        ),
    )
    tree = validate_information_tree(problem)
    assert tree.months == 1
    assert tuple(node.id for node in tree.decision) == ("root",)
    assert tuple(node.id for node in tree.leaves) == ("lower", "upper")
    assert tree.probability["lower"] == pytest.approx(0.4)
    assert tree.probability["upper"] == pytest.approx(0.6)


def test_one_period_is_a_special_case_of_multistage_convex_program() -> None:
    econ = OnePeriodProblem(
        gamma=1, initial_margin=(.4,), turnover_cost=(0,),
        old_weights=(0,),
        scenarios=(
            Scenario(.4, (1.8,), 1.0, 1.01, (.2,)),
            Scenario(.6, (2.0,), 1.0, 1.01, (.2,)),
        ),
    )
    original = solve_one_period(econ)
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("down", "root", 1, .4, 1.8, maintenance=.2),
            terminal("up", "root", 1, .6, 2.0, maintenance=.2),
        ),
    )
    multi = solve_multistage(tree)
    assert multi.contributions_r_per_path == 1
    assert multi.root_risky_r[0] == pytest.approx(
        original.risky_weights[0], abs=1e-5
    )
    assert multi.expected_terminal_r == pytest.approx(
        original.expected_equity, abs=1e-5
    )
    assert multi.certainty_equivalent_terminal_r == pytest.approx(
        original.certainty_equivalent, abs=1e-5
    )
    assert multi.equality_residual < 1e-7
    assert multi.inequality_residual < 1e-7
    assert multi.concavity_global_utility_gap_upper < 1e-5


def test_two_months_each_inject_exactly_one_r_not_investment_return() -> None:
    tree = MultistageProblem(
        gamma=2,
        nodes=(
            root(),
            InformationNode(
                id="month2", parent="root", t=1,
                conditional_probability=1,
                risky_gross=(.80,), cash_gross=1.05, debt_gross=1.06,
                maintenance=(.3,), initial_margin=(.4,), turnover_cost=(0,),
            ),
            terminal("end", "month2", 2, 1, .8,
                     cash=1.03, debt=1.04),
        ),
    )
    result = solve_multistage(tree)
    assert result.contributions_r_per_path == 2
    assert result.root_risky_r[0] == pytest.approx(0, abs=1e-7)
    assert result.node_decisions_r["month2"]["assetExposuresR"][0] == pytest.approx(
        0, abs=1e-7
    )
    # First 1r grows across both months; second 1r grows only one month.
    assert result.expected_terminal_r == pytest.approx(
        1.05 * 1.03 + 1.03, abs=1e-6
    )
    assert result.concavity_global_utility_gap_upper < 1e-5


def test_different_observations_allow_distinct_future_actions_not_foresight() -> None:
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(margin=.5),
            InformationNode(
                "bad", "root", 1, .5, (.95,), 1, 1.01, (.35,),
                (.5,), (0,),
            ),
            InformationNode(
                "good", "root", 1, .5, (1.05,), 1, 1.01, (.35,),
                (.5,), (0,),
            ),
            terminal("bad_low", "bad", 2, .5, .6),
            terminal("bad_high", "bad", 2, .5, .7),
            terminal("good_low", "good", 2, .5, 1.5),
            terminal("good_high", "good", 2, .5, 1.8),
        ),
    )
    result = solve_multistage(tree)
    assert result.contributions_r_per_path == 2
    assert set(result.node_decisions_r) == {"root", "bad", "good"}
    assert result.node_decisions_r["bad"]["assetExposuresR"][0] < 1e-5
    assert result.node_decisions_r["good"]["assetExposuresR"][0] > 0
    assert len(result.terminal_distribution) == 4
    assert sum(v["probability"] for v in result.terminal_distribution.values()) == pytest.approx(1)
    assert result.concavity_global_utility_gap_upper < 1e-5


def test_possible_total_loss_prevents_unsecured_positive_margin_borrowing() -> None:
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(margin=.4),
            terminal("wipeout", "root", 1, .4, 0.0,
                     cash=1.01, debt=1.05, maintenance=.6),
            terminal("rally", "root", 1, .6, 2.0,
                     cash=1.01, debt=1.05, maintenance=.3),
        ),
    )
    sol = solve_multistage(tree)
    assert sol.root_debt_r < 1e-6
    assert sol.terminal_distribution["wipeout"]["terminalR"] > 0
    assert sol.equality_residual < 1e-7


def test_probability_mass_and_hidden_information_are_economic_contracts() -> None:
    duplicated = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("hidden_A", "root", 1, .5, 1.5),
            terminal("hidden_B", "root", 1, .5, 1.5),
        ),
    )
    with pytest.raises(AlgebraicPolicyError, match="indistinguishable"):
        solve_multistage(duplicated)
    invalid_distribution = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("low", "root", 1, .25, 0.8),
            terminal("high", "root", 1, .5, 1.4),
        ),
    )
    with pytest.raises(AlgebraicPolicyError, match="sum to one"):
        solve_multistage(invalid_distribution)


def test_unequal_loan_and_deposit_rates_never_generate_free_arbitrage() -> None:
    tree = MultistageProblem(
        gamma=1,
        nodes=(
            root(),
            terminal("down", "root", 1, .5, .9, cash=1.04, debt=1.07),
            terminal("up", "root", 1, .5, 1.0, cash=1.04, debt=1.07),
        ),
    )
    result = solve_multistage(tree)
    assert result.root_cash_r == pytest.approx(1, abs=1e-6)
    assert result.root_debt_r == pytest.approx(0, abs=1e-6)
    assert result.root_risky_r[0] == pytest.approx(0, abs=1e-6)
    assert result.expected_terminal_r == pytest.approx(1.04, abs=1e-6)

def test_two_asset_joint_states_observe_only_current_branch_and_margin() -> None:
    root_node = InformationNode(
        "root", None, 0, 1, initial_margin=(.5, .5), turnover_cost=(.01, .01)
    )
    decisions = (
        InformationNode(
            "A", "root", 1, .45, (.9, 1.2), 1.01, 1.03,
            (.4, .4), (.5, .5), (.01, .01),
        ),
        InformationNode(
            "B", "root", 1, .55, (1.2, .9), 1.01, 1.03,
            (.4, .4), (.5, .5), (.01, .01),
        ),
    )
    leaves = (
        InformationNode(
            "A1", "A", 2, .3, (.95, 1.15), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
        InformationNode(
            "A2", "A", 2, .7, (1.2, 1.05), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
        InformationNode(
            "B1", "B", 2, .8, (1.05, .95), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
        InformationNode(
            "B2", "B", 2, .2, (1.3, 1.4), 1.01, 1.03,
            (.4, .4), terminal=True,
        ),
    )
    sol = solve_multistage(
        MultistageProblem(gamma=3, nodes=(root_node, *decisions, *leaves))
    )
    assert sol.contributions_r_per_path == 2
    assert len(sol.node_decisions_r) == 3
    assert len(sol.root_risky_r) == 2
    assert all(w >= 0 for w in sol.root_risky_r)
    assert sum(sol.root_risky_r) + sol.root_cash_r - sol.root_debt_r == pytest.approx(
        1 - sol.node_decisions_r["root"]["tradeCostR"], abs=1e-7
    )
    assert sum(x["probability"] for x in sol.terminal_distribution.values()) == pytest.approx(1)
    assert all(x["terminalR"] > 0 for x in sol.terminal_distribution.values())
    assert sol.equality_residual < 1e-7
    assert sol.inequality_residual < 1e-7
    assert sol.concavity_global_utility_gap_upper < 1e-5

def test_native_module_consumer_accepts_exact_json_and_no_execution_authority() -> None:
    import dataclasses
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    # Pytest adds src to sys.path via pythonpath config, but an independent
    # Runtime child process needs the same explicit native source binding.
    src = str(Path(__file__).resolve().parents[1] / "src")
    inherited = os.environ.get("PYTHONPATH")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = src + (
        os.pathsep + inherited if inherited else ""
    )
    payload = {
        "gamma": 2,
        "nodes": [
            dataclasses.asdict(root()),
            dataclasses.asdict(
                terminal(
                    "terminal", "root", 1, 1, .8,
                    cash=1.03, debt=1.04,
                )
            ),
        ],
    }
    command = [
        sys.executable,
        "-m",
        "ordivon_capital.portfolio.multistage_policy",
        "--input",
        "-",
    ]
    result = subprocess.run(
        command,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env=environment,
    )
    observed = json.loads(result.stdout)
    assert observed["inputStanding"] == "CALLER_SUPPLIED_NOT_MARKET_ATTESTED"
    assert observed["effectStanding"] == "READ_ONLY_NO_BROKER_NO_PAPER_LEDGER"
    assert observed["solution"]["contributions_r_per_path"] == 1
    assert observed["solution"]["expected_terminal_r"] == pytest.approx(
        1.03, abs=1e-6
    )
    assert observed["solution"]["root_debt_r"] < 1e-6
    missing = subprocess.run(
        command, input='{"nodes":[]}', text=True,
        capture_output=True, check=False, env=environment,
    )
    assert missing.returncode != 0
    assert "expected only gamma and nodes" in missing.stderr


@pytest.mark.parametrize("bad_case", [
    "duplicate_terminal_liability",
    "duplicate_intermediate_obligation",
    "duplicate_gamma",
    "boolean_gamma",
    "boolean_month",
    "boolean_probability",
    "boolean_gross",
    "integer_terminal",
])
def test_native_multistage_rejects_ambiguous_economic_input(bad_case: str) -> None:
    import dataclasses
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    payload = {
        "gamma": 1,
        "nodes": [
            dataclasses.asdict(root()),
            dataclasses.asdict(terminal("end", "root", 1, 1, .8)),
        ],
        "terminal_liabilities_r": {"end": .4},
        "node_outflow_after_contribution_r": {"root": .2},
    }
    if bad_case == "boolean_gamma":
        payload["gamma"] = True
    elif bad_case == "boolean_month":
        payload["nodes"][1]["t"] = True
    elif bad_case == "boolean_probability":
        payload["nodes"][1]["conditional_probability"] = True
    elif bad_case == "boolean_gross":
        payload["nodes"][1]["risky_gross"] = [True]
    elif bad_case == "integer_terminal":
        payload["nodes"][1]["terminal"] = 1
    raw = json.dumps(payload)
    if bad_case == "duplicate_terminal_liability":
        raw = raw.replace('"end": 0.4', '"end": 100, "end": 0.4')
    elif bad_case == "duplicate_intermediate_obligation":
        raw = raw.replace('"root": 0.2', '"root": 100, "root": 0.2')
    elif bad_case == "duplicate_gamma":
        raw = raw.replace('"gamma": 1', '"gamma": -1, "gamma": 1')
    result = subprocess.run(
        [sys.executable, "-m", "ordivon_capital.portfolio.multistage_policy", "--input", "-"],
        input=raw, text=True, capture_output=True, check=False,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert result.returncode != 0, result.stdout
    assert not result.stdout

@pytest.mark.parametrize("case", ("id-list", "parent-list", "time-string", "gamma-overflow", "probability-overflow", "probability-above-one"))
def test_information_tree_malformed_inputs_have_domain_error(case: str) -> None:
    from dataclasses import replace

    from ordivon_capital.portfolio.information_tree import validate_information_tree

    first = root()
    leaf = terminal("only", "root", 1, 1.0, 1.1)
    gamma = 2
    if case == "id-list":
        leaf = replace(leaf, id=["bad"])
    elif case == "parent-list":
        leaf = replace(leaf, parent=["root"])
    elif case == "time-string":
        leaf = replace(leaf, t="1")
    elif case == "gamma-overflow":
        gamma = 10**400
    elif case == "probability-overflow":
        leaf = replace(leaf, conditional_probability=10**400)
    elif case == "probability-above-one":
        # Sum tolerance is not permission to admit a probability above one.
        leaf = replace(leaf, conditional_probability=1.0 + 1e-12)
    with pytest.raises(AlgebraicPolicyError):
        validate_information_tree(MultistageProblem(gamma, (first, leaf)))


def test_information_tree_must_not_erase_positive_terminal_path() -> None:
    from dataclasses import replace

    from ordivon_capital.portfolio.information_tree import validate_information_tree

    rare = InformationNode(
        id="rare", parent="root", t=1, conditional_probability=1e-200,
        risky_gross=(.9,), cash_gross=1, debt_gross=1.01,
        maintenance=(.3,), initial_margin=(.4,), turnover_cost=(0,),
    )
    common = replace(rare, id="common", conditional_probability=1.0, risky_gross=(1.1,))
    nodes = (
        root(), rare, common,
        terminal("rare-rare", "rare", 2, 1e-200, .8),
        terminal("rare-common", "rare", 2, 1.0, 1.1),
        terminal("common-only", "common", 2, 1.0, 1.1),
    )
    # A possible history has mathematically positive probability. A binary64
    # representation that underflows must be rejected rather than becoming
    # a silently zero-weight scenario in the objective.
    from fractions import Fraction
    assert Fraction(rare.conditional_probability)**2 > 0
    with pytest.raises(AlgebraicPolicyError):
        validate_information_tree(MultistageProblem(2.0, nodes))


@pytest.mark.parametrize(
    ("target", "field", "value"),
    (
        ("problem", "nodes", 17),
        ("root", "initial_margin", None),
        ("root", "turnover_cost", None),
        ("leaf", "risky_gross", None),
        ("leaf", "maintenance", None),
        ("leaf", "risky_gross", [1.1]),
        ("leaf", "initial_margin", None),
        ("leaf", "turnover_cost", None),
    ),
)
def test_information_tree_rejects_noncanonical_vector_shapes(target, field, value):
    from dataclasses import replace

    from ordivon_capital.portfolio.information_tree import validate_information_tree

    first = root()
    leaf = terminal("only", "root", 1, 1.0, 1.1)
    problem = MultistageProblem(2.0, (first, leaf))
    if target == "problem":
        problem = replace(problem, **{field: value})
    elif target == "root":
        problem = replace(problem, nodes=(replace(first, **{field: value}), leaf))
    else:
        problem = replace(problem, nodes=(first, replace(leaf, **{field: value})))
    with pytest.raises(AlgebraicPolicyError):
        validate_information_tree(problem)

def test_information_tree_can_validate_without_loading_either_solver():
    """A pure information consumer must work with solver imports unavailable."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    program = """
import sys
from importlib.abc import MetaPathFinder
class NoSolvers(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in (
            'ordivon_capital.portfolio.algebraic_policy',
            'ordivon_capital.portfolio.multistage_policy',
        ) or fullname.split('.')[0] in ('numpy', 'scipy'):
            raise ImportError('solver unavailable: ' + fullname)
sys.meta_path.insert(0, NoSolvers())
from ordivon_capital.portfolio.information_tree import (
    InformationNode, MultistageProblem, validate_information_tree,
)
r = InformationNode('r', None, 0, 1, initial_margin=(.5,), turnover_cost=(0,))
l = InformationNode('l', 'r', 1, 1, risky_gross=(1.1,), maintenance=(.3,), terminal=True)
assert validate_information_tree(MultistageProblem(2, (r,l))).months == 1
"""
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=False,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert result.returncode == 0, result.stderr

def test_shared_policy_error_preserves_existing_consumer_identity():
    from ordivon_capital.portfolio.policy_contract import (
        AlgebraicPolicyError as CanonicalError,
    )
    from ordivon_capital.portfolio.policy_contract import finite_economic_number

    assert CanonicalError is AlgebraicPolicyError
    assert all(finite_economic_number(x) for x in (0, -1, 1.25, 5e-324))
    assert not any(finite_economic_number(x) for x in (
        True, False, "1.0", None, float("nan"), float("inf"), 10**400,
    ))

@pytest.mark.parametrize("gamma", (1.0, 0.9999999999999999, 1.0000000000000002, 1.000000000001, 2.0))
def test_crra_deterministic_cash_certainty_equivalent_is_terminal_wealth(gamma):
    # With a strictly inferior risky return, the all-cash optimum is 0.5r.
    # A certainty equivalent of a deterministic outcome cannot depend on gamma.
    single = solve_one_period(OnePeriodProblem(
        gamma, (1.,), (0.,), (0.,),
        (Scenario(1., (.4,), .5, .6, (.3,)),),
    ))
    multi = solve_multistage(MultistageProblem(
        gamma, (
            root(margin=1.),
            terminal("only", "root", 1, 1., .4, cash=.5, debt=.6),
        ),
    ))
    assert single.expected_equity == pytest.approx(.5, abs=1e-12)
    assert multi.expected_terminal_r == pytest.approx(.5, abs=1e-12)
    assert single.certainty_equivalent == pytest.approx(.5, abs=1e-12, rel=0)
    assert multi.certainty_equivalent_terminal_r == pytest.approx(.5, abs=1e-12, rel=0)
    assert multi.certainty_equivalent_disposable_r == pytest.approx(.5, abs=1e-12, rel=0)

def test_nonfinite_supporting_hyperplane_is_not_zero_gap(monkeypatch):
    from types import SimpleNamespace

    import numpy as np
    import scipy.optimize

    # All-cash is strictly feasible, so the only linprog call is the
    # supporting-hyperplane certificate. A reported success with NaN is
    # deliberately not a certificate of zero global optimality gap.
    def nonfinite_certificate(c, *args, **kwargs):
        return SimpleNamespace(success=True, x=np.full(len(c), np.nan), message="injected")

    monkeypatch.setattr(scipy.optimize, "linprog", nonfinite_certificate)
    problem = MultistageProblem(2., (
        root(margin=1.),
        terminal("only", "root", 1, 1., .4, cash=.5, debt=.6),
    ))
    with pytest.raises(AlgebraicPolicyError, match="nonfinite upper optimality bound"):
        solve_multistage(problem)
