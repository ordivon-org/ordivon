#!/usr/bin/env python3
"""Bounded read-only proof of the ACTIVE Gluetun endpoint, not standby health.

No new tunnel, scheduler, endpoint database, WireGuard secret or public-IP
fallback. The catalog location and observed public egress are separate facts.
"""
from __future__ import annotations

from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import subprocess
import sys

import native_profile as native

NATIVE_PROFILE = Path(__file__).resolve().with_name("native_profile.py")
PROXY = "http://10.252.246.2:19680"
CONTAINER = "network-v2-gluetun-owned-r1"


def run(*args: str, timeout: int = 20) -> str:
    return subprocess.run(
        list(args), capture_output=True, text=True, check=True,
        timeout=timeout,
    ).stdout


def endpoint_ip(wg_endpoints: str) -> str:
    """The kernel, not an environment country name, owns active endpoint truth."""
    endpoints = []
    for line in wg_endpoints.splitlines():
        parts = line.split()
        if len(parts) != 3 or parts[2] == "(none)":
            continue
        ip = parts[2].rsplit(":", 1)[0].strip("[]")
        endpoints.append(str(ipaddress.ip_address(ip)))
    if len(endpoints) != 1:
        raise ValueError("Expected exactly one active WireGuard endpoint")
    return endpoints[0]


def catalog_country(raw: str, ip: str) -> str | None:
    entries = json.loads(raw)["surfshark"]["servers"]
    countries = {
        entry.get("country") for entry in entries
        if entry.get("vpn") == "wireguard" and ip in entry.get("ips", [])
    }
    return next(iter(countries)) if len(countries) == 1 else None


def parse_curl_receipt(raw: str) -> tuple[bool, float]:
    parts = raw.strip().split()
    if len(parts) != 4:
        return False, 0.0
    try:
        http, connect = int(parts[0]), int(parts[1])
        tls, total = float(parts[2]), float(parts[3])
    except ValueError:
        return False, 0.0
    return http == 200 and connect == 200 and 0 < tls <= total, total


def standing(
    *, catalog_location: str | None, actual_exit: str | None,
    allowed: set[str], active_endpoint_stable: bool,
    provider_running: bool, business_receipts: list[bool],
) -> str:
    if catalog_location == "Hong Kong" or actual_exit == "HK":
        return "REJECTED_FORBIDDEN_EXIT"
    if catalog_location is None or actual_exit is None:
        return "UNKNOWN"
    if catalog_location not in allowed:
        return "REJECTED_NOT_ALLOWED"
    if not active_endpoint_stable or not provider_running:
        return "UNKNOWN"
    if len(business_receipts) < 2 or not all(business_receipts):
        return "NOT_QUALIFIED"
    return "QUALIFIED_ACTIVE_SAMPLE"


def curl_business(url: str) -> tuple[bool, float]:
    raw = run(
        "/usr/bin/curl", "-q", "-4", "--noproxy", "",
        "--proxy", PROXY, "--silent", "--show-error",
        "--connect-timeout", "5", "--max-time", "15",
        "-o", "/dev/null", "-w",
        "%{http_code} %{http_connect} %{time_appconnect} %{time_total}",
        url, timeout=18,
    )
    return parse_curl_receipt(raw)


def observe() -> dict[str, object]:
    # Source and installed/loaded admission is separate from current health.
    run("/usr/bin/python3", str(NATIVE_PROFILE), "--verify")
    selected = native.read_selector_policy()
    allowed = native.parse_allowed_policy(native.ALLOW_POLICY.read_text())
    pid = run(
        "/usr/bin/podman", "inspect", CONTAINER, "--format", "{{.State.Pid}}"
    ).strip()
    if not pid.isdecimal() or int(pid) < 2:
        raise ValueError("No running Gluetun namespace")
    def kernel_endpoint() -> str:
        return endpoint_ip(run(
            "/usr/bin/nsenter", "-t", pid, "-n",
            "/usr/bin/wg", "show", "all", "endpoints",
        ))
    before = kernel_endpoint()
    country = catalog_country(run(
        "/usr/bin/podman", "exec", CONTAINER, "cat", "/gluetun/servers.json",
    ), before)
    service = json.loads(run(
        "/usr/bin/podman", "exec", CONTAINER, "wget", "-qO-",
        "http://127.0.0.1:8000/v1/vpn/status",
    ))
    trace = run(
        "/usr/bin/curl", "-q", "-4", "--noproxy", "",
        "--proxy", PROXY, "--silent", "--show-error",
        "--connect-timeout", "5", "--max-time", "15",
        "https://www.cloudflare.com/cdn-cgi/trace",
    )
    exit_codes = [line.removeprefix("loc=").strip() for line in trace.splitlines()
                  if line.startswith("loc=")]
    exit_country = exit_codes[0] if len(exit_codes) == 1 and len(exit_codes[0]) == 2 else None
    probes = {}
    for consumer, url in (
        ("ordinary_https", "https://example.com/"),
        ("github_https", "https://github.com/"),
    ):
        ok, total = curl_business(url)
        probes[consumer] = {"httpTlsAndConnect": ok, "totalMs": round(1000*total)}
    after = kernel_endpoint()
    result = standing(
        catalog_location=country, actual_exit=exit_country,
        allowed=set(allowed["allowedCountries"]),
        active_endpoint_stable=(before == after),
        provider_running=service.get("status") == "running",
        business_receipts=[p["httpTlsAndConnect"] for p in probes.values()],
    )
    return {
        "kind": "ordivon.network.gluetun-active-qualification",
        "standing": result,
        "observedAtUtc": datetime.now(timezone.utc).isoformat(),
        "currentCatalogCountry": country,
        "currentPublicExitCountryCode": exit_country,
        "countryIdentityMismatchIsAllowed": True,
        "candidateCountryCount": len(selected["selectedCountries"]),
        "actualEndpointStableDuringSample": before == after,
        "providerStatus": service.get("status"),
        "business": probes,
        "qualifiedStandbyCount": 0,
        "boundary": "active-session-only; no standby liveness or automatic ranking",
    }


def main() -> int:
    try:
        receipt = observe()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, json.JSONDecodeError):
        receipt = {
            "kind": "ordivon.network.gluetun-active-qualification",
            "standing": "UNKNOWN",
            "boundary": "one-shot observation unavailable; not a proven VPN failure",
        }
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0 if receipt["standing"] == "QUALIFIED_ACTIVE_SAMPLE" else 1


if __name__ == "__main__":
    sys.exit(main())
