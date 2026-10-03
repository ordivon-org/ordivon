from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
STUDY = ROOT / "studies/security/dwc-r21-dw12-qualification"
sys.path.insert(0, str(STUDY))


def load_module():
    from dwc_dw12 import frozen_evaluation

    return frozen_evaluation


def frozen(mod):
    return mod.freeze_subject(ROOT, "3eec47b6b3ac4f317103a3629f934c2910abaf8a")


def prequalified(mod):
    subject = frozen(mod)
    proto = mod.protocol_r2(subject)
    result = mod.mechanical_prequalification_r2(ROOT, subject, proto)
    return subject, proto, result


def packet(mod):
    subject, proto, result = prequalified(mod)
    return mod.build_evaluator_packet(
        subject=subject,
        proto=proto,
        prequalification=result,
        evaluator_implementation_digest="sha256:" + "a" * 64,
        runner_digest="sha256:" + "b" * 64,
        qualification_digest="sha256:" + "c" * 64,
        candidate_builder_actor_ref="agent:builder",
    )


def test_frozen_subject_binds_all_dw01_dw11_module_acceptances_and_six_cases():
    mod = load_module()
    subject = frozen(mod)
    assert subject["moduleCoverage"]["complete"] is True
    assert subject["moduleCoverage"]["observedModuleCount"] == 11
    assert [row["moduleId"] for row in subject["moduleAcceptances"]] == [
        f"dw{i:02d}" for i in range(1, 12)
    ]
    assert len(subject["caseEvidence"]) == 6
    mod.verify_frozen_subject(
        ROOT,
        subject,
        observed_candidate_revision=subject["candidateRevision"],
    )


def test_frozen_subject_rejects_revision_or_artifact_drift():
    mod = load_module()
    subject = frozen(mod)
    with pytest.raises(mod.FrozenEvaluationError, match="candidate revision mismatch"):
        mod.verify_frozen_subject(
            ROOT,
            subject,
            observed_candidate_revision="0" * 40,
        )
    tampered = copy.deepcopy(subject)
    tampered["moduleAcceptances"][0]["fileDigest"] = "sha256:" + "0" * 64
    tampered_without_digest = dict(tampered)
    tampered_without_digest.pop("subjectDigest")
    tampered["subjectDigest"] = mod.canonical_digest(tampered_without_digest)
    with pytest.raises(mod.FrozenEvaluationError, match="artifact digest mismatch"):
        mod.verify_frozen_subject(
            ROOT,
            tampered,
            observed_candidate_revision=subject["candidateRevision"],
        )


def test_prequalification_is_mechanical_only_and_full_module_coverage():
    mod = load_module()
    _subject, proto, result = prequalified(mod)
    assert result["mechanicalStanding"] == "PASS"
    assert all(value == 0 for value in result["violations"].values())
    assert result["evidenceCoverage"]["moduleAcceptanceCount"] == 11
    assert result["evidenceCoverage"]["caseEvidenceCount"] == 6
    assert result["independentAcceptance"]["selfCertificationPerformed"] is False
    assert result["overallStanding"] == (
        "MECHANICAL_PREQUALIFICATION_PASS_INDEPENDENT_ACCEPTANCE_PENDING"
    )
    assert proto["missingMetricSemantics"] == "UNKNOWN_NOT_ZERO_NOT_PASS"


def test_only_dw10_has_executed_matched_mechanical_ablation():
    mod = load_module()
    _, proto, result = prequalified(mod)
    contract = proto["ablationContract"]
    assert contract["DW10"]["outcomeTrialExecuted"] is True
    assert contract["DW03"]["outcomeTrialExecuted"] is False
    assert contract["DW04"]["outcomeTrialExecuted"] is False
    assert contract["DW11"]["humanTrialExecuted"] is False
    trials = result["baselineCandidateTrials"]
    assert trials["standing"] == "PARTIAL_DW10_MATCHED_SYNTHETIC_ONLY"
    assert trials["DW10"]["deltaUnits"] == 17
    assert trials["DW10"]["productionPerformanceClaimAllowed"] is False
    assert trials["DW11"]["standing"] == "HUMAN_AGENT_OUTCOME_UNDERDETERMINED"


def test_evaluator_packet_freezes_harness_and_receipt_contract():
    mod = load_module()
    p = packet(mod)
    assert p["candidateRevision"] == "3eec47b6b3ac4f317103a3629f934c2910abaf8a"
    assert p["evaluationHarness"]["implementationDigest"] == "sha256:" + "a" * 64
    assert p["evaluationHarness"]["runnerDigest"] == "sha256:" + "b" * 64
    assert p["evaluationHarness"]["dependencyFiles"] == [
        {
            "path": "studies/security/dwc-r21-dw12-qualification/dwc_dw12/qualification.py",
            "digest": "sha256:" + "c" * 64,
        }
    ]
    assert p["frozenThresholds"]["falseClosureViolations"] == 0
    assert p["independentReceiptContract"]["standingEnum"] == [
        "PASS",
        "FAIL",
        "INVALID",
    ]


def valid_receipt(p):
    return {
        "schemaVersion": 2,
        "kind": "ordivon.security.dwc-dw12-independent-evaluator-receipt-r2",
        "packetDigest": p["packetDigest"],
        "subjectDigest": p["subjectDigest"],
        "observedCandidateRevision": p["candidateRevision"],
        "evaluatorActorRef": "agent:independent-evaluator",
        "evaluatorOccurrenceRef": "occurrence:independent:1",
        "independenceDeclaration": True,
        "candidateMechanicalClaimDigest": p["candidateMechanicalClaimDigest"],
        "recomputedMechanicalResultDigest": p["candidateMechanicalClaimDigest"],
        "mechanicalClaimReproduced": True,
        "postFreezeMutationObserved": False,
        "thresholdRetuningObserved": False,
        "standing": "PASS",
        "findings": [],
    }


def test_saved_packet_harness_and_frozen_subject_verify_exactly():
    mod = load_module()
    import json

    evidence = STUDY / "evidence/acceptance"
    subject = json.loads((evidence / "dw12-frozen-subject-r2.json").read_text())
    proto = json.loads((evidence / "dw12-protocol-r2.json").read_text())
    pre = json.loads(
        (evidence / "dw12-mechanical-prequalification-r2.json").read_text()
    )
    p = json.loads((evidence / "dw12-independent-evaluator-packet-r2.json").read_text())
    mod.verify_evaluator_packet_files(ROOT, p, subject, proto, pre)




def test_saved_packet_rejects_evaluator_dependency_drift():
    mod = load_module()
    import json

    evidence = STUDY / "evidence/acceptance"
    subject = json.loads((evidence / "dw12-frozen-subject-r2.json").read_text())
    proto = json.loads((evidence / "dw12-protocol-r2.json").read_text())
    pre = json.loads(
        (evidence / "dw12-mechanical-prequalification-r2.json").read_text()
    )
    p = json.loads((evidence / "dw12-independent-evaluator-packet-r2.json").read_text())
    tampered = copy.deepcopy(p)
    tampered["evaluationHarness"]["dependencyFiles"][0]["digest"] = "sha256:" + "0" * 64
    unsigned = dict(tampered)
    unsigned.pop("packetDigest", None)
    tampered["packetDigest"] = mod.canonical_digest(unsigned)
    with pytest.raises(mod.FrozenEvaluationError, match="dependency digest mismatch"):
        mod.verify_evaluator_packet_files(ROOT, tampered, subject, proto, pre)


def test_independent_receipt_accepts_independent_reproduction_shape_only():
    mod = load_module()
    p = packet(mod)
    mod.validate_independent_receipt(p, valid_receipt(p))



def test_saved_independent_receipt_validates_exactly_and_preserves_nonclaims():
    mod = load_module()
    import hashlib
    import json

    evidence = STUDY / "evidence/acceptance"
    subject = json.loads((evidence / "dw12-frozen-subject-r2.json").read_text())
    proto = json.loads((evidence / "dw12-protocol-r2.json").read_text())
    pre = json.loads(
        (evidence / "dw12-mechanical-prequalification-r2.json").read_text()
    )
    packet = json.loads(
        (evidence / "dw12-independent-evaluator-packet-r2.json").read_text()
    )
    receipt_path = evidence / "dw12-independent-evaluator-receipt-r2-20261001.json"
    receipt = json.loads(receipt_path.read_text())
    acceptance = json.loads(
        (evidence / "dw12-independent-acceptance-r2-20261001.json").read_text()
    )

    mod.verify_evaluator_packet_files(ROOT, packet, subject, proto, pre)
    mod.validate_independent_receipt(packet, receipt)

    assert receipt["standing"] == "PASS"
    assert receipt["evaluatorActorRef"] != packet["candidateBuilderActorRef"]
    assert receipt["mechanicalClaimReproduced"] is True
    assert receipt["postFreezeMutationObserved"] is False
    assert receipt["thresholdRetuningObserved"] is False
    assert receipt["recomputedMechanicalResultDigest"] == pre["resultDigest"]
    assert acceptance["standing"] == "PASS_FROZEN_MECHANICAL_QUALIFICATION"
    assert acceptance["independenceBoundary"]["providerIndependenceClaimed"] is False
    assert acceptance["independenceBoundary"]["contextOccurrenceIndependenceClaimed"] is True
    observed = "sha256:" + hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    assert observed == acceptance["independentReceipt"]["sha256"]
    assert "humanDecisionLatencyMs" in acceptance["unknownMetrics"]
    assert "unnecessaryApprovalPromptRate" in acceptance["unknownMetrics"]


def test_independent_receipt_rejects_self_certification_and_digest_drift():
    mod = load_module()
    p = packet(mod)
    self_receipt = valid_receipt(p)
    self_receipt["evaluatorActorRef"] = p["candidateBuilderActorRef"]
    with pytest.raises(mod.FrozenEvaluationError, match="self-certify"):
        mod.validate_independent_receipt(p, self_receipt)

    drift = valid_receipt(p)
    drift["packetDigest"] = "sha256:" + "0" * 64
    with pytest.raises(mod.FrozenEvaluationError, match="packetDigest mismatch"):
        mod.validate_independent_receipt(p, drift)

    false_pass = valid_receipt(p)
    false_pass["postFreezeMutationObserved"] = True
    with pytest.raises(mod.FrozenEvaluationError, match="post-freeze mutation"):
        mod.validate_independent_receipt(p, false_pass)


def test_prequalification_threads_verified_revision_into_freeze_and_evaluate(monkeypatch):
    mod = load_module()
    subject = frozen(mod)
    proto = mod.protocol_r2(subject)
    expected_revision = subject["candidateRevision"]
    real_freeze = mod.freeze_corpus
    real_evaluate = mod.evaluate
    observed = {}

    def guarded_freeze(repo, revision=None):
        if revision != expected_revision:
            raise AssertionError("freeze_corpus used a different or implicit revision")
        observed["freeze"] = revision
        return real_freeze(repo, revision=revision)

    def guarded_evaluate(repo, corpus, legacy_proto, revision=None):
        if revision != expected_revision:
            raise AssertionError("evaluate used a different or implicit revision")
        observed["evaluate"] = revision
        return real_evaluate(repo, corpus, legacy_proto, revision=revision)

    monkeypatch.setattr(mod, "freeze_corpus", guarded_freeze)
    monkeypatch.setattr(mod, "evaluate", guarded_evaluate)
    result = mod.mechanical_prequalification_r2(ROOT, subject, proto)

    assert observed == {
        "freeze": expected_revision,
        "evaluate": expected_revision,
    }
    assert result["candidateRevision"] == expected_revision
