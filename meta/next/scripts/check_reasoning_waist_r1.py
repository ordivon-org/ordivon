#!/usr/bin/env python3
"""Bounded, non-mutating smoke for the repository-native Reasoning Waist.

This validates only mechanical composition of mature reasoning providers on a
small synthetic case. The command prints current observations; it does not
rewrite historical acceptance receipts under evidence/.
"""

from __future__ import annotations

import importlib.metadata as md
import json
import platform
from math import inf

from pyshacl import validate
from rdflib import RDF, Graph, Literal, Namespace
from rdflib.namespace import SH
from scipy.optimize import Bounds, LinearConstraint, milp
from unified_planning.shortcuts import (
    BoolType,
    Fluent,
    InstantaneousAction,
    OneshotPlanner,
    Problem,
    get_environment,
)
from z3 import Bool, Implies, Not, Solver, sat, unsat

EX = Namespace("urn:ordivon:reasoning-waist:r1:")


def require(condition: bool, message: object) -> None:
    if not condition:
        raise RuntimeError(str(message))


def package_versions() -> dict[str, str]:
    return {
        "scipy": md.version("scipy"),
        "z3-solver": md.version("z3-solver"),
        "unified-planning": md.version("unified-planning"),
        "up-pyperplan": md.version("up-pyperplan"),
        "rdflib": md.version("rdflib"),
        "pyshacl": md.version("pyshacl"),
    }


def validate_problem_shape() -> dict:
    data = Graph()
    data.add((EX.case, RDF.type, EX.ProblemCase))
    data.add((EX.case, EX.hasGoal, EX.verifiedOutcome))
    data.add((EX.case, EX.maxCost, Literal(8)))

    shapes = Graph()
    shape = EX.ProblemCaseShape
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.targetClass, EX.ProblemCase))
    p_goal = EX.goalShape
    shapes.add((shape, SH.property, p_goal))
    shapes.add((p_goal, SH.path, EX.hasGoal))
    shapes.add((p_goal, SH.minCount, Literal(1)))
    p_cost = EX.costShape
    shapes.add((shape, SH.property, p_cost))
    shapes.add((p_cost, SH.path, EX.maxCost))
    shapes.add((p_cost, SH.minCount, Literal(1)))

    conforms, _, report = validate(data, shacl_graph=shapes)
    require(bool(conforms), report)

    bad = Graph()
    bad.add((EX.badCase, RDF.type, EX.ProblemCase))
    bad_conforms, _, _ = validate(bad, shacl_graph=shapes)
    require(not bool(bad_conforms), "invalid SHACL sibling unexpectedly conformed")

    rows = list(
        data.query(
            "SELECT ?goal WHERE { <urn:ordivon:reasoning-waist:r1:case> "
            "<urn:ordivon:reasoning-waist:r1:hasGoal> ?goal }"
        )
    )
    require(
        bool(rows) and rows[0].goal == EX.verifiedOutcome,
        "SPARQL goal projection mismatch",
    )
    return {
        "validCaseConforms": True,
        "invalidCaseRejected": True,
        "triples": len(data),
    }


def solve_configuration() -> dict:
    # Exact bounded binary mixed-integer optimization of the original CP-SAT
    # scenario. HiGHS (via SciPy) remains an independent, mature provider
    # alongside the separate Z3 satisfiability and Pyperplan checks.
    names = ("retrieve", "verify", "plan", "diagnose", "visualize")
    costs = [2, 3, 2, 4, 1]
    utilities = [3, 5, 4, 2, 1]
    result = milp(
        c=[-value for value in utilities],
        integrality=[1] * len(names),
        bounds=Bounds([1, 1, 0, 0, 0], [1] * len(names)),
        constraints=LinearConstraint(
            [costs, [-1, 0, 1, 0, 0]],
            [-inf, -inf],
            [8, 0],
        ),
        options={"time_limit": 10.0},
    )
    require(result.success and result.x is not None, f"SciPy MILP solve failed: {result.message}")
    selected = {name: round(float(value)) for name, value in zip(names, result.x, strict=True)}
    require(
        all(abs(float(value) - selected[name]) < 1e-6 for name, value in zip(names, result.x, strict=True)),
        "MILP output is not an integral binary selection",
    )
    require(selected["retrieve"] == 1 and selected["verify"] == 1, "required capabilities not selected")
    require(
        sum(costs[i] * selected[name] for i, name in enumerate(names)) <= 8
        and selected["plan"] <= selected["retrieve"],
        "selected capabilities violate source constraints",
    )
    objective = sum(utilities[i] * selected[name] for i, name in enumerate(names))
    require(abs(objective + float(result.fun)) < 1e-6, "solver objective drift")
    return {"selected": selected, "objective": float(objective)}


def crosscheck_logic(config: dict) -> dict:
    retrieve, verify, plan = Bool("retrieve"), Bool("verify"), Bool("plan")
    solver = Solver()
    solver.add(Implies(plan, retrieve))
    solver.add(retrieve == bool(config["selected"]["retrieve"]))
    solver.add(verify == bool(config["selected"]["verify"]))
    solver.add(plan == bool(config["selected"]["plan"]))
    require(solver.check() == sat, "selected configuration is not satisfiable")

    contradiction = Solver()
    contradiction.add(Implies(plan, retrieve), plan, Not(retrieve))
    require(contradiction.check() == unsat, "known contradiction was not rejected")
    return {
        "selectedConfigurationSatisfiable": True,
        "knownContradictionRejected": True,
    }


def generate_plan() -> dict:
    get_environment().credits_stream = None
    problem = Problem("verified_outcome")
    retrieved = Fluent("retrieved", BoolType())
    configured = Fluent("configured", BoolType())
    verified = Fluent("verified", BoolType())
    delivered = Fluent("delivered", BoolType())
    for fluent in (retrieved, configured, verified, delivered):
        problem.add_fluent(fluent, default_initial_value=False)

    retrieve = InstantaneousAction("retrieve_case_and_methods")
    retrieve.add_effect(retrieved, True)
    configure = InstantaneousAction("configure_solution")
    configure.add_precondition(retrieved)
    configure.add_effect(configured, True)
    verify = InstantaneousAction("verify_solution")
    verify.add_precondition(configured)
    verify.add_effect(verified, True)
    deliver = InstantaneousAction("deliver_verified_outcome")
    deliver.add_precondition(verified)
    deliver.add_effect(delivered, True)
    for action in (retrieve, configure, verify, deliver):
        problem.add_action(action)
    problem.add_goal(delivered)

    with OneshotPlanner(name="pyperplan") as planner:
        result = planner.solve(problem)
    require(result.plan is not None, "planner returned no plan")
    actions = [instance.action.name for instance in result.plan.actions]
    require(
        actions
        == [
            "retrieve_case_and_methods",
            "configure_solution",
            "verify_solution",
            "deliver_verified_outcome",
        ],
        f"unexpected plan: {actions}",
    )
    return {"engine": "pyperplan", "actions": actions}


def main() -> int:
    configuration = solve_configuration()
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.reasoning-waist-current-smoke",
        "standing": "PASS_LOCAL_COMPOSED_SMOKE",
        "pythonVersion": platform.python_version(),
        "packageVersions": package_versions(),
        "checks": {
            "rdfShaclProblemShape": validate_problem_shape(),
            "scipyMilpConfiguration": configuration,
            "z3LogicCrosscheck": crosscheck_logic(configuration),
            "unifiedPlanning": generate_plan(),
        },
        "executionHandoff": "NOT_EXERCISED_BY_THIS_SMOKE",
        "boundary": (
            "PASS proves only that mature reasoning providers compose mechanically on a tiny "
            "bounded case. It does not establish domain model correctness, universal planning "
            "competence, business decision authority, workflow durability or physical execution success."
        ),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
