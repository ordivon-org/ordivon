"""PostgreSQL-only Harness Journal/CAS persistence, independent of Host truth.

This implements the existing HarnessStore port without dual writes or a new
registry.  A single PostgreSQL transaction admits a contiguous event batch,
its Run projection, and consumes the exact lease.  Content-addressed objects
are immutable BYTEA: no filesystem CAS or SQLite compatibility is involved.

This owner-local Store does not grant Runtime effects or domain completion.
"""

from __future__ import annotations

from types import TracebackType

from anc_canonical import JsonValue, canonical_digest
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .core_contracts import HarnessRunContract
from .pg_store_schema import (
    _SCHEMA, _SCHEMA_NAME, _ISSUER_ADMISSION_FUNCTION,
    configured_postgres as configured_postgres,
)
from .pg_store_codec import (
    _EVENT_PAYLOAD_KIND, _CONTRACT_OBJECT_KIND, _MAX_EVENT_BATCH,
    event_payload, run_projection,
)
from .pg_store_objects import PostgresObjects
from .pg_store_queries import PostgresQueries
from .pg_store_leases import PostgresLeases
from .pg_store_integrity import PostgresIntegrity, invalid_typed_effect_reference_fields
from .store_errors import (
    HarnessEventConflict,
    HarnessJournalCorruption,
    HarnessLeaseConflict,
    HarnessRevisionConflict,
    HarnessTerminalConflict,
)
from .store import (
    HARNESS_STORE_EVENT_KINDS,
    HarnessEventAdmission,
    HarnessEventWrite,
    HarnessRunEventRecord,
    HarnessRunLease,
    HarnessRunStatus,
    StoredHarnessObject,
    harness_run_status_after_event,
    validate_harness_event_identity,
)


class PostgresHarnessStore(PostgresObjects, PostgresQueries, PostgresLeases, PostgresIntegrity):
    """PG-backed implementation of the established HarnessStore behavioral port.

    `initialize=True` creates only the explicitly named Harness schema; false
    requires an already-initialized schema.  Production operators must provide
    an explicit DSN/role and schema. Never creates a database or drops data.
    """

    def __init__(self, dsn: str, *, schema: str = "harness", initialize: bool = False):
        if not _SCHEMA_NAME.fullmatch(schema):
            raise ValueError("Harness PostgreSQL schema name must be a plain identifier")
        self.schema = schema
        self.connection = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
        try:
            if initialize:
                self.connection.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
                )
            self.connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            if initialize:
                # psycopg executes this multi-command schema seed only from a
                # constant, and the caller controls the owning SQL role.
                with self.connection.transaction():
                    self.connection.execute(_SCHEMA)
                    self.connection.execute(
                        sql.SQL(_ISSUER_ADMISSION_FUNCTION).format(
                            schema=sql.Identifier(schema)
                        )
                    )
            row = self.connection.execute(
                "SELECT value FROM schema_info WHERE key='schema_version'"
            ).fetchone()
            if row is None or row["value"] != "1":
                raise HarnessJournalCorruption("unsupported Harness PostgreSQL schema version")
        except BaseException:
            self.connection.close()
            raise

    def __enter__(self) -> PostgresHarnessStore:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()


    def create_run(self, contract: HarnessRunContract) -> HarnessEventAdmission:
        event_id = (
            "event:harness-run-created:"
            + canonical_digest(
                {"harnessRunId": contract.harness_run_id, "contractDigest": contract.digest}
            )[7:]
        )
        with self.connection.transaction():
            contract_object = self._object(
                contract.to_dict(), _CONTRACT_OBJECT_KIND, now_ms=contract.created_at_ms
            )
            data: dict[str, JsonValue] = {
                "contractDigest": contract.digest,
                "contractObjectDigest": contract_object.digest,
                "callerId": contract.caller_id,
                "callerRunRef": contract.caller_run_ref,
            }
            payload = self._object(
                event_payload("harness.run-created", data),
                _EVENT_PAYLOAD_KIND,
                now_ms=contract.created_at_ms,
            )
            row = self.connection.execute(
                "SELECT * FROM runs WHERE harness_run_id=%s FOR UPDATE", (contract.harness_run_id,)
            ).fetchone()
            if row is not None:
                projection = run_projection(contract.harness_run_id, row)
                if (
                    projection.contract_digest,
                    projection.contract_object_digest,
                    projection.caller_id,
                    projection.caller_run_ref,
                    projection.status,
                    projection.revision,
                ) != (
                    contract.digest,
                    contract_object.digest,
                    contract.caller_id,
                    contract.caller_run_ref,
                    HarnessRunStatus.CREATED,
                    1,
                ):
                    raise HarnessEventConflict("Harness Run identity already bound differently")
                self._exact_event(
                    event_id,
                    contract.harness_run_id,
                    1,
                    "harness.run-created",
                    payload,
                    None,
                    contract.created_at_ms,
                    (contract_object,),
                )
                return HarnessEventAdmission.EXISTING
            try:
                with self.connection.transaction():
                    self.connection.execute(
                        "INSERT INTO runs(harness_run_id,contract_digest,contract_object_digest,caller_id,"
                        "caller_run_ref,status,revision,created_at_ms,updated_at_ms) "
                        "VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s)",
                        (
                            contract.harness_run_id,
                            contract.digest,
                            contract_object.digest,
                            contract.caller_id,
                            contract.caller_run_ref,
                            HarnessRunStatus.CREATED.value,
                            contract.created_at_ms,
                            contract.created_at_ms,
                        ),
                    )
            except psycopg.errors.UniqueViolation as error:
                raise HarnessEventConflict("Harness Run/caller identity already bound") from error
            self._insert_event(
                contract.harness_run_id,
                event_id,
                1,
                "harness.run-created",
                payload,
                None,
                contract.created_at_ms,
                (contract_object,),
            )
        return HarnessEventAdmission.CREATED

    def append_event(
        self,
        *,
        event_id: str,
        harness_run_id: str,
        event_kind: str,
        data: dict[str, JsonValue],
        expected_revision: int,
        recorded_at_ms: int,
        lease: HarnessRunLease,
        lease_checked_at_ms: int,
        caused_by_event_id: str | None = None,
        referenced_objects: tuple[StoredHarnessObject, ...] = (),
    ) -> HarnessEventAdmission:
        return self.append_events(
            harness_run_id=harness_run_id,
            events=(
                HarnessEventWrite(
                    event_id=event_id,
                    event_kind=event_kind,
                    data=data,
                    recorded_at_ms=recorded_at_ms,
                    caused_by_event_id=caused_by_event_id,
                    referenced_objects=referenced_objects,
                ),
            ),
            expected_revision=expected_revision,
            lease=lease,
            lease_checked_at_ms=lease_checked_at_ms,
        )

    def append_events(
        self,
        *,
        harness_run_id: str,
        events: tuple[HarnessEventWrite, ...],
        expected_revision: int,
        lease: HarnessRunLease,
        lease_checked_at_ms: int,
    ) -> HarnessEventAdmission:
        if not events or len(events) > _MAX_EVENT_BATCH:
            raise ValueError("Harness event batch must be 1..256 events")
        if expected_revision < 1 or lease_checked_at_ms < 0:
            raise ValueError("Harness expected revision/time invalid")
        ids = [e.event_id for e in events]
        if len(set(ids)) != len(ids):
            raise ValueError("Harness batch has duplicate event identities")
        with self.connection.transaction():
            prepared: list[tuple[HarnessEventWrite, StoredHarnessObject]] = []
            for e in events:
                validate_harness_event_identity(e.event_id)
                if (
                    e.event_kind not in HARNESS_STORE_EVENT_KINDS
                    or e.event_kind == "harness.run-created"
                ):
                    raise ValueError("unsupported Harness store event kind")
                if e.recorded_at_ms < 0:
                    raise ValueError("negative Harness event time")
                payload = self._object(
                    event_payload(e.event_kind, e.data),
                    _EVENT_PAYLOAD_KIND,
                    now_ms=e.recorded_at_ms,
                )
                for ref in e.referenced_objects:
                    self._require_object(ref)
                prepared.append((e, payload))
            # Row lock serializes all writers, including lease acquisition.
            row = self.connection.execute(
                "SELECT * FROM runs WHERE harness_run_id=%s FOR UPDATE", (harness_run_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Harness Run does not exist: {harness_run_id}")
            existing = {
                r["event_id"]
                for r in self.connection.execute(
                    "SELECT event_id FROM run_events WHERE event_id=ANY(%s::text[])", (ids,)
                )
            }
            if existing:
                if existing != set(ids):
                    raise HarnessEventConflict("Harness Event batch partially admitted")
                for offset, (e, payload) in enumerate(prepared, 1):
                    self._exact_event(
                        e.event_id,
                        harness_run_id,
                        expected_revision + offset,
                        e.event_kind,
                        payload,
                        e.caused_by_event_id,
                        e.recorded_at_ms,
                        e.referenced_objects,
                    )
                return HarnessEventAdmission.EXISTING
            current = run_projection(harness_run_id, row)
            if current.revision != expected_revision:
                raise HarnessRevisionConflict("Harness Run revision changed")
            if current.status.terminal:
                raise HarnessTerminalConflict("terminal Harness Run cannot accept event")
            self._require_lease(lease, lease_checked_at_ms)
            if lease.harness_run_id != harness_run_id or lease.run_revision != expected_revision:
                raise HarnessLeaseConflict("Harness Run lease is bound to different revision")
            status = current.status
            when = current.updated_at_ms
            terminal_id = None
            preceding: set[str] = set()
            for idx, (e, _) in enumerate(prepared):
                invalid = invalid_typed_effect_reference_fields(
                    e.event_kind, e.data, {ref.digest: ref.kind for ref in e.referenced_objects}
                )
                if invalid:
                    raise HarnessEventConflict(
                        "New typed effect Event has missing or mismatched object references: " + ", ".join(invalid)
                    )
                if status.terminal:
                    raise HarnessTerminalConflict("terminal Event followed by another Event")
                if e.recorded_at_ms < when:
                    raise ValueError("Harness Event time regressed")
                if e.caused_by_event_id is not None and e.caused_by_event_id not in preceding:
                    cause = self.connection.execute(
                        "SELECT harness_run_id FROM run_events WHERE event_id=%s",
                        (e.caused_by_event_id,),
                    ).fetchone()
                    if cause is None or cause["harness_run_id"] != harness_run_id:
                        raise HarnessEventConflict(
                            "Harness caused-by identity is absent or from another Run"
                        )
                status = harness_run_status_after_event(e.event_kind, status)
                if status.terminal:
                    terminal_id = e.event_id
                    if idx != len(prepared) - 1:
                        raise HarnessTerminalConflict("terminal Event must be last")
                when = e.recorded_at_ms
                preceding.add(e.event_id)
            unknown_quarantine = False
            if (
                terminal_id is not None
                and status is HarnessRunStatus.STOPPED
                and prepared[-1][0].event_kind == "harness.run-stopped"
                and prepared[-1][0].data.get("stopCode") in {
                    "provider_state_unknown",
                    "runtime_unknown",
                    "cancel_unknown",
                }
            ):
                # Allow a genuine original Run Recorder UNKNOWN terminal as
                # immutable QUARANTINED_HELD audit evidence; NOT a safe
                # physical-effect release. A raw stopCode alone cannot
                # bypass the qualified normal terminal guard.
                fault = prepared[-1][0]
                self._require_original_unknown_stop_receipt(
                    harness_run_id=harness_run_id,
                    contract_digest=current.contract_digest,
                    data=fault.data,
                    referenced_receipt_digests={
                        ref.digest
                        for ref in fault.referenced_objects
                        if ref.kind == "independent-harness-run-receipt"
                    },
                )
                unknown_quarantine = True
            if terminal_id is not None and not unknown_quarantine:
                # All normal and non-UNKNOWN terminal admissions require
                # zero outstanding effects under this same Run row lock.
                # The Run row is still SELECT FOR UPDATE and the original
                # Lease/Revision CAS has already passed. No other Writer can
                # commit a Provider/Tool transition between this scan and the
                # terminal update. Inspect the entire *prospective* Journal,
                # including any earlier effects settled in this very batch.
                original_events = self.list_run_events(harness_run_id)
                # The same original Store validates exactly the read used
                # for terminal admission. The Run row is already locked;
                # an omitted pending Intent or detached persisted edge
                # cannot turn incomplete evidence into "no effects".
                original_contract = self._validate_original_run_history(current, original_events)
                proposed_events = tuple(
                    HarnessRunEventRecord(
                        sequence=-(offset),
                        event_id=e.event_id,
                        harness_run_id=harness_run_id,
                        run_revision=expected_revision + offset,
                        event_kind=e.event_kind,
                        payload_digest=payload.digest,
                        data=e.data,
                        caused_by_event_id=e.caused_by_event_id,
                        recorded_at_ms=e.recorded_at_ms,
                    )
                    for offset, (e, payload) in enumerate(prepared, 1)
                )
                prospective = original_events + proposed_events
                if any(
                    event.event_kind.startswith(("harness.provider-call-", "harness.tool-step-"))
                    for event in prospective
                ):
                    # Use the existing verified immutable-CAS continuity
                    # scanner, rather than a parallel Pending table, ledger,
                    # registry, or a check in a separate transaction.
                    from .ordivon.provider_record_reader import inspect_original_effect_sources

                    provider_ids, tool_digests = inspect_original_effect_sources(
                        self, original_contract, prospective
                    )
                    if provider_ids or tool_digests:
                        raise HarnessTerminalConflict(
                            "terminal Run cannot close over unresolved original "
                            "Provider/Tool effects; exact Owner reconciliation "
                            "is required before finalization"
                        )
            final_revision = expected_revision + len(prepared)
            changed = self.connection.execute(
                "UPDATE runs SET status=%s,revision=%s,updated_at_ms=%s,terminal_event_id=%s "
                "WHERE harness_run_id=%s AND revision=%s",
                (
                    status.value,
                    final_revision,
                    when,
                    terminal_id,
                    harness_run_id,
                    expected_revision,
                ),
            ).rowcount
            if changed != 1:
                raise HarnessRevisionConflict("Harness Run revision changed during admission")
            for offset, (e, payload) in enumerate(prepared, 1):
                self._insert_event(
                    harness_run_id,
                    e.event_id,
                    expected_revision + offset,
                    e.event_kind,
                    payload,
                    e.caused_by_event_id,
                    e.recorded_at_ms,
                    e.referenced_objects,
                )
            self._consume_lease(lease)
        return HarnessEventAdmission.CREATED

    def _insert_event(
        self,
        run_id: str,
        event_id: str,
        revision: int,
        kind: str,
        payload: StoredHarnessObject,
        cause: str | None,
        at: int,
        referenced: tuple[StoredHarnessObject, ...],
    ) -> None:
        self.connection.execute(
            "INSERT INTO run_events(event_id,harness_run_id,run_revision,event_kind,"
            "payload_digest,caused_by_event_id,recorded_at_ms) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (event_id, run_id, revision, kind, payload.digest, cause, at),
        )
        edges = {(payload.digest, "payload")}
        edges.update((x.digest, "reference") for x in referenced)
        for digest, role in sorted(edges):
            self.connection.execute(
                "INSERT INTO run_object_refs(harness_run_id,event_id,digest,role) "
                "VALUES(%s,%s,%s,%s)",
                (run_id, event_id, digest, role),
            )

    def _exact_event(
        self,
        event_id: str,
        run_id: str,
        revision: int,
        kind: str,
        payload: StoredHarnessObject,
        cause: str | None,
        at: int,
        referenced: tuple[StoredHarnessObject, ...],
    ) -> None:
        row = self.connection.execute(
            "SELECT * FROM run_events WHERE event_id=%s", (event_id,)
        ).fetchone()
        if row is None or (
            row["harness_run_id"],
            row["run_revision"],
            row["event_kind"],
            row["payload_digest"],
            row["caused_by_event_id"],
            row["recorded_at_ms"],
        ) != (run_id, revision, kind, payload.digest, cause, at):
            raise HarnessEventConflict("Harness Event identity differs from committed content")
        expected = {(payload.digest, "payload")}
        expected.update((x.digest, "reference") for x in referenced)
        actual = {
            (r["digest"], r["role"])
            for r in self.connection.execute(
                "SELECT digest,role FROM run_object_refs WHERE event_id=%s", (event_id,)
            )
        }
        if expected != actual:
            raise HarnessEventConflict("Harness Event references differ from committed content")
