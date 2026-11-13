#!/usr/bin/env python3
"""Finite Z3 refinement of source country permission -> native Gluetun filter.

Only the checked-in candidate/allowlist semantics and generated config are
proved. It does not prove server availability, liveness, or UDP behavior.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

from z3 import And, Bool, BoolVal, Not, Or, Solver, sat, unsat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "providers/gluetun"))
import native_profile as gluetun  # noqa: E402


def parse_native_filter(env: str, catalog: set[str]) -> set[str]:
    lines = [l.removeprefix("SERVER_COUNTRIES=") for l in env.splitlines()
             if l.startswith("SERVER_COUNTRIES=")]
    if len(lines) != 1:
        # In pinned v3.41.3, an omitted positive filter means ALL countries.
        return catalog
    return set(lines[0].split(","))


def violation(
    selected: set[str], permitted: set[str], catalog: set[str],
) -> tuple[object, str | None]:
    names = sorted(catalog | selected | permitted)
    s = Solver()
    selected_vars = {country: Bool(f"native_selected_{i}") for i, country in enumerate(names)}
    # Concrete generated native Gluetun filter is bound to symbolic countries.
    for country, var in selected_vars.items():
        s.add(var == BoolVal(country in selected))
    s.add(Or(*[
        And(var, Not(BoolVal(country in permitted)))
        for country, var in selected_vars.items()
    ]))
    status = s.check()
    return status, next(
        (country for country in names if country in selected and country not in permitted),
        None,
    ) if status == sat else None


def run() -> None:
    allowed = gluetun.parse_allowed_policy(gluetun.ALLOW_POLICY.read_text())
    selected = gluetun.read_selector_policy()
    perm = set(allowed["allowedCountries"])
    excluded = set(allowed["excludedCountries"])
    choices = set(selected["selectedCountries"])
    # A synthetic unrecognized country cannot become implicitly authorized.
    universe = perm | excluded | {"__not_in_official_catalog__"}
    assert perm and excluded == {"Hong Kong"}
    assert not (perm & excluded)

    base = gluetun.parse_env("VPN_SERVICE_PROVIDER=custom\nVPN_TYPE=wireguard\n")
    env = gluetun.generate_env(base, "10.64.200.9/16")
    actual = parse_native_filter(env, universe)
    expected = choices
    if actual != expected:
        raise AssertionError("native generator does not refine source-selected countries")

    result, counterexample = violation(actual, perm, universe)
    assert result == unsat and counterexample is None
    # Real runtime must not omit positive Gluetun country filter, even when
    # catalog/permissions are available as separate policy input.
    omitted = "\n".join(
        l for l in env.splitlines() if not l.startswith("SERVER_COUNTRIES=")
    )
    exposed = parse_native_filter(omitted, universe)
    bad_omitted, country = violation(exposed, perm, universe)
    assert bad_omitted == sat and country not in perm

    # Source-level negative control for malformed candidate admission.
    candidate = gluetun.parse_candidate_policy(
        json.dumps({"regions": [], "selectedCountries": ["Japan"]}), allowed
    )
    assert set(candidate["selectedCountries"]) <= perm
    try:
        gluetun.parse_candidate_policy(
            json.dumps({"regions": [], "selectedCountries": ["Japan", "Hong Kong"]}),
            allowed,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("forbidden candidate admitted by parser")

    # Independent counterexample to treating repeated failed connections as
    # proof that each Surfshark endpoint is bad: a common underlay failure
    # makes even an otherwise-good endpoint unobservable.
    endpoint_healthy = BoolVal(True)
    physical_underlay = BoolVal(False)
    observed_healthy = And(endpoint_healthy, physical_underlay)
    common_cause = Solver()
    common_cause.add(endpoint_healthy, Not(observed_healthy))
    assert common_cause.check() == sat

    print(json.dumps({
        "kind": "ordivon.network.gluetun-candidate-admission-formal",
        "scope": "checked-in countries and native env source only",
        "standing": "FINITE_SOURCE_REFINEMENT_PROVED",
        "allowedCountryCount": len(perm),
        "candidateCountryCount": len(choices),
        "nativeCountryFilter": "MATCH",
        "negativeControls": [
            "no SERVER_COUNTRIES filter => forbidden country SAT",
            "explicit Hong Kong candidate => parser rejects",
            "shared underlay DOWN with healthy endpoint => connection failure SAT",
        ],
        "unproved": [
            "actual Surfshark catalog freshness and individual endpoint health",
            "current loaded container and iOS consumer effects",
            "actual fast recovery time or qualified standby availability",
        ],
    }, sort_keys=True))


if __name__ == "__main__":
    run()
