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

from ortools.sat.python import cp_model
from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF
from rdflib.namespace import SH
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


def package_versions() -> dict[str, str]:
    return {
        "ortools": md.version("ortools"),
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
    assert conforms, report

    bad = Graph()
    bad.add((EX.badCase, RDF.type, EX.ProblemCase))
    bad_conforms, _, _ = validate(bad, shacl_graph=shapes)
    assert not bad_conforms

    rows = list(data.query(
        "SELECT ?goal WHERE { <urn:ordivon:reasoning-waist:r1:case> "
        "<urn:ordivon:reasoning-waist:r1:hasGoal> ?goal }"
    ))
    assert rows and rows[0].goal == EX.verifiedOutcome
    return {"validCaseConforms": True, "invalidCaseRejected": True, "triples": len(data)}


def solve_configuration() -> dict:
    model = cp_model.CpModel()
    retrieve = model.new_bool_var("retrieve")
    verify = model.new_bool_var("verify")
    plan = model.new_bool_var("plan")
    diagnose = model.new_bool_var("diagnose")
    visualize = model.new_bool_var("visualize")

    model.add(retrieve == 1)
    model.add(verify == 1)
    model.add(plan <= retrieve)
    model.add(2 * retrieve + 3 * verify + 2 * plan + 4 * diagnose + visualize <= 8)
    model.maximize(3 * retrieve + 5 * verify + 4 * plan + 2 * diagnose + visualize)

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    vars_ = [retrieve, verify, plan, diagnose, visualize]
    selected = {v.name: solver.value(v) for v in vars_}
    assert selected["retrieve"] == 1 and selected["verify"] == 1
    return {"selected": selected, "objective": solver.objective_value}


def crosscheck_logic(config: dict) -> dict:
    retrieve, verify, plan = Bool("retrieve"), Bool("verify"), Bool("plan")
    solver = Solver()
    solver.add(Implies(plan, retrieve))
    solver.add(retrieve == bool(config["selected"]["retrieve"]))
    solver.add(verify == bool(config["selected"]["verify"]))
    solver.add(plan == bool(config["selected"]["plan"]))
    assert solver.check() == sat

    contradiction = Solver()
    contradiction.add(Implies(plan, retrieve), plan, Not(retrieve))
    assert contradiction.check() == unsat
    return {"selectedConfigurationSatisfiable": True, "knownContradictionRejected": True}


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
    assert result.plan is not None
    actions = [instance.action.name for instance in result.plan.actions]
    assert actions == [
        "retrieve_case_and_methods",
        "configure_solution",
        "verify_solution",
        "deliver_verified_outcome",
    ]
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
            "ortoolsConfiguration": configuration,
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
