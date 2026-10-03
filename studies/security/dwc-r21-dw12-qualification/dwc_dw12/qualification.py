from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

CORPUS_REVISION = "3eec47b6b3ac4f317103a3629f934c2910abaf8a"

CORPUS_PATHS = {
    "dw03": "platform/security/evidence/acceptance/dw03-response-policy-r1-20261001.json",
    "dw04": "platform/security/evidence/acceptance/dw04-attack-coverage-r1-20261001.json",
    "dw05": "studies/security/dwc-r21-dw05-authorized-validation/evidence/acceptance/dw05-benign-synthetic-canary-r1.json",
    "dw06": "meta/next/evidence/acceptance/dwc-coa-r1-acceptance-20261001.json",
    "dw07": "platform/security/evidence/acceptance/dw07-reversible-effect-r1-20261001.json",
    "dw08": "platform/security/evidence/acceptance/dw08-consequence-verification-r1-20261001.json",
    "dw09": "platform/security/evidence/acceptance/dw09-compromise-recovery-r1-20261001.json",
    "dw10": "studies/security/dwc-r21-dw10-temporal-invalidation/evidence/acceptance/dw10-temporal-invalidation-r1.json",
    "dw11": "meta/next/evidence/acceptance/dwc-operator-ux-r1-live-owner-wiring-20261001.json",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(repo: Path, revision: str, rel: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{rel}"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise FileNotFoundError(f"missing frozen corpus artifact: {revision}:{rel}")
    return proc.stdout


def load_json(repo: Path, rel: str, revision: str = CORPUS_REVISION) -> dict[str, Any]:
    return json.loads(git_bytes(repo, revision, rel).decode("utf-8"))


def freeze_corpus(repo: Path, revision: str = CORPUS_REVISION) -> dict[str, Any]:
    artifacts = []
    for module_id, rel in CORPUS_PATHS.items():
        raw = git_bytes(repo, revision, rel)
        value = json.loads(raw.decode("utf-8"))
        artifacts.append(
            {
                "moduleId": module_id,
                "path": rel,
                "fileDigest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "kind": value.get("kind"),
                "standing": value.get("standing"),
            }
        )
    corpus = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-dw12-frozen-corpus-r1",
        "artifacts": artifacts,
        "caseSet": [
            "exchange-historical-replay",
            "benign-validation-and-bounded-negative",
            "response-loss-and-exact-replay",
            "stale-evidence-consequence",
            "synthetic-recovery",
            "live-operator-admission",
        ],
    }
    corpus["corpusDigest"] = canonical_digest(corpus)
    return corpus


def protocol(corpus_digest: str) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-dw12-qualification-protocol-r1",
        "corpusDigest": corpus_digest,
        "mechanicalGates": {
            "falseClosureViolations": 0,
            "authorityBoundaryViolations": 0,
            "staleEvidenceClosureViolations": 0,
            "duplicateEffectApplyViolations": 0,
            "historicalToCurrentLaunderingViolations": 0,
            "globalGreenViolations": 0,
        },
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
            "evidenceCoverage",
        ],
        "ablations": ["DW03", "DW04", "DW10", "DW11"],
        "independentAcceptanceRequired": True,
        "selfCertificationAllowed": False,
        "sharedPromotionRule": (
            "No shared-LEGO promotion from synthetic or single-case evidence alone. "
            "Repeated cross-case pressure plus independent acceptance is required."
        ),
    }
    value["protocolDigest"] = canonical_digest(value)
    return value


def evaluate(
    repo: Path,
    corpus: dict[str, Any],
    proto: dict[str, Any],
    revision: str = CORPUS_REVISION,
) -> dict[str, Any]:
    dw04 = load_json(repo, CORPUS_PATHS["dw04"], revision)
    dw05 = load_json(repo, CORPUS_PATHS["dw05"], revision)
    dw06 = load_json(repo, CORPUS_PATHS["dw06"], revision)
    dw07 = load_json(repo, CORPUS_PATHS["dw07"], revision)
    dw08 = load_json(repo, CORPUS_PATHS["dw08"], revision)
    dw09 = load_json(repo, CORPUS_PATHS["dw09"], revision)
    dw10 = load_json(repo, CORPUS_PATHS["dw10"], revision)
    dw11 = load_json(repo, CORPUS_PATHS["dw11"], revision)

    violations = {
        "falseClosureViolations": 0,
        "authorityBoundaryViolations": 0,
        "staleEvidenceClosureViolations": 0,
        "duplicateEffectApplyViolations": 0,
        "historicalToCurrentLaunderingViolations": 0,
        "globalGreenViolations": 0,
    }
    cases: dict[str, Any] = {}

    # 1. Historical Exchange replay must not mint current local protection/timing/recovery.
    historical_dw04 = dw04["historicalReplay"]["cases"][0]
    historical_dw09 = dw09["historicalExchangeReplay"]["projection"]
    if historical_dw04["verifiedProtectionEstablished"] is not False:
        violations["falseClosureViolations"] += 1
    if dw10["fixtureEvidence"]["exchangePublicReplayLocalTTVPms"] is not None:
        violations["historicalToCurrentLaunderingViolations"] += 1
    if dw10["fixtureEvidence"]["exchangePublicReplaySlackStanding"] != "UNKNOWN_DURATION":
        violations["historicalToCurrentLaunderingViolations"] += 1
    if historical_dw09["persistence"]["standing"] != "HISTORICAL_ADVERSE_REQUIRES_CURRENT_INVESTIGATION":
        violations["historicalToCurrentLaunderingViolations"] += 1
    if historical_dw09["recovery"]["standing"] != "UNKNOWN_CURRENT_INCIDENT_STATE":
        violations["falseClosureViolations"] += 1
    cases["exchangeHistoricalReplay"] = {
        "verifiedProtectionEstablished": historical_dw04["verifiedProtectionEstablished"],
        "localTTVPms": dw10["fixtureEvidence"]["exchangePublicReplayLocalTTVPms"],
        "slackStanding": dw10["fixtureEvidence"]["exchangePublicReplaySlackStanding"],
        "persistenceStanding": historical_dw09["persistence"]["standing"],
        "recoveryStanding": historical_dw09["recovery"]["standing"],
    }

    # 2. Benign study may prove plumbing / bounded negatives, never production security truth.
    benign_dw09 = dw09["benignPersistenceCanary"]["projection"]
    if dw05["binding"]["productionEffectAuthorityGranted"] is not False:
        violations["authorityBoundaryViolations"] += 1
    if dw05["binding"]["productionSecurityStandingEstablished"] is not False:
        violations["falseClosureViolations"] += 1
    if dw05["validationEvidence"]["verifiedProtectionEstablished"] is not False:
        violations["falseClosureViolations"] += 1
    if benign_dw09["compromiseAbsenceEstablished"] is not False:
        violations["falseClosureViolations"] += 1
    cases["benignValidation"] = {
        "validationAdmissionEstablished": dw05["binding"]["validationAdmissionEstablished"],
        "productionEffectAuthorityGranted": dw05["binding"]["productionEffectAuthorityGranted"],
        "productionSecurityStandingEstablished": dw05["binding"]["productionSecurityStandingEstablished"],
        "verifiedProtectionEstablished": dw05["validationEvidence"]["verifiedProtectionEstablished"],
        "boundedCompromiseStanding": benign_dw09["compromise"]["standing"],
        "boundedPersistenceStanding": benign_dw09["persistence"]["standing"],
        "globalCompromiseAbsenceEstablished": benign_dw09["compromiseAbsenceEstablished"],
    }

    # 3. Response loss / exact replay must not duplicate provider apply or self-verify.
    counts = dw07["providerApplyCounts"]
    if counts["normalAndReplay"] != 1 or counts["transportAfterCommit"] != 1 or counts["denied"] != 0:
        violations["duplicateEffectApplyViolations"] += 1
    if dw07["normalCommit"]["worldEffectVerified"] is not False:
        violations["falseClosureViolations"] += 1
    if dw07["normalCommit"]["verifiedProtectionEstablished"] is not False:
        violations["falseClosureViolations"] += 1
    cases["responseLossReplay"] = {
        "normalStanding": dw07["normalCommit"]["standing"],
        "replayStanding": dw07["exactReplay"]["standing"],
        "transportStanding": dw07["transportLossAfterCommit"]["standing"],
        "providerApplyCounts": counts,
        "verifiedProtectionEstablished": dw07["normalCommit"]["verifiedProtectionEstablished"],
    }

    # 4. Stale or receipt-only consequence evidence must not close.
    stale = dw08["negativeControls"]["staleObservation"]
    receipt_only = dw08["negativeControls"]["receiptOnly"]
    if stale["verificationStanding"] != "UNKNOWN" or stale["verifiedProtectionEstablished"] is not False:
        violations["staleEvidenceClosureViolations"] += 1
    if receipt_only["verificationStanding"] != "UNKNOWN" or receipt_only["verifiedProtectionEstablished"] is not False:
        violations["falseClosureViolations"] += 1
    if dw08["verificationResult"]["compromiseAbsenceEstablished"] is not False:
        violations["falseClosureViolations"] += 1
    cases["staleEvidence"] = {
        "staleVerificationStanding": stale["verificationStanding"],
        "receiptOnlyVerificationStanding": receipt_only["verificationStanding"],
        "currentBoundedProtectionStanding": dw08["verificationResult"]["standing"],
        "currentBoundedProtectionVerified": dw08["verificationResult"]["verifiedProtectionEstablished"],
        "compromiseAbsenceEstablished": dw08["verificationResult"]["compromiseAbsenceEstablished"],
    }

    # 5. Recovery requires explicit obligations and still is not domain acceptance.
    recovery = dw09["syntheticRecoveryCanary"]["projection"]
    if recovery["recovery"]["recoveryEstablished"] is not True:
        violations["falseClosureViolations"] += 1
    if recovery["domainAcceptanceEstablished"] is not False:
        violations["authorityBoundaryViolations"] += 1
    cases["syntheticRecovery"] = {
        "compromiseStanding": recovery["compromise"]["standing"],
        "persistenceStanding": recovery["persistence"]["standing"],
        "eradicationEstablished": recovery["recovery"]["eradicationEstablished"],
        "recoveryStanding": recovery["recovery"]["standing"],
        "recoveryEstablished": recovery["recovery"]["recoveryEstablished"],
        "domainAcceptanceEstablished": recovery["domainAcceptanceEstablished"],
    }

    # 6. Live operator admission must not collapse independent axes into a global green.
    axes = dw11["securityAxes"]
    expected_unknown = ["applicability", "protection", "compromise", "recovery"]
    if dw11["unresolvedAxes"] != expected_unknown:
        violations["globalGreenViolations"] += 1
    if dw11["projectionSemantics"]["authorizationDecisionIncluded"] is not False:
        violations["authorityBoundaryViolations"] += 1
    if dw11["effectReviewSummary"]["reviewCount"] != 0:
        violations["authorityBoundaryViolations"] += 1
    cases["liveOperatorAdmission"] = {
        "securityAxes": axes,
        "unresolvedAxes": dw11["unresolvedAxes"],
        "authorizationDecisionIncluded": dw11["projectionSemantics"]["authorizationDecisionIncluded"],
        "effectReviewCount": dw11["effectReviewSummary"]["reviewCount"],
        "observationStanding": dw11["observationStanding"],
    }

    # Cross-module authority/composition checks.
    if dw06["compositionBoundary"]["packageModified"] is not False:
        violations["authorityBoundaryViolations"] += 1
    if dw06["qualification"]["gateStanding"] != "COMPOSITION_GATES_OPEN":
        violations["falseClosureViolations"] += 1

    mechanical_pass = all(value == expected for value, expected in (
        (violations[name], expected)
        for name, expected in proto["mechanicalGates"].items()
    ))

    selective = dw10["fixtureEvidence"]["selectiveRevalidationCostUnits"]
    full = dw10["fixtureEvidence"]["fullRecomputeCostUnits"]
    ablations = {
        "DW03": {
            "responsePolicyProjectionAvailable": False,
            "deadlineProjectionAvailable": False,
            "claimBoundary": (
                "Ablation removes the bounded policy/deadline projection. No production outcome "
                "difference is inferred because legitimate organization policy/deadlines are absent."
            ),
        },
        "DW04": {
            "attackFlowCoverageProjectionAvailable": False,
            "structuralCutEvidenceAvailable": False,
            "claimBoundary": (
                "Ablation removes attack-flow/control coverage structure. No control-effectiveness "
                "difference is inferred from mapping-only historical evidence."
            ),
        },
        "DW10": {
            "candidateSelectiveRevalidationCostUnits": selective,
            "ablatedFullRecomputeCostUnits": full,
            "syntheticQualificationCostUnitsDelta": full - selective,
            "claimBoundary": (
                "Qualification units are synthetic fixture weights, not CPU, wall-clock or money."
            ),
        },
        "DW11": {
            "operatorProjectionAvailable": False,
            "independentAxesVisibleThroughDwcView": False,
            "humanDecisionLatencyDeltaMs": None,
            "unnecessaryApprovalPromptRateDelta": None,
            "claimBoundary": (
                "Mechanical view removal is observable; human/Agent decision-latency and prompt-rate "
                "effects remain unmeasured and require independent trials."
            ),
        },
    }

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-dw12-mechanical-qualification-r1",
        "corpusDigest": corpus["corpusDigest"],
        "protocolDigest": proto["protocolDigest"],
        "mechanicalStanding": "PASS" if mechanical_pass else "FAIL",
        "violations": violations,
        "cases": cases,
        "evidenceCoverage": {
            "frozenArtifactCount": len(corpus["artifacts"]),
            "caseCount": len(cases),
            "allFrozenArtifactsPresent": True,
        },
        "metrics": {
            "productionTTVPms": None,
            "timeToEradicationMs": None,
            "timeToRecoveryMs": None,
            "humanDecisionLatencyMs": None,
            "unnecessaryApprovalPromptRate": None,
            "syntheticSelectiveRevalidationCostUnits": selective,
            "syntheticFullRecomputeCostUnits": full,
        },
        "ablations": ablations,
        "independentAcceptance": {
            "required": True,
            "standing": "PENDING_NO_AGENT_OCCURRENCE_CREATE_TOOL",
            "selfCertificationPerformed": False,
        },
        "sharedPromotion": {
            "dw10ToSharedComposition": False,
            "standing": "NOT_JUSTIFIED_BY_CURRENT_EVIDENCE",
            "reason": (
                "Only synthetic qualification-cost savings and one bounded owner-binding case are "
                "available; repeated cross-case production pressure plus independent acceptance is absent."
            ),
        },
        "overallStanding": (
            "MECHANICAL_QUALIFICATION_PASS_INDEPENDENT_ACCEPTANCE_PENDING"
            if mechanical_pass
            else "MECHANICAL_QUALIFICATION_FAIL"
        ),
    }
    result["resultDigest"] = canonical_digest(result)
    return result
