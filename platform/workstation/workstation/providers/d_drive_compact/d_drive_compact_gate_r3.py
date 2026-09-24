#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Any

RUNTIME_STATUS = "/usr/local/libexec/ordivon/ordivon-runtime-status"
RUNTIME_INSPECT = "/usr/local/libexec/ordivon/ordivon-runtime-inspect"
RUNTIME_DOCTOR = "/usr/local/libexec/ordivon/ordivon-runtime-doctor"
REGISTRY_DB = Path("/var/lib/ordivon/registry/registry.sqlite3")
STORE_ROOT = Path("/var/lib/ordivon/runtime")
ADMISSION_LOCK = Path("/var/lib/ordivon/registry/admission.lock")
PRESSURE_TIMER = "ordivon-runtime-storage-pressure.timer"
PRESSURE_SERVICE = "ordivon-runtime-storage-pressure.service"
CONTROL_PLANE_UNITS = (
    "ordivon-runtime.service",
    "ordivon-host-v2.service",
    "ordivon-gateway.service",
)
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        with tmp.open("wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        try:
            fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError:
            pass
    finally:
        tmp.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_bytes(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def run(argv: list[str], *, timeout: float, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=check,
    )


def run_json(argv: list[str], *, timeout: float) -> dict[str, Any]:
    cp = run(argv, timeout=timeout)
    if cp.returncode != 0:
        raise RuntimeError(f"command rc={cp.returncode}: {' '.join(argv)}; stderr={cp.stderr.strip()[:2000]}")
    try:
        value = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command returned invalid JSON: {' '.join(argv)}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("JSON command returned non-object")
    return value


class GateFailure(RuntimeError):
    def __init__(self, reason_code: str, phase: str, detail: str, *, extra: dict[str, Any] | None = None):
        super().__init__(detail)
        self.reason_code = reason_code
        self.phase = phase
        self.detail = detail
        self.extra = extra or {}


class GateSignal(RuntimeError):
    def __init__(self, signum: int):
        super().__init__(f"received signal {signum}")
        self.signum = signum


def service_state(unit: str) -> str:
    cp = run(["/usr/bin/systemctl", "is-active", unit], timeout=10)
    state = cp.stdout.strip()
    return state or "unknown"


def restore_pressure() -> None:
    run(["/usr/bin/systemctl", "start", PRESSURE_TIMER], timeout=15)
    run(["/usr/bin/systemctl", "start", "--no-block", PRESSURE_SERVICE], timeout=15)


def pause_pressure(timeout_seconds: float) -> dict[str, Any]:
    run(["/usr/bin/systemctl", "stop", PRESSURE_TIMER], timeout=20)
    deadline = time.monotonic() + timeout_seconds
    last = "unknown"
    while time.monotonic() < deadline:
        last = service_state(PRESSURE_SERVICE)
        if last in {"inactive", "failed"}:
            return {"timer": service_state(PRESSURE_TIMER), "service": last}
        time.sleep(0.5)
    raise GateFailure(
        "PRESSURE_RECLAIM_DID_NOT_QUIESCE",
        "PRESSURE_QUIESCE",
        f"pressure service remained {last}",
    )


def status_projection() -> dict[str, Any]:
    return run_json(
        [
            RUNTIME_INSPECT,
            "registry-status",
            "--database",
            str(REGISTRY_DB),
            "--job-limit",
            "50",
            "--busy-timeout-ms",
            "5000",
        ],
        timeout=15,
    )


def status_counts(payload: dict[str, Any]) -> dict[str, int]:
    return {
        "activeReservations": int(payload.get("activeReservations", -1)),
        "heldReservations": int(payload.get("heldReservations", -1)),
        "jobsActive": int(payload.get("jobsActive", -1)),
        "nonterminalAttempts": int(payload.get("nonterminalAttempts", -1)),
        "recoveryRequired": int(payload.get("recoveryRequired", -1)),
    }


def active_job_ids(payload: dict[str, Any]) -> list[str]:
    jobs = payload.get("jobs")
    if not isinstance(jobs, dict):
        return []
    active = jobs.get("active")
    if not isinstance(active, list):
        return []
    out: list[str] = []
    for row in active:
        if isinstance(row, dict) and isinstance(row.get("jobId"), str):
            out.append(row["jobId"])
    return out


def is_quiescent(counts: dict[str, int]) -> bool:
    return all(counts[k] == 0 for k in counts)


def full_doctor(doctor_path: Path, timeout_seconds: float) -> dict[str, Any]:
    cp = run(
        [
            RUNTIME_DOCTOR,
            "inspect",
            "--database",
            str(REGISTRY_DB),
            "--store-root",
            str(STORE_ROOT),
            "--busy-timeout-ms",
            "5000",
            "--pretty",
            "--fail-on-violation",
        ],
        timeout=timeout_seconds,
    )
    if not cp.stdout.strip():
        raise GateFailure("DOCTOR_NO_OUTPUT", "INTEGRITY_VERIFY", "Runtime Doctor returned no JSON")
    try:
        payload = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise GateFailure("DOCTOR_INVALID_JSON", "INTEGRITY_VERIFY", "Runtime Doctor returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise GateFailure("DOCTOR_INVALID_JSON", "INTEGRITY_VERIFY", "Runtime Doctor returned non-object JSON")
    atomic_write_json(doctor_path, payload)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    violations = int(payload.get("violationCount", -1))
    holders = summary.get("capacityHolders") if isinstance(summary, dict) else None
    if (
        cp.returncode != 0
        or payload.get("integrityCheck") != "ok"
        or violations != 0
        or int(summary.get("recoveryRequiredAttempts", -1)) != 0
        or not isinstance(holders, list)
        or len(holders) != 0
        or bool(summary.get("capacityHoldersTruncated", False))
    ):
        raise GateFailure(
            "INTEGRITY_REJECTED",
            "INTEGRITY_VERIFY",
            f"Doctor rejected maintenance cut rc={cp.returncode} violations={violations}",
            extra={"doctorSha256": sha256_file(doctor_path)},
        )
    return payload


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--maintenance-id", required=True)
    p.add_argument("--unit-name", required=True)
    p.add_argument("--transaction-root", required=True, type=Path)
    p.add_argument("--drain-seconds", type=float, default=1200.0)
    p.add_argument("--lock-wait-seconds", type=float, default=30.0)
    p.add_argument("--pressure-wait-seconds", type=float, default=120.0)
    p.add_argument("--doctor-timeout-seconds", type=float, default=240.0)
    p.add_argument("--probe-failure-grace-seconds", type=float, default=20.0)
    p.add_argument("--ready-hold-seconds", type=float, default=300.0)
    p.add_argument("--handoff-hold-seconds", type=float, default=120.0)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not ID_RE.fullmatch(args.maintenance_id):
        raise SystemExit("invalid maintenance id")
    if not ID_RE.fullmatch(args.unit_name):
        raise SystemExit("invalid unit name")
    root = args.transaction_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "gate-state.json"
    ready_path = root / "ready.json"
    terminal_path = root / "gate-terminal.json"
    handoff_path = root / "handoff.json"
    handoff_observed_path = root / "handoff-observed.json"
    doctor_path = root / "doctor.json"
    status_path = root / "runtime-status.json"
    trim_path = root / "fstrim.txt"
    drain_log = root / "drain.ndjson"
    gate_source = Path(__file__).resolve()
    gate_source_sha = sha256_file(gate_source)
    start_monotonic = time.monotonic()
    pressure_paused = False
    handoff_seen = False
    lock_handle = None
    current_phase = "CREATED"

    def write_state(phase: str, **extra: Any) -> None:
        nonlocal current_phase
        current_phase = phase
        atomic_write_json(
            state_path,
            {
                "schemaVersion": 3,
                "kind": "ordivon.d-drive-compact-gate-state",
                "maintenanceId": args.maintenance_id,
                "unitName": args.unit_name,
                "phase": phase,
                "observedAtUtc": utc_now(),
                "gateSha256": gate_source_sha,
                **extra,
            },
        )

    def write_terminal(reason_code: str, phase: str, detail: str, **extra: Any) -> None:
        atomic_write_json(
            terminal_path,
            {
                "schemaVersion": 3,
                "kind": "ordivon.d-drive-compact-gate-terminal",
                "maintenanceId": args.maintenance_id,
                "unitName": args.unit_name,
                "status": "aborted",
                "phase": phase,
                "reasonCode": reason_code,
                "detail": detail,
                "observedAtUtc": utc_now(),
                "gateSha256": gate_source_sha,
                **extra,
            },
        )

    def on_signal(signum: int, _frame: Any) -> None:
        raise GateSignal(signum)

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    ready_path.unlink(missing_ok=True)
    terminal_path.unlink(missing_ok=True)
    handoff_observed_path.unlink(missing_ok=True)
    drain_log.unlink(missing_ok=True)
    write_state("CREATED")

    try:
        pressure = pause_pressure(args.pressure_wait_seconds)
        pressure_paused = True
        write_state("PRESSURE_QUIESCED", pressure=pressure)

        ADMISSION_LOCK.parent.mkdir(parents=True, exist_ok=True)
        lock_handle = ADMISSION_LOCK.open("a+")
        lock_deadline = time.monotonic() + args.lock_wait_seconds
        while True:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= lock_deadline:
                    raise GateFailure("ADMISSION_FENCE_TIMEOUT", "FENCE_ACQUIRE", "exclusive admission.lock was not acquired")
                time.sleep(0.1)
        write_state("FENCE_ACQUIRED", admissionLock=str(ADMISSION_LOCK))

        drain_deadline = time.monotonic() + args.drain_seconds
        probe_failure_since: float | None = None
        last_payload: dict[str, Any] | None = None
        while True:
            try:
                payload = status_projection()
                probe_failure_since = None
                last_payload = payload
                counts = status_counts(payload)
                jobs = active_job_ids(payload)
                append_jsonl(
                    drain_log,
                    {
                        "observedAtUtc": utc_now(),
                        "counts": counts,
                        "activeJobIds": jobs,
                    },
                )
                atomic_write_json(status_path, payload)
                write_state("DRAINING", counts=counts, activeJobIds=jobs)
                if is_quiescent(counts):
                    break
            except Exception as exc:
                now = time.monotonic()
                if probe_failure_since is None:
                    probe_failure_since = now
                append_jsonl(
                    drain_log,
                    {"observedAtUtc": utc_now(), "probeError": str(exc)},
                )
                if now - probe_failure_since >= args.probe_failure_grace_seconds:
                    raise GateFailure("STATUS_PROBE_FAILED", "DRAINING", str(exc)) from exc
            if time.monotonic() >= drain_deadline:
                counts = status_counts(last_payload) if last_payload else {}
                jobs = active_job_ids(last_payload) if last_payload else []
                raise GateFailure(
                    "DRAIN_DEADLINE_EXCEEDED",
                    "DRAINING",
                    "active or held Runtime work did not drain before monotonic deadline",
                    extra={"counts": counts, "activeJobIds": jobs},
                )
            time.sleep(0.25)

        write_state("QUIESCENT", counts=status_counts(last_payload or {}))
        doctor = full_doctor(doctor_path, args.doctor_timeout_seconds)
        write_state("INTEGRITY_VERIFIED", doctorSha256=sha256_file(doctor_path))

        final_status = run_json([RUNTIME_STATUS, "--health", "--json"], timeout=20)
        atomic_write_json(status_path, final_status)
        registry = final_status.get("registry") if isinstance(final_status.get("registry"), dict) else {}
        if (
            final_status.get("status") != "healthy"
            or int(registry.get("jobsActive", -1)) != 0
            or int(registry.get("activeReservations", -1)) != 0
            or int(registry.get("heldReservations", -1)) != 0
            or int(registry.get("recoveryRequired", -1)) != 0
        ):
            raise GateFailure("RUNTIME_HEALTH_REJECTED", "FINAL_HEALTH", "Runtime health did not bind a zero-holder healthy cut")

        services = {unit: service_state(unit) for unit in CONTROL_PLANE_UNITS}
        if any(state != "active" for state in services.values()):
            raise GateFailure("CONTROL_PLANE_NOT_ACTIVE", "FINAL_HEALTH", f"control plane states={services}")

        run(["/usr/bin/sync"], timeout=30, check=True)
        trim_cp = run(["/usr/sbin/fstrim", "-v", "/"], timeout=300)
        if trim_cp.returncode != 0:
            raise GateFailure("FSTRIM_FAILED", "TRIM", trim_cp.stderr.strip() or f"fstrim rc={trim_cp.returncode}")
        atomic_write_bytes(trim_path, trim_cp.stdout.encode())
        run(["/usr/bin/sync"], timeout=30, check=True)
        write_state("TRIMMED", fstrimSha256=sha256_file(trim_path))

        ready_hold_deadline = time.monotonic() + args.ready_hold_seconds
        ready = {
            "schemaVersion": 3,
            "kind": "ordivon.d-drive-compact-gate-ready",
            "maintenanceId": args.maintenance_id,
            "status": "ready",
            "readyAtUtc": utc_now(),
            "unitName": args.unit_name,
            "gateSha256": gate_source_sha,
            "admissionLockHeld": True,
            "integrityCheck": doctor.get("integrityCheck"),
            "violationCount": doctor.get("violationCount"),
            "recoveryRequiredAttempts": doctor.get("summary", {}).get("recoveryRequiredAttempts"),
            "capacityHolders": doctor.get("summary", {}).get("capacityHolders"),
            "runtimeHealth": final_status.get("status"),
            "runtimeActiveJobs": registry.get("jobsActive"),
            "runtimeActiveReservations": registry.get("activeReservations"),
            "runtimeHeldReservations": registry.get("heldReservations"),
            "runtimeRecoveryRequired": registry.get("recoveryRequired"),
            "services": services,
            "doctorSha256": sha256_file(doctor_path),
            "runtimeStatusSha256": sha256_file(status_path),
            "fstrimSha256": sha256_file(trim_path),
            "fstrim": trim_cp.stdout.strip(),
            "monotonicElapsedSeconds": round(time.monotonic() - start_monotonic, 3),
            "readyHoldSeconds": args.ready_hold_seconds,
        }
        atomic_write_json(ready_path, ready)
        ready_sha = sha256_file(ready_path)
        write_state("READY_HELD", readySha256=ready_sha)

        while time.monotonic() < ready_hold_deadline:
            if handoff_path.is_file():
                try:
                    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    raise GateFailure("HANDOFF_INVALID_JSON", "READY_HELD", str(exc)) from exc
                if (
                    not isinstance(handoff, dict)
                    or handoff.get("maintenanceId") != args.maintenance_id
                    or handoff.get("status") != "offline_authorized"
                    or handoff.get("readySha256") != ready_sha
                ):
                    raise GateFailure("HANDOFF_BINDING_MISMATCH", "READY_HELD", "handoff does not bind the exact ready receipt")
                handoff_seen = True
                atomic_write_json(
                    handoff_observed_path,
                    {
                        "schemaVersion": 3,
                        "kind": "ordivon.d-drive-compact-gate-handoff-observed",
                        "maintenanceId": args.maintenance_id,
                        "status": "accepted",
                        "readySha256": ready_sha,
                        "handoffSha256": sha256_file(handoff_path),
                        "observedAtUtc": utc_now(),
                    },
                )
                write_state("HANDOFF_HELD", readySha256=ready_sha, handoffSha256=sha256_file(handoff_path))
                handoff_deadline = time.monotonic() + args.handoff_hold_seconds
                while time.monotonic() < handoff_deadline:
                    time.sleep(0.25)
                raise GateFailure("HANDOFF_TIMEOUT", "HANDOFF_HELD", "Windows effect owner did not offline WSL before handoff hold expired")
            time.sleep(0.25)
        raise GateFailure("READY_HOLD_EXPIRED", "READY_HELD", "ready gate expired before exact offline handoff")

    except GateFailure as exc:
        write_terminal(exc.reason_code, exc.phase, exc.detail, **exc.extra)
        write_state("ABORTED", reasonCode=exc.reason_code)
        return 42
    except GateSignal as exc:
        if not handoff_seen:
            write_terminal("GATE_SIGNALLED", current_phase, str(exc), signal=exc.signum)
        return 143 if exc.signum == signal.SIGTERM else 130
    except subprocess.TimeoutExpired as exc:
        write_terminal("COMMAND_TIMEOUT", current_phase, str(exc))
        write_state("ABORTED", reasonCode="COMMAND_TIMEOUT")
        return 44
    except Exception as exc:
        write_terminal("UNEXPECTED_GATE_FAILURE", current_phase, repr(exc))
        write_state("ABORTED", reasonCode="UNEXPECTED_GATE_FAILURE")
        return 45
    finally:
        if lock_handle is not None:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            lock_handle.close()
        if pressure_paused and not handoff_seen:
            try:
                restore_pressure()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
