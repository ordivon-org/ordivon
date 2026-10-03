from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .qualification import (
    canonical_digest,
    evaluate,
    file_digest,
    freeze_corpus,
    protocol,
)

_SHA1 = re.compile(r"^[0-9a-f]{40}$")

MODULE_ACCEPTANCE_PATHS = {
    "dw01": "platform/security/evidence/acceptance/dwc-subject-exposure-r1-20261001.json",
    "dw02": "platform/security/evidence/acceptance/dwc-threat-applicability-r1-20261001.json",
    "dw03": "platform/security/evidence/acceptance/dw03-response-policy-r1-20261001.json",
    "dw04": "platform/security/evidence/acceptance/dw04-attack-coverage-r1-20261001.json",
    "dw05": "studies/security/dwc-r21-dw05-authorized-validation/evidence/acceptance/dw05-authorized-validation-r1-20261001.json",
    "dw06": "meta/next/evidence/acceptance/dwc-coa-r1-acceptance-20261001.json",
    "dw07": "platform/security/evidence/acceptance/dw07-effect-execution-r1-20261001.json",
    "dw08": "platform/security/evidence/acceptance/dw08-consequence-verification-r1-20261001.json",
    "dw09": "platform/security/evidence/acceptance/dw09-compromise-recovery-r1-20261001.json",
    "dw10": "studies/security/dwc-r21-dw10-temporal-invalidation/evidence/acceptance/dw10-temporal-invalidation-r1.json",
    "dw11": "meta/next/evidence/acceptance/dwc-operator-ux-r1-acceptance-20261001.json",
}

CASE_EVIDENCE = [
    (
        "exchange-historical-replay",
        "platform/security/evidence/acceptance/dw09-compromise-recovery-r1-20261001.json",
    ),
    (
        "benign-validation-and-bounded-negative",
        "studies/security/dwc-r21-dw05-authorized-validation/evidence/acceptance/dw05-benign-synthetic-canary-r1.json",
    ),
    (
        "response-loss-and-exact-replay",
        "platform/security/evidence/acceptance/dw07-reversible-effect-r1-20261001.json",
    ),
    (
        "stale-evidence-consequence",
        "platform/security/evidence/acceptance/dw08-consequence-verification-r1-20261001.json",
    ),
    (
        "synthetic-recovery",
        "platform/security/evidence/acceptance/dw09-compromise-recovery-r1-20261001.json",
    ),
    (
        "live-operator-admission",
        "meta/next/evidence/acceptance/dwc-operator-ux-r1-live-owner-wiring-20261001.json",
    ),
]


class FrozenEvaluationError(ValueError):
    pass


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FrozenEvaluationError(f"{path}: root must be object")
    return value


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git_bytes(repo: Path, revision: str, rel: str) -> bytes:
    if _SHA1.fullmatch(revision) is None:
        raise FrozenEvaluationError(
            "candidateRevision must be exact 40-hex Git revision"
        )
    if rel.startswith("/") or ".." in Path(rel).parts:
        raise FrozenEvaluationError("frozen artifact path must be repository-relative")
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{rel}"],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise FrozenEvaluationError(
            f"candidate revision does not contain frozen artifact: {rel}"
        )
    return proc.stdout


def _git_artifact(
    repo: Path, revision: str, module_id: str, rel: str
) -> dict[str, Any]:
    raw = _git_bytes(repo, revision, rel)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrozenEvaluationError(f"invalid JSON frozen artifact: {rel}") from exc
    if not isinstance(value, dict):
        raise FrozenEvaluationError(f"{rel}: frozen artifact root must be object")
    return {
        "moduleId": module_id,
        "path": rel,
        "fileDigest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "kind": value.get("kind"),
        "standing": value.get("standing"),
    }


def freeze_subject(repo: Path, candidate_revision: str) -> dict[str, Any]:
    if _SHA1.fullmatch(candidate_revision) is None:
        raise FrozenEvaluationError(
            "candidateRevision must be exact 40-hex Git revision"
        )
    modules = [
        _git_artifact(repo, candidate_revision, module_id, rel)
        for module_id, rel in MODULE_ACCEPTANCE_PATHS.items()
    ]
    cases = []
    for case_id, rel in CASE_EVIDENCE:
        row = _git_artifact(repo, candidate_revision, case_id, rel)
        row["caseId"] = case_id
        row.pop("moduleId", None)
        cases.append(row)
    value = {
        "schemaVersion": 2,
        "kind": "ordivon.security.dwc-dw12-frozen-subject-r2",
        "candidateRevision": candidate_revision,
        "moduleAcceptances": modules,
        "caseEvidence": cases,
        "moduleCoverage": {
            "requiredModuleIds": list(MODULE_ACCEPTANCE_PATHS),
            "observedModuleCount": len(modules),
            "complete": len(modules) == 11,
        },
        "caseSet": [case_id for case_id, _ in CASE_EVIDENCE],
        "freezeLaws": {
            "exactSourceIdentityRequired": True,
            "postFreezeMutationPreservesStanding": False,
            "thresholdRetuningAfterUnblindingAllowed": False,
            "independentEvidenceSeparateFromDevelopmentEvidence": True,
        },
    }
    value["subjectDigest"] = canonical_digest(value)
    return value


def verify_frozen_subject(
    repo: Path,
    subject: Mapping[str, Any],
    *,
    observed_candidate_revision: str,
) -> None:
    if subject.get("kind") != "ordivon.security.dwc-dw12-frozen-subject-r2":
        raise FrozenEvaluationError("unsupported frozen subject")
    if observed_candidate_revision != subject.get("candidateRevision"):
        raise FrozenEvaluationError(
            "candidate revision mismatch: evaluator must materialize exact frozen revision"
        )
    modules = subject.get("moduleAcceptances")
    cases = subject.get("caseEvidence")
    if not isinstance(modules, list) or not isinstance(cases, list):
        raise FrozenEvaluationError("frozen subject artifact lists are malformed")
    revision = str(subject["candidateRevision"])
    for row in [*modules, *cases]:
        observed = (
            "sha256:"
            + hashlib.sha256(_git_bytes(repo, revision, str(row["path"]))).hexdigest()
        )
        if observed != row.get("fileDigest"):
            raise FrozenEvaluationError(
                f"frozen artifact digest mismatch: {row['path']}"
            )
    expected = dict(subject)
    supplied = expected.pop("subjectDigest", None)
    if canonical_digest(expected) != supplied:
        raise FrozenEvaluationError("frozen subjectDigest mismatch")


def protocol_r2(subject: Mapping[str, Any]) -> dict[str, Any]:
    value = {
        "schemaVersion": 2,
        "kind": "ordivon.security.dwc-dw12-qualification-protocol-r2",
        "subjectDigest": subject["subjectDigest"],
        "candidateRevision": subject["candidateRevision"],
        "evaluationBoundaryLaws": {
            "freezePrecedesIndependentEvaluation": True,
            "postFreezeMutationPreservesStanding": False,
            "thresholdRetuningAfterUnblindingAllowed": False,
            "holdoutEvidenceSeparateFromDevelopmentEvidence": True,
            "evaluatorSemanticsRemainOwnerNative": True,
            "mechanicalClosureIsNotIndependentAcceptance": True,
        },
        "mechanicalGates": {
            "falseClosureViolations": 0,
            "authorityBoundaryViolations": 0,
            "staleEvidenceClosureViolations": 0,
            "duplicateEffectApplyViolations": 0,
            "historicalToCurrentLaunderingViolations": 0,
            "globalGreenViolations": 0,
        },
        "missingMetricSemantics": "UNKNOWN_NOT_ZERO_NOT_PASS",
        "metrics": [
            "productionTTVPms",
            "timeToEradicationMs",
            "timeToRecoveryMs",
            "falseClosureViolations",
            "staleEvidenceClosureViolations",
            "authorityBoundaryViolations",
            "duplicateEffectApplyViolations",
            "humanDecisionLatencyMs",
            "unnecessaryApprovalPromptRate",
            "moduleEvidenceCoverage",
            "caseEvidenceCoverage",
        ],
        "ablationContract": {
            "DW03": {
                "mode": "STRUCTURAL_CAPABILITY_REMOVAL_ONLY",
                "outcomeTrialExecuted": False,
                "productionOutcomeClaimAllowed": False,
            },
            "DW04": {
                "mode": "STRUCTURAL_CAPABILITY_REMOVAL_ONLY",
                "outcomeTrialExecuted": False,
                "productionOutcomeClaimAllowed": False,
            },
            "DW10": {
                "mode": "MATCHED_SYNTHETIC_FULL_RECOMPUTE_BASELINE",
                "outcomeTrialExecuted": True,
                "measurementUnit": "qualification-cost-unit",
                "productionOutcomeClaimAllowed": False,
            },
            "DW11": {
                "mode": "STRUCTURAL_CAPABILITY_REMOVAL_ONLY",
                "outcomeTrialExecuted": False,
                "humanTrialExecuted": False,
                "productionOutcomeClaimAllowed": False,
            },
        },
        "independentAcceptance": {
            "required": True,
            "selfCertificationAllowed": False,
            "evaluatorActorMustDifferFromCandidateBuilder": True,
            "evaluatorOccurrenceRequired": True,
            "receiptRequiredForFinalAcceptance": True,
        },
        "sharedPromotionRule": (
            "No shared-LEGO promotion from synthetic or single-case evidence alone. "
            "Repeated cross-case pressure plus independent acceptance is required."
        ),
    }
    value["protocolDigest"] = canonical_digest(value)
    return value


def mechanical_prequalification_r2(
    repo: Path,
    subject: Mapping[str, Any],
    proto: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_revision = str(subject["candidateRevision"])
    verify_frozen_subject(
        repo,
        subject,
        observed_candidate_revision=candidate_revision,
    )
    legacy_corpus = freeze_corpus(repo, revision=candidate_revision)
    legacy_protocol = protocol(legacy_corpus["corpusDigest"])
    legacy_result = evaluate(
        repo,
        legacy_corpus,
        legacy_protocol,
        revision=candidate_revision,
    )

    violations = dict(legacy_result["violations"])
    expected = proto["mechanicalGates"]
    mechanical_pass = all(
        violations.get(name) == value for name, value in expected.items()
    )

    result = {
        "schemaVersion": 2,
        "kind": "ordivon.security.dwc-dw12-mechanical-prequalification-r2",
        "subjectDigest": subject["subjectDigest"],
        "candidateRevision": subject["candidateRevision"],
        "protocolDigest": proto["protocolDigest"],
        "mechanicalStanding": "PASS" if mechanical_pass else "FAIL",
        "violations": violations,
        "evidenceCoverage": {
            "moduleAcceptanceCount": len(subject["moduleAcceptances"]),
            "requiredModuleAcceptanceCount": 11,
            "allModuleAcceptancesPresent": len(subject["moduleAcceptances"]) == 11,
            "caseEvidenceCount": len(subject["caseEvidence"]),
            "requiredCaseEvidenceCount": 6,
            "allCaseEvidencePresent": len(subject["caseEvidence"]) == 6,
        },
        "metrics": {
            "productionTTVPms": None,
            "timeToEradicationMs": None,
            "timeToRecoveryMs": None,
            "humanDecisionLatencyMs": None,
            "unnecessaryApprovalPromptRate": None,
            "syntheticSelectiveRevalidationCostUnits": legacy_result["metrics"][
                "syntheticSelectiveRevalidationCostUnits"
            ],
            "syntheticFullRecomputeCostUnits": legacy_result["metrics"][
                "syntheticFullRecomputeCostUnits"
            ],
        },
        "baselineCandidateTrials": {
            "standing": "PARTIAL_DW10_MATCHED_SYNTHETIC_ONLY",
            "DW03": {
                "standing": "OUTCOME_UNDERDETERMINED",
                "reason": "No matched production outcome baseline exists for policy projection removal.",
            },
            "DW04": {
                "standing": "OUTCOME_UNDERDETERMINED",
                "reason": "No matched production control-effectiveness baseline exists for coverage-graph removal.",
            },
            "DW10": {
                "standing": "SYNTHETIC_MECHANICAL_DELTA_ONLY",
                "candidateSelectiveRevalidationCostUnits": legacy_result["ablations"][
                    "DW10"
                ]["candidateSelectiveRevalidationCostUnits"],
                "baselineFullRecomputeCostUnits": legacy_result["ablations"]["DW10"][
                    "ablatedFullRecomputeCostUnits"
                ],
                "deltaUnits": legacy_result["ablations"]["DW10"][
                    "syntheticQualificationCostUnitsDelta"
                ],
                "productionPerformanceClaimAllowed": False,
            },
            "DW11": {
                "standing": "HUMAN_AGENT_OUTCOME_UNDERDETERMINED",
                "reason": "No independent timed re-entry or labeled approval-prompt trial has executed.",
            },
        },
        "independentAcceptance": {
            "required": True,
            "standing": "PENDING_INDEPENDENT_EVALUATOR_RECEIPT",
            "selfCertificationPerformed": False,
        },
        "sharedPromotion": {
            "dw10ToSharedComposition": False,
            "standing": "NOT_JUSTIFIED_BY_CURRENT_EVIDENCE",
        },
        "legacyMechanicalClaimDigest": legacy_result["resultDigest"],
        "overallStanding": (
            "MECHANICAL_PREQUALIFICATION_PASS_INDEPENDENT_ACCEPTANCE_PENDING"
            if mechanical_pass
            else "MECHANICAL_PREQUALIFICATION_FAIL"
        ),
    }
    result["resultDigest"] = canonical_digest(result)
    return result


def build_evaluator_packet(
    *,
    subject: Mapping[str, Any],
    proto: Mapping[str, Any],
    prequalification: Mapping[str, Any],
    evaluator_implementation_digest: str,
    runner_digest: str,
    qualification_digest: str,
    candidate_builder_actor_ref: str,
) -> dict[str, Any]:
    packet = {
        "schemaVersion": 2,
        "kind": "ordivon.security.dwc-dw12-independent-evaluator-packet-r2",
        "candidateBuilderActorRef": candidate_builder_actor_ref,
        "candidateRevision": subject["candidateRevision"],
        "subjectDigest": subject["subjectDigest"],
        "protocolDigest": proto["protocolDigest"],
        "candidateMechanicalClaimDigest": prequalification["resultDigest"],
        "evaluationHarness": {
            "implementationPath": "studies/security/dwc-r21-dw12-qualification/dwc_dw12/frozen_evaluation.py",
            "implementationDigest": evaluator_implementation_digest,
            "runnerPath": "studies/security/dwc-r21-dw12-qualification/scripts/run_frozen_evaluation_r2.py",
            "runnerDigest": runner_digest,
            "dependencyFiles": [
                {
                    "path": "studies/security/dwc-r21-dw12-qualification/dwc_dw12/qualification.py",
                    "digest": qualification_digest,
                }
            ],
        },
        "evaluationBoundaryRef": "meta/next/evidence/acceptance/evaluation-boundary-rw6-profile.json",
        "allowedEvidence": {
            "moduleAcceptances": [
                {"path": row["path"], "fileDigest": row["fileDigest"]}
                for row in subject["moduleAcceptances"]
            ],
            "caseEvidence": [
                {
                    "caseId": row["caseId"],
                    "path": row["path"],
                    "fileDigest": row["fileDigest"],
                }
                for row in subject["caseEvidence"]
            ],
        },
        "frozenThresholds": proto["mechanicalGates"],
        "missingMetricSemantics": proto["missingMetricSemantics"],
        "ablationContract": proto["ablationContract"],
        "independentReceiptContract": {
            "requiredFields": [
                "schemaVersion",
                "kind",
                "packetDigest",
                "subjectDigest",
                "observedCandidateRevision",
                "evaluatorActorRef",
                "evaluatorOccurrenceRef",
                "independenceDeclaration",
                "candidateMechanicalClaimDigest",
                "recomputedMechanicalResultDigest",
                "mechanicalClaimReproduced",
                "postFreezeMutationObserved",
                "thresholdRetuningObserved",
                "standing",
                "findings",
            ],
            "standingEnum": ["PASS", "FAIL", "INVALID"],
            "passRequires": [
                "evaluator actor differs from candidate builder actor",
                "independenceDeclaration=true",
                "exact packet/subject/candidate revision match",
                "candidate mechanical claim reproduced exactly",
                "no post-freeze mutation",
                "no threshold retuning",
            ],
        },
        "nonClaims": [
            "This packet does not authorize the candidate builder to certify final acceptance.",
            "Independent PASS would reproduce the frozen qualification boundary; it would not establish production security for targets outside the corpus.",
            "Null production timing and human-attention metrics remain UNKNOWN, not zero.",
            "DW10 shared-Composition promotion remains outside this packet unless later evidence satisfies the frozen promotion rule.",
        ],
    }
    packet["packetDigest"] = canonical_digest(packet)
    return packet


def _git_history_contains_digest(repo: Path, rel: str, expected: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo), "log", "--all", "--format=%H", "--", rel],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False
    for revision in proc.stdout.splitlines():
        try:
            raw = _git_bytes(repo, revision, rel)
        except FrozenEvaluationError:
            continue
        if "sha256:" + hashlib.sha256(raw).hexdigest() == expected:
            return True
    return False


def _verify_digest_bound_historical_file(repo: Path, rel: str, expected: str) -> None:
    current = repo / rel
    if current.is_file() and file_digest(current) == expected:
        return
    if not _git_history_contains_digest(repo, rel, expected):
        raise FrozenEvaluationError(f"frozen harness digest unavailable from Git history: {rel}")


def verify_evaluator_packet_files(
    repo: Path,
    packet: Mapping[str, Any],
    subject: Mapping[str, Any],
    proto: Mapping[str, Any],
    prequalification: Mapping[str, Any],
) -> None:
    supplied_packet_digest = packet.get("packetDigest")
    unsigned_packet = dict(packet)
    unsigned_packet.pop("packetDigest", None)
    if canonical_digest(unsigned_packet) != supplied_packet_digest:
        raise FrozenEvaluationError("packetDigest mismatch")
    if packet.get("subjectDigest") != subject.get("subjectDigest"):
        raise FrozenEvaluationError("packet/subject digest mismatch")
    if packet.get("protocolDigest") != proto.get("protocolDigest"):
        raise FrozenEvaluationError("packet/protocol digest mismatch")
    if packet.get("candidateMechanicalClaimDigest") != prequalification.get(
        "resultDigest"
    ):
        raise FrozenEvaluationError("packet/mechanical claim digest mismatch")
    harness = packet.get("evaluationHarness")
    if not isinstance(harness, Mapping):
        raise FrozenEvaluationError("evaluationHarness must be object")
    for path_key, digest_key in (
        ("implementationPath", "implementationDigest"),
        ("runnerPath", "runnerDigest"),
    ):
        rel = harness.get(path_key)
        expected = harness.get(digest_key)
        if not isinstance(rel, str) or not isinstance(expected, str):
            raise FrozenEvaluationError("evaluation harness path/digest missing")
        try:
            _verify_digest_bound_historical_file(repo, rel, expected)
        except FrozenEvaluationError as exc:
            raise FrozenEvaluationError(f"evaluation harness digest mismatch: {rel}") from exc
    dependencies = harness.get("dependencyFiles")
    if not isinstance(dependencies, list) or not dependencies:
        raise FrozenEvaluationError("evaluation harness dependency closure is missing")
    for row in dependencies:
        if not isinstance(row, Mapping):
            raise FrozenEvaluationError("evaluation harness dependency must be object")
        rel = row.get("path")
        expected = row.get("digest")
        if not isinstance(rel, str) or not isinstance(expected, str):
            raise FrozenEvaluationError("evaluation harness dependency path/digest missing")
        try:
            _verify_digest_bound_historical_file(repo, rel, expected)
        except FrozenEvaluationError as exc:
            raise FrozenEvaluationError(
                f"evaluation harness dependency digest mismatch: {rel}"
            ) from exc
    verify_frozen_subject(
        repo,
        subject,
        observed_candidate_revision=str(packet["candidateRevision"]),
    )


def validate_independent_receipt(
    packet: Mapping[str, Any], receipt: Mapping[str, Any]
) -> None:
    if receipt.get("schemaVersion") != 2:
        raise FrozenEvaluationError("receipt schemaVersion must be 2")
    if (
        receipt.get("kind")
        != "ordivon.security.dwc-dw12-independent-evaluator-receipt-r2"
    ):
        raise FrozenEvaluationError("unsupported independent evaluator receipt")
    if receipt.get("packetDigest") != packet.get("packetDigest"):
        raise FrozenEvaluationError("receipt packetDigest mismatch")
    if receipt.get("subjectDigest") != packet.get("subjectDigest"):
        raise FrozenEvaluationError("receipt subjectDigest mismatch")
    if receipt.get("observedCandidateRevision") != packet.get("candidateRevision"):
        raise FrozenEvaluationError("receipt candidate revision mismatch")
    actor = receipt.get("evaluatorActorRef")
    if not isinstance(actor, str) or not actor:
        raise FrozenEvaluationError("evaluatorActorRef is required")
    if actor == packet.get("candidateBuilderActorRef"):
        raise FrozenEvaluationError(
            "candidate builder cannot self-certify independent acceptance"
        )
    occurrence = receipt.get("evaluatorOccurrenceRef")
    if not isinstance(occurrence, str) or not occurrence:
        raise FrozenEvaluationError("evaluatorOccurrenceRef is required")
    if receipt.get("independenceDeclaration") is not True:
        raise FrozenEvaluationError("independenceDeclaration must be true")
    if receipt.get("candidateMechanicalClaimDigest") != packet.get(
        "candidateMechanicalClaimDigest"
    ):
        raise FrozenEvaluationError("candidate mechanical claim digest mismatch")
    if receipt.get("standing") not in {"PASS", "FAIL", "INVALID"}:
        raise FrozenEvaluationError("invalid independent receipt standing")
    findings = receipt.get("findings")
    if not isinstance(findings, list):
        raise FrozenEvaluationError("findings must be an array")
    if receipt.get("standing") == "PASS":
        if receipt.get("recomputedMechanicalResultDigest") != packet.get(
            "candidateMechanicalClaimDigest"
        ):
            raise FrozenEvaluationError(
                "PASS requires exact mechanical-result reproduction"
            )
        if receipt.get("mechanicalClaimReproduced") is not True:
            raise FrozenEvaluationError("PASS requires mechanicalClaimReproduced=true")
        if receipt.get("postFreezeMutationObserved") is not False:
            raise FrozenEvaluationError("PASS forbids post-freeze mutation")
        if receipt.get("thresholdRetuningObserved") is not False:
            raise FrozenEvaluationError("PASS forbids threshold retuning")
