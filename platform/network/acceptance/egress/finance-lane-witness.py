#!/usr/bin/env python3
"""Independent read-only Finance Carrier/loopback observation for OPEN routing.

Reuses existing Network Carrier Observer and Finance public-data admission.
Nine Finance business samples stay bounded even though the network carrier
accepts arbitrary TCP CONNECT hostnames and ports. Does not place trades,
read credentials, change VPN, or claim arbitrary direct-path privacy.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import time

NETWORK = Path(__file__).resolve().parents[2]
ROOT = Path("/etc/network-v2")
shared = runpy.run_path(str(Path(__file__).with_name("live-carrier-witness.py")))
Observer = shared["Observer"]
pid = shared["pid"]


def probe(proxy_port: int, host: str, dest_port: int) -> tuple[subprocess.CompletedProcess[str], bool]:
    result = subprocess.run(
        ["curl", "-q", "-4", "--noproxy", "", "-x", f"http://127.0.0.1:{proxy_port}",
         "-I", "-sS", "--connect-timeout", "4", "--max-time", "12",
         "-o", "/dev/null", "-w", "%{http_connect}|%{http_code}|%{time_appconnect}",
         f"https://{host}:{dest_port}/"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=14,
    )
    fields = result.stdout.strip().split("|")
    try:
        tls = (len(fields) == 3 and fields[0] == "200" and
               int(fields[1]) >= 200 and float(fields[2]) > 0)
    except ValueError:
        tls = False
    return result, tls


def no_direct_loopback_fallback(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(0.3)
        local_port = int(listener.getsockname()[1])
        probe(port, "127.0.0.1", local_port)
        try:
            conn, _ = listener.accept()
        except socket.timeout:
            return True
        else:
            conn.close()
            return False


def main() -> int:
    source = NETWORK / "consumers/finance/config/egress.json"
    installed = ROOT / "finance/egress.json"
    data = source.read_bytes()
    if data != installed.read_bytes():
        raise AssertionError("Finance installed SourceCut differs")
    native_contract = runpy.run_path(str(Path(__file__).with_name("finance-public-data.py")))
    ports = native_contract["validate_contract"](data, data)
    authority_files = sorted(
        (NETWORK / "consumers/finance/config").glob("*-authority.json")
    )
    if len(authority_files) != len(ports) or len(ports) != 9:
        raise AssertionError("Finance authority coverage incomplete")

    cases = []
    for authority in authority_files:
        d = json.loads(authority.read_text(encoding="utf-8"))
        tag = d.get("profile")
        dest = d.get("destination", {})
        host, dest_port = dest.get("host"), dest.get("port")
        if (tag not in ports or d.get("listenHost") != "127.0.0.1" or
                d.get("listenPort") != ports[tag] or
                not isinstance(host, str) or not host or
                type(dest_port) is not int or dest_port not in (443, 8443) or
                d.get("allowedTcpPorts") != [dest_port]):
            raise AssertionError("Finance independent business sample invalid")
        direct = tag in {"finance-us-treasury-public", "finance-fred-public-csv"}
        if direct == ("networkAuthority" in d):
            raise AssertionError("Finance physical Carrier/direct consumer mismatch")
        cases.append((tag, host, dest_port, "public-direct" if direct else "provider-carrier"))
    if len({case[0] for case in cases}) != 9:
        raise AssertionError("Duplicate Finance business profiles")

    finance_before = pid("network-v2-finance-egress.service")
    provider_before = pid("network-v2-gluetun-owned.service")
    observer = Observer("host")
    results = []
    try:
        time.sleep(1.1)
        observer.assert_live()
        for tag, host, dest_port, route in cases:
            endpoint = f"{host}:{dest_port}"
            before = observer.count(endpoint)
            accepted, tls = probe(ports[tag], host, dest_port)
            time.sleep(0.25)
            business_forward = observer.count(endpoint) - before
            provider_lane = route == "provider-carrier"
            business_ok = (
                accepted.returncode == 0 and tls and
                (business_forward > 0 if provider_lane else business_forward == 0)
            )

            # An independent, intentionally unresolvable hostname is admitted
            # to the Carrier in OPEN mode. Origin TLS may fail after forwarding.
            unknown_host = f"ns2-{os.getpid()}-{tag}.example.com"
            unknown = f"{unknown_host}:{dest_port}"
            before_unknown = observer.count(unknown)
            probe(ports[tag], unknown_host, dest_port)
            time.sleep(0.2)
            unknown_forward = observer.count(unknown) - before_unknown

            # The policy admits other TCP ports too; no claim of remote TLS
            # on a destination likely not serving HTTPS at port 444.
            wrong = f"{host}:444"
            before_wrong = observer.count(wrong)
            probe(ports[tag], host, 444)
            time.sleep(0.2)
            wrong_forward = observer.count(wrong) - before_wrong
            unknown_ok = (unknown_forward > 0 if provider_lane else unknown_forward == 0)
            wrong_ok = (wrong_forward > 0 if provider_lane else wrong_forward == 0)

            # Direct Finance exception has a distinct contract. Never claim
            # that we tested it for absence of local direct network routing.
            loopback_ok = no_direct_loopback_fallback(ports[tag]) if provider_lane else None
            results.append({
                "lane": tag,
                "outbound": route,
                "businessCarrierConnects": business_forward,
                "businessTLS": tls,
                "unlistedCarrierConnects": unknown_forward,
                "otherPortCarrierConnects": wrong_forward,
                "localDirectFallbackBlocked": loopback_ok,
                "pass": business_ok and unknown_ok and wrong_ok and loopback_ok is not False,
            })
            observer.assert_live()
    finally:
        observer.close()

    if pid("network-v2-finance-egress.service") != finance_before:
        raise AssertionError("Finance proxy replaced during witness")
    if pid("network-v2-gluetun-owned.service") != provider_before:
        raise AssertionError("Gluetun replaced during witness")
    if data != source.read_bytes() or data != installed.read_bytes():
        raise AssertionError("Finance SourceCut changed during witness")

    standing = "PASS" if len(results) == 9 and all(x["pass"] for x in results) else "FAIL"
    print(json.dumps({
        "schemaVersion": 1,
        "kind": "ordivon.network-v2.finance-live-lane-witness",
        "standing": standing,
        "laneCount": len(results),
        "sourceSha256": hashlib.sha256(data).hexdigest(),
        "providerPidStable": True,
        "financePidStable": True,
        "scope": "sampled read-only Finance business HTTPS plus open Carrier forwarding",
        "unproved": [
            "arbitrary DNS/DoH/IPv6 escape and every future endpoint",
            "direct Finance path local forwarding beyond explicit observations",
            "process-loaded policy digest and financial-write authority",
        ],
        "lanes": results,
    }, sort_keys=True))
    return 0 if standing == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
