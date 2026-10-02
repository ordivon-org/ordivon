#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

SOURCE = Path(__file__).with_name("RealChromeUserSessionProvider.ps1")
ROOT = Path("/mnt/c/ProgramData/Ordivon/Workstation/Providers/RealChromeUserSessionProvider")
RECEIPT = Path("/mnt/c/ProgramData/Ordivon/Workstation/Providers/receipts/real-chrome-user-session-provider.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize() -> dict:
    source_digest = digest(SOURCE)
    target = ROOT / source_digest / SOURCE.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if digest(target) != source_digest:
            raise RuntimeError("existing real-Chrome user-session provider bytes differ from source digest")
    else:
        shutil.copyfile(SOURCE, target)
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.real-chrome-user-session-provider-materialization",
        "sourceSha256": "sha256:" + source_digest,
        "target": str(target),
        "targetSha256": "sha256:" + digest(target),
        "activationAttempted": False,
        "browserControlAuthorityGranted": False,
        "providerEffectAuthorized": False,
    }
    tmp = RECEIPT.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(RECEIPT)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("materialize", "status"))
    args = parser.parse_args()
    if args.command == "materialize":
        payload = materialize()
    else:
        source_digest = digest(SOURCE)
        target = ROOT / source_digest / SOURCE.name
        payload = {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.real-chrome-user-session-provider-status",
            "sourceSha256": "sha256:" + source_digest,
            "target": str(target),
            "present": target.is_file(),
            "matches": target.is_file() and digest(target) == source_digest,
            "activationAttempted": False,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
