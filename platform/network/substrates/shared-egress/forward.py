#!/usr/bin/env python3
"""Non-destructive, exact legacy Docker FORWARD exception convergence.

Only two owned rule fingerprints are accepted. A service restart never
removes live shared rules; deliberate retirement is a separate operator act.
"""
from __future__ import annotations

import ipaddress
import os
import re
import subprocess
import sys

MARKER = "network-v2-browserless-forward-v1"


class ForwardError(RuntimeError):
    pass


def config() -> tuple[str, str]:
    interface = os.environ.get("HOST_IF", "")
    cidr = os.environ.get("NS_CIDR", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", interface):
        raise ForwardError("invalid HOST_IF")
    try:
        network = ipaddress.IPv4Network(cidr, strict=True)
        host = ipaddress.IPv4Interface(os.environ.get("HOST_ADDR", ""))
        peer = ipaddress.IPv4Interface(os.environ.get("NS_ADDR", ""))
    except ValueError as exc:
        raise ForwardError("invalid shared forwarding IPv4 configuration") from exc
    # One veth pair needs only two endpoints (/30, or RFC 3021 /31).
    # Never accept a drifted wide subnet merely because it parses as IPv4.
    if network.prefixlen not in (30, 31):
        raise ForwardError("shared forwarding subnet must be point-to-point sized")
    if host.network != network or peer.network != network or host.ip == peer.ip:
        raise ForwardError("shared forwarding subnet does not match veth endpoints")
    return interface, str(network)


def rules(interface: str, cidr: str) -> tuple[tuple[str, ...], ...]:
    return (
        ("-i", interface, "-s", cidr, "-m", "comment",
         "--comment", MARKER, "-j", "ACCEPT"),
        ("-o", interface, "-d", cidr, "-m", "conntrack",
         "--ctstate", "RELATED,ESTABLISHED", "-m", "comment",
         "--comment", MARKER, "-j", "ACCEPT"),
    )


def command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("/usr/bin/iptables-legacy", "-w", "5", *args),
        capture_output=True, text=True, check=False, timeout=15,
    )


def require_success(result: subprocess.CompletedProcess[str], operation: str) -> None:
    if result.returncode != 0:
        raise ForwardError(f"{operation}: exit {result.returncode}: {result.stderr.strip()}")


def inspect(expected: tuple[tuple[str, ...], ...]) -> tuple[bool, bool]:
    listing = command("-S", "FORWARD")
    require_success(listing, "iptables -S FORWARD")
    owned = [
        line for line in listing.stdout.splitlines()
        if f"--comment {MARKER}" in line
    ]
    present: list[bool] = []
    for rule in expected:
        result = command("-C", "FORWARD", *rule)
        if result.returncode not in (0, 1):
            raise ForwardError(f"iptables -C failed with {result.returncode}")
        present.append(result.returncode == 0)
    if len(owned) != sum(present):
        raise ForwardError(
            "unrecognized or duplicated shared forwarding marker; refusing mutation"
        )
    return (present[0], present[1])


def verify(expected: tuple[tuple[str, ...], ...]) -> None:
    if inspect(expected) != (True, True):
        raise ForwardError("shared forwarding exceptions incomplete")


def ensure(expected: tuple[tuple[str, ...], ...]) -> None:
    present = inspect(expected)
    if present == (True, True):
        print("SHARED_EGRESS_FORWARD_REUSED=PASS")
        return
    for rule, already_present in zip(expected, present):
        if not already_present:
            require_success(command("-I", "FORWARD", "1", *rule), "iptables -I")
    verify(expected)
    print("SHARED_EGRESS_FORWARD_CONVERGED=PASS")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("ensure", "verify"):
        print("usage: shared-egress-forward [ensure|verify]", file=sys.stderr)
        return 2
    try:
        wanted = rules(*config())
        if sys.argv[1] == "ensure":
            ensure(wanted)
        else:
            verify(wanted)
            print("SHARED_EGRESS_FORWARD_VERIFIED=PASS")
    except (ForwardError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"shared-egress-forward: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
