"""Fixture-scoped consumer oracle: only observed retirement can be accepted.

This is Harness evaluation source, not an execution/admission policy or a
general repository/Workspace garbage collector. The candidate cannot edit it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture"
REQUIRED_DELETIONS = frozenset({"docs/MIGRATION-R1.md", "docs/OLD-PHASE.md"})
PROTECTED = frozenset({
    "README.md",
    "docs/OPERATOR.md",
    "evidence/consumed-fixture.json",
})
EXPECTED_INITIAL = REQUIRED_DELETIONS | PROTECTED


def _snapshot(directory: Path) -> dict[str, str]:
    if not directory.is_dir() or directory.is_symlink():
        raise OSError("workspace must be a normal directory")
    observed: dict[str, str] = {}
    for entry in sorted(directory.rglob("*")):
        if entry.is_symlink():
            raise OSError("symlinks are not part of this fixture contract")
        if not entry.is_file():
            continue
        relative_path = entry.relative_to(directory).as_posix()
        observed[relative_path] = hashlib.sha256(entry.read_bytes()).hexdigest()
    return observed


def evaluate(candidate_workspace: Path) -> dict:
    """Compare the candidate's actual bytes to a verifier-owned fixed fixture.

    ACCEPTED is valid only within this bounded fixture contract. It does not
    certify real dynamic consumers or any production deployment.
    """
    try:
        baseline = _snapshot(FIXTURE)
        if set(baseline) != EXPECTED_INITIAL:
            raise OSError("original evaluation fixture changed")
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
