"""Legacy Writer admission must not erase extensions it cannot re-encode.

Pure tests intentionally avoid any production or disposable database access.
The real PG18 CAS transaction remains a separate qualification gate.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.work_inputs import WorkSnapshotInput
from ordivon_host_v2.work_store import _require_legacy_work_snapshot_shape


def legacy_payload() -> dict:
    return WorkSnapshotInput(
        objective="versioned Work migration",
        frontier="legacy writer must not erase future state",
        established=["old source still recognized"],
        reference_refs=["job:fake-no-physical-effect-claim"],
    ).canonical_payload()


def test_legacy_snapshot_roundtrips_without_rewriting_canonical_payload() -> None:
    source = legacy_payload()
    preserved = deepcopy(source)
    assert _require_legacy_work_snapshot_shape(source) is None
    assert source == preserved


@pytest.mark.parametrize(
    ("extension", "value"),
    [
        ("engagement", {"schemaVersion": 1, "phase": "offered"}),
        ("futureLifecycle", {"phase": "unknown-but-owner-native"}),
        ("schemaVersion", 2),
        ("newEvidence", ["artifact:new:unknown"]),
    ],
)
def test_new_owner_extensions_cannot_be_erased_by_legacy_cas(
    extension: str,
    value: object,
) -> None:
    source = legacy_payload()
    source[extension] = value
    with pytest.raises(ConflictError, match="not writable"):
        _require_legacy_work_snapshot_shape(source)


def test_old_dto_alias_cannot_silently_reencode_durable_payload() -> None:
    source = legacy_payload()
    source["next_actions"] = source.pop("nextActions")
    with pytest.raises(ConflictError, match="cannot roundtrip"):
        _require_legacy_work_snapshot_shape(source)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("objective", None),
        ("frontier", ""),
        ("established", ["  untrimmed  "]),
        ("constraints", [""] * 129),
    ],
)
def test_bad_or_unknown_current_work_shape_fails_closed(field: str, value: object) -> None:
    source = legacy_payload()
    source[field] = value
    with pytest.raises(ConflictError, match="not writable"):
        _require_legacy_work_snapshot_shape(source)


def test_missing_required_current_snapshot_field_fails_closed() -> None:
    source = legacy_payload()
    source.pop("objective")
    with pytest.raises(ConflictError, match="not writable"):
        _require_legacy_work_snapshot_shape(source)


def test_legacy_cas_guards_current_authority_before_any_write(monkeypatch) -> None:
    """A real WorkStore command attempts no UPDATE when old codec loses state.

    Fake the SQL adapter only: the production commit_snapshot control flow
    and its receipt-before-lock/check ordering remain exercised directly.
    The PostgreSQL transaction/row-lock proof requires the separate PG18 gate.
    """
    from contextlib import nullcontext

    from ordivon_host_v2 import work_store
    from ordivon_host_v2.work_store import WorkStore

    class Cursor:
        def __init__(self, result):
            self.result = result

        def fetchone(self):
            return self.result

    class Connection:
        def __init__(self, payload):
            self.payload = payload
            self.statements = []

        def __enter__(self):
            return self

        def __exit__(self, kind, value, traceback):
            return False

        def transaction(self):
            return nullcontext()

        def execute(self, statement, parameters=()):
            self.statements.append(statement)
            if statement.startswith("SELECT 1 FROM actor_refs"):
                return Cursor({"1": 1})
            if "FROM works WHERE work_ref=%s FOR UPDATE" in statement:
                return Cursor({"current_revision": 2, "state": "open"})
            if "SELECT payload FROM work_snapshots" in statement:
                return Cursor({"payload": self.payload})
            raise AssertionError(f"legacy CAS performed an unverified effect: {statement}")

    unknown = legacy_payload()
    unknown["engagement"] = {"schemaVersion": 1, "phase": "offered"}
    conn = Connection(unknown)
    store = WorkStore("postgresql://unused.invalid/host")
    monkeypatch.setattr(store, "_connect", lambda: conn)
    monkeypatch.setattr(work_store, "claim_command_receipt", lambda *args, **kwargs: None)
    with pytest.raises(ConflictError, match="not writable"):
        store.commit_snapshot(
            "work:test:legacy-forward-compat",
            expected_revision=2,
            snapshot=WorkSnapshotInput(objective="old writer", frontier="cannot erase claim"),
            actor_ref="actor:test:legacy-writer",
            client_request_id="request:test:legacy-writer-downgrade",
        )
    assert len(conn.statements) == 3, conn.statements
    assert "FOR UPDATE" in conn.statements[1]
    assert "SELECT payload FROM work_snapshots" in conn.statements[2]
    assert not any(
        sql.lstrip().startswith(("UPDATE ", "INSERT ", "DELETE ")) for sql in conn.statements
    )


def test_existing_receipt_replay_precedes_upgrade_rejection(monkeypatch) -> None:
    """Response-loss recovery remains immutable after a newer Work upgrade."""
    from contextlib import nullcontext

    from ordivon_host_v2 import work_store
    from ordivon_host_v2.work_store import WorkStore

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, kind, value, traceback):
            return False

        def transaction(self):
            return nullcontext()

        def execute(self, statement, parameters=()):
            raise AssertionError(f"existing receipt must short-circuit SQL: {statement}")

    store = WorkStore("postgresql://unused.invalid/host")
    monkeypatch.setattr(store, "_connect", Connection)
    original = {"kind": "ordivon.host-work", "admission": "existing", "revision": 2}
    monkeypatch.setattr(
        work_store,
        "claim_command_receipt",
        lambda *args, **kwargs: original,
    )
    replay = store.commit_snapshot(
        "work:test:legacy-forward-compat",
        expected_revision=1,
        snapshot=WorkSnapshotInput(objective="old writer", frontier="replayed receipt"),
        actor_ref="actor:test:legacy-writer",
        client_request_id="request:test:legacy-writer-replay",
    )
    assert replay is original
