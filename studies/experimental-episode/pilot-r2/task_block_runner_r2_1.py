from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def journal_append(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def journal_state(path: Path) -> tuple[set[str], set[str]]:
    started: set[str] = set()
    completed: set[str] = set()
    if not path.exists():
        return started, completed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        trial_id = row.get("trialId")
        if not isinstance(trial_id, str):
            raise RuntimeError("task-block journal event lacks trialId")
        if row.get("event") == "trial_started":
            started.add(trial_id)
        elif row.get("event") == "trial_completed":
            completed.add(trial_id)
    return started, completed


def assert_no_uncertain_started(path: Path) -> None:
    started, completed = journal_state(path)
    uncertain = sorted(started - completed)
    if uncertain:
        raise RuntimeError(f"uncertain trials require reconciliation before dispatch: {uncertain}")


def trial_record_path(output_dir: Path, trial_id: str) -> Path:
    return output_dir / "trials" / f"{trial_id.replace(':', '-')}.json"


def validate_complete_block(trials: list[dict[str, Any]]) -> None:
    if len(trials) != 4:
        raise ValueError("TaskBlock requires exactly four Model×Harness trials")
    task_ids = {row.get("taskId") for row in trials}
    block_ids = {row.get("blockId") for row in trials}
    if len(task_ids) != 1 or len(block_ids) != 1:
        raise ValueError("TaskBlock trials must share one taskId and one blockId")
    cells = {(row.get("model"), row.get("codec")) for row in trials}
    if len(cells) != 4:
        raise ValueError("TaskBlock requires four unique Model×Harness cells")


def execute_task_block(
    *,
    output_dir: Path,
    trials: list[dict[str, Any]],
    execute_one: Callable[[dict[str, Any]], dict[str, Any]],
    continuation_check: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    validate_complete_block(trials)
    journal = output_dir / "journal.jsonl"
    assert_no_uncertain_started(journal)
    _, completed = journal_state(journal)
    records: list[dict[str, Any]] = []
    for trial in trials:
        trial_id = str(trial["trialId"])
        path = trial_record_path(output_dir, trial_id)
        if trial_id in completed:
            if not path.is_file():
                raise RuntimeError(f"completed journal entry lacks trial artifact: {trial_id}")
            record = json.loads(path.read_text(encoding="utf-8"))
            records.append(record)
            if continuation_check is not None:
                continuation_check(record)
            continue
        journal_append(
            journal,
            {
                "event": "trial_started",
                "trialId": trial_id,
                "blockId": trial["blockId"],
                "blockOrdinal": trial["blockOrdinal"],
                "ordinal": trial["ordinal"],
                "taskId": trial["taskId"],
                "taskFamily": trial["taskFamily"],
                "model": trial["model"],
                "codec": trial["codec"],
                "observedAtUnixMs": int(time.time() * 1000),
            },
        )
        record = execute_one(trial)
        record_digest = record.get("recordDigest")
        if not isinstance(record_digest, str) or not record_digest.startswith("sha256:"):
            raise RuntimeError(f"trial callback returned no canonical recordDigest: {trial_id}")
        json_write(path, record)
        journal_append(
            journal,
            {
                "event": "trial_completed",
                "trialId": trial_id,
                "blockId": trial["blockId"],
                "recordDigest": record_digest,
                "observedAtUnixMs": int(time.time() * 1000),
            },
        )
        records.append(record)
        if continuation_check is not None:
            continuation_check(record)
    if len(records) != 4:
        raise RuntimeError("TaskBlock did not converge to four durable trial records")
    return records
