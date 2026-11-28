"""Qualify the finite native Mise configuration readset against one Git cut.

The source proof is a pre-task observation, not a claim about all child
execution inputs or transient mutations. External global configs remain an
environment assumption. Immutable Git blobs may be reused within one call;
working-tree bytes and native configuration discovery are never cached.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys


def qualify(repo: Path) -> None:
    repo = repo.resolve()

    def git(*args: str, input: bytes | None = None) -> bytes:
        return subprocess.check_output(
            ["git", "--no-replace-objects", *args], cwd=repo,
            input=input, stderr=subprocess.PIPE, timeout=30,
        )

    head = git("rev-parse", "--verify", "HEAD").strip().decode("ascii")
    if os.environ.get("GITHUB_SHA", head) != head:
        raise ValueError("checkout differs from provider GITHUB_SHA")
    entries = {}
    for row in git("ls-tree", "-r", "-z", "--full-tree", head).split(b"\0"):
        if row:
            meta, name = row.split(b"\t", 1)
            entries[os.fsdecode(name)] = meta.split()

    def oid(relative: str) -> bytes:
        fields = entries.get(relative, ())
        if (
            len(fields) != 3
            or fields[0] not in (b"100644", b"100755")
            or fields[1] != b"blob"
            or re.fullmatch(rb"[0-9a-f]{40}|[0-9a-f]{64}", fields[2]) is None
        ):
            raise ValueError("untracked or nonregular native Mise config: " + relative)
        return fields[2]

    # Native Git batch protocol avoids spawning one Git process per manifest
    # on every native discovery result. Only immutable object bytes are reused.
    blobs: dict[bytes, bytes] = {}

    def load(ids: list[bytes]) -> None:
        pending = list(dict.fromkeys(x for x in ids if x not in blobs))
        if not pending:
            return
        data = git("cat-file", "--batch", input=b"\n".join(pending) + b"\n")
        offset = 0
        for expected in pending:
            end = data.find(b"\n", offset)
            if end < 0:
                raise ValueError("incomplete Git batch header")
            fields = data[offset:end].split()
            if (
                len(fields) != 3 or fields[:2] != [expected, b"blob"]
                or not fields[2].isdigit()
            ):
                raise ValueError("unexpected Git batch object")
            size = int(fields[2])
            offset = end + 1
            if data[offset + size:offset + size + 1] != b"\n":
                raise ValueError("incomplete Git batch body")
            blobs[expected] = data[offset:offset + size]
            offset += size + 1
        if offset != len(data):
            raise ValueError("unexpected trailing Git batch data")

    def check(relative: str) -> None:
        identity = oid(relative)
        path = repo / relative
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ValueError("nonregular actual native Mise config: " + relative)
        load([identity])
        if path.read_bytes() != blobs[identity]:
            raise ValueError("native Mise config differs from Git HEAD: " + relative)

    roots = sorted(
        name for name in entries if name == "mise.toml" or name.endswith("/mise.toml")
    )
    if not roots:
        raise ValueError("no native Mise task manifests in Git HEAD")
    load([oid(name) for name in roots])
    for name in roots:
        check(name)
    for name in roots:
        directory = (repo / name).parent
        native = subprocess.run(
            ["mise", "--cd", str(directory), "config", "ls", "--json"],
            cwd=repo, capture_output=True, text=True, check=False, timeout=15,
        )
        if native.returncode:
            raise ValueError("native Mise config resolver failed for " + name)
        loaded = json.loads(native.stdout)
        if not isinstance(loaded, list):
            raise ValueError("invalid native Mise config result")
        for item in loaded:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise ValueError("invalid native Mise config entry")
            path = Path(item["path"])
            if not path.is_absolute():
                raise ValueError("native Mise reported nonabsolute config")
            try:
                relative = path.relative_to(repo)
            except ValueError:
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(repo):
                raise ValueError("unqualified native Mise config link")
            check(relative.as_posix())
    # A later discovery must not leave previously checked files changed.
    for name in roots:
        check(name)
    if git("rev-parse", "--verify", "HEAD").strip().decode("ascii") != head:
        raise ValueError("Git HEAD changed during qualification")


def main() -> int:
    try:
        qualify(Path.cwd())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("ERROR: nested Mise task source differs from exact Git HEAD: "
              + str(exc), file=sys.stderr)
        return 43
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
