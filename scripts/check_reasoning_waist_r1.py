#!/usr/bin/env python3
"""Bounded acceptance smoke for the local Reasoning Waist R1.

Run with the accepted reasoning-waist Python 3.12 environment. This proves only
that the selected mature providers can be composed mechanically on a tiny case.
"""
from __future__ import annotations

import importlib.metadata as md
import json
from pathlib import Path

from ortools.sat.python import cp_model
from pyshacl import validate
from rdflib import RDF, Graph, Literal, Namespace
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "acceptance" / "reasoning-waist-r1-acceptance-20260914.json"
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
    # Tiny provider configuration: retrieval + verification are mandatory for the
    # named outcome; planning requires retrieval; diagnosis and visualization are optional.
    model = cp_model.CpModel()
    retrieve = model.new_bool_var("retrieve")
    verify = model.new_bool_var("verify")
    plan = model.new_bool_var("plan")
    diagnose = model.new_bool_var("diagnose")
    visualize = model.new_bool_var("visualize")

    model.add(retrieve == 1)
    model.add(verify == 1)
    model.add(plan <= retrieve)
    model.add(2 * retrieve + 3 * verify + 2 * plan + 4 * diagnose + 1 * visualize <= 8)
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
    s = Solver()
    s.add(Implies(plan, retrieve))
    s.add(retrieve == bool(config["selected"]["retrieve"]))
    s.add(verify == bool(config["selected"]["verify"]))
    s.add(plan == bool(config["selected"]["plan"]))
    assert s.check() == sat

    contradiction = Solver()
    contradiction.add(Implies(plan, retrieve), plan, Not(retrieve))
    assert contradiction.check() == unsat
    return {"selectedConfigurationSatisfiable": True, "knownContradictionRejected": True}


def generate_plan() -> dict:
    get_environment().credits_stream = None
    p = Problem("verified_outcome")
    retrieved = Fluent("retrieved", BoolType())
    configured = Fluent("configured", BoolType())
    verified = Fluent("verified", BoolType())
    delivered = Fluent("delivered", BoolType())
    for f in (retrieved, configured, verified, delivered):
        p.add_fluent(f, default_initial_value=False)

    a1 = InstantaneousAction("retrieve_case_and_methods")
    a1.add_effect(retrieved, True)
    a2 = InstantaneousAction("configure_solution")
    a2.add_precondition(retrieved)
    a2.add_effect(configured, True)
    a3 = InstantaneousAction("verify_solution")
    a3.add_precondition(configured)
    a3.add_effect(verified, True)
    a4 = InstantaneousAction("deliver_verified_outcome")
    a4.add_precondition(verified)
    a4.add_effect(delivered, True)
    for action in (a1, a2, a3, a4):
        p.add_action(action)
    p.add_goal(delivered)

    with OneshotPlanner(name="pyperplan") as planner:
        result = planner.solve(p)
    assert result.plan is not None
    actions = [ai.action.name for ai in result.plan.actions]
    assert actions == [
        "retrieve_case_and_methods",
        "configure_solution",
        "verify_solution",
        "deliver_verified_outcome",
    ]
    return {"engine": "pyperplan", "actions": actions}


def main() -> None:
    versions = package_versions()
    shape = validate_problem_shape()
    configuration = solve_configuration()
    logic = crosscheck_logic(configuration)
    plan = generate_plan()
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.reasoning-waist-r1-acceptance",
        "observedDate": "2026-09-14",
        "standing": "PASS_LOCAL_COMPOSED_SMOKE",
        "pythonBinding": "/root/.local/share/ordivon/reasoning-waist/.venv/bin/python",
        "packageVersions": versions,
        "checks": {
            "rdfShaclProblemShape": shape,
            "ortoolsConfiguration": configuration,
            "z3LogicCrosscheck": logic,
            "unifiedPlanning": plan,
        },
        "executionHandoff": "NOT_EXERCISED_BY_THIS_SMOKE",
        "taskShapeSpecificProcessDecisionCaseProvider": {
            "provider": "Flowable",
            "version": "8.0.0",
            "image": "localhost/ordivon-flowable-rest:8.0.0",
            "manifestDigest": "sha256:b67720807e7b091ef46b5e96f191541e1aa67ba0eb284504b5c6e2771d6a5ae2",
            "standing": "MATERIALIZED_ENGINE_BOOT_SMOKE_PASS_PRODUCTION_HOLD_UNTIL_WORKLOAD",
            "partOfCoreWaist": False,
        },
        "boundary": (
            "PASS proves only that mature local reasoning providers compose mechanically on a tiny "
            "bounded case. It does not establish domain model correctness, universal planning competence, "
            "business decision authority, workflow durability or physical execution success."
        ),
    }
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
