"""Qualify a private extracted release source tree against native Git objects.

Generated venv and ordinary source-derived cache filenames are separate build
carriers, not part of the reviewed source inventory. Their contents are not
attested here. This check assumes a quiescent, operator-owned release tree.
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

SUBTREE = "services/host"


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def inventory(repo: Path, commit: str) -> dict[str, tuple[str, bytes]]:
    expected = {}
    for record in git(repo, "ls-tree", "-rz", "--full-tree", commit, "--", SUBTREE).split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, kind, oid = meta.split(b" ")
        path = os.fsdecode(raw_path)
        require(path.startswith(SUBTREE + "/"), "unexpected Git path")
        require(
            kind == b"blob" and mode in (b"100644", b"100755", b"120000"),
            f"unsupported Git entry {path}",
        )
        expected[path[len(SUBTREE) + 1 :]] = (mode.decode("ascii"), oid)
    require(bool(expected), "empty Git source subtree")
    return expected


def cache_directory(path: Path, source_stems: set[str]) -> None:
    require(bool(source_stems), f"unexpected cache directory {path}")
    for child in path.iterdir():
        require(stat.S_ISREG(child.lstat().st_mode), f"unexpected cache entry {child}")
        require(
            any(
                re.fullmatch(
                    re.escape(stem) + r"\.cpython-[0-9]+[a-z]?(?:\.opt-[0-9]+)?\.pyc", child.name
                )
                for stem in source_stems
            ),
            f"unexpected cache filename {child}",
        )


def verify(repo: Path, commit: str, release: Path) -> None:
    release = release.absolute()
    expected = inventory(repo, commit)
    dirs = {str(parent) for name in expected for parent in PurePosixPath(name).parents}
    caches: dict[str, set[str]] = {}
    for name in expected:
        path = PurePosixPath(name)
        if path.suffix == ".py" and expected[name][0] != "120000":
            caches.setdefault(str(path.parent), set()).add(path.stem)

    require(stat.S_ISDIR(release.lstat().st_mode), "release root must be a real directory")
    seen: set[str] = set()
    regular: list[tuple[Path, bytes]] = []

    def walk(directory: Path, relative: PurePosixPath) -> None:
        for entry in directory.iterdir():
            rel = str(relative / entry.name)
            mode = entry.lstat().st_mode
            if rel in expected:
                git_mode, oid = expected[rel]
                seen.add(rel)
                if git_mode == "120000":
                    require(stat.S_ISLNK(mode), f"missing symlink {rel}")
                    actual = git(
                        repo, "hash-object", "--stdin", input_bytes=os.fsencode(os.readlink(entry))
                    ).strip()
                    require(actual == oid, f"Git blob differs for {rel}")
                else:
                    require(stat.S_ISREG(mode), f"missing regular file {rel}")
                    require(
                        bool(mode & 0o111) == (git_mode == "100755"),
                        f"Git executable bit differs for {rel}",
                    )
                    regular.append((entry, oid))
            elif rel in dirs:
                require(stat.S_ISDIR(mode), f"source parent is not a real directory {rel}")
                walk(entry, relative / entry.name)
            elif rel == ".venv":
                require(stat.S_ISDIR(mode), "generated .venv must be a real directory")
            elif entry.name == "__pycache__":
                require(stat.S_ISDIR(mode), f"cache must be a real directory {rel}")
                cache_directory(entry, caches.get(str(relative), set()))
            else:
                raise ValueError(f"unexpected release entry {rel}")

    walk(release, PurePosixPath("."))
    require(seen == expected.keys(), f"missing source entries {sorted(expected.keys() - seen)}")
    # Native Git computes blob identity in batches, without text path splitting
    # or repository clean/smudge filters. This supports either Git object format.
    for start in range(0, len(regular), 64):
        batch = regular[start : start + 64]
        hashes = git(
            repo, "hash-object", "--no-filters", "--", *(str(p) for p, _ in batch)
        ).splitlines()
        require(len(hashes) == len(batch), "Git blob observation count differs")
        for (path, oid), actual in zip(batch, hashes, strict=True):
            require(actual == oid, f"Git blob differs for {path.relative_to(release)}")
    print(f"release_source_verified={len(expected)}")


if __name__ == "__main__":
    try:
        verify(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"release source drift: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
