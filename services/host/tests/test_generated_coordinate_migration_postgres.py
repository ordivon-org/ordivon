"""Migration rejection must preserve the original schema, rows and allocator.

The three explicitly dedicated databases are seeded beyond the wire domain;
never run these cases against an ordinary or shared Host database.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

MAX_EXACT = (1 << 53) - 1
ROOT = Path(__file__).resolve().parents[1]


def observe(conn):
    return {
        "schema": conn.execute("SELECT schema_version FROM host_v2_schema").fetchone(),
        "alembic": conn.execute("SELECT version_num FROM alembic_version").fetchone(),
        "clock": conn.execute("SELECT value FROM swf_change_clock WHERE singleton").fetchone(),
        "actors": conn.execute(
            "SELECT actor_ref, change_sequence FROM actor_refs ORDER BY actor_ref"
        ).fetchall(),
        "messages": conn.execute("SELECT count(*) FROM messages").fetchone(),
        "receipts": conn.execute("SELECT count(*) FROM command_receipts").fetchone(),
        "sequence_max": conn.execute(
            "SELECT seqmax FROM pg_sequence "
            "WHERE seqrelid=pg_get_serial_sequence('messages','sequence')::regclass"
        ).fetchone(),
        "sequence_state": conn.execute(
            "SELECT last_value,is_called FROM messages_sequence_seq"
        ).fetchone(),
        "constraints": conn.execute(
            "SELECT conrelid::regclass::text,conname,pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE connamespace='public'::regnamespace ORDER BY 1,2"
        ).fetchall(),
    }


@pytest.mark.parametrize(
    ("variant", "error"),
    [
        ("CLOCK", "swf_exact_change_clock"),
        ("HISTORY", "actor_refs_exact_change_sequence"),
        ("ALLOCATOR", "psycopg.errors.InvalidParameterValue"),
    ],
)
def test_schema15_rejects_unrepresentable_legacy_state_atomically(variant, error):
    dsn = os.environ.get(f"ORDIVON_HOST_V2_MIGRATION_{variant}_DSN")
    if not dsn:
        pytest.skip("requires an explicitly dedicated empty schema-14 migration database")
    with psycopg.connect(dsn) as conn:
        clean = observe(conn)
        assert clean["schema"] == (14,)
        assert clean["alembic"] == ("0014",)
        assert clean["clock"] == (0,)
        assert clean["actors"] == []
        assert clean["messages"] == clean["receipts"] == (0,)
        assert clean["sequence_state"] == (1, False)
        assert clean["sequence_max"] == ((1 << 63) - 1,)
        if variant == "CLOCK":
            conn.execute("UPDATE swf_change_clock SET value=%s WHERE singleton", (MAX_EXACT + 1,))
        elif variant == "HISTORY":
            conn.execute("UPDATE swf_change_clock SET value=%s WHERE singleton", (MAX_EXACT,))
            conn.execute(
                "INSERT INTO actor_refs(actor_ref,actor_kind) "
                "VALUES ('actor:agent:bad-history','agent')"
            )
            # Isolate the historical row from a simultaneously invalid clock.
            conn.execute("UPDATE swf_change_clock SET value=%s WHERE singleton", (MAX_EXACT,))
        else:
            conn.execute(
                "SELECT setval(pg_get_serial_sequence('messages','sequence'),%s,true)",
                (MAX_EXACT + 1,),
            )
        before = observe(conn)
    if variant == "HISTORY":
        assert before["actors"] == [("actor:agent:bad-history", MAX_EXACT + 1)]
    env = {**os.environ, "ORDIVON_HOST_V2_DSN": dsn}
    env.pop("ORDIVON_HOST_V2_SQLALCHEMY_URL", None)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "0015"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode != 0
    assert error in result.stderr, result.stderr
    with psycopg.connect(dsn) as conn:
        assert observe(conn) == before, "migration partially committed or repaired legacy state"


def test_schema15_lock_timeout_rolls_back_then_normal_retry_succeeds():
    dsn = os.environ.get("ORDIVON_HOST_V2_MIGRATION_LOCK_DSN")
    if not dsn:
        pytest.skip("requires an explicitly dedicated empty schema-14 migration database")
    with psycopg.connect(dsn) as conn:
        before = observe(conn)
        assert before["schema"] == (14,)
        assert before["alembic"] == ("0014",)
        assert before["clock"] == (0,)
        assert before["actors"] == []
        assert before["messages"] == before["receipts"] == (0,)
        assert before["sequence_state"] == (1, False)
    # End the observation transaction first: its ACCESS SHARE locks on
    # messages and the sequence would otherwise block the *first* DDL step.
    with psycopg.connect(dsn) as conn:
        # The late DDL step must wait on a real reader. Earlier DDL in the
        # migration has already run and must be rolled back with the timeout.
        conn.execute("LOCK TABLE subscriptions IN ACCESS SHARE MODE")
        env = {
            **os.environ,
            "ORDIVON_HOST_V2_DSN": dsn,
            "PGOPTIONS": "-c lock_timeout=500ms -c statement_timeout=10000ms",
        }
        env.pop("ORDIVON_HOST_V2_SQLALCHEMY_URL", None)
        blocked = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "0015"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert blocked.returncode != 0
        assert "psycopg.errors.LockNotAvailable" in blocked.stderr, blocked.stderr
        assert "subscriptions" in blocked.stderr
    with psycopg.connect(dsn) as conn:
        assert observe(conn) == before
    # Once the blocker releases naturally, retry the same native migration.
    retry = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "0015"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert retry.returncode == 0, retry.stderr
    with psycopg.connect(dsn) as conn:
        after = observe(conn)
    assert after["schema"] == (15,) and after["alembic"] == ("0015",)
    for key in ("clock", "actors", "messages", "receipts", "sequence_state"):
        assert after[key] == before[key]
    assert after["sequence_max"] == (MAX_EXACT,)
