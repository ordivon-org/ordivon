#!/usr/bin/env python3
"""Collect non-secret CF07 session/lifecycle metadata from production Browserless carriers.

The collector is intentionally metadata-only. It does not visit a provider, wake a sleeping carrier,
read cookie/history/profile contents, read prompt/turn/handoff/attempt receipt bodies, or select
request_json/detail/provider_coordinate from the SQLite birth ledger.

It observes:
- active/sleeping/container state;
- non-blocking carrier-lease availability;
- session COUNT only for an already-active carrier while holding its lease;
- last-use timestamp age;
- profile-root filesystem stat ages only;
- aggregate carrier-binding/receipt file counts and file-age ranges;
- aggregate SQLite standing/timing/effect-generation statistics.

No provider effect and no SEND.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import math
import re
import sqlite3
import statistics
import subprocess
import sys
import time
from pathlib import Path

HARNESS_CURRENT = Path(
    os.environ.get("ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT", "/opt/ordivon/agent-automation/current")
)
HARNESS_SCRIPTS = HARNESS_CURRENT / "scripts"
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from agent_automation_browserless import (  # noqa: E402
    BrowserlessAutomationConfig,
    BrowserlessCarrierBusy,
    _carrier_last_use_path,
    _carrier_lease,
    _read_json,
)
from browserless_idle_reaper import _human_transport_active  # noqa: E402

CONFIG = Path("/etc/ordivon/agent-automation-browserless.json")
HOST_PROFILE_ROOT = Path("/var/lib/ordivon/browserless")
PRODUCTION_ENDPOINT_RE = re.compile(r"^chatgpt-carrier-(11|12|13)$")
SERVICE_INSTANCE_RE = re.compile(r"^ordivon-browserless@(11|12|13)\.service$")
WINDOWS_SECONDS = {
    "1h": 3600,
    "6h": 6 * 3600,
    "24h": 24 * 3600,
    "72h": 72 * 3600,
}
FORBIDDEN_DATA_CLASSES = (
    "cookie values",
    "browser history contents",
    "saved credentials/tokens",
    "prompt text",
    "turn text",
    "handoff URLs",
    "attempt receipt bodies",
    "SQLite request_json",
    "SQLite detail",
    "SQLite provider_coordinate",
    "provider page content",
)


def _age(now: float, timestamp: float) -> int | None:
    value = now - timestamp
    if value < 0:
        return None
    return int(value)


def _active(unit: str) -> bool:
    return (
        subprocess.run(
            ["/usr/bin/systemctl", "is-active", "--quiet", unit],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        ).returncode
        == 0
    )


def _container_exists(name: str) -> bool:
    return (
        subprocess.run(
            ["/usr/bin/podman", "container", "exists", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        ).returncode
        == 0
    )


def _profile_metadata(instance: int, *, now: float) -> dict[str, object]:
    root = HOST_PROFILE_ROOT / str(instance)
    if not root.is_dir():
        return {
            "exists": False,
            "rootMtimeAgeSeconds": None,
            "rootCtimeAgeSeconds": None,
            "defaultDirectoryExists": False,
            "defaultDirectoryMtimeAgeSeconds": None,
            "semanticCreationAgeKnown": False,
        }
    stat = root.stat()
    default = root / "Default"
    default_stat = default.stat() if default.is_dir() else None
    return {
        "exists": True,
        "rootMtimeAgeSeconds": _age(now, stat.st_mtime),
        "rootCtimeAgeSeconds": _age(now, stat.st_ctime),
        "defaultDirectoryExists": default_stat is not None,
        "defaultDirectoryMtimeAgeSeconds": (
            _age(now, default_stat.st_mtime) if default_stat is not None else None
        ),
        # POSIX ctime is metadata-change time, not creation time.
        "semanticCreationAgeKnown": False,
    }


def _file_age_summary(paths: list[Path], *, now: float) -> dict[str, object]:
    ages = sorted(
        age
        for path in paths
        if path.is_file() and (age := _age(now, path.stat().st_mtime)) is not None
    )
    if not ages:
        return {
            "count": 0,
            "newestAgeSeconds": None,
            "oldestAgeSeconds": None,
        }
    return {
        "count": len(ages),
        "newestAgeSeconds": ages[0],
        "oldestAgeSeconds": ages[-1],
    }


def _occurrence_aggregates(
    state_root: Path, endpoint_ids: set[str], *, now: float
) -> dict[str, dict[str, object]]:
    out = {
        endpoint_id: {
            "boundOccurrenceCount": 0,
            "bindingFiles": [],
            "preEffectFiles": [],
            "attemptFiles": [],
            "humanHandoffFiles": [],
            "turnFiles": [],
        }
        for endpoint_id in sorted(endpoint_ids)
    }
    occurrences = state_root / "occurrences"
    if not occurrences.is_dir():
        return {
            endpoint_id: {
                "boundOccurrenceCount": 0,
                "bindingFileAges": _file_age_summary([], now=now),
                "preEffectReceiptAges": _file_age_summary([], now=now),
                "attemptReceiptAges": _file_age_summary([], now=now),
                "humanHandoffReceiptAges": _file_age_summary([], now=now),
                "turnReceiptAges": _file_age_summary([], now=now),
            }
            for endpoint_id in sorted(endpoint_ids)
        }

    for occurrence in occurrences.iterdir():
        if not occurrence.is_dir():
            continue
        binding = occurrence / "carrier-binding.json"
        if not binding.is_file():
            continue
        # carrier-binding contains only effectId, endpointId, endpointIdentityDigest.
        # We intentionally retain only endpointId and discard the identities.
        try:
            value = json.loads(binding.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        endpoint_id = value.get("endpointId")
        if endpoint_id not in out:
            continue
        row = out[endpoint_id]
        row["boundOccurrenceCount"] += 1
        row["bindingFiles"].append(binding)
        for key, directory in (
            ("preEffectFiles", "pre-effect"),
            ("attemptFiles", "attempts"),
            ("humanHandoffFiles", "human-handoff"),
            ("turnFiles", "turns"),
        ):
            folder = occurrence / directory
            if folder.is_dir():
                row[key].extend(path for path in folder.iterdir() if path.is_file())

    result: dict[str, dict[str, object]] = {}
    for endpoint_id, row in out.items():
        result[endpoint_id] = {
            "boundOccurrenceCount": row["boundOccurrenceCount"],
            "bindingFileAges": _file_age_summary(row["bindingFiles"], now=now),
            "preEffectReceiptAges": _file_age_summary(row["preEffectFiles"], now=now),
            "attemptReceiptAges": _file_age_summary(row["attemptFiles"], now=now),
            "humanHandoffReceiptAges": _file_age_summary(
                row["humanHandoffFiles"], now=now
            ),
            "turnReceiptAges": _file_age_summary(row["turnFiles"], now=now),
        }
    return result


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    index = (len(values) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[lower]
    weight = index - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def _ledger_aggregate(path: Path, *, now_ms: int) -> dict[str, object]:
    if not path.is_file():
        return {
            "available": False,
            "totalRequests": 0,
            "standingCounts": {},
        }
    # mode=ro plus a narrow SELECT ensures request_json/detail/provider_coordinate are not read.
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    try:
        rows = db.execute(
            "SELECT standing,effect_generation,created_at_ms,updated_at_ms "
            "FROM requests ORDER BY created_at_ms"
        ).fetchall()
    finally:
        db.close()
    standings = collections.Counter(str(row[0]) for row in rows)
    created = [int(row[2]) for row in rows]
    updated = [int(row[3]) for row in rows]
    generations = [int(row[1]) for row in rows]
    intervals = sorted(
        (created[index] - created[index - 1]) / 1000
        for index in range(1, len(created))
        if created[index] >= created[index - 1]
    )
    recent_created = {
        label: sum(now_ms - value <= seconds * 1000 for value in created)
        for label, seconds in WINDOWS_SECONDS.items()
    }
    recent_updated = {
        label: sum(now_ms - value <= seconds * 1000 for value in updated)
        for label, seconds in WINDOWS_SECONDS.items()
    }
    return {
        "available": True,
        "totalRequests": len(rows),
        "standingCounts": dict(sorted(standings.items())),
        "effectGeneration": {
            "max": max(generations) if generations else None,
            "mean": round(statistics.fmean(generations), 4) if generations else None,
            "zeroCount": sum(value == 0 for value in generations),
            "nonZeroCount": sum(value != 0 for value in generations),
        },
        "requestAgeSeconds": {
            "oldest": (
                int((now_ms - min(created)) / 1000) if created else None
            ),
            "newest": (
                int((now_ms - max(created)) / 1000) if created else None
            ),
            "newestUpdate": (
                int((now_ms - max(updated)) / 1000) if updated else None
            ),
        },
        "createdWithin": recent_created,
        "updatedWithin": recent_updated,
        "createdInterarrivalSeconds": {
            "count": len(intervals),
            "min": round(intervals[0], 3) if intervals else None,
            "median": round(statistics.median(intervals), 3) if intervals else None,
            "p90": (
                round(value, 3)
                if (value := _percentile(intervals, 0.9)) is not None
                else None
            ),
            "max": round(intervals[-1], 3) if intervals else None,
        },
        "selectedColumns": [
            "standing",
            "effect_generation",
            "created_at_ms",
            "updated_at_ms",
        ],
    }


def _carrier_snapshot(
    config: BrowserlessAutomationConfig,
    endpoint,
    occurrence: dict[str, object],
    *,
    now: float,
) -> dict[str, object]:
    match = PRODUCTION_ENDPOINT_RE.fullmatch(endpoint.endpoint_id)
    if match is None:
        raise RuntimeError(f"unexpected production endpoint id: {endpoint.endpoint_id}")
    instance = int(match.group(1))
    unit = endpoint.service_unit
    if not isinstance(unit, str) or SERVICE_INSTANCE_RE.fullmatch(unit) is None:
        raise RuntimeError(f"unexpected production service unit: {unit}")
    active = _active(unit)
    container_exists = _container_exists(f"ordivon-browserless-{instance}")
    if active != container_exists:
        lifecycle_consistency = "AMBIGUOUS"
    else:
        lifecycle_consistency = "CONSISTENT"

    stamp = _carrier_last_use_path(config, endpoint.endpoint_id)
    last_use_age = _age(now, stamp.stat().st_mtime) if stamp.is_file() else None

    lease = "AVAILABLE"
    session_count: int | None = None
    session_observation = "NOT_NEEDED_SLEEPING"
    if active:
        try:
            with _carrier_lease(config, endpoint.endpoint_id, blocking=False):
                lease = "AVAILABLE"
                try:
                    sessions = endpoint.sessions(timeout_seconds=3)
                    session_count = len(sessions)
                    session_observation = "OBSERVED_COUNT_ONLY"
                except Exception as error:
                    session_observation = f"UNAVAILABLE:{type(error).__name__}"
        except BrowserlessCarrierBusy:
            lease = "BUSY"
            session_observation = "SUPPRESSED_LEASE_BUSY"

    return {
        "endpointId": endpoint.endpoint_id,
        "managedServiceUnit": unit,
        "warmFloor": endpoint.endpoint_id in set(config.browserless_warm_endpoint_ids),
        "active": active,
        "containerExists": container_exists,
        "lifecycleConsistency": lifecycle_consistency,
        "leaseStanding": lease,
        "sessionCount": session_count,
        "sessionObservation": session_observation,
        "humanTransportActive": _human_transport_active(unit),
        "lastUse": {
            "stampExists": stamp.is_file(),
            "ageSeconds": last_use_age,
            "idleTtlSeconds": config.browserless_idle_ttl_seconds,
            "olderThanIdleTtl": (
                last_use_age >= config.browserless_idle_ttl_seconds
                if last_use_age is not None
                else None
            ),
        },
        "profileFilesystemMetadata": _profile_metadata(instance, now=now),
        "occurrenceMetadata": occurrence,
    }


def collect() -> dict[str, object]:
    now = time.time()
    now_ms = int(now * 1000)
    config = BrowserlessAutomationConfig.from_dict(_read_json(CONFIG))
    endpoints = tuple(
        endpoint
        for endpoint in config.browserless_pool.endpoints
        if PRODUCTION_ENDPOINT_RE.fullmatch(endpoint.endpoint_id)
    )
    endpoint_ids = {endpoint.endpoint_id for endpoint in endpoints}
    if endpoint_ids != {
        "chatgpt-carrier-11",
        "chatgpt-carrier-12",
        "chatgpt-carrier-13",
    }:
        raise RuntimeError("production carrier set is not exact 11/12/13")

    occurrences = _occurrence_aggregates(config.state_root, endpoint_ids, now=now)
    carriers = [
        _carrier_snapshot(config, endpoint, occurrences[endpoint.endpoint_id], now=now)
        for endpoint in sorted(endpoints, key=lambda row: row.endpoint_id)
    ]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-cf07-metadata-r4",
        "standing": "NON_SECRET_METADATA_SNAPSHOT",
        "snapshotNowMs": now_ms,
        "harnessRevision": json.loads(
            (HARNESS_CURRENT / ".ordivon-agent-automation-release.json").read_text(
                encoding="utf-8"
            )
        )["commit"],
        "privacyBoundary": {
            "metadataOnly": True,
            "providerVisited": False,
            "providerEffectAttempted": False,
            "providerSendAttempted": False,
            "sleepingCarrierWoken": False,
            "forbiddenDataClassesRead": [],
            "forbiddenDataClasses": list(FORBIDDEN_DATA_CLASSES),
        },
        "carrierPolicy": {
            "idleTtlSeconds": config.browserless_idle_ttl_seconds,
            "warmEndpointIds": list(config.browserless_warm_endpoint_ids),
        },
        "carriers": carriers,
        "birthLedgerAggregate": _ledger_aggregate(config.ledger, now_ms=now_ms),
        "interpretationGuard": {
            "profileFilesystemTimesAreNotSemanticCreationTimes": True,
            "lastUseStampIsLifecycleUseNotProviderSessionCreation": True,
            "requestCadenceIsAggregateAgentAutomationCadenceNotProviderBehavior": True,
            "providerCausalityEstablished": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "standing": value["standing"],
                "carriers": [
                    {
                        "endpointId": row["endpointId"],
                        "active": row["active"],
                        "leaseStanding": row["leaseStanding"],
                        "sessionCount": row["sessionCount"],
                        "lastUseAgeSeconds": row["lastUse"]["ageSeconds"],
                        "boundOccurrenceCount": row["occurrenceMetadata"][
                            "boundOccurrenceCount"
                        ],
                    }
                    for row in value["carriers"]
                ],
                "birthLedgerAggregate": value["birthLedgerAggregate"],
                "privacyBoundary": value["privacyBoundary"],
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
