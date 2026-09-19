#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess

RUNTIME_STATUS = "/usr/local/libexec/ordivon/ordivon-runtime-status"
RUNTIME_DOCTOR = "/usr/local/libexec/ordivon/ordivon-runtime-doctor"
REGISTRY_DB = "/var/lib/ordivon/registry/registry.sqlite3"
STORE_ROOT = "/var/lib/ordivon/runtime"


def _json_command(argv: list[str]) -> dict:
    completed = subprocess.run(
        argv,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def health() -> dict:
    return _json_command([RUNTIME_STATUS, "--health", "--json"])


def doctor() -> dict:
    return _json_command(
        [
            RUNTIME_DOCTOR,
            "inspect",
            "--database",
            REGISTRY_DB,
            "--store-root",
            STORE_ROOT,
            "--pretty",
        ]
    )


def status() -> dict:
    health_result = health()
    doctor_result = doctor()
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.runtime-control-provider-status",
        "providerId": "provider/linux-local/runtime-control-observer-v1",
        "capabilities": [
            "capability/runtime/doctor",
            "capability/runtime/health",
        ],
        "healthy": (
            health_result.get("status") == "healthy"
            and doctor_result.get("integrityCheck") == "ok"
            and doctor_result.get("violationCount") == 0
        ),
        "runtimeHealth": health_result,
        "runtimeDoctor": doctor_result,
        "mutationAttempted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("health", "doctor", "status"))
    args = parser.parse_args()
    payload = {"health": health, "doctor": doctor, "status": status}[args.command]()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
