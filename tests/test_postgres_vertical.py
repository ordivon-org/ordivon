from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from ordivon_host_v2 import CheckpointInput, ConflictError, HostV2, TaskState

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def host() -> HostV2:
    assert DSN is not None
    value = HostV2(DSN)
    value.initialize()
    return value


def tid(label: str) -> str:
    return f"task:v2:{label}:{uuid4().hex}"


def test_adopt_checkpoint_resume_and_historical_pin() -> None:
    h = host()
    task_id = tid("vertical")
    first = h.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(payload={"objective": "prove v2", "frontier": "e1"}),
        client_request_id=f"adopt:{task_id}",
    )
    assert first.task.revision == 1
    second = h.checkpoint(
        task_id=task_id,
        expected_revision=1,
        checkpoint=CheckpointInput(payload={"objective": "prove v2", "frontier": "e2"}),
        client_request_id=f"cp:{task_id}:2",
    )
    assert second.task.revision == 2
    assert h.resume(task_id).checkpoint["frontier"] == "e2"
    assert h.resume(task_id, 1).checkpoint["frontier"] == "e1"


def test_exact_adopt_replay_converges_and_conflict_fails() -> None:
    h = host()
    task_id = tid("adopt-replay")
    cp = CheckpointInput(payload={"x": 1})
    a = h.adopt(task_id=task_id, checkpoint=cp, client_request_id=f"a:{task_id}")
    b = h.adopt(task_id=task_id, checkpoint=cp, client_request_id=f"b:{task_id}")
    assert a.task.checkpoint_digest == b.task.checkpoint_digest
    assert b.admission.value == "existing"
    with pytest.raises(ConflictError):
        h.adopt(
            task_id=task_id,
            checkpoint=CheckpointInput(payload={"x": 2}),
            client_request_id=f"c:{task_id}",
        )


def test_response_loss_replay_with_new_request_id_is_existing() -> None:
    h = host()
    task_id = tid("response-loss")
    h.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(payload={"n": 1}),
        client_request_id=f"a:{task_id}",
    )
    first = h.checkpoint(
        task_id=task_id,
        expected_revision=1,
        checkpoint=CheckpointInput(payload={"n": 2}),
        client_request_id=f"cp1:{task_id}",
    )
    replay = h.checkpoint(
        task_id=task_id,
        expected_revision=1,
        checkpoint=CheckpointInput(payload={"n": 2}),
        client_request_id=f"cp2:{task_id}",
    )
    assert first.task.revision == replay.task.revision == 2
    assert replay.admission.value == "existing"


def test_same_revision_race_has_one_committed_winner() -> None:
    h = host()
    task_id = tid("race")
    h.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(payload={"winner": None}),
        client_request_id=f"a:{task_id}",
    )

    def write(value: str) -> str:
        try:
            result = h.checkpoint(
                task_id=task_id,
                expected_revision=1,
                checkpoint=CheckpointInput(payload={"winner": value}),
                client_request_id=f"cp:{task_id}:{value}",
            )
            return result.admission.value
        except ConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(write, ("a", "b")))
    assert outcomes == ["committed", "conflict"]
    assert h.resume(task_id).revision == 2


def test_terminal_task_cannot_reopen() -> None:
    h = host()
    task_id = tid("terminal")
    h.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(payload={"n": 1}),
        client_request_id=f"a:{task_id}",
    )
    h.checkpoint(
        task_id=task_id,
        expected_revision=1,
        checkpoint=CheckpointInput(payload={"n": 2}),
        client_request_id=f"done:{task_id}",
        state=TaskState.COMPLETED,
    )
    with pytest.raises(ConflictError):
        h.checkpoint(
            task_id=task_id,
            expected_revision=2,
            checkpoint=CheckpointInput(payload={"n": 3}),
            client_request_id=f"reopen:{task_id}",
        )


def test_transaction_failure_does_not_leave_partial_checkpoint() -> None:
    import psycopg
    from psycopg import sql

    h = host()
    task_id = tid("rollback")
    h.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(payload={"n": 1}),
        client_request_id=f"a:{task_id}",
    )
    assert DSN is not None
    safe_token = task_id.replace(":", "_").replace("-", "_")
    function_name = f"fail_checkpoint_{safe_token[-24:]}"
    trigger_name = f"trg_{safe_token[-24:]}"
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(
            sql.SQL(
                "CREATE FUNCTION {}() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN IF NEW.task_id = {} THEN RAISE EXCEPTION 'injected checkpoint failure'; "
                "END IF; RETURN NEW; END $$"
            ).format(sql.Identifier(function_name), sql.Literal(task_id))
        )
        conn.execute(
            sql.SQL(
                "CREATE TRIGGER {} BEFORE INSERT ON checkpoints FOR EACH ROW EXECUTE FUNCTION {}()"
            ).format(sql.Identifier(trigger_name), sql.Identifier(function_name))
        )
    try:
        with pytest.raises(psycopg.errors.RaiseException):
            h.checkpoint(
                task_id=task_id,
                expected_revision=1,
                checkpoint=CheckpointInput(payload={"n": 2}),
                client_request_id=f"cp:{task_id}",
            )
    finally:
        with psycopg.connect(DSN, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP TRIGGER IF EXISTS {} ON checkpoints").format(
                    sql.Identifier(trigger_name)
                )
            )
            conn.execute(
                sql.SQL("DROP FUNCTION IF EXISTS {}()").format(sql.Identifier(function_name))
            )
    resumed = h.resume(task_id)
    assert resumed.revision == 1
    assert resumed.checkpoint == {"n": 1}


def test_client_request_id_conflicting_reuse_fails_closed() -> None:
    h = host()
    task_id = tid("request-id")
    request_id = f"same:{task_id}"
    h.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(payload={"x": 1}),
        client_request_id=request_id,
    )
    with pytest.raises(ConflictError):
        h.adopt(
            task_id=task_id,
            checkpoint=CheckpointInput(payload={"x": 2}),
            client_request_id=request_id,
        )
