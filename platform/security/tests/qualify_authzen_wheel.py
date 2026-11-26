"""Opt-in qualification of a locally built wheel's source content.

This does not establish installed, running, or authenticated release identity.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "platform/security/services/gateway-authzen/src/"
PACKAGE = "ordivon_security_gateway_authzen/"


def check_package_sources(wheel: Path, expected: dict[str, bytes]) -> int:
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive member")
        actual = {
            name: archive.read(name)
            for name in names
            if name.startswith(PACKAGE) and not name.endswith("/")
        }
    if set(actual) != set(expected):
        raise ValueError("package source inventory mismatch")
    if any(actual[name] != data for name, data in expected.items()):
        raise ValueError("package source bytes mismatch")
    return len(actual)


def main():
    wheel = Path(sys.argv[1])
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
    ).strip()
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "-z", revision, "--", SOURCE + PACKAGE],
        cwd=ROOT,
    ).decode().split("\0")
    expected = {
        path.removeprefix(SOURCE): subprocess.check_output(
            ["git", "show", f"{revision}:{path}"], cwd=ROOT,
        )
        for path in paths if path
    }
    if not expected:
        raise ValueError("no package source inventory in revision")
    count = check_package_sources(wheel, expected)
    print("SOURCE_REVISION", revision)
    print("WHEEL_SOURCE_FILES", count, "EXACT")
    print("WHEEL_SHA256", hashlib.sha256(wheel.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
