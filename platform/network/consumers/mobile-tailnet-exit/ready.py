#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

UNIT = "network-v2-mobile-tailnet-exit.service"
CTR = "network-v2-gluetun-owned-r1"
RUNTIME = Path("/run/ordivon-mobile-surfshark-tailnet-r1")
SOCKET = RUNTIME / "tailscaled.sock"


def run(*args: str, timeout: int = 8) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, text=True, capture_output=True, timeout=timeout, check=False
    )


def emit(standing: str, **extra: object) -> int:
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.network-v2.mobile-tailnet-exit-readiness",
        "standing": standing,
        **extra,
    }
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0 if standing == "READY" else 3


def read_pid(path: Path) -> int | None:
    try:
        value = int(path.read_text().strip())
    except (OSError, ValueError):
        return None
    return value if value > 1 and Path(f"/proc/{value}/ns/net").exists() else None


def netns(pid: int | None) -> str | None:
    if pid is None:
        return None
    try:
        return str(Path(f"/proc/{pid}/ns/net").readlink())
    except OSError:
        return None


def main() -> int:
    active = run("/usr/bin/systemctl", "is-active", "--quiet", UNIT).returncode == 0
    if not active:
        return emit("SERVICE_INACTIVE", serviceActive=False)

    provider = run("/usr/bin/podman", "inspect", "-f", "{{.State.Pid}}", CTR)
    try:
        provider_pid = (
            int(provider.stdout.strip()) if provider.returncode == 0 else None
        )
    except ValueError:
        provider_pid = None
    tailscaled_pid = read_pid(RUNTIME / "tailscaled.pid")
    namespace_match = netns(provider_pid) is not None and netns(provider_pid) == netns(
        tailscaled_pid
    )
    if not namespace_match:
        return emit(
            "NAMESPACE_MISMATCH",
            serviceActive=True,
            providerPidPresent=provider_pid is not None,
            tailscaledPidPresent=tailscaled_pid is not None,
            namespaceMatch=False,
        )

    status = run("/usr/bin/tailscale", f"--socket={SOCKET}", "status", "--json")
    prefs = run("/usr/bin/tailscale", f"--socket={SOCKET}", "debug", "prefs")
    if status.returncode != 0 or prefs.returncode != 0:
        return emit("TAILSCALE_UNAVAILABLE", serviceActive=True, namespaceMatch=True)
    try:
        status_value = json.loads(status.stdout)
        prefs_value = json.loads(prefs.stdout)
    except json.JSONDecodeError:
        return emit(
            "TAILSCALE_PROJECTION_INVALID", serviceActive=True, namespaceMatch=True
        )

    self_value = status_value.get("Self") or {}
    routes = set(prefs_value.get("AdvertiseRoutes") or [])
    advertised = {"0.0.0.0/0", "::/0"}.issubset(routes)
    online = (
        status_value.get("BackendState") == "Running"
        and self_value.get("Online") is True
    )
    approved = self_value.get("ExitNodeOption") is True
    common = {
        "serviceActive": True,
        "namespaceMatch": True,
        "backendState": status_value.get("BackendState"),
        "online": online,
        "advertisedExitRoutes": advertised,
        "adminApprovedExitNode": approved,
        "hostname": self_value.get("HostName"),
    }
    if not online:
        return emit("TAILSCALE_NOT_RUNNING", **common)
    if not advertised:
        return emit("EXIT_ROUTES_NOT_ADVERTISED", **common)
    if not approved:
        return emit("ADVERTISED_PENDING_ADMIN_APPROVAL", **common)

    # Tailscale joins the Gluetun container namespace directly, not the
    # shared Browserless HTTP Carrier. Check the provider using its own
    # upstream healthcheck rather than requiring unrelated finance/model APIs.
    # Gluetun's healthcheck does not establish a real iOS client exit.
    try:
        health = run(
            "/usr/bin/podman", "exec", CTR, "/gluetun-entrypoint", "healthcheck",
            timeout=12,
        )
    except (OSError, subprocess.TimeoutExpired):
        return emit("PROVIDER_HEALTH_NOT_READY", **common)
    if health.returncode != 0:
        return emit("PROVIDER_HEALTH_NOT_READY", **common)
    return emit(
        "READY", providerHealth="NATIVE_OK",
        providerHealthMechanism="gluetun-healthcheck",
        clientPublicExit="NOT_EVALUATED", **common,
    )


if __name__ == "__main__":
    raise SystemExit(main())
