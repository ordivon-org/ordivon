"""Structured proof caps are explicit, exact and independently replayable."""

from dataclasses import replace
from fractions import Fraction as Q

import pytest

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage
from ordivon_capital.portfolio.optimality_evidence import (
    certify_canonical_gap,
    verify_canonical_gap_claim,
)
from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError


def contract(gamma=2.0):
    return MultistageProblem(
        gamma,
        (
            InformationNode(
                "root", None, 0, 1.0, initial_margin=(0.5, 0.75), turnover_cost=(0.0, 0.0)
            ),
            InformationNode(
                "leaf",
                "root",
                1,
                1.0,
                risky_gross=(1.125, 1.25),
                cash_gross=1.0,
                debt_gross=1.0625,
                maintenance=(0.25, 0.25),
                terminal=True,
            ),
        ),
        terminal_liabilities_r={"leaf": 0.125},
        node_outflow_after_contribution_r={"root": 0.125},
    )


@pytest.mark.parametrize("gamma", [2.0, 0.75])
def test_new_version_explicit_and_legacy_receipt_replays(gamma):
    p = contract(gamma)
    raw = {"root": (0.125, 0.125)}
    y = (0.0,) * 8
    old = certify_canonical_gap(p, raw, y, (0.0,), 0.0)
    new = certify_canonical_gap(p, raw, y, (0.0,), 0.0, cap_method="STRUCTURED_V2")
    assert old == certify_canonical_gap(p, raw, y, (0.0,), 0.0, cap_method="LEGACY_V1")
    assert old.certified_canonical_gap_upper > new.certified_canonical_gap_upper > 0
    assert new.reason.endswith("_STRUCTURED_CAP_V2")
    assert verify_canonical_gap_claim(p, raw, old)
    assert verify_canonical_gap_claim(p, raw, new)
    assert not verify_canonical_gap_claim(p, raw, replace(new, reason=old.reason))
    assert not verify_canonical_gap_claim(p, raw, replace(old, reason=new.reason))


def test_structured_exact_operator_vertices():
    from ordivon_capital.portfolio.canonical_caps import (
        structured_arrival_cap,
        structured_decision_caps,
    )

    m = (Q(1, 2), Q(3, 4))
    g = (Q(9, 8), Q(5, 4))
    c = Q(7, 8)
    lend = Q(1)
    # independent vertices of the weighted risky simplex.
    vertices = [(Q(0), Q(0)), (c / m[0], Q(0)), (Q(0), c / m[1])]
    oracle = max(
        lend * c + sum((gi - lend) * ri for gi, ri in zip(g, r, strict=True)) for r in vertices
    )
    assert structured_arrival_cap(c, m, g, lend) == oracle
    assert structured_decision_caps(c, m, (Q(1, 4), Q(1, 8))) == (
        c / m[0],
        c / m[1],
        c,
        c,
        c / m[0] + Q(1, 4),
        c / m[1] + Q(1, 8),
    )


def test_unknown_method_before_numerical_effect():
    from unittest.mock import patch

    with patch("scipy.optimize.minimize", side_effect=AssertionError("must not optimize")):
        with pytest.raises(AlgebraicPolicyError, match="cap method"):
            solve_multistage(contract(), cap_method="AUTO")


def test_opt_in_actual_solver_and_historical_default():
    p = contract()
    a = solve_multistage(p)
    b = solve_multistage(p, cap_method="STRUCTURED_V2")
    assert a.node_decisions_r == b.node_decisions_r
    assert a.expected_utility == b.expected_utility
    raw = {k: v["assetExposuresR"] for k, v in b.node_decisions_r.items()}
    assert b.optimality_evidence.reason.endswith("_STRUCTURED_CAP_V2")
    assert verify_canonical_gap_claim(p, raw, b.optimality_evidence)


def test_exact_vertex_and_feasible_financing_differential():
    import random

    from ordivon_capital.portfolio.canonical_caps import (
        structured_arrival_cap,
        structured_decision_caps,
    )

    rng = random.Random(32745)
    for _ in range(512):
        n = rng.randint(1, 6)
        m = tuple(Q(rng.randint(1, 16), 16) for _ in range(n))
        g = tuple(Q(rng.randint(0, 32), 16) for _ in range(n))
        lend = Q(rng.randint(1, 24), 16)
        borrow = lend + Q(rng.randint(0, 8), 16)
        equity = Q(rng.randint(0, 32), 8)
        cap = equity + Q(rng.randint(0, 8), 8)
        weights = [rng.randint(0, 10) for _ in range(n)]
        norm = max(1, sum(weights) + rng.randint(0, 10))
        risky = tuple(equity * Q(w, norm) / mi for w, mi in zip(weights, m, strict=True))
        net = equity - sum(risky)
        simultaneous = Q(rng.randint(0, 8), 8)
        cash = max(Q(0), net) + simultaneous
        debt = max(Q(0), -net) + simultaneous
        actual = sum(a * b for a, b in zip(risky, g, strict=True)) + cash * lend - debt * borrow
        bound = structured_arrival_cap(cap, m, g, lend)
        vertex = max(
            [lend * cap]
            + [lend * cap + (gi - lend) * cap / mi for mi, gi in zip(m, g, strict=True)]
        )
        assert bound == vertex and actual <= bound
        old = tuple(Q(rng.randint(0, 16), 8) for _ in range(n))
        box = structured_decision_caps(cap, m, old)
        actual_turnover = tuple(abs(a - b) for a, b in zip(risky, old, strict=True))
        canonical = (*risky, max(Q(0), net), max(Q(0), -net), *actual_turnover)
        assert all(0 <= a <= b for a, b in zip(canonical, box, strict=True))


def test_distinct_repair_both_methods_and_forged_method():
    from ordivon_capital.portfolio.witness_repair import (
        repair_canonical_witness,
        verify_repaired_witness,
    )

    p = MultistageProblem(
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
                maintenance=(0.25,),
                terminal=True,
            ),
        ),
    )
    p = replace(p, node_outflow_after_contribution_r={"root": 0.125})
    raw = {"root": (0.8750000000000001,)}
    a = repair_canonical_witness(p, raw, (0.0,) * 6, (0.0,), 0.0, max_change_r=2**-40)
    b = repair_canonical_witness(
        p, raw, (0.0,) * 6, (0.0,), 0.0, max_change_r=2**-40, cap_method="STRUCTURED_V2"
    )
    assert a.canonical_evidence is not None and b.canonical_evidence is not None
    assert a.repaired_policy == b.repaired_policy
    assert (
        a.canonical_evidence.certified_canonical_gap_upper
        > b.canonical_evidence.certified_canonical_gap_upper
    )
    assert verify_repaired_witness(p, raw, a)
    assert verify_repaired_witness(p, raw, b)
    assert not verify_repaired_witness(
        p, raw, replace(b, canonical_evidence=replace(b.canonical_evidence, reason=[]))
    )
    assert not verify_repaired_witness(
        p,
        raw,
        replace(
            b, canonical_evidence=replace(b.canonical_evidence, reason=a.canonical_evidence.reason)
        ),
    )


def test_actual_cli_opt_in():
    import json
    import os
    import subprocess
    import sys
    from dataclasses import asdict
    from pathlib import Path

    from ordivon_capital.portfolio.optimality_evidence import DualProposal, OptimalityEvidence

    p = contract()
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    cmd = [
        sys.executable,
        "-m",
        "ordivon_capital.portfolio.multistage_policy",
        "--cap-method",
        "STRUCTURED_V2",
    ]
    out = json.loads(
        subprocess.run(
            cmd, input=json.dumps(asdict(p)), capture_output=True, text=True, check=True, env=env
        ).stdout
    )
    assert out["effectStanding"] == "READ_ONLY_NO_BROKER_NO_PAPER_LEDGER"
    sol = out["solution"]
    e = sol["optimality_evidence"]
    d = e["dual_proposal"]
    e["dual_proposal"] = DualProposal(
        tuple(d["inequality_marginals"]), tuple(d["equality_marginals"])
    )
    raw = {k: tuple(v["assetExposuresR"]) for k, v in sol["node_decisions_r"].items()}
    assert verify_canonical_gap_claim(p, raw, OptimalityEvidence(**e))
