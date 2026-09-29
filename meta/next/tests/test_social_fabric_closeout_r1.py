import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from social_fabric_closeout_r1 import (  # noqa: E402
    CloseoutError,
    compile_gate,
    validate_cascade,
    validate_concurrency,
    validate_dogfood,
)

E = ROOT / "evidence" / "acceptance"


def load(n):
    return json.loads((E / n).read_text(encoding="utf-8"))


def test_concurrency_measurement_keeps_petri_unauthorized_without_gap():
    out = validate_concurrency(
        load("social-fabric-concurrency-gap-measurement-r1-20260924.json")
    )
    assert out["inScopeMissCount"] == 0
    assert out["petriPrototypeAuthorized"] is False


def test_owner_enforced_conflict_is_not_social_gap():
    d = load("social-fabric-concurrency-gap-measurement-r1-20260924.json")
    row = next(
        r
        for r in d["cases"]
        if r["observedCaseId"] == "CONC-PAPER2-RUNTIME-DEPLOYMENT-FENCE"
    )
    assert row["actualConflictObserved"] and not row["inSocialScope"]


def test_cascade_measurement_distinguishes_repetition_from_self_amplification():
    out = validate_cascade(load("social-fabric-cascade-measurement-r1-20260924.json"))
    assert out["provenCascadeCount"] == 0
    assert out["detectorAuthorized"] is False


def test_wave7_has_all_four_domains_and_preserves_owner_boundary():
    out = validate_dogfood(load("social-fabric-wave7-dogfood-r1-20260924.json"))
    assert out["caseCount"] == 4 and out["ownerBoundaryPreserved"]


def test_gate_kills_unjustified_advanced_mechanisms():
    out = compile_gate(
        load("social-fabric-concurrency-gap-measurement-r1-20260924.json"),
        load("social-fabric-cascade-measurement-r1-20260924.json"),
        load("social-fabric-wave7-dogfood-r1-20260924.json"),
        load("social-fabric-gate79-decisions-r1-20260924.json"),
        False,
    )
    by = {r["lego"]: r["decision"] for r in out["decisions"]}
    assert by["CONC62"] == "KILL"
    assert by["CascadeDetector"] == "KILL"
    assert by["SIG34"] == "HOLD"
    assert by["AgentUXViews"] == "PROMOTE"
    assert by["SocialPreflight"] == "PROMOTE"


def test_gate_rejects_petri_promotion_without_measured_gap():
    ds = load("social-fabric-gate79-decisions-r1-20260924.json")
    ds = [dict(x) for x in ds]
    next(x for x in ds if x["lego"] == "CONC62")["decision"] = "PROMOTE"
    try:
        compile_gate(
            load("social-fabric-concurrency-gap-measurement-r1-20260924.json"),
            load("social-fabric-cascade-measurement-r1-20260924.json"),
            load("social-fabric-wave7-dogfood-r1-20260924.json"),
            ds,
            False,
        )
    except CloseoutError:
        return
    assert False, "expected CloseoutError"
