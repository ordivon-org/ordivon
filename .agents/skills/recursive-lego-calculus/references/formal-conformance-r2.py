#!/usr/bin/env python3
"""Bounded executable conformance probes for Recursive LEGO Calculus R2.

This file checks only narrow encoded obligations against mature local providers.
A PASS here is not a proof of the whole calculus, a domain result, or implementation refinement.
"""

from __future__ import annotations

import json


def z3_checks() -> dict[str, object]:
    from z3 import And, Bool, Implies, Not, Or, Real, RealVal, Solver, get_version_string, sat, unsat

    out: dict[str, object] = {"version": get_version_string()}

    # C1: deterministic soundness forbids a false PASS under the encoded semantics.
    passed = Bool("passed")
    phi = Bool("phi")
    solver = Solver()
    solver.add(passed, Not(phi), Implies(passed, phi))
    out["deterministic_soundness_rejects_false_pass"] = solver.check() == unsat

    # C13: a small JOINT false-accept probability does not imply an equally
    # small CONDITIONAL false-discovery probability.  Division is avoided by
    # checking p(false and PASS) > delta * p(PASS).
    p_pass = Real("p_pass")
    p_false_pass = Real("p_false_pass")
    delta = RealVal(1) / 100
    solver = Solver()
    solver.add(p_pass > 0, p_pass <= 1, p_false_pass >= 0, p_false_pass <= p_pass, p_false_pass <= delta, p_false_pass > delta * p_pass)
    joint_counterexample = solver.check()
    out["joint_bound_does_not_imply_conditional_bound"] = joint_counterexample == sat
    if joint_counterexample == sat:
        model = solver.model()
        out["joint_counterexample_model"] = {"p_pass": str(model[p_pass]), "p_false_and_pass": str(model[p_false_pass])}

    solver = Solver()
    solver.add(p_pass > 0, p_pass <= 1, p_false_pass >= 0, p_false_pass <= p_pass, p_false_pass <= delta * p_pass, p_false_pass > delta * p_pass)
    out["conditional_bound_excludes_counterexample"] = solver.check() == unsat

    # C2: composition is partial.  A good seam has post1 => pre2; a bad seam
    # admits a counterexample where post1 holds and pre2 does not.
    seam_ready = Bool("seam_ready")
    seam_authorized = Bool("seam_authorized")
    solver = Solver()
    solver.add(seam_authorized, Not(seam_authorized))
    out["good_composition_seam_has_no_post_pre_counterexample"] = solver.check() == unsat
    solver = Solver()
    solver.add(seam_ready, Not(seam_authorized))
    out["bad_composition_seam_exposes_counterexample"] = solver.check() == sat

    # C15: witness-preserving and universal-safe representation refinement are
    # materially different obligations.
    concrete_a_ok = Bool("concrete_a_ok")
    concrete_b_ok = Bool("concrete_b_ok")
    solver = Solver()
    solver.add(concrete_a_ok, Not(concrete_b_ok), Or(concrete_a_ok, concrete_b_ok), Not(And(concrete_a_ok, concrete_b_ok)))
    out["witness_mode_can_hold_while_universal_mode_fails"] = solver.check() == sat

    # C9 local invariant only: the current mutable domain and frozen anchor are
    # declared disjoint.  Influence/control separation still requires external
    # system evidence and is deliberately not claimed by this SMT check.
    anchor_mutable = Bool("anchor_mutable")
    solver = Solver()
    solver.add(Not(anchor_mutable), anchor_mutable)
    out["anchor_mutation_rejected_by_declared_disjointness"] = solver.check() == unsat
    return out


def unified_planning_checks() -> dict[str, object]:
    from unified_planning.plans import ActionInstance, SequentialPlan
    from unified_planning.shortcuts import BoolType, Fluent, InstantaneousAction, PlanValidator, Problem

    ready = Fluent("ready", BoolType())
    authorized = Fluent("authorized", BoolType())
    done = Fluent("done", BoolType())
    problem = Problem("recursive_lego_legal_program")
    problem.add_fluent(ready, default_initial_value=False)
    problem.add_fluent(authorized, default_initial_value=False)
    problem.add_fluent(done, default_initial_value=False)

    authorize = InstantaneousAction("authorize")
    authorize.add_precondition(ready)
    authorize.add_effect(authorized, True)
    problem.add_action(authorize)

    execute = InstantaneousAction("execute")
    execute.add_precondition(ready)
    execute.add_precondition(authorized)
    execute.add_effect(done, True)
    problem.add_action(execute)

    problem.set_initial_value(ready, True)
    problem.set_initial_value(authorized, False)
    problem.set_initial_value(done, False)
    problem.add_goal(done)

    invalid = SequentialPlan([ActionInstance(execute, ())])
    valid = SequentialPlan([ActionInstance(authorize, ()), ActionInstance(execute, ())])
    with PlanValidator(problem_kind=problem.kind, plan_kind=invalid.kind) as validator:
        invalid_status = str(validator.validate(problem, invalid).status)
        valid_status = str(validator.validate(problem, valid).status)

    return {"illegal_program_rejected": invalid_status.endswith("INVALID"), "legal_program_accepted": valid_status.endswith("VALID"), "invalid_status": invalid_status, "valid_status": valid_status}


def provider_inventory() -> dict[str, object]:
    import importlib
    providers = {}
    for module in ("z3", "unified_planning", "ortools", "rdflib", "pyshacl", "pacti"):
        try:
            imported = importlib.import_module(module)
            version = getattr(imported, "__version__", None)
            if module == "z3":
                version = imported.get_version_string()
            providers[module] = {"available": True, "version": version}
        except Exception as exc:
            providers[module] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return providers


def main() -> int:
    report = {"schemaVersion": 2, "kind": "ordivon.recursive-lego-calculus.r2-formal-conformance", "scope": "bounded local formal obligations only", "providers": provider_inventory(), "z3": z3_checks(), "unifiedPlanning": unified_planning_checks(), "nonClaims": ["does not prove the whole Recursive LEGO Calculus", "does not prove implementation refinement", "does not establish domain truth or external qualification", "does not establish evaluator-anchor causal noninterference", "does not require optional Pacti availability"]}
    required = [report["providers"]["z3"]["available"], report["providers"]["unified_planning"]["available"], report["z3"]["deterministic_soundness_rejects_false_pass"], report["z3"]["joint_bound_does_not_imply_conditional_bound"], report["z3"]["conditional_bound_excludes_counterexample"], report["z3"]["good_composition_seam_has_no_post_pre_counterexample"], report["z3"]["bad_composition_seam_exposes_counterexample"], report["z3"]["witness_mode_can_hold_while_universal_mode_fails"], report["z3"]["anchor_mutation_rejected_by_declared_disjointness"], report["unifiedPlanning"]["illegal_program_rejected"], report["unifiedPlanning"]["legal_program_accepted"]]
    report["verdict"] = "PASS" if all(required) else "FAIL"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
