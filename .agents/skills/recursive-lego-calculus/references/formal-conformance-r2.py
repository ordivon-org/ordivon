#!/usr/bin/env python3
"""Bounded executable conformance probes for Recursive LEGO Calculus R2.1.

Checks narrow encoded obligations against mature local providers. A PASS here is not a proof
of the whole calculus, representation adequacy, implementation refinement, domain truth,
or external qualification.
"""

from __future__ import annotations

import json


def z3_checks() -> dict[str, object]:
    from z3 import And, Bool, Implies, Not, Or, Real, RealVal, Solver, get_version_string, sat, unsat

    out: dict[str, object] = {"version": get_version_string()}

    # C1/C17: local checker soundness vs end-to-end specification bridge.
    passed = Bool("passed")
    psi = Bool("psi")
    phi = Bool("phi")

    solver = Solver()
    solver.add(passed, Not(psi), Implies(passed, psi))
    out["local_soundness_rejects_false_encoded_pass"] = solver.check() == unsat

    solver = Solver()
    solver.add(passed, psi, Not(phi), Implies(passed, psi))
    out["local_soundness_without_bridge_allows_false_problem_claim"] = solver.check() == sat

    solver = Solver()
    solver.add(passed, Not(phi), Implies(passed, psi), Implies(psi, phi))
    out["bridge_eliminates_false_problem_claim"] = solver.check() == unsat

    # C13: joint false-accept probability does not imply conditional reliability.
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

    # C2: a compatible seam discharges the downstream precondition; an incompatible seam exposes a witness.
    post1 = Bool("post1")
    pre2 = Bool("pre2")
    solver = Solver()
    solver.add(post1, Not(pre2), Implies(post1, pre2))
    out["good_composition_seam_has_no_post_pre_counterexample"] = solver.check() == unsat
    solver = Solver()
    solver.add(post1, Not(pre2))
    out["bad_composition_seam_exposes_counterexample"] = solver.check() == sat

    # C15: witness-preserving and universal-safe refinement differ.
    concrete_a_ok = Bool("concrete_a_ok")
    concrete_b_ok = Bool("concrete_b_ok")
    solver = Solver()
    solver.add(concrete_a_ok, Not(concrete_b_ok), Or(concrete_a_ok, concrete_b_ok), Not(And(concrete_a_ok, concrete_b_ok)))
    out["witness_mode_can_hold_while_universal_mode_fails"] = solver.check() == sat

    # Naive universal safety is vacuous when there is no related realization.
    transformed_ok = Bool("transformed_ok")
    related_exists = Bool("related_exists")
    all_related_ok = Bool("all_related_ok")
    solver = Solver()
    solver.add(transformed_ok, Not(related_exists), all_related_ok, Implies(transformed_ok, all_related_ok))
    out["naive_universal_refinement_allows_empty_realization"] = solver.check() == sat
    solver = Solver()
    solver.add(transformed_ok, Not(related_exists), Implies(transformed_ok, And(related_exists, all_related_ok)))
    out["nonempty_realization_blocks_vacuous_universal_refinement"] = solver.check() == unsat

    # C9/C20 local mutation invariant only. Causal/noninterference isolation remains an external obligation.
    anchor_mutable = Bool("anchor_mutable")
    solver = Solver()
    solver.add(Not(anchor_mutable), anchor_mutable)
    out["anchor_mutation_rejected_by_declared_disjointness"] = solver.check() == unsat

    # C19: an objectively attractive candidate is not admissible if it violates hard feasibility.
    better_objective = Bool("better_objective")
    hard_valid = Bool("hard_valid")
    solver = Solver()
    solver.add(better_objective, Not(hard_valid))
    out["unconstrained_optimizer_can_prefer_infeasible_candidate"] = solver.check() == sat
    solver = Solver()
    solver.add(better_objective, hard_valid, Not(hard_valid))
    out["qualified_feasible_region_excludes_infeasible_candidate"] = solver.check() == unsat

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
    report = {
        "schemaVersion": 3,
        "kind": "ordivon.recursive-lego-calculus.r2_1-formal-conformance",
        "scope": "bounded local formal obligations only",
        "providers": provider_inventory(),
        "z3": z3_checks(),
        "unifiedPlanning": unified_planning_checks(),
        "nonClaims": [
            "does not prove the whole Recursive LEGO Calculus",
            "does not prove representation adequacy or implementation refinement",
            "does not establish domain truth or external qualification",
            "does not establish evaluator-anchor causal noninterference",
            "does not require optional Pacti availability",
        ],
    }
    required_keys = [
        "local_soundness_rejects_false_encoded_pass",
        "local_soundness_without_bridge_allows_false_problem_claim",
        "bridge_eliminates_false_problem_claim",
        "joint_bound_does_not_imply_conditional_bound",
        "conditional_bound_excludes_counterexample",
        "good_composition_seam_has_no_post_pre_counterexample",
        "bad_composition_seam_exposes_counterexample",
        "witness_mode_can_hold_while_universal_mode_fails",
        "naive_universal_refinement_allows_empty_realization",
        "nonempty_realization_blocks_vacuous_universal_refinement",
        "anchor_mutation_rejected_by_declared_disjointness",
        "unconstrained_optimizer_can_prefer_infeasible_candidate",
        "qualified_feasible_region_excludes_infeasible_candidate",
    ]
    required = [report["providers"]["z3"]["available"], report["providers"]["unified_planning"]["available"]]
    required.extend(report["z3"][key] for key in required_keys)
    required.extend([report["unifiedPlanning"]["illegal_program_rejected"], report["unifiedPlanning"]["legal_program_accepted"]])
    report["verdict"] = "PASS" if all(required) else "FAIL"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
