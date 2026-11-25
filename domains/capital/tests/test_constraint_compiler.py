"""Independent economic equations for the sparse compiler, not solver internals."""
from __future__ import annotations

import math
from dataclasses import replace
from random import Random

import numpy as np
import pytest
from scipy.sparse import isspmatrix_csr

from ordivon_capital.portfolio.constraint_compiler import compile_multistage_constraints
from ordivon_capital.portfolio.information_tree import InformationNode, MultistageProblem
from ordivon_capital.portfolio.multistage_policy import solve_multistage


def _fixture(depth: int, assets: int, seed: int) -> MultistageProblem:
    rng = Random(seed)
    nodes = [InformationNode("root", None, 0, 1.,
                             initial_margin=(.6,) * assets, turnover_cost=(0.,) * assets)]
    level = ["root"]
    for t in range(1, depth + 1):
        children = []
        for parent in level:
            for label, p in (("a", .25), ("b", .75)):
                key = parent + label
                terminal = t == depth
                nodes.append(InformationNode(
                    key, parent, t, p,
                    risky_gross=tuple(rng.choice((0., .75, 1., 1.25)) for _ in range(assets)),
                    cash_gross=1.01, debt_gross=1.03,
                    maintenance=tuple(rng.choice((0., .25, 1.)) for _ in range(assets)),
                    initial_margin=() if terminal else tuple(rng.choice((.25, .6, 1.)) for _ in range(assets)),
                    turnover_cost=() if terminal else tuple(rng.choice((0., .005, .03)) for _ in range(assets)),
                    terminal=terminal, observed_label=label,
                ))
                children.append(key)
        level = children
    liabilities = {n.id: rng.choice((0., .125, .75)) for n in nodes if n.terminal}
    outflows = {n.id: rng.choice((0., .25, 1.)) for n in nodes if not n.terminal}
    rng.shuffle(nodes)
    return MultistageProblem(2., tuple(nodes), liabilities, outflows)


def _economic_equations(problem, compiled, x):
    """Scalar interpretation of contracts using node states, not matrix columns."""
    n = compiled.tree.asset_count
    states = dict(zip(
        (node.id for node in compiled.tree.decision),
        x.reshape(-1, 2*n+2), strict=True,
    ))
    equality, inequality, arrival, terminal = [], [], [], []
    for node in sorted(problem.nodes, key=lambda node: (node.t, node.id)):
        prior_risky = [0.] * n
        prior_wealth = 0.
        if node.parent is not None:
            parent = states[node.parent]
            prior_risky = [float(a*g) for a, g in zip(parent[:n], node.risky_gross, strict=True)]
            prior_wealth = math.fsum((*prior_risky, parent[n]*node.cash_gross, -parent[n+1]*node.debt_gross))
            arrival.append(prior_wealth)
            inequality.append(math.fsum(a*m for a, m in zip(prior_risky, node.maintenance, strict=True)) - prior_wealth)
        if node.terminal:
            terminal.append(prior_wealth)
            continue
        state = states[node.id]
        risky, cash, debt, turnover = state[:n], state[n], state[n+1], state[n+2:]
        equity = math.fsum((*risky, cash, -debt))
        cost = math.fsum(k*h for k, h in zip(node.turnover_cost, turnover, strict=True))
        equality.append(equity + cost - prior_wealth)
        for a, old, h in zip(risky, prior_risky, turnover, strict=True):
            inequality.extend((a-old-h, old-a-h))
        inequality.append(math.fsum(a*m for a, m in zip(risky, node.initial_margin, strict=True)) - equity)
    return equality, inequality, terminal, arrival


@pytest.mark.parametrize("depth,assets,seed", [(d, a, s) for d in (1, 2, 3) for a in (1, 3) for s in (17, 43)])
def test_compiler_linear_map_equals_independent_economic_equations(depth, assets, seed):
    problem = _fixture(depth, assets, seed)
    compiled = compile_multistage_constraints(problem)
    matrices = (compiled.A_eq, compiled.A_ub, compiled.W_leaf, compiled.W_arrival)
    assert all(isspmatrix_csr(m) and m.has_canonical_format and np.all(m.data != 0) for m in matrices)
    # Evaluating every basis vector identifies the entire linear map.
    for x in np.eye(compiled.size):
        expected = _economic_equations(problem, compiled, x)
        for matrix, values in zip(matrices, expected, strict=True):
            np.testing.assert_allclose(matrix @ x, values, rtol=0, atol=1e-14)
    # Nontrivial values also exercise fees, cash, debt and net wealth.
    x = np.random.default_rng(seed).uniform(0, 3, compiled.size)
    for matrix, values in zip(matrices, _economic_equations(problem, compiled, x), strict=True):
        np.testing.assert_allclose(matrix @ x, values, rtol=1e-13, atol=1e-13)
    assert compiled.b_eq.tolist() == [1-problem.node_outflow_after_contribution_r[n.id] for n in compiled.tree.decision]
    assert not np.any(compiled.b_ub)
    assert compiled.liabilities.tolist() == [problem.terminal_liabilities_r[n.id] for n in compiled.tree.leaves]
    by_id = {n.id: n for n in problem.nodes}
    for leaf, actual in zip(compiled.tree.leaves, compiled.probabilities, strict=True):
        factors = [leaf.conditional_probability]
        node = leaf
        while node.parent is not None:
            node = by_id[node.parent]
            factors.append(node.conditional_probability)
        assert actual == pytest.approx(math.prod(factors), rel=1e-15)
    reversed_problem = replace(problem, nodes=tuple(reversed(problem.nodes)))
    again = compile_multistage_constraints(reversed_problem)
    for first, second in zip(matrices, (again.A_eq, again.A_ub, again.W_leaf, again.W_arrival), strict=True):
        assert (first != second).nnz == 0


def test_feasibility_and_certificate_both_use_native_sparse_lp(monkeypatch):
    import scipy.optimize

    actual = scipy.optimize.linprog
    calls = []

    def observe(*args, **kwargs):
        assert isspmatrix_csr(kwargs["A_eq"])
        assert isspmatrix_csr(kwargs["A_ub"])
        calls.append(kwargs["A_eq"].shape[1])
        return actual(*args, **kwargs)

    monkeypatch.setattr(scipy.optimize, "linprog", observe)
    problem = MultistageProblem(2., (
        InformationNode("root", None, 0, 1., initial_margin=(1.,), turnover_cost=(0.,)),
        InformationNode("leaf", "root", 1, 1., risky_gross=(2.,), maintenance=(.3,), terminal=True),
    ), terminal_liabilities_r={"leaf": 1.25})
    result = solve_multistage(problem)
    assert calls == [5, 4]
    assert result.expected_disposable_terminal_r == pytest.approx(.75, abs=1e-7)
    assert result.concavity_global_utility_gap_upper < 1e-7


def test_large_tree_compilation_stays_linear_in_local_coefficients():
    problem = _fixture(9, 3, 17)
    compiled = compile_multistage_constraints(problem)
    matrices = (compiled.A_eq, compiled.A_ub, compiled.W_leaf, compiled.W_arrival)
    # The contract has only parent/current blocks in each row, not global width.
    assert all(np.diff(matrix.indptr).max() <= 3*3+4 for matrix in matrices)
    assert sum(m.nnz for m in matrices) < 40*len(problem.nodes)
    sparse = sum(m.data.nbytes + m.indices.nbytes + m.indptr.nbytes for m in matrices)
    dense = sum(m.shape[0]*m.shape[1]*8 for m in matrices)
    assert sparse < dense/100
