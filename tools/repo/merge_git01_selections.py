#!/usr/bin/env python3
"""Lossless, fail-closed GIT-01 evidence-set union. No second registry."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import os
import tempfile
from pathlib import Path


class MergeConflict(ValueError):
    """No automatic choice can safely reconcile these two proof sources."""


def _issue(doc: dict) -> dict:
    items = doc.get("issues")
    if not isinstance(items, list):
        raise MergeConflict("issues must be an array")
    found = [x for x in items if isinstance(x, dict) and x.get("id") == "GIT-01"]
    if len(found) != 1:
        raise MergeConflict("expected exactly one GIT-01 issue")
    return found[0]


def _proofs(issue: dict) -> dict[str, dict]:
    rows = issue.get("consumerSelections")
    if not isinstance(rows, list):
        raise MergeConflict("consumerSelections must be an array")
    claims: dict[str, dict] = {}
    claimed_history: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise MergeConflict("claim must be an object")
        sha = row.get("localCommit")
        if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
            raise MergeConflict("localCommit must be a lowercase full Git SHA")
        if sha in claims:
            raise MergeConflict(f"duplicate localCommit {sha}")
        for field in ("owner", "consumer", "remoteWitness", "evidenceScope", "disposition"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise MergeConflict(f"{sha}: missing {field}")
        if "sourceQualification" in row:
            q = row["sourceQualification"]
            if not isinstance(q, dict):
                raise MergeConflict(f"{sha}: invalid sourceQualification")
            if q.get("branchDeletionAllowed") is not False:
                raise MergeConflict(f"{sha}: branchDeletionAllowed must be false")
        if "historicalCohort" in row:
            cohort = row["historicalCohort"]
            if (
                not isinstance(cohort, list)
                or not cohort
                or any(
                    not isinstance(member, str)
                    or re.fullmatch(r"[0-9a-f]{40}", member) is None
                    for member in cohort
                )
                or sha not in cohort
                or len(cohort) != len(set(cohort))
            ):
                raise MergeConflict(f"{sha}: invalid historicalCohort overlap or identity")
        # A representative may belong to its own cohort, but a different row
        # cannot re-claim that same historical source as a standalone commit.
        footprint = {sha, *row.get("historicalCohort", [])}
        if not claimed_history.isdisjoint(footprint):
            raise MergeConflict(f"{sha}: historicalCohort identity overlap")
        claimed_history.update(footprint)
        claims[sha] = row
    return claims


def merge_selections(current: dict, candidate: dict) -> dict:
    """Union immutable proof claims by SHA, leaving current Main's other truth intact."""
    main, old = _issue(current), _issue(candidate)
    cut = main.get("consumerSourceCut", {}).get("localMain")
    if not isinstance(cut, str) or not cut or cut != old.get("consumerSourceCut", {}).get("localMain"):
        raise MergeConflict("localMain source identity differs")
    current_claims, proposed = _proofs(main), _proofs(old)
    for sha, claim in proposed.items():
        if sha in current_claims and claim != current_claims[sha]:
            raise MergeConflict(f"conflicting proof for localCommit {sha}")
    result = copy.deepcopy(current)
    rows = _issue(result)["consumerSelections"]
    rows.extend(copy.deepcopy(proposed[sha]) for sha in sorted(proposed.keys() - current_claims.keys()))
    # Cross-branch cohorts can overlap even when each input is valid alone.
    # Validate the *joined* evidence before returning a canonical candidate.
    _proofs(_issue(result))
    return result


def merge_many_selections(current: dict, candidates: list[dict]) -> dict:
    """Join independently verified Owner shards without constructing a second registry.

    Every candidate must agree on the frozen local-Main identity. Reject an
    incompatible proof or overlapping cohort before returning any output.
    """
    if not candidates:
        raise MergeConflict("at least one candidate is required")
    result = current
    for candidate in candidates:
        result = merge_selections(result, candidate)
    # Preserve Main's existing evidence order but canonicalize every newly
    # admitted proof. Otherwise parallel PR arrival order changes JSON bytes
    # even when the selected consumer graph is exactly equivalent.
    existing = len(_issue(current)["consumerSelections"])
    selected = _issue(result)["consumerSelections"]
    selected[existing:] = sorted(selected[existing:], key=lambda row: row["localCommit"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--candidate", required=True, action="append", type=Path,
                        help="repeat for independent Owner/PR evidence candidates")
    parser.add_argument("--output", type=Path, help="explicit output; omit to print JSON")
    args = parser.parse_args()
    try:
        merged = merge_many_selections(
            json.loads(args.current.read_text(encoding="utf-8")),
            [json.loads(path.read_text(encoding="utf-8")) for path in args.candidate],
        )
    except (MergeConflict, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    value = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        sys.stdout.write(value)
    else:
        # Crash-safe publication: never leave a partially written owner census.
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=args.output.parent,
                prefix=f".{args.output.name}.", suffix=".tmp", delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, args.output)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        print(f"GIT-01 union: {len(_issue(merged)['consumerSelections'])} proofs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
