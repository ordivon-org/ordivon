from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
S = importlib.util.spec_from_file_location(
    "social_fabric_flow_r1", ROOT / "scripts/social_fabric_flow_r1.py"
)
m = importlib.util.module_from_spec(S)
assert S.loader
S.loader.exec_module(m)


def pair():
    def cut(t, a, b):
        return {
            "observedAt": t,
            "sourceRefs": [f"host:{t}"],
            "counters": {
                "host.tasks": {
                    "value": a,
                    "owner": "host",
                    "unit": "task-record",
                    "counterSemantics": "monotonic",
                },
                "host.events": {
                    "value": b,
                    "owner": "host",
                    "unit": "event-record",
                    "counterSemantics": "monotonic",
                },
            },
        }

    return {
        "schemaVersion": 1,
        "kind": "ordivon.social-fabric-counter-cut-pair",
        "start": cut("2026-09-23T00:00:00+08:00", 10, 100),
        "end": cut("2026-09-23T01:00:00+08:00", 12, 118),
        "coverage": {"standing": "BOUNDED_OWNER_COUNTERS", "scope": "host-v2"},
    }


def test_dimensional_rates_are_deterministic():
    p = pair()
    a = m.compile_flux(p)
    assert a == m.compile_flux(p)
    x = {r["metric"]: r for r in a["metrics"]}
    assert a["windowSeconds"] == 3600
    assert x["host.tasks"]["delta"] == 2
    assert x["host.tasks"]["rate"]["perHour"] == 2
    assert x["host.tasks"]["rate"]["dimensions"]["perHour"] == "task-record/hour"


def test_nonpositive_window_fails():
    p = pair()
    p["end"]["observedAt"] = p["start"]["observedAt"]
    with pytest.raises(m.SocialFluxError, match="end must be after start"):
        m.compile_flux(p)


def test_contract_drift_fails():
    p = pair()
    p["end"]["counters"]["host.tasks"]["unit"] = "banana"
    with pytest.raises(m.SocialFluxError, match="counter contract drift"):
        m.compile_flux(p)


def test_monotonic_regression_fails_closed():
    p = pair()
    p["end"]["counters"]["host.tasks"]["value"] = 9
    with pytest.raises(m.SocialFluxError, match="regressed"):
        m.compile_flux(p)


def test_key_mismatch_fails():
    p = pair()
    del p["end"]["counters"]["host.events"]
    with pytest.raises(m.SocialFluxError, match="counter key mismatch"):
        m.compile_flux(p)


def test_no_priority_or_score_claim():
    raw = json.dumps(m.compile_flux(pair())).lower()
    assert (
        '"priority"' not in raw
        and '"score"' not in raw
        and "effectauthoritygranted" not in raw
    )


def test_real_host_dogfood_fixture():
    p = json.loads(
        (
            ROOT / "evidence/acceptance/social-fabric-flow-r1-host-pair-20260923.json"
        ).read_text()
    )
    r = m.compile_flux(p)
    x = {q["metric"]: q for q in r["metrics"]}
    assert x["host.task_records"]["delta"] == 9
    assert x["host.task_events"]["delta"] == 29
    assert x["host.board_messages"]["delta"] == 3
    assert r["coverage"]["standing"] == "BOUNDED_OWNER_COUNTERS"
