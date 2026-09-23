#!/usr/bin/env python3
"""Social Fabric R2: CloudEvents-based signal lifecycle and shadow coordination."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

if __package__:
    from .social_fabric_r1 import SocialFabricError, canonical_digest
else:
    from social_fabric_r1 import SocialFabricError, canonical_digest

SCHEMA_VERSION = 1
CUT_KIND = "ordivon.social-fabric-coordination-cut"
PROJECTION_KIND = "ordivon.social-fabric-coordination-projection"

SCOPE_VALUES = {"self", "direct", "neighborhood", "domain", "system"}
MODE_VALUES = {"shared", "exclusive"}

CANDIDATE = "io.ordivon.social.candidate.v1"
SUPPORT = "io.ordivon.social.support.v1"
INHIBITION = "io.ordivon.social.inhibition.v1"
DAMAGE = "io.ordivon.social.damage.v1"
MODULATORY = "io.ordivon.social.modulatory.v1"
RETRACT = "io.ordivon.social.retract.v1"

KNOWN_TYPES = {CANDIDATE, SUPPORT, INHIBITION, DAMAGE, MODULATORY, RETRACT}


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SocialFabricError(f"{label} must be an object")
    return value


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SocialFabricError(f"{label} must be non-empty")
    return value


def _string_list(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise SocialFabricError(f"{label} must be a list")
    if not allow_empty and not value:
        raise SocialFabricError(f"{label} must be non-empty")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise SocialFabricError(f"{label}[{index}] must be non-empty")
        result.append(item)
    return result


def _instant(value: Any, label: str) -> datetime:
    text = _nonempty(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise SocialFabricError(f"{label} must be RFC3339 date-time") from error
    if parsed.tzinfo is None:
        raise SocialFabricError(f"{label} must include an offset")
    return parsed.astimezone(UTC)


def _evidence_refs(data: dict[str, Any], label: str) -> list[str]:
    return _string_list(data.get("evidenceRefs", []), f"{label}.evidenceRefs")


def _validate_event(event: dict[str, Any], label: str) -> None:
    if event.get("specversion") != "1.0":
        raise SocialFabricError(f"{label}.specversion must be CloudEvents 1.0")
    _nonempty(event.get("id"), f"{label}.id")
    _nonempty(event.get("source"), f"{label}.source")
    event_type = _nonempty(event.get("type"), f"{label}.type")
    if event_type not in KNOWN_TYPES:
        raise SocialFabricError(f"{label}.type unsupported: {event_type}")
    _nonempty(event.get("subject"), f"{label}.subject")
    event_time = _instant(event.get("time"), f"{label}.time")
    scope = event.get("ordivonscope")
    if scope not in SCOPE_VALUES:
        raise SocialFabricError(f"{label}.ordivonscope unsupported: {scope}")
    expires = event.get("ordivonexpiresat")
    if expires is not None:
        expires_at = _instant(expires, f"{label}.ordivonexpiresat")
        if expires_at <= event_time:
            raise SocialFabricError(f"{label}.ordivonexpiresat must be after time")
    for field in ("ordivonsupersedes", "ordivonrefreshes"):
        if field in event:
            _nonempty(event[field], f"{label}.{field}")
    data = _object(event.get("data"), f"{label}.data")
    _evidence_refs(data, f"{label}.data")

    if event_type == CANDIDATE:
        _nonempty(data.get("holderRef"), f"{label}.data.holderRef")
        _nonempty(data.get("effectOwner"), f"{label}.data.effectOwner")
        _nonempty(data.get("operation"), f"{label}.data.operation")
        if data.get("mode") not in MODE_VALUES:
            raise SocialFabricError(f"{label}.data.mode unsupported")
    elif event_type in {SUPPORT, INHIBITION}:
        _nonempty(data.get("candidateEventId"), f"{label}.data.candidateEventId")
        if event_type == SUPPORT:
            _nonempty(data.get("supporterRef"), f"{label}.data.supporterRef")
        else:
            _nonempty(data.get("inhibitorRef"), f"{label}.data.inhibitorRef")
            _nonempty(data.get("reasonCode"), f"{label}.data.reasonCode")
    elif event_type == DAMAGE:
        _nonempty(data.get("reasonCode"), f"{label}.data.reasonCode")
    elif event_type == MODULATORY:
        _nonempty(data.get("dimension"), f"{label}.data.dimension")
    elif event_type == RETRACT:
        _nonempty(data.get("targetEventId"), f"{label}.data.targetEventId")


def _validate_receptor(receptor: dict[str, Any], label: str) -> None:
    _nonempty(receptor.get("receptorId"), f"{label}.receptorId")
    accepted = _string_list(
        receptor.get("acceptedTypes"), f"{label}.acceptedTypes", allow_empty=False
    )
    unknown = sorted(set(accepted) - KNOWN_TYPES)
    if unknown:
        raise SocialFabricError(f"{label}.acceptedTypes unsupported: {unknown}")
    scopes = _string_list(receptor.get("scopes"), f"{label}.scopes", allow_empty=False)
    bad_scopes = sorted(set(scopes) - SCOPE_VALUES)
    if bad_scopes:
        raise SocialFabricError(f"{label}.scopes unsupported: {bad_scopes}")
    _string_list(receptor.get("subjectPrefixes", []), f"{label}.subjectPrefixes")
    _string_list(receptor.get("sources", []), f"{label}.sources")
    max_age = receptor.get("maxAgeSeconds")
    if max_age is not None and (not isinstance(max_age, int) or max_age < 0):
        raise SocialFabricError(f"{label}.maxAgeSeconds must be non-negative integer")
    if not isinstance(receptor.get("requireEvidence", False), bool):
        raise SocialFabricError(f"{label}.requireEvidence must be boolean")


def validate_cut(cut: dict[str, Any]) -> None:
    if cut.get("schemaVersion") != SCHEMA_VERSION:
        raise SocialFabricError("unsupported coordination cut schemaVersion")
    if cut.get("kind") != CUT_KIND:
        raise SocialFabricError("unsupported coordination cut kind")
    _instant(cut.get("observedAt"), "observedAt")

    events = cut.get("events")
    if not isinstance(events, list):
        raise SocialFabricError("events must be a list")
    seen_events: set[str] = set()
    for index, raw in enumerate(events):
        event = _object(raw, f"events[{index}]")
        _validate_event(event, f"events[{index}]")
        event_id = event["id"]
        if event_id in seen_events:
            raise SocialFabricError(f"duplicate event identity: {event_id}")
        seen_events.add(event_id)

    receptors = cut.get("receptors", [])
    if not isinstance(receptors, list):
        raise SocialFabricError("receptors must be a list")
    seen_receptors: set[str] = set()
    for index, raw in enumerate(receptors):
        receptor = _object(raw, f"receptors[{index}]")
        _validate_receptor(receptor, f"receptors[{index}]")
        receptor_id = receptor["receptorId"]
        if receptor_id in seen_receptors:
            raise SocialFabricError(f"duplicate receptor identity: {receptor_id}")
        seen_receptors.add(receptor_id)

    for event in events:
        for field in ("ordivonsupersedes", "ordivonrefreshes"):
            target_id = event.get(field)
            if target_id is None:
                continue
            if target_id not in seen_events:
                raise SocialFabricError(f"{event['id']}.{field} target is unknown")
            if target_id == event["id"]:
                raise SocialFabricError(f"{event['id']}.{field} cannot target itself")
        if event["type"] == RETRACT:
            target_id = event["data"]["targetEventId"]
            if target_id not in seen_events:
                raise SocialFabricError(f"{event['id']} retract target is unknown")
            if target_id == event["id"]:
                raise SocialFabricError(f"{event['id']} cannot retract itself")


def _lifecycle(cut: dict[str, Any]) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    observed_at = _instant(cut["observedAt"], "observedAt")
    events = {event["id"]: event for event in cut["events"]}
    status: dict[str, str] = {}
    for event_id, event in events.items():
        event_time = _instant(event["time"], f"{event_id}.time")
        expires = event.get("ordivonexpiresat")
        if event_time > observed_at:
            status[event_id] = "future"
        elif (
            expires is not None
            and _instant(expires, f"{event_id}.ordivonexpiresat") <= observed_at
        ):
            status[event_id] = "expired"
        else:
            status[event_id] = "active"

    eligible = {event_id for event_id, state in status.items() if state == "active"}

    for event_id in sorted(eligible):
        event = events[event_id]
        if event["type"] == RETRACT:
            target_id = event["data"]["targetEventId"]
            if status.get(target_id) == "active":
                status[target_id] = "retracted"

    for event_id in sorted(eligible):
        event = events[event_id]
        target_id = event.get("ordivonrefreshes")
        if target_id is not None:
            target = events[target_id]
            if (
                event["type"] != target["type"]
                or event["source"] != target["source"]
                or event["subject"] != target["subject"]
            ):
                raise SocialFabricError(
                    f"{event_id}.ordivonrefreshes must preserve type/source/subject"
                )
            if _instant(event["time"], f"{event_id}.time") <= _instant(
                target["time"], f"{target_id}.time"
            ):
                raise SocialFabricError(
                    f"{event_id}.ordivonrefreshes must be newer than target"
                )
            if status.get(target_id) == "active":
                status[target_id] = "refreshed"

        target_id = event.get("ordivonsupersedes")
        if target_id is not None:
            target = events[target_id]
            if event["subject"] != target["subject"]:
                raise SocialFabricError(
                    f"{event_id}.ordivonsupersedes must preserve subject"
                )
            if status.get(target_id) == "active":
                status[target_id] = "superseded"

    return status, events


def _finding(
    code: str,
    severity: str,
    subject_refs: list[str],
    evidence_refs: list[str],
    detail: str,
) -> dict[str, Any]:
    body = {
        "code": code,
        "severity": severity,
        "subjectRefs": sorted(set(subject_refs)),
        "evidenceRefs": sorted(set(evidence_refs)),
        "detail": detail,
    }
    return {
        "findingId": "finding:" + canonical_digest(body),
        **body,
        "truthBoundary": (
            "Shadow coordination finding only; it does not select a winner, mint a lease, "
            "grant execution, or alter natural-owner authority."
        ),
    }


def _route(
    cut: dict[str, Any],
    status: dict[str, str],
    events: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    observed_at = _instant(cut["observedAt"], "observedAt")
    deliveries: list[dict[str, Any]] = []
    for receptor in sorted(cut.get("receptors", []), key=lambda row: row["receptorId"]):
        accepted = set(receptor["acceptedTypes"])
        scopes = set(receptor["scopes"])
        prefixes = tuple(receptor.get("subjectPrefixes", []))
        sources = set(receptor.get("sources", []))
        max_age = receptor.get("maxAgeSeconds")
        require_evidence = receptor.get("requireEvidence", False)
        signal_ids: list[str] = []
        for event_id, event in sorted(events.items()):
            if status[event_id] != "active":
                continue
            if event["type"] not in accepted or event["ordivonscope"] not in scopes:
                continue
            if prefixes and not event["subject"].startswith(prefixes):
                continue
            if sources and event["source"] not in sources:
                continue
            if max_age is not None:
                age = (
                    observed_at - _instant(event["time"], f"{event_id}.time")
                ).total_seconds()
                if age < 0 or age > max_age:
                    continue
            if require_evidence and not _evidence_refs(
                event["data"], f"{event_id}.data"
            ):
                continue
            signal_ids.append(event_id)
        deliveries.append(
            {
                "receptorId": receptor["receptorId"],
                "signalIds": signal_ids,
                "truthBoundary": "Delivery is an interest match, not authority or acceptance.",
            }
        )
    return deliveries


def compile_coordination_projection(cut: dict[str, Any]) -> dict[str, Any]:
    validate_cut(cut)
    status, events = _lifecycle(cut)
    active_events = {
        event_id: event
        for event_id, event in events.items()
        if status[event_id] == "active"
    }
    candidates = {
        event_id: event
        for event_id, event in active_events.items()
        if event["type"] == CANDIDATE
    }
    findings: list[dict[str, Any]] = []
    support_by_candidate: dict[str, list[str]] = {
        event_id: [] for event_id in candidates
    }
    inhibition_by_candidate: dict[str, list[str]] = {
        event_id: [] for event_id in candidates
    }
    conflict_by_candidate: dict[str, set[str]] = {
        event_id: set() for event_id in candidates
    }
    all_candidate_ids = {
        event_id for event_id, event in events.items() if event["type"] == CANDIDATE
    }

    for event_id, event in sorted(active_events.items()):
        if event["type"] not in {SUPPORT, INHIBITION}:
            continue
        target = event["data"]["candidateEventId"]
        if target not in candidates:
            findings.append(
                _finding(
                    "REFERENCE_TARGET_NOT_ACTIVE"
                    if target in all_candidate_ids
                    else "REFERENCE_TARGET_UNKNOWN",
                    "info" if target in all_candidate_ids else "warning",
                    [event_id, target],
                    _evidence_refs(event["data"], f"{event_id}.data"),
                    "Support/inhibition points to a candidate that is not active in this cut.",
                )
            )
            continue
        if event["type"] == SUPPORT:
            support_by_candidate[target].append(event_id)
        else:
            inhibition_by_candidate[target].append(event_id)

    grouped: dict[str, list[str]] = {}
    for event_id, event in candidates.items():
        grouped.setdefault(event["subject"], []).append(event_id)

    for subject, ids in sorted(grouped.items()):
        for left_id, right_id in combinations(sorted(ids), 2):
            left = candidates[left_id]
            right = candidates[right_id]
            if (
                left["data"]["mode"] != "exclusive"
                and right["data"]["mode"] != "exclusive"
            ):
                continue
            conflict_by_candidate[left_id].add(right_id)
            conflict_by_candidate[right_id].add(left_id)
            findings.append(
                _finding(
                    "SUBJECT_MODE_CONFLICT",
                    "warning",
                    [subject, left_id, right_id],
                    _evidence_refs(left["data"], f"{left_id}.data")
                    + _evidence_refs(right["data"], f"{right_id}.data"),
                    (
                        f"Active candidates {left_id} and {right_id} target the same subject; "
                        "at least one requests exclusive coordination."
                    ),
                )
            )

    standing: list[dict[str, Any]] = []
    for candidate_id, event in sorted(candidates.items()):
        explicit = sorted(inhibition_by_candidate[candidate_id])
        conflicts = sorted(conflict_by_candidate[candidate_id])
        standing.append(
            {
                "candidateEventId": candidate_id,
                "subject": event["subject"],
                "holderRef": event["data"]["holderRef"],
                "effectOwner": event["data"]["effectOwner"],
                "operation": event["data"]["operation"],
                "mode": event["data"]["mode"],
                "supportEventIds": sorted(support_by_candidate[candidate_id]),
                "inhibitionEventIds": explicit,
                "conflictsWith": conflicts,
                "state": "inhibited_shadow"
                if explicit or conflicts
                else "eligible_shadow",
                "truthBoundary": (
                    "Shadow standing only; support is not a vote count and this state cannot "
                    "authorize, schedule, or execute the operation."
                ),
            }
        )

    lifecycle = [
        {
            "eventId": event_id,
            "type": events[event_id]["type"],
            "subject": events[event_id]["subject"],
            "scope": events[event_id]["ordivonscope"],
            "status": status[event_id],
        }
        for event_id in sorted(events)
    ]
    deliveries = _route(cut, status, events)
    active_damage = sorted(
        event_id for event_id, event in active_events.items() if event["type"] == DAMAGE
    )
    active_modulatory = sorted(
        event_id
        for event_id, event in active_events.items()
        if event["type"] == MODULATORY
    )
    findings.sort(key=lambda row: (row["severity"], row["code"], row["findingId"]))
    attention = [row for row in findings if row["severity"] in {"warning", "error"}]

    result = {
        "schemaVersion": 1,
        "kind": PROJECTION_KIND,
        "truthRole": "rebuildable-shadow-coordination-projection",
        "observedAt": cut["observedAt"],
        "sourceCutDigest": canonical_digest(cut),
        "lifecycle": lifecycle,
        "receptorDeliveries": deliveries,
        "candidateStanding": standing,
        "damageSignals": active_damage,
        "modulatorySignals": active_modulatory,
        "findings": findings,
        "attention": attention,
        "commonOperatingPicture": {
            "activeSignalCount": sum(state == "active" for state in status.values()),
            "activeCandidateCount": len(candidates),
            "inhibitedCandidateCount": sum(
                row["state"] == "inhibited_shadow" for row in standing
            ),
            "conflictFindingCount": sum(
                row["code"] == "SUBJECT_MODE_CONFLICT" for row in findings
            ),
            "activeDamageSignalCount": len(active_damage),
            "activeModulatorySignalCount": len(active_modulatory),
            "receptorDeliveryCount": sum(len(row["signalIds"]) for row in deliveries),
        },
        "commitmentProjection": {
            "state": "NOT_EVALUATED",
            "reason": (
                "R2 stops at deterministic Candidate/Support/Inhibition shadow semantics; "
                "policy quorum and owner-native enforcement are separate gates."
            ),
        },
        "nonClaims": [
            "No candidate is selected as a winner.",
            "Support count is not a score, rank, quorum, priority, or vote.",
            "Lifecycle expiry is not an owner-native lease unless the natural owner explicitly binds one.",
            "A receptor delivery does not grant authority.",
            "An inhibition is a shadow coordination result and does not itself block an external effect.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("view", choices=("current", "attention", "route"))
    parser.add_argument("--cut", type=Path, required=True)
    args = parser.parse_args()
    cut = _object(json.loads(args.cut.read_text(encoding="utf-8")), str(args.cut))
    projection = compile_coordination_projection(cut)
    if args.view == "current":
        output: Any = projection
    elif args.view == "attention":
        output = {
            "schemaVersion": 1,
            "kind": "ordivon.social-fabric-coordination-attention",
            "observedAt": projection["observedAt"],
            "sourceCutDigest": projection["sourceCutDigest"],
            "items": projection["attention"],
        }
    else:
        output = {
            "schemaVersion": 1,
            "kind": "ordivon.social-fabric-receptor-deliveries",
            "observedAt": projection["observedAt"],
            "sourceCutDigest": projection["sourceCutDigest"],
            "deliveries": projection["receptorDeliveries"],
        }
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
