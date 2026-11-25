from dataclasses import replace
from fractions import Fraction

import pytest

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage
from ordivon_capital.portfolio.optimality_evidence import certify_canonical_gap
from ordivon_capital.portfolio.witness_repair import (
    repair_canonical_witness,
    verify_repaired_witness,
)


def _problem(gamma=2.0):
    return MultistageProblem(
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


def test_repair_distinct_witness_and_budget():
    problem = _problem()
    raw = {"root": (1.0000000000000002,)}
    original = certify_canonical_gap(problem, raw, (0.0,) * 6, (0.0,), 0.0)
    assert original.reason == "INEXACT_WITNESS"
    result = repair_canonical_witness(problem, raw, (0.0,) * 6, (0.0,), 0.0, max_change_r=2**-40)
    assert result.standing == "VERIFIED_DISTINCT_CANONICAL_WITNESS"
    assert raw == {"root": (1.0000000000000002,)}
    assert result.repaired_policy != raw
    assert result.repaired_policy["root"][0] <= 1.0
    assert result.source_evidence == original
    delta = abs(Fraction(raw["root"][0]) - Fraction(result.repaired_policy["root"][0]))
    assert 0 < delta <= Fraction(result.max_observed_change_r) <= Fraction(result.max_change_r)
    assert verify_repaired_witness(problem, raw, result)
    assert not verify_repaired_witness(problem, {"root": (1.0,)}, result)
    assert not verify_repaired_witness(problem, raw, replace(result, max_observed_change_r=0.0))
    assert not verify_repaired_witness(problem, raw, replace(result, problem_sha256="0" * 64))
    assert not verify_repaired_witness(problem, raw, replace(result, repaired_policy=raw))
    assert not verify_repaired_witness(
        problem,
        raw,
        replace(
            result,
            canonical_evidence=replace(
                result.canonical_evidence, certified_canonical_gap_upper=0.0
            ),
        ),
    )


@pytest.mark.parametrize("budget", (0.0, 2**-54))
def test_insufficient_budget_stays_unknown(budget):
    result = repair_canonical_witness(
        _problem(), {"root": (1.0000000000000002,)}, (0.0,) * 6, (0.0,), 0.0, max_change_r=budget
    )
    assert result.standing == "UNKNOWN"
    assert result.repaired_policy is None
    assert result.canonical_evidence is None


def test_no_anchor_terminal_claim_and_fractional_gamma():
    p = replace(_problem(), terminal_liabilities_r={"leaf": 1.125})
    r = repair_canonical_witness(p, {"root": (1.0,)}, (0.0,) * 6, (0.0,), 0.0, max_change_r=2**-40)
    assert r.standing == "UNKNOWN" and r.canonical_evidence is None
    r = repair_canonical_witness(
        _problem(0.3), {"root": (1.0,)}, (0.0,) * 6, (0.0,), 0.0, max_change_r=2**-40
    )
    assert r.standing == "UNKNOWN" and r.reason == "SOURCE_NOT_REPAIRABLE"


def test_solver_keeps_original_result_and_optional_distinct_receipt():
    problem = _problem()
    baseline = solve_multistage(problem)
    result = solve_multistage(problem, witness_repair_max_change_r=2**-40)
    assert result.root_risky_r == baseline.root_risky_r
    assert result.optimality_evidence == baseline.optimality_evidence
    assert result.node_decisions_r == baseline.node_decisions_r
    assert baseline.witness_repair is None
    if result.optimality_evidence.reason == "INEXACT_WITNESS":
        assert verify_repaired_witness(
            problem, {"root": result.root_risky_r}, result.witness_repair
        )


@pytest.mark.parametrize("depth,gamma", ((2, 2.0), (3, 1.0), (3, 2.0), (4, 1.0), (4, 2.0)))
def test_actual_prior_unknown_contracts_repair_as_separate_witness(depth, gamma):
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
    problem = MultistageProblem(gamma, tuple(nodes))
    solved = solve_multistage(problem, witness_repair_max_change_r=2**-40)
    source = {k: v["assetExposuresR"] for k, v in solved.node_decisions_r.items()}
    assert solved.optimality_evidence.reason == "INEXACT_WITNESS"
    assert solved.optimality_evidence.certified_canonical_gap_upper is None
    repair = solved.witness_repair
    assert repair.standing == "VERIFIED_DISTINCT_CANONICAL_WITNESS"
    assert 0 < repair.max_observed_change_r <= 2**-40
    assert verify_repaired_witness(problem, source, repair)
    assert verify_repaired_witness(
        replace(problem, nodes=tuple(reversed(problem.nodes))), source, repair
    )


def test_cli_opt_in_receipt_preserves_original_solver_fields():
    import json
    import os
    import subprocess
    import sys
    from dataclasses import asdict
    from pathlib import Path

    from ordivon_capital.portfolio.optimality_evidence import DualProposal, OptimalityEvidence
    from ordivon_capital.portfolio.witness_repair import WitnessRepair

    problem = _problem()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    cmd = [sys.executable, "-m", "ordivon_capital.portfolio.multistage_policy"]
    payload = json.dumps(asdict(problem))
    baseline = json.loads(
        subprocess.run(
            cmd, input=payload, env=env, text=True, capture_output=True, check=True
        ).stdout
    )["solution"]
    result = json.loads(
        subprocess.run(
            [*cmd, "--witness-repair-max-change-r", str(2**-40)],
            input=payload,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
    )["solution"]
    receipt = result.pop("witness_repair")
    assert baseline.pop("witness_repair") is None
    assert result == baseline
    assert receipt["standing"] == "VERIFIED_DISTINCT_CANONICAL_WITNESS"
    receipt["source_evidence"] = OptimalityEvidence(**receipt["source_evidence"])
    cert = receipt["canonical_evidence"]
    proposal = cert["dual_proposal"]
    cert["dual_proposal"] = DualProposal(
        tuple(proposal["inequality_marginals"]), tuple(proposal["equality_marginals"])
    )
    receipt["canonical_evidence"] = OptimalityEvidence(**cert)
    receipt["repaired_policy"] = {k: tuple(v) for k, v in receipt["repaired_policy"].items()}
    assert verify_repaired_witness(
        problem, {"root": tuple(result["root_risky_r"])}, WitnessRepair(**receipt)
    )


@pytest.mark.parametrize("budget", (-1.0, float("inf"), float("nan"), True))
def test_malformed_budget_is_rejected_before_optimizer(budget):
    from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError

    with pytest.raises(AlgebraicPolicyError, match="repair budget"):
        solve_multistage(_problem(), witness_repair_max_change_r=budget)
