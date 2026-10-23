#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = 1
RESOURCE_RECEIPT_SCHEMA_VERSION = 1
RESOURCE_RECEIPT_SCOPE = "attempt_cgroup_including_runner"
RESOURCE_RECEIPT_PROVIDER = "linux_cgroup_v2"


def _require_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _require_u64(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 2**64 - 1:
        raise ValueError(f"{field} must be an unsigned 64-bit integer")
    return value


def _candidate_receipt_name(path: Path) -> bool:
    name = path.name.lower()
    return path.suffix.lower() == ".json" and (
        "resource-receipt" in name or "resource_receipt" in name
    )


def discover_receipts(inputs: Iterable[Path], *, max_files: int) -> list[Path]:
    if max_files <= 0:
        raise ValueError("max-files must be positive")
    discovered: set[Path] = set()
    for raw in inputs:
        path = Path(raw)
        if path.is_file():
            discovered.add(path.resolve())
        elif path.is_dir():
            for candidate in path.rglob("*.json"):
                if _candidate_receipt_name(candidate):
                    discovered.add(candidate.resolve())
                    if len(discovered) > max_files:
                        raise ValueError(f"max-files bound exceeded: more than {max_files} receipt files")
        else:
            raise ValueError(f"input does not exist: {path}")
    ordered = sorted(discovered, key=lambda value: value.as_posix())
    if len(ordered) > max_files:
        raise ValueError(f"max-files bound exceeded: {len(ordered)} > {max_files}")
    if not ordered:
        raise ValueError("no resource receipt files discovered")
    return ordered


def _read_receipt(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid receipt {path}: {error}") from error
    receipt = _require_mapping(payload, str(path))

    if receipt.get("schemaVersion") != RESOURCE_RECEIPT_SCHEMA_VERSION:
        raise ValueError(f"{path}: schemaVersion must equal {RESOURCE_RECEIPT_SCHEMA_VERSION}")
    task_id = _require_string(receipt.get("taskId"), f"{path}: taskId")
    _require_string(receipt.get("jobId"), f"{path}: jobId")
    attempt_id = _require_string(receipt.get("attemptId"), f"{path}: attemptId")
    if task_id != attempt_id:
        raise ValueError(f"{path}: taskId must match attemptId")
    launch_digest = _require_string(receipt.get("launchTokenDigest"), f"{path}: launchTokenDigest")
    if not launch_digest.startswith("sha256:") or len(launch_digest) != 71:
        raise ValueError(f"{path}: launchTokenDigest must be a sha256 digest")
    _require_u64(receipt.get("observedUnixMs"), f"{path}: observedUnixMs")
    if receipt.get("scope") != RESOURCE_RECEIPT_SCOPE:
        raise ValueError(f"{path}: scope must equal {RESOURCE_RECEIPT_SCOPE}")
    if receipt.get("provider") != RESOURCE_RECEIPT_PROVIDER:
        raise ValueError(f"{path}: provider must equal {RESOURCE_RECEIPT_PROVIDER}")

    cpu = _require_mapping(receipt.get("cpu"), f"{path}: cpu")
    for key in ("usageUsec", "userUsec", "systemUsec"):
        _require_u64(cpu.get(key), f"{path}: cpu.{key}")

    memory = _require_mapping(receipt.get("memory"), f"{path}: memory")
    _require_u64(memory.get("peakBytes"), f"{path}: memory.peakBytes")
    if "swapPeakBytes" in memory:
        _require_u64(memory.get("swapPeakBytes"), f"{path}: memory.swapPeakBytes")
    events = _require_mapping(memory.get("events"), f"{path}: memory.events")
    for key in ("low", "high", "max", "oom", "oomKill"):
        _require_u64(events.get(key), f"{path}: memory.events.{key}")

    io = _require_mapping(receipt.get("io"), f"{path}: io")
    for key in ("readBytes", "writeBytes", "readOps", "writeOps", "discardBytes", "discardOps"):
        _require_u64(io.get(key), f"{path}: io.{key}")
    return receipt


def _nearest_rank(values: list[int], percentile: int) -> int:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile / 100) * len(ordered)))
    return ordered[rank - 1]


def _percentiles(values: list[int]) -> dict[str, int]:
    return {
        "p50": _nearest_rank(values, 50),
        "p95": _nearest_rank(values, 95),
        "p99": _nearest_rank(values, 99),
    }


def build_profile(receipt_paths: Iterable[Path], expected_attempts: int | None) -> dict[str, object]:
    paths = sorted({Path(path).resolve() for path in receipt_paths}, key=lambda value: value.as_posix())
    if not paths:
        raise ValueError("at least one receipt is required")
    receipts = [_read_receipt(path) for path in paths]
    receipt_count = len(receipts)

    if expected_attempts is not None:
        if expected_attempts <= 0 or expected_attempts < receipt_count:
            raise ValueError("expected-attempts must be positive and not below receipt count")
        coverage: dict[str, object] = {
            "basis": "caller_supplied_expected_attempts",
            "expectedAttempts": expected_attempts,
            "receiptCount": receipt_count,
            "missingReceiptCount": expected_attempts - receipt_count,
            "basisPoints": (receipt_count * 10_000) // expected_attempts,
        }
    else:
        coverage = {
            "basis": "receipt_files_only",
            "expectedAttempts": None,
            "receiptCount": receipt_count,
            "missingReceiptCount": None,
            "basisPoints": None,
        }

    cpu_usage = [int(_require_mapping(receipt["cpu"], "cpu")["usageUsec"]) for receipt in receipts]
    memory_peak = [int(_require_mapping(receipt["memory"], "memory")["peakBytes"]) for receipt in receipts]
    read_bytes = [int(_require_mapping(receipt["io"], "io")["readBytes"]) for receipt in receipts]
    write_bytes = [int(_require_mapping(receipt["io"], "io")["writeBytes"]) for receipt in receipts]
    io_total = [read + write for read, write in zip(read_bytes, write_bytes, strict=True)]

    swap_values: list[int] = []
    for receipt in receipts:
        memory = _require_mapping(receipt["memory"], "memory")
        value = memory.get("swapPeakBytes")
        if value is not None:
            swap_values.append(int(value))

    observed = [int(receipt["observedUnixMs"]) for receipt in receipts]
    event_totals: Counter[str] = Counter()
    for receipt in receipts:
        events = _require_mapping(_require_mapping(receipt["memory"], "memory")["events"], "memory.events")
        for key in ("low", "high", "max", "oom", "oomKill"):
            event_totals[key] += int(events[key])

    return {
        "schemaVersion": SCHEMA_VERSION,
        "receiptCount": receipt_count,
        "coverage": coverage,
        "scope": RESOURCE_RECEIPT_SCOPE,
        "provider": RESOURCE_RECEIPT_PROVIDER,
        "observationWindowUnixMs": {"min": min(observed), "max": max(observed)},
        "cpuUsageUsec": _percentiles(cpu_usage),
        "memoryPeakBytes": _percentiles(memory_peak),
        "ioReadBytes": _percentiles(read_bytes),
        "ioWriteBytes": _percentiles(write_bytes),
        "ioTotalBytes": _percentiles(io_total),
        "swapPeakBytes": {
            "observedCount": len(swap_values),
            "missingCount": receipt_count - len(swap_values),
            "percentiles": _percentiles(swap_values) if swap_values else None,
        },
        "memoryEventTotals": dict(sorted(event_totals.items())),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic read-only workload profile from Runtime resource receipt artifacts."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="Receipt JSON files or directories to scan")
    parser.add_argument(
        "--expected-attempts",
        type=int,
        default=None,
        help="Caller-supplied terminal Attempt denominator for meaningful receipt coverage",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=10_000,
        help="Hard upper bound for discovered receipt files (default: 10000)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        paths = discover_receipts(args.inputs, max_files=args.max_files)
        profile = build_profile(paths, expected_attempts=args.expected_attempts)
    except ValueError as error:
        raise SystemExit(f"resource workload profile error: {error}") from error
    print(json.dumps(profile, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
