#!/usr/bin/env python3
"""Conservatively reclaim idle managed Browserless carriers.

The existing carrier flock is the concurrency boundary. Any uncertainty is a skip: the reaper
never guesses that an interactive carrier is safe to stop. Warm-floor endpoints are never reaped.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path

try:
    from agent_automation_browserless import (
        BrowserlessAutomationConfig,
        BrowserlessAutomationService,
        BrowserlessCarrierBusy,
        _carrier_last_use_path,
        _carrier_lease,
        _touch_carrier_last_use,
    )
except ImportError:  # pragma: no cover
    from scripts.agent_automation_browserless import (
        BrowserlessAutomationConfig,
        BrowserlessAutomationService,
        BrowserlessCarrierBusy,
        _carrier_last_use_path,
        _carrier_lease,
        _touch_carrier_last_use,
    )

_INSTANCE_RE = re.compile(r"@(?P<instance>[0-9]+)\.service$")


def _active(unit: str) -> bool:
    return subprocess.run(
        ["/usr/bin/systemctl", "is-active", "--quiet", unit],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    ).returncode == 0


def _human_transport_active(service_unit: str) -> bool:
    match = _INSTANCE_RE.search(service_unit)
    if match is None:
        return True
    instance = match.group("instance")
    return any(
        _active(f"ordivon-browserless-human-{kind}@{instance}.service")
        for kind in ("vnc", "web")
    )


def _stop(unit: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["/usr/bin/systemctl", "stop", unit],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def reap_once(service: BrowserlessAutomationService, *, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    rows: list[dict] = []
    warm = set(service.config.browserless_warm_endpoint_ids)
    ttl = service.config.browserless_idle_ttl_seconds
    for endpoint in service.config.browserless_pool.endpoints:
        unit = getattr(endpoint, "service_unit", None)
        row = {"endpointId": endpoint.endpoint_id, "serviceUnit": unit}
        if not isinstance(unit, str) or not unit:
            row["standing"] = "SKIP_UNMANAGED"
            rows.append(row)
            continue
        if endpoint.endpoint_id in warm:
            row["standing"] = "SKIP_WARM_FLOOR"
            rows.append(row)
            continue
        if not _active(unit):
            row["standing"] = "ALREADY_COLD"
            rows.append(row)
            continue
        stamp = _carrier_last_use_path(service.config, endpoint.endpoint_id)
        if not stamp.is_file():
            _touch_carrier_last_use(service.config, endpoint.endpoint_id)
            row["standing"] = "SKIP_GRACE_STARTED"
            rows.append(row)
            continue
        age = now - stamp.stat().st_mtime
        if age < 0:
            row["standing"] = "SKIP_CLOCK_UNCERTAIN"
            rows.append(row)
            continue
        if age < ttl:
            row.update({"standing": "SKIP_RECENT_USE", "idleSeconds": int(age)})
            rows.append(row)
            continue
        try:
            with _carrier_lease(service.config, endpoint.endpoint_id, blocking=False):
                if not stamp.is_file():
                    _touch_carrier_last_use(service.config, endpoint.endpoint_id)
                    row["standing"] = "SKIP_GRACE_STARTED"
                    rows.append(row)
                    continue
                locked_age = now - stamp.stat().st_mtime
                if locked_age < 0:
                    row["standing"] = "SKIP_CLOCK_UNCERTAIN"
                    rows.append(row)
                    continue
                if locked_age < ttl:
                    row.update({"standing": "SKIP_RECENT_USE", "idleSeconds": int(locked_age)})
                    rows.append(row)
                    continue
                try:
                    sessions = endpoint.sessions(timeout_seconds=3)
                except Exception as error:
                    row.update(
                        {
                            "standing": "SKIP_SESSION_OBSERVATION_FAILED",
                            "detail": type(error).__name__,
                        }
                    )
                    rows.append(row)
                    continue
                if sessions:
                    row.update(
                        {"standing": "SKIP_ACTIVE_SESSION", "sessionCount": len(sessions)}
                    )
                    rows.append(row)
                    continue
                if _human_transport_active(unit):
                    row["standing"] = "SKIP_HUMAN_HANDOFF"
                    rows.append(row)
                    continue
                proc = _stop(unit)
                if proc.returncode != 0:
                    row.update({"standing": "STOP_FAILED", "returnCode": proc.returncode})
                else:
                    row.update({"standing": "REAPED", "idleSeconds": int(locked_age)})
                rows.append(row)
        except BrowserlessCarrierBusy:
            row["standing"] = "SKIP_LEASE_BUSY"
            rows.append(row)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-idle-reap",
        "ttlSeconds": ttl,
        "warmEndpointIds": list(service.config.browserless_warm_endpoint_ids),
        "carriers": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.config.read_text(encoding="utf-8"))
    service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(raw))
    print(json.dumps(reap_once(service), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
