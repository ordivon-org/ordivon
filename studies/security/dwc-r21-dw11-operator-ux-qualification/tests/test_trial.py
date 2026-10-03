from __future__ import annotations
import copy
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[4]
STUDY=ROOT/"studies/security/dwc-r21-dw11-operator-ux-qualification"
sys.path.insert(0,str(STUDY))
from dwc_dw11_eval.trial import build_packet, materialize_trial, score_receipt, verify_packet_files

def trial():
    subject,gt=materialize_trial(ROOT,STUDY)
    packet=build_packet(subject,"agent:builder")
    return subject,gt,packet

def valid_receipt(gt,packet):
    return {
      "schemaVersion":2,
      "kind":"ordivon.security.dwc-dw11-independent-agent-reentry-receipt-r2",
      "packetDigest":packet["packetDigest"],
      "subjectDigest":packet["subjectDigest"],
      "observedCandidateRevision":packet["candidateRevision"],
      "evaluatorActorRef":"agent:independent",
      "evaluatorOccurrenceRef":"occurrence:independent:1",
      "independenceDeclaration":True,
      "cases":copy.deepcopy(gt["cases"]),
      "findings":[],
    }

def test_trial_freezes_live_and_three_prompt_controls():
    subject,gt,packet=trial()
    assert subject["candidateRevision"]=="b3d165961aa3e28d42942dfa9aa1dacf9b0a870f"
    assert len(subject["trialCases"])==4
    assert {r["caseId"] for r in subject["trialCases"]}=={
      "live-current-owner-bundle","prompt-required","prompt-not-required","prompt-unknown"
    }
    assert len(gt["cases"])==4
    verify_packet_files(ROOT,packet)

def test_ground_truth_preserves_no_global_green_and_unranked_actions():
    _,gt,_=trial()
    for row in gt["cases"]:
        assert row["globalSecurityVerdictIncluded"] is False
        assert row["orderingSemantics"]=="NONE_UNRANKED"
        assert row["projectionSemantics"]["rankingApplied"] is False

def test_live_case_preserves_four_unknown_axes_and_no_effect_review():
    _,gt,_=trial()
    live=next(r for r in gt["cases"] if r["caseId"]=="live-current-owner-bundle")
    assert live["securityAxes"]["exposure"]["closureStanding"]=="CLOSED"
    assert live["unresolvedAxes"]==["applicability","protection","compromise","recovery"]
    assert live["policyClock"] is None
    assert live["effectReviews"]==[]

def test_prompt_counterfactual_labels_are_required_notrequired_unknown():
    _,gt,_=trial()
    labels={}
    for row in gt["cases"]:
        if row["caseId"].startswith("prompt-"):
            labels[row["caseId"]]=row["effectReviews"][0]["approvalPromptStanding"]
    assert labels=={
      "prompt-required":"REQUIRED",
      "prompt-not-required":"NOT_REQUIRED",
      "prompt-unknown":"UNKNOWN",
    }

def test_perfect_independent_receipt_scores_pass_without_human_or_production_claims():
    _,gt,packet=trial()
    score=score_receipt(packet,gt,valid_receipt(gt,packet),12345)
    assert score["standing"]=="PASS"
    assert score["criticalFieldMismatchCount"]==0
    assert score["coldReentryExact"] is True
    assert score["runtimeEndToEndElapsedMs"]==12345
    assert score["latencyThresholdMs"] is None
    assert score["humanDecisionLatencyMs"] is None
    assert score["syntheticPromptFidelity"]["unnecessaryPromptRate"]==0
    assert score["syntheticPromptFidelity"]["requiredPromptMissRate"]==0
    assert score["syntheticPromptFidelity"]["unknownPromptPreservationRate"]==1
    assert score["syntheticPromptFidelity"]["productionPromptRateClaimAllowed"] is False

def test_prompt_false_positive_fails_exact_reentry_score():
    _,gt,packet=trial()
    receipt=valid_receipt(gt,packet)
    row=next(r for r in receipt["cases"] if r["caseId"]=="prompt-not-required")
    row["effectReviews"][0]["approvalPromptStanding"]="REQUIRED"
    score=score_receipt(packet,gt,receipt,100)
    assert score["standing"]=="FAIL"
    assert score["syntheticPromptFidelity"]["unnecessaryPromptRate"]==1.0

def test_self_certification_rejected():
    _,gt,packet=trial()
    receipt=valid_receipt(gt,packet)
    receipt["evaluatorActorRef"]=packet["candidateBuilderActorRef"]
    with pytest.raises(Exception,match="independent evaluator actor"):
        score_receipt(packet,gt,receipt,100)


def test_saved_independent_agent_receipt_and_score_validate_exactly():
    import hashlib
    import json

    e=STUDY/"evidence/acceptance"
    packet=json.loads((e/"dw11-independent-agent-reentry-packet-r2.json").read_text())
    gt=json.loads((e/"dw11-agent-reentry-ground-truth-r2.json").read_text())
    receipt_path=e/"dw11-independent-agent-reentry-receipt-r2-20261001.json"
    receipt=json.loads(receipt_path.read_text())
    saved_score=json.loads((e/"dw11-independent-agent-reentry-score-r2-20261001.json").read_text())
    acceptance=json.loads((e/"dw11-independent-agent-ux-acceptance-r2-20261001.json").read_text())

    verify_packet_files(ROOT,packet)
    score=score_receipt(packet,gt,receipt,acceptance["runtimeOccurrence"]["runtimeEndToEndElapsedMs"])
    assert score==saved_score
    assert score["standing"]=="PASS"
    assert score["criticalFieldMismatchCount"]==0
    assert score["coldReentryExact"] is True
    assert score["syntheticPromptFidelity"]["unnecessaryPromptRate"]==0.0
    assert score["syntheticPromptFidelity"]["requiredPromptMissRate"]==0.0
    assert score["syntheticPromptFidelity"]["unknownPromptPreservationRate"]==1.0
    assert score["humanDecisionLatencyMs"] is None
    assert acceptance["humanUx"]["standing"]=="NOT_MEASURED"
    assert acceptance["productionUx"]["standing"]=="NOT_MEASURED"
    assert acceptance["independenceBoundary"]["groundTruthExposed"] is False
    assert ("sha256:"+hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            == acceptance["independentReceipt"]["sha256"])


@pytest.mark.parametrize(
    ("path_attr", "name"),
    [
        ("OPERATOR_PATH", "dwc_operator_ux_trial"),
        ("SOCIAL_FABRIC_PATH", "social_fabric_r1"),
    ],
)
def test_frozen_python_digest_is_verified_before_exec(monkeypatch, path_attr, name):
    import dwc_dw11_eval.trial as trial_module

    def tampered_git_bytes(_repo, _revision, _rel):
        return b'raise AssertionError("historical Python executed before digest verification")\n'

    monkeypatch.setattr(trial_module, "git_bytes", tampered_git_bytes)
    with pytest.raises(trial_module.Dw11TrialError, match="digest mismatch"):
        trial_module._module_from_git(
            ROOT,
            trial_module.CANDIDATE_REVISION,
            getattr(trial_module, path_attr),
            name,
        )
