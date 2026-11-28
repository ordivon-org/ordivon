#!/usr/bin/env python3
"""Read-only, bounded post-restart installed Gateway readiness observer.

After the original installer switches the immutable release symlink, systemd
Type=simple can report Started *before* the application or new PID are ready.
This observer neither installs nor restarts; caller owns production rollback.
External authenticated ChatGPT/Cloudflare business calls remain separate.
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from check_same_route_admission import _local_anonymous_denied

PREFIX = Path("/opt/ordivon/gateway")
PROC_ROOT = Path("/proc")
UNIT = "ordivon-gateway.service"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _systemctl_value(property_name: str) -> str:
    result = subprocess.run(
        ["/usr/bin/systemctl", "show", UNIT, "-p", property_name, "--value"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout.strip()


def _local_health() -> bool:
    """Only HTTP200 from exact local /health qualifies a process as ready."""
    connection = http.client.HTTPConnection("127.0.0.1", 8899, timeout=2)
    try:
        connection.request("GET", "/health")
        response = connection.getresponse()
        response.read(256)
        return response.status == 200
    finally:
        connection.close()


def _source_and_process(
    expected_release: Path, prior_pid: int | None
) -> tuple[bool, int | None, str]:
    """Read the physical process, never infer it from symlink/systemctl alone."""
    current = PREFIX / "current"
    if current.resolve() != expected_release:
        return False, None, "EXPECTED_SOURCECUT_NOT_CURRENT"
    if (
        not expected_release.is_dir()
        or expected_release.is_symlink()
        or not expected_release.resolve().is_relative_to(PREFIX / "releases")
    ):
        return False, None, "IMMUTABLE_RELEASE_UNOBSERVABLE"
    if _systemctl_value("ActiveState") != "active":
        return False, None, "SYSTEMD_NOT_ACTIVE"
    if _systemctl_value("SubState") != "running":
        return False, None, "SYSTEMD_NOT_RUNNING"
    if _systemctl_value("User") != "ordivon-gateway":
        return False, None, "GATEWAY_SERVICE_IDENTITY_DRIFT"
    pid_text = _systemctl_value("MainPID")
    if not pid_text.isdecimal() or int(pid_text) < 1:
        return False, None, "SYSTEMD_PID_NOT_OBSERVED"
    pid = int(pid_text)
    if prior_pid is not None and pid == prior_pid:
        return False, pid, "PREVIOUS_PROCESS_STILL_OWNING_SERVICE"
    process_dir = PROC_ROOT / str(pid) / "cwd"
    if not process_dir.exists():
        return False, pid, "NATIVE_PROCESS_NOT_PRESENT"
    if process_dir.resolve() != expected_release:
        return False, pid, "PROCESS_STILL_RUNNING_OTHER_SOURCECUT"
    return True, pid, "CURRENT_PROCESS_MATCHES_EXPECTED_RELEASE"


def observe(expected_sha: str, prior_pid: int | None, *, timeout_seconds: float) -> dict[str, Any]:
    if not SHA40.fullmatch(expected_sha) or timeout_seconds < 0 or timeout_seconds > 60:
        raise ValueError("expected a 40-character release SHA and bounded timeout")
    expected = PREFIX / "releases" / expected_sha
    deadline = time.monotonic() + timeout_seconds
    attempt = 0
    last_reason = "NOT_YET_OBSERVED"
    last_pid: int | None = None
    health_observed = False
    deny_observed = False

    while True:
        attempt += 1
        try:
            current, pid, reason = _source_and_process(expected, prior_pid)
            last_pid, last_reason = pid, reason
            if current:
                health_observed = _local_health()
                if health_observed:
                    deny_observed = _local_anonymous_denied()
                    if deny_observed:
                        # Revalidate after HTTP calls, not only before them.
                        still_current, final_pid, reason = _source_and_process(expected, prior_pid)
                        if still_current and final_pid == pid:
                            return {
                                "schemaVersion": 1,
                                "kind": "ordivon.gateway-running-release-readiness",
                                "status": "READY",
                                "expectedSourceCut": expected_sha,
                                "observedMainPid": pid,
                                "attempts": attempt,
                                "localHealthHttp200": True,
                                "localAnonymousMcpDenied": True,
                                "authenticatedExternalAgentConsumer": "UNVERIFIED",
                                "truthBoundary": (
                                    "Exact running systemd PID+cwd/installed SourceCut and local "
                                    "HTTP health/anonymous deny only. Connected authenticated "
                                    "ChatGPT Agent and Host domain acceptance require separate "
                                    "real client evidence. No restart, promotion, rollback, "
                                    "credential read or Security decision is performed."
                                ),
                            }
                        last_reason = reason if not still_current else "PID_CHANGED_DURING_CANARY"
                    else:
                        last_reason = "LOCAL_ANONYMOUS_DENIAL_NOT_PROVEN"
                else:
                    last_reason = "LOCAL_HTTP_HEALTH_NOT_READY"
        except OSError, subprocess.SubprocessError, ValueError, TimeoutError:
            last_reason = "PHYSICAL_READINESS_UNOBSERVABLE"
        if time.monotonic() >= deadline:
            break
        time.sleep(min(0.5, max(0, deadline - time.monotonic())))
    return {
        "schemaVersion": 1,
        "kind": "ordivon.gateway-running-release-readiness",
        "status": "NO_GO",
        "reason": last_reason,
        "expectedSourceCut": expected_sha,
        "observedMainPid": last_pid,
        "attempts": attempt,
        "localHealthHttp200": health_observed,
        "localAnonymousMcpDenied": deny_observed,
        "authenticatedExternalAgentConsumer": "UNVERIFIED",
        "truthBoundary": "Read-only readiness observer; not an authorization or rollback decision.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sourcecut", required=True)
    parser.add_argument("--previous-pid", type=int)
    parser.add_argument("--timeout-seconds", type=float, default=16.0)
    args = parser.parse_args()
    try:
        result = observe(
            args.expected_sourcecut, args.previous_pid, timeout_seconds=args.timeout_seconds
        )
    except ValueError:
        result = {
            "schemaVersion": 1,
            "kind": "ordivon.gateway-running-release-readiness",
            "status": "NO_GO",
            "reason": "INVALID_RELEASE_QUALIFICATION",
            "authenticatedExternalAgentConsumer": "UNVERIFIED",
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "READY" else 3


if __name__ == "__main__":
    sys.exit(main())
