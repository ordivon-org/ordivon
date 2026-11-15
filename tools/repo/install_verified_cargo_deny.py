#!/usr/bin/env python3
"""Install one pinned upstream cargo-deny CI binary via GitHub's official asset API.

This is a thin GitHub CLI + SHA-256 composition, not a package-manager or
Release-client replacement. The Actions cache holds *untrusted bytes*, never
install authority; every restored archive is reverified before extraction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time

REPO = "EmbarkStudios/cargo-deny"
VERSION = "0.20.2"
ASSET_ID = 471598214
ASSET_NAME = "cargo-deny-0.20.2-x86_64-unknown-linux-musl.tar.gz"
ASSET_SIZE = 4936832
ASSET_SHA256 = "9f12ed4c49936e09b48bf862b595cde2fe64fcbd9d74dfacac6131ca824c8d5f"
MEMBER = "cargo-deny-0.20.2-x86_64-unknown-linux-musl/cargo-deny"


def _gh_api(accept: str, *, destination: Path | None = None) -> bytes:
    cmd = [
        "gh", "api", "-H", f"Accept: {accept}",
        f"repos/{REPO}/releases/assets/{ASSET_ID}",
    ]
    # Replay only an idempotent GET. Each binary retry truncates the partial
    # target and no partial response is ever treated as installed authority.
    # This is transport retry, not bypass of version/size/digest verification.
    for attempt in range(3):
        try:
            if destination is None:
                result = subprocess.run(
                    cmd, capture_output=True, check=False, timeout=35,
                )
            else:
                with destination.open("wb") as stream:
                    result = subprocess.run(
                        cmd, stdout=stream, stderr=subprocess.DEVNULL,
                        check=False, timeout=60,
                    )
            if result.returncode == 0:
                return result.stdout if destination is None else b""
        except subprocess.TimeoutExpired:
            pass
        if attempt < 2:
            time.sleep(2 ** attempt)
    role = "metadata" if destination is None else "binary"
    raise RuntimeError(f"GitHub Release asset {role} request failed after 3 attempts")


def _check_metadata(raw: bytes) -> None:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, ValueError) as error:
        raise RuntimeError("GitHub Release asset metadata is invalid") from error
    if (
        not isinstance(value, dict)
        or type(value.get("id")) is not int
        or value["id"] != ASSET_ID
        or value.get("name") != ASSET_NAME
        or type(value.get("size")) is not int
        or value["size"] != ASSET_SIZE
        or value.get("digest") != "sha256:" + ASSET_SHA256
        or value.get("state") != "uploaded"
    ):
        raise RuntimeError("GitHub Release asset identity, size or digest drift")


def _verified_archive(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    if path.stat().st_size != ASSET_SIZE:
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == ASSET_SHA256


def install(cache_dir: Path, bin_dir: Path) -> str:
    if not cache_dir.is_absolute() or not bin_dir.is_absolute():
        raise ValueError("CI cargo-deny cache and install directories must be absolute")
    cache_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)
    if cache_dir.is_symlink() or bin_dir.is_symlink():
        raise RuntimeError("CI cargo-deny cache/install directory is a symlink")
    archive = cache_dir / "cargo-deny.tar.gz"
    if archive.is_symlink():
        raise RuntimeError("CI cargo-deny cache archive is a symlink")
    cache_hit = _verified_archive(archive)
    if not cache_hit:
        # The official metadata is checked *before* downloading and an exact
        # digest is checked *afterwards*, including partial transfer failures.
        _check_metadata(_gh_api("application/vnd.github+json"))
        with tempfile.TemporaryDirectory(prefix=".cargo-deny-download-", dir=cache_dir) as td:
            candidate = Path(td) / "asset.tar.gz"
            _gh_api("application/octet-stream", destination=candidate)
            if not _verified_archive(candidate):
                raise RuntimeError("CI cargo-deny downloaded archive failed SHA-256/size verification")
            os.replace(candidate, archive)
    # Never use extractall: select only the exact binary from a verified tarball.
    with tarfile.open(archive, "r:gz") as contents:
        member = contents.getmember(MEMBER)
        if not member.isfile():
            raise RuntimeError("CI cargo-deny archive executable member is not a file")
        stream = contents.extractfile(member)
        if stream is None:
            raise RuntimeError("CI cargo-deny archive executable member is unavailable")
        with tempfile.TemporaryDirectory(prefix=".cargo-deny-bin-", dir=bin_dir) as td:
            candidate = Path(td) / "cargo-deny"
            with candidate.open("wb") as output:
                shutil.copyfileobj(stream, output)
            candidate.chmod(0o755)
            result = subprocess.run(
                [str(candidate), "--version"],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if result.returncode != 0 or result.stdout.strip() != f"cargo-deny {VERSION}":
                raise RuntimeError("CI cargo-deny executable/version check failed")
            os.replace(candidate, bin_dir / "cargo-deny")
    return "verified-cache-hit" if cache_hit else "verified-api-download"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--bin-dir", type=Path, required=True)
    args = parser.parse_args()
    print(f"cargo-deny {VERSION}: {install(args.cache_dir, args.bin_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
