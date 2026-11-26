"""Deterministic, read-only Host Work obligation handoff coverage check.

Inputs are caller-supplied snapshots; coverage proves only exact navigation, never
freshness, semantic equivalence, effect authorization, or technical completion.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping

# Host work.get revision is a positive PostgreSQL bigint, not an arbitrary
# Python integer. This is the consumer's native wire admission boundary.
_MAX_HOST_REVISION = 2**63 - 1


def _unique_members(pairs):
    row = {}
    for key, value in pairs:
        if key in row:
            raise ValueError("duplicate JSON object member")
        row[key] = value
    return row


def _reject_constant(_value):
    raise ValueError("non-finite JSON numeric constant")


def _host_text(value: object) -> bool:
    # Match the Host snapshot text projection, not Unicode normalization.
    # PostgreSQL text cannot contain U+0000; lone surrogates are not UTF-8.
    return (
        isinstance(value, str) and bool(value) and value == value.strip()
        and "\x00" not in value
        and not any(0xD800 <= ord(ch) <= 0xDFFF for ch in value)
    )


def _strict_work(row: object, *, terminal: bool) -> dict:
    if not isinstance(row, dict) or set(row) != {"workRef", "revision", "state", "unresolved"}:
        raise ValueError("work must contain exactly workRef, revision, state, unresolved")
    ref = row["workRef"]
    # Native Host WorkCreateInput: 3..1024, trimmed, no C0 controls.
    if not _host_text(ref) or not 3 <= len(ref) <= 1024 or any(ord(ch) < 0x20 for ch in ref):
        raise ValueError("invalid workRef")
    if type(row["revision"]) is not int or not 1 <= row["revision"] <= _MAX_HOST_REVISION:
        raise ValueError("invalid revision")
    allowed = ("completed", "abandoned") if terminal else ("open",)
    if row["state"] not in allowed:
        raise ValueError("source must be terminal and successors open")
    obligations = row["unresolved"]
    if (not isinstance(obligations, list) or len(obligations) > 128
            or any(not _host_text(v) for v in obligations)):
        raise ValueError("unresolved must contain at most 128 nonempty trimmed Host strings")
    # Host WorkSnapshotInput is an ordered list[str], not a set. An identical
    # textual obligation can occur twice; never collapse occurrences by text.
    return row


def _ordinal(items: list[str], value: str, supplied: object, *, field: str) -> int | None:
    """Resolve one list occurrence; duplicate text requires an explicit index."""
    if supplied is None:
        matches = [i for i, item in enumerate(items) if item == value]
        if len(matches) > 1:
            raise ValueError(f"{field} required for repeated obligation text")
        return matches[0] if matches else None
    if type(supplied) is not int or supplied < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    if supplied >= len(items) or items[supplied] != value:
        return None
    return supplied


def assess(payload: object) -> dict:
    if not isinstance(payload, Mapping) or set(payload) != {"source", "successors", "links"}:
        raise ValueError("expected exact source, successors and links")
    source = _strict_work(payload["source"], terminal=True)
    raw_successors = payload["successors"]
    if not isinstance(raw_successors, list):
        raise ValueError("successors must be an array")
    successors = {}
    for row in raw_successors:
        item = _strict_work(row, terminal=False)
        if item["workRef"] == source["workRef"] or item["workRef"] in successors:
            raise ValueError("duplicate or self successor")
        successors[item["workRef"]] = item

    raw_links = payload["links"]
    if not isinstance(raw_links, list):
        raise ValueError("links must be an array")
    required = {"sourceObligation", "sourceRevision", "successorRef",
                "successorRevision", "successorObligation"}
    optional = {"sourceIndex", "successorIndex"}
    by_index = {}
    invalid_indices = []
    for link in raw_links:
        if not isinstance(link, dict) or not required <= set(link) or set(link) - (required | optional):
            raise ValueError("every link needs exact typed source and receiver witnesses")
        obligation = link["sourceObligation"]
        if not isinstance(obligation, str) or obligation not in source["unresolved"]:
            raise ValueError("link refers to nonexistent source obligation")
        index = _ordinal(source["unresolved"], obligation, link.get("sourceIndex"),
                         field="sourceIndex")
        if index is None:
            raise ValueError("sourceIndex inconsistent with source obligation")
        if index in by_index:
            raise ValueError("duplicate source obligation link")
        by_index[index] = link
        receiver = successors.get(link["successorRef"]) if isinstance(link["successorRef"], str) else None
        target = link["successorObligation"]
        if (type(link["sourceRevision"]) is not int
            or link["sourceRevision"] != source["revision"]
            or receiver is None
            or type(link["successorRevision"]) is not int
            or link["successorRevision"] != receiver["revision"]
            or not isinstance(target, str)
            or target not in receiver["unresolved"]):
            invalid_indices.append(index)
            continue
        if _ordinal(receiver["unresolved"], target, link.get("successorIndex"),
                    field="successorIndex") is None:
            invalid_indices.append(index)

    missing_indices = [i for i in range(len(source["unresolved"])) if i not in by_index]
    missing = [source["unresolved"][i] for i in missing_indices]
    invalid_links = [source["unresolved"][i] for i in invalid_indices]
    covered_indices = [
        i for i in range(len(source["unresolved"]))
        if i in by_index and i not in invalid_indices
    ]
    return {
        "kind": "ordivon.task-obligation-handoff-coverage-v1",
        "sourceRef": source["workRef"],
        "sourceRevision": source["revision"],
        "navigationCovered": not missing_indices and not invalid_indices,
        "missing": missing,
        "missingIndices": missing_indices,
        "invalidLinks": invalid_links,
        "invalidIndices": invalid_indices,
        "obligationsCarried": [source["unresolved"][i] for i in covered_indices],
        "coveredIndices": covered_indices,
        "semanticEquivalence": "UNKNOWN",
        "ownerCurrentness": "UNKNOWN",
        "technicalCompletion": "UNKNOWN",
        "effectAuthority": "NONE",
        "truthBoundary": "caller-supplied bounded snapshots only; reread native Host and owner truths",
    }


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(262145)
        if len(raw) > 262144:
            raise ValueError("input exceeds 262144 bytes")
        result = assess(json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_members,
            parse_constant=_reject_constant,
        ))
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        print(json.dumps({"kind": "ordivon.task-obligation-handoff-error-v1",
                          "error": str(exc), "navigationCovered": False}),
              file=sys.stdout)
        return 2
    # ASCII JSON escape sequences preserve the exact scalar text even when
    # the caller's stdout encoding cannot encode that scalar directly.
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["navigationCovered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
