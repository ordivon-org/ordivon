"""Compile validated local information-tree economics into sparse linear rows.

Column order is one (risky..., cash, debt, turnover...) block per decision.
The compiler owns no solver selection, market authority or financial effect.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .information_tree import (
    MultistageProblem,
    ValidatedInformationTree,
    validate_information_tree,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from scipy.sparse import csr_matrix


@dataclass(frozen=True)
class CompiledConstraints:
    tree: ValidatedInformationTree
    offsets: dict[str, int]
    size: int
    A_eq: csr_matrix
    b_eq: NDArray
    A_ub: csr_matrix
    b_ub: NDArray
    W_leaf: csr_matrix
    W_arrival: csr_matrix
    liabilities: NDArray
    probabilities: NDArray


def compile_multistage_constraints(problem: MultistageProblem) -> CompiledConstraints:
    """Build CSR directly from local nonzero coefficients, not dense rows."""
    import numpy as np
    from scipy.sparse import csr_matrix

    tree = validate_information_tree(problem)
    n = tree.asset_count
    width = 2 * n + 2
    size = len(tree.decision) * width
    offsets = {node.id: i * width for i, node in enumerate(tree.decision)}
    eq_rows: list[dict[int, float]] = []
    ub_rows: list[dict[int, float]] = []
    arrival_rows: list[dict[int, float]] = []
    leaf_rows: list[dict[int, float]] = []
    rhs_eq: list[float] = []

    def csr(rows: list[dict[int, float]]) -> csr_matrix:
        data: list[float] = []
        indices: list[int] = []
        indptr = [0]
        for row in rows:
            for col, value in sorted(row.items()):
                if value != 0:
                    indices.append(col)
                    data.append(value)
            indptr.append(len(data))
        return csr_matrix((data, indices, indptr), shape=(len(rows), size), dtype=float)

    for node in tree.ordered:
        incoming: dict[int, float] = {}
        if node.parent is not None:
            parent = offsets[node.parent]
            incoming = {parent + i: g for i, g in enumerate(node.risky_gross)}
            incoming.update({parent + n: node.cash_gross, parent + n + 1: -node.debt_gross})
            arrival_rows.append(incoming)
            margin = {
                parent + i: (m - 1.0) * g
                for i, (m, g) in enumerate(zip(node.maintenance, node.risky_gross, strict=True))
            }
            margin.update({parent + n: -node.cash_gross, parent + n + 1: node.debt_gross})
            ub_rows.append(margin)
        if node.terminal:
            leaf_rows.append(incoming)
            continue

        index = offsets[node.id]
        row = {col: -value for col, value in incoming.items()}
        row.update({index + i: 1.0 for i in range(n)})
        row.update({index + n: 1.0, index + n + 1: -1.0})
        row.update({index + n + 2 + i: k for i, k in enumerate(node.turnover_cost)})
        eq_rows.append(row)
        due = 0.0 if problem.node_outflow_after_contribution_r is None else problem.node_outflow_after_contribution_r[node.id]
        rhs_eq.append(1.0 - due)

        for i in range(n):
            buy = {index + i: 1.0, index + n + 2 + i: -1.0}
            sell = {index + i: -1.0, index + n + 2 + i: -1.0}
            if node.parent is not None:
                parent_col = offsets[node.parent] + i
                buy[parent_col] = -node.risky_gross[i]
                sell[parent_col] = node.risky_gross[i]
            ub_rows.extend((buy, sell))

        margin = {index + i: m - 1.0 for i, m in enumerate(node.initial_margin)}
        margin.update({index + n: -1.0, index + n + 1: 1.0})
        ub_rows.append(margin)

    return CompiledConstraints(
        tree, offsets, size, csr(eq_rows), np.asarray(rhs_eq),
        csr(ub_rows), np.zeros(len(ub_rows)), csr(leaf_rows), csr(arrival_rows),
        np.asarray([
            0.0 if problem.terminal_liabilities_r is None else problem.terminal_liabilities_r[leaf.id]
            for leaf in tree.leaves
        ], dtype=float),
        np.asarray([tree.probability[leaf.id] for leaf in tree.leaves]),
    )
