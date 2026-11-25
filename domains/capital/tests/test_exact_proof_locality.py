"""Proof generation and replay share strict admission and sparse locality."""

from dataclasses import replace
from fractions import Fraction
from unittest.mock import patch

import pytest

from ordivon_capital.portfolio import optimality_evidence as proof
from ordivon_capital.portfolio.information_tree import (
    InformationNode,
    MultistageProblem,
    validate_information_tree,
)
from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError


def contract(depth=1, fanout=2, assets=1, gamma=2.0):
    nodes = [
        InformationNode(
            "root", None, 0, 1.0, initial_margin=(1.0,) * assets, turnover_cost=(0.0,) * assets
        )
    ]
    level = ["root"]
    for t in range(1, depth + 1):
        nxt = []
        for parent in level:
            for i in range(fanout):
                key = f"{parent}:{i}"
                term = t == depth
                nodes.append(
                    InformationNode(
                        key,
                        parent,
                        t,
                        1.0 / fanout,
                        risky_gross=tuple(
                            1.03125 + i * 0.03125 + j * 0.015625 for j in range(assets)
                        ),
                        cash_gross=1.0,
                        debt_gross=1.125,
                        maintenance=(0.25,) * assets,
                        initial_margin=() if term else (1.0,) * assets,
                        turnover_cost=() if term else (0.0,) * assets,
                        terminal=term,
                        observed_label=str(i),
                    )
                )
                nxt.append(key)
        level = nxt
    p = MultistageProblem(
        gamma,
        tuple(nodes),
        terminal_liabilities_r={n.id: 0.0625 for n in nodes if n.terminal},
        node_outflow_after_contribution_r={n.id: 0.03125 for n in nodes if not n.terminal},
    )
    tree = validate_information_tree(p)
    raw = {n.id: (0.125,) * assets for n in tree.decision}
    dims = proof.proof_dual_dimensions(tree)
    assert dims is not None
    return p, raw, (0.0,) * dims[0], (0.0,) * dims[1]


@pytest.mark.parametrize("bad", (float("nan"), float("inf"), -1.0, True, "0", None))
def test_invalid_estimate_rejected_before_dual_read(bad):
    p, raw, _, _ = contract()

    class NoRead:
        def __iter__(self):
            raise AssertionError("invalid estimate must reject before proof work")

    with pytest.raises(AlgebraicPolicyError, match="finite nonnegative numerical estimate"):
        proof.certify_canonical_gap(p, raw, NoRead(), NoRead(), bad)


@pytest.mark.parametrize("method", ("RATIONAL", "DYADIC"))
def test_gradient_budget_only_inspects_updated_sparse_coordinates(method):
    p, raw, y, lam = contract(depth=4, assets=2)
    counts = []
    original = proof._within_bit_budget

    def observed(values):
        items = tuple(values)
        counts.append(len(items))
        return original(items)

    with patch.object(proof, "_within_bit_budget", observed):
        claim = proof.certify_canonical_gap(p, raw, y, lam, 0.0, gradient_method=method)
    assert claim.certified_canonical_gap_upper is not None
    # A local decision block checks x, cap, probability: 2*(2*A+2)+1.
    # Every other row check must stay within that same local envelope.
    assert max(counts) <= 13
    assert proof.verify_canonical_gap_claim(p, raw, claim)


@pytest.mark.parametrize(
    "depth,fanout,assets,gamma", [(2, 2, 2, 1.0), (3, 3, 2, 0.75), (5, 2, 3, 2.0), (4, 2, 1, 5.0)]
)
def test_exact_validity_and_forged_bound_rejection(depth, fanout, assets, gamma):
    p, raw, y, lam = contract(depth, fanout, assets, gamma)
    claim = proof.certify_canonical_gap(p, raw, y, lam, 0.0)
    assert claim.certified_canonical_gap_upper > 0.0
    assert proof.verify_canonical_gap_claim(p, raw, claim)
    assert not proof.verify_canonical_gap_claim(
        p, raw, replace(claim, certified_canonical_gap_upper=0.0)
    )


def test_local_budget_detects_overwide_newly_written_fraction():
    # Exercise the new local admission operator independently of the solver.
    assert proof._within_bit_budget((Fraction(1, 2), Fraction(3, 7)))
    assert not proof._within_bit_budget((Fraction(1, 1 << 16384),))


def test_zero_bound_cannot_be_forged_as_false():
    from ordivon_capital.portfolio.multistage_policy import solve_multistage

    p = MultistageProblem(
        1.0,
        (
            InformationNode("root", None, 0, 1.0, initial_margin=(1.0,), turnover_cost=(0.0,)),
            InformationNode(
                "leaf",
                "root",
                1,
                1.0,
                risky_gross=(1.0,),
                cash_gross=1.0,
                debt_gross=1.0,
                maintenance=(0.25,),
                terminal=True,
            ),
        ),
    )
    result = solve_multistage(p)
    raw = {"root": result.root_risky_r}
    e = result.optimality_evidence
    assert e.certified_canonical_gap_upper == 0.0
    assert proof.verify_canonical_gap_claim(p, raw, e)
    assert not proof.verify_canonical_gap_claim(
        p, raw, replace(e, certified_canonical_gap_upper=False)
    )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {"root": None},
        {"root": [0.125]},
        {"root": (0.125,), "other": (0.125,)},
        {"root": (False,)},
        ["root"],
    ],
)
def test_malformed_risky_policy_is_unknown_not_untyped_exception(bad):
    p, raw, y, lam = contract()
    e = proof.certify_canonical_gap(p, bad, y, lam, 0.0)
    assert e.reason == "INEXACT_WITNESS"
    assert e.certified_canonical_gap_upper is None


def test_new_gradient_bit_overflow_rejected_before_dual_read():
    p, raw, _, _ = contract(gamma=0.75)

    class NoRead:
        def __iter__(self):
            raise AssertionError("unqualified gradient must not read duals")

    with patch.object(
        proof, "enclose_rational", return_value=(Fraction(1 << 16384), Fraction(1 << 16384))
    ):
        e = proof.certify_canonical_gap(p, raw, NoRead(), NoRead(), 0.0)
    assert e.reason == "EXACT_WITNESS_RESOURCE_SCOPE"
    assert e.certified_canonical_gap_upper is None
