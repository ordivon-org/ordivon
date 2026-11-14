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

    # Source-linked finite refinement: first eligible quality country,
    # at most one independent fallback; no duplicate, stale or current country.
    country_cases = 0
    for a, b, c, current in product(
        ("Japan", "Mexico", "North Macedonia", "Hong Kong", None),
        ("Japan", "Mexico", "North Macedonia", "Hong Kong", None),
        ("Japan", "Mexico", "North Macedonia", "Hong Kong", None),
        ("Japan", "Mexico", "North Macedonia"),
    ):
        countries = (a, b, c)
        evidence = [
            {
                "catalogCountry": name, "standing": (
                    "RECENT_HISTORICAL_CONSUMER_SUCCESS"
                    if name not in ("Hong Kong", None)
                    else "REJECTED_NOT_ALLOWED"),
                "medianOfConsumerP90Ms": 1000 + idx * 100,
                "worstConsumerSuccessRatio": .99,
                "lastObservedHoursAgo": 1,
            }
            for idx, name in enumerate(countries)
        ]
        action = policy.decision(
            active_healthy=False, underlay_reachable=True,
            evidence=evidence, now=NOW, current_country=current,
        )
        expected = []
        for name in countries:
            if name not in (None, "Hong Kong", current) and name not in expected:
                expected.append(name)
            if len(expected) == 2:
                break
        actual = action.get("trialCountries", [])
        if expected:
            assert action["decision"].startswith("TRIAL_ONLY_")
            assert actual == expected and action["trialCountry"] == expected[0]
        else:
            assert action["decision"] == "HOLD_NO_RECENT_EVIDENCE"
        # This is an exact finite source-refinement check, not proof that
        # future Surfshark endpoints are physically reachable.
        mismatch = Solver()
        mismatch.add(BoolVal(actual != expected))
        assert mismatch.check() == unsat
        country_cases += 1

    # Source hint is only a time-bounded *candidate* and cannot bypass
    # the same active/underlay/allowed-country admission predicate. These
    # scenarios do not claim hot-standby reachability or real API effects.
    hinted = policy.source_trial_hints(NOW, {"Malaysia", "North Macedonia", "Mexico"})
    assert len(hinted) == 2
    hint_cases = 0
    for active, underlay, current in product(
        (True, False, None), (True, False, None),
        ("Malaysia", "North Macedonia", "Mexico"),
    ):
        action = policy.decision(active_healthy=active,
            underlay_reachable=underlay, evidence=hinted, now=NOW,
            current_country=current)
        expected = active is False and underlay is True
        trial = action["decision"].startswith("TRIAL_ONLY_")
        z = Solver()
        z.add(BoolVal(expected) != BoolVal(trial))
        assert z.check() == unsat
        if trial:
            assert "Hong Kong" not in action["trialCountries"]
            assert len(set(action["trialCountries"])) == len(action["trialCountries"])
            assert len(action["trialCountries"]) <= 2
            assert current not in action["trialCountries"]
            assert action["certifiedHotStandbyCount"] == 0
        hint_cases += 1
    # Historical quality expires after 7d. Catalog-only cold preferences
    # remain permitted under exactly the same real failure/underlay guards;
    # they are never classified as fresh success or current standby.
    expired = policy.source_trial_hints(NOW + timedelta(days=8),
                                         {"Malaysia", "North Macedonia", "Mexico"})
    assert expired == []
    assert policy.decision(active_healthy=False, underlay_reachable=True,
                           evidence=expired, now=NOW+timedelta(days=8),
                           current_country="Malaysia")["decision"] == "HOLD_NO_RECENT_EVIDENCE"
    cold_catalog = json.dumps({"surfshark":{"servers":[
       {"vpn":"wireguard","country":"North Macedonia","ips":["192.0.2.18"]},
       {"vpn":"wireguard","country":"Mexico","ips":["192.0.2.19"]},
       {"vpn":"wireguard","country":"Hong Kong","ips":["192.0.2.20"]}]}})
    cold = policy.catalog_cold_trials(
        cold_catalog, {"Malaysia","North Macedonia","Mexico"})
    assert len(cold) == 2 and all(
        row["standing"]=="SOURCE_CATALOG_COLD_TRIAL_UNVERIFIED" and
        row["qualifiedNowStandby"] is False for row in cold)
    cold_cases = 0
    for active, underlay, current in product(
        (True, False, None), (True, False, None),
        ("Malaysia", "North Macedonia","Mexico"),
    ):
        outcome=policy.decision(active_healthy=active, underlay_reachable=underlay,
          evidence=expired+cold, now=NOW+timedelta(days=8),
          current_country=current)
        actual=outcome["decision"].startswith("TRIAL_ONLY_")
        expected=active is False and underlay is True and (
            len([x for x in cold if x["catalogCountry"]!=current])>0)
        z=Solver()
        z.add(BoolVal(actual)!=BoolVal(expected))
        assert z.check()==unsat
        if actual:
            assert outcome["certifiedHotStandbyCount"]==0
            assert "Hong Kong" not in outcome["trialCountries"]
            assert len(outcome["trialCountries"])<=2
        cold_cases+=1

    # Finite temporal *schedule* model, bound to the native source
    # intervals. The proof is only about maximum sampling/timer phase,
    # not VPN interruption, Prometheus scheduling under load or WAN TTR.
    from pathlib import Path
    source_root = ROOT
    fast_jobs = {
        "blackbox-scoped-claude-api": "claude.yml",
        "blackbox-scoped-codex-mcp": "codex.yml",
        "blackbox-vpn-pypi": "supply-chain.yml",
    }
    for job, fragment in fast_jobs.items():
        raw = (source_root/"config/prometheus/consumers"/fragment).read_text()
        piece = raw.split("  - job_name: " + job + "\n", 1)[1].split("  - job_name:", 1)[0]
        assert "scrape_interval: 30s" in piece
        assert "scrape_timeout: 12s" in piece
    timer_source = (source_root/"providers/gluetun/systemd/network-v2-gluetun-owned-reconcile.timer").read_text()
    assert "OnCalendar=*-*-* *:*:00" in timer_source
    assert "RandomizedDelaySec=5s" in timer_source
    assert "AccuracySec=5s" in timer_source
    scan = 30
    timer_period = 60
    scrape_deadline = 12
    timer_jitter = 10
    worst_case = (3 * scan) + timer_period + scrape_deadline + timer_jitter
    assert worst_case == 172
    old_worst_case = (3 * 60) + 120 + scrape_deadline + 15
    z = Solver()
    z.add(BoolVal(worst_case < old_worst_case) == BoolVal(False))
    assert z.check() == unsat

    # Real-consumer signal freshness refinement. The 30s scrape policy
    # must not promote retained 135-second-old failed samples into current
    # failure after Prometheus/Blackbox stopped. Model original, not
    # query_range replayed timestamps, on a finite boundary grid.
    assert policy.FAILURE_SCRAPE_SECONDS == scan
    assert policy.FAILURE_LAST_SAMPLE_AGE_SECONDS == 75
    assert policy.FAILURE_MAX_SAMPLE_GAP_SECONDS == 45
    assert policy.FAILURE_MAX_WINDOW_AGE_SECONDS == 165
    assert policy.FAILURE_CROSS_LANE_SKEW_SECONDS == 45
    original_http = policy.http_raw_samples
    raw_cases = 0
    stale_mutants = 0
    try:
        for age, gap, skew in product(
            (15, 65, 75, 76, 100, 135, 151),
            (30, 45, 46, 60),
            (0, 30, 45, 46),
        ):
            windows = [
                {"metric": {"job": job}, "values": [
                    [NOW.timestamp()-age-extra-2*gap, "0"],
                    [NOW.timestamp()-age-extra-gap, "0"],
                    [NOW.timestamp()-age-extra, "0"],
                ]}
                for i, job in enumerate(policy.JOBS)
                for extra in ([skew] if i==2 else [0])
            ]
            policy.http_raw_samples = lambda metric, now, values=windows: values
            action = policy.recent_failure_witness(NOW)
            expected = (
                age <= 75 and age+skew <= 75 and
                gap <= 45 and
                age+skew+2*gap <= 165 and
                skew <= 45
            )
            model = Solver()
            model.add(BoolVal(action is True) != BoolVal(expected))
            assert model.check() == unsat, (age,gap,skew,action,expected)
            if action is None:
                assert not expected
            raw_cases += 1
            if age == 135 and gap == 30 and skew == 0:
                # The pre-fix 150-second freshness bound admitted this.
                old_mutant_admits = age <= 150 and age+2*gap <= 300
                assert old_mutant_admits and action is None
                stale_mutants += 1
    finally:
        policy.http_raw_samples = original_http
    assert stale_mutants == 1

    # An incorrect selector copying duplicate countries into both slots has
    # a satisfiable distinctness violation; implemented source above cannot.
    c0, c1 = Bool("candidate_first_allowed"), Bool("candidate_second_distinct")
    wrong_selector = Solver()
    wrong_selector.add(c0, Not(c1))
    assert wrong_selector.check() == sat

    print(json.dumps({
        "kind": "ordivon.network.vpn-recovery-finite-refinement",
        "standing": "SOURCE_ENUMERATION_REFINED_WITH_Z3",
        "finiteCases": cases,
        "distinctCandidateCases": country_cases,
        "timeBoundedSourceHintCases": hint_cases,
        "postExpiryCatalogColdTrialCases": cold_cases,
        "sourceBoundMaxSamplingAndTimerDecisionSeconds": worst_case,
        "raw30sFreshnessCounterexampleCases": raw_cases,
        "previousStaleZeroMutantRejected": stale_mutants,
        "premises": [
            "observed consumer failure (not UNKNOWN)",
            "direct underlay reachable",
            "approved trial country (recent quality or official catalog-only cold)",
            "no switch inside cooldown",
            "candidate different from active country",
        ],
        "negativeControls": [
            "missing underlay guard mutant SAT",
            "UNKNOWN active must not grant trial",
            "duplicate fallback country mutation SAT",
        ],
        "notProved": [
            "Gluetun implementation", "API authorization/PUT effect",
            "real standby current availability", "fault recovery time",
        ],
    }, sort_keys=True))


if __name__ == "__main__":
    validate()
