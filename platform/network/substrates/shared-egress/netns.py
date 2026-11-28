#!/usr/bin/env python3
"""One-shot, non-destructive shared-egress netns/veth convergence.

The Linux kernel owns interfaces and namespace lifetime; systemd owns service
admission and ordering. Existing topology is never deleted or silently repaired.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import subprocess
import sys
from pathlib import Path

NAMESPACE = "nv2-browserless-prod"


class TopologyError(RuntimeError):
    pass


def command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ("/usr/bin/ip", *args), text=True, capture_output=True, check=False, timeout=10
    )
    if check and result.returncode != 0:
        raise TopologyError(f"ip {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def config() -> tuple[str, str, str, str]:
    values = tuple(os.environ.get(name, "") for name in ("HOST_IF", "NS_IF", "HOST_ADDR", "NS_ADDR"))
    host_if, ns_if, host_addr, ns_addr = values
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", iface) for iface in (host_if, ns_if)):
        raise TopologyError("invalid or missing veth interface names")
    if host_if == ns_if:
        raise TopologyError("veth endpoint names must differ")
    try:
        host = ipaddress.IPv4Interface(host_addr)
        peer = ipaddress.IPv4Interface(ns_addr)
    except ValueError as exc:
        raise TopologyError("invalid IPv4 endpoint address") from exc
    if host.network != peer.network or host.ip == peer.ip:
        raise TopologyError("veth endpoints must have distinct addresses on one subnet")
    return host_if, ns_if, str(host), str(peer)


def link(name: str, ns: str | None = None) -> dict:
    args = ("-j", "-d") + (("-n", ns) if ns else ()) + ("link", "show", "dev", name)
    value = json.loads(command(*args).stdout)
    if len(value) != 1:
        raise TopologyError(f"unexpected link count for {name}")
    return value[0]


def ipv4(name: str, ns: str | None = None) -> set[tuple[str, int]]:
    args = ("-j",) + (("-n", ns) if ns else ()) + ("-4", "addr", "show", "dev", name)
    value = json.loads(command(*args).stdout)
    if len(value) != 1:
        raise TopologyError(f"unexpected address link count for {name}")
    return {
        (entry["local"], entry["prefixlen"])
        for entry in value[0].get("addr_info", [])
        if entry.get("family") == "inet"
    }


def verify(host_if: str, ns_if: str, host_addr: str, ns_addr: str) -> None:
    if not Path(f"/run/netns/{NAMESPACE}").exists():
        raise TopologyError("shared network namespace missing")
    host = link(host_if)
    peer = link(ns_if, NAMESPACE)
    if host.get("linkinfo", {}).get("info_kind") != "veth":
        raise TopologyError("host link is not a veth")
    if peer.get("linkinfo", {}).get("info_kind") != "veth":
        raise TopologyError("namespace link is not a veth")
    if host.get("link_index") != peer.get("ifindex") or peer.get("link_index") != host.get("ifindex"):
        raise TopologyError("veth endpoints do not form the expected pair")
    if "UP" not in host.get("flags", ()) or "UP" not in peer.get("flags", ()):
        raise TopologyError("veth endpoint administratively down")
    if "UP" not in link("lo", NAMESPACE).get("flags", ()):
        raise TopologyError("namespace loopback administratively down")
    for iface, ns, expected in (
        (host_if, None, host_addr),
        (ns_if, NAMESPACE, ns_addr),
    ):
        addr = ipaddress.IPv4Interface(expected)
        if ipv4(iface, ns) != {(str(addr.ip), addr.network.prefixlen)}:
            raise TopologyError(f"unexpected IPv4 addresses on {iface}")
    for family in ("-4", "-6"):
        route = json.loads(command("-j", "-n", NAMESPACE, family, "route", "show", "default").stdout)
        if route:
            raise TopologyError(f"unexpected {family} namespace default route")


def ensure(host_if: str, ns_if: str, host_addr: str, ns_addr: str) -> None:
    namespace_exists = Path(f"/run/netns/{NAMESPACE}").exists()
    host_exists = Path(f"/sys/class/net/{host_if}").exists()
    if namespace_exists or host_exists:
        if not (namespace_exists and host_exists):
            raise TopologyError("partial shared topology; refusing destructive recovery")
        verify(host_if, ns_if, host_addr, ns_addr)
        print("SHARED_EGRESS_NETNS_REUSED=PASS")
        return

    # Cold boot only. Never remove pre-existing namespace, veth or their users.
    # If startup fails partway through, preserve evidence and refuse repair
    # until the partial topology is explicitly reconciled.
    command("netns", "add", NAMESPACE)
    command("link", "add", host_if, "type", "veth", "peer", "name", ns_if)
    command("link", "set", ns_if, "netns", NAMESPACE)
    command("addr", "add", host_addr, "dev", host_if)
    command("link", "set", host_if, "up")
    command("-n", NAMESPACE, "addr", "add", ns_addr, "dev", ns_if)
    command("-n", NAMESPACE, "link", "set", "lo", "up")
    command("-n", NAMESPACE, "link", "set", ns_if, "up")
    verify(host_if, ns_if, host_addr, ns_addr)
    print("SHARED_EGRESS_NETNS_CREATED=PASS")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("ensure", "verify"):
        print("usage: shared-egress-netns [ensure|verify]", file=sys.stderr)
        return 2
    try:
        params = config()
        if sys.argv[1] == "ensure":
            ensure(*params)
        else:
            verify(*params)
            print("SHARED_EGRESS_NETNS_VERIFIED=PASS")
    except (TopologyError, OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"shared-egress-netns: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
