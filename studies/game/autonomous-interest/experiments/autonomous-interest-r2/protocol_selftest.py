#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import evaluator_reference as er
import selection_reference as sr

PROTOCOL = ROOT / "domains/game/game-autonomous-interest-protocol-r2.json"
SCHEMA = ROOT / "domains/game/game-autonomous-interest-candidate-r2.schema.json"
FIXTURE = HERE / "selftest_adapter.py"


def assert_protocol_constants(p):
    assert p["searchBudget"] == {
        "initialCompositionSlots": 12,
        "maxStructuralSurvivors": 6,
        "maxPlayableImplementations": 3,
        "maxHumanHoldoutWinners": 1,
        "budgetExpansionAfterOutcomeObservationAllowed": False,
        "eliminatedCandidateResurrectionAllowed": False,
    }
    assert p["seedLaw"]["trainSamplesPerContext"] == sr.TRAIN_SAMPLES_PER_CONTEXT == 8
    assert p["seedLaw"]["evalSamplesPerContext"] == sr.EVAL_SAMPLES_PER_CONTEXT == 24
    assert p["surrogates"]["strictPairwiseEffectDelta"] == sr.STRICT_EFFECT_DELTA == 0.05
    assert p["candidateContract"]["maxEpisodeDecisions"] == er.MAX_EPISODE_DECISIONS == 96
    assert p["candidateContract"]["oracleMaxDepth"] == er.ORACLE_MAX_DEPTH == 24
    assert p["candidateContract"]["oracleMaxNodes"] == er.ORACLE_MAX_NODES == 50000
    assert p["state"]["candidateGenerationStarted"] is False
    assert p["state"]["candidateSemanticSlotsConsumed"] == 0
    assert p["state"]["productSelected"] is False and p["state"]["g0Entered"] is False


def assert_seed_law():
    all_eval = set()
    for cid in sr.SLOT_IDS:
        m = sr.seed_matrix(cid)
        train = [x for c in m["train"].values() for x in c]
        ev = [x for c in m["eval"].values() for x in c]
        assert len(train) == 32 and len(ev) == 96
        assert len(set(train)) == len(train)
        assert len(set(ev)) == len(ev)
        assert not (set(train) & set(ev))
        # Cross-candidate collision is not semantically required, but any observed one fails this frozen fixture.
        assert not (all_eval & set(ev))
        all_eval.update(ev)


def assert_applicability():
    base = {"agencyMode": "spatial", "improvementCarrier": "execution-skill", "consequenceHorizon": "short-loop", "failureValue": "skill"}
    assert sr.required_families(base) == ("S1", "S3", "S6", "S8", "S9")
    rich = {"agencyMode": "mixed", "improvementCarrier": "planning", "consequenceHorizon": "multi-loop", "failureValue": "information"}
    assert sr.required_families(rich) == ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9")


def fake_candidate(cid, descriptors, carrier="web-ts"):
    return {"candidateId": cid, "descriptors": descriptors, "implementationCarrier": carrier}


def assert_subset_determinism():
    ds = [
        {"agencyMode": "spatial", "improvementCarrier": "execution-skill", "consequenceHorizon": "short-loop", "failureValue": "skill"},
        {"agencyMode": "temporal", "improvementCarrier": "planning", "consequenceHorizon": "short-loop", "failureValue": "information"},
        {"agencyMode": "informational", "improvementCarrier": "world-model-knowledge", "consequenceHorizon": "multi-loop", "failureValue": "information"},
        {"agencyMode": "compositional", "improvementCarrier": "authored-construction", "consequenceHorizon": "short-loop", "failureValue": "redesign"},
    ]
    cs = [fake_candidate(f"R2C{i+1:02d}", ds[i]) for i in range(4)]
    expected = [x["candidateId"] for x in sr.choose_diverse_subset(cs, 3)]
    for perm in itertools.permutations(cs):
        assert [x["candidateId"] for x in sr.choose_diverse_subset(list(perm), 3)] == expected


def assert_tournament_determinism():
    manifest = {
        "adapter": {"actionCount": 3, "observationFieldCount": 3, "playerFacingRuleCount": 3, "uiModeCount": 1, "maxEpisodeDecisions": 20}
    }
    entries = [
        {"candidateId": "R2C01", "candidateSpecDigest": "a" * 64, "manifest": manifest, "applicableFamilies": ["S1", "S3", "S6", "S9"], "scores": {"S1": .5, "S3": .5, "S6": .5, "S9": .5}},
        {"candidateId": "R2C02", "candidateSpecDigest": "b" * 64, "manifest": manifest, "applicableFamilies": ["S1", "S3", "S6", "S9"], "scores": {"S1": .7, "S3": .7, "S6": .5, "S9": .5}},
        {"candidateId": "R2C03", "candidateSpecDigest": "c" * 64, "manifest": manifest, "applicableFamilies": ["S1", "S3", "S6", "S9"], "scores": {"S1": .4, "S3": .4, "S6": .4, "S9": .4}},
    ]
    assert sr.tournament_select(entries)["candidateId"] == "R2C02"
    for perm in itertools.permutations(entries):
        assert sr.tournament_select(list(perm))["candidateId"] == "R2C02"


def assert_evaluator_executes():
    out = er.evaluate(str(FIXTURE))
    assert out["candidateId"] == "R2SELFTEST"
    assert set(out["policySuccess"]) == {"P0_HASH", "P1_REACTIVE_Q", "P2_MEMORY_Q", "P3_ORACLE_BFS"}
    assert set(out["passes"]) == {f"S{i}" for i in range(1, 10)}
    assert set(out["antiGoodhart"]) == {
        "determinism", "stalling", "dominantUniversalPolicy", "playerModelOverfit",
        "hiddenAuthorizationByPolicyIdentity", "candidateRewardIgnored", "complexityInflation",
        "cosmeticConsequence", "failureTax", "proxyBundleGaming"
    }
    assert out["uncertaintyTreatment"] == "NONE_FROZEN_EVAL_MATRIX_IS_BENCHMARK_CENSUS_NOT_POPULATION_SAMPLE"


def main():
    p = json.loads(PROTOCOL.read_text())
    s = json.loads(SCHEMA.read_text())
    assert s["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert_protocol_constants(p)
    assert_seed_law()
    assert_applicability()
    assert_subset_determinism()
    assert_tournament_determinism()
    assert_evaluator_executes()
    print("R2_PROTOCOL_SELFTEST=PASS")
    print("R2_CANDIDATE_GENERATION_STARTED=false")
    print("R2_SEMANTIC_SLOTS_CONSUMED=0")


if __name__ == "__main__":
    main()
