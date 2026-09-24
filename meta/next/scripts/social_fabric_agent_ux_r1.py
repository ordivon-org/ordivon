#!/usr/bin/env python3
"""Agent-facing orthogonal views over existing Social Fabric projections.

Wave 5 is composition-only. It does not read owner databases, create mutable state,
rank attention, authorize effects, or reinterpret visibility as access control.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from social_fabric_r1 import SocialFabricError, canonical_digest

SCHEMA_VERSION = 1
MANIFEST_KIND = "ordivon.social-fabric-agent-ux-manifest"
BUNDLE_KIND = "ordivon.social-fabric-agent-ux-bundle"
KINDS = {
    "current": "ordivon.social-fabric-current-projection",
    "coordination": "ordivon.social-fabric-coordination-projection",
    "signaling": "ordivon.social-fabric-signaling-r3-projection",
    "memory": "ordivon.social-fabric-transactive-memory-projection",
    "freshness": "ordivon.social-fabric-freshness-projection",
    "commitment": "ordivon.social-fabric-commitment-projection",
    "epistemic": "ordivon.social-fabric-epistemic-projection",
    "hostAttention": "ordivon.host-current-attention-delta",
}
VIEW_KINDS = {
    "current": "ordivon.social-fabric-agent-current-view",
    "attention": "ordivon.social-fabric-agent-attention-view",
    "coordination": "ordivon.social-fabric-agent-coordination-view",
    "authority": "ordivon.social-fabric-agent-authority-view",
}
FORBIDDEN_CONTROL_FIELDS = {
    "priority",
    "rank",
    "score",
    "weight",
    "voteCount",
    "winner",
    "winnerSelected",
    "allow",
    "deny",
    "authorized",
    "authorizationGranted",
}


class AgentUxProjectionError(SocialFabricError):
    pass


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AgentUxProjectionError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise AgentUxProjectionError(f"{label} must be a list")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AgentUxProjectionError(f"{label} must be a non-empty string")
    return value


def _assert_no_control_fields(value: Any, label: str = "input") -> None:
    if isinstance(value, dict):
        bad = sorted(FORBIDDEN_CONTROL_FIELDS & set(value))
        if bad:
            raise AgentUxProjectionError(
                f"{label} contains forbidden control fields: {bad}"
            )
        for key, item in value.items():
            _assert_no_control_fields(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_control_fields(item, f"{label}[{index}]")


def validate_bundle(bundle: dict[str, Any]) -> None:
    if (
        bundle.get("schemaVersion") != SCHEMA_VERSION
        or bundle.get("kind") != BUNDLE_KIND
    ):
        raise AgentUxProjectionError("unsupported Agent UX bundle kind/schema")
    inputs = _obj(bundle.get("inputs"), "inputs")
    if set(inputs) != set(KINDS):
        raise AgentUxProjectionError(
            f"inputs mismatch: expected={sorted(KINDS)} actual={sorted(inputs)}"
        )
    for name, expected_kind in KINDS.items():
        row = _obj(inputs[name], f"inputs.{name}")
        if row.get("schemaVersion") not in {1, 3}:
            raise AgentUxProjectionError(f"inputs.{name}.schemaVersion unsupported")
        if row.get("kind") != expected_kind:
            raise AgentUxProjectionError(
                f"inputs.{name}.kind expected {expected_kind}, got {row.get('kind')}"
            )
    host = inputs["hostAttention"]
    if host.get("truthRole") != "derived-non-authoritative-coordination-navigation":
        raise AgentUxProjectionError(
            "Host attention truthRole must remain non-authoritative navigation"
        )
    commitment = _obj(
        inputs["commitment"].get("commitmentProjection"), "commitmentProjection"
    )
    if (
        commitment.get("effectAuthorityGranted") is not False
        or commitment.get("externalEffectPerformed") is not False
    ):
        raise AgentUxProjectionError(
            "commitment source must not grant authority or claim effect"
        )


def _source_index(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    inputs = bundle["inputs"]
    rows: list[dict[str, Any]] = []
    for name in sorted(inputs):
        value = inputs[name]
        rows.append(
            {
                "input": name,
                "kind": value["kind"],
                "observedAt": value.get("observedAt"),
                "digest": canonical_digest(value),
                "truthRole": value.get("truthRole"),
            }
        )
    return rows


def _base(bundle: dict[str, Any], view: str, detail: bool) -> dict[str, Any]:
    index = _source_index(bundle)
    horizons = sorted(
        {row["observedAt"] for row in index if isinstance(row.get("observedAt"), str)}
    )
    undated = sorted(
        row["input"] for row in index if not isinstance(row.get("observedAt"), str)
    )
    if undated:
        observation_standing = "MIXED_OR_UNDATED_SOURCES"
    elif len(horizons) > 1:
        observation_standing = "MIXED_HORIZONS"
    else:
        observation_standing = "COHERENT_HORIZON"
    return {
        "schemaVersion": 1,
        "kind": VIEW_KINDS[view],
        "truthRole": "agent-facing-projection-only-no-owner-authority",
        "view": view.upper(),
        "disclosure": "detail" if detail else "compact",
        "sourceSetDigest": canonical_digest(index),
        "sourceHorizons": horizons,
        "undatedSourceInputs": undated,
        "observationStanding": observation_standing,
        "coherentObservationHorizon": len(horizons) <= 1 and not undated,
        "sourceIndex": index
        if detail
        else [
            {"input": row["input"], "kind": row["kind"], "digest": row["digest"]}
            for row in index
        ],
    }


def compile_current(bundle: dict[str, Any], *, detail: bool = False) -> dict[str, Any]:
    validate_bundle(bundle)
    inputs = bundle["inputs"]
    current = inputs["current"]
    freshness = inputs["freshness"]
    coordination = inputs["coordination"]
    commitment = inputs["commitment"]
    epistemic = inputs["epistemic"]
    owner_views = _list(freshness.get("ownerViews"), "freshness.ownerViews")
    claims = _list(epistemic.get("claims"), "epistemic.claims")
    standing_counts = Counter(
        str(row.get("standing")) for row in owner_views if isinstance(row, dict)
    )
    epistemic_counts = Counter(
        str(row.get("standing")) for row in claims if isinstance(row, dict)
    )
    result = _base(bundle, "current", detail)
    result["summary"] = {
        "operatingPicture": current.get("commonOperatingPicture", {}),
        "freshnessStandingCounts": dict(sorted(standing_counts.items())),
        "coordination": coordination.get("commonOperatingPicture", {}),
        "commitmentState": commitment["commitmentProjection"].get("state"),
        "commitmentRequiresOwnerBinding": commitment["commitmentProjection"].get(
            "requiresOwnerBinding"
        ),
        "epistemicStandingCounts": dict(sorted(epistemic_counts.items())),
    }
    if detail:
        result["detail"] = {
            "freshnessOwnerViews": owner_views,
            "supersession": freshness.get("supersession", []),
            "reconciliation": current.get("reconciliation", {}),
            "coordinationOperatingPicture": coordination.get(
                "commonOperatingPicture", {}
            ),
            "commitmentProjection": commitment["commitmentProjection"],
            "epistemicClaims": claims,
        }
    result["nonClaims"] = [
        "CURRENT composes bounded owner projections and does not create a global truth owner.",
        "Different source horizons remain explicit; mixed horizons are never presented as one same-cut observation.",
        "Host Task state, Git recency, and physical realization do not independently establish domain completion.",
        "This view grants no execution, scheduling, priority, lease, authorization, or EffectAuthority.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def compile_attention(
    bundle: dict[str, Any], *, detail: bool = False
) -> dict[str, Any]:
    validate_bundle(bundle)
    inputs = bundle["inputs"]
    current_items = _list(inputs["current"].get("attention", []), "current.attention")
    coordination_items = _list(
        inputs["coordination"].get("attention", []), "coordination.attention"
    )
    host = inputs["hostAttention"]
    routed = _list(host.get("routedTasks", []), "hostAttention.routedTasks")
    unrouted = _list(host.get("unroutedMessages", []), "hostAttention.unroutedMessages")
    result = _base(bundle, "attention", detail)
    result["summary"] = {
        "grouping": "source-preserving-unranked",
        "reconciliationFindingCount": len(current_items),
        "coordinationFindingCount": len(coordination_items),
        "hostRoutedTaskCount": len(routed),
        "hostUnroutedMessageCount": len(unrouted),
        "reconciliationFindingRefs": sorted(
            row["findingId"]
            for row in current_items
            if isinstance(row, dict) and isinstance(row.get("findingId"), str)
        ),
        "coordinationFindingRefs": sorted(
            row["findingId"]
            for row in coordination_items
            if isinstance(row, dict) and isinstance(row.get("findingId"), str)
        ),
        "hostTaskRefs": sorted(
            f"{row.get('taskId')}@{row.get('taskRevision')}"
            for row in routed
            if isinstance(row, dict)
        ),
        "unroutedMessageSequences": sorted(
            row["sequence"]
            for row in unrouted
            if isinstance(row, dict) and isinstance(row.get("sequence"), int)
        ),
    }
    if detail:
        result["detail"] = {
            "reconciliationFindings": current_items,
            "coordinationFindings": coordination_items,
            "hostRoutedTasks": routed,
            "hostUnroutedMessages": unrouted,
            "hostBoardFence": host.get("boardFence"),
        }
    result["nonClaims"] = [
        "ATTENTION groups owner-derived findings by source; it does not rank, score, prioritize, assign, or suppress them.",
        "Host Board navigation requires exact task.resume re-entry before acting.",
        "A warning is not an execution denial, security verdict, or domain-completion verdict.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def _visible_signals(
    signals: list[Any], prefixes: tuple[str, ...]
) -> list[dict[str, Any]]:
    rows = [row for row in signals if isinstance(row, dict)]
    if not prefixes:
        return rows
    return [
        row
        for row in rows
        if any(
            isinstance(ref, str) and ref.startswith(prefix)
            for ref in row.get("compartmentRefs", [])
            for prefix in prefixes
        )
    ]


def compile_coordination(
    bundle: dict[str, Any],
    *,
    detail: bool = False,
    compartment_prefixes: tuple[str, ...] = (),
) -> dict[str, Any]:
    validate_bundle(bundle)
    inputs = bundle["inputs"]
    coordination = inputs["coordination"]
    signaling = inputs["signaling"]
    host = inputs["hostAttention"]
    candidates = _list(
        coordination.get("candidateStanding", []), "coordination.candidateStanding"
    )
    signals = _visible_signals(
        _list(signaling.get("signals", []), "signaling.signals"), compartment_prefixes
    )
    visible_ids = {row.get("eventId") for row in signals}
    deliveries: list[dict[str, Any]] = []
    for raw in _list(
        signaling.get("receptorDeliveries", []), "signaling.receptorDeliveries"
    ):
        if not isinstance(raw, dict):
            continue
        ids = [sid for sid in raw.get("signalIds", []) if sid in visible_ids]
        if ids:
            deliveries.append({**raw, "signalIds": ids})
    conflicts = sorted(
        {
            tuple(sorted((row["candidateEventId"], other)))
            for row in candidates
            if isinstance(row, dict) and isinstance(row.get("candidateEventId"), str)
            for other in row.get("conflictsWith", [])
            if isinstance(other, str)
        }
    )
    state_counts = Counter(
        str(row.get("state")) for row in candidates if isinstance(row, dict)
    )
    routed = _list(host.get("routedTasks", []), "hostAttention.routedTasks")
    result = _base(bundle, "coordination", detail)
    result["visibility"] = {
        "compartmentPrefixes": list(compartment_prefixes),
        "appliesTo": ["signaling.signals", "signaling.receptorDeliveries"],
        "presentationFilterOnly": True,
        "authorizationEffect": False,
        "aclEffect": False,
    }
    result["summary"] = {
        "candidateStateCounts": dict(sorted(state_counts.items())),
        "candidateRefs": sorted(
            row["candidateEventId"]
            for row in candidates
            if isinstance(row, dict) and isinstance(row.get("candidateEventId"), str)
        ),
        "conflictPairs": [list(pair) for pair in conflicts],
        "visibleSignalCount": len(signals),
        "visibleReceptorDeliveryCount": sum(
            len(row.get("signalIds", [])) for row in deliveries
        ),
        "hostRoutedTaskCount": len(routed),
    }
    if detail:
        result["detail"] = {
            "candidateStanding": candidates,
            "visibleSignals": signals,
            "visibleReceptorDeliveries": deliveries,
            "hostRoutedTasks": routed,
        }
    result["nonClaims"] = [
        "COORDINATION exposes shadow candidates/conflicts and re-entry coordinates; it is not a scheduler or lock manager.",
        "A visibility filter changes presentation only and cannot grant or deny access or execution.",
        "Candidate support is not a vote, score, rank, priority, or winner-selection mechanism.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def compile_authority(
    bundle: dict[str, Any], *, detail: bool = False
) -> dict[str, Any]:
    validate_bundle(bundle)
    inputs = bundle["inputs"]
    memory = inputs["memory"]
    coordination = inputs["coordination"]
    commitment = inputs["commitment"]
    entries = _list(memory.get("entries", []), "memory.entries")
    candidates = _list(
        coordination.get("candidateStanding", []), "coordination.candidateStanding"
    )
    effect_owners = sorted(
        {
            row["effectOwner"]
            for row in candidates
            if isinstance(row, dict) and isinstance(row.get("effectOwner"), str)
        }
    )
    compact_bindings = sorted(
        (
            {
                "subjectRef": row.get("subjectRef"),
                "relation": row.get("relation"),
                "principalRef": row.get("principalRef"),
            }
            for row in entries
            if isinstance(row, dict)
        ),
        key=lambda row: (
            str(row["subjectRef"]),
            str(row["relation"]),
            str(row["principalRef"]),
        ),
    )
    result = _base(bundle, "authority", detail)
    result["summary"] = {
        "bindingCount": len(entries),
        "bindings": compact_bindings,
        "candidateEffectOwnerRefs": effect_owners,
        "commitmentState": commitment["commitmentProjection"].get("state"),
        "requiresOwnerBinding": commitment["commitmentProjection"].get(
            "requiresOwnerBinding"
        ),
        "authorizationDecisionIncluded": False,
    }
    if detail:
        result["detail"] = {
            "ownerAndVerifierLocators": entries,
            "candidateEffectOwners": [
                {
                    "candidateEventId": row.get("candidateEventId"),
                    "subject": row.get("subject"),
                    "effectOwner": row.get("effectOwner"),
                }
                for row in candidates
                if isinstance(row, dict)
            ],
            "commitmentProjection": commitment["commitmentProjection"],
        }
    result["nonClaims"] = [
        "AUTHORITY is a locator view: it does not authenticate a principal, authorize an effect, or replace the natural owner.",
        "Capability owner, continuity owner, external issuer, verifier, and effect owner are distinct relations.",
        "Absence of a binding remains absence/unknown; this view does not infer expertise or ownership.",
    ]
    result["viewDigest"] = canonical_digest(result)
    return result


def compile_view(
    bundle: dict[str, Any],
    view: str,
    *,
    detail: bool = False,
    compartment_prefixes: tuple[str, ...] = (),
) -> dict[str, Any]:
    if view == "current":
        result = compile_current(bundle, detail=detail)
    elif view == "attention":
        result = compile_attention(bundle, detail=detail)
    elif view == "coordination":
        result = compile_coordination(
            bundle, detail=detail, compartment_prefixes=compartment_prefixes
        )
    elif view == "authority":
        result = compile_authority(bundle, detail=detail)
    else:
        raise AgentUxProjectionError(f"unsupported view: {view}")
    _assert_no_control_fields(result, "view")
    return result


PREFLIGHT_KIND = "ordivon.social-preflight-request"
TRAIT_KEYS = ("durable", "shared", "effectful", "scarce")
VIEW_ORDER = ("CURRENT", "ATTENTION", "COORDINATION", "AUTHORITY")


def compile_preflight(request: dict[str, Any]) -> dict[str, Any]:
    if request.get("schemaVersion") != 1 or request.get("kind") != PREFLIGHT_KIND:
        raise AgentUxProjectionError("unsupported Social Preflight request kind/schema")
    operation_ref = _text(request.get("operationRef"), "operationRef")
    traits = _obj(request.get("traits"), "traits")
    if set(traits) != set(TRAIT_KEYS):
        raise AgentUxProjectionError(f"traits must be exactly {list(TRAIT_KEYS)}")
    for key in TRAIT_KEYS:
        if not isinstance(traits[key], bool):
            raise AgentUxProjectionError(f"traits.{key} must be boolean")
    subject_refs = request.get("subjectRefs", [])
    compartment_refs = request.get("compartmentRefs", [])
    if not isinstance(subject_refs, list) or not all(
        isinstance(v, str) and v for v in subject_refs
    ):
        raise AgentUxProjectionError("subjectRefs must be a list of non-empty strings")
    if not isinstance(compartment_refs, list) or not all(
        isinstance(v, str) and v for v in compartment_refs
    ):
        raise AgentUxProjectionError(
            "compartmentRefs must be a list of non-empty strings"
        )
    if len(subject_refs) != len(set(subject_refs)) or len(compartment_refs) != len(
        set(compartment_refs)
    ):
        raise AgentUxProjectionError(
            "subjectRefs/compartmentRefs must not contain duplicates"
        )
    active = [key for key in TRAIT_KEYS if traits[key]]
    if active and not subject_refs:
        raise AgentUxProjectionError(
            "a recommended social read requires at least one explicit subjectRef"
        )
    recommendations: set[str] = set()
    reasons: list[str] = []
    if active:
        recommendations.add("CURRENT")
    if traits["durable"]:
        recommendations.add("ATTENTION")
        reasons.append("DURABLE_CONTINUITY")
    if traits["shared"]:
        recommendations.update({"ATTENTION", "COORDINATION"})
        reasons.append("SHARED_COORDINATION")
    if traits["effectful"]:
        recommendations.update({"COORDINATION", "AUTHORITY"})
        reasons.append("EFFECT_OWNER_BINDING")
    if traits["scarce"]:
        recommendations.update({"ATTENTION", "COORDINATION"})
        reasons.append("SCARCE_RESOURCE_COORDINATION")
    ordered = [name for name in VIEW_ORDER if name in recommendations]
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.social-fabric-agent-preflight-advice",
        "truthRole": "advisory-view-selection-not-admission-or-effect-authority",
        "operationRef": operation_ref,
        "standing": "SOCIAL_READ_RECOMMENDED" if active else "SOCIAL_READ_OPTIONAL",
        "explicitTraits": {key: traits[key] for key in TRAIT_KEYS},
        "subjectRefs": sorted(subject_refs),
        "compartmentRefs": sorted(compartment_refs),
        "recommendationReasonCodes": reasons,
        "recommendedViews": ordered,
        "effectAuthorizationIncluded": False,
        "executionAdmissionIncluded": False,
        "nonClaims": [
            "Preflight uses only caller-declared durable/shared/effectful/scarce traits and does not infer risk or priority.",
            "A recommendation to read Social Fabric is not a requirement, allow/deny decision, scheduler decision, lease, or EffectAuthority.",
            "Natural owners remain responsible for any enforceable admission, authorization, resource lock, or external effect.",
        ],
    }
    _assert_no_control_fields(result, "preflight")
    result["adviceDigest"] = canonical_digest(result)
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = _obj(json.loads(path.read_text(encoding="utf-8")), str(path))
    if manifest.get("schemaVersion") != 1 or manifest.get("kind") != MANIFEST_KIND:
        raise AgentUxProjectionError("unsupported Agent UX manifest kind/schema")
    raw_inputs = _obj(manifest.get("inputs"), "manifest.inputs")
    if set(raw_inputs) != set(KINDS):
        raise AgentUxProjectionError(
            "manifest inputs do not match required projection set"
        )
    sources: dict[str, Path] = {}
    for name in sorted(raw_inputs):
        rel = _text(raw_inputs[name], f"manifest.inputs.{name}")
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise AgentUxProjectionError(
                f"manifest.inputs.{name} must be a local relative path"
            )
        sources[name] = path.parent / rel_path
    inputs: dict[str, Any] = {}
    for name in sorted(sources):
        source = sources[name]
        inputs[name] = _obj(json.loads(source.read_text(encoding="utf-8")), str(source))
    bundle = {"schemaVersion": 1, "kind": BUNDLE_KIND, "inputs": inputs}
    validate_bundle(bundle)
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("view", choices=(*VIEW_KINDS, "preflight"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--compartment-prefix", action="append", default=[])
    args = parser.parse_args()
    try:
        if args.view == "preflight":
            if args.request is None:
                raise AgentUxProjectionError("preflight requires --request")
            request = _obj(
                json.loads(args.request.read_text(encoding="utf-8")), str(args.request)
            )
            result = compile_preflight(request)
        else:
            if args.manifest is None:
                raise AgentUxProjectionError(f"{args.view} requires --manifest")
            result = compile_view(
                load_manifest(args.manifest),
                args.view,
                detail=args.detail,
                compartment_prefixes=tuple(args.compartment_prefix),
            )
    except (OSError, json.JSONDecodeError, AgentUxProjectionError) as exc:
        raise SystemExit(f"Social Fabric Agent UX failed: {exc}") from exc
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
