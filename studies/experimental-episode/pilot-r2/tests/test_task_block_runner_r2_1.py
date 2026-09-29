from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "task_block_runner_r2_1.py"


def load():
    spec = importlib.util.spec_from_file_location("r2_1_task_block_runner_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def trials():
    return [
        {"trialId": f"trial-{i}", "ordinal": i, "blockId": "block-1", "blockOrdinal": 1, "taskId": "task-1", "taskFamily": "family", "model": model, "codec": codec}
        for i, (model, codec) in enumerate((("m1", "c1"), ("m1", "c2"), ("m2", "c1"), ("m2", "c2")), start=1)
    ]


def test_uncertain_trial_blocks_callback_before_any_redispatch(tmp_path: Path) -> None:
    m = load()
    m.journal_append(tmp_path / "journal.jsonl", {"event": "trial_started", "trialId": "trial-1"})
    called = False
    def execute_one(_):
        nonlocal called
        called = True
        raise AssertionError("must not execute")
    with pytest.raises(RuntimeError, match="require reconciliation"):
        m.execute_task_block(output_dir=tmp_path, trials=trials(), execute_one=execute_one)
    assert called is False


def test_task_block_replay_reads_completed_records_without_reexecution(tmp_path: Path) -> None:
    m = load()
    count = 0
    def execute_one(trial):
        nonlocal count
        count += 1
        return {**trial, "recordDigest": f"sha256:{count:064x}"}
    first = m.execute_task_block(output_dir=tmp_path, trials=trials(), execute_one=execute_one)
    assert len(first) == 4 and count == 4
    def must_not_execute(_):
        raise AssertionError("completed record was redispatched")
    second = m.execute_task_block(output_dir=tmp_path, trials=trials(), execute_one=must_not_execute)
    assert second == first


def test_continuation_failure_happens_after_durable_completion(tmp_path: Path) -> None:
    m = load()
    def execute_one(trial):
        return {**trial, "recordDigest": "sha256:" + "a" * 64, "standing": "STOP"}
    def continuation(record):
        if record["standing"] == "STOP":
            raise RuntimeError("stop after durable record")
    with pytest.raises(RuntimeError, match="stop after durable record"):
        m.execute_task_block(output_dir=tmp_path, trials=trials(), execute_one=execute_one, continuation_check=continuation)
    started, completed = m.journal_state(tmp_path / "journal.jsonl")
    assert "trial-1" in started and "trial-1" in completed
    assert (tmp_path / "trials" / "trial-1.json").is_file()
