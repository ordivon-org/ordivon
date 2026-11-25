"""Numerical carrier adapter; not a scientific or financial certificate.

The economic model, feasibility admission and independent optimality evidence
are owned by the caller. No fallback, no invented contracts or effects.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from .policy_contract import AlgebraicPolicyError

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from scipy.optimize import OptimizeResult
    from scipy.sparse import csr_matrix

    from .constraint_compiler import CompiledConstraints

NumericalSolver = Literal["SLSQP", "TRUST_CONSTR_SPARSE"]


def validate_numerical_solver(value: object) -> None:
    if not isinstance(value, str) or value not in ("SLSQP", "TRUST_CONSTR_SPARSE"):
        raise AlgebraicPolicyError("unknown numerical solver; select SLSQP or TRUST_CONSTR_SPARSE")


def solve_numeric(
    *,
    selection: NumericalSolver,
    compiled: CompiledConstraints,
    x0: NDArray,
    objective: Callable[[NDArray], tuple[float, NDArray]],
    gamma: float,
    numerical_interior: float,
) -> OptimizeResult:
    """Explicit dense or native sparse boundary using the same compiled model."""
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, minimize

    validate_numerical_solver(selection)
    sparse = selection == "TRUST_CONSTR_SPARSE"
    matrix = (lambda a: a) if sparse else (lambda a: a.toarray())
    constraints = [
        LinearConstraint(matrix(compiled.A_eq), compiled.b_eq, compiled.b_eq),
        LinearConstraint(matrix(compiled.A_ub), -np.inf, compiled.b_ub),
        LinearConstraint(matrix(compiled.W_arrival), 0.0, np.inf),
        LinearConstraint(
            matrix(compiled.W_leaf),
            compiled.liabilities + numerical_interior,
            np.inf,
        ),
    ]
    bounds = Bounds(np.zeros(compiled.size), np.full(compiled.size, np.inf))
    if not sparse:
        return minimize(
            objective,
            x0,
            method="SLSQP",
            jac=True,
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-11, "maxiter": 3000},
        )

    def hessian(x: NDArray) -> csr_matrix:
        # Negative CRRA objective Hessian = W.T diag(p*gamma*w**(-gamma-1)) W.
        # Keep the entire operator sparse; never form a dense diagonal.
        W = compiled.W_leaf
        wealth = W @ x - compiled.liabilities
        if np.any(wealth <= 0) or not np.all(np.isfinite(wealth)):
            raise AlgebraicPolicyError("sparse solver left positive terminal wealth domain")
        weights = compiled.probabilities * gamma * wealth ** (-gamma - 1)
        if not np.all(np.isfinite(weights)):
            raise AlgebraicPolicyError("nonfinite sparse solver Hessian")
        return (W.T @ W.multiply(weights[:, None])).tocsr()

    return minimize(
        objective,
        x0,
        method="trust-constr",
        jac=True,
        hess=hessian,
        bounds=bounds,
        constraints=constraints,
        options={
            "sparse_jacobian": True,
            "factorization_method": "AugmentedSystem",
            "gtol": 1e-13,
            "initial_barrier_parameter": 1e-7,
            "initial_barrier_tolerance": 1e-7,
            "barrier_tol": 1e-12,
            "maxiter": 3000,
        },
    )
