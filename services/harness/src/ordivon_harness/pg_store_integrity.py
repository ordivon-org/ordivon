"""Original Journal history, snapshot and UNKNOWN receipt integrity.

Original PostgreSQL connection and existing transaction authority are retained.
"""

from __future__ import annotations
from collections.abc import Iterator
from contextlib import contextmanager
from anc_canonical import JsonValue
from psycopg.pq import TransactionStatus
from .core_contracts import HarnessRunContract
from .store_errors import (
    HarnessJournalCorruption,
    HarnessObjectCorrupt,
    HarnessObjectMissing,
    HarnessRevisionConflict,
    HarnessTerminalConflict,
)
from .store import (
    HarnessRunEventRecord,
    HarnessRunProjection,
    HarnessRunStatus,
    harness_run_status_after_event,
)

from .pg_store_codec import _CONTRACT_OBJECT_KIND

def invalid_typed_effect_reference_fields(
    event_kind: str, data: dict[str, JsonValue], reference_kinds: dict[str, str],
) -> tuple[str, ...]:
    """Known original Provider/Tool object fields require matching typed edges.

    Unknown opaque event fields are not inferred. Null privacy-redacted and
    historical optional object fields are allowed. Kind is durable metadata,
    not part of the PostgreSQL CAS payload digest.
    """
    if event_kind in {
        "harness.provider-call-claimed", "harness.provider-call-superseded",
        "harness.provider-call-dispatching", "harness.provider-call-completed",
        "harness.provider-call-failed", "harness.provider-call-unknown",
    }:
        required = {
            "providerCallRecordObjectDigest": "harness-provider-call-record",
            "stateObjectDigest": "harness-run-state",
        }
        optional = {
            "requestObjectDigest": "agent-turn-request",
            "resultObjectDigest": "agent-turn-result",
            "failureObjectDigest": "harness-provider-call-failure",
        }
    elif event_kind == "harness.tool-step-prepared":
        required = {
            "toolStepIntentObjectDigest": "harness-tool-step-intent",
            "snapshotObjectDigest": "harness-run-snapshot",
            "stateObjectDigest": "harness-run-state",
        }
        optional = {"dispatchFenceObjectDigest": "harness-dispatch-fence"}
    elif event_kind in {
        "harness.tool-step-recorded", "harness.tool-step-unknown", "harness.tool-step-reconciled",
    }:
        required = {
            "toolStepIntentObjectDigest": "harness-tool-step-intent",
            "receiptObjectDigest": "harness-tool-step-receipt",
        }
        optional = {
            "dispatchFenceObjectDigest": "harness-dispatch-fence",
            "previousReceiptObjectDigest": "harness-tool-step-receipt",
            "observationObjectDigest": "harness-tool-observation",
        }
    else:
        return ()
    fields = required | {field: kind for field, kind in optional.items() if data.get(field) is not None}
    return tuple(
        field for field, kind in fields.items()
        if not isinstance(data.get(field), str) or reference_kinds.get(data[field]) != kind
    )


class PostgresIntegrity:
    """Original Journal history, snapshot and UNKNOWN receipt integrity."""

    @contextmanager
    def _history_snapshot(self, *, harness_run_id: str | None = None) -> Iterator[None]:
        """Read one self-consistent original PostgreSQL history without a second Store.

        The normal autocommit Store uses a fresh read-only REPEATABLE READ
        snapshot. If invoked inside an existing caller-owned transaction, it
        cannot silently change the caller's isolation: either the caller already
        has a stable snapshot, or a writable READ COMMITTED transaction fences
        a single original Run using its existing Run-row FOR UPDATE discipline.
        Global Doctor needs a stable snapshot: existing row locks do not
        exclude new Run creation, new CAS objects, or other global phantoms.
        """
        standalone = self.connection.info.transaction_status is TransactionStatus.IDLE
        with self.connection.transaction():
            if standalone:
                self.connection.execute(
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                )
            else:
                level = self.connection.execute(
                    "SHOW transaction_isolation"
                ).fetchone()["transaction_isolation"]
                if level in {"read committed", "read uncommitted"}:
                    if harness_run_id is None:
                        raise HarnessRevisionConflict(
                            "global Harness Doctor requires a stable caller snapshot; "
                            "use standalone Doctor or begin REPEATABLE READ before any query"
                        )
                    read_only = self.connection.execute(
                        "SHOW transaction_read_only"
                    ).fetchone()["transaction_read_only"]
                    if read_only == "on":
                        raise HarnessJournalCorruption(
                            "read-only caller transaction has no stable history snapshot"
                        )
                    self.connection.execute(
                        "SELECT harness_run_id FROM runs "
                        "WHERE harness_run_id=%s FOR SHARE",
                        (harness_run_id,),
                    ).fetchall()
            yield

    def _require_original_unknown_stop_receipt(
        self,
        *,
        harness_run_id: str,
        contract_digest: str,
        data: dict[str, JsonValue],
        referenced_receipt_digests: set[str],
    ) -> None:
        """One original typed UNKNOWN receipt rule for Writer and Doctor.

        The stopped projection cannot prove this by its stopCode alone.
        Only the original immutable typed receipt with an Event reference and
        exact Contract/Run binding can justify UNKNOWN audit quarantine. It
        never authorizes physical resource release.
        """
        from .independent_result_contracts import IndependentHarnessRunReceipt

        receipt_object_digest = data.get("runReceiptObjectDigest")
        receipt_digest = data.get("runReceiptDigest")
        if (
            not isinstance(receipt_object_digest, str)
            or not isinstance(receipt_digest, str)
            or receipt_object_digest not in referenced_receipt_digests
        ):
            raise HarnessTerminalConflict(
                "UNKNOWN fault requires its original typed immutable Run Receipt"
            )
        raw = self.get_object(
            receipt_object_digest,
            expected_kind="independent-harness-run-receipt",
        )
        if not isinstance(raw, dict):
            raise HarnessTerminalConflict("UNKNOWN fault Run Receipt is not an object")
        receipt = IndependentHarnessRunReceipt.from_dict(raw)
        if (
            receipt.digest != receipt_digest
            or receipt.harness_run_id != harness_run_id
            or receipt.contract_digest != contract_digest
            or receipt.termination_code != data.get("stopCode")
            or receipt.stop_reason != "unknown"
        ):
            raise HarnessTerminalConflict(
                "UNKNOWN fault Run Receipt differs from original Run identity"
            )

    def _validate_event_edges(
        self,
        harness_run_id: str,
        events: tuple[HarnessRunEventRecord, ...],
        *,
        contract_object_digest: str,
    ) -> None:
        """Verify mandatory original Event edges without inventing optional refs.

        The durable Event row is authoritative for its payload digest, and the
        Run projection is authoritative for the creation Contract digest.
        Known typed Provider/Tool object references are checked from their
        actual writer schema. Arbitrary opaque event fields are not inferred.
        """
        rows = self.connection.execute(
            "SELECT e.event_id, e.payload_digest, e.event_kind, "
            "r.digest AS reference_digest, r.role AS reference_role, "
            "r.harness_run_id AS reference_run_id, o.kind AS reference_kind "
            "FROM run_events e "
            "LEFT JOIN run_object_refs r ON r.event_id=e.event_id "
            "LEFT JOIN objects o ON o.digest=r.digest "
            "WHERE e.harness_run_id=%s ORDER BY e.run_revision",
            (harness_run_id,),
        ).fetchall()
        refs: dict[str, set[tuple[str, str]]] = {}
        kinds: dict[str, dict[str, str]] = {}
        for row in rows:
            event_id = row["event_id"]
            ref_digest = row["reference_digest"]
            if (ref_digest is None or row["reference_run_id"] != harness_run_id
                    or row["reference_kind"] is None):
                raise HarnessJournalCorruption(
                    "Original Run Event has missing or foreign-owned object references"
                )
            refs.setdefault(event_id, set()).add(
                (row["reference_role"], ref_digest)
            )
            if row["reference_role"] == "reference":
                kinds.setdefault(event_id, {})[ref_digest] = row["reference_kind"]
        if set(refs) != {event.event_id for event in events}:
            raise HarnessJournalCorruption("Original Run Event reference graph differs")
        for event in events:
            edges = refs[event.event_id]
            payload_edges = {digest for role, digest in edges if role == "payload"}
            if payload_edges != {event.payload_digest}:
                raise HarnessJournalCorruption(
                    "Original Run Event payload reference differs from Journal"
                )
            invalid = invalid_typed_effect_reference_fields(
                event.event_kind, event.data, kinds.get(event.event_id, {})
            )
            if invalid:
                raise HarnessJournalCorruption(
                    "Original typed effect Event has missing or mismatched object references: " + ", ".join(invalid)
                )
            if event.event_kind == "harness.run-created":
                expected = {
                    ("payload", event.payload_digest),
                    ("reference", contract_object_digest),
                }
                if edges != expected:
                    raise HarnessJournalCorruption(
                        "Original Run creation Contract reference differs"
                    )

    def validate_run_history(
        self, harness_run_id: str
    ) -> tuple[HarnessRunProjection, tuple[HarnessRunEventRecord, ...]]:
        """Return the exact original cut verified inside one native snapshot."""
        with self._history_snapshot(harness_run_id=harness_run_id):
            projection, events, _ = self._validate_run_history_snapshot(harness_run_id)
            return projection, events

    def _validate_run_history_snapshot(
        self, harness_run_id: str
    ) -> tuple[HarnessRunProjection, tuple[HarnessRunEventRecord, ...], HarnessRunContract]:
        projection = self.load_run(harness_run_id)
        events = self.list_run_events(harness_run_id)
        return projection, events, self._validate_original_run_history(projection, events)

    def _validate_original_run_history(
        self, projection: HarnessRunProjection, events: tuple[HarnessRunEventRecord, ...]
    ) -> HarnessRunContract:
        """Validate an exact original cut under its caller's snapshot/row lock."""
        harness_run_id = projection.harness_run_id
        if not events or events[0].event_kind != "harness.run-created":
            raise HarnessJournalCorruption("Run has no creation Event")
        status = HarnessRunStatus.CREATED
        when = -1
        terminal = None
        for revision, event in enumerate(events, 1):
            if (
                event.run_revision != revision
                or event.harness_run_id != harness_run_id
                or event.recorded_at_ms < when
                or terminal is not None
            ):
                raise HarnessJournalCorruption(
                    "Run Event chain violates revision/time/terminal law"
                )
            status = harness_run_status_after_event(event.event_kind, status)
            if status.terminal:
                terminal = event.event_id
            when = event.recorded_at_ms
        if (
            projection.revision != len(events)
            or projection.status is not status
            or projection.terminal_event_id != terminal
            or projection.updated_at_ms != when
        ):
            raise HarnessJournalCorruption("Run projection diverges from Journal")
        contract = self.get_object(
            projection.contract_object_digest, expected_kind=_CONTRACT_OBJECT_KIND
        )
        if not isinstance(contract, dict):
            raise HarnessObjectCorrupt("Harness Run contract object must be dict")
        self._validate_event_edges(
            harness_run_id, events,
            contract_object_digest=projection.contract_object_digest,
        )
        try:
            restored = HarnessRunContract.from_dict(contract)
        except ValueError as error:
            raise HarnessObjectCorrupt("Harness Run contract object invalid") from error
        if (
            restored.harness_run_id != harness_run_id
            or restored.digest != projection.contract_digest
            or restored.caller_id != projection.caller_id
            or restored.caller_run_ref != projection.caller_run_ref
        ):
            raise HarnessJournalCorruption("Run contract metadata differs from Journal")
        if (
            status is HarnessRunStatus.STOPPED
            and events[-1].event_kind == "harness.run-stopped"
            and events[-1].data.get("stopCode") in {
                "provider_state_unknown",
                "runtime_unknown",
                "cancel_unknown",
            }
        ):
            # Legacy/foreign Writers may have bypassed the typed admission
            # fence. Doctor must not certify a raw stopCode as healthy history.
            # Reuse Writer's *same* original receipt rule, not a parallel
            # approximation or another pending-state registry.
            references = {
                row["digest"]
                for row in self.connection.execute(
                    "SELECT digest FROM run_object_refs "
                    "WHERE event_id=%s AND role='reference'",
                    (events[-1].event_id,),
                )
            }
            try:
                self._require_original_unknown_stop_receipt(
                    harness_run_id=harness_run_id,
                    contract_digest=projection.contract_digest,
                    data=events[-1].data,
                    referenced_receipt_digests=references,
                )
            except (HarnessTerminalConflict, HarnessObjectMissing,
                    HarnessObjectCorrupt, ValueError, TypeError) as error:
                raise HarnessJournalCorruption(
                    "UNKNOWN terminal lacks its qualified original Run Receipt"
                ) from error
        return restored

    def doctor(self, *, full: bool = True) -> dict[str, JsonValue]:
        with self._history_snapshot():
            return self._doctor_consistent(full=full)

    def _doctor_consistent(self, *, full: bool = True) -> dict[str, JsonValue]:
        objects = self.connection.execute("SELECT digest FROM objects").fetchall()
        for row in objects:
            self.inspect_object(row["digest"])
        runs = self.list_runs()
        for run in runs:
            _, history, contract = self._validate_run_history_snapshot(run.harness_run_id)
            if not run.status.terminal:
                continue
            if not any(
                event.event_kind.startswith(
                    ("harness.provider-call-", "harness.tool-step-")
                )
                for event in history
            ):
                continue
            if (
                run.status is HarnessRunStatus.STOPPED
                and history[-1].data.get("stopCode") in {
                    "provider_state_unknown",
                    "runtime_unknown",
                    "cancel_unknown",
                }
            ):
                # The original typed UNKNOWN terminal was verified above.
                # Pending external effects belong to QUARANTINED_HELD, not a
                # healthy normal terminal, so do not require them settled.
                continue
            from .ordivon.provider_record_reader import inspect_original_effect_sources

            # Reuse the Writer's original typed complete-history scanner and
            # CAS Provider reader. This is a pure read; neither a second
            # Pending registry nor a Domain/Runtime release certification.
            try:
                pending_provider, pending_tool = inspect_original_effect_sources(
                    self, contract, history
                )
            except (ValueError, TypeError, KeyError) as error:
                raise HarnessJournalCorruption(
                    "terminal Run has invalid original Provider/Tool evidence"
                ) from error
            if pending_provider or pending_tool:
                raise HarnessJournalCorruption(
                    "normal terminal Run retains unsettled original Provider/Tool effects"
                )
        events = self.connection.execute("SELECT count(*) AS n FROM run_events").fetchone()["n"]
        leases = self.connection.execute("SELECT count(*) AS n FROM run_leases").fetchone()["n"]
        return {
            "schemaVersion": 1,
            "kind": "ordivon.harness-store-doctor",
            "healthy": True,
            "full": full,
            "runs": len(runs),
            "events": events,
            "objects": len(objects),
            "leases": leases,
            "storageBackend": "postgresql",
            "integrityChecks": [
                "canonical-object-sha256",
                "contiguous-run-journal",
                "contract-binding",
                "mandatory-event-reference-graph",
                "single-pg-snapshot",
            ],
            "quickCheck": ["not-applicable-postgresql"],
        }
