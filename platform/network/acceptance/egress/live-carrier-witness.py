#!/usr/bin/env python3
"""NS2: scoped LIVE source/installed/consumer/carrier witness.

This is not a full route noninterference proof. Capture stays in memory; only
parsed CONNECT authorities for expected requests are counted. No pcap/log,
credential read, iptables changes or service restart is performed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time

NETWORK = Path(__file__).resolve().parents[2]
ROOT = Path("/etc/network-v2")
NAMESPACE = "nv2-browserless-prod"
CARRIER_PORT = 19680
CASES = ("codex", "discord", "model-provider", "supply-chain", "x-reality", "claude", "chat-ingress")
# CONNECT targets can contain bracketed IPv6 literals, not only DNS/IPv4.
# Missing this case makes a leaking IPv6 CONNECT invisible to the Carrier spy.
CONNECT_AUTHORITY = re.compile(r"CONNECT\s+(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9.-]+):(\d+)\s+HTTP/1")


def command(*args: str, timeout: float = 8) -> str:
    return subprocess.check_output(args, text=True, timeout=timeout).strip()


def pid(unit: str) -> int:
    if command("systemctl", "is-active", unit) != "active":
        raise AssertionError(f"{unit}: not active")
    value = command("systemctl", "show", "-P", "MainPID", unit)
    if not value.isdecimal() or int(value) < 2:
        raise AssertionError(f"{unit}: no running process")
    return int(value)


def contract(name: str) -> dict:
    filename = "sing-box.json" if name in ("codex", "claude", "chat-ingress") else "egress.json"
    source = NETWORK / "consumers" / name / "config" / filename
    installed = ROOT / name / filename
    b = source.read_bytes()
    if b != installed.read_bytes():
        raise AssertionError(f"{name}: installed SourceCut diverges")
    config = json.loads(b)
    if config["route"]["rules"][-1] != {"action": "reject"}:
        raise AssertionError(f"{name}: no terminal reject rule")
    if config["outbounds"] != [{
        "type": "http", "tag": "provider-carrier",
        "server": "10.252.246.2", "server_port": CARRIER_PORT
    }]:
        raise AssertionError(f"{name}: physical carrier contract changed")
    host = config["route"]["rules"][0]["domain"][0]
    ports = config["route"]["rules"][0]["port"]
    if ports not in (443, [443]):
        raise AssertionError(f"{name}: expected scoped TLS port")
    if name == "codex":
        relay = (NETWORK / "consumers/codex/systemd/network-v2-codex-relay.service").read_text()
        match = re.search(r"systemd-socket-activate -l 127\.0\.0\.1:(\d+)", relay)
        assert match is not None
        port = int(match.group(1))
    elif name in ("claude", "chat-ingress"):
        relay = (NETWORK / f"consumers/{name}/systemd/network-v2-{name}-relay.service").read_text()
        match = re.search(r"systemd-socket-activate -l 127\.0\.0\.1:(\d+)", relay)
        assert match is not None, f"{name}: no source-bound host relay"
        assert config["inbounds"][0]["listen"] == "127.0.0.1"
        if name == "claude":
            ready = (NETWORK / "consumers/claude/ready.sh").read_text()
            client = re.search(r"^client_proxy=http://10\.252\.247\.1:(\d+)$", ready, re.M)
            assert client is not None
            port = int(client.group(1))
            proxy_host = "10.252.247.1"
            probe_namespace = "nv2-claude-client"
        else:
            port = int(match.group(1))
            proxy_host = "127.0.0.1"
            probe_namespace = None
    else:
        assert config["inbounds"][0]["listen"] == "127.0.0.1"
        port = int(config["inbounds"][0]["listen_port"])
    unit = (
        "network-v2-codex-proxy.service" if name == "codex"
        else f"network-v2-{name}-proxy.service" if name in ("claude", "chat-ingress")
        else f"network-v2-{name}-egress.service"
    )
    return {
        "consumer": name, "proxyPort": port, "allowedHost": host,
        "proxyHost": proxy_host if name in ("claude", "chat-ingress") else "127.0.0.1",
        "probeNamespace": probe_namespace if name in ("claude", "chat-ingress") else None,
        "sensor": "namespace" if name in ("codex", "claude", "chat-ingress") else "host",
        "sourceSha256": hashlib.sha256(b).hexdigest(),
        "unit": unit, "pid": pid(unit),
    }


class Observer:
    def __init__(self, kind: str) -> None:
        prefix = ["ip", "netns", "exec", NAMESPACE] if kind == "namespace" else []
        self.process = subprocess.Popen(
            [*prefix, "tcpdump", "-i", "any", "-n", "-l", "-A", "-s", "410",
             f"tcp port {CARRIER_PORT}"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, errors="replace", bufsize=1,
        )
        self.seen: list[tuple[str, int]] = []
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            for m in CONNECT_AUTHORITY.finditer(line):
                if len(self.seen) >= 10000:
                    return
                # No raw packet payloads, auth headers or packet files are stored.
                self.seen.append((m.group(1).lower(), int(m.group(2))))

    def count(self, target: str) -> int:
        host, port = target.rsplit(":", 1)
        return self.seen.count((host.lower(), int(port)))

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.thread.join(timeout=3)


def run(names: list[str]) -> dict:
    data = [contract(n) for n in names]
    provider_before = pid("network-v2-gluetun-owned.service")
    observations: list[dict] = []
    kinds = set(d["sensor"] for d in data)
    observers: dict[str, Observer] = {}
    try:
        for kind in kinds:
            observers[kind] = Observer(kind)
        time.sleep(1.1)
        if any(o.process.poll() is not None for o in observers.values()):
            raise AssertionError("packet observer not running; no negative proof")
        for c in data:
            observer = observers[c["sensor"]]
            forbidden = f"ns2-{c['consumer']}-{os.getpid()}.example.com"
            for scenario, target in (
                ("allowed", f"{c['allowedHost']}:443"),
                ("unknown-host", f"{forbidden}:443"),
                ("wrong-port", f"{c['allowedHost']}:444"),
                # Literal targets bypass DNS-name allowlisting; both families
                # must produce no upstream Carrier CONNECT.
                ("ipv4-literal", "1.1.1.1:443"),
                ("ipv6-literal", "[2606:4700:4700::1111]:443"),
            ):
                before = observer.count(target)
                prefix = (["ip", "netns", "exec", c["probeNamespace"]]
                          if c["probeNamespace"] else [])
                result = subprocess.run([*prefix,
                    "curl", "-q", "-4", "--noproxy", "",
                    "-x", f"http://{c['proxyHost']}:{c['proxyPort']}",
                    "-I", "-sS", "--connect-timeout", "4", "--max-time", "9",
                    "-o", "/dev/null", "-w", "%{http_connect}/%{http_code}",
                    f"https://{target}/",
                ], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    timeout=11)
                time.sleep(0.3)
                forwarded = observer.count(target) - before
                accepted = forwarded > 0 and result.returncode == 0
                # The sing-box native listener can acknowledge CONNECT 200
                # before terminating a rejected route. A nonzero curl exit
                # AND zero observed upstream delivery are both required.
                rejected = forwarded == 0 and result.returncode != 0
                observations.append({
                    "consumer": c["consumer"], "scenario": scenario,
                    "observer": c["sensor"], "forwardedConnects": forwarded,
                    "proxyAndOriginHttp": result.stdout, "curlExit": result.returncode,
                    "pass": accepted if scenario == "allowed" else rejected,
                })
        time.sleep(0.7)
    finally:
        for o in observers.values():
            o.close()
    for c in data:
        if pid(c["unit"]) != c["pid"]:
            raise AssertionError(f"{c['consumer']}: process replaced during witness")
        filename = "sing-box.json" if c["consumer"] in ("codex", "claude", "chat-ingress") else "egress.json"
        source = NETWORK / "consumers" / c["consumer"] / "config" / filename
        installed = ROOT / c["consumer"] / filename
        if source.read_bytes() != installed.read_bytes() or (
            hashlib.sha256(source.read_bytes()).hexdigest() != c["sourceSha256"]
        ):
            raise AssertionError(f"{c['consumer']}: SourceCut changed during witness")
    if pid("network-v2-gluetun-owned.service") != provider_before:
        raise AssertionError("Physical VPN provider restarted during witness")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.network-v2.ns2-live-carrier-witness",
        "standing": "PASS" if all(x["pass"] for x in observations) else "FAIL",
        "scope": "sampled scoped HTTP CONNECT (DNS names, IPv4/IPv6 IP literals) -> shared Carrier; not IPv6 transport path",
        "unproved": ["DNS/DoH indirect exits", "IPv6 direct/UDP egress", "Finance direct exception",
                     "all local app process binding", "loaded memory policy digest"],
        "observedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "providerPidStable": True, "consumerCount": len(data),
        "cases": observations,
        "consumerSourceCuts": [
            {"consumer": c["consumer"], "sha256": c["sourceSha256"], "pid": c["pid"]}
            for c in data
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consumers", nargs="+", choices=CASES, default=list(CASES))
    args = parser.parse_args()
    receipt = run(args.consumers)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["standing"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
