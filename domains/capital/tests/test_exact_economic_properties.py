"""Generated independent economic oracles, not solver/checker self-agreement."""

from dataclasses import replace
from fractions import Fraction as Q

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.optimality_evidence import (
    certify_canonical_gap,
    verify_canonical_gap_claim,
)
from ordivon_capital.portfolio.rational_enclosure import enclose_inverse_power


@st.composite
def contracts(draw):
    assets = draw(st.integers(1, 4))
    branches = draw(st.sampled_from((1, 2)))
    due = Q(draw(st.integers(0, 4)), 8)
    gross = tuple(
        tuple(Q(v, 8) for v in draw(st.lists(st.integers(4, 16), min_size=assets, max_size=assets)))
        for _ in range(branches)
    )
    liabilities = tuple(
        Q(v, 32) for v in draw(st.lists(st.integers(0, 4), min_size=branches, max_size=branches))
    )
    weights = draw(st.lists(st.integers(0, 8), min_size=assets, max_size=assets))
    # Dyadic coordinates whose sum is bounded by funded equity, without assume.
    divisor = 2 ** max(3, sum(weights).bit_length())
    risky = tuple((1 - due) * Q(w, divisor) for w in weights)
    probability = Q(draw(st.integers(1, 7)), 8) if branches == 2 else Q(1)
    probabilities = (probability, 1 - probability) if branches == 2 else (probability,)
    root = InformationNode(
        "root", None, 0, 1.0, initial_margin=(1.0,) * assets, turnover_cost=(0.0,) * assets
    )
    nodes = (
        root,
        *(
            InformationNode(
                str(i),
                "root",
                1,
                float(p),
                risky_gross=tuple(map(float, g)),
                cash_gross=1.0,
                debt_gross=1.125,
                maintenance=(0.25,) * assets,
                terminal=True,
                observed_label=str(i),
            )
            for i, (p, g) in enumerate(zip(probabilities, gross, strict=True))
        ),
    )
    problem = MultistageProblem(
        2.0,
        nodes,
        terminal_liabilities_r={str(i): float(v) for i, v in enumerate(liabilities)},
        node_outflow_after_contribution_r={"root": float(due)},
    )
    # Count explicit inequalities from economic meaning, not proof dimensions.
    rows = 2 * branches + 2 * assets + 1 + branches
    dual = tuple(draw(st.lists(st.integers(-8, 8), min_size=rows, max_size=rows)))
    eq = (draw(st.integers(-8, 8)),)
    return problem, risky, due, gross, liabilities, probabilities, dual, eq


@settings(max_examples=160, derandomize=True, deadline=None)
@given(case=contracts(), method=st.sampled_from(("LEGACY_V1", "STRUCTURED_V2")))
def test_exact_bound_dominates_independent_feasible_economic_oracle(case, method):
    problem, risky, due, gross, liabilities, probabilities, dual, eq = case
    equity = 1 - due
    raw = {"root": tuple(map(float, risky))}
    claim = certify_canonical_gap(problem, raw, dual, eq, 0.0, cap_method=method)
    assert claim.certified_canonical_gap_upper is not None
    assert verify_canonical_gap_claim(problem, raw, claim)
    assert claim == certify_canonical_gap(
        replace(problem, nodes=tuple(reversed(problem.nodes))),
        raw,
        dual,
        eq,
        0.0,
        cap_method=method,
    )

    def utility(positions):
        cash = equity - sum(positions)
        return sum(
            p * (1 - 1 / (cash + sum(a * b for a, b in zip(positions, g, strict=True)) - liability))
            for p, g, liability in zip(probabilities, gross, liabilities, strict=True)
        )

    # Exact single-branch optimum at a simplex vertex; with multiple branches,
    # vertices and convex combinations are feasible lower bounds on optimum.
    n = len(risky)
    competitors = [(Q(0),) * n]
    for j in range(n):
        for k in range(1, 9):
            competitors.append(tuple(equity * Q(k, 8) if i == j else Q(0) for i in range(n)))
    for j in range(n):
        for k in range(j + 1, n):
            competitors.append(tuple(equity / 2 if i in (j, k) else Q(0) for i in range(n)))
    lower = max(map(utility, competitors)) - utility(risky)
    assert Q(claim.certified_canonical_gap_upper) >= lower


@settings(max_examples=100, derandomize=True, deadline=None)
@given(bits=st.integers(1, 1024), exponent=st.sampled_from((Q(1, 16), Q(3, 2), Q(2), Q(15, 2))))
def test_dyadic_budget_boundary_and_independent_integer_power_oracle(bits, exponent):
    wealth = Q(1, 1 << bits)
    budget = exponent.numerator * (bits + 1) + 96 * exponent.denominator
    assert enclose_inverse_power(wealth, exponent, max_bits=budget - 1) is None
    lo, hi = enclose_inverse_power(wealth, exponent, max_bits=budget)
    power = wealth ** (-exponent.numerator)
    assert lo**exponent.denominator <= power <= hi**exponent.denominator
    assert hi - lo <= Q(1, 2**96)
