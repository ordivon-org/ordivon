"""Fixture-scoped consumer oracle: only observed retirement can be accepted.

This is Harness evaluation source, not an execution/admission policy or a
general repository/Workspace garbage collector. The candidate cannot edit it.
"""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture"
TASK = ROOT / "task.json"
REQUIRED_DELETIONS = frozenset({"docs/MIGRATION-R1.md", "docs/OLD-PHASE.md"})
PROTECTED = frozenset({
    "README.md",
    "docs/OPERATOR.md",
    "evidence/consumed-fixture.json",
})
# Spec v2: a bounded, quiescent filesystem tree with typed nodes. A retired
# path must be absent as a node, not merely absent from a regular-file list.
# Retained regular files are byte-identical and retained directory topology
# is unchanged. Unsupported nodes or failed traversal are UNKNOWN. A full
# closed-world fixture census is an assumption; this is not a live GC fence.
DIRECTORIES = frozenset({"docs", "evidence"})
EXPECTED_INITIAL = REQUIRED_DELETIONS | PROTECTED | DIRECTORIES


def _snapshot(directory: Path) -> dict[str, tuple[str, str]]:
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise OSError("workspace must be a normal directory")
    observed: dict[str, tuple[str, str]] = {}
    pending = [directory]
    while pending:
        # iterdir propagates filesystem scan failures; rglob can suppress them.
        for entry in sorted(pending.pop().iterdir()):
            relative_path = entry.relative_to(directory).as_posix()
            mode = entry.lstat().st_mode
            if stat.S_ISDIR(mode):
                observed[relative_path] = ("directory", "")
                pending.append(entry)
            elif stat.S_ISREG(mode):
                observed[relative_path] = (
                    "file", hashlib.sha256(entry.read_bytes()).hexdigest(),
                )
            else:
                raise OSError("unsupported node in fixture: " + relative_path)
    return observed


def _canonical_digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate task key")
        result[key] = value
    return result


def _reject_noninteger_number(token: str) -> None:
    raise ValueError("non-integer task number: " + token)


def _qualify_original(baseline: dict[str, tuple[str, str]]) -> None:
    # The existing task manifest is the source of expected initial identity.
    # The caller must still bind the task/oracle to its immutable Git cut:
    # self-consistency is not an authentication or concurrent-mutation fence.
    try:
        task = json.loads(
            TASK.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_float=_reject_noninteger_number,
            parse_constant=_reject_noninteger_number,
        )
        if not isinstance(task, dict):
            raise ValueError("task manifest must be an object")
        integrity = task.pop("integrity")
        if (task["taskId"] != "HARNESS-DOC-RETIREMENT-004"
                or type(task["taskVersion"]) is not int
                or task["taskVersion"] != 2
                or integrity != {
                    "algorithm": "sha256",
                    "canonicalization": "ordivon-canonical-json-v1",
                    "payloadDigest": _canonical_digest(task),
                }
                or task["oracle"]["digest"] !=
                    "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
            raise ValueError("task/oracle identity mismatch")
        manifest = [
            {"path": path, "digest": "sha256:" + value[1]}
            for path, value in sorted(baseline.items()) if value[0] == "file"
        ]
        if task["initialState"]["environmentDigest"] != _canonical_digest(manifest):
            raise ValueError("original evaluation fixture bytes changed")
    except (KeyError, TypeError, ValueError, UnicodeError) as error:
        raise OSError("unqualified original task: " + str(error)) from error


def evaluate(candidate_workspace: Path) -> dict:
    """Compare the candidate's actual bytes to a verifier-owned fixed fixture.

    ACCEPTED is valid only within this bounded fixture contract. It does not
    certify real dynamic consumers or any production deployment.
    """
    try:
        baseline = _snapshot(FIXTURE)
        if (set(baseline) != EXPECTED_INITIAL
                or any(baseline[path][0] != "directory" for path in DIRECTORIES)
                or any(baseline[path][0] != "file"
                       for path in REQUIRED_DELETIONS | PROTECTED)):
            raise OSError("original evaluation fixture changed")
        _qualify_original(baseline)
        actual = _snapshot(candidate_workspace)
    except OSError as error:
        return {
            "standing": "UNKNOWN",
            "reason": str(error),
            "deleted": [],
            "modified": [],
            "added": [],
        }

    deleted = sorted(set(baseline) - set(actual))
    modified = sorted(
        path for path in set(baseline) & set(actual)
        if baseline[path] != actual[path]
    )
    added = sorted(set(actual) - set(baseline))
    accepted = set(deleted) == REQUIRED_DELETIONS and not modified and not added
    return {
        "standing": "ACCEPTED" if accepted else "REJECTED",
        "deleted": deleted,
        "modified": modified,
        "added": added,
    }
