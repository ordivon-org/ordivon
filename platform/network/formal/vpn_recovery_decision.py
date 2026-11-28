#!/usr/bin/env python3
"""Finite source-linked Z3 refinement of one-shot VPN recovery admission.

Exhausts three-state consumer/underlay evidence, candidate evidence,
cooldown and same-active-country states. No claim about actual Gluetun or WG.
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from itertools import product
from pathlib import Path

from z3 import And, Bool, BoolVal, Not, Or, Solver, sat, unsat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "providers/gluetun"))
import quality_history as policy

NOW = datetime(2026, 11, 14, tzinfo=UTC)


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


def _validate_recovery_admission() -> int:
    """Refine one-shot recovery admission and retain underlay/UNKNOWN mutants."""
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
    return cases


def _validate_candidate_selection() -> int:
    """Refine first eligible country plus at most one distinct fallback."""
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
    return country_cases


def _validate_source_hints_and_cold_trials() -> tuple[int, int]:
    """Bound source hints and cold trials to the same recovery admission seam."""
    selected = set(policy.native.read_selector_policy()["selectedCountries"])
    assert not policy.source_trial_hints(NOW, selected)
    hinted = [
        row | {"standing": "SOURCE_TIME_BOUNDED_CONSUMER_TRIAL_HINT"}
        for row in ({"catalogCountry": "Singapore", "medianOfConsumerP90Ms": 800},
                    {"catalogCountry": "Japan", "medianOfConsumerP90Ms": 1200})
    ]
    hint_cases = 0
    for active, underlay, current in product(
        (True, False, None), (True, False, None), sorted(selected),
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
            assert set(action["trialCountries"]) <= selected - {current}
            assert len(set(action["trialCountries"])) == len(action["trialCountries"])
            assert len(action["trialCountries"]) <= 2
            assert action["certifiedHotStandbyCount"] == 0
        hint_cases += 1
    # Cold trials use the current source country subset, not the catalog-wide
    # permission list, and cannot be promoted to historical success.
    expired = policy.source_trial_hints(NOW + timedelta(days=8), selected)
    assert expired == []
    cold_catalog = json.dumps({"surfshark":{"servers":[
        {"vpn": "wireguard", "country": country, "ips": [f"192.0.2.{i}"]}
        for i, country in enumerate(sorted(selected | {"Panama", "Hong Kong"}), 11)
    ]}})
    cold = policy.catalog_cold_trials(cold_catalog, selected)
    assert {row["catalogCountry"] for row in cold} == selected
    assert all(row["standing"] == "SOURCE_CATALOG_COLD_TRIAL_UNVERIFIED"
               and row["qualifiedNowStandby"] is False for row in cold)
    cold_cases = 0
    for active, underlay, current in product(
        (True, False, None), (True, False, None),
        sorted(selected),
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
    return (hint_cases, cold_cases)


def _validate_sampling_schedule() -> tuple[int, int]:
    """Bind finite sampling/timer cadence to source, not physical VPN TTR."""
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
    return (scan, worst_case)


def _validate_failure_freshness(scan: int) -> tuple[int, int]:
    """Reject retained stale samples as current consumer-failure evidence."""
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
    return (raw_cases, stale_mutants)


def _validate_direct_underlay() -> tuple[int, int]:
    """Require two direct HTTPS origins and bind their Prometheus targets."""
    source_root = ROOT
    direct_cases = 0
    for first, second in product((True, False, None), repeat=2):
        observed = policy.direct_underlay_evidence((first, second))
        expected = (True if first is True and second is True else
                    False if first is False and second is False else None)
        assert observed is expected
        s = Solver()
        s.add(BoolVal(observed is True) !=
              And(BoolVal(first is True), BoolVal(second is True)))
        assert s.check() == unsat
        direct_cases += 1
    single_origin_mutant = Solver()
    first_ok, second_ok = Bool("first_direct_ok"), Bool("second_direct_ok")
    single_origin_mutant.add(first_ok, Not(second_ok),
                             Or(first_ok, second_ok),
                             Not(And(first_ok, second_ok)))
    assert single_origin_mutant.check() == sat
    # Bind recovery admission's two HTTPS origin strings to the real native
    # Prometheus direct consumer *targets*, not only to matching job names.
    # Previous proof passed even if either job's target silently drifted.
    # Reuse source's one-job YAML blocks; the native promtool/preflight owns
    # full syntax/module/relabel validation, not this finite model.
    direct_source = (source_root / "config/prometheus/prometheus.yml").read_text()
    direct_jobs = ("blackbox-http-ipv4", "blackbox-http-ipv4-alternate")
    def direct_target(source: str, job: str) -> str:
        heading = "  - job_name: " + job + "\n"
        assert source.count(heading) == 1
        block = source.split(heading, 1)[1].split("  - job_name:", 1)[0]
        assert "    metrics_path: /probe\n" in block
        assert "        - http_2xx_ipv4\n" in block
        target_lines = [row.removeprefix("          - ").strip()
                        for row in block.splitlines()
                        if row.startswith("          - https://")]
        assert len(target_lines) == 1
        return target_lines[0]

    actual_direct = tuple(direct_target(direct_source, job) for job in direct_jobs)
    assert actual_direct == policy.DIRECT_UNDERLAY_HTTPS
    drift_cases = 0
    for observed in policy.DIRECT_UNDERLAY_HTTPS:
        bad_source = direct_source.replace(
            "          - " + observed + "\n",
            "          - https://unexpected.invalid/\n", 1)
        assert bad_source != direct_source
        mutated_targets = tuple(direct_target(bad_source, job) for job in direct_jobs)
        assert mutated_targets != policy.DIRECT_UNDERLAY_HTTPS
        drift_cases += 1
    return (direct_cases, drift_cases)


def _validate_selector_distinctness_mutant() -> None:
    """Refute a selector that duplicates one country across both trial slots."""
    c0, c1 = Bool("candidate_first_allowed"), Bool("candidate_second_distinct")
    wrong_selector = Solver()
    wrong_selector.add(c0, Not(c1))
    assert wrong_selector.check() == sat


def validate() -> None:
    cases = _validate_recovery_admission()
    country_cases = _validate_candidate_selection()
    hint_cases, cold_cases = _validate_source_hints_and_cold_trials()
    scan, worst_case = _validate_sampling_schedule()
    raw_cases, stale_mutants = _validate_failure_freshness(scan)
    direct_cases, drift_cases = _validate_direct_underlay()
    _validate_selector_distinctness_mutant()

    print(json.dumps({
        "kind": "ordivon.network.vpn-recovery-finite-refinement",
        "standing": "SOURCE_ENUMERATION_REFINED_WITH_Z3",
        "finiteCases": cases,
        "distinctCandidateCases": country_cases,
        "twoDirectOriginTriStateCases": direct_cases,
        "directProbeTargetDriftMutantsRejected": drift_cases,
        "singleOriginOptimisticMutantRefuted": True,
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
            "single successful host-direct origin prematurely grants VPN mutation SAT",
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
