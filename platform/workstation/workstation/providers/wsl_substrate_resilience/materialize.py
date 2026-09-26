#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

SOURCE = Path(__file__).with_name("wsl_substrate_resilience.py")
ROOT = Path("/usr/local/libexec/ordivon/workstation-v2/wsl-substrate-resilience")
RECEIPT = Path("/var/lib/ordivon/workstation/providers/receipts/wsl-substrate-resilience-r1.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def materialize() -> dict:
    source_digest = digest(SOURCE)
    target = ROOT / source_digest / SOURCE.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if digest(target) != source_digest:
            raise RuntimeError("existing WSL substrate provider bytes differ from source digest")
    else:
        shutil.copyfile(SOURCE, target)
        target.chmod(0o755)
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.wsl-substrate-resilience-materialization",
        "sourceSha256": "sha256:" + source_digest,
        "target": str(target),
        "targetSha256": "sha256:" + digest(target),
        "mutationCapabilities": ["compact_memory"],
        "forbiddenRoutineEffects": ["drop_caches", "persistent_sysctl_tuning"],
    }
    atomic_json(RECEIPT, payload)
    return payload


def status() -> dict:
    source_digest = digest(SOURCE)
    target = ROOT / source_digest / SOURCE.name
    return {
        "schemaVersion": 1,
        "sourceSha256": "sha256:" + source_digest,
        "target": str(target),
        "present": target.is_file(),
        "matches": target.is_file() and digest(target) == source_digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("materialize", "status"))
    args = parser.parse_args()
    print(json.dumps(materialize() if args.command == "materialize" else status(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
