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


def _git_path_set(root: Path, *args: str) -> set[str]:
    """NUL-safe Git inventory, with bounded discovery and no path guessing."""
    raw = _git(root, *args)
    if not raw:
        return set()
    if len(raw) > 1024 * 1024:
        raise DeliveryGateError("original output path inventory exceeds safe bound")
    paths = raw.split(b"\0")
    if paths[-1] != b"":
        raise DeliveryGateError("original Git path inventory was truncated")
    result: set[str] = set()
    for value in paths[:-1]:
        try:
            path = value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise DeliveryGateError("non-UTF8 original path requires source review") from exc
        posix = PurePosixPath(path)
        if (
            not path or "\0" in path or "\\" in path or posix.is_absolute()
            or path != posix.as_posix() or any(part in (".", "..") for part in posix.parts)
        ):
            raise DeliveryGateError("invalid original Git path")
        result.add(path)
    if len(result) > 2048:
        raise DeliveryGateError("original output scope exceeds bounded qualification")
    return result


def qualify_original_git_output_scope(
    original_repo: Path,
    original_base_commit: str,
    consumer_repo: Path,
    consumer_commit: str,
) -> dict[str, Any]:
    """Compare *every* Git-worktree delta with independent immutable Git bytes.

    This is a bounded worktree/Git-scope verifier, not a trusted Run-wide
    output manifest, original recipient authorization, or Native OS drain.
    Unknown ignored/deleted outputs fail closed. The caller-selected original
    workspace, baseline and destination are not independently authenticated.
    """
    if not (
        isinstance(original_base_commit, str)
        and COMMIT_RE.fullmatch(original_base_commit)
        and isinstance(consumer_commit, str)
        and COMMIT_RE.fullmatch(consumer_commit)
    ):
        raise DeliveryGateError("original/consumer baselines require immutable full Git IDs")
    if original_repo.is_symlink() or consumer_repo.is_symlink():
        raise DeliveryGateError("original and recipient Git roots must be directories")
    origin = original_repo.resolve(strict=True)
    receiver = consumer_repo.resolve(strict=True)
    if origin == receiver or origin in receiver.parents or receiver in origin.parents:
        raise DeliveryGateError("original and consumer Git roots must be independent")
    for repo in (origin, receiver):
        git_root = Path(_git(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
        if git_root != repo:
            raise DeliveryGateError("expected exact original or consumer Git root")
    source_base = _git(
        origin, "rev-parse", "--verify", original_base_commit + "^{commit}",
    ).decode().strip()
    if source_base != original_base_commit:
        raise DeliveryGateError("original baseline changed during verification")
    receiver_commit = _git(
        receiver, "rev-parse", "--verify", consumer_commit + "^{commit}",
    ).decode().strip()
    if receiver_commit != consumer_commit:
        raise DeliveryGateError("consumer immutable commit identity changed")
    # Enumerate both staged/committed modifications since the original
    # baseline and still-untracked outputs. Git -z retains spaces/newlines.
    removed = _git_path_set(
        origin, "diff", "--no-renames", "--name-only", "-z",
        "--diff-filter=D", original_base_commit, "--",
    )
    if removed:
        raise DeliveryGateError("deleted original source needs explicit Domain decision")
    ignored = _git_path_set(
        origin, "ls-files", "--others", "--ignored", "--exclude-standard", "-z",
    )
    if ignored:
        raise DeliveryGateError("ignored original outputs require Domain retention decision: UNKNOWN")
    changed = _git_path_set(
        origin, "diff", "--no-renames", "--name-only", "-z",
        "--diff-filter=ACMRT", original_base_commit, "--",
    )
    untracked = _git_path_set(origin, "ls-files", "--others", "--exclude-standard", "-z")
    scoped = sorted(changed | untracked)
    if not scoped:
        raise DeliveryGateError("empty original Git output scope requires explicit Domain decision")
    digests: dict[str, str] = {}
    for relative in scoped:
        original = origin / relative
        if original.is_symlink() or not original.is_file() or origin not in original.resolve().parents:
            raise DeliveryGateError("original output must be ordinary in-root file, not symlink")
        if original.stat().st_size > 64 * 1024 * 1024:
            raise DeliveryGateError("large original file requires streaming Artifact recipient")
        source_bytes = original.read_bytes()
        entry = _git(receiver, "ls-tree", consumer_commit, "--", relative).decode().strip()
        if not (entry.startswith("100644 blob ") or entry.startswith("100755 blob ")):
            raise DeliveryGateError("consumer omitted original output or stored non-file Git object")
        received = _git(receiver, "show", consumer_commit + ":" + relative)
        if received != source_bytes:
            raise DeliveryGateError("original/consumer Git output bytes mismatch")
        if original.read_bytes() != source_bytes:
            raise DeliveryGateError("original output changed during consumer verification")
        digests[relative] = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    # Consumer blobs are immutable under this exact commit. Verify source
    # membership did not change while reading; native Run Epoch fencing is
    # still independently required before a real protected Finalizer.
    if removed != _git_path_set(
        origin, "diff", "--no-renames", "--name-only", "-z",
        "--diff-filter=D", original_base_commit, "--",
    ) or changed != _git_path_set(
        origin, "diff", "--no-renames", "--name-only", "-z",
        "--diff-filter=ACMRT", original_base_commit, "--",
    ) or untracked != _git_path_set(
        origin, "ls-files", "--others", "--exclude-standard", "-z",
    ) or ignored != _git_path_set(
        origin, "ls-files", "--others", "--ignored", "--exclude-standard", "-z",
    ):
        raise DeliveryGateError("original output scope changed during verification")
    return {
        "originalOutputSetStanding": "verified_test_scope",
        "completeOriginalOutputSetReadbackQualified": True,
        "originalOutputPaths": scoped,
        "originalOutputDigests": digests,
        "originalBaseCommit": original_base_commit,
        "consumerCommit": consumer_commit,
        "sourceScope": "git-worktree-delta-and-untracked-only",
        "scopeAuthority": "caller-supplied-original-and-consumer-not-authenticated",
        "originalRunFullOutputCoverage": "UNKNOWN",
        "workspaceSourceFenced": False,
        "finalUserDeliveryProven": False,
        "userAcknowledgement": "UNKNOWN",
        "productionFinalizerEligible": False,
    }


def qualify(
    candidate_path: Path,
    consumer_repo: Path,
    consumer_commit: str,
    delivered_path: str | None = None,
    *,
    task_id: str = TASK_ID,
    original_workspace_repo: Path | None = None,
    original_base_commit: str | None = None,
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
    if (original_workspace_repo is None) != (original_base_commit is None):
        raise DeliveryGateError("original workspace and immutable baseline must both be supplied")
    scope: dict[str, Any] = (
        qualify_original_git_output_scope(
            original_workspace_repo, original_base_commit, repo, consumer_commit,
        )
        if original_workspace_repo is not None and original_base_commit is not None
        else {
            "originalOutputSetStanding": "UNKNOWN",
            "completeOriginalOutputSetReadbackQualified": False,
            "originalRunFullOutputCoverage": "UNKNOWN",
            "workspaceSourceFenced": False,
            "productionFinalizerEligible": False,
        }
    )
    return {
        **scope,
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
    parser.add_argument("--original-workspace-repo", type=Path, default=None)
    parser.add_argument("--original-base-commit", default=None)
    args = parser.parse_args()
    try:
        value = qualify(
            args.candidate,
            args.consumer_repo,
            args.consumer_commit,
            delivered_path=args.consumer_path,
            task_id=args.task_id,
            original_workspace_repo=args.original_workspace_repo,
            original_base_commit=args.original_base_commit,
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
