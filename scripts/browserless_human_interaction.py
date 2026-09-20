#!/usr/bin/env python3
"""Thin operator transport over Xvfb + x11vnc + noVNC/websockify.

This module does not implement remote-display, WebSocket, browser, or provider semantics.
It only starts/stops the mature bounded service templates for one already-running Browserless
carrier and projects a loopback operator URL. It never performs provider interaction itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess

VALID_INSTANCES = {11, 12, 13}


def validate_instance(value: int | str) -> int:
    try:
        instance = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("human interaction carrier instance must be an integer") from error
    if instance not in VALID_INSTANCES:
        raise ValueError("human interaction carrier instance must be 11, 12, or 13")
    return instance


def units(instance: int) -> tuple[str, str]:
    instance = validate_instance(instance)
    return (
        f"ordivon-browserless-human-vnc@{instance}.service",
        f"ordivon-browserless-human-web@{instance}.service",
    )


def operator_url(instance: int) -> str:
    instance = validate_instance(instance)
    return (
        f"http://127.0.0.1:160{instance}/vnc.html"
        f"?host=127.0.0.1&port=160{instance}&path=websockify&autoconnect=1&resize=scale"
    )


def _systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/systemctl", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _active(unit: str) -> bool:
    return _systemctl("is-active", "--quiet", unit, check=False).returncode == 0


def _http_ready(instance: int, timeout: float = 1.0) -> bool:
    """Observe the host-loopback noVNC endpoint even when called from a carrier netns."""
    url = f"http://127.0.0.1:160{instance}/vnc.html"
    try:
        completed = subprocess.run(
            [
                "/usr/bin/nsenter",
                "--net=/proc/1/ns/net",
                "/usr/bin/curl",
                "--silent",
                "--show-error",
                "--fail",
                "--noproxy",
                "*",
                "--max-time",
                str(float(timeout)),
                "--output",
                "/dev/null",
                "--write-out",
                "%{http_code}",
                url,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=float(timeout) + 1.0,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0 and completed.stdout.strip() == "200"


def observe(instance: int) -> dict:
    instance = validate_instance(instance)
    vnc, web = units(instance)
    vnc_active = _active(vnc)
    web_active = _active(web)
    ready = vnc_active and web_active and _http_ready(instance)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-human-interaction-transport",
        "instance": instance,
        "standing": "READY" if ready else ("PARTIAL" if vnc_active or web_active else "CLOSED"),
        "vncActive": vnc_active,
        "webActive": web_active,
        "operatorHttpReady": ready,
        "operatorURL": operator_url(instance) if ready else None,
        "loopbackOnlyRequired": True,
        "providerEffectAttempted": False,
    }


def open_transport(instance: int) -> dict:
    instance = validate_instance(instance)
    vnc, web = units(instance)
    _systemctl("start", vnc)
    _systemctl("start", web)
    for _ in range(30):
        value = observe(instance)
        if value["standing"] == "READY":
            return value
        __import__("time").sleep(0.1)
    value = observe(instance)
    close_transport(instance)
    raise RuntimeError(f"human interaction transport failed to become READY: {value['standing']}")


def close_transport(instance: int) -> dict:
    instance = validate_instance(instance)
    vnc, web = units(instance)
    _systemctl("stop", web, check=False)
    _systemctl("stop", vnc, check=False)
    return observe(instance)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("open", "observe", "close"))
    parser.add_argument("--instance", required=True)
    args = parser.parse_args()
    try:
        instance = validate_instance(args.instance)
        if args.action == "open":
            value = open_transport(instance)
        elif args.action == "close":
            value = close_transport(instance)
        else:
            value = observe(instance)
        print(json.dumps(value, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps({"schemaVersion": 1, "ok": False, "error": str(exc)}),
            file=__import__("sys").stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
