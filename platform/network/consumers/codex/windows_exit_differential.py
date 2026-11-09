#!/usr/bin/env python3
"""Windows native curl positive/negative control for advisory proxy egress.

Uses mature curl instead of a custom network stack. This is a bounded,
read-only HTTPS observation of curl.exe under the invoking Windows identity:
it is NOT proof that any running Codex/ChatGPT process uses the same route.
No raw public IP, credential, HTTP response or proxy payload is emitted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import ipaddress
import secrets
import json
import subprocess
import sys

ENDPOINT = "https://ipinfo.io/json"
PROXY_HOST = "127.0.0.1"
DEFAULT_PORT = 19781


def _probe(mode: str, *, curl: str, port: int, hmac_key: bytes, runner=subprocess.run) -> dict:
    if mode not in {"proxy", "direct"}:
        raise ValueError("Unknown curl transport")
    if not 1 <= port <= 65535:
        raise ValueError("Invalid proxy port")
    # curl -q must be FIRST; bypass .curlrc and explicitly override environment
    # proxies in BOTH directions, preventing accidental test-path ambiguity.
    args = [
        curl, "-q", "-4", "--connect-timeout", "5", "--max-time", "12",
        "--noproxy", "" if mode == "proxy" else "*",
        "--proxy", f"http://{PROXY_HOST}:{port}" if mode == "proxy" else "",
        "--fail", "--silent", "--show-error", ENDPOINT,
    ]
    try:
        proc = runner(args, capture_output=True, text=True, timeout=17,
                      check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"outcome": "UNKNOWN", "reason": "CURL_UNAVAILABLE_OR_TIMEOUT"}
    # Do not expose curl stderr; it may contain machine details.
    if proc.returncode != 0:
        return {"outcome": "FAILED", "reason": "HTTPS_REQUEST_NONZERO"}
    try:
        data = json.loads(proc.stdout)
        addr = ipaddress.ip_address(data["ip"])
        if addr.version != 4 or not addr.is_global:
            raise ValueError("Not a globally routed IPv4 exit address")
    except (TypeError, ValueError, KeyError, AttributeError):
        return {"outcome": "UNKNOWN", "reason": "UNTRUSTED_EXIT_RESPONSE"}
    return {
        "outcome": "HTTPS_OK",
        "exitTag": hmac.new(hmac_key, str(addr).encode("ascii"), hashlib.sha256).hexdigest(),
    }


def evaluate(*, curl: str = "curl.exe", port: int = DEFAULT_PORT,
             runner=subprocess.run) -> dict:
    # Per-run secret means the exported equality witness cannot be reversed
    # via brute-forcing the small IPv4 address space or linked across runs.
    session_key = secrets.token_bytes(32)
    direct = _probe("direct", curl=curl, port=port, hmac_key=session_key, runner=runner)
    proxy = _probe("proxy", curl=curl, port=port, hmac_key=session_key, runner=runner)
    compared = (direct["outcome"] == "HTTPS_OK"
                and proxy["outcome"] == "HTTPS_OK")
    distinct = (compared and direct["exitTag"] != proxy["exitTag"])
    return {
        "schemaVersion": 1,
        "kind": "ordivon.network.windows-native-exit-differential",
        "observedAtUtc": datetime.now(timezone.utc).isoformat(),
        "standing": ("DIRECT_EXIT_COUNTEREXAMPLE" if distinct else "UNKNOWN"),
        "direct": direct,
        "proxy": proxy,
        "samePublicExit": (not distinct) if compared else None,
        "fingerprintScope": "ephemeral per-run keyed HMAC; not cross-run comparable",
        "processScope": "controlled curl.exe invocation, NOT Codex/ChatGPT",
        "scope": "Two explicit IPv4 HTTPS calls to ipinfo.io; observational only",
        "unproved": [
            "mandatory Windows WFP per-app egress policy",
            "actual Codex/ChatGPT application request attribution",
            "UDP, QUIC, DoH, IPv6 and other native application paths",
            "provider-path process correlation without independent packet witness",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curl-path", default="curl.exe")
    parser.add_argument("--proxy-port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Live Windows native acceptance requires Windows")
    result = evaluate(curl=args.curl_path, port=args.proxy_port)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    # UNKNOWN is a qualified observation, not a test PASS. A real observed
    # counterexample is nevertheless a successful falsification result.
    return 0 if result["standing"] == "DIRECT_EXIT_COUNTEREXAMPLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
