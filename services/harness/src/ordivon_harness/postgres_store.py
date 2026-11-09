"""PostgreSQL-only Harness Journal/CAS persistence, independent of Host truth.

This implements the existing HarnessStore port without dual writes or a new
registry.  A single PostgreSQL transaction admits a contiguous event batch,
its Run projection, and consumes the exact lease.  Content-addressed objects
are immutable BYTEA: no filesystem CAS or SQLite compatibility is involved.

This owner-local Store does not grant Runtime effects or domain completion.
"""

from __future__ import annotations

import re
import os
from types import TracebackType

from anc_canonical import JsonValue, canonical_bytes, canonical_digest, loads_strict
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .core_contracts import HarnessRunContract
from .store_errors import (
    HarnessEventConflict,
    HarnessJournalCorruption,
    HarnessLeaseConflict,
    HarnessLeaseHeld,
    HarnessObjectCorrupt,
    HarnessObjectMissing,
    HarnessRevisionConflict,
    HarnessTerminalConflict,
)
from .store import (
    HARNESS_STORE_EVENT_KINDS,
    HarnessEventAdmission,
    HarnessEventWrite,
    HarnessRunEventRecord,
    HarnessRunLease,
    HarnessRunProjection,
    HarnessRunStatus,
    StoredHarnessObject,
    harness_run_status_after_event,
    validate_harness_event_identity,
)

from .postgres_schema import HARNESS_POSTGRES_SCHEMA_SQL as _SCHEMA
_EVENT_PAYLOAD_KIND = "ordivon.harness-run-event-payload"
_CONTRACT_OBJECT_KIND = "harness-run-contract"
_MAX_EVENT_BATCH = 256
_SCHEMA_NAME = re.compile(r"[a-z][a-z0-9_]{0,62}\Z")


def configured_postgres() -> tuple[str, str]:
    """The owner default is PG-only. No SQLite state-root or import fallback."""
    # Preserve the already-published Harness PG CLI authority while retiring
    # SQLite entirely: the explicit marker is advisory and cannot select SQLite.
    dsn = (os.environ.get("ORDIVON_HARNESS_PG_DSN") or os.environ.get("HARNESS_PG_DSN", "")).strip()
    if not dsn:
        raise RuntimeError(
            "HARNESS_PG_DSN required (or ORDIVON_HARNESS_PG_DSN); SQLite fallback prohibited"
        )
    schema = os.environ.get("ORDIVON_HARNESS_PG_SCHEMA") or os.environ.get(
        "HARNESS_PG_SCHEMA", "harness"
    )
    if not _SCHEMA_NAME.fullmatch(schema):
        raise ValueError("HARNESS_PG_SCHEMA must be one plain SQL identifier")
    return dsn, schema


def _projection(harness_run_id: str, row: dict) -> HarnessRunProjection:
    try:
        return HarnessRunProjection(
            harness_run_id=harness_run_id,
            contract_digest=row["contract_digest"],
            contract_object_digest=row["contract_object_digest"],
            caller_id=row["caller_id"],
            caller_run_ref=row["caller_run_ref"],
            status=HarnessRunStatus(row["status"]),
            revision=int(row["revision"]),
            created_at_ms=int(row["created_at_ms"]),
            updated_at_ms=int(row["updated_at_ms"]),
            terminal_event_id=row["terminal_event_id"],
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HarnessJournalCorruption("Harness PostgreSQL Run projection is invalid") from error


class PostgresHarnessStore:
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

    def _object(self, value: JsonValue, kind: str, *, now_ms: int = 0) -> StoredHarnessObject:
        if not isinstance(kind, str) or not kind or kind != kind.strip():
            raise ValueError("Harness object kind must be non-empty and trimmed")
        raw = canonical_bytes(value)
        digest = canonical_digest(value)
        metadata = StoredHarnessObject(digest, len(raw), kind)
        self.connection.execute(
            "INSERT INTO objects(digest,kind,byte_length,content,first_seen_at_ms) "
            "VALUES (%s,%s,%s,%s,%s) ON CONFLICT(digest) DO NOTHING",
            (digest, kind, len(raw), raw, now_ms),
        )
        self._require_object(metadata)
        return metadata

    def _require_object(self, item: StoredHarnessObject) -> None:
        actual = self.inspect_object(item.digest)
        if actual != item:
            raise HarnessObjectCorrupt("Harness object metadata differs from committed digest")

    def put_object(self, value: JsonValue, *, kind: str) -> StoredHarnessObject:
        return self._object(value, kind)

    def get_object(self, digest: str, *, expected_kind: str | None = None) -> JsonValue:
        row = self.connection.execute(
            "SELECT kind,byte_length,content FROM objects WHERE digest=%s", (digest,)
        ).fetchone()
        if row is None:
            raise HarnessObjectMissing(f"Harness PostgreSQL object missing: {digest}")
        if expected_kind is not None and row["kind"] != expected_kind:
            raise HarnessObjectCorrupt("Harness PostgreSQL object kind differs")
        raw = bytes(row["content"])
        try:
            value = loads_strict(raw)
        except ValueError as error:
            raise HarnessObjectCorrupt("Harness PostgreSQL object is invalid JSON") from error
        if (
            len(raw) != int(row["byte_length"])
            or canonical_digest(value) != digest
            or canonical_bytes(value) != raw
        ):
            raise HarnessObjectCorrupt("Harness PostgreSQL object hash/size differs")
        return value

    def inspect_object(self, digest: str) -> StoredHarnessObject:
        row = self.connection.execute(
            "SELECT kind,byte_length,content FROM objects WHERE digest=%s", (digest,)
        ).fetchone()
        if row is None:
            raise HarnessObjectMissing(f"Harness PostgreSQL object missing: {digest}")
        raw = bytes(row["content"])
        if len(raw) != int(row["byte_length"]):
            raise HarnessObjectCorrupt("Harness PostgreSQL object size differs")
        try:
            value = loads_strict(raw)
            if canonical_digest(value) != digest or canonical_bytes(value) != raw:
                raise HarnessObjectCorrupt("Harness PostgreSQL object hash differs")
        except ValueError as error:
            raise HarnessObjectCorrupt("Harness PostgreSQL object content invalid") from error
        return StoredHarnessObject(digest, int(row["byte_length"]), row["kind"])

    def _payload(self, event_kind: str, data: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if event_kind not in HARNESS_STORE_EVENT_KINDS:
            raise ValueError("unsupported Harness store event kind")
        return {
            "schemaVersion": 1,
            "kind": _EVENT_PAYLOAD_KIND,
            "eventKind": event_kind,
            "data": data,
        }

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
                self._payload("harness.run-created", data),
                _EVENT_PAYLOAD_KIND,
                now_ms=contract.created_at_ms,
            )
            row = self.connection.execute(
                "SELECT * FROM runs WHERE harness_run_id=%s FOR UPDATE", (contract.harness_run_id,)
            ).fetchone()
            if row is not None:
                projection = _projection(contract.harness_run_id, row)
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

    def load_run(self, harness_run_id: str) -> HarnessRunProjection:
        row = self.connection.execute(
            "SELECT * FROM runs WHERE harness_run_id=%s", (harness_run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"Harness Run does not exist: {harness_run_id}")
        return _projection(harness_run_id, row)

    def list_runs(self) -> tuple[HarnessRunProjection, ...]:
        rows = self.connection.execute(
            "SELECT * FROM runs ORDER BY created_at_ms,harness_run_id"
        ).fetchall()
        return tuple(_projection(row["harness_run_id"], row) for row in rows)

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
                    self._payload(e.event_kind, e.data),
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
            current = _projection(harness_run_id, row)
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

    def list_run_events(
        self, harness_run_id: str, *, after_sequence: int = 0
    ) -> tuple[HarnessRunEventRecord, ...]:
        if after_sequence < 0:
            raise ValueError("negative event cursor")
        self.load_run(harness_run_id)
        rows = self.connection.execute(
            "SELECT * FROM run_events WHERE harness_run_id=%s AND sequence>%s ORDER BY sequence",
            (harness_run_id, after_sequence),
        ).fetchall()
        result = []
        for row in rows:
            payload = self.get_object(row["payload_digest"], expected_kind=_EVENT_PAYLOAD_KIND)
            if (
                not isinstance(payload, dict)
                or set(payload) != {"schemaVersion", "kind", "eventKind", "data"}
                or payload["schemaVersion"] != 1
                or payload["kind"] != _EVENT_PAYLOAD_KIND
                or payload["eventKind"] != row["event_kind"]
                or not isinstance(payload["data"], dict)
            ):
                raise HarnessJournalCorruption("Harness event payload differs from metadata")
            result.append(
                HarnessRunEventRecord(
                    sequence=int(row["sequence"]),
                    event_id=row["event_id"],
                    harness_run_id=row["harness_run_id"],
                    run_revision=int(row["run_revision"]),
                    event_kind=row["event_kind"],
                    payload_digest=row["payload_digest"],
                    data=dict(payload["data"]),
                    caused_by_event_id=row["caused_by_event_id"],
                    recorded_at_ms=int(row["recorded_at_ms"]),
                )
            )
        return tuple(result)

    def acquire_run_lease(
        self,
        harness_run_id: str,
        *,
        owner_id: str,
        ttl_ms: int,
        now_ms: int,
        expected_run_revision: int | None = None,
    ) -> HarnessRunLease:
        if not owner_id or owner_id != owner_id.strip() or ttl_ms < 1 or now_ms < 0:
            raise ValueError("Harness lease identity, TTL or clock is invalid")
        with self.connection.transaction():
            row = self.connection.execute(
                "SELECT * FROM runs WHERE harness_run_id=%s FOR UPDATE", (harness_run_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Harness Run does not exist: {harness_run_id}")
            run = _projection(harness_run_id, row)
            if expected_run_revision is not None and run.revision != expected_run_revision:
                raise HarnessRevisionConflict("Run revision changed before lease admission")
            if run.status.terminal:
                raise HarnessTerminalConflict("terminal Run cannot be leased")
            current = self.connection.execute(
                "SELECT * FROM run_leases WHERE harness_run_id=%s FOR UPDATE", (harness_run_id,)
            ).fetchone()
            revision = 1
            if current is not None:
                if current["expires_at_ms"] > now_ms:
                    if current["owner_id"] == owner_id and current["run_revision"] == run.revision:
                        return HarnessRunLease(
                            harness_run_id,
                            owner_id,
                            int(current["lease_revision"]),
                            run.revision,
                            int(current["expires_at_ms"]),
                        )
                    raise HarnessLeaseHeld("Harness Run leased by other execution")
                revision = int(current["lease_revision"]) + 1
            expires = now_ms + ttl_ms
            self.connection.execute(
                "INSERT INTO run_leases(harness_run_id,owner_id,lease_revision,run_revision,expires_at_ms) "
                "VALUES(%s,%s,%s,%s,%s) ON CONFLICT(harness_run_id) DO UPDATE SET "
                "owner_id=EXCLUDED.owner_id,lease_revision=EXCLUDED.lease_revision,"
                "run_revision=EXCLUDED.run_revision,expires_at_ms=EXCLUDED.expires_at_ms",
                (harness_run_id, owner_id, revision, run.revision, expires),
            )
            return HarnessRunLease(harness_run_id, owner_id, revision, run.revision, expires)

    def release_run_lease(self, lease: HarnessRunLease) -> bool:
        with self.connection.transaction():
            changed = self.connection.execute(
                "DELETE FROM run_leases WHERE harness_run_id=%s AND owner_id=%s "
                "AND lease_revision=%s AND run_revision=%s AND expires_at_ms=%s",
                (
                    lease.harness_run_id,
                    lease.owner_id,
                    lease.lease_revision,
                    lease.run_revision,
                    lease.expires_at_ms,
                ),
            ).rowcount
        return changed == 1

    def _require_lease(self, lease: HarnessRunLease, at: int) -> None:
        row = self.connection.execute(
            "SELECT * FROM run_leases WHERE harness_run_id=%s FOR UPDATE", (lease.harness_run_id,)
        ).fetchone()
        if (
            row is None
            or (row["owner_id"], row["lease_revision"], row["run_revision"], row["expires_at_ms"])
            != (lease.owner_id, lease.lease_revision, lease.run_revision, lease.expires_at_ms)
            or row["expires_at_ms"] <= at
        ):
            raise HarnessLeaseConflict("Harness Run lease expired or superseded")

    def _consume_lease(self, lease: HarnessRunLease) -> None:
        changed = self.connection.execute(
            "DELETE FROM run_leases WHERE harness_run_id=%s AND owner_id=%s "
            "AND lease_revision=%s AND run_revision=%s AND expires_at_ms=%s",
            (
                lease.harness_run_id,
                lease.owner_id,
                lease.lease_revision,
                lease.run_revision,
                lease.expires_at_ms,
            ),
        ).rowcount
        if changed != 1:
            raise HarnessLeaseConflict("Harness Run lease changed during batch")

    def validate_run_history(self, harness_run_id: str) -> None:
        projection = self.load_run(harness_run_id)
        events = self.list_run_events(harness_run_id)
        if not events or events[0].event_kind != "harness.run-created":
            raise HarnessJournalCorruption("Run has no creation Event")
        status = HarnessRunStatus.CREATED
        when = -1
        terminal = None
        for revision, event in enumerate(events, 1):
            if (
                event.run_revision != revision
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

    def doctor(self, *, full: bool = True) -> dict[str, JsonValue]:
        objects = self.connection.execute("SELECT digest FROM objects").fetchall()
        for row in objects:
            self.inspect_object(row["digest"])
        runs = self.list_runs()
        for run in runs:
            self.validate_run_history(run.harness_run_id)
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
            ],
            "quickCheck": ["not-applicable-postgresql"],
        }
