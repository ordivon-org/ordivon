"""Reject ambiguous Node manifest authority using standard JSON semantics.

Native file consumers (Nix, Node and Python) must not disagree about duplicate
object member names. Reuse Python's JSON parser instead of adding another tool.
"""

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _reject_duplicate_object_members(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member {key!r}")
        result[key] = value
    return result


def test_duplicate_json_member_refuses_to_select_last_wins() -> None:
    with pytest.raises(ValueError, match="duplicate JSON member 'name'"):
        json.loads(
            '{"name":"old","name":"new"}', object_pairs_hook=_reject_duplicate_object_members
        )


def test_every_tracked_node_manifest_has_one_authoritative_value_per_key() -> None:
    tracked = (
        subprocess.check_output(["git", "-C", str(REPO_ROOT), "ls-files", "-z"], text=False)
        .decode()
        .split("\0")
    )
    manifests = sorted(name for name in tracked if name.endswith("/package.json"))
    assert manifests, "expected live tracked Node package consumers"
    for name in manifests:
        path = REPO_ROOT / name
        if path.is_file():
            try:
                json.loads(
                    path.read_text(encoding="utf-8"),
                    object_pairs_hook=_reject_duplicate_object_members,
                )
            except (ValueError, json.JSONDecodeError) as exc:
                pytest.fail(f"{name}: ambiguous or invalid JSON: {exc}")
