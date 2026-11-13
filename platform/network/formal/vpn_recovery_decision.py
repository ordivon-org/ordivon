#!/usr/bin/env python3
"""Finite source-linked Z3 refinement of one-shot VPN recovery admission.

Exhausts three-state consumer/underlay evidence, candidate evidence,
cooldown and same-active-country states. No claim about actual Gluetun or WG.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import product
import json
from pathlib import Path
import sys
from z3 import And, Bool, BoolVal, Not, Or, Solver, sat, unsat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "providers/gluetun"))
import quality_history as policy  # noqa: E402

NOW = datetime(2026, 11, 14, tzinfo=timezone.utc)


def source_decision(active: bool | None, underlay: bool | None,
                    evidence: bool, cooldown: bool, same: bool) -> bool:
    candidate = {
        "catalogCountry": "Mexico",
        "standing": "RECENT_HISTORICAL_CONSUMER_SUCCESS",
        "medianOfConsumerP90Ms": 1200,
        "lastObservedHoursAgo": 1,
        "worstConsumerSuccessRatio": .99,
    }
    action = policy.decision(
        active_healthy=active, underlay_reachable=underlay,
        evidence=[candidate] if evidence else [], now=NOW,
        last_switch=NOW-timedelta(minutes=3) if cooldown else None,
        current_country="Mexico" if same else "Japan",
    )
    return action["decision"].startswith("TRIAL_ONLY_")


def validate() -> None:
    c_active = Bool("active_known_failed")
    c_underlay = Bool("underlay_reachable")
    c_evidence = Bool("historical_candidate_eligible")
    c_notcooling = Bool("outside_cooldown")
    c_different = Bool("different_country")
    spec = And(c_active, c_underlay, c_evidence, c_notcooling, c_different)
    mismatches = []
    cases = 0
    for active, underlay, evidence, cooling, same in product(
        (True, False, None), (True, False, None), (True, False),
        (True, False), (True, False),
    ):
        cases += 1
        implemented = source_decision(active, underlay, evidence, cooling, same)
        s = Solver()
        s.add(c_active == BoolVal(active is False))
        s.add(c_underlay == BoolVal(underlay is True))
        s.add(c_evidence == BoolVal(evidence))
        s.add(c_notcooling == BoolVal(not cooling))
        s.add(c_different == BoolVal(not same))
        s.add(spec != BoolVal(implemented))
        if s.check() != unsat:
            mismatches.append((active, underlay, evidence, cooling, same))
    if mismatches:
        raise AssertionError(f"Source policy not refined by finite model: {mismatches!r}")

    # A mutant omitting underlay-failure guard must produce a counterexample.
    mutant = And(c_active, c_evidence, c_notcooling, c_different)
    s = Solver()
    s.add(mutant, Not(c_underlay))
    assert s.check() == sat

    # A mutant treating UNKNOWN active as failure has a counterexample.
    q = Solver()
    q.add(c_active == BoolVal(True), c_underlay, c_evidence, c_notcooling, c_different)
    assert q.check() == sat

    print(json.dumps({
        "kind": "ordivon.network.vpn-recovery-finite-refinement",
        "standing": "SOURCE_ENUMERATION_REFINED_WITH_Z3",
        "finiteCases": cases,
        "premises": [
            "observed consumer failure (not UNKNOWN)",
            "direct underlay reachable",
            "recent allowed historical candidate",
            "no switch inside cooldown",
            "candidate different from active country",
        ],
        "negativeControls": [
            "missing underlay guard mutant SAT",
            "UNKNOWN active must not grant trial",
        ],
        "notProved": [
            "Gluetun implementation", "API authorization/PUT effect",
            "real standby current availability", "fault recovery time",
        ],
    }, sort_keys=True))


if __name__ == "__main__":
    validate()
