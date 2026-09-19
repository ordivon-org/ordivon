from __future__ import annotations

import hashlib
import json
import sqlite3
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rfc8785

from .provider_adapters import (
    EffectLedgerEffect,
    EffectLedgerSnapshot,
    ProviderProtocolError,
)


@dataclass(frozen=True)
class BrowserlessTurnEffectCoordinate:
    turn_request_id: str
    prompt_digest: str
    target_coordinate: str


BrowserlessTurnCoordinateResolver = Callable[..., BrowserlessTurnEffectCoordinate]


def _evidence_ref(
    ledger_path: Path,
    coordinate: BrowserlessTurnEffectCoordinate,
    *,
    state: str,
    updated_at_ms: int | None,
    receipt_json: str | None,
) -> str:
    payload = {
        "ledgerPathDigest": "sha256:"
        + hashlib.sha256(str(ledger_path.resolve()).encode("utf-8")).hexdigest(),
        "turnRequestId": coordinate.turn_request_id,
        "promptDigest": coordinate.prompt_digest,
        "targetCoordinate": coordinate.target_coordinate,
        "state": state,
        "updatedAtMs": updated_at_ms,
        "receiptJsonDigest": None
        if receipt_json is None
        else "sha256:" + hashlib.sha256(receipt_json.encode("utf-8")).hexdigest(),
    }
    return (
        "browserless-turn-ledger://sha256:"
        + hashlib.sha256(rfc8785.dumps(payload)).hexdigest()
    )


def _validate_coordinate(
    value: BrowserlessTurnEffectCoordinate,
) -> BrowserlessTurnEffectCoordinate:
    if not isinstance(value, BrowserlessTurnEffectCoordinate):
        raise TypeError(
            "Browserless coordinate resolver must return BrowserlessTurnEffectCoordinate"
        )
    if (
        not isinstance(value.turn_request_id, str)
        or not value.turn_request_id.strip()
        or not isinstance(value.prompt_digest, str)
        or not value.prompt_digest.startswith("sha256:")
        or not isinstance(value.target_coordinate, str)
        or not value.target_coordinate.strip()
    ):
        raise ValueError("Browserless effect coordinate is incomplete")
    return BrowserlessTurnEffectCoordinate(
        turn_request_id=value.turn_request_id.strip(),
        prompt_digest=value.prompt_digest.strip(),
        target_coordinate=value.target_coordinate.strip(),
    )


def _validate_receipt(
    receipt_json: str | None,
    coordinate: BrowserlessTurnEffectCoordinate,
) -> dict[str, Any]:
    if not isinstance(receipt_json, str) or not receipt_json:
        raise ProviderProtocolError("COMPLETED Browserless turn lacks receipt_json")
    try:
        receipt = json.loads(receipt_json)
    except json.JSONDecodeError as error:
        raise ProviderProtocolError(
            "Browserless turn receipt_json is invalid"
        ) from error
    if not isinstance(receipt, dict):
        raise ProviderProtocolError("Browserless turn receipt must be an object")
    expected = (
        coordinate.turn_request_id,
        coordinate.prompt_digest,
        coordinate.target_coordinate,
    )
    observed = (
        receipt.get("turnRequestId"),
        receipt.get("promptDigest"),
        receipt.get("targetResource"),
    )
    if observed != expected:
        raise ProviderProtocolError(
            "Browserless turn receipt identity does not match effect coordinate"
        )
    digest = receipt.get("receiptDigest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise ProviderProtocolError("Browserless turn receipt omitted receiptDigest")
    material = dict(receipt)
    material.pop("receiptDigest", None)
    computed = "sha256:" + hashlib.sha256(rfc8785.dumps(material)).hexdigest()
    if computed != digest:
        raise ProviderProtocolError("Browserless turn receiptDigest mismatch")
    return receipt


class BrowserlessTurnEffectLedgerReader:
    """Read the Harness Browserless turn_effects fence as domain-specific replay evidence.

    This reader is deliberately narrow. It knows only the ChatGPT Web SEND fence established by
    playwright_browserless_turn_once.py. It does not claim to cover arbitrary Agent Service effects.
    """

    def __init__(
        self,
        ledger_path: str | Path,
        coordinate_resolver: BrowserlessTurnCoordinateResolver,
    ) -> None:
        self._ledger_path = Path(ledger_path)
        self._coordinate_resolver = coordinate_resolver

    def __repr__(self) -> str:
        digest = hashlib.sha256(
            str(self._ledger_path.resolve()).encode("utf-8")
        ).hexdigest()[:12]
        return f"BrowserlessTurnEffectLedgerReader(ledger=<path:{digest}>)"

    def read_replay_snapshot(
        self,
        *,
        task: Any,
        envelope: Any,
        source_binding: Any,
        target_binding: Any,
        quiescence_proof: Any,
        source_receipt: Any | None,
        source_observations: tuple[Any, ...],
    ) -> EffectLedgerSnapshot:
        coordinate = _validate_coordinate(
            self._coordinate_resolver(
                task=task,
                envelope=envelope,
                source_binding=source_binding,
                target_binding=target_binding,
                quiescence_proof=quiescence_proof,
                source_receipt=source_receipt,
                source_observations=source_observations,
            )
        )
        task_id = task.id
        source_binding_id = source_binding.id
        target_binding_id = target_binding.id
        if not self._ledger_path.is_file():
            return EffectLedgerSnapshot(
                task_id=task_id,
                source_binding_id=source_binding_id,
                target_binding_id=target_binding_id,
                complete=False,
                effects=(),
                evidence_ref=_evidence_ref(
                    self._ledger_path,
                    coordinate,
                    state="LEDGER_MISSING",
                    updated_at_ms=None,
                    receipt_json=None,
                ),
            )

        uri = (
            "file:" + urllib.parse.quote(str(self._ledger_path.resolve())) + "?mode=ro"
        )
        db = sqlite3.connect(uri, uri=True)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA query_only=ON")
            table = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='turn_effects'"
            ).fetchone()
            if table is None:
                return EffectLedgerSnapshot(
                    task_id=task_id,
                    source_binding_id=source_binding_id,
                    target_binding_id=target_binding_id,
                    complete=False,
                    effects=(),
                    evidence_ref=_evidence_ref(
                        self._ledger_path,
                        coordinate,
                        state="TABLE_MISSING",
                        updated_at_ms=None,
                        receipt_json=None,
                    ),
                )
            row = db.execute(
                """
                SELECT prompt_digest,target_coordinate,state,receipt_json,updated_at_ms
                FROM turn_effects WHERE turn_request_id=?
                """,
                (coordinate.turn_request_id,),
            ).fetchone()
        finally:
            db.close()

        if row is None:
            return EffectLedgerSnapshot(
                task_id=task_id,
                source_binding_id=source_binding_id,
                target_binding_id=target_binding_id,
                complete=True,
                effects=(),
                evidence_ref=_evidence_ref(
                    self._ledger_path,
                    coordinate,
                    state="ABSENT",
                    updated_at_ms=None,
                    receipt_json=None,
                ),
            )

        if row["prompt_digest"] != coordinate.prompt_digest:
            raise ProviderProtocolError(
                "Browserless turn ledger prompt digest does not match effect coordinate"
            )
        if row["target_coordinate"] != coordinate.target_coordinate:
            raise ProviderProtocolError(
                "Browserless turn ledger target coordinate does not match effect coordinate"
            )
        state = row["state"]
        receipt_json = row["receipt_json"]
        updated_at_ms = row["updated_at_ms"]
        if not isinstance(state, str) or not state:
            raise ProviderProtocolError("Browserless turn ledger state is invalid")
        state = state.upper()
        evidence_ref = _evidence_ref(
            self._ledger_path,
            coordinate,
            state=state,
            updated_at_ms=updated_at_ms,
            receipt_json=receipt_json,
        )

        if state == "UNKNOWN":
            return EffectLedgerSnapshot(
                task_id=task_id,
                source_binding_id=source_binding_id,
                target_binding_id=target_binding_id,
                complete=False,
                effects=(
                    EffectLedgerEffect(
                        effect_id=coordinate.turn_request_id,
                        state="UNKNOWN",
                        idempotency_key=None,
                        replay_target_binding_id=None,
                        evidence_ref=evidence_ref,
                    ),
                ),
                evidence_ref=evidence_ref,
            )
        if state == "COMPLETED":
            _validate_receipt(receipt_json, coordinate)
            return EffectLedgerSnapshot(
                task_id=task_id,
                source_binding_id=source_binding_id,
                target_binding_id=target_binding_id,
                complete=True,
                effects=(
                    EffectLedgerEffect(
                        effect_id=coordinate.turn_request_id,
                        state="COMMITTED",
                        idempotency_key=None,
                        replay_target_binding_id=None,
                        evidence_ref=evidence_ref,
                    ),
                ),
                evidence_ref=evidence_ref,
            )
        raise ProviderProtocolError(
            f"unsupported Browserless turn ledger state: {state}"
        )
