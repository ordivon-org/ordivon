#!/usr/bin/env python3
"""Create one private Xauthority file for a durable CfT human-session slot."""

from __future__ import annotations

import argparse
import os
import pwd
import subprocess
import tempfile
from pathlib import Path

ROOT = Path("/run/ordivon/cft-human-xauth")
SLOTS = frozenset(range(41, 49))


def slot_value(raw: str | int) -> int:
    value = int(raw)
    if value not in SLOTS:
        raise ValueError("CfT human-session slot must be 41..48")
    return value


def run(
    args: list[str], *, input_bytes: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        args,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def prepare(slot: str | int) -> dict:
    slot = slot_value(slot)
    display = 200 + slot
    ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(ROOT, 0o700)
    account = pwd.getpwnam("ordivon")
    destination = ROOT / str(slot)
    cookie = run(["/usr/bin/mcookie"]).stdout.strip()
    if len(cookie) != 32:
        raise RuntimeError("mcookie returned unexpected credential shape")
    with tempfile.TemporaryDirectory(dir=ROOT) as raw:
        local = Path(raw) / "authority"
        local.touch(mode=0o600)
        run(
            [
                "/usr/bin/xauth",
                "-f",
                str(local),
                "add",
                f":{display}",
                ".",
                cookie.decode("ascii"),
            ]
        )
        destination.write_bytes(local.read_bytes())
    os.chown(destination, account.pw_uid, account.pw_gid)
    os.chmod(destination, 0o400)
    return {
        "slot": slot,
        "display": f":{display}",
        "path": str(destination),
        "credentialExposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", required=True)
    args = parser.parse_args()
    try:
        prepare(args.slot)
        return 0
    except Exception as error:
        print(f"cft-human-session-auth: {error}", file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
