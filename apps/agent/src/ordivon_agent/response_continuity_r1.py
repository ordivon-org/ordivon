from __future__ import annotations

import sqlite3
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path

from anc_canonical import JsonValue, canonical_digest


class ResponseContinuityError(RuntimeError):
    pass


class ResponseRevisionConflict(ResponseContinuityError):
    pass


class ResponseDeliveryState(StrEnum):
    PREPARED = "prepared"
    EMITTED = "emitted"
    DELIVERY_UNKNOWN = "delivery-unknown"
    CONFIRMED = "confirmed"


@dataclass(frozen=True, slots=True)
class ResponseContinuityReceipt:
    response_id: str
    caller_id: str
    caller_run_ref: str
    harness_run_id: str
    source_run_revision: int
    output_digest: str
    evidence_refs: tuple[str, ...]
    observed_attention_sequence: int
    presented_attention_sequence: int
    state: ResponseDeliveryState
    revision: int
    created_at_ms: int
    updated_at_ms: int

    def __post_init__(self) -> None:
        for value, label in (
            (self.response_id, "response identity"),
            (self.caller_id, "caller identity"),
            (self.caller_run_ref, "caller Run reference"),
            (self.harness_run_id, "Harness Run identity"),
        ):
            if not value or value != value.strip():
                raise ValueError(f"{label} must be non-empty and trimmed")
        if not self.output_digest.startswith("sha256:") or len(self.output_digest) != 71:
            raise ValueError("output digest must be sha256")
        if self.source_run_revision < 1 or self.revision < 1:
            raise ValueError("Run and response revisions must be positive")
        if (
            min(
                self.observed_attention_sequence,
                self.presented_attention_sequence,
                self.created_at_ms,
                self.updated_at_ms,
            )
            < 0
        ):
            raise ValueError("response continuity counters and times must be non-negative")
        if self.presented_attention_sequence > self.observed_attention_sequence:
            raise ValueError("presented Attention cannot exceed observed Attention")
        if self.updated_at_ms < self.created_at_ms:
            raise ValueError("response continuity update time precedes creation")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("response evidence references must be unique")
        for value in self.evidence_refs:
            if not value or value != value.strip():
                raise ValueError("response evidence references must be non-empty and trimmed")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.agent-response-continuity-receipt",
            "responseId": self.response_id,
            "callerId": self.caller_id,
            "callerRunRef": self.caller_run_ref,
            "harnessRunId": self.harness_run_id,
            "sourceRunRevision": self.source_run_revision,
            "outputDigest": self.output_digest,
            "evidenceRefs": list(self.evidence_refs),
            "observedAttentionSequence": self.observed_attention_sequence,
            "presentedAttentionSequence": self.presented_attention_sequence,
            "state": self.state.value,
            "revision": self.revision,
            "createdAtMs": self.created_at_ms,
            "updatedAtMs": self.updated_at_ms,
        }


_SCHEMA = """
CREATE TABLE IF NOT EXISTS response_receipts(
    response_id TEXT PRIMARY KEY,
    caller_id TEXT NOT NULL,
    caller_run_ref TEXT NOT NULL,
    harness_run_id TEXT NOT NULL,
    source_run_revision INTEGER NOT NULL CHECK(source_run_revision >= 1),
    output_digest TEXT NOT NULL,
    evidence_refs TEXT NOT NULL,
    observed_attention_sequence INTEGER NOT NULL CHECK(observed_attention_sequence >= 0),
    presented_attention_sequence INTEGER NOT NULL CHECK(presented_attention_sequence >= 0),
    state TEXT NOT NULL CHECK(state IN ('prepared','emitted','delivery-unknown','confirmed')),
    revision INTEGER NOT NULL CHECK(revision >= 1),
    created_at_ms INTEGER NOT NULL CHECK(created_at_ms >= 0),
    updated_at_ms INTEGER NOT NULL CHECK(updated_at_ms >= created_at_ms)
);
CREATE INDEX IF NOT EXISTS response_receipts_caller_idx
ON response_receipts(caller_id, caller_run_ref, updated_at_ms, response_id);
"""


class ResponseContinuityStore:
    """Agent-product authority for response delivery and presentation only.

    It never claims Provider/Runtime execution, Harness completion, Host semantic state,
    or safe effect redispatch. A delivery-unknown receipt therefore blocks presentation
    watermark advancement but does not alter the bound Harness Run.
    """

    def __init__(self, root: str | Path) -> None:
        root_path = Path(root).expanduser().resolve()
        root_path.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.database_path = root_path / "agent-response-continuity.sqlite3"
        self.connection = sqlite3.connect(self.database_path, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode = WAL")
        self.connection.execute("PRAGMA synchronous = FULL")
        self.connection.executescript(_SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> ResponseContinuityStore:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def create(self, receipt: ResponseContinuityReceipt) -> ResponseContinuityReceipt:
        if receipt.revision != 1 or receipt.state is not ResponseDeliveryState.PREPARED:
            raise ValueError("new response continuity receipt must be prepared revision 1")
        import json

        try:
            self.connection.execute(
                "INSERT INTO response_receipts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt.response_id,
                    receipt.caller_id,
                    receipt.caller_run_ref,
                    receipt.harness_run_id,
                    receipt.source_run_revision,
                    receipt.output_digest,
                    json.dumps(list(receipt.evidence_refs), separators=(",", ":")),
                    receipt.observed_attention_sequence,
                    receipt.presented_attention_sequence,
                    receipt.state.value,
                    receipt.revision,
                    receipt.created_at_ms,
                    receipt.updated_at_ms,
                ),
            )
        except sqlite3.IntegrityError:
            existing = self.get(receipt.response_id)
            if existing != receipt:
                raise ResponseRevisionConflict(
                    "response identity is already bound to different immutable content"
                )
            return existing
        return receipt

    def get(self, response_id: str) -> ResponseContinuityReceipt:
        row = self.connection.execute(
            "SELECT * FROM response_receipts WHERE response_id = ?", (response_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"response continuity receipt does not exist: {response_id}")
        return self._from_row(row)

    def latest_for_caller(
        self, caller_id: str, caller_run_ref: str
    ) -> ResponseContinuityReceipt | None:
        row = self.connection.execute(
            "SELECT * FROM response_receipts WHERE caller_id = ? AND caller_run_ref = ? "
            "ORDER BY updated_at_ms DESC, response_id DESC LIMIT 1",
            (caller_id, caller_run_ref),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def confirmed_presentation_watermark(self, caller_id: str, caller_run_ref: str) -> int:
        row = self.connection.execute(
            "SELECT COALESCE(MAX(presented_attention_sequence), 0) AS watermark "
            "FROM response_receipts WHERE caller_id = ? AND caller_run_ref = ? "
            "AND state = 'confirmed'",
            (caller_id, caller_run_ref),
        ).fetchone()
        return int(row["watermark"])

    def transition(
        self,
        response_id: str,
        *,
        expected_revision: int,
        state: ResponseDeliveryState,
        updated_at_ms: int,
        presented_attention_sequence: int | None = None,
    ) -> ResponseContinuityReceipt:
        current = self.get(response_id)
        if current.revision != expected_revision:
            raise ResponseRevisionConflict(
                f"response revision is {current.revision}, expected {expected_revision}"
            )
        allowed = {
            ResponseDeliveryState.PREPARED: {
                ResponseDeliveryState.EMITTED,
                ResponseDeliveryState.DELIVERY_UNKNOWN,
            },
            ResponseDeliveryState.EMITTED: {
                ResponseDeliveryState.CONFIRMED,
                ResponseDeliveryState.DELIVERY_UNKNOWN,
            },
            ResponseDeliveryState.DELIVERY_UNKNOWN: {ResponseDeliveryState.CONFIRMED},
            ResponseDeliveryState.CONFIRMED: set(),
        }
        if state not in allowed[current.state]:
            raise ResponseContinuityError(
                f"response delivery transition {current.state.value} -> {state.value} is invalid"
            )
        presented = (
            current.presented_attention_sequence
            if presented_attention_sequence is None
            else presented_attention_sequence
        )
        if (
            state is not ResponseDeliveryState.CONFIRMED
            and presented != current.presented_attention_sequence
        ):
            raise ResponseContinuityError(
                "presentation watermark may advance only on confirmed delivery"
            )
        successor = replace(
            current,
            state=state,
            revision=current.revision + 1,
            updated_at_ms=updated_at_ms,
            presented_attention_sequence=presented,
        )
        changed = self.connection.execute(
            "UPDATE response_receipts SET state = ?, revision = ?, updated_at_ms = ?, "
            "presented_attention_sequence = ? WHERE response_id = ? AND revision = ?",
            (
                successor.state.value,
                successor.revision,
                successor.updated_at_ms,
                successor.presented_attention_sequence,
                response_id,
                expected_revision,
            ),
        ).rowcount
        if changed != 1:
            raise ResponseRevisionConflict("response receipt changed during transition")
        return successor

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ResponseContinuityReceipt:
        import json

        return ResponseContinuityReceipt(
            response_id=row["response_id"],
            caller_id=row["caller_id"],
            caller_run_ref=row["caller_run_ref"],
            harness_run_id=row["harness_run_id"],
            source_run_revision=row["source_run_revision"],
            output_digest=row["output_digest"],
            evidence_refs=tuple(json.loads(row["evidence_refs"])),
            observed_attention_sequence=row["observed_attention_sequence"],
            presented_attention_sequence=row["presented_attention_sequence"],
            state=ResponseDeliveryState(row["state"]),
            revision=row["revision"],
            created_at_ms=row["created_at_ms"],
            updated_at_ms=row["updated_at_ms"],
        )


__all__ = [
    "ResponseContinuityError",
    "ResponseContinuityReceipt",
    "ResponseContinuityStore",
    "ResponseDeliveryState",
    "ResponseRevisionConflict",
]
