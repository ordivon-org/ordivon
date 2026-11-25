"""Explicit numerical carrier selection is not a financial authorization."""

import json
from dataclasses import asdict
from unittest.mock import patch

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage
from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError


def problem(gamma=2.0, depth=2):
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
    return MultistageProblem(
        gamma,
        tuple(nodes),
        terminal_liabilities_r={n.id: 0.12 for n in nodes if n.terminal},
        node_outflow_after_contribution_r={n.id: 0.06 for n in nodes if not n.terminal},
    )


def test_sparse_native_boundary_never_calls_csr_toarray():
    p = problem()
    baseline = solve_multistage(p)
    with patch.object(csr_matrix, "toarray", side_effect=AssertionError("dense conversion")):
        result = solve_multistage(p, numerical_solver="TRUST_CONSTR_SPARSE")
    assert result.numerical_solver == "TRUST_CONSTR_SPARSE"
    assert result.expected_utility == pytest.approx(baseline.expected_utility, abs=1e-6)
    assert result.equality_residual < 1e-7 and result.inequality_residual < 1e-7
    assert baseline.numerical_solver == "SLSQP"
    assert asdict(solve_multistage(p, numerical_solver="SLSQP")) == asdict(baseline)


@pytest.mark.parametrize("selection", ("auto", "trust-constr", None, True))
def test_unrecognized_carrier_rejected_before_optimizer(selection):
    with patch("scipy.optimize.minimize", side_effect=AssertionError("must not optimize")):
        with pytest.raises(AlgebraicPolicyError, match="numerical solver"):
            solve_multistage(problem(), numerical_solver=selection)


def test_sparse_failure_is_not_automatic_dense_fallback():
    from scipy.optimize import OptimizeResult

    calls = []

    def fail(fun, x0, **kwargs):
        calls.append(kwargs["method"])
        return OptimizeResult(x=np.asarray(x0), success=False, message="synthetic failure")

    with patch("scipy.optimize.minimize", fail):
        with pytest.raises(AlgebraicPolicyError, match="did not yield"):
            solve_multistage(problem(), numerical_solver="TRUST_CONSTR_SPARSE")
    assert calls == ["trust-constr"]


@pytest.mark.parametrize(
    "depth,gamma", [(1, 0.5), (2, 1.0), (3, 0.75), (3, 5.0), (4, 2.0), (5, 0.5)]
)
def test_heldout_liability_and_outflow_contracts(depth, gamma):
    from ordivon_capital.portfolio.optimality_evidence import verify_canonical_gap_claim
    from ordivon_capital.portfolio.witness_repair import verify_repaired_witness
    from ordivon_capital.research.independent_policy_replay import replay_multistage_json

    p = problem(gamma, depth)
    reference = solve_multistage(p, witness_repair_max_change_r=2**-40)
    candidate = solve_multistage(
        p, numerical_solver="TRUST_CONSTR_SPARSE", witness_repair_max_change_r=2**-40
    )
    assert candidate.expected_utility == pytest.approx(reference.expected_utility, abs=1e-6)
    for result in (reference, candidate):
        assert result.equality_residual <= 1e-7 and result.inequality_residual <= 1e-7
        replay = replay_multistage_json(
            json.loads(json.dumps(asdict(p))), json.loads(json.dumps(asdict(result)))
        )
        assert replay["max_identity_residual_r"] <= 1e-6
        raw = {k: v["assetExposuresR"] for k, v in result.node_decisions_r.items()}
        if result.optimality_evidence.certified_canonical_gap_upper is not None:
            assert verify_canonical_gap_claim(p, raw, result.optimality_evidence)
        elif result.witness_repair and result.witness_repair.canonical_evidence:
            assert verify_repaired_witness(p, raw, result.witness_repair)
        else:
            assert result.optimality_evidence.standing == "UNKNOWN"


@pytest.mark.parametrize("bad", [np.array([0.0]), np.full(12, np.nan)])
def test_invalid_optimizer_result_is_rejected(bad):
    from scipy.optimize import OptimizeResult

    with patch(
        "scipy.optimize.minimize", return_value=OptimizeResult(x=bad, success=True, message="bad")
    ):
        with pytest.raises(AlgebraicPolicyError, match="candidate coordinates"):
            solve_multistage(problem(), numerical_solver="TRUST_CONSTR_SPARSE")


def test_sparse_hessian_against_independent_centered_gradient_difference():
    from scipy.optimize import OptimizeResult
    from scipy.sparse import issparse

    def probe(fun, x0, **kw):
        x = np.asarray(x0) + 0.1
        v = np.linspace(-0.1, 0.2, len(x))
        step = 1e-5
        H = kw["hess"](x)
        assert issparse(H)
        expected = (fun(x + step * v)[1] - fun(x - step * v)[1]) / (2 * step)
        assert H @ v == pytest.approx(expected, rel=1e-6, abs=1e-8)
        return OptimizeResult(x=x0, success=False, message="probe")

    with patch("scipy.optimize.minimize", probe):
        with pytest.raises(AlgebraicPolicyError, match="did not yield"):
            solve_multistage(problem(0.75), numerical_solver="TRUST_CONSTR_SPARSE")


def test_actual_cli_opt_in_and_independent_replay():
    import os
    import subprocess
    import sys
    from pathlib import Path

    from ordivon_capital.research.independent_policy_replay import replay_multistage_json

    p = json.loads(json.dumps(asdict(problem(0.5, 2))))
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    cmd = [
        sys.executable,
        "-m",
        "ordivon_capital.portfolio.multistage_policy",
        "--numerical-solver",
        "TRUST_CONSTR_SPARSE",
    ]
    payload = json.loads(
        subprocess.run(
            cmd, input=json.dumps(p), text=True, capture_output=True, check=True, env=env
        ).stdout
    )
    assert payload["effectStanding"] == "READ_ONLY_NO_BROKER_NO_PAPER_LEDGER"
    assert payload["solution"]["numerical_solver"] == "TRUST_CONSTR_SPARSE"
    assert (
        replay_multistage_json(p, payload["solution"])["effects"] == "NONE_NO_BROKER_NO_ACCOUNTING"
    )
