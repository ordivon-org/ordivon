#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import tool_binding as core

DEFAULT_CATALOG = core.CATALOG


def _legacy_binding(*, equipment_id: str, provider: str, execution_target: str, executable: str, executable_digest: str, provider_identity: Mapping[str, Any], environment: Mapping[str, Any] | None = None) -> dict[str, Any]:
    identity = {
        "schemaVersion": 1,
        "kind": "ordivon.workstation-equipment-binding-identity",
        "equipmentId": equipment_id,
        "provider": provider,
        "executionTarget": execution_target,
        "executable": executable,
        "executableDigest": executable_digest,
        "providerIdentity": dict(provider_identity),
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation-equipment-binding",
        "truthRole": "physical-equipment-projection",
        "equipmentId": equipment_id,
        "state": "AVAILABLE",
        "provider": provider,
        "executionTarget": execution_target,
        "executable": executable,
        "executableDigest": executable_digest,
        "providerIdentity": dict(provider_identity),
        "validUntilMs": None,
        "environment": dict(environment or {}),
        "bindingDigest": core.canonical_digest(identity),
        "authorityBoundary": "Compatibility projection from Workstation v2. It proves exact caller-selected node-local materialization only; Runtime owns execution and the consuming domain owns semantic suitability/success.",
    }


def bind_managed(catalog: Mapping[str, Any], equipment_id: str) -> dict[str, Any]:
    value = core.resolve_managed(catalog, equipment_id)
    rows = catalog.get("managed_equipment")
    spec = rows.get(equipment_id) if isinstance(rows, Mapping) else None
    if not isinstance(spec, Mapping):
        raise RuntimeError(f"managed equipment is not declared: {equipment_id}")
    return _legacy_binding(
        equipment_id=equipment_id,
        provider="workstation.v2.managed-external",
        execution_target=str(value["executionTarget"]),
        executable=str(value["observedExecutable"]),
        executable_digest=str(value["executableDigest"]),
        provider_identity={"configuredExecutable": str(spec.get("executable") or ""), "expectedSha256": str(spec.get("sha256") or "")},
    )


def bind_professional(catalog: Mapping[str, Any], software_id: str, launcher: str) -> dict[str, Any]:
    value = core.resolve_professional(catalog, software_id, launcher)
    return _legacy_binding(
        equipment_id=f"professional:{software_id}:{launcher}",
        provider="workstation.v2.professional-software",
        execution_target=str(value["executionTarget"]),
        executable=str(value["observedExecutable"]),
        executable_digest=str(value["executableDigest"]),
        provider_identity={
            "softwareId": software_id,
            "displayName": value.get("displayName"),
            "category": value.get("category"),
            "softwareProvider": value.get("provider"),
            "launcherName": launcher,
            "configuredExecutable": value.get("configuredExecutable"),
            "versionEvidence": value.get("versionEvidence"),
        },
    )


def _browser_candidates(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    full = sorted(path for path in root.glob("chromium-*/chrome-linux*/chrome") if path.is_file())
    headless = sorted(path for path in root.glob("chromium_headless_shell-*/chrome-headless-shell-linux*/chrome-headless-shell") if path.is_file())
    return [*full, *headless]


def bind_browser(catalog: Mapping[str, Any]) -> dict[str, Any]:
    browser = catalog.get("browser")
    if not isinstance(browser, Mapping):
        raise RuntimeError("browser declaration is unavailable")
    root = Path(str(browser.get("playwright_root") or ""))
    candidates = _browser_candidates(root)
    if not candidates:
        raise RuntimeError("no Workstation v2 Playwright Chromium executable is available")
    full = [path for path in candidates if "chromium_headless_shell-" not in str(path)]
    executable = (full or candidates)[-1].resolve()
    proc = subprocess.run(["/usr/bin/ldd", str(executable)], capture_output=True, text=True, timeout=10, check=False)
    if proc.returncode != 0:
        raise RuntimeError("cannot verify Playwright Chromium ELF linkage")
    missing = [line.strip() for line in proc.stdout.splitlines() if "not found" in line]
    if missing:
        raise RuntimeError("Playwright Chromium has missing ELF dependencies: " + "; ".join(missing))
    return _legacy_binding(
        equipment_id="browser:playwright-chromium",
        provider="workstation.v2.playwright-cache",
        execution_target="local_linux",
        executable=str(executable),
        executable_digest=core.sha256_file(executable),
        provider_identity={"playwrightRoot": str(root), "linkageVerified": True},
        environment={"PLAYWRIGHT_BROWSERS_PATH": str(root)},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Workstation v2 compatibility equipment binding projection")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CATALOG, help="compatibility alias for the binding catalog")
    sub = parser.add_subparsers(dest="command", required=True)
    browser = sub.add_parser("browser"); browser.add_argument("--family", choices=["chromium"], required=True)
    managed = sub.add_parser("managed"); managed.add_argument("--equipment-id", required=True)
    professional = sub.add_parser("professional"); professional.add_argument("--software-id", required=True); professional.add_argument("--launcher", required=True)
    args = parser.parse_args()
    try:
        catalog = core.read_catalog(args.contract)
        if args.command == "managed": value = bind_managed(catalog, args.equipment_id)
        elif args.command == "professional": value = bind_professional(catalog, args.software_id, args.launcher)
        else: value = bind_browser(catalog)
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"command": args.command, "error": str(error)}, ensure_ascii=False, sort_keys=True), file=os.sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
