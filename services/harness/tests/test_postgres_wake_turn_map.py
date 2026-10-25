"""PostgreSQL 18 physical cutover contract; run with disposable PG test DSN."""
from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg", reason="PG provider is owned by the Temporal worker")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from postgres_wake_turn_map import PostgresWakeTurnMap, WakeTurnConflict  # noqa: E402

PG_TEST_DSN = os.environ.get("ORDIVON_PG_WAKE_TEST_DSN")
pytestmark = pytest.mark.skipif(not PG_TEST_DSN, reason="disposable PostgreSQL database not provisioned")


@pytest.fixture
def owner():
    assert PG_TEST_DSN is not None
    w = PostgresWakeTurnMap(PG_TEST_DSN)
    with psycopg.connect(PG_TEST_DSN) as db:
        db.execute("DROP TRIGGER IF EXISTS corrupt_wake_insert ON ordivon_harness.wake_turn_map")
        db.execute("DROP FUNCTION IF EXISTS ordivon_harness.corrupt_wake_insert()")
        db.execute("TRUNCATE TABLE ordivon_harness.wake_turn_map")
    return w


def test_first_schema_admission_is_serialized_on_disposable_pg() -> None:
    """Actual PostgreSQL first-admission race: CREATE SCHEMA IF NOT EXISTS alone races."""
    dsn = os.environ.get("ORDIVON_PG_WAKE_BOOTSTRAP_TEST_DSN")
    if not dsn:
        pytest.skip("dedicated PostgreSQL bootstrap-test database not provisioned")
    from threading import Barrier

    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute("DROP SCHEMA IF EXISTS ordivon_harness CASCADE")
    started = Barrier(12)

    def bootstrap(_index: int) -> None:
        started.wait(timeout=15)
        PostgresWakeTurnMap(dsn)

    # Twelve independent connections racing fresh schema admission must all succeed.
    with ThreadPoolExecutor(max_workers=12) as executor:
        list(executor.map(bootstrap, range(12)))
    with psycopg.connect(dsn) as db:
        count = db.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='ordivon_harness' AND table_name='wake_turn_map'"
        ).fetchone()[0]
    assert count == 1


def payload(wake: str = "wake:" + "a" * 32) -> dict[str, str]:
    return {
        "campaign_ref": "sha256:" + "a" * 64,
        "agent_id": "A01",
        "wake_intent_id": wake,
        "prompt_digest": "sha256:" + "b" * 64,
    }


def test_exact_replay_preserves_identity(owner: PostgresWakeTurnMap) -> None:
    first = owner.allocate(**payload())
    second = owner.allocate(**payload())
    assert first["disposition"] == "created"
    assert second["disposition"] == "existing"
    assert second["turnRequestId"] == first["turnRequestId"]
    assert owner.get(payload()["wake_intent_id"]) == second


def test_same_wake_different_semantics_fails_closed(owner: PostgresWakeTurnMap) -> None:
    owner.allocate(**payload())
    with pytest.raises(WakeTurnConflict, match="semantics"):
        owner.allocate(**{**payload(), "agent_id": "A02"})


def test_concurrent_same_wake_has_one_identity(owner: PostgresWakeTurnMap) -> None:
    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(lambda _: owner.allocate(**payload()), range(24)))
    assert len({r["turnRequestId"] for r in rows}) == 1
    assert sum(r["disposition"] == "created" for r in rows) == 1
    with psycopg.connect(PG_TEST_DSN) as db:
        assert db.execute("SELECT count(*) FROM ordivon_harness.wake_turn_map").fetchone()[0] == 1


def test_post_write_mutation_is_rolled_back(owner: PostgresWakeTurnMap) -> None:
    with psycopg.connect(PG_TEST_DSN) as db:
        db.execute(
            """CREATE FUNCTION ordivon_harness.corrupt_wake_insert()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                UPDATE ordivon_harness.wake_turn_map
                SET agent_id='FORGED' WHERE wake_intent_id=NEW.wake_intent_id;
                RETURN NEW;
            END $$"""
        )
        db.execute(
            """CREATE TRIGGER corrupt_wake_insert
            AFTER INSERT ON ordivon_harness.wake_turn_map
            FOR EACH ROW EXECUTE FUNCTION ordivon_harness.corrupt_wake_insert()"""
        )
    with pytest.raises(WakeTurnConflict, match="semantics"):
        owner.allocate(**payload())
    with psycopg.connect(PG_TEST_DSN) as db:
        assert db.execute("SELECT count(*) FROM ordivon_harness.wake_turn_map").fetchone()[0] == 0


def test_invalid_uuid7_on_durable_replay_fails_closed(owner: PostgresWakeTurnMap) -> None:
    row = owner.allocate(**payload())
    with psycopg.connect(PG_TEST_DSN) as db:
        db.execute(
            "UPDATE ordivon_harness.wake_turn_map "
            "SET turn_request_id='FORGED' WHERE wake_intent_id=%s",
            (row["wakeIntentId"],),
        )
    with pytest.raises(WakeTurnConflict, match="receipt"):
        owner.allocate(**payload())
    with pytest.raises(WakeTurnConflict, match="identity"):
        owner.get(row["wakeIntentId"])


def test_legacy_sqlite_import_retirement_and_pg_growth(owner: PostgresWakeTurnMap, tmp_path: Path) -> None:
    import sqlite3

    from sqlite_wake_turn_map import SQLiteWakeTurnMap

    source = tmp_path / "turn?origin.sqlite"
    legacy = SQLiteWakeTurnMap(source, now_ms=lambda: 1800000000000)
    a = legacy.allocate(**payload())
    b = legacy.allocate(**payload("wake:" + "c" * 32))
    witness = owner.retire_legacy_and_import(source)
    assert witness["migrationStanding"] == "source-sealed"
    assert witness["sourceRows"] == 2 == witness["postgresRows"]
    assert witness["identityDigest"].startswith("sha256:")
    assert owner.get(a["wakeIntentId"])["turnRequestId"] == a["turnRequestId"]
    assert owner.get(b["wakeIntentId"])["turnRequestId"] == b["turnRequestId"]
    owner.assert_legacy_sealed(source)

    # Old processes can still *read* their old identity, but a new old-source
    # writer cannot create a distinct identity after cutover.
    with pytest.raises(sqlite3.IntegrityError, match="retired"):
        legacy.allocate(**payload("wake:" + "e" * 32))
    new = owner.allocate(**payload("wake:" + "f" * 32))
    assert new["disposition"] == "created"
    owner.assert_legacy_sealed(source)  # PG-only rows are permitted after cutover.


def test_divergent_pg_import_does_not_retire_source(owner: PostgresWakeTurnMap, tmp_path: Path) -> None:
    from sqlite_wake_turn_map import SQLiteWakeTurnMap

    source = tmp_path / "legacy.sqlite"
    legacy = SQLiteWakeTurnMap(source)
    legacy.allocate(**payload())
    owner.allocate(**{**payload(), "agent_id": "A02"})
    with pytest.raises(WakeTurnConflict, match="divergent"):
        owner.retire_legacy_and_import(source)
    with pytest.raises(WakeTurnConflict, match="fence"):
        owner.assert_legacy_sealed(source)
    still_active = legacy.allocate(**payload("wake:" + "d" * 32))
    assert still_active["disposition"] == "created"


def test_tampering_pg_after_cutover_fails_consumer_readback(
    owner: PostgresWakeTurnMap, tmp_path: Path
) -> None:
    from sqlite_wake_turn_map import SQLiteWakeTurnMap

    source = tmp_path / "wake.sqlite"
    legacy = SQLiteWakeTurnMap(source)
    old = legacy.allocate(**payload())
    owner.retire_legacy_and_import(source)
    with psycopg.connect(PG_TEST_DSN) as db:
        db.execute(
            "UPDATE ordivon_harness.wake_turn_map SET agent_id='FORGED' "
            "WHERE wake_intent_id=%s", (old["wakeIntentId"],)
        )
    with pytest.raises(WakeTurnConflict, match="differs"):
        owner.assert_legacy_sealed(source)


def test_same_name_forged_retirement_trigger_is_rejected(
    owner: PostgresWakeTurnMap, tmp_path: Path
) -> None:
    import sqlite3

    from sqlite_wake_turn_map import SQLiteWakeTurnMap

    source = tmp_path / "legacy.sqlite"
    legacy = SQLiteWakeTurnMap(source)
    legacy.allocate(**payload())
    owner.retire_legacy_and_import(source)
    with sqlite3.connect(source) as db:
        db.execute("DROP TRIGGER wake_turn_pg_retired_insert")
        db.execute(
            "CREATE TRIGGER wake_turn_pg_retired_insert BEFORE INSERT "
            "ON wake_turn_map BEGIN SELECT 1; END"
        )
        db.commit()
    with pytest.raises(WakeTurnConflict, match="altered"):
        owner.assert_legacy_sealed(source)
    with pytest.raises(WakeTurnConflict, match="drifted"):
        owner.retire_legacy_and_import(source)


def test_missing_legacy_source_requires_explicit_fresh_bootstrap(
    owner: PostgresWakeTurnMap, tmp_path: Path
) -> None:
    source = tmp_path / "not-there.sqlite"
    with pytest.raises(WakeTurnConflict, match="not qualified"):
        owner.assert_legacy_sealed(source)
    owner.assert_legacy_sealed(source, fresh_bootstrap=True)


def test_pg_turn_request_collision_cannot_alias_different_wakes(
    owner: PostgresWakeTurnMap,
) -> None:
    # A broken ID generator must fail rather than silently rebind another
    # wake intent to the same eventual Provider effect identity.
    fixed = "019a9af0-7b00-7000-8000-000000000011"
    assert PG_TEST_DSN is not None
    bad_generator = PostgresWakeTurnMap(PG_TEST_DSN, uuid7_factory=lambda: fixed)
    first = bad_generator.allocate(**payload())
    assert first["turnRequestId"] == fixed
    with pytest.raises(WakeTurnConflict, match="collision"):
        bad_generator.allocate(**payload("wake:" + "f" * 32))
    with psycopg.connect(PG_TEST_DSN) as db:
        assert db.execute("SELECT count(*) FROM ordivon_harness.wake_turn_map").fetchone()[0] == 1


@pytest.mark.parametrize("unsafe_clock", [True, 1.5, -1, 2**63, "1"])
def test_pg_wake_clock_requires_exact_native_bigint_before_write(
    owner: PostgresWakeTurnMap, unsafe_clock: object,
) -> None:
    """Never let an invalid producer clock get coerced or delegated to PG."""
    assert PG_TEST_DSN is not None
    candidate = PostgresWakeTurnMap(
        PG_TEST_DSN,
        now_ms=lambda: unsafe_clock,  # type: ignore[arg-type,return-value]
    )
    with pytest.raises(WakeTurnConflict, match="timestamp"):
        candidate.allocate(**payload())
    with psycopg.connect(PG_TEST_DSN) as db:
        assert db.execute(
            "SELECT count(*) FROM ordivon_harness.wake_turn_map"
        ).fetchone()[0] == 0
