"""Verified official GitHub REST API release acquisition for the pinned mise CI tool."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "jdx/mise"
VERSION = "2026.9.12"
ASSET_ID = 576717062
ASSET_NAME = "mise-v2026.9.12-linux-x64.tar.zst"
ASSET_SIZE = 31356996
ASSET_SHA256 = "e302176806b007f63eacaa22f10418a651c25a9d98a606d9ea40fe7198af3bf2"
BINARY_SHA256 = "e79ae57945034903aee8aa2ea66b4c7ca9cd4f4edd5a8a78a589cbae6d0f428a"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_metadata(row: dict[str, object]) -> None:
    if (
        row.get("id") != ASSET_ID
        or row.get("name") != ASSET_NAME
        or row.get("size") != ASSET_SIZE
        or row.get("digest") != "sha256:" + ASSET_SHA256
        or row.get("state") != "uploaded"
    ):
        raise ValueError("official asset identity/size/digest mismatch")


def mise_dir() -> Path:
    if value := os.environ.get("MISE_DATA_DIR"):
        return Path(value)
    if value := os.environ.get("XDG_DATA_HOME"):
        return Path(value) / "mise"
    return Path.home() / ".local" / "share" / "mise"


def provision() -> Path:
    target = mise_dir() / "bin" / "mise"
    if target.is_file() and file_sha256(target) == BINARY_SHA256:
        print("NETWORK_GH_API_MISE_REUSED", VERSION)
        return target

    row = json.loads(subprocess.run(
        ["gh", "api", "repos/jdx/mise/releases/assets/576717062"],
        check=True, capture_output=True, text=True, timeout=35,
    ).stdout)
    verify_metadata(row)

    with tempfile.TemporaryDirectory(prefix="ordivon-ci-mise-") as tmp:
        base = Path(tmp)
        archive = base / ASSET_NAME
        for attempt in range(1, 4):
            try:
                with archive.open("wb") as out:
                    subprocess.run(
                        ["gh", "api", "-H", "Accept: application/octet-stream",
                         "repos/jdx/mise/releases/assets/576717062"],
                        stdout=out, check=True, timeout=150,
                    )
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if attempt == 3:
                    raise
                time.sleep(attempt)
        if archive.stat().st_size != ASSET_SIZE or file_sha256(archive) != ASSET_SHA256:
            raise ValueError("binary response mismatch or partial download")
        subprocess.run(
            ["tar", "--zstd", "-xf", str(archive), "-C", str(base), "mise/bin/mise"],
            check=True, timeout=45,
        )
        binary = base / "mise/bin/mise"
        if not binary.is_file() or file_sha256(binary) != BINARY_SHA256:
            raise ValueError("extracted mise binary does not match pinned identity")
        binary.chmod(0o755)
        actual = subprocess.run(
            [str(binary), "version"], check=True, capture_output=True,
            text=True, timeout=15,
            env={**os.environ, "MISE_NO_UPDATE_NOTIFIER": "1"},
        ).stdout.split()[0]
        if actual != VERSION:
            raise ValueError("executable version does not match pin")
        target.parent.mkdir(parents=True, exist_ok=True)
        staged = target.with_name(f".mise-{os.getpid()}.new")
        try:
            shutil.copyfile(binary, staged)
            staged.chmod(0o755)
            if file_sha256(staged) != BINARY_SHA256:
                raise ValueError("staged binary changed")
            os.replace(staged, target)
        finally:
            staged.unlink(missing_ok=True)
    print("NETWORK_GH_API_MISE_VERIFIED", VERSION, ASSET_SIZE)
    return target


if __name__ == "__main__":
    try:
        provision()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print("NETWORK_GH_API_MISE_NOT_VERIFIED", type(error).__name__, file=sys.stderr)
        raise SystemExit(1) from error
