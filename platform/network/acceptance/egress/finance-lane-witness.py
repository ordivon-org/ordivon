#!/usr/bin/env python3
"""Independent, read-only nine-lane Finance Carrier/loopback observation.

Uses the existing Network Carrier Observer; no credentials, financial writes,
route changes, new VPN or service restarts. Direct egress proof is bounded.
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
        tls = len(fields) == 3 and fields[0] == "200" and float(fields[2]) > 0
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
            conn, _addr = listener.accept()
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
    config = json.loads(data)
    expected_outbounds = [
        {"type": "http", "tag": "provider-carrier",
         "server": "10.252.246.2", "server_port": 19680},
        {"type": "direct", "tag": "public-direct"},
    ]
    if config["outbounds"] != expected_outbounds or config["route"]["rules"][-1] != {"action": "reject"}:
        raise AssertionError("Finance outbound policy drift")
    inbounds = config["inbounds"]
    routes = config["route"]["rules"][:-1]
    if len(inbounds) != 9 or len(routes) != 9:
        raise AssertionError("Finance lane count drift")
    ports = {x["tag"]: int(x["listen_port"]) for x in inbounds
             if x.get("listen") == "127.0.0.1"}
    if len(ports) != 9:
        raise AssertionError("Finance inbound not uniquely loopback scoped")
    finance_pid = pid("network-v2-finance-egress.service")
    provider_pid = pid("network-v2-gluetun-owned.service")
    observer = Observer("host")
    results = []
    try:
        time.sleep(1.1)
        if observer.process.poll() is not None:
            raise AssertionError("Carrier observer unavailable")
        for rule in routes:
            labels = rule.get("inbound")
            tag = labels[0] if isinstance(labels, list) and len(labels) == 1 else ""
            host, port, route = rule.get("domain"), rule.get("port"), rule.get("outbound")
            if (tag not in ports or not isinstance(host, str) or not host
                    or not isinstance(port, int) or port not in (443, 8443)
                    or route not in ("provider-carrier", "public-direct")
                    or rule.get("action") != "route"):
                raise AssertionError("Invalid Finance lane contract")
            endpoint = f"{host}:{port}"
            before = observer.count(endpoint)
            # Public data services can transiently fail one HEAD request.
            # Retry only the permitted probe; never forgive any observed
            # forbidden outbound effect or incorrect Carrier selection.
            permitted = False
            forwarded = 0
            tls = False
            for _attempt in range(2):
                allowed, attempt_tls = probe(ports[tag], host, port)
                time.sleep(0.25)
                forwarded = observer.count(endpoint) - before
                tls = tls or attempt_tls
                permitted = (allowed.returncode == 0 and attempt_tls and
                             (forwarded > 0 if route == "provider-carrier" else forwarded == 0))
                if permitted:
                    break

            unknown = f"ns2-{os.getpid()}-{tag}.example.com:{port}"
            before_unknown = observer.count(unknown)
            denied, denied_tls = probe(ports[tag], unknown.rsplit(":", 1)[0], port)
            time.sleep(0.15)
            unknown_forwarded = observer.count(unknown) - before_unknown
            unknown_ok = denied.returncode != 0 and not denied_tls and unknown_forwarded == 0

            wrong = f"{host}:444"
            before_wrong = observer.count(wrong)
            wrong_result, wrong_tls = probe(ports[tag], host, 444)
            time.sleep(0.15)
            wrong_forwarded = observer.count(wrong) - before_wrong
            wrong_ok = wrong_result.returncode != 0 and not wrong_tls and wrong_forwarded == 0

            loopback_ok = no_direct_loopback_fallback(ports[tag])
            results.append({
                "lane": tag, "outbound": route, "allowedCarrierConnects": forwarded,
                "allowedTLS": tls, "unknownCarrierConnects": unknown_forwarded,
                "wrongPortCarrierConnects": wrong_forwarded,
                "localDirectFallbackBlocked": loopback_ok,
                "pass": permitted and unknown_ok and wrong_ok and loopback_ok,
            })
    finally:
        observer.close()
    if len({x["lane"] for x in results}) != 9:
        raise AssertionError("Finance lane coverage incomplete")
    if pid("network-v2-finance-egress.service") != finance_pid:
        raise AssertionError("Finance proxy replaced during witness")
    if pid("network-v2-gluetun-owned.service") != provider_pid:
        raise AssertionError("Gluetun replaced during witness")
    if data != source.read_bytes() or data != installed.read_bytes():
        raise AssertionError("Finance SourceCut changed during witness")

    standing = "PASS" if all(x["pass"] for x in results) else "FAIL"
    print(json.dumps({
        "schemaVersion": 1, "kind": "ordivon.network-v2.finance-live-lane-witness",
        "standing": standing, "laneCount": len(results),
        "sourceSha256": hashlib.sha256(data).hexdigest(),
        "providerPidStable": True, "financePidStable": True,
        "scope": "sampled read-only IPv4 HTTPS Carrier and loopback observations",
        "unproved": ["arbitrary DNS/DoH/IPv6 escape", "other host egress",
                     "process-loaded policy digest", "financial-write authority"],
        "lanes": results,
    }, sort_keys=True))
    return 0 if standing == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
