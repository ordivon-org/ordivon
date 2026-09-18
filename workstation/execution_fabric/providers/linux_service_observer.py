#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess

CONTROL_PLANE_UNITS = (
    "ordivon-runtime.service",
    "ordivon-host-v2.service",
)


def unit_state(unit: str) -> str:
    completed = subprocess.run(
        ["/usr/bin/systemctl", "is-active", unit],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    state = completed.stdout.strip()
    return state or "unknown"


def probe_control_plane() -> dict:
    units = {unit: unit_state(unit) for unit in CONTROL_PLANE_UNITS}
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.linux-service-observer",
        "providerId": "provider/linux-local/service-observer-v1",
        "capabilities": ["capability/service/probe"],
        "units": units,
        "healthy": all(state == "active" for state in units.values()),
        "mutationAttempted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("probe-control-plane",))
    args = parser.parse_args()
    if args.command == "probe-control-plane":
        print(json.dumps(probe_control_plane(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
