"""Deterministic, read-only Host Work obligation handoff coverage check.

Inputs are caller-supplied snapshots; coverage proves only exact navigation, never
freshness, semantic equivalence, effect authorization, or technical completion.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping


def _strict_work(row: object, *, terminal: bool) -> dict:
    if not isinstance(row, dict) or set(row) != {"workRef", "revision", "state", "unresolved"}:
        raise ValueError("work must contain exactly workRef, revision, state, unresolved")
    if not isinstance(row["workRef"], str) or not row["workRef"].strip():
        raise ValueError("invalid workRef")
    if type(row["revision"]) is not int or row["revision"] < 1:
        raise ValueError("invalid revision")
    allowed = ("completed", "abandoned") if terminal else ("open",)
    if row["state"] not in allowed:
        raise ValueError("source must be terminal and successors open")
    obligations = row["unresolved"]
    if not isinstance(obligations, list) or any(
        not isinstance(v, str) or not v.strip() for v in obligations
    ):
        raise ValueError("unresolved must be a list of nonempty strings")
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
        result = assess(json.loads(raw))
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"kind": "ordivon.task-obligation-handoff-error-v1",
                          "error": str(exc), "navigationCovered": False}),
              file=sys.stdout)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["navigationCovered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
