#!/usr/bin/env python3
"""Install and verify the production Agent Automation Temporal worker."""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_SERVER = "temporal.service"
WORKER = "ordivon-agent-temporal-worker.service"
SYSTEMD = Path("/etc/systemd/system")
CONFIG = Path("/etc/ordivon/agent-automation-browserless.json")
VENV_PY = Path("/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python")
TEMPORAL = Path("/opt/ordivon/external/temporal-cli/1.8.3/temporal")
TEMPORAL_SHA = "76aea8d71fafe2d39c1104bef3ce86c1600d9adbff79953d102f60e535ae1413"
PRODUCTION_ADDRESS = "127.0.0.1:17233"
EXPECTED_RUNTIME_VERSIONS = {
    "temporalio": "1.32.0",
    "rfc8785": "0.1.4",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active(unit: str) -> bool:
    return (
        subprocess.run(["/usr/bin/systemctl", "is-active", "--quiet", unit], check=False).returncode
        == 0
    )


def cluster_health(address: str) -> bool:
    return (
        subprocess.run(
            [str(TEMPORAL), "operator", "cluster", "health", "--address", address],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=15,
        ).returncode
        == 0
    )


def runtime_versions() -> dict[str, str] | None:
    if not VENV_PY.is_file():
        return None
    code = (
        "import importlib.metadata as m,json;"
        "names=['temporalio','rfc8785'];"
        "print(json.dumps({n:m.version(n) for n in names},sort_keys=True))"
    )
    proc = subprocess.run(
        [str(VENV_PY), "-c", code],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        return None
    try:
        value = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def config_address() -> str | None:
    try:
        value = json.loads(CONFIG.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    address = value.get("temporalAddress") if isinstance(value, dict) else None
    return address if isinstance(address, str) else None


def plan() -> dict:
    source = ROOT / "systemd" / WORKER
    installed = SYSTEMD / WORKER
    return {
        "schemaVersion": 1,
        "kind": "ordivon.temporal-agent-production-deployment-plan",
        "temporalBinaryValid": TEMPORAL.is_file() and sha(TEMPORAL) == TEMPORAL_SHA,
        "temporalSdkPresent": VENV_PY.is_file(),
        "runtimeVersions": runtime_versions(),
        "runtimeVersionsExact": runtime_versions() == EXPECTED_RUNTIME_VERSIONS,
        "browserlessConfigPresent": CONFIG.is_file(),
        "admissionAddress": config_address(),
        "productionCluster": {
            "address": PRODUCTION_ADDRESS,
            "healthy": cluster_health(PRODUCTION_ADDRESS),
        },
        "serverActive": active(PRODUCTION_SERVER),
        "worker": {
            "unit": WORKER,
            "installed": installed.is_file()
            and source.is_file()
            and installed.read_bytes() == source.read_bytes(),
            "active": active(WORKER),
        },
    }


def apply() -> dict:
    current = plan()
    if not current["temporalBinaryValid"]:
        raise RuntimeError("Temporal CLI exact binary is unavailable")
    if not current["temporalSdkPresent"]:
        raise RuntimeError("Temporal SDK venv is unavailable")
    if not current["runtimeVersionsExact"]:
        raise RuntimeError(
            f"Temporal worker runtime versions differ from contract: {current['runtimeVersions']}"
        )
    if not current["browserlessConfigPresent"]:
        raise RuntimeError("Browserless config must be prepared first")
    if current["admissionAddress"] != PRODUCTION_ADDRESS:
        raise RuntimeError(f"Browserless config must point admissions at {PRODUCTION_ADDRESS}")
    if not current["productionCluster"]["healthy"] or not current["serverActive"]:
        raise RuntimeError("production Temporal cluster is unavailable")
    SYSTEMD.mkdir(parents=True, exist_ok=True)
    src = ROOT / "systemd" / WORKER
    dst = SYSTEMD / WORKER
    dst.write_bytes(src.read_bytes())
    os.chmod(dst, 0o644)
    subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)
    subprocess.run(["/usr/bin/systemctl", "enable", WORKER], check=True)
    subprocess.run(["/usr/bin/systemctl", "restart", WORKER], check=True)
    result = plan()
    if not result["worker"]["installed"] or not result["worker"]["active"]:
        raise RuntimeError("production Agent Automation Temporal worker did not converge")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    r = apply() if a.apply else plan()
    print(json.dumps(r, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
