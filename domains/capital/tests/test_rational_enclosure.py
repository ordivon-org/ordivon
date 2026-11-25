"""Exact independent enclosure oracles and real scenario certificates."""

from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction as Q

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage
from ordivon_capital.portfolio.optimality_evidence import (
    certify_canonical_gap,
    verify_canonical_gap_claim,
)
from ordivon_capital.portfolio.rational_enclosure import (
    enclose_inverse_power,
    enclose_rational,
)
from ordivon_capital.portfolio.witness_repair import verify_repaired_witness


@settings(max_examples=256, derandomize=True, deadline=None)
@given(
    value=st.fractions(min_value=-(10**9), max_value=10**9, max_denominator=10**9),
    wealth=st.fractions(min_value=Q(1, 10**6), max_value=10**6, max_denominator=10**6),
    numerator=st.integers(1, 64),
    denominator=st.sampled_from((4, 8, 16)),
)
def test_signed_rational_rounding_and_exact_power_enclosures(value, wealth, numerator, denominator):
    lo, hi = enclose_rational(value)
    assert lo <= value <= hi and hi - lo <= Q(1, 2**96)
    gamma = Q(numerator, denominator)
    lo, hi = enclose_inverse_power(wealth, gamma, max_bits=16384)
    exact = wealth ** (-gamma.numerator)
    assert 0 <= lo <= hi and hi - lo <= Q(1, 2**96)
    assert lo**gamma.denominator <= exact <= hi**gamma.denominator


def test_scope_is_explicit_and_no_fake_bound():
    assert enclose_inverse_power(Q(1, 3), Q(1, 3), max_bits=16384) is None
    assert enclose_inverse_power(Q(1, 3), Q(1, 32), max_bits=16384) is None
    assert enclose_inverse_power(Q(1, 2**1000), Q(31, 2), max_bits=16384) is None
    assert enclose_inverse_power(Q(0), Q(1, 2), max_bits=16384) is None


@pytest.mark.parametrize("gamma", (0.0625, 0.5, 0.75, 1.5, 2.5, 15.5))
def test_fractional_dyadic_tangent_bounds_independent_analytic_optimum(gamma):
    p = MultistageProblem(
        gamma,
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
    e = certify_canonical_gap(p, {"root": (0.0,)}, (0.0,) * 6, (0.0,), 0.0)
    assert e.standing == "EXACT_RATIONAL_CANONICAL_WITNESS_GAP_UPPER"
    assert e.reason == "EXACT_DYADIC_GRADIENT_ENCLOSURE_AND_CANONICAL_WITNESS"
    with localcontext() as ctx:
        ctx.prec = 100
        power = 1 - Decimal.from_float(gamma)
        true_optimum = ((power * Decimal("1.125").ln()).exp() - 1) / power
        assert Decimal.from_float(e.certified_canonical_gap_upper) >= true_optimum > 0
    assert verify_canonical_gap_claim(p, {"root": (0.0,)}, e)
    assert not verify_canonical_gap_claim(
        p, {"root": (0.0,)}, replace(e, certified_canonical_gap_upper=0.0)
    )


def fixture(depth, gamma):
    nodes = [InformationNode("root", None, 0, 1.0, initial_margin=(0.8,), turnover_cost=(0.002,))]
    level = ["root"]
    for t in range(1, depth + 1):
        nxt = []
        for parent in level:
            for label, g, p in (("a", 0.85, 0.4), ("b", 1.22, 0.6)):
                key = parent + label
                term = t == depth
                nodes.append(
                    InformationNode(
                        key,
                        parent,
                        t,
                        p,
                        risky_gross=(g,),
                        cash_gross=1.01,
                        debt_gross=1.03,
                        maintenance=(0.3,),
                        initial_margin=() if term else (0.8,),
                        turnover_cost=() if term else (0.002,),
                        terminal=term,
                        observed_label=label,
                    )
                )
                nxt.append(key)
        level = nxt
    return MultistageProblem(gamma, tuple(nodes))


@pytest.mark.parametrize("depth,gamma", ((4, 5.0), (5, 2.0), (5, 5.0)))
def test_prior_bit_budget_cases_now_have_enclosed_certificates(depth, gamma):
    p = fixture(depth, gamma)
    r = solve_multistage(p, witness_repair_max_change_r=2**-40)
    raw = {k: v["assetExposuresR"] for k, v in r.node_decisions_r.items()}
    e = r.optimality_evidence
    if e.certified_canonical_gap_upper is not None:
        assert e.reason == "EXACT_DYADIC_GRADIENT_ENCLOSURE_AND_CANONICAL_WITNESS"
        assert verify_canonical_gap_claim(p, raw, e)
    else:
        assert e.reason == "INEXACT_WITNESS"
        assert r.witness_repair.standing == "VERIFIED_DISTINCT_CANONICAL_WITNESS"
        assert verify_repaired_witness(p, raw, r.witness_repair)
        e = r.witness_repair.canonical_evidence
        raw = r.witness_repair.repaired_policy
    proposal = e.dual_proposal
    old = certify_canonical_gap(
        p,
        raw,
        proposal.inequality_marginals,
        proposal.equality_marginals,
        e.numerical_tangent_gap_estimate,
        gradient_method="RATIONAL",
    )
    assert old.reason == "EXACT_WITNESS_RESOURCE_SCOPE"
    assert e.certified_canonical_gap_upper is not None


def test_legacy_rational_proof_replay_survives_new_enclosure_default():
    p = fixture(4, 2.0)
    r = solve_multistage(p, witness_repair_max_change_r=2**-40)
    raw = {k: v["assetExposuresR"] for k, v in r.node_decisions_r.items()}
    repair = r.witness_repair
    assert repair is not None
    e = repair.canonical_evidence
    proposal = e.dual_proposal
    old = certify_canonical_gap(
        p,
        repair.repaired_policy,
        proposal.inequality_marginals,
        proposal.equality_marginals,
        e.numerical_tangent_gap_estimate,
        gradient_method="RATIONAL",
    )
    assert old.certified_canonical_gap_upper is not None
    assert e.certified_canonical_gap_upper >= old.certified_canonical_gap_upper
    assert verify_canonical_gap_claim(p, repair.repaired_policy, old)
    assert verify_repaired_witness(p, raw, replace(repair, canonical_evidence=old))


def test_coarse_interval_correction_dominates_exact_rational_dual_bound(monkeypatch):
    # Coarsen the grid only in a test so losing the correction is observable
    # rather than hidden below binary64 output rounding.
    import ordivon_capital.portfolio.rational_enclosure as enclosure

    monkeypatch.setattr(enclosure, "DYADIC_FRACTION_BITS", 0)
    monkeypatch.setattr(enclosure, "_SCALE", 1)
    p = fixture(1, 2.0)
    raw = {"root": (0.25,)}
    exact = certify_canonical_gap(p, raw, (0.0,) * 9, (0.0,), 0.0, gradient_method="RATIONAL")
    interval = certify_canonical_gap(p, raw, (0.0,) * 9, (0.0,), 0.0, gradient_method="DYADIC")
    assert exact.certified_canonical_gap_upper is not None
    assert interval.certified_canonical_gap_upper is not None
    assert interval.certified_canonical_gap_upper >= exact.certified_canonical_gap_upper
