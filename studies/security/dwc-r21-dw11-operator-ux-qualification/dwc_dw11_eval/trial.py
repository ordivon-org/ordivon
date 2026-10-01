from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

CANDIDATE_REVISION = "b3d165961aa3e28d42942dfa9aa1dacf9b0a870f"
LIVE_PATH = "meta/next/evidence/acceptance/dwc-operator-ux-r1-live-owner-bundle-20261001.json"
SYNTHETIC_PATH = "meta/next/evidence/acceptance/dwc-operator-ux-r1-reentry-fixture-20261001.json"
OPERATOR_PATH = "meta/next/scripts/dwc_operator_ux_r1.py"


class Dw11TrialError(ValueError):
    pass


def canonical_digest(value: Any) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return "sha256:"+hashlib.sha256(raw).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(repo: Path, revision: str, rel: str) -> bytes:
    proc=subprocess.run(["git","-C",str(repo),"show",f"{revision}:{rel}"],capture_output=True,check=False)
    if proc.returncode != 0:
        raise Dw11TrialError(f"missing frozen artifact: {rel}")
    return proc.stdout


def git_json(repo: Path, revision: str, rel: str) -> dict[str,Any]:
    value=json.loads(git_bytes(repo,revision,rel))
    if not isinstance(value,dict):
        raise Dw11TrialError(f"{rel}: root must be object")
    return value


def _operator(repo: Path):
    scripts=repo/"meta/next/scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0,str(scripts))
    path=repo/OPERATOR_PATH
    spec=importlib.util.spec_from_file_location("dwc_operator_ux_trial",path)
    if spec is None or spec.loader is None:
        raise Dw11TrialError("cannot load operator projection")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_counterfactual(base: Mapping[str,Any], case_id: str, standing: str) -> dict[str,Any]:
    row=copy.deepcopy(dict(base))
    row["caseRef"]=f"case:dwc:synthetic-prompt-{case_id}-r2"
    for event in row.get("attentionEvents",[]):
        event["caseRef"]=row["caseRef"]
    reviews=row.get("effectReviews",[])
    if len(reviews)!=1:
        raise Dw11TrialError("base fixture must have exactly one effect review")
    reviews[0]["approvalPromptStanding"]=standing
    return row


def materialize_trial(repo: Path, out_root: Path, candidate_revision: str=CANDIDATE_REVISION) -> tuple[dict[str,Any],dict[str,Any]]:
    if candidate_revision != CANDIDATE_REVISION:
        raise Dw11TrialError("R2 trial freezes exact candidate revision")
    live=git_json(repo,candidate_revision,LIVE_PATH)
    synthetic=git_json(repo,candidate_revision,SYNTHETIC_PATH)
    controls={
        "required": make_counterfactual(synthetic,"required","REQUIRED"),
        "not-required": make_counterfactual(synthetic,"not-required","NOT_REQUIRED"),
        "unknown": make_counterfactual(synthetic,"unknown","UNKNOWN"),
    }
    fixture_dir=out_root/"fixtures"
    fixture_dir.mkdir(parents=True,exist_ok=True)
    inputs={"live-current-owner-bundle": live, **{f"prompt-{k}":v for k,v in controls.items()}}
    case_rows=[]
    for case_id,value in inputs.items():
        p=fixture_dir/f"{case_id}.json"
        p.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        case_rows.append({
            "caseId":case_id,
            "path":str(p.relative_to(repo)),
            "fileDigest":file_digest(p),
            "class":"LIVE_OWNER_REENTRY" if case_id=="live-current-owner-bundle" else "SYNTHETIC_PROMPT_COUNTERFACTUAL",
        })

    op=_operator(repo)
    gt_cases=[]
    for row in case_rows:
        bundle=json.loads((repo/row["path"]).read_text())
        view=op.compile_view(bundle,"plan")
        gt_cases.append(_summary(row["caseId"],view))

    subject={
        "schemaVersion":2,
        "kind":"ordivon.security.dwc-dw11-agent-reentry-subject-r2",
        "candidateRevision":candidate_revision,
        "operatorImplementation":{
            "path":OPERATOR_PATH,
            "candidateFileDigest":"sha256:"+hashlib.sha256(git_bytes(repo,candidate_revision,OPERATOR_PATH)).hexdigest(),
        },
        "sourceInputs":{
            "liveBundle":{"path":LIVE_PATH,"candidateFileDigest":"sha256:"+hashlib.sha256(git_bytes(repo,candidate_revision,LIVE_PATH)).hexdigest()},
            "syntheticBase":{"path":SYNTHETIC_PATH,"candidateFileDigest":"sha256:"+hashlib.sha256(git_bytes(repo,candidate_revision,SYNTHETIC_PATH)).hexdigest()},
        },
        "trialCases":case_rows,
        "laws":{
            "globalVerdictForbidden":True,
            "workflowSeparateFromSecurityStanding":True,
            "nextActionsUnranked":True,
            "ownerPromptStandingPreserved":True,
            "humanLatencyClaimAllowed":False,
            "productionPromptRateClaimAllowed":False,
        },
    }
    subject["subjectDigest"]=canonical_digest(subject)

    ground_truth={
        "schemaVersion":2,
        "kind":"ordivon.security.dwc-dw11-agent-reentry-ground-truth-r2",
        "subjectDigest":subject["subjectDigest"],
        "cases":gt_cases,
        "scoring":{
            "criticalFieldMismatchesRequiredForPass":0,
            "latencyThresholdMs":None,
            "latencySemantics":"MEASURE_END_TO_END_RUNTIME_JOB_ONLY_NO_PASS_THRESHOLD",
            "productionPromptRateClaimAllowed":False,
            "humanLatencyClaimAllowed":False,
        },
    }
    ground_truth["groundTruthDigest"]=canonical_digest(ground_truth)
    return subject,ground_truth


def _summary(case_id: str, view: Mapping[str,Any]) -> dict[str,Any]:
    policy=view.get("policyClock")
    if policy is None:
        policy_summary=None
    else:
        policy_summary={
            "deadlineAt":policy.get("deadlineAt"),
            "deadlineProjectionStanding":policy["deadlineProjectionStanding"],
            "policyOwnerRef":policy["policyOwnerRef"],
        }
    blockers=[
        {"blockerRef":r["blockerRef"],"ownerRef":r["ownerRef"]}
        for r in view["workflowProgress"].get("blockers",[])
    ]
    reviews=[
        {
            "actionRef":r["actionRef"],
            "authorityStanding":r["authorityStanding"],
            "approvalPromptStanding":r["approvalPromptStanding"],
            "commitPoint":r["commitPoint"],
            "reversibility":r["reversibility"],
            "verifierRef":r["verifierRef"],
        }
        for r in view.get("effectReviews",[])
    ]
    actions=[
        {
            "actionRef":r["actionRef"],
            "ownerRef":r["ownerRef"],
            "effectful":r["effectful"],
            "executionStanding":r["executionStanding"],
        }
        for r in view.get("nextSafeActions",{}).get("actions",[])
    ]
    return {
        "caseId":case_id,
        "caseRef":view["caseRef"],
        "sourceSetDigest":view["sourceSetDigest"],
        "observationStanding":view["observationStanding"],
        "coherentObservationHorizon":view["coherentObservationHorizon"],
        "securityAxes":view["securityStanding"]["axes"],
        "unresolvedAxes":view["securityStanding"]["unresolvedAxes"],
        "globalSecurityVerdictIncluded":view["securityStanding"]["globalSecurityVerdictIncluded"],
        "workflowPhase":view["workflowProgress"]["phase"],
        "blockers":sorted(blockers,key=lambda x:x["blockerRef"]),
        "policyClock":policy_summary,
        "effectReviews":sorted(reviews,key=lambda x:x["actionRef"]),
        "nextSafeActions":sorted(actions,key=lambda x:x["actionRef"]),
        "orderingSemantics":view["nextSafeActions"]["orderingSemantics"],
        "projectionSemantics":view["projectionSemantics"],
    }


def build_packet(subject: Mapping[str,Any], builder_actor: str) -> dict[str,Any]:
    packet={
        "schemaVersion":2,
        "kind":"ordivon.security.dwc-dw11-independent-agent-reentry-packet-r2",
        "candidateBuilderActorRef":builder_actor,
        "candidateRevision":subject["candidateRevision"],
        "subjectDigest":subject["subjectDigest"],
        "allowedInputs":[
            {"caseId":r["caseId"],"path":r["path"],"fileDigest":r["fileDigest"],"class":r["class"]}
            for r in subject["trialCases"]
        ],
        "requiredOutput":{
            "caseFields":[
                "caseId","caseRef","sourceSetDigest","observationStanding",
                "coherentObservationHorizon","securityAxes","unresolvedAxes",
                "globalSecurityVerdictIncluded","workflowPhase","blockers",
                "policyClock","effectReviews","nextSafeActions","orderingSemantics",
                "projectionSemantics"
            ],
            "agentMustNotRankActions":True,
            "agentMustNotCreateGlobalSecurityVerdict":True,
        },
        "measurementContract":{
            "coldReentryCaseId":"live-current-owner-bundle",
            "agentLatency":"Runtime job end-to-end elapsedMs; no pass/fail threshold",
            "syntheticPromptCases":["prompt-required","prompt-not-required","prompt-unknown"],
            "unnecessaryPromptRateDenominator":"owner label NOT_REQUIRED only",
            "requiredPromptMissDenominator":"owner label REQUIRED only",
            "unknownPromptPreservationDenominator":"owner label UNKNOWN only",
        },
        "nonClaims":[
            "Synthetic prompt counterfactuals measure owner-label preservation only; they are not production prompt-rate evidence.",
            "Agent wall-clock is not human decision latency.",
            "Re-entry PASS does not grant authority, rank actions, close UNKNOWN axes, or create a global security verdict."
        ],
    }
    packet["packetDigest"]=canonical_digest(packet)
    return packet


def verify_packet_files(repo: Path, packet: Mapping[str,Any]) -> None:
    unsigned=dict(packet); supplied=unsigned.pop("packetDigest",None)
    if canonical_digest(unsigned)!=supplied:
        raise Dw11TrialError("packetDigest mismatch")
    for row in packet.get("allowedInputs",[]):
        p=repo/row["path"]
        if file_digest(p)!=row["fileDigest"]:
            raise Dw11TrialError(f"trial input digest mismatch: {row['caseId']}")


def score_receipt(packet: Mapping[str,Any], ground_truth: Mapping[str,Any], receipt: Mapping[str,Any], runtime_elapsed_ms: int) -> dict[str,Any]:
    if receipt.get("schemaVersion")!=2 or receipt.get("kind")!="ordivon.security.dwc-dw11-independent-agent-reentry-receipt-r2":
        raise Dw11TrialError("unsupported receipt")
    if receipt.get("packetDigest")!=packet.get("packetDigest"):
        raise Dw11TrialError("receipt packetDigest mismatch")
    if receipt.get("subjectDigest")!=packet.get("subjectDigest"):
        raise Dw11TrialError("receipt subjectDigest mismatch")
    if receipt.get("observedCandidateRevision")!=packet.get("candidateRevision"):
        raise Dw11TrialError("receipt candidate revision mismatch")
    actor=receipt.get("evaluatorActorRef")
    if not isinstance(actor,str) or not actor or actor==packet.get("candidateBuilderActorRef"):
        raise Dw11TrialError("independent evaluator actor required")
    occurrence=receipt.get("evaluatorOccurrenceRef")
    if not isinstance(occurrence,str) or not occurrence:
        raise Dw11TrialError("evaluator occurrence required")
    if receipt.get("independenceDeclaration") is not True:
        raise Dw11TrialError("independenceDeclaration must be true")
    cases=receipt.get("cases")
    if not isinstance(cases,list):
        raise Dw11TrialError("receipt cases must be array")
    by_id={r.get("caseId"):r for r in cases if isinstance(r,dict)}
    expected={r["caseId"]:r for r in ground_truth["cases"]}
    if set(by_id)!=set(expected):
        raise Dw11TrialError("receipt case set mismatch")

    mismatch=[]
    for case_id,exp in expected.items():
        got=by_id[case_id]
        for key,value in exp.items():
            if got.get(key)!=value:
                mismatch.append({"caseId":case_id,"field":key,"expected":value,"observed":got.get(key)})

    prompt_expected={}
    prompt_observed={}
    for case_id in ["prompt-required","prompt-not-required","prompt-unknown"]:
        er=expected[case_id]["effectReviews"]
        gr=by_id[case_id].get("effectReviews",[])
        prompt_expected[case_id]=er[0]["approvalPromptStanding"] if er else None
        prompt_observed[case_id]=gr[0].get("approvalPromptStanding") if len(gr)==1 else None

    not_required=[k for k,v in prompt_expected.items() if v=="NOT_REQUIRED"]
    required=[k for k,v in prompt_expected.items() if v=="REQUIRED"]
    unknown=[k for k,v in prompt_expected.items() if v=="UNKNOWN"]
    unnecessary=sum(1 for k in not_required if prompt_observed.get(k)=="REQUIRED")
    required_miss=sum(1 for k in required if prompt_observed.get(k)!="REQUIRED")
    unknown_miss=sum(1 for k in unknown if prompt_observed.get(k)!="UNKNOWN")
    live_id=packet["measurementContract"]["coldReentryCaseId"]
    live_mismatches=[m for m in mismatch if m["caseId"]==live_id]

    result={
        "schemaVersion":2,
        "kind":"ordivon.security.dwc-dw11-independent-agent-reentry-score-r2",
        "packetDigest":packet["packetDigest"],
        "subjectDigest":packet["subjectDigest"],
        "evaluatorActorRef":actor,
        "evaluatorOccurrenceRef":occurrence,
        "runtimeEndToEndElapsedMs":runtime_elapsed_ms,
        "latencyThresholdMs":None,
        "latencyPassFailStanding":"MEASURED_NO_LEGITIMATE_THRESHOLD",
        "criticalFieldMismatchCount":len(mismatch),
        "coldReentryExact":len(live_mismatches)==0,
        "syntheticPromptFidelity":{
            "unnecessaryPromptCount":unnecessary,
            "notRequiredCaseCount":len(not_required),
            "unnecessaryPromptRate":None if not not_required else unnecessary/len(not_required),
            "requiredPromptMissCount":required_miss,
            "requiredCaseCount":len(required),
            "requiredPromptMissRate":None if not required else required_miss/len(required),
            "unknownPromptMismatchCount":unknown_miss,
            "unknownCaseCount":len(unknown),
            "unknownPromptPreservationRate":None if not unknown else (len(unknown)-unknown_miss)/len(unknown),
            "productionPromptRateClaimAllowed":False,
        },
        "humanDecisionLatencyMs":None,
        "humanLatencyClaimAllowed":False,
        "mismatches":mismatch,
        "standing":"PASS" if len(mismatch)==0 else "FAIL",
        "nonClaims":[
            "Agent end-to-end Runtime wall-clock is not human decision latency.",
            "Synthetic prompt fidelity is not a production unnecessary-approval-prompt rate.",
            "PASS tests faithful cold re-entry/projection interpretation only; it grants no authority."
        ],
    }
    result["scoreDigest"]=canonical_digest(result)
    return result
