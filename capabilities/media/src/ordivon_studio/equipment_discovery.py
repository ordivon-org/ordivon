"""Physical discovery of external creative equipment.

This adapter observes local executables, Workstation-provided bindings and
redacted configuration. It does not select a tool, compile execution
intent, or claim that any generated asset meets a production postcondition.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

WINDOWS_POWERSHELL = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")

def _first_line(value: str) -> str:
    for line in value.splitlines():
        line = line.strip()
        if not line:
            continue
        if set(line) <= set("*-=~_"):
            continue
        return line[:500]
    return ""


def _run_version(executable: Path, args: Sequence[str], environment: Mapping[str, str] | None = None) -> str | None:
    try:
        result = subprocess.run(
            [str(executable), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env={**os.environ, **dict(environment or {}), "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = result.stdout or result.stderr
    return _first_line(text) or None


def _decode_process_bytes(value: bytes) -> str:
    if not value:
        return ""
    for encoding in ("utf-8-sig", "utf-16-le", "gb18030"):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            continue
    return value.decode("utf-8", errors="replace")


def _windows_file_version(path: Path) -> str | None:
    if not WINDOWS_POWERSHELL.is_file():
        return None
    windows_path = str(path).replace("/mnt/c/", "C:/")
    literal = windows_path.replace("'", "''")
    command = f"[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); $v=(Get-Item -LiteralPath '{literal}').VersionInfo; if($v.ProductVersion){{$v.ProductVersion}}else{{$v.FileVersion}}"
    try:
        result = subprocess.run(
            [str(WINDOWS_POWERSHELL), "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=False,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return _first_line(_decode_process_bytes(result.stdout)) or None




def _workstation_equipment_binding(
    equipment_id: str,
    executable: str | None = None,
    *,
    mode: str = "isolated",
) -> dict[str, Any] | None:
    tool = Path(os.environ.get("ORDIVON_EQUIPMENT_BINDING", "/root/tools/bin/equipment-binding"))
    if not tool.is_file() or not os.access(tool, os.X_OK):
        return None
    if mode not in {"isolated", "managed"}:
        raise ValueError(f"unsupported Workstation equipment binding mode: {mode}")
    if mode == "isolated" and not executable:
        raise ValueError("isolated Workstation equipment binding requires executable identity")
    arguments = [str(tool), mode, "--equipment-id", equipment_id]
    if mode == "isolated":
        arguments.extend(["--executable", str(executable)])
    try:
        result = subprocess.run(
            arguments,
            capture_output=True, text=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.workstation-equipment-binding":
        return None
    if value.get("state") != "AVAILABLE" or value.get("executionTarget") != "local_linux":
        return None
    path = value.get("executable")
    if not isinstance(path, str) or not Path(path).is_file():
        return None
    return value


def _binding_environment(binding: Mapping[str, Any]) -> dict[str, str]:
    projected = binding.get("environment")
    if not isinstance(projected, Mapping):
        return {}
    environment: dict[str, str] = {}
    library_dirs = projected.get("libraryDirs")
    if isinstance(library_dirs, list) and all(isinstance(value, str) for value in library_dirs) and library_dirs:
        existing = os.environ.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = ":".join([*library_dirs, *([existing] if existing else [])])
    python_sites = projected.get("pythonSitePackages")
    if isinstance(python_sites, list) and all(isinstance(value, str) for value in python_sites) and python_sites:
        existing = os.environ.get("PYTHONPATH")
        environment["PYTHONPATH"] = ":".join([*python_sites, *([existing] if existing else [])])
    return environment

def _discovery_paths(spec: Mapping[str, Any]) -> list[Path]:
    if "path" in spec:
        return [Path(spec["path"])]
    if "glob" in spec:
        return [Path(value) for value in sorted(glob.glob(spec["glob"]))]
    return []


def _safe_configuration_projection(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    if spec.get("kind") != "glob":
        return []
    results: list[dict[str, Any]] = []
    redacted = set(spec.get("redact", []))
    for raw in sorted(glob.glob(spec["pattern"])):
        path = Path(raw)
        row: dict[str, Any] = {"path": str(path), "exists": path.is_file()}
        if path.is_file() and path.suffix.lower() == ".json":
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                value = None
            if isinstance(value, dict):
                projection: dict[str, Any] = {}
                for key, item in value.items():
                    if key in redacted or "password" in key.lower() or "token" in key.lower() or "secret" in key.lower():
                        projection[key] = "<redacted-present>" if item else "<redacted-empty>"
                    elif isinstance(item, (str, int, float, bool)) or item is None:
                        projection[key] = item
                row["safeProjection"] = projection
        results.append(row)
    return results


def discover_equipment(world: Mapping[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for item in world.get("equipment", []):
        candidates: list[dict[str, Any]] = []
        for spec in item.get("discovery", []):
            if spec.get("kind") in {"workstation-isolated-binding", "workstation-managed-binding"}:
                binding_mode = "managed" if spec.get("kind") == "workstation-managed-binding" else "isolated"
                binding = _workstation_equipment_binding(
                    str(spec["equipmentId"]),
                    str(spec["executable"]) if binding_mode == "isolated" else None,
                    mode=binding_mode,
                )
                if binding is not None:
                    path = Path(str(binding["executable"]))
                    version = _run_version(path, spec.get("versionArgs", ["--version"]), _binding_environment(binding))
                    candidates.append({
                        "path": str(path), "version": version, "platform": spec.get("platform"),
                        "provider": binding.get("provider"), "bindingDigest": binding.get("bindingDigest"),
                        "providerIdentity": binding.get("providerIdentity"), "validUntilMs": binding.get("validUntilMs"),
                    })
                continue
            for path in _discovery_paths(spec):
                if not path.is_file():
                    continue
                if spec.get("versionKind") == "windows-file":
                    version = _windows_file_version(path)
                else:
                    environment = spec.get("environment") if isinstance(spec.get("environment"), Mapping) else None
                    version = _run_version(path, spec.get("versionArgs", ["--version"]), environment)
                candidates.append({"path": str(path), "version": version, "platform": spec.get("platform")})
        configuration: list[dict[str, Any]] = []
        for spec in item.get("configuration", []):
            configuration.extend(_safe_configuration_projection(spec))
        records.append(
            {
                "id": item["id"],
                "family": item["family"],
                "present": bool(candidates),
                "candidates": candidates,
                "configuration": configuration,
                "capabilities": item.get("capabilities", []),
                "retention": item.get("retention"),
                "reason": item.get("reason"),
            }
        )
    return {"schemaVersion": 1, "kind": "ordivon.studio-equipment-inventory", "equipment": records}
