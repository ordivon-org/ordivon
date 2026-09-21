#!/usr/bin/env python3
"""Render/check/install durable CfT human-session systemd templates."""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

try:
    from cft_human_session import browser_equipment_binding, websockify_equipment_binding
except ModuleNotFoundError:
    from scripts.cft_human_session import (
        browser_equipment_binding,
        websockify_equipment_binding,
    )

ROOT = Path(__file__).resolve().parents[1]
SYSTEMD_ROOT = Path("/etc/systemd/system")
UNIT_NAMES = (
    "ordivon-cft-human-session@.target",
    "ordivon-cft-human-display@.service",
    "ordivon-cft-human-browser@.service",
    "ordivon-cft-human-vnc@.service",
    "ordivon-cft-human-web@.service",
)
AUTHORITY_ROOT = Path("/var/lib/ordivon/human-browser-session-authority")


def _safe_absolute_executable(value: object, label: str) -> Path:
    path = Path(str(value or ""))
    if not path.is_absolute() or any(ch.isspace() for ch in str(path)):
        raise RuntimeError(f"{label} executable path is unsafe")
    return path


def render_units(*, browser: dict[str, Any], websockify: dict[str, Any]) -> dict[str, bytes]:
    if browser.get("equipmentId") != "browser:playwright-chromium":
        raise RuntimeError("unexpected CfT browser equipment identity")
    if browser.get("executionTarget") != "local_linux":
        raise RuntimeError("CfT browser equipment must target local_linux")
    browser_executable = _safe_absolute_executable(browser.get("executable"), "CfT")
    cft_root = browser_executable.parent
    if websockify.get("equipmentId") != "browserless-websockify-0-13-0":
        raise RuntimeError("unexpected websockify equipment identity")
    if websockify.get("executionTarget") != "local_linux":
        raise RuntimeError("websockify equipment must target local_linux")
    websockify_executable = _safe_absolute_executable(
        websockify.get("executable"), "websockify"
    )

    rendered: dict[str, bytes] = {}
    for name in UNIT_NAMES:
        source = ROOT / "systemd" / name
        text = source.read_text(encoding="utf-8")
        if name == "ordivon-cft-human-browser@.service":
            if text.count("@CFT_ROOT@") != 1 or text.count("@CFT_EXECUTABLE@") != 1:
                raise RuntimeError("CfT browser unit placeholder contract changed")
            text = text.replace("@CFT_ROOT@", str(cft_root))
            text = text.replace(
                "@CFT_EXECUTABLE@", f"/opt/ordivon/cft-current/{browser_executable.name}"
            )
        if name == "ordivon-cft-human-web@.service":
            if text.count("@WEBSOCKIFY_EXECUTABLE@") != 1:
                raise RuntimeError("websockify unit placeholder contract changed")
            text = text.replace("@WEBSOCKIFY_EXECUTABLE@", str(websockify_executable))
        if "@CFT_" in text or "@WEBSOCKIFY_" in text:
            raise RuntimeError(f"unresolved human-session unit placeholder: {name}")
        rendered[name] = text.encode("utf-8")
    return rendered


def desired_units() -> dict[str, bytes]:
    return render_units(
        browser=browser_equipment_binding(),
        websockify=websockify_equipment_binding(),
    )


def _atomic(path: Path, raw: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def check(*, systemd_root: Path = SYSTEMD_ROOT) -> dict[str, Any]:
    desired = desired_units()
    issues: list[str] = []
    for name, raw in desired.items():
        path = systemd_root / name
        if not path.is_file() or path.is_symlink():
            issues.append(f"missing:{name}")
            continue
        if path.read_bytes() != raw:
            issues.append(f"drift:{name}")
        if stat.S_IMODE(path.stat().st_mode) != 0o644:
            issues.append(f"mode:{name}")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cft-human-session-deployment",
        "standing": "CURRENT" if not issues else "DRIFT",
        "unitCount": len(desired),
        "issues": issues,
    }


def apply(*, systemd_root: Path = SYSTEMD_ROOT) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise RuntimeError("root authority required")
    desired = desired_units()
    changed: list[str] = []
    for name, raw in desired.items():
        path = systemd_root / name
        if (
            not path.is_file()
            or path.is_symlink()
            or path.read_bytes() != raw
            or stat.S_IMODE(path.stat().st_mode) != 0o644
        ):
            _atomic(path, raw, 0o644)
            changed.append(str(path))
    AUTHORITY_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(AUTHORITY_ROOT, 0o700)
    if changed:
        subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True, timeout=20)
    value = check(systemd_root=systemd_root)
    if value["standing"] != "CURRENT":
        raise RuntimeError(f"CfT human-session deployment is not current: {value['issues']}")
    return {**value, "standing": "MATERIALIZED", "changedPaths": changed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        value = apply() if args.apply else check()
        print(json.dumps(value, sort_keys=True))
        return 0 if value["standing"] in {"CURRENT", "MATERIALIZED"} else 2
    except Exception as error:
        print(json.dumps({"standing": "HOLD", "detail": str(error)}), file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
