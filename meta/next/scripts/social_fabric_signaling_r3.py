#!/usr/bin/env python3
"""Social Fabric Wave 3: signaling specificity and longitudinal attention measurement."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from social_fabric_coordination_r2 import (
    DAMAGE,
    KNOWN_TYPES,
    compile_coordination_projection,
)
from social_fabric_r1 import SocialFabricError, canonical_digest

SIGNALING_CUT_KIND = "ordivon.social-fabric-signaling-r3-cut"
SIGNALING_PROJECTION_KIND = "ordivon.social-fabric-signaling-r3-projection"
ATTENTION_HISTORY_KIND = "ordivon.social-fabric-attention-history-manifest"
ATTENTION_MEASUREMENT_KIND = "ordivon.social-fabric-attention-recurrence-measurement"
PROPAGATION_MODES = {"self", "direct", "local", "broadcast", "environmental"}
ANOMALY_ORIGINS = {"endogenous", "exogenous", "unknown"}
RECEPTOR_FIELDS = {
    "receptorId",
    "acceptedTypes",
    "semanticScopePrefixes",
    "propagationModes",
    "compartmentPrefixes",
    "subjectPrefixes",
    "sources",
    "maxAgeSeconds",
    "requireEvidence",
}


def _obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SocialFabricError(f"{label} must be an object")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SocialFabricError(f"{label} must be non-empty string")
    return value


def _strings(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise SocialFabricError(f"{label} must be a list")
    if nonempty and not value:
        raise SocialFabricError(f"{label} must be non-empty")
    out: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise SocialFabricError(f"{label}[{index}] must be non-empty string")
        out.append(item)
    return out


def _instant(value: Any, label: str) -> datetime:
    text = _text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SocialFabricError(f"{label} must be RFC3339") from exc
    if parsed.tzinfo is None:
        raise SocialFabricError(f"{label} must include timezone")
    return parsed.astimezone(UTC)


def _validate_semantics(binding: dict[str, Any], label: str, event_type: str) -> None:
    allowed = {
        "eventId",
        "semanticScope",
        "propagationMode",
        "compartmentRefs",
        "anomalyOrigin",
        "originSourceRef",
    }
    unknown = sorted(set(binding) - allowed)
    if unknown:
        raise SocialFabricError(f"{label} unsupported fields: {unknown}")
    _text(binding.get("semanticScope"), f"{label}.semanticScope")
    mode = binding.get("propagationMode")
    if mode not in PROPAGATION_MODES:
        raise SocialFabricError(f"{label}.propagationMode unsupported: {mode}")
    refs = _strings(
        binding.get("compartmentRefs"), f"{label}.compartmentRefs", nonempty=True
    )
    if len(refs) != len(set(refs)):
        raise SocialFabricError(f"{label}.compartmentRefs must be unique")
    origin = binding.get("anomalyOrigin")
    source = binding.get("originSourceRef")
    if origin is None and source is not None:
        raise SocialFabricError(f"{label}.originSourceRef requires anomalyOrigin")
    if origin is not None:
        if event_type != DAMAGE:
            raise SocialFabricError(
                f"{label}.anomalyOrigin is valid only for damage signals"
            )
        if origin not in ANOMALY_ORIGINS:
            raise SocialFabricError(f"{label}.anomalyOrigin unsupported: {origin}")
        _text(source, f"{label}.originSourceRef")


def _validate_receptor(receptor: dict[str, Any], label: str) -> None:
    unknown = sorted(set(receptor) - RECEPTOR_FIELDS)
    if unknown:
        raise SocialFabricError(
            f"{label} unsupported fields: {unknown}; receptors are simple interest filters"
        )
    _text(receptor.get("receptorId"), f"{label}.receptorId")
    accepted = _strings(
        receptor.get("acceptedTypes"), f"{label}.acceptedTypes", nonempty=True
    )
    bad_types = sorted(set(accepted) - KNOWN_TYPES)
    if bad_types:
        raise SocialFabricError(f"{label}.acceptedTypes unsupported: {bad_types}")
    _strings(
        receptor.get("semanticScopePrefixes", []), f"{label}.semanticScopePrefixes"
    )
    modes = _strings(
        receptor.get("propagationModes"), f"{label}.propagationModes", nonempty=True
    )
    bad_modes = sorted(set(modes) - PROPAGATION_MODES)
    if bad_modes:
        raise SocialFabricError(f"{label}.propagationModes unsupported: {bad_modes}")
    _strings(receptor.get("compartmentPrefixes", []), f"{label}.compartmentPrefixes")
    _strings(receptor.get("subjectPrefixes", []), f"{label}.subjectPrefixes")
    _strings(receptor.get("sources", []), f"{label}.sources")
    max_age = receptor.get("maxAgeSeconds")
    if max_age is not None and (not isinstance(max_age, int) or max_age < 0):
        raise SocialFabricError(f"{label}.maxAgeSeconds must be non-negative integer")
    if not isinstance(receptor.get("requireEvidence", False), bool):
        raise SocialFabricError(f"{label}.requireEvidence must be boolean")


def _prefix_match(value: str, prefixes: list[str]) -> bool:
    return not prefixes or any(value.startswith(prefix) for prefix in prefixes)


def compile_signaling(cut: dict[str, Any]) -> dict[str, Any]:
    if cut.get("schemaVersion") != 1 or cut.get("kind") != SIGNALING_CUT_KIND:
        raise SocialFabricError("unsupported signaling R3 cut kind/schema")
    coordination_cut = _obj(cut.get("coordinationCut"), "coordinationCut")
    coordination = compile_coordination_projection(coordination_cut)
    events = {event["id"]: event for event in coordination_cut["events"]}
    status = {row["eventId"]: row["status"] for row in coordination["lifecycle"]}

    bindings_raw = cut.get("signalSemantics")
    if not isinstance(bindings_raw, list):
        raise SocialFabricError("signalSemantics must be a list")
    bindings: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(bindings_raw):
        binding = _obj(raw, f"signalSemantics[{index}]")
        event_id = _text(binding.get("eventId"), f"signalSemantics[{index}].eventId")
        if event_id not in events:
            raise SocialFabricError(
                f"signalSemantics[{index}].eventId unknown: {event_id}"
            )
        if event_id in bindings:
            raise SocialFabricError(f"duplicate signal semantics binding: {event_id}")
        _validate_semantics(
            binding, f"signalSemantics[{index}]", events[event_id]["type"]
        )
        bindings[event_id] = binding
    missing = sorted(set(events) - set(bindings))
    if missing:
        raise SocialFabricError(
            f"every event requires explicit signaling semantics; missing={missing}"
        )

    receptors_raw = cut.get("receptors", [])
    if not isinstance(receptors_raw, list):
        raise SocialFabricError("receptors must be a list")
    receptors: list[dict[str, Any]] = []
    seen_receptors: set[str] = set()
    for index, raw in enumerate(receptors_raw):
        receptor = _obj(raw, f"receptors[{index}]")
        _validate_receptor(receptor, f"receptors[{index}]")
        receptor_id = receptor["receptorId"]
        if receptor_id in seen_receptors:
            raise SocialFabricError(f"duplicate receptor identity: {receptor_id}")
        seen_receptors.add(receptor_id)
        receptors.append(receptor)

    observed_at = _instant(coordination_cut["observedAt"], "coordinationCut.observedAt")
    signals: list[dict[str, Any]] = []
    for event_id in sorted(events):
        event = events[event_id]
        binding = bindings[event_id]
        signals.append(
            {
                "eventId": event_id,
                "type": event["type"],
                "source": event["source"],
                "subject": event["subject"],
                "status": status[event_id],
                "semanticScope": binding["semanticScope"],
                "propagationMode": binding["propagationMode"],
                "compartmentRefs": sorted(binding["compartmentRefs"]),
                "legacyVisibilityScope": event["ordivonscope"],
                "anomalyOrigin": binding.get("anomalyOrigin"),
                "originSourceRef": binding.get("originSourceRef"),
                "evidenceRefs": sorted(event["data"].get("evidenceRefs", [])),
            }
        )

    deliveries: list[dict[str, Any]] = []
    by_id = {row["eventId"]: row for row in signals}
    for receptor in sorted(receptors, key=lambda row: row["receptorId"]):
        matches: list[str] = []
        for event_id in sorted(events):
            event = events[event_id]
            signal = by_id[event_id]
            if signal["status"] != "active":
                continue
            if event["type"] not in set(receptor["acceptedTypes"]):
                continue
            if not _prefix_match(
                signal["semanticScope"], receptor.get("semanticScopePrefixes", [])
            ):
                continue
            if signal["propagationMode"] not in set(receptor["propagationModes"]):
                continue
            compartment_prefixes = receptor.get("compartmentPrefixes", [])
            if compartment_prefixes and not any(
                _prefix_match(ref, compartment_prefixes)
                for ref in signal["compartmentRefs"]
            ):
                continue
            if not _prefix_match(event["subject"], receptor.get("subjectPrefixes", [])):
                continue
            sources = set(receptor.get("sources", []))
            if sources and event["source"] not in sources:
                continue
            max_age = receptor.get("maxAgeSeconds")
            if max_age is not None:
                age = (
                    observed_at - _instant(event["time"], f"{event_id}.time")
                ).total_seconds()
                if age < 0 or age > max_age:
                    continue
            if receptor.get("requireEvidence", False) and not signal["evidenceRefs"]:
                continue
            matches.append(event_id)
        deliveries.append(
            {
                "receptorId": receptor["receptorId"],
                "signalIds": matches,
                "truthBoundary": (
                    "Interest match only; no policy evaluation, assignment, priority, "
                    "routing authority, scheduling, lease, or EffectAuthority."
                ),
            }
        )

    result = {
        "schemaVersion": 1,
        "kind": SIGNALING_PROJECTION_KIND,
        "truthRole": "rebuildable-signaling-specificity-projection",
        "observedAt": coordination_cut["observedAt"],
        "sourceCoordinationCutDigest": canonical_digest(coordination_cut),
        "sourceSignalingCutDigest": canonical_digest(cut),
        "signals": signals,
        "receptorDeliveries": deliveries,
        "nonClaims": [
            "legacyVisibilityScope is retained for historical interpretation and is not used to infer semanticScope, propagationMode, or compartmentRefs.",
            "A compartment is an explicit reference projection, not a mutable registry or transport boundary.",
            "Propagation mode describes intended social visibility semantics and does not itself deliver a network message.",
            "Receptors are deterministic interest filters only; no expression language, score, vote, policy, or readiness logic is evaluated.",
            "anomalyOrigin is preserved only when explicitly supplied with a source reference and is not a threat/security verdict.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def _finding_ids(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        candidate = value.get("findingId")
        if isinstance(candidate, str) and candidate:
            found.add(candidate)
        for child in value.values():
            found.update(_finding_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_finding_ids(child))
    return found


def measure_attention_history(
    manifest: dict[str, Any], base_dir: Path
) -> dict[str, Any]:
    if (
        manifest.get("schemaVersion") != 1
        or manifest.get("kind") != ATTENTION_HISTORY_KIND
    ):
        raise SocialFabricError("unsupported attention history manifest")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise SocialFabricError("documents must be non-empty list")
    horizons: dict[str, dict[str, Any]] = {}
    document_rows: list[dict[str, Any]] = []
    for index, raw in enumerate(documents):
        row = _obj(raw, f"documents[{index}]")
        relative = _text(row.get("path"), f"documents[{index}].path")
        path = (base_dir / relative).resolve()
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SocialFabricError(
                f"cannot read history document {relative}: {exc}"
            ) from exc
        source_digest = document.get("sourceSnapshotDigest") or document.get(
            "sourceCutDigest"
        )
        source_digest = _text(source_digest, f"{relative}.source digest")
        observed_at = _text(document.get("observedAt"), f"{relative}.observedAt")
        ids = sorted(_finding_ids(document))
        document_rows.append(
            {
                "path": relative,
                "horizonRef": source_digest,
                "observedAt": observed_at,
                "findingIds": ids,
            }
        )
        horizon = horizons.setdefault(
            source_digest,
            {"observedAtValues": set(), "findingIds": set(), "documentPaths": []},
        )
        horizon["observedAtValues"].add(observed_at)
        horizon["findingIds"].update(ids)
        horizon["documentPaths"].append(relative)

    horizon_rows: list[dict[str, Any]] = []
    finding_horizons: dict[str, set[str]] = defaultdict(set)
    for horizon_ref, value in sorted(horizons.items()):
        ids = sorted(value["findingIds"])
        for finding_id in ids:
            finding_horizons[finding_id].add(horizon_ref)
        horizon_rows.append(
            {
                "horizonRef": horizon_ref,
                "observedAtValues": sorted(value["observedAtValues"]),
                "findingIds": ids,
                "documentPaths": sorted(value["documentPaths"]),
            }
        )
    repeated = sorted(
        finding_id for finding_id, refs in finding_horizons.items() if len(refs) >= 2
    )
    standing = (
        "LONGITUDINAL_RECURRENCE_OBSERVED_MEASURE_ONLY"
        if repeated
        else "INSUFFICIENT_LONGITUDINAL_EVIDENCE_HOLD"
    )
    result = {
        "schemaVersion": 1,
        "kind": ATTENTION_MEASUREMENT_KIND,
        "truthRole": "measurement-only-no-attention-policy",
        "standing": standing,
        "rawDocumentCount": len(document_rows),
        "distinctHorizonCount": len(horizon_rows),
        "duplicateViewCountCollapsed": len(document_rows) - len(horizon_rows),
        "documents": document_rows,
        "horizons": horizon_rows,
        "findingIdsRepeatedAcrossDistinctHorizons": repeated,
        "promotionGate": {
            "requiresDistinctHorizons": 2,
            "requiresStableFindingRecurrence": True,
            "adaptationImplementationAuthorized": False,
        },
        "nonClaims": [
            "Repeated rendering of one source cut is not repeated stimulation.",
            "A shared finding code is not treated as the same stimulus identity.",
            "This measurement cannot suppress, attenuate, rank, or hide attention items.",
            "No attention adaptation is authorized by this measurement alone.",
        ],
    }
    result["measurementDigest"] = canonical_digest(result)
    return result


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return _obj(value, str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    project = sub.add_parser("project")
    project.add_argument("--cut", required=True, type=Path)
    measure = sub.add_parser("measure-attention")
    measure.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "project":
        result = compile_signaling(_load(args.cut))
    else:
        manifest = _load(args.manifest)
        result = measure_attention_history(manifest, args.manifest.resolve().parents[1])
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
