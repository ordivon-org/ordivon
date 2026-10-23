#!/usr/bin/env python3
"""Read-only planning and exact admission for materialization-ledger reconciliation.

UNKNOWN and SUBMIT_OBSERVED are observation-only states: this module never treats them
as resend permission. PRE_EFFECT_FAILED is deliberately left for a separately authorized
explicit retry path rather than backlog cleanup.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

AMBIGUOUS_STANDINGS = frozenset({"unknown", "submit-observed"})


def classify_standing(standing: str) -> dict[str, Any]:
    if not isinstance(standing, str) or not standing:
        raise ValueError("materialization standing is required")
    if standing in AMBIGUOUS_STANDINGS:
        action = "RECONCILE_OBSERVATION"
        eligible = True
    elif standing in {"bound", "ready-confirmed"}:
        action = "NOOP_BOUND"
        eligible = False
    elif standing == "pre-effect-failed":
        action = "EXPLICIT_RETRY_REQUIRED"
        eligible = False
    elif standing == "human-required":
        action = "HUMAN_CONTROL_TRANSFER_REQUIRED"
        eligible = False
    elif standing == "prepared":
        action = "HOLD_PREPARED"
        eligible = False
    else:
        action = "HOLD_UNSUPPORTED_STANDING"
        eligible = False
    return {
        "action": action,
        "providerObservationEligible": eligible,
        "automaticRetryAuthorized": False,
        "safeToResend": False,
    }


def _read_rows(path: Path) -> list[sqlite3.Row]:
    path = Path(path)
    if not path.is_file():
        raise ValueError("materialization ledger does not exist")
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='requests'"
        ).fetchone()
        if exists is None:
            raise ValueError("materialization ledger has no requests table")
        return db.execute(
            """
            SELECT request_id, standing, provider_coordinate, evidence_digest,
                   effect_generation, updated_at_ms
            FROM requests
            ORDER BY request_id
            """
        ).fetchall()
    finally:
        db.close()


def _normalize_effect_ids(effect_ids: Iterable[str] | None) -> set[str] | None:
    if effect_ids is None:
        return None
    selected = set(effect_ids)
    if any(not isinstance(value, str) or not value for value in selected):
        raise ValueError("effect ids must be non-empty strings")
    return selected


def plan_ledger(
    ledger: Path, *, effect_ids: Iterable[str] | None = None
) -> dict[str, Any]:
    selected = _normalize_effect_ids(effect_ids)
    rows = _read_rows(Path(ledger))
    projected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        effect_id = str(row["request_id"])
        if selected is not None and effect_id not in selected:
            continue
        seen.add(effect_id)
        decision = classify_standing(str(row["standing"]))
        item: dict[str, Any] = {
            "effectId": effect_id,
            "standing": str(row["standing"]),
            **decision,
            "effectGeneration": int(row["effect_generation"]),
            "updatedAtMs": int(row["updated_at_ms"]),
        }
        provider_coordinate = row["provider_coordinate"]
        evidence_digest = row["evidence_digest"]
        if isinstance(provider_coordinate, str) and provider_coordinate:
            item["providerResource"] = provider_coordinate
        if isinstance(evidence_digest, str) and evidence_digest:
            item["evidenceDigest"] = evidence_digest
        projected.append(item)

    missing = sorted((selected or set()) - seen)
    counts: dict[str, int] = {}
    for item in projected:
        action = str(item["action"])
        counts[action] = counts.get(action, 0) + 1
    return {
        "schemaVersion": 1,
        "kind": "ordivon.materialization-ledger-reconcile-plan",
        "dryRun": True,
        "requestCount": len(projected),
        "actionCounts": counts,
        "missingEffectIds": missing,
        "requests": projected,
        "automaticRetryAuthorized": False,
    }


def execute_exact_reconciliation(
    *,
    effect_id: str,
    expected_effect_id: str,
    standing: str,
    reconcile: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Admit one caller-selected observation reconciliation and nothing else."""
    if (
        not isinstance(effect_id, str)
        or not effect_id
        or effect_id != expected_effect_id
    ):
        raise ValueError("exact effect identity is required for reconciliation")
    decision = classify_standing(standing)
    if not decision["providerObservationEligible"]:
        raise ValueError(
            f"materialization standing {standing!r} is not eligible for observation reconciliation"
        )
    result = reconcile()
    if not isinstance(result, dict):
        raise ValueError("reconcile callback must return one receipt object")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.materialization-ledger-reconcile-execution",
        "effectId": effect_id,
        "standingBefore": standing,
        **decision,
        "reconcileResult": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--effect-id", action="append", default=[])
    args = parser.parse_args()
    value = plan_ledger(
        args.ledger, effect_ids=args.effect_id if args.effect_id else None
    )
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
