#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tomllib
from typing import Any, Mapping

CATALOG = Path(__file__).with_name("software.toml")
WINDOWS_USERS_ROOT = Path(os.environ.get("ORDIVON_WINDOWS_USERS_ROOT", "/mnt/c/Users"))
WINDOWS_MOUNT_ROOT = Path(os.environ.get("ORDIVON_WINDOWS_MOUNT_ROOT", "/mnt"))
WINDOWS_POWERSHELL = Path(os.environ.get("ORDIVON_WINDOWS_POWERSHELL", "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"))


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def read_catalog(path: Path = CATALOG) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _windows_parts(value: str) -> tuple[str, ...]:
    parts = tuple(part for part in value.replace("\\", "/").split("/") if part)
    if not parts or any(part in {".", ".."} for part in parts):
        raise RuntimeError("Windows launcher contains invalid path components")
    return parts


def resolve_windows_path(configured: str, *, users_root: Path = WINDOWS_USERS_ROOT, mount_root: Path = WINDOWS_MOUNT_ROOT) -> Path:
    raw = configured.strip()
    prefix = "%LOCALAPPDATA%\\"
    if raw.upper().startswith(prefix):
        suffix = Path(*_windows_parts(raw[len(prefix):]))
        matches = []
        if users_root.is_dir():
            for home in users_root.iterdir():
                candidate = home / "AppData" / "Local" / suffix
                if candidate.is_file():
                    matches.append(candidate)
        if len(matches) != 1:
            raise RuntimeError(f"expected one mounted LOCALAPPDATA launcher for {configured!r}, found {len(matches)}")
        return matches[0].resolve()
    if len(raw) >= 3 and raw[0].isalpha() and raw[1] == ":" and raw[2] in {"\\", "/"}:
        candidate = mount_root / raw[0].lower() / Path(*_windows_parts(raw[3:]))
        if not candidate.is_file():
            raise RuntimeError(f"declared Windows launcher is unavailable: {candidate}")
        return candidate.resolve()
    raise RuntimeError(f"unsupported Windows launcher projection: {configured!r}")


def _linux_package_version(package: str) -> dict[str, Any]:
    proc = subprocess.run(["/usr/bin/pacman", "-Q", package], capture_output=True, text=True, check=False, timeout=10)
    if proc.returncode != 0:
        return {"standing": "UNKNOWN", "source": "pacman-local-db", "reason": (proc.stderr or proc.stdout).strip()[:500]}
    fields = proc.stdout.strip().split(maxsplit=1)
    return {"standing": "AVAILABLE", "source": "pacman-local-db", "value": fields[1] if len(fields) == 2 else None}


def _mounted_to_windows(path: Path, mount_root: Path = WINDOWS_MOUNT_ROOT) -> str:
    resolved = path.resolve()
    rel = resolved.relative_to(mount_root.resolve())
    parts = rel.parts
    if len(parts) < 2 or len(parts[0]) != 1 or not parts[0].isalpha():
        raise RuntimeError(f"not a mounted Windows drive path: {resolved}")
    return parts[0].upper() + ":\\" + "\\".join(parts[1:])


def _windows_file_version(path: Path) -> dict[str, Any]:
    if not WINDOWS_POWERSHELL.is_file():
        return {"standing": "UNKNOWN", "source": "windows-file-version", "reason": "powershell-provider-unavailable"}
    native = _mounted_to_windows(path)
    escaped = native.replace("'", "''")
    command = "$ErrorActionPreference='Stop'; [System.Diagnostics.FileVersionInfo]::GetVersionInfo('" + escaped + "').FileVersion"
    encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    proc = subprocess.run([str(WINDOWS_POWERSHELL), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], capture_output=True, text=True, check=False, timeout=15)
    value = proc.stdout.strip()
    if proc.returncode != 0 or not value:
        return {"standing": "UNKNOWN", "source": "windows-file-version", "reason": (proc.stderr or proc.stdout).strip()[:500] or f"exit-{proc.returncode}"}
    return {"standing": "AVAILABLE", "source": "windows-file-version", "value": value}


def resolve_professional(catalog: Mapping[str, Any], software_id: str, launcher_name: str | None = None, *, users_root: Path = WINDOWS_USERS_ROOT, mount_root: Path = WINDOWS_MOUNT_ROOT) -> dict[str, Any]:
    rows = catalog.get("professional_software")
    if not isinstance(rows, Mapping) or not isinstance(rows.get(software_id), Mapping):
        raise RuntimeError(f"professional software is not declared: {software_id}")
    spec = rows[software_id]
    launchers = spec.get("launchers")
    if not isinstance(launchers, list) or not launchers:
        raise RuntimeError(f"declared software has no launchers: {software_id}")
    if launcher_name is None:
        if len(launchers) != 1:
            raise RuntimeError(f"launcher must be named for multi-launcher software: {software_id}")
        selected = launchers[0]
    else:
        matches = [row for row in launchers if isinstance(row, Mapping) and row.get("name") == launcher_name]
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one launcher {launcher_name!r} for {software_id}, found {len(matches)}")
        selected = matches[0]
    if not isinstance(selected, Mapping) or not isinstance(selected.get("path"), str):
        raise RuntimeError("launcher declaration is invalid")
    configured = selected["path"]
    platform = str(spec.get("platform") or "")
    if platform == "linux":
        executable = Path(configured).resolve()
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise RuntimeError(f"declared Linux launcher is unavailable: {executable}")
        package = spec.get("package")
        version = _linux_package_version(str(package)) if isinstance(package, str) and package else {"standing":"UNKNOWN","source":"provider-native","reason":"no-package-version-source-declared"}
        target = "local_linux"
    elif platform == "windows":
        executable = resolve_windows_path(configured, users_root=users_root, mount_root=mount_root)
        version = _windows_file_version(executable)
        target = "windows_native"
    else:
        raise RuntimeError(f"unsupported software platform: {platform or 'unknown'}")
    identity = {
        "schemaVersion": 1,
        "softwareId": software_id,
        "launcherName": selected.get("name"),
        "configuredExecutable": configured,
        "observedExecutable": str(executable),
        "executableDigest": sha256_file(executable),
        "executionTarget": target,
        "provider": spec.get("provider"),
        "versionEvidence": version,
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.v2.tool-binding",
        "truthRole": "node-local-materialization-binding",
        "state": "AVAILABLE",
        "displayName": spec.get("display_name"),
        "category": spec.get("category"),
        **identity,
        "bindingDigest": canonical_digest(identity),
        "authorityBoundary": "Workstation v2 proves this caller-selected node-local materialization only. Runtime owns execution admission/Job truth; the consuming domain owns suitability, authorization and semantic success.",
        "nonClaims": ["runtime_execution_admitted", "task_authorized", "domain_suitable", "domain_success", "network_serviceable"],
    }


def resolve_managed(catalog: Mapping[str, Any], equipment_id: str) -> dict[str, Any]:
    rows = catalog.get("managed_equipment")
    if not isinstance(rows, Mapping) or not isinstance(rows.get(equipment_id), Mapping):
        raise RuntimeError(f"managed equipment is not declared: {equipment_id}")
    spec = rows[equipment_id]
    path = Path(str(spec.get("executable") or "")).resolve()
    if not path.is_file():
        raise RuntimeError(f"managed equipment executable is unavailable: {path}")
    digest = sha256_file(path).removeprefix("sha256:")
    expected = str(spec.get("sha256") or "")
    if expected and digest != expected:
        raise RuntimeError(f"managed equipment digest mismatch for {equipment_id}: expected {expected}, observed {digest}")
    identity = {"schemaVersion":1,"equipmentId":equipment_id,"observedExecutable":str(path),"executableDigest":"sha256:"+digest,"executionTarget":str(spec.get("execution_target") or "local_linux")}
    return {"schemaVersion":1,"kind":"ordivon.workstation.v2.tool-binding","truthRole":"node-local-materialization-binding","state":"AVAILABLE",**identity,"bindingDigest":canonical_digest(identity),"nonClaims":["runtime_execution_admitted","task_authorized","domain_suitable","domain_success"]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one exact caller-selected Workstation v2 tool binding")
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    sub = parser.add_subparsers(dest="kind", required=True)
    professional = sub.add_parser("professional")
    professional.add_argument("software_id")
    professional.add_argument("--launcher")
    managed = sub.add_parser("managed")
    managed.add_argument("equipment_id")
    args = parser.parse_args()
    catalog = read_catalog(args.catalog)
    result = resolve_professional(catalog, args.software_id, args.launcher) if args.kind == "professional" else resolve_managed(catalog, args.equipment_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
