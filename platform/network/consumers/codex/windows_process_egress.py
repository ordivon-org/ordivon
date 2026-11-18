#!/usr/bin/env python3
"""Read-only Windows Codex process/socket observation via mature psutil.

Profile existence, a local CONNECT response or source configuration alone
cannot prove that an existing application actually uses a VPN path.
No environment values, remote IPs, commands, credentials or payloads are output.
"""
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit

# Desktop and known child components are observed independently; no inference
# that one process socket proves the networking of its whole process tree.
TARGETS = {
    "codex.exe", "chatgpt.exe", "codex-code-mode-host.exe",
    "codex-computer-use-swift.exe",
}


def proxy_env_state(env: dict[str, str], port: int = 19781) -> str:
    http = [env[k] for k in ("HTTP_PROXY", "http_proxy") if k in env]
    https = [env[k] for k in ("HTTPS_PROXY", "https_proxy") if k in env]
    if not http and not https:
        return "UNSET"
    if not http or not https:
        return "PARTIAL"
    for value in http + https:
        try:
            target = urlsplit(value)
            if (target.scheme, target.hostname, target.port) != ("http", "127.0.0.1", port):
                return "MISMATCH"
        except ValueError:
            return "MISMATCH"
    return "SCOPED"


def socket_observation(env_state: str, proxy_count: int, tls_count: int) -> str:
    # Socket observations are independent of proxy environment variables:
    # Windows Desktop normally reads system proxy instead of HTTP_PROXY.
    # A proxy socket is positive evidence, never a universal no-bypass proof.
    if proxy_count > 0 and tls_count > 0:
        return "PROXY_AND_OTHER_TLS_SOCKETS_OBSERVED"
    if proxy_count > 0:
        return "LOCAL_PROXY_SOCKET_OBSERVED"
    if tls_count > 0:
        return "NONLOCAL_TLS_SOCKET_OBSERVED"
    return "NOT_OBSERVED"


def observe(psutil: object, profile: Path, port: int) -> dict:
    modified = profile.stat().st_mtime if profile.is_file() else None
    observed = []
    for process in psutil.process_iter(["name", "pid"]):
        if (process.info.get("name") or "").casefold() not in TARGETS:
            continue
        try:
            env = proxy_env_state(process.environ(), port)
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            env = "UNREADABLE"
        try:
            older = modified is not None and process.create_time() < modified
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            older = None
        proxy_count = tls_count = public_tcp = other_tcp = 0
        tcp_readable = True
        malformed_remote = False
        try:
            for conn in process.net_connections(kind="tcp"):
                if conn.status != "ESTABLISHED" or not conn.raddr:
                    continue
                ip, remote_port = conn.raddr[:2]
                if ip in ("127.0.0.1", "::1") and remote_port == port:
                    proxy_count += 1
                    continue
                other_tcp += 1
                if ip not in ("127.0.0.1", "::1") and remote_port == 443:
                    tls_count += 1
                try:
                    public_tcp += bool(ipaddress.ip_address(ip).is_global)
                except ValueError:
                    malformed_remote = True
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            tcp_readable = False
        udp_count = None
        try:
            # A UDP endpoint records a local bind, not successful QUIC/DNS
            # datagrams, their destination, or their actual forwarding path.
            udp_count = len(process.net_connections(kind="udp"))
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            pass
        observed.append({
            "process": process.info.get("name"),
            "pid": process.pid,
            "profileNewerThanProcess": older,
            "proxyEnvironment": env,
            "proxyTcpSockets": proxy_count if tcp_readable else None,
            "nonlocalTlsTcpSockets": tls_count if tcp_readable else None,
            "otherTcpSockets": other_tcp if tcp_readable else None,
            "publicTcpSockets": public_tcp if tcp_readable else None,
            "publicTcpStanding": (
                "DIRECT_PUBLIC_TCP_SOCKET_OBSERVED" if public_tcp
                else "UNKNOWN" if not tcp_readable or malformed_remote
                else "NOT_OBSERVED_IN_SNAPSHOT"
            ),
            "udpBoundEndpoints": udp_count,
            "udpStanding": (
                "UNKNOWN" if udp_count is None else
                "BOUND_ENDPOINTS_NOT_DATAGRAM_FLOW" if udp_count
                else "NOT_OBSERVED_IN_SNAPSHOT"
            ),
            "socketObservation": (
                socket_observation(env, proxy_count, tls_count)
                if tcp_readable else "UNREADABLE"
            ),
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.network.codex.windows-process-proxy-observation",
        "standing": "END_TO_END_EGRESS_UNKNOWN",
        "observedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "expectedProxy": f"127.0.0.1:{port}",
        "proxyPortRole": (
            "windows-desktop-shared-carrier" if port == 19781
            else "explicitly-selected-proxy"
        ),
        "processSocketScope": "point-in-time TCP and UDP bind metadata; no historical flows",
        "windowsSystemProxyPolicy": "NOT_EVALUATED",
        "profileExists": modified is not None,
        "observedProcessCount": len(observed),
        "processes": sorted(observed, key=lambda row: (row["process"], row["pid"])),
        "unproved": [
            "real Codex API request ownership and full request tracing",
            "independent same-request Gluetun Carrier forwarding",
            "all process descendants and unobserved short-lived sockets",
            "interactive-user system proxy configuration",
            "Windows WFP permitted/blocked flow auditing",
            "UDP/QUIC and DNS/DoH datagram destinations or content",
            "historical, short-lived, child-process and unsampled IPv6 bypass",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=Path.home() / ".codex" / ".env")
    parser.add_argument("--proxy-port", type=int, default=19781)
    args = parser.parse_args()
    import psutil
    print(json.dumps(observe(psutil, args.profile, args.proxy_port), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
