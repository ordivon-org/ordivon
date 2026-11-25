"""Economic wire admission is stronger than numerical polyhedron success."""

import json
from dataclasses import asdict
from unittest.mock import patch

import numpy as np
import pytest
from scipy.optimize import OptimizeResult

from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage
from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError
from ordivon_capital.research.independent_policy_replay import replay_multistage_json


def contract(depth, fan, assets, gamma):
    nodes = [
        InformationNode(
            "root", None, 0, 1.0, initial_margin=(0.85,) * assets, turnover_cost=(0.0015,) * assets
        )
    ]
    level = ["root"]
    for t in range(1, depth + 1):
        nxt = []
        for parent in level:
            for i in range(fan):
                key = f"{parent}:{i}"
                term = t == depth
                gross = tuple(
                    0.88 + 0.25 * i / max(1, fan - 1) + (0.015 if j % 2 == 0 else -0.015) * (i - 1)
                    for j in range(assets)
                )
                nodes.append(
                    InformationNode(
                        key,
                        parent,
                        t,
                        1.0 / fan,
                        risky_gross=gross,
                        cash_gross=1.012,
                        debt_gross=1.04,
                        maintenance=(0.35,) * assets,
                        initial_margin=() if term else (0.85,) * assets,
                        turnover_cost=() if term else (0.0015,) * assets,
                        terminal=term,
                        observed_label=str(i),
                    )
                )
                nxt.append(key)
        level = nxt
    return MultistageProblem(
        gamma,
        tuple(nodes),
        terminal_liabilities_r={n.id: 0.13 + 0.02 * int(n.id[-1]) for n in nodes if n.terminal},
        node_outflow_after_contribution_r={n.id: 0.035 for n in nodes if not n.terminal},
    )


def test_feasible_polyhedron_but_excess_fee_is_not_economic_policy():
    p = contract(1, 2, 1, 2.0)

    def fake(fun, x0, **kw):
        x = np.array(x0)
        x[3] = 1.0
        x[1] -= 0.0015
        return OptimizeResult(x=x, success=True, message="feasible but excess turnover")

    with (
        patch("scipy.optimize.minimize", fake),
        patch(
            "scipy.optimize.linprog",
            side_effect=AssertionError("inadmissible economic policy must not reach certificate"),
        ),
    ):
        with pytest.raises(AlgebraicPolicyError, match="turnover identity"):
            solve_multistage(p, numerical_solver="TRUST_CONSTR_SPARSE")


@pytest.mark.parametrize("depth,fan,assets,gamma", [(5, 3, 1, 1.5), (8, 2, 2, 2.0)])
def test_actual_large_tree_replays_with_tighter_carrier(depth, fan, assets, gamma):
    p = contract(depth, fan, assets, gamma)
    r = solve_multistage(p, numerical_solver="TRUST_CONSTR_SPARSE")
    report = replay_multistage_json(
        json.loads(json.dumps(asdict(p))), json.loads(json.dumps(asdict(r)))
    )
    assert report["max_identity_residual_r"] <= 1e-6
    assert r.optimality_evidence.reason == "EXACT_WITNESS_RESOURCE_SCOPE"
