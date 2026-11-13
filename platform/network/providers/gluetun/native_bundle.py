#!/usr/bin/env python3
"""Install only a bounded upstream-Gluetun recovery consumer onto native systemd.

Uses pre-existing two-minute systemd timer, the single current Gluetun
instance, live Prometheus, and official authenticated VPN Settings. It does
not create a new WireGuard tunnel, daemon, proxy or source of credentials.
"""
from __future__ import annotations

import argparse
import filecmp
import json
import os
from pathlib import Path
import subprocess
import sys

SOURCE = Path(__file__).resolve().parent
DEST = Path("/usr/local/libexec/network-v2/gluetun-native")
SVC_NAME = "network-v2-gluetun-owned-reconcile.service"
SOURCE_SVC = SOURCE / "systemd" / SVC_NAME
INSTALLED_SVC = Path("/etc/systemd/system") / SVC_NAME
FILES = (
    "native_profile.py",
    "observe_active.py",
    "quality_history.py",
    "native_switch.py",
    "auth_profile.py",
    "config/exit-allowlist.json",
    "config/exit-selector.json",
)
EFFECT = str(DEST / "native_switch.py")


def run(*args: str, timeout: int = 25) -> str:
    return subprocess.run(
        list(args), check=True, capture_output=True, text=True, timeout=timeout,
    ).stdout.strip()


def validate_source() -> dict[str, object]:
    content = SOURCE_SVC.read_text(encoding="utf-8")
    clause = f"ExecStartPost=/usr/bin/python3 {EFFECT} --recover"
    if content.splitlines().count(clause) != 1:
        raise ValueError("Native reconcile does not invoke exactly one official-switch consumer")
    if "TimeoutStartSec=4min" not in content:
        raise ValueError("Native one-shot timeout cannot cover bounded recovery trial")
    if content.count("ExecStart=/usr/bin/systemctl start network-v2-gluetun-owned.service network-v2-gluetun-owned-adapter.service") != 1:
        raise ValueError("Original provider/adapter native start contract missing")
    for name in FILES:
        file = SOURCE / name
        if not file.is_file() or file.is_symlink():
            raise ValueError(f"Native recovery source is missing: {name}")
    # Do not create a second custom VPN, cron or scheduler.
    if any(word in content for word in ("podman run ", "wg-quick", "sleep ", "http://0.0.0.0")):
        raise ValueError("Native recovery wrongly owns physical tunneling")
    return {"standing": "NATIVE_BUNDLE_SOURCE_VALID", "nonsecretFileCount": len(FILES)}


def copy_payload(dest: Path = DEST) -> None:
    if dest.is_symlink() or (dest.exists() and not dest.is_dir()):
        raise ValueError("Unexpected native recovery bundle directory")
    for relative in FILES:
        path = dest / relative
        path.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
        subprocess.run(
            ["/usr/bin/install", "-m", "0644", str(SOURCE / relative), str(path)],
            check=True, capture_output=True, timeout=15,
        )


def verify(*, dest: Path = DEST, verify_systemd: bool = True) -> dict[str, object]:
    validate_source()
    for relative in FILES:
        if not filecmp.cmp(SOURCE / relative, dest / relative, shallow=False):
            raise ValueError(f"Native recovery source vs installed mismatch: {relative}")
    if verify_systemd:
        if not filecmp.cmp(SOURCE_SVC, INSTALLED_SVC, shallow=False):
            raise ValueError("Native recovery systemd source vs installed mismatch")
        loaded = run("/usr/bin/systemctl", "show", SVC_NAME, "-p", "ExecStartPost")
        if EFFECT not in loaded or "--recover" not in loaded:
            raise ValueError("New native recovery systemd unit not loaded")
    return {"standing": "NATIVE_BUNDLE_INSTALLED_SOURCE_MATCH",
            "nonsecretFileCount": len(FILES),
            "loadedSystemd": verify_systemd}


def install() -> dict[str, object]:
    if os.geteuid() != 0:
        raise ValueError("Native provider recovery installation requires root")
    validate_source()
    # An installed credential file is not enough: require the running
    # official upstream process to actually accept authenticated GET.
    run("/usr/bin/python3", str(SOURCE / "native_profile.py"), "--verify")
    preflight = json.loads(run("/usr/bin/python3",
                               str(SOURCE / "native_switch.py"), "--preflight", timeout=35))
    if preflight.get("standing") != "NATIVE_API_AUTHORIZED_READONLY":
        raise ValueError("Native Gluetun API is not loaded or source matched")
    before = run("/usr/bin/systemctl", "show",
                 "network-v2-gluetun-owned.service", "-p", "MainPID", "--value")
    if not before.isdigit() or int(before) < 2:
        raise ValueError("Provider main process not active")
    copy_payload()
    # Change service bytes only after all script/config payload is installed.
    subprocess.run(
        ["/usr/bin/install", "-m", "0644", str(SOURCE_SVC), str(INSTALLED_SVC)],
        check=True, capture_output=True, timeout=15,
    )
    run("/usr/bin/systemctl", "daemon-reload", timeout=25)
    receipt = verify()
    after = run("/usr/bin/systemctl", "show",
                "network-v2-gluetun-owned.service", "-p", "MainPID", "--value")
    if before != after:
        raise ValueError("Provider PID changed during source-only recovery activation")
    return receipt | {
        "standing": "EXISTING_NATIVE_TIMER_CONSUMER_INSTALLED_LOADED",
        "providerRestarted": False,
        "newTimerCreated": False,
        "newVpnSessionCreated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--validate", action="store_true")
    options.add_argument("--verify", action="store_true")
    options.add_argument("--install", action="store_true")
    args = parser.parse_args()
    try:
        result = (validate_source() if args.validate else
                  install() if args.install else verify())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {"standing": "NATIVE_BUNDLE_UNKNOWN", "reasonClass": type(exc).__name__,
                  "effectConfirmed": False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["standing"] != "NATIVE_BUNDLE_UNKNOWN" else 1


if __name__ == "__main__":
    sys.exit(main())
