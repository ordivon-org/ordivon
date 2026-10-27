#!/usr/bin/env python3
"""Exact-SourceCut source *name* lookup from the existing owner classifier.

Agent-native source navigation: names are aliases, NEVER LEGO identities,
authority approvals, consumer proofs, or directory move instructions.
Never guess a winner for ambiguous names. The underlying Git tree and
manifest remain the only inputs, and the result is never persisted.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from affected_owners import project_source_classification

SEARCH_FIELDS = frozenset(
    {
        "sourceCell",
        "sourceCellDisplayName",
        "sourceSection",
        "sourceRegion",
        "semanticName",
        "verificationOwner",
        "sourceCellRole",
        "sourceSectionRole",
        "sourceFileForm",
    }
)
MAX_RETURNED = 100


def resolve_source_name(
    classification: dict[str, Any],
    *,
    name: str,
    field: str,
    scope_prefix: str | None = None,
    max_candidates: int = 30,
) -> dict[str, Any]:
    """Group exact-label matches by source cell, fail closed on collisions."""
    if not isinstance(name, str) or not name or name != name.strip():
        raise ValueError("name must be an exact, nonempty untrimmed source label")
    if field not in SEARCH_FIELDS:
        raise ValueError("field is not an allowed source navigation dimension")
    if type(max_candidates) is not int or not (1 <= max_candidates <= MAX_RETURNED):
        raise ValueError("max_candidates must be an integer from 1 to 100")
    if scope_prefix is not None and (
        not isinstance(scope_prefix, str)
        or not scope_prefix
        or scope_prefix.startswith(("/", "./"))
        or not scope_prefix.endswith("/")
        or ".." in scope_prefix.split("/")
        or "//" in scope_prefix
        or "\\" in scope_prefix
    ):
        raise ValueError("scope_prefix must be an exact canonical Git directory prefix")
    if (
        classification.get("truthRole")
        != "SOURCE_NAVIGATION_NOT_OWNER_OR_LEGO_QUALIFICATION"
    ):
        raise ValueError(
            "a real source classification, not a user-authored name list, is required"
        )
    if not isinstance(classification.get("sourceRevision"), str):
        raise TypeError("exact sourceRevision identity required")

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in classification["entries"]:
        path = entry["path"]
        if scope_prefix is not None and not path.startswith(scope_prefix):
            continue
        if entry.get(field) != name:
            continue
        # Resolve at the level where the queried name is defined. An owner-
        # area name shared by 29 nested cells is one area, not 29 competing
        # identities. A section name similarly denotes one source section.
        # Cell-role and file-form queries still distinguish individual cells.
        if field in {"semanticName", "verificationOwner"} and entry.get("verificationOwner"):
            key = f"verification-region/{entry['verificationOwner']}"
        elif field == "sourceSection" and entry.get("sourceSection"):
            key = f"source-section/{entry['sourceSection']}"
        else:
            key = entry.get("sourceCell") or (
                f"source-region/{entry['sourceRegion']}"
                if entry.get("sourceRegion")
                else f"unplaced-path/{path}"
            )
        grouped[key].append(entry)
    groups = sorted(grouped)
    candidates = []
    for key in groups[:max_candidates]:
        members = sorted(grouped[key], key=lambda r: r["path"])
        first = members[0]
        candidates.append(
            {
                "sourceGroup": key,
                "sourceCellRole": first.get("sourceCellRole"),
                "sourceName": (
                    first.get("semanticName") if field == "semanticName"
                    else first.get("verificationOwner") if field == "verificationOwner"
                    else first.get("sourceSection") if field == "sourceSection"
                    else first.get("sourceCellDisplayName") or first.get("semanticName")
                ),
                "classificationStanding": first.get("classificationStanding"),
                "matchedPaths": len(members),
                "sampleSourceObjects": [
                    {"path": e["path"], "sourceIdentity": e["sourceIdentity"]}
                    for e in members[:3]
                ],
                "sampleTruncated": len(members) > 3,
            }
        )
    match_count = len(groups)
    return {
        "kind": "ordivon.repository-source-name-resolution",
        "truthRole": "EXACT_SOURCE_ALIAS_NAVIGATION_NO_SEMANTIC_IDENTITY",
        "sourceRevision": classification["sourceRevision"],
        "sourceTree": classification["sourceTree"],
        "ownerManifestIdentity": classification["ownerManifestIdentity"],
        "classifierSourceIdentity": classification.get("classifierSourceIdentity"),
        "query": {
            "name": name,
            "field": field,
            "scopePrefix": scope_prefix,
            "matchType": "EXACT_FIELD_EQUALITY_NOT_FUZZY",
        },
        "standing": (
            "NOT_FOUND"
            if match_count == 0
            else "UNIQUE_SOURCE_GROUP_NOT_LEGO_PROOF"
            if match_count == 1
            else "AMBIGUOUS_MULTIPLE_SOURCE_GROUPS"
        ),
        "candidateGroupCount": match_count,
        "returnedCandidateGroups": len(candidates),
        "truncated": len(candidates) != match_count,
        "candidates": candidates,
        "proofReuseAdmissible": False,
        "semanticIdentityQualified": False,
        "externalConsumersQualified": False,
        "physicalRenameAdmissible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only exact Git source name lookup (never an owner selection)"
    )
    parser.add_argument(
        "--source-cut", required=True, help="exact immutable Git commit"
    )
    parser.add_argument("--name", required=True, help="exact existing source label")
    parser.add_argument("--field", choices=sorted(SEARCH_FIELDS), required=True)
    parser.add_argument("--scope-prefix", help="exact canonical source folder prefix")
    parser.add_argument("--max-candidates", type=int, default=30)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        classification = project_source_classification(args.repo, args.source_cut)
        result = resolve_source_name(
            classification,
            name=args.name,
            field=args.field,
            scope_prefix=args.scope_prefix,
            max_candidates=args.max_candidates,
        )
    except ValueError as err:
        parser.error(str(err))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
