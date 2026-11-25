"""Pure exact preparation, bounded numerical proposal, independent proof."""

from dataclasses import FrozenInstanceError
from fractions import Fraction
from unittest.mock import patch

import pytest

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage
from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError


def contract(depth=1, near=False):
    nodes = [
        InformationNode(
            "root", None, 0, 1.0, initial_margin=(0.85, 0.85), turnover_cost=(0.0015, 0.0015)
        )
    ]
    level = ["root"]
    for t in range(1, depth + 1):
        nxt = []
        for parent in level:
            for i, g in enumerate((0.88, 1.13)):
                key = f"{parent}:{i}"
                terminal = t == depth
                nodes.append(
                    InformationNode(
                        key,
                        parent,
                        t,
                        0.5,
                        risky_gross=(g, g + 0.015 * (i - 1)),
                        cash_gross=1.012,
                        debt_gross=1.04,
                        maintenance=(0.35, 0.35),
                        initial_margin=() if terminal else (0.85, 0.85),
                        turnover_cost=() if terminal else (0.0015, 0.0015),
                        terminal=terminal,
                        observed_label=str(i),
                    )
                )
                nxt.append(key)
        level = nxt
    return MultistageProblem(
        5.0 if near else 2.0,
        tuple(nodes),
        terminal_liabilities_r={n.id: depth - 0.3 if near else 0.125 for n in nodes if n.terminal},
        node_outflow_after_contribution_r={n.id: 0.035 for n in nodes if not n.terminal},
    )


def test_exact_preparation_immutable_and_replay_pure():
    from ordivon_capital.portfolio.optimality_evidence import (
        certify_canonical_gap,
        certify_prepared_gap,
        prepare_canonical_witness,
        verify_canonical_gap_claim,
    )

    p = contract()
    raw = {"root": (0.125, 0.125)}
    with patch(
        "scipy.optimize.linprog", side_effect=AssertionError("no numerical optimizer in proof")
    ):
        a = prepare_canonical_witness(p, raw, cap_method="STRUCTURED_V2")
        with pytest.raises(FrozenInstanceError):
            a.x = ()
        assert isinstance(a.ub, tuple) and isinstance(a.ub[0][0], tuple)
        assert isinstance(a.grad[0], Fraction)
        y = (0.0,) * len(a.ub)
        lam = (0.0,) * len(a.eq)
        e = certify_prepared_gap(a, y, lam, 0.0)
        assert e == certify_canonical_gap(p, raw, y, lam, 0.0, cap_method="STRUCTURED_V2")
        assert verify_canonical_gap_claim(p, raw, e)


def test_unknown_proposal_mode_fails_before_optimizer():
    with patch("scipy.optimize.minimize", side_effect=AssertionError("must not optimize")):
        with pytest.raises(AlgebraicPolicyError, match="dual proposal"):
            solve_multistage(contract(), dual_proposal_method="AUTO")


def test_near_liability_actual_entry_preserves_strategy_and_replays():
    from ordivon_capital.portfolio.optimality_evidence import verify_canonical_gap_claim

    p = contract(5, True)
    a = solve_multistage(p, numerical_solver="TRUST_CONSTR_SPARSE", cap_method="STRUCTURED_V2")
    b = solve_multistage(
        p,
        numerical_solver="TRUST_CONSTR_SPARSE",
        cap_method="STRUCTURED_V2",
        dual_proposal_method="CANONICAL_GRADIENT",
    )
    assert a.node_decisions_r == b.node_decisions_r
    assert a.expected_utility == b.expected_utility
    assert a.concavity_global_utility_gap_upper == b.concavity_global_utility_gap_upper
    raw = {k: v["assetExposuresR"] for k, v in b.node_decisions_r.items()}
    assert (
        b.optimality_evidence.certified_canonical_gap_upper
        < a.optimality_evidence.certified_canonical_gap_upper
    )
    assert b.dual_proposal_standing == "CANONICAL_GRADIENT_SELECTED"
    assert verify_canonical_gap_claim(p, raw, b.optimality_evidence)


def test_proposal_failure_malformed_and_nonimprovement_retain_baseline():
    from types import SimpleNamespace

    from ordivon_capital.portfolio.canonical_dual_proposal import improve_canonical_proposal
    from ordivon_capital.portfolio.optimality_evidence import (
        certify_prepared_gap,
        prepare_canonical_witness,
        verify_canonical_gap_claim,
    )

    p = contract()
    raw = {"root": (0.125, 0.125)}
    prepared = prepare_canonical_witness(p, raw, cap_method="STRUCTURED_V2")
    y = (0.0,) * len(prepared.ub)
    lam = (0.0,) * len(prepared.eq)
    baseline = certify_prepared_gap(prepared, y, lam, 0.0)
    assert baseline.certified_canonical_gap_upper is not None
    for ans, status in (
        (SimpleNamespace(success=False), "BASELINE_RETAINED_PROPOSAL_FAILED"),
        (
            SimpleNamespace(
                success=True,
                ineqlin=SimpleNamespace(marginals=(float("nan"),) * len(y)),
                eqlin=SimpleNamespace(marginals=lam),
            ),
            "BASELINE_RETAINED_MALFORMED_PROPOSAL",
        ),
        (
            SimpleNamespace(
                success=True,
                ineqlin=SimpleNamespace(marginals=y),
                eqlin=SimpleNamespace(marginals=lam),
            ),
            "BASELINE_RETAINED_NO_IMPROVEMENT",
        ),
    ):
        with patch("scipy.optimize.linprog", return_value=ans) as call:
            result, standing = improve_canonical_proposal(prepared, baseline)
        assert call.call_count == 1
        assert result is baseline and standing == status
        assert verify_canonical_gap_claim(p, raw, result)


def test_unknown_witness_does_not_call_proposal_carrier():
    from ordivon_capital.portfolio.canonical_dual_proposal import improve_canonical_proposal
    from ordivon_capital.portfolio.optimality_evidence import (
        certify_prepared_gap,
        prepare_canonical_witness,
    )

    p = contract()
    prepared = prepare_canonical_witness(p, {"root": (-0.125, 0.125)})
    baseline = certify_prepared_gap(prepared, (), (), 0.0)
    with patch("scipy.optimize.linprog", side_effect=AssertionError("no solver")):
        assert improve_canonical_proposal(prepared, baseline) == (
            baseline,
            "BASELINE_NOT_CERTIFIED",
        )


def test_exact_normalization_and_bounded_native_proposal():
    from types import SimpleNamespace

    import numpy as np
    from scipy.sparse import issparse

    from ordivon_capital.portfolio.canonical_dual_proposal import improve_canonical_proposal
    from ordivon_capital.portfolio.optimality_evidence import (
        certify_prepared_gap,
        prepare_canonical_witness,
    )

    p = contract()
    a = prepare_canonical_witness(p, {"root": (0.125, 0.125)})
    y = (0.0,) * len(a.ub)
    lam = (0.0,) * len(a.eq)
    baseline = certify_prepared_gap(a, y, lam, 0.0)

    def inspect(c, **kw):
        assert np.max(np.abs(c)) == 1.0
        assert issparse(kw["A_ub"]) and issparse(kw["A_eq"])
        assert kw["options"]["time_limit"] == 5.0
        assert kw["method"] == "highs"
        return SimpleNamespace(success=False)

    with patch("scipy.optimize.linprog", inspect):
        assert improve_canonical_proposal(a, baseline)[0] is baseline


def test_repaired_actual_consumer_remains_separate():
    from ordivon_capital.portfolio.witness_repair import verify_repaired_witness

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
                maintenance=(0.3,),
                terminal=True,
            ),
        ),
    )
    a = solve_multistage(p, witness_repair_max_change_r=2**-40)
    b = solve_multistage(
        p, witness_repair_max_change_r=2**-40, dual_proposal_method="CANONICAL_GRADIENT"
    )
    assert a.node_decisions_r == b.node_decisions_r
    assert a.optimality_evidence == b.optimality_evidence
    assert a.optimality_evidence.reason == "INEXACT_WITNESS"
    assert a.witness_repair.repaired_policy == b.witness_repair.repaired_policy
    assert b.dual_proposal_standing.startswith("REPAIRED_")
    assert (
        b.witness_repair.canonical_evidence.certified_canonical_gap_upper
        <= a.witness_repair.canonical_evidence.certified_canonical_gap_upper
    )
    assert verify_repaired_witness(p, {"root": b.root_risky_r}, b.witness_repair)


def test_actual_cli_independent_replay():
    import json
    import os
    import subprocess
    import sys
    from dataclasses import asdict
    from pathlib import Path

    from ordivon_capital.research.independent_policy_replay import replay_multistage_json

    p = json.loads(json.dumps(asdict(contract())))
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
    cmd = [
        sys.executable,
        "-m",
        "ordivon_capital.portfolio.multistage_policy",
        "--cap-method",
        "STRUCTURED_V2",
        "--dual-proposal-method",
        "CANONICAL_GRADIENT",
    ]
    result = json.loads(
        subprocess.run(
            cmd, input=json.dumps(p), capture_output=True, text=True, check=True, env=env
        ).stdout
    )
    assert result["effectStanding"] == "READ_ONLY_NO_BROKER_NO_PAPER_LEDGER"
    assert result["solution"]["dual_proposal_standing"] != "NUMERICAL_TANGENT"
    assert (
        replay_multistage_json(p, result["solution"])["effects"] == "NONE_NO_BROKER_NO_ACCOUNTING"
    )


def test_both_dual_vectors_rescaled_before_exact_verification():
    from types import SimpleNamespace

    from ordivon_capital.portfolio.canonical_dual_proposal import improve_canonical_proposal
    from ordivon_capital.portfolio.optimality_evidence import (
        certify_prepared_gap,
        prepare_canonical_witness,
    )

    p = contract()
    prepared = prepare_canonical_witness(p, {"root": (0.125, 0.125)})
    scale = float(
        max(abs((a + b) / 2) for a, b in zip(prepared.grad, prepared.grad_hi, strict=True))
    )
    assert scale != 1.0
    baseline = certify_prepared_gap(
        prepared, (0.0,) * len(prepared.ub), (0.0,) * len(prepared.eq), 0.0
    )
    y = (-0.25,) * len(prepared.ub)
    lam = (0.5,) * len(prepared.eq)
    proposal = SimpleNamespace(
        success=True, ineqlin=SimpleNamespace(marginals=y), eqlin=SimpleNamespace(marginals=lam)
    )
    with (
        patch("scipy.optimize.linprog", return_value=proposal),
        patch(
            "ordivon_capital.portfolio.canonical_dual_proposal.certify_prepared_gap",
            wraps=certify_prepared_gap,
        ) as check,
    ):
        improve_canonical_proposal(prepared, baseline)
    check.assert_called_once_with(
        prepared, tuple(v * scale for v in y), tuple(v * scale for v in lam), 0.0
    )


def test_unrepresentable_scale_and_excess_coordinates_retain_baseline():
    from dataclasses import replace
    from types import SimpleNamespace

    from ordivon_capital.portfolio.canonical_dual_proposal import improve_canonical_proposal
    from ordivon_capital.portfolio.optimality_evidence import (
        certify_prepared_gap,
        prepare_canonical_witness,
    )

    a = prepare_canonical_witness(contract(), {"root": (0.125, 0.125)})
    baseline = certify_prepared_gap(a, (0.0,) * len(a.ub), (0.0,) * len(a.eq), 0.0)
    for magnitude in (Fraction(1 << 2000), Fraction(1, 1 << 2000)):
        invalid = replace(a, grad=(magnitude,) * len(a.x), grad_hi=(magnitude,) * len(a.x))
        with patch("scipy.optimize.linprog", side_effect=AssertionError("no LP for invalid scale")):
            assert improve_canonical_proposal(invalid, baseline) == (
                baseline,
                "BASELINE_RETAINED_UNREPRESENTABLE_PROPOSAL",
            )

    class Probe:
        count = 0

        def __iter__(self):
            while True:
                self.count += 1
                if self.count > len(a.ub) + 1:
                    raise AssertionError("unbounded read")
                yield 0.0

    values = Probe()
    proposal = SimpleNamespace(
        success=True,
        ineqlin=SimpleNamespace(marginals=values),
        eqlin=SimpleNamespace(marginals=(0.0,) * len(a.eq)),
    )
    with patch("scipy.optimize.linprog", return_value=proposal):
        assert improve_canonical_proposal(a, baseline) == (
            baseline,
            "BASELINE_RETAINED_MALFORMED_PROPOSAL",
        )
    assert values.count == len(a.ub) + 1
