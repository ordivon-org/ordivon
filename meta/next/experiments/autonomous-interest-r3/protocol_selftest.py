#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import evaluator_reference as er
import selection_reference as sr

SCHEMA = ROOT / "domains/game/game-autonomous-interest-model-r3.schema.json"
PROTOCOL = ROOT / "domains/game/game-autonomous-interest-protocol-r3.json"
MODEL = HERE / "selftest_model.json"
CHECK_JSONSCHEMA = "/root/.local/bin/check-jsonschema"


def schema_validate():
    subprocess.run([CHECK_JSONSCHEMA, "--schemafile", str(SCHEMA), str(MODEL)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_p0_visible_state_only(model):
    m = copy.deepcopy(model)
    # Force two distinct hidden state IDs to expose the same visible decision state.
    m["states"]["t0"]["observation"] = {"same": 1}
    m["states"]["t3"]["observation"] = {"same": 1}
    # Keep same legal set/order.
    assert er.ordered_legal(m, "t0") == er.ordered_legal(m, "t3") == ["a", "b", "c"]
    assert er.p0_action(m, "t0") == er.p0_action(m, "t3")
    # P0 has no seed/context/time parameter, so there is no alternate hidden input path.
    assert er.p0_action.__code__.co_argcount == 2


def test_state_keyed_duplicate_detection(model):
    ag = er.agency_and_duplicates(model)
    assert ["a", "b"] in ag["duplicateActionPairs"]
    row = ag["pairRates"]["a|b"]
    assert row["coObserved"] > 0
    assert row["equivalent"] == row["coObserved"]
    assert row["rate"] == 1.0


def test_representation_determinism(model):
    a = er.evaluate_model(copy.deepcopy(model), allow_selftest=True)
    b = er.evaluate_model(copy.deepcopy(model), allow_selftest=True)
    assert er.canonical_json(a) == er.canonical_json(b)



def test_representation_order_invariance(model):
    base = er.evaluate_model(copy.deepcopy(model), allow_selftest=True)
    perm = copy.deepcopy(model)
    perm["actions"] = list(reversed(perm["actions"]))
    for ctx in perm["contexts"].values():
        ctx["trainInitialStates"] = list(reversed(ctx["trainInitialStates"]))
        ctx["evalInitialStates"] = list(reversed(ctx["evalInitialStates"]))
    got = er.evaluate_model(perm, allow_selftest=True)
    # Model digest may differ because representation bytes differ; evaluation evidence may not.
    for key in ("policySuccess", "scores", "complexityMeasured", "hardCorePass", "antiGoodhart", "eligibleForTournament"):
        assert er.canonical_json(base[key]) == er.canonical_json(got[key]), key
    assert er.canonical_json(base["diagnostics"]) == er.canonical_json(got["diagnostics"])

def test_measured_complexity_only(model):
    r = er.evaluate_model(model, allow_selftest=True)
    measured = r["complexityMeasured"]
    assert set(measured) == {"actionCount", "reachableStateCount", "uniqueObservationCount", "maxObservationJsonNodes", "maxObservationBytes"}
    forbidden_declared = {"observationFieldCount", "playerFacingRuleCount", "uiModeCount", "maxEpisodeDecisions", "maxReachableStatesPerSeed"}
    assert not (forbidden_declared & set(model))


def test_mechanical_coupling_ablation(model):
    assert er.next_state(model, "t0", "a", None) == "win"
    assert er.next_state(model, "t0", "a", "coupling-one") == "loss"
    normal = er.evaluate_model(model, allow_selftest=True)
    ablated = er.evaluate_model(model, allow_selftest=True, disabled_coupling="coupling-one")
    assert normal["modelDigest"] == ablated["modelDigest"]
    assert ablated["disabledCoupling"] == "coupling-one"
    # Training must occur in the ablated world, not be reused from the winner.
    assert normal["scores"]["S6"] != ablated["scores"]["S6"]


def test_schema_blocks_candidate_reward(model):
    bad = copy.deepcopy(model)
    bad["reward"] = 999
    tmp = HERE / ".bad-selftest.json"
    tmp.write_text(json.dumps(bad), encoding="utf-8")
    try:
        p = subprocess.run([CHECK_JSONSCHEMA, "--schemafile", str(SCHEMA), str(tmp)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert p.returncode != 0
    finally:
        tmp.unlink(missing_ok=True)



def test_strict_json_loader():
    dup = HERE / ".dup.json"
    nan = HERE / ".nan.json"
    dup.write_text('{"x":1,"x":2}', encoding="utf-8")
    nan.write_text('{"x":NaN}', encoding="utf-8")
    try:
        for path in (dup, nan):
            try:
                er.load_model(str(path))
            except ValueError:
                pass
            else:
                raise AssertionError(f"strict loader accepted {path.name}")
    finally:
        dup.unlink(missing_ok=True); nan.unlink(missing_ok=True)


def test_validator_version():
    out = subprocess.check_output([CHECK_JSONSCHEMA, "--version"], text=True).strip()
    assert out == "check-jsonschema, version 0.38.0"

def test_tournament_no_external_digest():
    # Candidate ID is the only final deterministic tie source.
    base = {"eligibleForTournament": True, "scores": {f: 0.5 for f in sr.SCALAR_FAMILIES}}
    rows = [dict(base, candidateId="R3C01"), dict(base, candidateId="R3C02"), dict(base, candidateId="R3C03")]
    expected = min(rows, key=lambda r: sr.sha256_text(r["candidateId"]))["candidateId"]
    assert sr.tournament_select(rows)["candidateId"] == expected
    assert "candidateSpecDigest" not in sr.tournament_select.__code__.co_names


def test_protocol_zero_slots():
    p = json.loads(PROTOCOL.read_text())
    assert p["scope"]["exactFreshCandidates"] == 3
    assert p["scope"]["preimplementationQualitySelection"] is False
    assert p["state"]["candidateGenerationStarted"] is False
    assert p["state"]["candidateSemanticSlotsConsumed"] == 0
    assert p["selection"]["manifestSelfReportUsedForApplicability"] is False
    assert p["selection"]["manifestSelfReportUsedForComplexityTieBreak"] is False


def main():
    schema_validate()
    model = er.load_model(str(MODEL))
    er.validate_model(model, allow_selftest=True)
    test_p0_visible_state_only(model)
    test_state_keyed_duplicate_detection(model)
    test_representation_determinism(model)
    test_representation_order_invariance(model)
    test_measured_complexity_only(model)
    test_mechanical_coupling_ablation(model)
    test_schema_blocks_candidate_reward(model)
    test_strict_json_loader()
    test_validator_version()
    test_tournament_no_external_digest()
    test_protocol_zero_slots()
    print("R3_PROTOCOL_SELFTEST=PASS")
    print("R3_R2_REGRESSIONS=PASS")
    print("R3_CANDIDATE_GENERATION_STARTED=false")
    print("R3_SEMANTIC_SLOTS_CONSUMED=0")


if __name__ == "__main__":
    main()
