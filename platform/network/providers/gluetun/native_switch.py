#!/usr/bin/env python3
"""One-shot, guarded adapter to Gluetun's existing authenticated VPN API.

No separate VPN, daemon, background queue, new provider, public control port,
or bypass of the original Gluetun kill switch.  The default is read-only.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request

import native_profile as native
import quality_history as quality
import observe_active as observer

AUTH = Path("/var/lib/network-v2/gluetun/auth/config.toml")
API_URL = "http://127.0.0.1:8000/v1/vpn/settings"
CONTAINER = "network-v2-gluetun-owned-r1"
LOCK = Path("/run/network-v2-gluetun-native-switch.lock")
LAST_SWITCH = Path("/run/network-v2-gluetun-native-switch-last-attempt")
COOLDOWN = timedelta(minutes=10)


def last_attempt() -> datetime | None:
    try:
        raw = LAST_SWITCH.read_text(encoding="ascii").strip()
        result = datetime.fromisoformat(raw)
        if result.tzinfo is None or result > datetime.now(timezone.utc):
            return None
        return result
    except (OSError, ValueError):
        return None


def mark_attempt() -> None:
    # The lock is already owned by the caller. Record BEFORE the native PUT,
    # since a network timeout does not prove the upstream ignored the request.
    LAST_SWITCH.write_text(datetime.now(timezone.utc).isoformat(), encoding="ascii")
    os.chmod(LAST_SWITCH, 0o600)



def protected_key() -> str:
    stat = AUTH.lstat()
    if stat.st_uid != 0 or stat.st_mode & 0o077 or not AUTH.is_file():
        raise ValueError("Gluetun native control auth config must be root-only")
    roles = tomllib.loads(AUTH.read_text(encoding="utf-8")).get("roles", [])
    selected = [r for r in roles
                if r.get("name") == "ordivon-native-country-switch"]
    if len(selected) != 1:
        raise ValueError("Missing unique authorized country-switch role")
    r = selected[0]
    if r.get("auth") != "apikey":
        raise ValueError("Native country-switch role is not API-key authenticated")
    if set(r.get("routes", [])) != {"GET /v1/vpn/settings", "PUT /v1/vpn/settings"}:
        raise ValueError("Native country-switch role has unexpected permissions")
    token = r.get("apikey")
    if not isinstance(token, str) or len(token) < 28:
        raise ValueError("No adequate Gluetun control credential")
    return token


def country_patch(country: str, allowed: set[str]) -> dict:
    if country not in allowed or country == "Hong Kong":
        raise ValueError("Cannot apply a country outside policy")
    return {"provider": {"server_selection": {"countries": [country]}}}


def selected_snapshot(raw: dict, allowed: set[str]) -> dict:
    if raw.get("type") != "wireguard":
        raise ValueError("Unexpected VPN type")
    provider = raw.get("provider", {})
    if provider.get("name") != "surfshark":
        raise ValueError("Unexpected VPN provider")
    s = provider.get("server_selection", {})
    countries = s.get("countries")
    if not isinstance(countries, list) or not countries or any(
        not isinstance(c, str) or c not in allowed or c == "Hong Kong"
        for c in countries
    ):
        raise ValueError("Gluetun control country selection violates policy")
    if any(s.get(field) for field in ("regions", "cities", "hostnames", "names",
                                     "isps", "numbers")):
        raise ValueError("Unexpected other native server selection filters")
    if len(countries) != len(set(countries)):
        raise ValueError("Duplicate native selected country")
    return {"countries": list(countries), "vpn": raw.get("type"), "provider": provider.get("name")}


def internal_http(method: str) -> int:
    # Run only in Gluetun's own loopback namespace. The API is NOT published.
    if method not in ("GET", "PUT"):
        raise ValueError("Unsupported API verb")
    try:
        key = protected_key()
    except (OSError, ValueError, tomllib.TOMLDecodeError) as e:
        print(json.dumps({"standing": "AUTH_NOT_CONFIGURED",
                          "reasonClass": type(e).__name__}))
        return 42
    payload = sys.stdin.read() if method == "PUT" else None
    req = urllib.request.Request(
        API_URL, data=payload.encode() if payload is not None else None,
        headers={"X-API-Key": key, "Content-Type": "application/json"},
        method=method,
    )
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=16) as response:
            body = response.read(50000)
            status = response.status
        if method == "GET":
            raw = json.loads(body)
            # Only emit the schema fields needed, NEVER serialise VPN secrets.
            p = raw.get("provider", {})
            output = {
                "status": status, "type": raw.get("type"),
                "provider": {
                    "name": p.get("name"), "server_selection": {
                        x: p.get("server_selection", {}).get(x)
                        for x in ("countries", "regions", "cities", "hostnames",
                                  "names", "isps", "numbers")
                    },
                },
            }
        else:
            output = {"status": status, "outcome": body.decode(errors="replace")[:200]}
        print(json.dumps(output))
        return 0 if status == 200 else 3
    except urllib.error.HTTPError as exc:
        print(json.dumps({"standing": "NATIVE_API_HTTP_REJECTED", "status": exc.code}))
        return 3
    except (OSError, ValueError) as exc:
        print(json.dumps({"standing": "NATIVE_API_UNKNOWN", "reasonClass": type(exc).__name__}))
        return 3


def container_pid() -> str:
    data = subprocess.run(
        ["/usr/bin/podman", "inspect", CONTAINER,
         "--format", "{{.State.Pid}}"],
        capture_output=True, text=True, check=True, timeout=9,
    ).stdout.strip()
    if not data.isdecimal() or int(data) <= 1:
        raise ValueError("No active Gluetun process namespace")
    return data


def api_call(method: str, payload: dict | None = None) -> dict:
    pid = container_pid()
    cmd = ["/usr/bin/nsenter", "-t", pid, "-n",
           "/usr/bin/python3", str(Path(__file__).resolve()),
           "--internal-api", method]
    receipt = subprocess.run(
        cmd, input=json.dumps(payload) if payload is not None else "",
        capture_output=True, text=True, timeout=25,
    )
    # The internal worker deliberately redacts any Gluetun private key from
    # GET /v1/vpn/settings before producing subprocess output.
    try:
        data = json.loads(receipt.stdout)
    except (json.JSONDecodeError, ValueError):
        raise ValueError("Native VPN API returned no inspectable receipt") from None
    if receipt.returncode != 0:
        raise ValueError("Native VPN API not authorized or unavailable: "+str(data.get("standing","UNKNOWN")))
    return data


def initial_preflight() -> dict:
    subprocess.run(
        ["/usr/bin/python3", str(Path(__file__).resolve().parent/"native_profile.py"), "--verify"],
        check=True, capture_output=True, timeout=20,
    )
    key = protected_key()  # do not log or expose
    del key
    allowed = set(native.parse_allowed_policy(native.ALLOW_POLICY.read_text())["allowedCountries"])
    current = selected_snapshot(api_call("GET"), allowed)
    return {"standing": "NATIVE_API_AUTHORIZED_READONLY", "countryCount": len(current["countries"]),
            "forbiddenCountrySelected": False, "effectAttempted": False}


def guarded_recover() -> dict:
    # A one-shot guarded native settings change, not a second autonomous
    # provider or an unconditional "speed optimization" when users are healthy.
    allowed = set(native.parse_allowed_policy(native.ALLOW_POLICY.read_text())["allowedCountries"])
    plan = quality.observe(hours=48)
    outcome = plan["recommended"]
    if outcome["decision"] != "TRIAL_ONLY_REQUIRES_NATIVE_AUTH_AND_POST_SWITCH_CONSUMER_PROOF":
        return {"standing": outcome["decision"], "effectAttempted": False}
    chosen = outcome["trialCountry"]
    patch = country_patch(chosen, allowed)
    initial_preflight()
    current = selected_snapshot(api_call("GET"), allowed)
    previous = current["countries"]
    if previous == [chosen]:
        return {"standing": "HOLD_ALREADY_SELECTED", "effectAttempted": False}
    # A previous failure cannot justify a fresh global cutover if the user
    # consumer is already healthy again. Revalidate immediately at effect edge.
    try:
        active = observer.observe()
    except (OSError, ValueError, subprocess.SubprocessError):
        active = {"standing": "UNKNOWN_CONSUMER_PROBE_INCOMPLETE"}
    if active.get("standing") == "QUALIFIED_ACTIVE_SAMPLE":
        return {"standing": "HOLD_CONSUMER_RECOVERED", "effectAttempted": False}
    if quality.recent_failure_witness(datetime.now(timezone.utc)) is not True:
        return {"standing": "HOLD_FAILURE_WITNESS_NOT_REPRODUCED", "effectAttempted": False}
    previous_attempt = last_attempt()
    if previous_attempt is not None and datetime.now(timezone.utc)-previous_attempt < COOLDOWN:
        return {"standing": "HOLD_COOLDOWN", "effectAttempted": False}
    started = time.monotonic()
    switched = False
    try:
        mark_attempt()
        switched = True  # a timed-out native PUT might still be applied
        api_call("PUT", patch)
        if selected_snapshot(api_call("GET"), allowed)["countries"] != [chosen]:
            raise ValueError("Native Gluetun settings did not adopt requested candidate")
        # Exact trial effect is checked by new real tunnel and real business
        # origin, not only by HTTP 200 from the API.
        while time.monotonic() - started < 85:
            try:
                checked = observer.observe()
                if checked.get("standing") == "QUALIFIED_ACTIVE_SAMPLE" and (
                    checked.get("currentCatalogCountry") == chosen
                ):
                    return {
                        "standing": "NATIVE_SWITCH_CONSUMED", "country": chosen,
                        "recoverySeconds": round(time.monotonic()-started, 1),
                        "effectAttempted": True, "sourceRuntimeOverride": True,
                    }
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            time.sleep(6)
        raise ValueError("New country did not pass real provider and consumer acceptance")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        # Return to the previous native selection; this is a selection rollback,
        # not a guarantee that the original endpoint IP or TCP sessions survive.
        rollback = "NOT_NEEDED"
        if switched:
            try:
                api_call("PUT", {"provider": {"server_selection": {"countries": previous}}})
                rollback = "REQUESTED"
            except (OSError, ValueError, subprocess.SubprocessError):
                rollback = "FAILED"
        return {"standing": "NATIVE_SWITCH_FAILED", "reasonClass": type(exc).__name__,
                "rollback": rollback, "effectAttempted": switched}


def main() -> int:
    parser = argparse.ArgumentParser()
    choice = parser.add_mutually_exclusive_group(required=False)
    choice.add_argument("--preflight", action="store_true")
    choice.add_argument("--recover", action="store_true")
    parser.add_argument("--internal-api", choices=("GET", "PUT"))
    args = parser.parse_args()
    if args.internal_api:
        return internal_http(args.internal_api)
    if not (args.preflight or args.recover):
        parser.error("select --preflight (default) or --recover")
    with LOCK.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            result = initial_preflight() if args.preflight else guarded_recover()
        except (ValueError, OSError, subprocess.SubprocessError, tomllib.TOMLDecodeError) as e:
            result = {"standing": "HOLD_NATIVE_API_NOT_READY",
                      "reasonClass": type(e).__name__, "effectAttempted": False}
    print(json.dumps(result, sort_keys=True))
    # Healthy/unknown hold is a successful NO-OP decision, not a service
    # failure. Auth/effect failure remains nonzero for native systemd callers.
    if result["standing"] in ("NATIVE_API_AUTHORIZED_READONLY", "NATIVE_SWITCH_CONSUMED"):
        return 0
    if args.recover and result.get("effectAttempted") is False and (
        result["standing"].startswith("HOLD_")
        and result["standing"] != "HOLD_NATIVE_API_NOT_READY"
    ):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
