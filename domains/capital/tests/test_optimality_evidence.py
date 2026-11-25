"""Exact witness and untrusted LP proposals: economic, not file-shape, tests."""

from dataclasses import asdict, replace
from decimal import Decimal, localcontext
from fractions import Fraction
from math import inf, nan, nextafter

import pytest

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage
from ordivon_capital.portfolio.optimality_evidence import (
    DualProposal,
    OptimalityEvidence,
    certify_canonical_gap,
    verify_canonical_gap_claim,
)


def _deterministic(gamma=1.0, gross=1.0000000001):
    return MultistageProblem(
        gamma,
        (
            InformationNode("root", None, 0, 1.0, initial_margin=(1.0,), turnover_cost=(0.0,)),
            InformationNode(
                "leaf",
                "root",
                1,
                1.0,
                risky_gross=(gross,),
                cash_gross=1.0,
                debt_gross=1.1,
                maintenance=(0.3,),
                terminal=True,
            ),
        ),
    )


@pytest.mark.parametrize("gamma", (1.0, 2.0, 5.0))
def test_near_tie_analytic_optimum_is_not_a_false_zero_certificate(gamma):
    problem = _deterministic(gamma)
    result = solve_multistage(problem)
    evidence = result.optimality_evidence
    with localcontext() as ctx:
        ctx.prec = 80
        gross = Decimal.from_float(problem.nodes[1].risky_gross[0])
        exact = gross.ln() if gamma == 1.0 else (gross ** (1 - int(gamma)) - 1) / (1 - int(gamma))
        # For the actual all-cash numerical candidate, canonical utility is 0.
        assert result.root_risky_r == (0.0,)
        assert result.concavity_global_utility_gap_upper == 0.0
        assert evidence.numerical_tangent_gap_estimate == 0.0
        assert Decimal.from_float(evidence.certified_canonical_gap_upper) >= exact > 0
    assert verify_canonical_gap_claim(problem, {"root": result.root_risky_r}, evidence)
    assert not verify_canonical_gap_claim(
        problem, {"root": result.root_risky_r}, replace(evidence, certified_canonical_gap_upper=0.0)
    )


@pytest.mark.parametrize(
    "y,lam",
    (
        ((0.0,) * 5, (0.0,)),
        ((1.0, -2.0, 3.0, -4.0, 5.0), (-1.0,)),
        ((-1e5,) * 5, (2e5,)),
    ),
)
def test_arbitrary_dual_proposals_are_corrected_over_proven_finite_box(y, lam):
    problem = _deterministic(2.0, 1.125)
    # 3 node constraints (buy,sell,initial), edge margin, arrival, terminal:
    # explicitly account for both edge constraints in the native LP.
    y = (*y, 0.0)
    evidence = certify_canonical_gap(problem, {"root": (0.0,)}, y, lam, 0.0)
    assert evidence.standing == "EXACT_RATIONAL_CANONICAL_WITNESS_GAP_UPPER"
    optimum = 1 - Fraction(1, 1) / Fraction(1.125)
    assert Fraction(evidence.certified_canonical_gap_upper) >= optimum
    assert verify_canonical_gap_claim(problem, {"root": (0.0,)}, evidence)


def test_receipt_roundtrip_and_tampered_dual():
    problem = _deterministic()
    result = solve_multistage(problem)
    original = result.optimality_evidence
    raw = asdict(original)
    raw["dual_proposal"] = DualProposal(**raw["dual_proposal"])
    claim = OptimalityEvidence(**raw)
    assert verify_canonical_gap_claim(problem, {"root": result.root_risky_r}, claim)
    forged = replace(claim, dual_proposal=DualProposal((0.0,) * 6, (0.0,)))
    assert not verify_canonical_gap_claim(problem, {"root": result.root_risky_r}, forged)


@pytest.mark.parametrize(
    "gamma,policy,reason",
    (
        (0.5, {"root": (0.0,)}, "INTEGER_GAMMA_1_TO_16_ONLY"),
        (17.0, {"root": (0.0,)}, "INTEGER_GAMMA_1_TO_16_ONLY"),
        (2.0, {"root": (nextafter(1.0, inf),)}, "INEXACT_WITNESS"),
        (2.0, {"root": (nan,)}, "INEXACT_WITNESS"),
        (2.0, {"root": (-0.01,)}, "INEXACT_WITNESS"),
        (2.0, {}, "INEXACT_WITNESS"),
    ),
)
def test_unknown_never_acquires_a_certified_bound(gamma, policy, reason):
    proof = certify_canonical_gap(_deterministic(gamma), policy, (0.0,) * 6, (0.0,), 0.0)
    assert proof.standing == "UNKNOWN"
    assert proof.reason == reason
    assert proof.certified_canonical_gap_upper is None
    assert proof.dual_proposal is None


@pytest.mark.parametrize("bad", (None, (0.0,), (nan,) * 6, (inf,) * 6))
def test_bad_dual_proposal_never_becomes_certificate(bad):
    proof = certify_canonical_gap(_deterministic(), {"root": (0.0,)}, bad, (0.0,), 0.0)
    assert proof.standing == "UNKNOWN"
    assert proof.reason == "MALFORMED_DUAL_PROPOSAL"


def test_fractional_solver_still_returns_numeric_result_without_claiming_exactness():
    result = solve_multistage(_deterministic(0.5))
    assert result.optimality_evidence.standing == "UNKNOWN"
    assert result.optimality_evidence.certified_canonical_gap_upper is None


def test_two_period_deterministic_liability_contract_bounds_analytic_optimum():
    # One risk asset, 100% initial margin, no fees and costly debt.
    # At each period the strictly superior risky asset is the exact optimum.
    problem = MultistageProblem(
        1.0,
        (
            InformationNode("root", None, 0, 1.0, initial_margin=(1.0,), turnover_cost=(0.0,)),
            InformationNode(
                "middle",
                "root",
                1,
                1.0,
                risky_gross=(1.125,),
                cash_gross=1.0,
                debt_gross=1.5,
                maintenance=(0.25,),
                initial_margin=(1.0,),
                turnover_cost=(0.0,),
            ),
            InformationNode(
                "leaf",
                "middle",
                2,
                1.0,
                risky_gross=(1.25,),
                cash_gross=1.0,
                debt_gross=1.5,
                maintenance=(0.25,),
                terminal=True,
            ),
        ),
        terminal_liabilities_r={"leaf": 0.25},
        node_outflow_after_contribution_r={"root": 0.0, "middle": 0.25},
    )
    policy = {"root": (0.0,), "middle": (0.0,)}
    proof = certify_canonical_gap(problem, policy, (0.0,) * 11, (0.0,) * 2, 0.0)
    # 2 nodes*3 inequalities + 2 maintenance + 2 arrival + 1 terminal.
    assert proof.standing == "EXACT_RATIONAL_CANONICAL_WITNESS_GAP_UPPER"
    with localcontext() as ctx:
        ctx.prec = 80
        optimum = ((Decimal("1.125") + Decimal(".75")) * Decimal("1.25") - Decimal(".25")).ln()
        witness = Decimal("1.5").ln()
        assert Decimal.from_float(proof.certified_canonical_gap_upper) >= optimum - witness > 0
    assert verify_canonical_gap_claim(problem, policy, proof)


def test_native_json_receipt_is_replayable_without_optimizer():
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    problem = _deterministic()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    native = subprocess.run(
        [sys.executable, "-m", "ordivon_capital.portfolio.multistage_policy"],
        input=json.dumps(asdict(problem)),
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    solution = json.loads(native.stdout)["solution"]
    payload = solution["optimality_evidence"]
    proposal = payload["dual_proposal"]
    payload["dual_proposal"] = DualProposal(
        tuple(proposal["inequality_marginals"]), tuple(proposal["equality_marginals"])
    )
    claim = OptimalityEvidence(**payload)
    assert verify_canonical_gap_claim(problem, {"root": tuple(solution["root_risky_r"])}, claim)
    # This verifier has no need for either numerical carrier in a fresh process.
    code = """
import sys
from importlib.abc import MetaPathFinder
class BlockNumerical(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy','scipy'}:
            raise ImportError(fullname)
sys.meta_path.insert(0,BlockNumerical())
from ordivon_capital.portfolio.optimality_evidence import certify_canonical_gap
from ordivon_capital.portfolio.information_tree import InformationNode,MultistageProblem
p=MultistageProblem(1.,(InformationNode('root',None,0,1.,initial_margin=(1.,),turnover_cost=(0.,)),InformationNode('leaf','root',1,1.,risky_gross=(1.125,),maintenance=(.25,),terminal=True)))
assert certify_canonical_gap(p,{'root':(0.,)},(0.,)*6,(0.,),0.).certified_canonical_gap_upper >= .125
"""
    subprocess.run([sys.executable, "-c", code], env=env, check=True)


def test_exact_verification_resource_scope_is_not_economic_rejection():
    nodes = [InformationNode("root", None, 0, 1.0, initial_margin=(1.0,), turnover_cost=(0.0,))]
    parent = "root"
    for t in range(1, 64):
        key = f"n{t}"
        term = t == 63
        nodes.append(
            InformationNode(
                key,
                parent,
                t,
                1.0,
                risky_gross=(1.0,),
                maintenance=(0.25,),
                initial_margin=() if term else (1.0,),
                turnover_cost=() if term else (0.0,),
                terminal=term,
            )
        )
        parent = key
    problem = MultistageProblem(1.0, tuple(nodes))
    proof = certify_canonical_gap(problem, {}, (), (), 0.0)
    assert proof.standing == "UNKNOWN"
    assert proof.reason == "EXACT_WITNESS_RESOURCE_SCOPE"
    assert proof.certified_canonical_gap_upper is None


def test_liability_exhausting_terminal_wealth_invalidates_exact_witness():
    # Zero risky position and 1r cash exactly meet the terminal liability.
    # A different policy may be feasible; this witness is not.
    problem = replace(_deterministic(2.0, 1.125), terminal_liabilities_r={"leaf": 1.0})
    proof = certify_canonical_gap(problem, {"root": (0.0,)}, (0.0,) * 6, (0.0,), 0.0)
    assert proof.standing == "UNKNOWN"
    assert proof.reason == "INEXACT_WITNESS"
    assert proof.certified_canonical_gap_upper is None


def test_outflow_and_turnover_cannot_be_ignored_by_exact_margin_witness():
    # The risky cap alone admits .75, but a .5 outflow and .125 fee per
    # risky unit leave insufficient equity for a 100% initial margin.
    original = _deterministic(2.0, 1.125)
    problem = replace(
        original,
        nodes=(replace(original.nodes[0], turnover_cost=(0.125,)), original.nodes[1]),
        node_outflow_after_contribution_r={"root": 0.5},
    )
    proof = certify_canonical_gap(problem, {"root": (0.75,)}, (0.0,) * 6, (0.0,), 0.0)
    assert proof.standing == "UNKNOWN"
    assert proof.reason == "INEXACT_WITNESS"
