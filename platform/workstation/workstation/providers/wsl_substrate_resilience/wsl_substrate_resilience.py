#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

COMPACT_MEMORY = Path("/proc/sys/vm/compact_memory")
BUDDYINFO = Path("/proc/buddyinfo")
PAGETYPEINFO = Path("/proc/pagetypeinfo")
MEMINFO = Path("/proc/meminfo")
VMSTAT = Path("/proc/vmstat")
MEMORY_PSI = Path("/proc/pressure/memory")
SYSCTLS = {
    "compactionProactiveness": Path("/proc/sys/vm/compaction_proactiveness"),
    "extfragThreshold": Path("/proc/sys/vm/extfrag_threshold"),
    "defragMode": Path("/proc/sys/vm/defrag_mode"),
}
CONTROL_PLANE_UNITS = (
    "ordivon-runtime.service",
    "ordivon-host-v2.service",
    "ordivon-gateway.service",
)
KERNEL_LOOKBACK = "5 minutes ago"
KNOWN_CLASSES = (
    "HEALTHY",
    "F1_HIGH_ORDER_FRAGMENTATION",
    "F2_PINNED_VSOCK_RESOURCE",
    "F3_INTEROP_CHANNEL_DEAD",
    "F4_GENERAL_MEMORY_PRESSURE",
    "F5_HOST_CONTROL_PLANE",
    "UNKNOWN",
)


def _read(path: Path, limit: int = 131072) -> str:
    data = path.read_bytes()
    if len(data) > limit:
        data = data[-limit:]
    return data.decode("utf-8", errors="replace")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def object_digest(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def file_digest(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def parse_buddyinfo(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in text.splitlines():
        match = re.match(r"Node\s+(\d+),\s+zone\s+(\S+)\s+(.+)$", raw.strip())
        if not match:
            continue
        orders = [int(value) for value in match.group(3).split()]
        rows.append(
            {
                "node": int(match.group(1)),
                "zone": match.group(2),
                "freeBlocksByOrder": orders,
                "order7Blocks": orders[7] if len(orders) > 7 else None,
                "order7PlusBlocks": sum(orders[7:]) if len(orders) > 7 else None,
            }
        )
    return rows


def parse_meminfo(text: str) -> dict[str, int]:
    selected = {"MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached", "SwapTotal", "SwapFree"}
    result: dict[str, int] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key not in selected:
            continue
        token = value.strip().split()[0]
        if token.isdigit():
            result[key + "KiB"] = int(token)
    return result


def parse_vmstat(text: str) -> dict[str, int]:
    prefixes = ("compact_", "pgscan_", "pgsteal_", "oom_kill")
    result: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        if parts[0].startswith(prefixes):
            result[parts[0]] = int(parts[1])
    return result


def parse_psi(text: str) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        row: dict[str, float | int] = {}
        for item in parts[1:]:
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            row[key] = int(value) if key == "total" else float(value)
        result[parts[0]] = row
    return result


def kernel_evidence() -> dict[str, Any]:
    command = ["/usr/bin/dmesg", "--ctime", "--since", KERNEL_LOOKBACK, "--level=err,warn"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
        text = completed.stdout[-65536:]
        error = completed.stderr[-4096:]
        exit_code = completed.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        text = ""
        error = str(exc)
        exit_code = -1
    orders = [int(value) for value in re.findall(r"page allocation failure:.*?order:(\d+)", text)]
    lowered = text.lower()
    return {
        "command": command,
        "lookback": KERNEL_LOOKBACK,
        "exitCode": exit_code,
        "stderr": error,
        "excerpt": text,
        "pageAllocationFailureOrders": orders,
        "vmbusAllocRingObserved": "vmbus_alloc_ring" in text,
        "vmbusOpenObserved": "vmbus_open" in text,
        "hvPriChanObserved": "hv_pri_chan" in text,
        "vsockObserved": "vsock" in lowered,
        "utilAcceptVsockTimeoutObserved": "utilacceptvsock" in lowered and "failed 110" in lowered,
    }


def snapshot() -> dict[str, Any]:
    buddy_raw = _read(BUDDYINFO)
    pagetype_raw = _read(PAGETYPEINFO)
    psi_raw = _read(MEMORY_PSI)
    vmstat_raw = _read(VMSTAT)
    payload: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.wsl-substrate-linux-snapshot",
        "truthRole": "observation",
        "observedUnixMs": int(time.time() * 1000),
        "buddy": parse_buddyinfo(buddy_raw),
        "memory": parse_meminfo(_read(MEMINFO)),
        "vmstat": parse_vmstat(vmstat_raw),
        "memoryPsi": parse_psi(psi_raw),
        "sysctls": {name: _read(path, 4096).strip() for name, path in SYSCTLS.items()},
        "kernel": kernel_evidence(),
        "raw": {
            "buddyinfo": buddy_raw,
            "pagetypeinfo": pagetype_raw,
            "memoryPsi": psi_raw,
        },
    }
    payload["snapshotSha256"] = object_digest(payload)
    return payload


def classify(probe: dict[str, Any], linux: dict[str, Any]) -> dict[str, Any]:
    admission = probe.get("admissionProbe") or {}
    status = admission.get("status")
    kernel = linux.get("kernel") or {}
    orders = [int(value) for value in kernel.get("pageAllocationFailureOrders", [])]
    high_order_failure = any(order >= 7 for order in orders)
    vmbus_ring = bool(kernel.get("vmbusAllocRingObserved"))

    if status == "READY" and bool(admission.get("verified")):
        failure_class = "HEALTHY"
        confidence = "high"
        recommended = "none"
        reasons = ["fresh WSL session admission succeeded"]
    elif high_order_failure and vmbus_ring:
        failure_class = "F1_HIGH_ORDER_FRAGMENTATION"
        confidence = "high"
        recommended = "compact_memory"
        reasons = [
            "fresh WSL session admission did not verify",
            "kernel recorded vmbus_alloc_ring",
            "kernel recorded page allocation failure at order >= 7",
        ]
    else:
        failure_class = "UNKNOWN"
        confidence = "insufficient"
        recommended = "collect_forensics"
        reasons = [
            "fresh WSL session admission did not verify",
            "available evidence does not prove one recovery mechanism",
        ]

    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.wsl-substrate-classification",
        "truthRole": "diagnosis",
        "failureClass": failure_class,
        "confidence": confidence,
        "recommendedEffect": recommended,
        "reasons": reasons,
        "knownClassVocabulary": list(KNOWN_CLASSES),
        "probeSha256": object_digest(probe),
        "linuxSnapshotSha256": linux.get("snapshotSha256") or object_digest(linux),
        "observedProbeStatus": status,
        "highOrderAllocationFailureObserved": high_order_failure,
        "vmbusAllocRingObserved": vmbus_ring,
    }
    payload["classificationSha256"] = object_digest(payload)
    return payload


def compact(classification_path: Path, expected_digest: str) -> dict[str, Any]:
    actual_digest = file_digest(classification_path)
    if actual_digest != expected_digest:
        raise RuntimeError("classification digest mismatch")
    classification = json.loads(classification_path.read_text(encoding="utf-8"))
    if classification.get("failureClass") != "F1_HIGH_ORDER_FRAGMENTATION":
        raise RuntimeError("compact_memory is only admitted for F1_HIGH_ORDER_FRAGMENTATION")
    if classification.get("confidence") != "high":
        raise RuntimeError("compact_memory requires high-confidence classification")
    if classification.get("recommendedEffect") != "compact_memory":
        raise RuntimeError("classification does not authorize compact_memory")

    before = snapshot()
    COMPACT_MEMORY.write_text("1\n", encoding="ascii")
    after = snapshot()
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.wsl-substrate-compaction-receipt",
        "truthRole": "effect-evidence",
        "effect": "compact_memory",
        "classificationFileSha256": actual_digest,
        "classificationSha256": classification.get("classificationSha256"),
        "effectExecuted": True,
        "before": before,
        "after": after,
        "recoveryConfirmed": False,
        "note": "Effect execution does not prove WSL recovery; run a new Windows admission probe and requalify.",
    }
    payload["receiptSha256"] = object_digest(payload)
    return payload


def unit_states() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit in CONTROL_PLANE_UNITS:
        completed = subprocess.run(
            ["/usr/bin/systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        rows.append(
            {
                "unit": unit,
                "state": completed.stdout.strip() or "unknown",
                "exitCode": completed.returncode,
            }
        )
    return rows


def requalify(probe: dict[str, Any]) -> dict[str, Any]:
    admission = probe.get("admissionProbe") or {}
    states = unit_states()
    admission_ready = admission.get("status") == "READY" and bool(admission.get("verified"))
    units_ready = all(row["state"] == "active" and row["exitCode"] == 0 for row in states)
    payload = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.wsl-substrate-requalification",
        "truthRole": "verification",
        "freshSessionAdmissionReady": admission_ready,
        "controlPlaneUnits": states,
        "controlPlaneReady": units_ready,
        "recoveryConfirmed": bool(admission_ready and units_ready),
        "probeSha256": object_digest(probe),
    }
    payload["requalificationSha256"] = object_digest(payload)
    return payload


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("snapshot")

    classify_parser = sub.add_parser("classify")
    classify_parser.add_argument("--probe-json", type=Path, required=True)
    classify_parser.add_argument("--snapshot-json", type=Path, required=True)

    compact_parser = sub.add_parser("compact")
    compact_parser.add_argument("--classification-json", type=Path, required=True)
    compact_parser.add_argument("--expected-classification-file-sha256", required=True)

    requalify_parser = sub.add_parser("requalify")
    requalify_parser.add_argument("--probe-json", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "snapshot":
        emit(snapshot())
    elif args.command == "classify":
        emit(classify(load_json(args.probe_json), load_json(args.snapshot_json)))
    elif args.command == "compact":
        emit(compact(args.classification_json, args.expected_classification_file_sha256))
    elif args.command == "requalify":
        emit(requalify(load_json(args.probe_json)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
