#!/usr/bin/env python3
"""Wave 4 Social Fabric epistemic standing and constraint-feasibility projections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from social_fabric_r1 import SocialFabricError, canonical_digest

EPI_CUT_KIND = "ordivon.social-fabric-epistemic-cut"
EPI_PROJECTION_KIND = "ordivon.social-fabric-epistemic-projection"
FEASIBILITY_KIND = "ordivon.social-fabric-feasibility-projection"
STANDINGS = {
    "SEQUENCE_OBSERVED",
    "MECHANISM_HYPOTHESIS",
    "MECHANISM_EVIDENCE_SUPPORTED",
}
FORBIDDEN_SCORE_FIELDS = {
    "score",
    "rank",
    "weight",
    "voteCount",
    "priority",
    "chemicalPotential",
    "socialPressure",
}


class EpistemicProjectionError(SocialFabricError):
    pass


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EpistemicProjectionError(f"{label} must be an object")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise EpistemicProjectionError(f"{label} must be non-empty string")
    return value


def _refs(value: Any, label: str, *, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise EpistemicProjectionError(
            f"{label} must be a list with at least {minimum} item(s)"
        )
    rows: list[str] = []
    for index, item in enumerate(value):
        rows.append(_text(item, f"{label}[{index}]"))
    if len(rows) != len(set(rows)):
        raise EpistemicProjectionError(f"{label} must not contain duplicates")
    return sorted(rows)


def compile_epistemic(cut: dict[str, Any]) -> dict[str, Any]:
    if cut.get("schemaVersion") != 1 or cut.get("kind") != EPI_CUT_KIND:
        raise EpistemicProjectionError("unsupported epistemic cut kind/schema")
    observed_at = _text(cut.get("observedAt"), "observedAt")
    raw = cut.get("claims")
    if not isinstance(raw, list) or not raw:
        raise EpistemicProjectionError("claims must be non-empty list")

    claims: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, value in enumerate(raw):
        row = _obj(value, f"claims[{index}]")
        claim_ref = _text(row.get("claimRef"), f"claims[{index}].claimRef")
        if claim_ref in seen:
            raise EpistemicProjectionError(f"duplicate claimRef: {claim_ref}")
        seen.add(claim_ref)
        standing = row.get("standing")
        if standing not in STANDINGS:
            raise EpistemicProjectionError(
                f"claims[{index}].standing unsupported: {standing}"
            )
        statement = _text(row.get("statement"), f"claims[{index}].statement")
        source_ref = _text(row.get("sourceRef"), f"claims[{index}].sourceRef")
        evidence_refs = _refs(
            row.get("evidenceRefs", []), f"claims[{index}].evidenceRefs"
        )
        sequence_refs = _refs(
            row.get("sequenceRefs", []), f"claims[{index}].sequenceRefs"
        )

        projection: dict[str, Any] = {
            "claimRef": claim_ref,
            "statement": statement,
            "standing": standing,
            "sourceRef": source_ref,
            "evidenceRefs": evidence_refs,
            "sequenceRefs": sequence_refs,
            "mechanismAuthorityTransferred": False,
        }
        if standing == "SEQUENCE_OBSERVED":
            _text(
                row.get("observationOwnerRef"), f"claims[{index}].observationOwnerRef"
            )
            if len(sequence_refs) < 2 or not evidence_refs:
                raise EpistemicProjectionError(
                    f"{claim_ref}: SEQUENCE_OBSERVED requires >=2 sequenceRefs and evidenceRefs"
                )
            projection["observationOwnerRef"] = row["observationOwnerRef"]
        elif standing == "MECHANISM_HYPOTHESIS":
            projection["hypothesisOwnerRef"] = _text(
                row.get("hypothesisOwnerRef"), f"claims[{index}].hypothesisOwnerRef"
            )
        else:
            if len(evidence_refs) < 1:
                raise EpistemicProjectionError(
                    f"{claim_ref}: MECHANISM_EVIDENCE_SUPPORTED requires evidenceRefs"
                )
            projection["verificationOwnerRef"] = _text(
                row.get("verificationOwnerRef"), f"claims[{index}].verificationOwnerRef"
            )
            projection["verificationStandingRef"] = _text(
                row.get("verificationStandingRef"),
                f"claims[{index}].verificationStandingRef",
            )
            projection["ownerNativeStanding"] = _text(
                row.get("ownerNativeStanding"), f"claims[{index}].ownerNativeStanding"
            )
            residual = row.get("residualOpenClaims", [])
            projection["residualOpenClaims"] = _refs(
                residual, f"claims[{index}].residualOpenClaims"
            )
        claims.append(projection)

    result = {
        "schemaVersion": 1,
        "kind": EPI_PROJECTION_KIND,
        "truthRole": "epistemic-standing-bridge-not-causal-authority",
        "observedAt": observed_at,
        "sourceCutDigest": canonical_digest(cut),
        "claims": sorted(claims, key=lambda row: row["claimRef"]),
        "nonClaims": [
            "Temporal order, trace linkage, or PROV linkage alone never upgrades a sequence into a mechanism.",
            "MECHANISM_HYPOTHESIS is not causal identification.",
            "MECHANISM_EVIDENCE_SUPPORTED preserves an explicit verification-owner standing; Social Fabric does not independently judge evidence sufficiency.",
            "Residual open causal claims remain open and are not erased by a supported local mechanism.",
            "No epistemic standing grants execution, policy, priority, lease, or EffectAuthority.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def compile_feasibility(commitment: dict[str, Any]) -> dict[str, Any]:
    if commitment.get("kind") != "ordivon.social-fabric-commitment-projection":
        raise EpistemicProjectionError("expected Social Fabric commitment projection")
    top = _obj(commitment.get("commitmentProjection"), "commitmentProjection")
    if (
        top.get("effectAuthorityGranted") is not False
        or top.get("externalEffectPerformed") is not False
    ):
        raise EpistemicProjectionError(
            "feasibility source must not grant EffectAuthority or claim effect"
        )
    raw = commitment.get("candidateDecisions")
    if not isinstance(raw, list):
        raise EpistemicProjectionError("candidateDecisions must be a list")

    rows: list[dict[str, Any]] = []
    for index, value in enumerate(raw):
        decision = _obj(value, f"candidateDecisions[{index}]")
        forbidden = sorted(FORBIDDEN_SCORE_FIELDS & set(decision))
        if forbidden:
            raise EpistemicProjectionError(
                f"numeric/ranking semantics forbidden: {forbidden}"
            )
        candidate_id = _text(
            decision.get("candidateEventId"),
            f"candidateDecisions[{index}].candidateEventId",
        )
        satisfied = decision.get("satisfied")
        if not isinstance(satisfied, bool):
            raise EpistemicProjectionError(f"{candidate_id}.satisfied must be boolean")
        unmet = decision.get("unmet")
        if not isinstance(unmet, list):
            raise EpistemicProjectionError(f"{candidate_id}.unmet must be list")
        constraints: list[dict[str, str]] = []
        for item_index, item in enumerate(unmet):
            constraint = _obj(item, f"{candidate_id}.unmet[{item_index}]")
            constraints.append(
                {
                    "code": _text(constraint.get("code"), f"{candidate_id}.unmet.code"),
                    "value": _text(
                        constraint.get("value"), f"{candidate_id}.unmet.value"
                    ),
                }
            )
        if satisfied and constraints:
            raise EpistemicProjectionError(
                f"{candidate_id}: satisfied=true with unmet constraints"
            )
        if not satisfied and not constraints:
            raise EpistemicProjectionError(
                f"{candidate_id}: satisfied=false without unmet constraints"
            )
        rows.append(
            {
                "candidateEventId": candidate_id,
                "subject": _text(decision.get("subject"), f"{candidate_id}.subject"),
                "standing": "FEASIBLE_SHADOW" if satisfied else "INFEASIBLE_SHADOW",
                "unmetConstraints": sorted(
                    constraints, key=lambda row: (row["code"], row["value"])
                ),
                "policyDecisionDigest": _text(
                    decision.get("policyDecisionDigest"),
                    f"{candidate_id}.policyDecisionDigest",
                ),
            }
        )

    feasible = sorted(
        row["candidateEventId"] for row in rows if row["standing"] == "FEASIBLE_SHADOW"
    )
    result = {
        "schemaVersion": 1,
        "kind": FEASIBILITY_KIND,
        "truthRole": "constraint-feasibility-projection-not-ranking",
        "sourceCommitmentProjectionDigest": _text(
            commitment.get("projectionDigest"), "projectionDigest"
        ),
        "policyId": _text(commitment.get("policyId"), "policyId"),
        "candidates": sorted(rows, key=lambda row: row["candidateEventId"]),
        "feasibleCandidateIds": feasible,
        "effectAuthorityGranted": False,
        "externalEffectPerformed": False,
        "winnerSelected": False,
        "nonClaims": [
            "Feasibility is boolean constraint satisfaction, not a score, rank, vote, priority, or utility function.",
            "Multiple feasible candidates remain a set; no tie-breaker or winner is inferred.",
            "An infeasible candidate reports unmet constraints rather than a lower numerical score.",
            "FEASIBLE_SHADOW is not execution authorization, lease, or EffectAuthority.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return _obj(value, str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    epistemic = sub.add_parser("epistemic")
    epistemic.add_argument("--cut", type=Path, required=True)
    feasibility = sub.add_parser("feasibility")
    feasibility.add_argument("--commitment", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "epistemic":
        result = compile_epistemic(_load(args.cut))
    else:
        result = compile_feasibility(_load(args.commitment))
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
