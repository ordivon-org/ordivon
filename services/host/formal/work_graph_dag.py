"""Bounded SMT model of Host Work Graph DAG admission.

Models exact directed transitive reachability (the same predicate as the
PostgreSQL WITH RECURSIVE gate), not actual PostgreSQL locking, transaction
isolation, or Python/SQL refinement.

The accepted pre-state is acyclic. Prove for all graphs on 2, 3 and 4
labeled nodes that adding u->v is acyclic iff v cannot reach u.
A negative control proves a direction-swapped guard is unsound.
"""

from __future__ import annotations

from z3 import And, Bool, BoolVal, Not, Or, Solver, sat, unsat


def closure(edges: list[list]) -> list[list]:
    """Finite Warshall transitive closure; paths of positive length only."""
    size = len(edges)
    result = edges
    for mid in range(size):
        prev = result
        result = [
            [
                Or(prev[i][j], And(prev[i][mid], prev[mid][j]))
                for j in range(size)
            ]
            for i in range(size)
        ]
    return result


def verified(label: str, solver: Solver, expected) -> None:
    result = solver.check()
    if result != expected:
        witness = str(solver.model()) if result == sat else str(result)
        raise AssertionError(f"{label}: expected {expected}, got {result}; {witness}")


def check_graph(size: int) -> int:
    edges = [[Bool(f"e{size}_{i}_{j}") for j in range(size)] for i in range(size)]
    old_reach = closure(edges)
    acyclic_before = And(*(Not(old_reach[i][i]) for i in range(size)))
    checked = 0
    for source in range(size):
        for target in range(size):
            if source == target:
                continue  # Public WorkRelationInput rejects self edges separately.
            added = [
                [
                    Or(edges[i][j], BoolVal(i == source and j == target))
                    for j in range(size)
                ]
                for i in range(size)
            ]
            new_reach = closure(added)
            cycle_after = Or(*(new_reach[i][i] for i in range(size)))

            # Soundness: a DAG plus an admitted edge stays a DAG.
            admitted = Solver()
            admitted.add(acyclic_before, Not(old_reach[target][source]), cycle_after)
            verified(f"soundness(n={size},src={source},dst={target})", admitted, unsat)
            checked += 1

            # Completeness relative to the invariant: if it closes a path,
            # a cycle follows, so the existing guard must reject.
            rejected = Solver()
            rejected.add(acyclic_before, old_reach[target][source], Not(cycle_after))
            verified(f"rejection(n={size},src={source},dst={target})", rejected, unsat)
            checked += 1
    return checked


def main() -> None:
    count = sum(check_graph(n) for n in (2, 3, 4))

    # Falsifying control: the common error is checking the forward direction
    # u -> v, instead of v -> u, before inserting u -> v.
    e = [[Bool(f"bad_{i}_{j}") for j in range(3)] for i in range(3)]
    reach = closure(e)
    new = [[Or(e[i][j], BoolVal(i == 0 and j == 1)) for j in range(3)] for i in range(3)]
    swapped = Solver()
    swapped.add(
        And(*(Not(reach[i][i]) for i in range(3))),
        Not(reach[0][1]),  # Incorrect swapped-direction admission.
        Or(*(closure(new)[i][i] for i in range(3))),
    )
    verified("negative_control_swapped_guard", swapped, sat)
    print(f"MODEL_VERIFIED bounded_DAG n=2,3,4 obligations={count}; negative_control=SAT")
    print("IMPLEMENTATION_REFINEMENT=UNKNOWN until native PostgreSQL recursive-CTE/lock evidence")
    print("UNBOUNDED_THEOREM=CHECK_HOST_WORK_DAG_LEAN; DELIVERY_AND_DOMAIN_TRUTH=NOT_CLAIMED")


if __name__ == "__main__":
    main()
