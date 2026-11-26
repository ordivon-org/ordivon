#!/usr/bin/env python3
"""Read-only ZTE U30 Pro MU5358 performance observation adapter.

Uses standard ZTE HTTPS AJAX GET. Projects explicit non-secret fields only.
Throughput and queue management remain with iperf3/Flent/tc, not this module.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import ipaddress
import json
import re
import shutil
import subprocess
import sys

KIND = "ordivon.network.zte-u30pro.performance-observation.v1"
FIELDS = {
    "identity": ("model_name", "market_name", "hardware_version", "wa_inner_version", "cr_version"),
    "cellular": ("network_information", "network_type", "network_provider", "ppp_status", "Z5g_rsrp", "opms_wan_mode"),
    "lan": ("lan_ipaddr", "lan_netmask", "dhcpEnabled", "dhcpStart", "dhcpEnd", "dhcpLease_hour", "mtu", "tcp_mss"),
    "wifi": ("wifi6_mode", "wifi_onoff_state"),
    "power": ("performance_mode", "router_bw_switch", "power_supply_mode", "battery_charging", "sleep_sysIdleTimeToSleep", "reboot_schedule_enable", "reboot_schedule_mode", "reboot_hour1", "reboot_min1", "reboot_dow"),
}
NR_FIELDS = ("Nr_bands", "Nr_band_widths", "Nr_fcn", "Nr_signal_strength", "Nr_snr", "nr_rsrp", "nr_rsrq")
SAFE_FIELDS = ({x for values in FIELDS.values() for x in values} - {"network_information"}) | set(NR_FIELDS)


def validate_gateway(s: str) -> str:
    try:
        a = ipaddress.IPv4Address(s)
    except ipaddress.AddressValueError as e:
        raise ValueError("require private numeric IPv4 gateway") from e
    if not a.is_private or a.is_loopback or a.is_link_local or a.is_multicast:
        raise ValueError("require private numeric IPv4 gateway")
    return s


def project(group: str, response: dict) -> dict:
    if not isinstance(response, dict) or response.get("Error"):
        raise ValueError("device state not available")
    allowed = set(FIELDS[group]) | (set(NR_FIELDS) if group == "cellular" else set())
    return {k: (response[k] if isinstance(response.get(k), (str, int, float, bool)) and response[k] != "" else None)
            for k in sorted(allowed & SAFE_FIELDS)}


def read_group(gateway: str, group: str) -> dict:
    # Prefer the installed curl implementation: this embedded HTTPS server
    # times out with Python urllib on the tested B24 firmware. Do not reimplement.
    args = [
        "curl", "-k", "--noproxy", "*", "--silent", "--show-error",
        "--max-time", "6", "--get",
        f"https://{gateway}/goform/goform_get_cmd_process",
        "--data-urlencode", "isTest=false",
        "--data-urlencode", "multi_data=1",
        "--data-urlencode", "cmd=" + ",".join(FIELDS[group]),
        "-H", f"Referer: https://{gateway}/index.html",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
    ]
    proc = subprocess.run(args, capture_output=True, text=True,
                          timeout=9, check=False)
    if proc.returncode != 0:
        raise ValueError("curl read failed")
    if len(proc.stdout) > 65536:
        raise ValueError("oversized reply")
    return project(group, json.loads(proc.stdout))



def ping_gateway(gateway: str) -> dict:
    if not shutil.which("ping"):
        return {"standing": "UNKNOWN", "reason": "ping unavailable"}
    try:
        p = subprocess.run(
            ["ping", "-n", "-c", "10", "-i", "0.25", "-W", "2", gateway],
            text=True, capture_output=True, timeout=12, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"standing": "UNKNOWN", "reason": "ping execution error"}
    match = re.search(r"(\d+) packets transmitted, (\d+) received, ([\d.]+)% packet loss", p.stdout)
    rtt = re.search(r"(?:rtt|round-trip) min/avg/max/(?:mdev|stddev) = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms", p.stdout)
    if not match:
        return {"standing": "UNKNOWN", "reason": "unrecognized ping output"}
    return {"standing": "MEASURED", "sent": int(match.group(1)),
            "received": int(match.group(2)), "loss_percent": float(match.group(3)),
            "rtt_ms": ({k: float(v) for k, v in zip(
                ("min", "avg", "max", "mdev"), rtt.groups())} if rtt else None)}


def dig_gateway(gateway: str, kind: str) -> dict:
    if not shutil.which("dig"):
        return {"standing": "UNKNOWN", "reason": "dig unavailable"}
    try:
        p = subprocess.run(["dig", "+tries=1", "+time=2", "+stats", f"@{gateway}",
                            "example.com", kind], text=True, capture_output=True,
                           timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"standing": "UNKNOWN", "reason": "dig execution error"}
    rcode = re.search(r"status: ([A-Z]+)", p.stdout)
    ms = re.search(r"Query time: (\d+) msec", p.stdout)
    if p.returncode or not rcode:
        return {"standing": "UNKNOWN", "reason": "DNS query failed"}
    return {"standing": "MEASURED", "rcode": rcode.group(1),
            "query_ms": int(ms.group(1)) if ms else None}


def observe(gateway: str, *, active: bool, fetch=read_group) -> dict:
    obs = {}
    for group in FIELDS:
        try:
            obs[group] = {"standing": "OBSERVED", "fields": fetch(gateway, group)}
        except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            obs[group] = {"standing": "UNKNOWN", "reason": type(exc).__name__}
    identity = obs["identity"].get("fields", {})
    model_ok = identity.get("model_name") == "MU5358"
    measures = ({"gateway_ping": ping_gateway(gateway),
                 "dns_A": dig_gateway(gateway, "A"),
                 "dns_AAAA": dig_gateway(gateway, "AAAA")}
                if active else {"standing": "NOT_RUN"})
    return {"kind": KIND, "observed_at": datetime.now(timezone.utc).isoformat(),
            "gateway": gateway, "device_identity": "MU5358_CONFIRMED" if model_ok else "UNKNOWN_OR_DIFFERENT",
            "device": obs, "local_probes": measures,
            "constraints": {"mutated_device": False, "wan_speed_test": False,
                            "no_passwords_or_device_identifiers": True,
                            "empty_fields_mean": "UNKNOWN"},
            "interpretation": "Local-only ICMP/DNS cannot prove Wi-Fi airtime or cellular throughput."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gateway", default="192.168.0.1")
    p.add_argument("--no-probes", action="store_true")
    a = p.parse_args()
    try:
        gateway = validate_gateway(a.gateway)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    r = observe(gateway, active=not a.no_probes)
    print(json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if r["device_identity"] == "MU5358_CONFIRMED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
