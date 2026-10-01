#!/usr/bin/env python3
"""Projection-only operator UX for Defense-Window Convergence (DWC) R2.1.

This module never becomes a security truth owner, scheduler, ranker, policy engine,
or effect-authority service. It renders bounded owner-provided state for fast
human/Agent re-entry while preserving independent security axes and source horizons.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from social_fabric_r1 import canonical_digest

SCHEMA_VERSION = 1
BUNDLE_KIND = "ordivon.security-dwc-operator-bundle-r1"
VIEW_KIND = "ordivon.security-dwc-operator-view-r1"
DISCLOSURES = ("compact", "plan", "evidence", "raw")
AXIS_ORDER = ("applicability", "exposure", "protection", "compromise", "recovery")
CLOSURE_STANDINGS = {"CLOSED", "OPEN", "UNKNOWN"}
ACTION_STANDINGS = {"READY", "BLOCKED", "UNKNOWN"}
APPROVAL_PROMPT_STANDINGS = {"REQUIRED", "NOT_REQUIRED", "UNKNOWN"}


class DwcOperatorUxError(ValueError):
    pass


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DwcOperatorUxError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise DwcOperatorUxError(f"{label} must be a list")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise DwcOperatorUxError(f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    rows = _list(value, label)
    if nonempty and not rows:
        raise DwcOperatorUxError(f"{label} must not be empty")
    if not all(isinstance(item, str) and item for item in rows):
        raise DwcOperatorUxError(f"{label} must contain non-empty strings")
    if len(rows) != len(set(rows)):
        raise DwcOperatorUxError(f"{label} must not contain duplicates")
    return rows


def _validate_source_refs(refs: list[str], source_refs: set[str], label: str) -> None:
    missing = sorted(set(refs) - source_refs)
    if missing:
        raise DwcOperatorUxError(f"{label} references unknown sourceRefs: {missing}")


def validate_bundle(bundle: dict[str, Any]) -> None:
    if bundle.get("schemaVersion") != SCHEMA_VERSION or bundle.get("kind") != BUNDLE_KIND:
        raise DwcOperatorUxError("unsupported DWC operator bundle kind/schema")

    case_ref = _text(bundle.get("caseRef"), "caseRef")
    subject_refs = _string_list(bundle.get("subjectRefs"), "subjectRefs", nonempty=True)

    sources = _list(bundle.get("sources"), "sources")
    if not sources:
        raise DwcOperatorUxError("sources must not be empty")
    seen_sources: set[str] = set()
    for index, raw in enumerate(sources):
        row = _obj(raw, f"sources[{index}]")
        ref = _text(row.get("sourceRef"), f"sources[{index}].sourceRef")
        if ref in seen_sources:
            raise DwcOperatorUxError(f"duplicate sourceRef: {ref}")
        seen_sources.add(ref)
        _text(row.get("ownerRef"), f"sources[{index}].ownerRef")
        _text(row.get("digest"), f"sources[{index}].digest")
        observed = row.get("observedAt")
        if observed is not None and (not isinstance(observed, str) or not observed):
            raise DwcOperatorUxError(f"sources[{index}].observedAt must be string or null")
        if "currentnessStanding" in row:
            _text(row.get("currentnessStanding"), f"sources[{index}].currentnessStanding")

    axes = _obj(bundle.get("axes"), "axes")
    if set(axes) != set(AXIS_ORDER):
        raise DwcOperatorUxError(
            f"axes must be exactly {list(AXIS_ORDER)}"
        )
    for axis in AXIS_ORDER:
        row = _obj(axes[axis], f"axes.{axis}")
        _text(row.get("state"), f"axes.{axis}.state")
        closure = _text(row.get("closureStanding"), f"axes.{axis}.closureStanding")
        if closure not in CLOSURE_STANDINGS:
            raise DwcOperatorUxError(
                f"axes.{axis}.closureStanding must be one of {sorted(CLOSURE_STANDINGS)}"
            )
        _string_list(row.get("evidenceRefs", []), f"axes.{axis}.evidenceRefs")
        refs = _string_list(row.get("sourceRefs", []), f"axes.{axis}.sourceRefs", nonempty=True)
        _validate_source_refs(refs, seen_sources, f"axes.{axis}.sourceRefs")

    workflow = _obj(bundle.get("workflow"), "workflow")
    _text(workflow.get("phase"), "workflow.phase")
    for key in ("runningRefs", "pendingRefs", "completedRefs"):
        _string_list(workflow.get(key, []), f"workflow.{key}")
    blockers = _list(workflow.get("blockedBy", []), "workflow.blockedBy")
    blocker_refs: set[str] = set()
    for index, raw in enumerate(blockers):
        row = _obj(raw, f"workflow.blockedBy[{index}]")
        blocker_ref = _text(row.get("blockerRef"), f"workflow.blockedBy[{index}].blockerRef")
        if blocker_ref in blocker_refs:
            raise DwcOperatorUxError(f"duplicate workflow blockerRef: {blocker_ref}")
        blocker_refs.add(blocker_ref)
        _text(row.get("ownerRef"), f"workflow.blockedBy[{index}].ownerRef")
        _text(row.get("reason"), f"workflow.blockedBy[{index}].reason")

    policy = bundle.get("policy")
    if policy is not None:
        policy = _obj(policy, "policy")
        for key in ("decisionRef", "policyRef", "policyVersion", "policyOwnerRef"):
            _text(policy.get(key), f"policy.{key}")
        deadline = policy.get("deadlineAt")
        if deadline is not None and (not isinstance(deadline, str) or not deadline):
            raise DwcOperatorUxError("policy.deadlineAt must be string or null")
        decision_observed = policy.get("decisionObservedAt")
        if decision_observed is not None and (
            not isinstance(decision_observed, str) or not decision_observed
        ):
            raise DwcOperatorUxError("policy.decisionObservedAt must be string or null")
        source_ref = _text(policy.get("sourceRef"), "policy.sourceRef")
        _validate_source_refs([source_ref], seen_sources, "policy.sourceRef")

    actions = _list(bundle.get("nextSafeActions", []), "nextSafeActions")
    action_refs: set[str] = set()
    for index, raw in enumerate(actions):
        row = _obj(raw, f"nextSafeActions[{index}]")
        action_ref = _text(row.get("actionRef"), f"nextSafeActions[{index}].actionRef")
        if action_ref in action_refs:
            raise DwcOperatorUxError(f"duplicate actionRef: {action_ref}")
        action_refs.add(action_ref)
        _text(row.get("description"), f"nextSafeActions[{index}].description")
        _text(row.get("ownerRef"), f"nextSafeActions[{index}].ownerRef")
        if not isinstance(row.get("effectful"), bool):
            raise DwcOperatorUxError(f"nextSafeActions[{index}].effectful must be boolean")
        standing = _text(
            row.get("executionStanding"), f"nextSafeActions[{index}].executionStanding"
        )
        if standing not in ACTION_STANDINGS:
            raise DwcOperatorUxError(
                f"nextSafeActions[{index}].executionStanding must be one of {sorted(ACTION_STANDINGS)}"
            )
        _string_list(row.get("blockerRefs", []), f"nextSafeActions[{index}].blockerRefs")
        _string_list(row.get("dependencyRefs", []), f"nextSafeActions[{index}].dependencyRefs")
        _string_list(row.get("evidenceRefs", []), f"nextSafeActions[{index}].evidenceRefs")

    edges = _list(bundle.get("dependencyEdges", []), "dependencyEdges")
    for index, raw in enumerate(edges):
        row = _obj(raw, f"dependencyEdges[{index}]")
        _text(row.get("fromRef"), f"dependencyEdges[{index}].fromRef")
        _text(row.get("toRef"), f"dependencyEdges[{index}].toRef")
        _text(row.get("relation"), f"dependencyEdges[{index}].relation")

    reviews = _list(bundle.get("effectReviews", []), "effectReviews")
    review_action_refs: set[str] = set()
    for index, raw in enumerate(reviews):
        row = _obj(raw, f"effectReviews[{index}]")
        action_ref = _text(row.get("actionRef"), f"effectReviews[{index}].actionRef")
        if action_ref in review_action_refs:
            raise DwcOperatorUxError(f"duplicate effect review actionRef: {action_ref}")
        review_action_refs.add(action_ref)
        required = (
            "targetRefs",
            "actuatorRef",
            "providerRef",
            "authorityBindingRef",
            "authorityStanding",
            "blastRadius",
            "commitPoint",
            "reversibility",
            "verifierRef",
            "sourceRef",
            "approvalPromptStanding",
        )
        for key in required:
            if key == "targetRefs":
                _string_list(row.get(key), f"effectReviews[{index}].{key}", nonempty=True)
            else:
                _text(row.get(key), f"effectReviews[{index}].{key}")
        if row["approvalPromptStanding"] not in APPROVAL_PROMPT_STANDINGS:
            raise DwcOperatorUxError(
                f"effectReviews[{index}].approvalPromptStanding must be one of "
                f"{sorted(APPROVAL_PROMPT_STANDINGS)}"
            )
        _validate_source_refs([row["sourceRef"]], seen_sources, f"effectReviews[{index}].sourceRef")

    events = _list(bundle.get("attentionEvents", []), "attentionEvents")
    for index, raw in enumerate(events):
        row = _obj(raw, f"attentionEvents[{index}]")
        if _text(row.get("caseRef"), f"attentionEvents[{index}].caseRef") != case_ref:
            raise DwcOperatorUxError(f"attentionEvents[{index}].caseRef must equal caseRef")
        subject = _text(row.get("subjectRef"), f"attentionEvents[{index}].subjectRef")
        if subject not in subject_refs:
            raise DwcOperatorUxError(
                f"attentionEvents[{index}].subjectRef is not in subjectRefs"
            )
        _text(row.get("updateRef"), f"attentionEvents[{index}].updateRef")
        source_ref = _text(row.get("sourceRef"), f"attentionEvents[{index}].sourceRef")
        _validate_source_refs([source_ref], seen_sources, f"attentionEvents[{index}].sourceRef")
        _text(row.get("summary"), f"attentionEvents[{index}].summary")
        _string_list(row.get("evidenceRefs", []), f"attentionEvents[{index}].evidenceRefs")

    _string_list(bundle.get("rawArtifactRefs", []), "rawArtifactRefs")


def _source_index(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for raw in bundle["sources"]:
        rows.append(
            {
                "sourceRef": raw["sourceRef"],
                "ownerRef": raw["ownerRef"],
                "observedAt": raw.get("observedAt"),
                "digest": raw["digest"],
                "currentnessStanding": raw.get("currentnessStanding", "UNSPECIFIED"),
            }
        )
    return sorted(rows, key=lambda row: row["sourceRef"])


def _attention_groups(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw in bundle["attentionEvents"]:
        key = (raw["caseRef"], raw["subjectRef"], raw["updateRef"])
        grouped[key].append(raw)

    result: list[dict[str, Any]] = []
    for (case_ref, subject_ref, update_ref), rows in sorted(grouped.items()):
        variant_by_digest: dict[str, dict[str, Any]] = {}
        source_refs: set[str] = set()
        for row in rows:
            source_refs.add(row["sourceRef"])
            variant = {
                "summary": row["summary"],
                "evidenceRefs": sorted(row.get("evidenceRefs", [])),
            }
            variant_by_digest.setdefault(canonical_digest(variant), variant)
        variants = [
            variant_by_digest[key]
            for key in sorted(variant_by_digest)
        ]
        result.append(
            {
                "caseRef": case_ref,
                "subjectRef": subject_ref,
                "updateRef": update_ref,
                "sourceRefs": sorted(source_refs),
                "inputEventCount": len(rows),
                "uniqueVariantCount": len(variants),
                "collapsedDuplicateCount": len(rows) - len(variants),
                "variantStanding": (
                    "MULTIPLE_VARIANTS"
                    if len(variants) > 1
                    else "DEDUPLICATED_SINGLE_UPDATE"
                ),
                "variants": variants,
            }
        )
    return result


def compile_view(bundle: dict[str, Any], disclosure: str = "compact") -> dict[str, Any]:
    validate_bundle(bundle)
    if disclosure not in DISCLOSURES:
        raise DwcOperatorUxError(f"unsupported disclosure: {disclosure}")

    source_index = _source_index(bundle)
    horizons = sorted(
        {row["observedAt"] for row in source_index if isinstance(row.get("observedAt"), str)}
    )
    undated = sorted(
        row["sourceRef"] for row in source_index if not isinstance(row.get("observedAt"), str)
    )
    if undated:
        observation_standing = "MIXED_OR_UNDATED_SOURCES"
    elif len(horizons) > 1:
        observation_standing = "MIXED_HORIZONS"
    else:
        observation_standing = "COHERENT_HORIZON"

    axes = {
        axis: {
            "state": bundle["axes"][axis]["state"],
            "closureStanding": bundle["axes"][axis]["closureStanding"],
        }
        for axis in AXIS_ORDER
    }
    unresolved_axes = [
        axis
        for axis in AXIS_ORDER
        if bundle["axes"][axis]["closureStanding"] != "CLOSED"
    ]
    blockers = sorted(
        (
            {
                "blockerRef": row["blockerRef"],
                "ownerRef": row["ownerRef"],
                "reason": row["reason"],
            }
            for row in bundle["workflow"]["blockedBy"]
        ),
        key=lambda row: row["blockerRef"],
    )
    actions = sorted(
        (
            {
                "actionRef": row["actionRef"],
                "description": row["description"],
                "ownerRef": row["ownerRef"],
                "effectful": row["effectful"],
                "executionStanding": row["executionStanding"],
                "blockerRefs": sorted(row.get("blockerRefs", [])),
                "dependencyRefs": sorted(row.get("dependencyRefs", [])),
                "evidenceRefs": sorted(row.get("evidenceRefs", [])),
            }
            for row in bundle["nextSafeActions"]
        ),
        key=lambda row: row["actionRef"],
    )
    reviews = sorted(
        (
            {
                "actionRef": row["actionRef"],
                "targetRefs": sorted(row["targetRefs"]),
                "actuatorRef": row["actuatorRef"],
                "providerRef": row["providerRef"],
                "authorityBindingRef": row["authorityBindingRef"],
                "authorityStanding": row["authorityStanding"],
                "blastRadius": row["blastRadius"],
                "commitPoint": row["commitPoint"],
                "reversibility": row["reversibility"],
                "verifierRef": row["verifierRef"],
                "approvalPromptStanding": row["approvalPromptStanding"],
                "sourceRef": row["sourceRef"],
            }
            for row in bundle["effectReviews"]
        ),
        key=lambda row: row["actionRef"],
    )
    attention_groups = _attention_groups(bundle)

    policy = None
    if bundle.get("policy") is not None:
        source = bundle["policy"]
        policy = {
            "decisionRef": source["decisionRef"],
            "policyRef": source["policyRef"],
            "policyVersion": source["policyVersion"],
            "policyOwnerRef": source["policyOwnerRef"],
            "sourceRef": source["sourceRef"],
            "decisionObservedAt": source.get("decisionObservedAt"),
            "deadlineAt": source.get("deadlineAt"),
            "deadlineProjectionStanding": (
                "POLICY_GROUNDED"
                if source.get("deadlineAt") is not None
                else "NO_DEADLINE_SUPPLIED"
            ),
        }

    result: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": VIEW_KIND,
        "truthRole": "dwc-operator-projection-only-no-domain-policy-or-effect-authority",
        "disclosure": disclosure,
        "caseRef": bundle["caseRef"],
        "subjectRefs": sorted(bundle["subjectRefs"]),
        "sourceSetDigest": canonical_digest(source_index),
        "sourceHorizons": horizons,
        "undatedSourceRefs": undated,
        "observationStanding": observation_standing,
        "coherentObservationHorizon": len(horizons) <= 1 and not undated,
        "securityStanding": {
            "axes": axes,
            "unresolvedAxes": unresolved_axes,
            "globalSecurityVerdictIncluded": False,
        },
        "workflowProgress": {
            "phase": bundle["workflow"]["phase"],
            "runningCount": len(bundle["workflow"].get("runningRefs", [])),
            "pendingCount": len(bundle["workflow"].get("pendingRefs", [])),
            "completedCount": len(bundle["workflow"].get("completedRefs", [])),
            "blockerCount": len(blockers),
            "blockerRefs": [row["blockerRef"] for row in blockers],
            "separateFromSecurityStanding": True,
        },
        "policyClock": policy,
        "effectReviewSummary": {
            "reviewCount": len(reviews),
            "authorityStandings": [
                {
                    "actionRef": row["actionRef"],
                    "authorityStanding": row["authorityStanding"],
                    "authorityBindingRef": row["authorityBindingRef"],
                }
                for row in reviews
            ],
            "approvalPromptStandings": [
                {
                    "actionRef": row["actionRef"],
                    "approvalPromptStanding": row["approvalPromptStanding"],
                }
                for row in reviews
            ],
            "authorizationDecisionIncluded": False,
        },
        "attentionSummary": {
            "inputEventCount": len(bundle["attentionEvents"]),
            "deduplicatedUpdateGroupCount": len(attention_groups),
            "collapsedDuplicateCount": sum(
                row["collapsedDuplicateCount"] for row in attention_groups
            ),
            "groupingKey": ["caseRef", "subjectRef", "updateRef"],
            "rankingApplied": False,
        },
        "projectionSemantics": {
            "presentationOnly": True,
            "rankingApplied": False,
            "schedulerDecisionIncluded": False,
            "authorizationDecisionIncluded": False,
            "policyDecisionMadeByView": False,
            "effectPerformedByView": False,
        },
    }

    if disclosure in {"plan", "evidence", "raw"}:
        result["workflowProgress"]["runningRefs"] = sorted(
            bundle["workflow"].get("runningRefs", [])
        )
        result["workflowProgress"]["pendingRefs"] = sorted(
            bundle["workflow"].get("pendingRefs", [])
        )
        result["workflowProgress"]["completedRefs"] = sorted(
            bundle["workflow"].get("completedRefs", [])
        )
        result["workflowProgress"]["blockers"] = blockers
        result["nextSafeActions"] = {
            "orderingSemantics": "NONE_UNRANKED",
            "actions": actions,
        }
        result["dependencyGraph"] = {
            "edges": sorted(
                bundle["dependencyEdges"],
                key=lambda row: (row["fromRef"], row["relation"], row["toRef"]),
            )
        }
        result["effectReviews"] = reviews

    if disclosure in {"evidence", "raw"}:
        result["sourceIndex"] = source_index
        result["securityStanding"]["axisEvidence"] = {
            axis: {
                "sourceRefs": sorted(bundle["axes"][axis].get("sourceRefs", [])),
                "evidenceRefs": sorted(bundle["axes"][axis].get("evidenceRefs", [])),
            }
            for axis in AXIS_ORDER
        }
        result["attentionGroups"] = attention_groups

    if disclosure == "raw":
        result["rawArtifactRefs"] = sorted(bundle["rawArtifactRefs"])

    result["nonClaims"] = [
        "The five security axes are independent; this projection emits no global green/PASS verdict.",
        "Workflow progress is not security standing and cannot close an UNKNOWN/open security axis.",
        "AuthorityStanding, policy clocks, blockers, and approval-prompt standing are copied from bounded owner inputs; this projection does not grant authority or make policy.",
        "Next safe actions are an unranked presentation of owner-supplied candidates; ordering has no priority or scheduler meaning.",
        "Presentation and disclosure choices never change policy, access control, credentials, effect authority, or domain truth.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def render_text(view: dict[str, Any]) -> str:
    lines = [
        f"DWC CASE {view['caseRef']}",
        (
            "OBSERVATION "
            f"{view['observationStanding']} coherent={str(view['coherentObservationHorizon']).lower()}"
        ),
        "SECURITY AXES (independent; no global verdict):",
    ]
    axes = view["securityStanding"]["axes"]
    for axis in AXIS_ORDER:
        row = axes[axis]
        lines.append(
            f"- {axis.upper()}: state={row['state']} closure={row['closureStanding']}"
        )
    wf = view["workflowProgress"]
    lines.append(
        "WORKFLOW (separate): "
        f"phase={wf['phase']} running={wf['runningCount']} "
        f"pending={wf['pendingCount']} blockers={wf['blockerCount']}"
    )
    if view.get("policyClock") is None:
        lines.append("DEADLINE: not projected (no policy owner input)")
    else:
        policy = view["policyClock"]
        lines.append(
            "DEADLINE: "
            f"{policy.get('deadlineAt') or 'none'} "
            f"standing={policy['deadlineProjectionStanding']} "
            f"policy={policy['policyRef']}@{policy['policyVersion']}"
        )
    if "nextSafeActions" in view:
        lines.append("NEXT SAFE ACTIONS (unranked):")
        for action in view["nextSafeActions"]["actions"]:
            lines.append(
                f"- {action['actionRef']}: {action['executionStanding']} "
                f"owner={action['ownerRef']} effectful={str(action['effectful']).lower()} "
                f"{action['description']}"
            )
    if "effectReviews" in view:
        lines.append("EFFECT REVIEW:")
        for row in view["effectReviews"]:
            lines.append(
                f"- {row['actionRef']}: authority={row['authorityStanding']} "
                f"binding={row['authorityBindingRef']} commit={row['commitPoint']} "
                f"reversibility={row['reversibility']} verifier={row['verifierRef']}"
            )
    return "\n".join(lines)


def load_bundle(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DwcOperatorUxError(f"failed to load bundle: {exc}") from exc
    return _obj(raw, str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--disclosure", choices=DISCLOSURES, default="compact")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()
    try:
        view = compile_view(load_bundle(args.bundle), args.disclosure)
    except DwcOperatorUxError as exc:
        raise SystemExit(f"DWC operator UX projection failed: {exc}") from exc
    if args.format == "text":
        print(render_text(view))
    else:
        print(json.dumps(view, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
