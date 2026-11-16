#!/usr/bin/env python3
"""Independent Coding QA + committed-Git-byte readback; no delivery registry.

This is an opt-in task evaluator: its existing qa.py executes candidate Python;
never run untrusted arbitrary source outside an owner-qualified OS sandbox.
It does not call a model, mutate a Workspace, publish Git, claim Runtime
Artifact delivery, or accept a caller-authored success Boolean.
Actual user acknowledgement remains outside this verifier.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any


TASK_ID = "HARNESS-EDIT-ADDRESSING-002"
HERE = Path(__file__).resolve().parent
# Closed-world task adapters. Do not accept arbitrary caller supplied Python QA paths.
TASK_TARGETS = {
    "HARNESS-EDIT-ADDRESSING-002": ("harness-edit-addressing-002", "feature_flags.py"),
    "HARNESS-EDIT-MULTIREGION-003": ("harness-edit-multiregion-003", "pipeline.py"),
}
COMMIT_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
GIT = "/usr/bin/git"


class DeliveryGateError(ValueError):
    pass


def _task_qa(task_id: str = TASK_ID):
    try:
        task_dir, _ = TASK_TARGETS[task_id]
    except KeyError as error:
        raise DeliveryGateError("unsupported independent Coding task") from error
    spec = importlib.util.spec_from_file_location(
        "existing_harness_edit_qa_" + task_id.replace("-", "_"),
        HERE.parent / task_dir / "qa.py",
    )
    if spec is None or spec.loader is None:
        raise DeliveryGateError("existing independent QA is not loadable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        [GIT, "-C", str(repo), *args],
        capture_output=True,
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        raise DeliveryGateError(
            "consumer Git readback failed: "
            + result.stderr.decode("utf-8", errors="replace")[:250]
        )
    return result.stdout


def _path_in_commit(value: str, *, target_filename: str = "feature_flags.py") -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise DeliveryGateError("invalid delivered path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in (".", "..") for p in path.parts):
        raise DeliveryGateError("delivered path must stay relative within consumer Git")
    if path.as_posix() != value:
        raise DeliveryGateError("delivered path is not canonical")
    if path.name != target_filename:
        raise DeliveryGateError("delivery must be the task's edited source file")
    return value


def qualify(
    candidate_path: Path,
    consumer_repo: Path,
    consumer_commit: str,
    delivered_path: str | None = None,
    *,
    task_id: str = TASK_ID,
) -> dict[str, Any]:
    """Require hidden DomainQA and exact bytes read from an independent Git commit.

    An externally chosen consumer repository is an input, NOT a proof that a
    particular user accepted the result. A git object and consumer readback are
    stronger than a model's claim or Runtime Job exit=0, but not a user ACK.
    """
    if candidate_path.is_symlink():
        raise DeliveryGateError("candidate must be an ordinary source file")
    candidate = candidate_path.resolve(strict=True)
    repo = consumer_repo.resolve(strict=True)
    if not candidate.is_file():
        raise DeliveryGateError("candidate must be an ordinary source file")
    if not repo.is_dir():
        raise DeliveryGateError("consumer Git repository does not exist")
    if candidate == repo or repo in candidate.parents:
        raise DeliveryGateError("candidate and consumer source cannot be the same tree")

    if task_id not in TASK_TARGETS:
        raise DeliveryGateError("unsupported independent Coding task")
    _, target_filename = TASK_TARGETS[task_id]
    qa = _task_qa(task_id)
    task = qa.validate_task()
    if task["taskId"] != task_id:
        raise DeliveryGateError("wrong independent QA task")
    trial_count = task["reproducibility"]["cleanRebuildTrials"]
    # Test a frozen byte representation, not a file an Agent can edit between
    # visible/hidden QA and the subsequent immutable consumer-Git readback.
    source_bytes = candidate.read_bytes()
    with tempfile.TemporaryDirectory(prefix="harness-coding-qa-snapshot-") as directory:
        snapshot = Path(directory) / target_filename
        snapshot.write_bytes(source_bytes)
        qa_results = [
            qa.run_candidate("delivered-candidate", snapshot)
            for _ in range(trial_count)
        ]
        if snapshot.read_bytes() != source_bytes:
            raise DeliveryGateError("QA snapshot changed during verification")
    if candidate.read_bytes() != source_bytes:
        raise DeliveryGateError("candidate changed during independent QA")
    if not all(r["visiblePassed"] and r["hiddenPassed"] for r in qa_results):
        raise DeliveryGateError("independent public/hidden DomainQA did not pass")

    if not isinstance(consumer_commit, str) or not COMMIT_RE.fullmatch(consumer_commit):
        raise DeliveryGateError("delivery requires one immutable full Git commit ID")
    relative = _path_in_commit(
        delivered_path if delivered_path is not None else target_filename,
        target_filename=target_filename,
    )
    repo_root = Path(_git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if repo_root != repo:
        raise DeliveryGateError("consumer repo must be the exact independent Git root")
    read_commit = _git(repo, "rev-parse", "--verify", consumer_commit + "^{commit}").decode().strip()
    if read_commit != consumer_commit:
        raise DeliveryGateError("commit identity changed during readback")
    tree_entry = _git(repo, "ls-tree", consumer_commit, "--", relative).decode().strip()
    if not (tree_entry.startswith("100644 blob ") or tree_entry.startswith("100755 blob ")):
        raise DeliveryGateError("delivered Git path is not a regular tracked blob")
    delivered = _git(repo, "show", consumer_commit + ":" + relative)
    if candidate.read_bytes() != source_bytes:
        raise DeliveryGateError("candidate changed during independent QA")
    if delivered != source_bytes:
        raise DeliveryGateError("consumer Git blob does not match the independently QA-passed candidate")
    source_sha = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    return {
        "schemaVersion": 1,
        "kind": "ordivon.harness-coding-consumer-delivery-qualification",
        "taskId": task_id,
        "domainQA": "passed",
        "domainQATrials": trial_count,
        "consumerGitByteReadback": "verified",
        "candidateDigest": source_sha,
        "consumerCommit": consumer_commit,
        "consumerPath": relative,
        "consumerGitByteReadbackQualified": True,
        "finalUserDeliveryProven": False,
        "userAcknowledgement": "UNKNOWN",
        "modelAuthorshipEvidence": "UNKNOWN",
        "runtimeToolEffectEvidence": "UNKNOWN",
        "truthBoundary": (
            "an independent verifier read exact QA-passed bytes from the caller-supplied "
            "consumer Git repository; user acceptance and production deployment remain UNKNOWN"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--consumer-repo", type=Path, required=True)
    parser.add_argument("--consumer-commit", required=True)
    parser.add_argument("--consumer-path", default=None)
    parser.add_argument("--task-id", choices=tuple(TASK_TARGETS), default=TASK_ID)
    args = parser.parse_args()
    try:
        value = qualify(
            args.candidate,
            args.consumer_repo,
            args.consumer_commit,
            delivered_path=args.consumer_path,
            task_id=args.task_id,
        )
    except (DeliveryGateError, FileNotFoundError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({
            "kind": "ordivon.harness-coding-consumer-delivery-qualification",
            "taskId": args.task_id,
            "consumerGitByteReadbackQualified": False,
            "finalUserDeliveryProven": False,
            "userAcknowledgement": "UNKNOWN",
            "reason": str(error)[:500],
        }, sort_keys=True))
        return 1
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
