#!/usr/bin/env python3
"""Measurement-only closeout validators for Social Fabric Cross-Disciplinary R2.

This module does not fetch owner state, schedule work, acquire locks, authorize effects,
or create a new truth store. It validates already-captured owner-native references and
compiles bounded PROMOTE/HOLD/KILL closeout evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FORBIDDEN_CONTROL_FIELDS = {
    "priority",
    "rank",
    "score",
    "weight",
    "voteCount",
    "winner",
    "allow",
    "deny",
    "authorized",
    "authorizationGranted",
}
ALLOWED_VIEWS = {"CURRENT", "ATTENTION", "COORDINATION", "AUTHORITY"}
ALLOWED_DECISIONS = {"PROMOTE", "HOLD", "KILL"}


class CloseoutError(ValueError):
    pass


def _walk_no_control(v: Any, path: str = "root") -> None:
    if isinstance(v, dict):
        bad = FORBIDDEN_CONTROL_FIELDS & set(v)
        if bad:
            raise CloseoutError(
                f"{path} contains forbidden control fields: {sorted(bad)}"
            )
        for k, x in v.items():
            _walk_no_control(x, f"{path}.{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v):
            _walk_no_control(x, f"{path}[{i}]")


def validate_concurrency(doc: dict[str, Any]) -> dict[str, Any]:
    if (
        doc.get("kind") != "ordivon.social-fabric-concurrency-gap-measurement"
        or doc.get("schemaVersion") != 1
    ):
        raise CloseoutError("bad concurrency document")
    cases = doc.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CloseoutError("concurrency cases required")
    misses = []
    for row in cases:
        for key in (
            "observedCaseId",
            "sourceRefs",
            "subjects",
            "participants",
            "inSocialScope",
            "pairwiseModelDetected",
            "actualConflictObserved",
            "missClass",
            "evidenceRefs",
            "nonClaims",
        ):
            if key not in row:
                raise CloseoutError(f"missing {key}")
        if (
            row["inSocialScope"]
            and row["actualConflictObserved"]
            and not row["pairwiseModelDetected"]
        ):
            misses.append(row["observedCaseId"])
    standing = (
        "PROVEN_REPRESENTATIONAL_GAP"
        if misses
        else "PAIRWISE_SUFFICIENT_ON_OBSERVED_IN_SCOPE_CASES"
    )
    return {
        "observedCaseCount": len(cases),
        "inScopeMissCount": len(misses),
        "inScopeMissCaseIds": misses,
        "representationStanding": standing,
        "petriPrototypeAuthorized": bool(misses),
    }


def validate_cascade(doc: dict[str, Any]) -> dict[str, Any]:
    if (
        doc.get("kind") != "ordivon.social-fabric-cascade-measurement"
        or doc.get("schemaVersion") != 1
    ):
        raise CloseoutError("bad cascade document")
    cases = doc.get("cases")
    if not isinstance(cases, list) or not cases:
        raise CloseoutError("cascade cases required")
    proven = []
    for row in cases:
        for key in (
            "observedCaseId",
            "sourceRefs",
            "trigger",
            "repeatedObservation",
            "selfAmplifyingWorkGeneration",
            "generationEvidenceRefs",
            "nonClaims",
        ):
            if key not in row:
                raise CloseoutError(f"missing {key}")
        if row["selfAmplifyingWorkGeneration"]:
            if len(row["generationEvidenceRefs"]) < 2:
                raise CloseoutError(
                    "self-amplification requires at least two explicit generation-edge evidence refs"
                )
            proven.append(row["observedCaseId"])
    return {
        "observedCaseCount": len(cases),
        "provenCascadeCount": len(proven),
        "provenCascadeCaseIds": proven,
        "standing": "PROVEN_SELF_AMPLIFICATION"
        if proven
        else "NO_PROVEN_SELF_AMPLIFYING_WORK_GENERATION",
        "detectorAuthorized": bool(proven),
    }


def validate_dogfood(doc: dict[str, Any]) -> dict[str, Any]:
    if (
        doc.get("kind") != "ordivon.social-fabric-wave7-dogfood"
        or doc.get("schemaVersion") != 1
    ):
        raise CloseoutError("bad dogfood document")
    cases = doc.get("cases")
    ids = {r.get("id") for r in cases or []}
    if ids != {"DOG70", "DOG71", "DOG72", "DOG73"}:
        raise CloseoutError("dogfood must contain DOG70-73 exactly")
    for row in cases:
        views = row.get("viewsUsed")
        if not isinstance(views, list) or not views or not set(views) <= ALLOWED_VIEWS:
            raise CloseoutError(f"bad views for {row.get('id')}")
        if (
            row.get("ownerBoundaryPreserved") is not True
            or row.get("effectAuthorityClaimed") is not False
            or row.get("executionAdmissionClaimed") is not False
        ):
            raise CloseoutError(f"owner boundary failure in {row.get('id')}")
        if not row.get("utilityFindings"):
            raise CloseoutError(f"utility evidence missing in {row.get('id')}")
    return {
        "caseCount": 4,
        "boundedUtilityObserved": True,
        "ownerBoundaryPreserved": True,
        "domains": [r["domain"] for r in cases],
    }


def compile_gate(
    concurrency: dict[str, Any],
    cascade: dict[str, Any],
    dogfood: dict[str, Any],
    decisions: list[dict[str, Any]],
    longitudinal_attention_evidence: bool,
) -> dict[str, Any]:
    conc = validate_concurrency(concurrency)
    cas = validate_cascade(cascade)
    dog = validate_dogfood(dogfood)
    by = {r.get("lego"): r for r in decisions}
    required = {
        "SIG34",
        "CONC62",
        "CascadeDetector",
        "SocialPreflight",
        "AgentUXViews",
        "SocialFlux",
        "TransactiveMemory",
        "Freshness",
        "MechanismStanding",
        "ConstraintFeasibility",
    }
    if set(by) != required:
        raise CloseoutError(f"gate decisions mismatch: {sorted(set(by) ^ required)}")
    if any(r.get("decision") not in ALLOWED_DECISIONS for r in decisions):
        raise CloseoutError("invalid decision")
    if by["CONC62"]["decision"] == "PROMOTE" and not conc["petriPrototypeAuthorized"]:
        raise CloseoutError("CONC62 cannot promote without measured gap")
    if by["CascadeDetector"]["decision"] == "PROMOTE" and not cas["detectorAuthorized"]:
        raise CloseoutError("cascade detector cannot promote without measured cascade")
    if by["SIG34"]["decision"] == "PROMOTE" and not longitudinal_attention_evidence:
        raise CloseoutError("SIG34 cannot promote without longitudinal evidence")
    _walk_no_control(decisions, "decisions")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.social-fabric-gate79",
        "truthRole": "measured-closeout-projection-not-authority",
        "concurrency": conc,
        "cascade": cas,
        "dogfood": dog,
        "decisions": decisions,
        "packageStanding": "PROMOTE_BOUNDED_CORE_WITH_OPTIONAL_LEGOS_HELD_OR_KILLED",
        "nonClaims": [
            "GATE79 does not authorize external effects or replace natural owners.",
            "PROMOTE means retain in the bounded Social Fabric projection package, not grant priority, scheduling, locking, or authorization authority.",
        ],
    }


def main() -> int:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("concurrency", type=Path)
    p.add_argument("cascade", type=Path)
    p.add_argument("dogfood", type=Path)
    p.add_argument("decisions", type=Path)
    p.add_argument("--attention-longitudinal", action="store_true")
    a = p.parse_args()

    def load(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    out = compile_gate(
        load(a.concurrency),
        load(a.cascade),
        load(a.dogfood),
        load(a.decisions),
        a.attention_longitudinal,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
