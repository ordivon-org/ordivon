from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from ordivon_host_v2 import CheckpointInput, HostV2

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set")


def host() -> HostV2:
    assert DSN is not None
    value = HostV2(DSN)
    value.initialize()
    return value


def test_concurrent_identical_adopt_same_idempotency_key_all_converge() -> None:
    h = host()
    task_id = f"task:v2:destroy-adopt:{uuid4().hex}"
    request_id = f"request:v2:destroy-adopt:{uuid4().hex}"

    def call(_: int) -> str:
        result = h.adopt(
            task_id=task_id,
            checkpoint=CheckpointInput(payload={"x": 1}),
            client_request_id=request_id,
        )
        return result.admission.value

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(call, range(8)))

    assert set(outcomes) <= {"committed", "existing"}
    assert outcomes.count("committed") == 1
    assert h.resume(task_id).revision == 1


def test_concurrent_identical_checkpoint_same_idempotency_key_all_converge() -> None:
    h = host()
    task_id = f"task:v2:destroy-checkpoint:{uuid4().hex}"
    h.adopt(
        task_id=task_id,
        checkpoint=CheckpointInput(payload={"x": 1}),
        client_request_id=f"adopt:{task_id}",
    )
    request_id = f"request:v2:destroy-checkpoint:{uuid4().hex}"

    def call(_: int) -> str:
        result = h.checkpoint(
            task_id=task_id,
            expected_revision=1,
            checkpoint=CheckpointInput(payload={"x": 2}),
            client_request_id=request_id,
        )
        return result.admission.value

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(call, range(8)))

    assert set(outcomes) <= {"committed", "existing"}
    assert outcomes.count("committed") == 1
    assert h.resume(task_id).revision == 2
