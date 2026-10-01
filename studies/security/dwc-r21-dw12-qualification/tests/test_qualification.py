from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = ROOT / "studies/security/dwc-r21-dw12-qualification/dwc_dw12/qualification.py"


def load_module():
    spec = importlib.util.spec_from_file_location("dw12_under_test", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_corpus_binds_all_required_artifacts():
    mod = load_module()
    corpus = mod.freeze_corpus(ROOT)
    assert len(corpus["artifacts"]) == 9
    assert len({row["path"] for row in corpus["artifacts"]}) == 9
    assert all(row["fileDigest"].startswith("sha256:") for row in corpus["artifacts"])


def test_candidate_mechanical_safety_gates_are_zero_violation():
    mod = load_module()
    corpus = mod.freeze_corpus(ROOT)
    proto = mod.protocol(corpus["corpusDigest"])
    result = mod.evaluate(ROOT, corpus, proto)
    assert result["mechanicalStanding"] == "PASS"
    assert all(value == 0 for value in result["violations"].values())


def test_exchange_history_does_not_become_local_timing_or_recovery_truth():
    mod = load_module()
    corpus = mod.freeze_corpus(ROOT)
    proto = mod.protocol(corpus["corpusDigest"])
    result = mod.evaluate(ROOT, corpus, proto)
    case = result["cases"]["exchangeHistoricalReplay"]
    assert case["verifiedProtectionEstablished"] is False
    assert case["localTTVPms"] is None
    assert case["slackStanding"] == "UNKNOWN_DURATION"
    assert case["recoveryStanding"] == "UNKNOWN_CURRENT_INCIDENT_STATE"


def test_response_loss_and_replay_do_not_duplicate_apply():
    mod = load_module()
    corpus = mod.freeze_corpus(ROOT)
    proto = mod.protocol(corpus["corpusDigest"])
    result = mod.evaluate(ROOT, corpus, proto)
    counts = result["cases"]["responseLossReplay"]["providerApplyCounts"]
    assert counts == {"normalAndReplay": 1, "transportAfterCommit": 1, "denied": 0}
    assert result["cases"]["responseLossReplay"]["verifiedProtectionEstablished"] is False


def test_dw10_ablation_reports_only_synthetic_qualification_units():
    mod = load_module()
    corpus = mod.freeze_corpus(ROOT)
    proto = mod.protocol(corpus["corpusDigest"])
    result = mod.evaluate(ROOT, corpus, proto)
    ablation = result["ablations"]["DW10"]
    assert ablation["candidateSelectiveRevalidationCostUnits"] == 20
    assert ablation["ablatedFullRecomputeCostUnits"] == 37
    assert ablation["syntheticQualificationCostUnitsDelta"] == 17
    assert "not CPU" in ablation["claimBoundary"]


def test_independent_acceptance_and_shared_promotion_remain_open():
    mod = load_module()
    corpus = mod.freeze_corpus(ROOT)
    proto = mod.protocol(corpus["corpusDigest"])
    result = mod.evaluate(ROOT, corpus, proto)
    assert result["overallStanding"] == (
        "MECHANICAL_QUALIFICATION_PASS_INDEPENDENT_ACCEPTANCE_PENDING"
    )
    assert result["independentAcceptance"]["selfCertificationPerformed"] is False
    assert result["sharedPromotion"]["dw10ToSharedComposition"] is False
