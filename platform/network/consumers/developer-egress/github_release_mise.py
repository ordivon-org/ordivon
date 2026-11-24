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


# Official standalone Python bundle reused by native mise core backend.
PYTHON_REPO = "astral-sh/python-build-standalone"
PYTHON_ASSET_ID = 663549456
PYTHON_ASSET_NAME = (
    "cpython-3.15.1+20261021-x86_64-unknown-linux-gnu-"
    "install_only_stripped.tar.gz"
)
PYTHON_ASSET_SIZE = 38075450
PYTHON_ASSET_SHA256 = "01d901e09ca673c99a6c9bd9ec2cfbd58dbe8813d07514c36cb73cfd20b18bd8"
PYTHON_EXECUTABLE_SHA256 = "00e3569b62ae453b0e9000b9a0957f210a2d1de0fad7c439cabd61360ea87228"


def provision_python() -> Path:
    """Place the exact verified upstream distribution in mise's own install prefix."""
    target = mise_dir() / "installs" / "python" / "3.15.1"
    interpreter = target / "bin" / "python3.15"
    if interpreter.is_file():
        if (
            file_sha256(interpreter) != PYTHON_EXECUTABLE_SHA256
            or not (target / "bin" / "python").is_symlink()
            or (target / "bin" / "python").resolve() != interpreter
        ):
            raise ValueError("cached Python executable does not match pinned upstream")
        version = subprocess.run(
            [str(interpreter), "--version"], capture_output=True, check=True,
            text=True, timeout=12,
        ).stdout.strip()
        if version == "Python 3.15.1":
            print("NETWORK_GH_API_PYTHON_REUSED", version)
            return target
        raise ValueError("existing mise python version mismatches pinned release")

    response = subprocess.run(
        ["gh", "api", f"repos/{PYTHON_REPO}/releases/assets/{PYTHON_ASSET_ID}"],
        check=True, capture_output=True, text=True, timeout=35,
    )
    row = json.loads(response.stdout)
    if (
        row.get("id") != PYTHON_ASSET_ID
        or row.get("name") != PYTHON_ASSET_NAME
        or row.get("size") != PYTHON_ASSET_SIZE
        or row.get("digest") != "sha256:" + PYTHON_ASSET_SHA256
        or row.get("state") != "uploaded"
    ):
        raise ValueError("official Python release metadata disagrees with pin")

    with tempfile.TemporaryDirectory(prefix="ordivon-ci-python-") as tmp:
        root = Path(tmp)
        archive = root / PYTHON_ASSET_NAME
        for attempt in range(1, 4):
            try:
                with archive.open("wb") as out:
                    subprocess.run(
                        ["gh", "api", "-H", "Accept: application/octet-stream",
                         f"repos/{PYTHON_REPO}/releases/assets/{PYTHON_ASSET_ID}"],
                        stdout=out, check=True, timeout=150,
                    )
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if attempt == 3:
                    raise
                time.sleep(attempt)
        if (
            archive.stat().st_size != PYTHON_ASSET_SIZE
            or file_sha256(archive) != PYTHON_ASSET_SHA256
        ):
            raise ValueError("official Python release asset partial or digest mismatched")
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = target.parent / f".python-3.15.1-{os.getpid()}.new"
        staging.mkdir(parents=True, exist_ok=False)
        try:
            subprocess.run(
                ["tar", "-xzf", str(archive), "--strip-components=1",
                 "--no-same-owner", "-C", str(staging)],
                check=True, timeout=90,
            )
            staged_interpreter = staging / "bin" / "python3.15"
            if (
                not staged_interpreter.is_file()
                or file_sha256(staged_interpreter) != PYTHON_EXECUTABLE_SHA256
            ):
                raise ValueError("Python executable fails pinned upstream digest")
            version = subprocess.run(
                [str(staged_interpreter), "--version"], capture_output=True,
                text=True, check=True, timeout=12,
            ).stdout.strip()
            if version != "Python 3.15.1":
                raise ValueError("Python interpreter does not satisfy mise pin")
            if target.exists():
                raise ValueError("concurrent mise Python materialization detected")
            os.replace(staging, target)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    print("NETWORK_GH_API_PYTHON_VERIFIED", "3.15.1", PYTHON_ASSET_SIZE)
    return target


if __name__ == "__main__":
    try:
        if sys.argv[1:] == ["--python"]:
            provision_python()
        elif len(sys.argv) == 1:
            provision()
        else:
            raise ValueError("usage: github_release_mise.py [--python]")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print("NETWORK_GH_API_MISE_NOT_VERIFIED", type(error).__name__, file=sys.stderr)
        raise SystemExit(1) from error
