"""Native concurrent-index failure, restart and real message-write qualification.

Only a separately provisioned, empty schema-15 database is eligible. No
catalog edits, mock index readiness, production schema or arbitrary sleeps.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_host_v2.collaboration_inputs import MessageInput, MessageKind, SpaceInput, TopicInput
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

ROOT = Path(__file__).resolve().parents[1]
OLD = "message_unicode_ngrams3_idx"
NEW = "message_cjk_sparse_ngrams3_v1_idx"


def _identity(conn):
    return conn.execute(
        "SELECT current_database(),(SELECT oid FROM pg_database "
        "WHERE datname=current_database()),"
        "(SELECT system_identifier FROM pg_control_system())"
    ).fetchone()


def _standing(conn):
    return (
        conn.execute("SELECT version_num FROM alembic_version").fetchone()[0],
        conn.execute("SELECT schema_version FROM host_v2_schema").fetchone()[0],
        dict(
            (name, (valid, ready))
            for name, valid, ready in conn.execute(
                "SELECT c.relname,i.indisvalid,i.indisready FROM pg_index i "
                "JOIN pg_class c ON c.oid=i.indexrelid WHERE c.relname IN (%s,%s)",
                (OLD, NEW),
            )
        ),
    )


def _migration_env(dsn, *, lock_timeout):
    env = {
        **os.environ,
        "ORDIVON_HOST_V2_DSN": dsn,
        "PGOPTIONS": f"-c lock_timeout={lock_timeout} -c statement_timeout=20000ms",
    }
    env.pop("ORDIVON_HOST_V2_SQLALCHEMY_URL", None)
    return env


def _new_topic(dsn):
    token = uuid4().hex
    actor, space, topic = (
        f"actor:agent:online:{token}",
        f"space:online:{token}",
        f"topic:online:{token}",
    )
    ActorReferenceStore(dsn).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{actor}",
    )
    social = SocialStore(dsn)
    social.create_space(
        SpaceInput(space_ref=space, purpose="migration test", actor_ref=actor),
        client_request_id=f"space:{space}",
    )
    social.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="Online", actor_ref=actor),
        client_request_id=f"topic:{topic}",
    )
    return social, MessageInput(
        message_ref=f"message:online:{token}",
        client_request_id=f"post:online:{token}",
        space_ref=space,
        topic_ref=topic,
        author_actor_ref=actor,
        message_kind=MessageKind.FINDING,
        body="before 中a文b字",
        recorded_at_ms=123,
    )


def test_sparse_index_timeout_retry_and_concurrent_message_write():
    dsn = os.environ.get("ORDIVON_HOST_V2_MIGRATION_CJK_DSN")
    if not dsn:
        pytest.skip("requires separate empty schema-15 CJK migration database")
    # Distinct actual database identity, not just different DSN spelling.
    ordinary = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
    if not ordinary:
        pytest.fail("ordinary test database identity must be supplied")
    with psycopg.connect(ordinary) as conn:
        ordinary_id = _identity(conn)
    with psycopg.connect(dsn) as conn:
        assert _identity(conn) != ordinary_id
        assert _standing(conn) == ("0015", 15, {OLD: (True, True)})
        for table in ("messages", "actor_refs", "command_receipts"):
            # Fixed identifiers only.
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
    social, first = _new_topic(dsn)
    assert social.post_message(first)["admission"] == "committed"
    with psycopg.connect(dsn) as blocker:
        blocker.execute("LOCK TABLE messages IN ROW EXCLUSIVE MODE")
        failed = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "0016"],
            cwd=ROOT,
            env=_migration_env(dsn, lock_timeout="500ms"),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert failed.returncode != 0
        assert "LockNotAvailable" in failed.stderr, failed.stderr
    with psycopg.connect(dsn) as conn:
        version, schema, indexes = _standing(conn)
        assert (version, schema) == ("0015", 15)
        assert indexes[OLD] == (True, True)
        # A real concurrent DDL failure, not a fabricated pg_index row.
        assert NEW in indexes and not indexes[NEW][0]
    # Isolate retry recovery from the separate concurrent-write proof: DROP
    # INDEX CONCURRENTLY itself waits for preexisting writers.
    for operation, target in (("upgrade", "0016"), ("downgrade", "0015")):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", operation, target],
            cwd=ROOT,
            env=_migration_env(dsn, lock_timeout="5s"),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        with psycopg.connect(dsn) as conn:
            expected = (
                ("0016", 16, {OLD: (True, True), NEW: (True, True)})
                if target == "0016"
                else ("0015", 15, {OLD: (True, True)})
            )
            assert _standing(conn) == expected
    second = first.model_copy(
        update={
            "message_ref": first.message_ref + ":during",
            "client_request_id": first.client_request_id + ":during",
            "body": "during 中a文b字",
        }
    )
    with psycopg.connect(dsn) as blocker:
        blocker.execute("LOCK TABLE messages IN ROW EXCLUSIVE MODE")
        with subprocess.Popen(
            [sys.executable, "-m", "alembic", "upgrade", "0016"],
            cwd=ROOT,
            env=_migration_env(dsn, lock_timeout="15s"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as proc:
            try:
                # The fresh build must reach a real
                # concurrent build wait before the concurrent consumer writes.
                deadline = time.monotonic() + 8
                with psycopg.connect(dsn, autocommit=True) as monitor:
                    while time.monotonic() < deadline:
                        if proc.poll() is not None:
                            pytest.fail(f"build exited early: {proc.communicate()}")
                        row = monitor.execute(
                            "SELECT phase FROM pg_stat_progress_create_index "
                            "WHERE index_relid=to_regclass(%s)",
                            (NEW,),
                        ).fetchone()
                        if row and "waiting for writers" in row[0]:
                            break
                        time.sleep(0.025)
                    else:
                        pytest.fail("build never reached native concurrent writer wait")
                # Use the actual owner message write, not hand-built row/digest.
                assert social.post_message(second)["admission"] == "committed"
                blocker.commit()
                out, err = proc.communicate(timeout=25)
                assert proc.returncode == 0, (out, err)
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()
    with psycopg.connect(dsn) as conn:
        assert _standing(conn) == ("0016", 16, {OLD: (True, True), NEW: (True, True)})
        rows = conn.execute(
            "SELECT message_ref FROM messages WHERE topic_ref=%s "
            "AND strpos(body,%s)>0 ORDER BY sequence DESC",
            (first.topic_ref, "中a文b字"),
        ).fetchall()
    assert rows == [(second.message_ref,), (first.message_ref,)]
    result = social.search_messages("中a文b字", topic_ref=first.topic_ref)
    assert [row["messageRef"] for row in result["messages"]] == [r[0] for r in rows]
    for original in (first, second):
        assert social.post_message(original)["admission"] == "existing"


@given(
    st.text(
        alphabet=st.sampled_from(
            ["中", "文", "字", "㐀", "鿿", "𠀀", "😀", "a", "é", "%", "_", " ", "\\"]
        ),
        min_size=0,
        max_size=40,
    )
)
@settings(max_examples=120, deadline=None, derandomize=True)
def test_sparse_grams_matches_independent_codepoint_oracle(body):
    dsn = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
    if not dsn:
        pytest.skip("requires native PostgreSQL test database")
    expected = sorted(
        {
            body[i : i + 3]
            for i in range(len(body) - 2)
            if any("\u3400" <= c <= "\u9fff" for c in body[i : i + 3])
        }
    )
    with psycopg.connect(dsn) as conn:
        actual = conn.execute("SELECT host_cjk_sparse_ngrams3_v1(%s)", (body,)).fetchone()[0]
    assert actual == expected
