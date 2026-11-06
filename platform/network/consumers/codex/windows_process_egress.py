#!/usr/bin/env python3
"""Read-only Windows Codex process/socket observation via mature psutil.

Profile existence, a local CONNECT response or source configuration alone
cannot prove that an existing application actually uses a VPN path.
No environment values, remote IPs, commands, credentials or payloads are output.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlsplit

TARGETS = {"codex.exe", "chatgpt.exe", "codex-code-mode-host.exe"}


def proxy_env_state(env: dict[str, str], port: int = 19982) -> str:
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
    if env_state == "SCOPED" and proxy_count > 0:
        return "SCOPED_PROXY_SOCKET_OBSERVED"
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
        proxy_count = tls_count = 0
        socket_readable = True
        try:
            for conn in process.net_connections(kind="tcp"):
                if conn.status != "ESTABLISHED" or not conn.raddr:
                    continue
                ip, remote_port = conn.raddr
                if ip in ("127.0.0.1", "::1") and remote_port == port:
                    proxy_count += 1
                elif ip not in ("127.0.0.1", "::1") and remote_port == 443:
                    tls_count += 1
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            socket_readable = False
        observed.append({
            "process": process.info.get("name"),
            "pid": process.pid,
            "profileNewerThanProcess": older,
            "proxyEnvironment": env,
            "proxyTcpSockets": proxy_count if socket_readable else None,
            "nonlocalTlsTcpSockets": tls_count if socket_readable else None,
            "socketObservation": (
                socket_observation(env, proxy_count, tls_count)
                if socket_readable else "UNREADABLE"
            ),
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.network.codex.windows-process-proxy-observation",
        "standing": "END_TO_END_EGRESS_UNKNOWN",
        "observedAtUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "expectedProxy": f"127.0.0.1:{port}",
        "profileExists": modified is not None,
        "observedProcessCount": len(observed),
        "processes": sorted(observed, key=lambda row: (row["process"], row["pid"])),
        "unproved": [
            "actual Codex API request ownership",
            "independent Gluetun Carrier forwarding",
            "Windows VPN/DNS/IPv6 routing",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=Path.home() / ".codex" / ".env")
    parser.add_argument("--proxy-port", type=int, default=19982)
    args = parser.parse_args()
    import psutil
    print(json.dumps(observe(psutil, args.profile, args.proxy_port), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
