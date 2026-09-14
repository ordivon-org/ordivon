#!/usr/bin/env python3
"""Prepare one Xauthority file for a pinned Browserless headful carrier.

The X11 server remains mature Xvfb authority. This helper only creates a fresh
MIT-MAGIC-COOKIE-1 credential with a FamilyWild duplicate so the bind-mounted
Unix display remains usable across the Browserless container hostname boundary.
It never prints cookie bytes.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

XAUTH_ROOT = Path("/run/ordivon/browserless-xauth")
BROWSERLESS_UID = 999
BROWSERLESS_GID = 999


def validate_instance(raw: str | int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as error:
        raise ValueError("Browserless display instance must be an integer") from error
    if value not in {11, 12, 13, 21}:
        raise ValueError("Browserless display instance must be 11, 12, 13, or 21")
    return value


def display_number(instance: int) -> int:
    return 100 + validate_instance(instance)


def authority_path(instance: int) -> Path:
    return XAUTH_ROOT / str(validate_instance(instance))


def run(args: list[str], *, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        args, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )


def prepare(instance: int) -> dict:
    instance = validate_instance(instance)
    display = display_number(instance)
    XAUTH_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(XAUTH_ROOT, 0o700)
    destination = authority_path(instance)
    cookie = run(["/usr/bin/mcookie"]).stdout.strip()
    if len(cookie) != 32:
        raise RuntimeError("mcookie returned an unexpected credential shape")
    with tempfile.TemporaryDirectory(dir=XAUTH_ROOT) as raw:
        root = Path(raw)
        local = root / "authority"
        numeric = root / "nlist"
        local.touch(mode=0o600)
        run(["/usr/bin/xauth", "-f", str(local), "add", f":{display}", ".", cookie.decode("ascii")])
        numeric.write_bytes(
            run(["/usr/bin/xauth", "-f", str(local), "nlist", f":{display}"]).stdout
        )
        rows = []
        for line in numeric.read_text(encoding="ascii").splitlines():
            if not line.strip():
                continue
            rows.append("ffff" + line[4:])
        if not rows:
            raise RuntimeError("xauth produced no numeric authority entry")
        run(
            ["/usr/bin/xauth", "-f", str(local), "nmerge", "-"],
            input_bytes=("\n".join(rows) + "\n").encode("ascii"),
        )
        raw = local.read_bytes()
        destination.write_bytes(raw)
        os.chown(destination, BROWSERLESS_UID, BROWSERLESS_GID)
        os.chmod(destination, 0o400)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-x11-authority-materialization",
        "instance": instance,
        "display": f":{display}",
        "path": str(destination),
        "mode": "0400",
        "ownerUid": BROWSERLESS_UID,
        "ownerGid": BROWSERLESS_GID,
        "credentialExposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", required=True)
    args = parser.parse_args()
    try:
        value = prepare(validate_instance(args.instance))
        import json

        print(json.dumps(value, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"browserless-display-auth: {exc}", file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
