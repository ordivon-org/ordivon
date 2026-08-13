from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_WORLD = Path("research/equipment/equipment-world.json")
WINDOWS_POWERSHELL = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")


@dataclass(frozen=True)
class EquipmentPlan:
    equipment_id: str
    capability: str
    transport: str
    executable: str | None
    args: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "equipmentId": self.equipment_id,
            "capability": self.capability,
            "transport": self.transport,
            "executable": self.executable,
            "args": list(self.args),
            "notes": list(self.notes),
        }


def load_equipment_world(path: Path = DEFAULT_WORLD) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or value.get("id") != "studio.equipment-world":
        raise ValueError("unsupported equipment world")
    ids = [item["id"] for item in value.get("equipment", [])]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate equipment id")
    return value


def _first_line(value: str) -> str:
    for line in value.splitlines():
        line = line.strip()
        if line:
            return line[:500]
    return ""


def _run_version(executable: Path, args: Sequence[str]) -> str | None:
    try:
        result = subprocess.run(
            [str(executable), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
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
            for path in _discovery_paths(spec):
                if not path.is_file():
                    continue
                if spec.get("versionKind") == "windows-file":
                    version = _windows_file_version(path)
                else:
                    version = _run_version(path, spec.get("versionArgs", ["--version"]))
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


def equipment_by_id(world: Mapping[str, Any], equipment_id: str) -> Mapping[str, Any]:
    for item in world.get("equipment", []):
        if item.get("id") == equipment_id:
            return item
    raise KeyError(equipment_id)


def select_for_capability(world: Mapping[str, Any], capability: str, *, inventory: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    present = None
    if inventory is not None:
        present = {item["id"]: item["present"] for item in inventory.get("equipment", [])}
    order = {"core-equipment": 0, "external-workstation": 1, "specialist-on-demand": 2, "candidate": 3, "challenger": 4, "reject": 5}
    matches = []
    for item in world.get("equipment", []):
        if capability not in item.get("capabilities", []):
            continue
        matches.append(
            {
                "id": item["id"],
                "family": item["family"],
                "retention": item.get("retention"),
                "present": present.get(item["id"]) if present is not None else None,
                "reason": item.get("reason"),
            }
        )
    matches.sort(key=lambda item: (item["present"] is not True, order.get(item["retention"], 99), item["id"]))
    return matches


def _require_existing(path: str) -> str:
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    return path


def compile_operation(equipment_id: str, capability: str, parameters: Mapping[str, Any]) -> EquipmentPlan:
    """Compile one narrow Studio equipment intent into an exact Runtime-ready proposal.

    This function does not execute the program. Runtime remains process authority.
    """
    if equipment_id == "typst" and capability == "document.compile.pdf":
        source = str(parameters["source"])
        output = str(parameters["output"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/typst"), ("compile", source, output))
    if equipment_id == "imagemagick" and capability == "image.resize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/magick"), (input_path, "-resize", f"{width}x{height}!", output))
    if equipment_id == "inkscape" and capability == "vector.export":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        args = [input_path, "--export-filename", output]
        if parameters.get("width") is not None:
            args.extend(["--export-width", str(int(parameters["width"]))])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/inkscape"), tuple(args))
    if equipment_id == "blender" and capability in {"scene.render", "asset.export.gltf", "geometry.procedural"}:
        script = str(parameters["script"])
        args = ("--background", "--factory-startup", "--python", script)
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/blender"), args, ("Blender Python owns scene mutation; Runtime owns process execution.",))
    if equipment_id == "godot" and capability in {"interactive.run.headless", "interactive.script", "state.trace"}:
        script = str(parameters["script"])
        extra = tuple(str(value) for value in parameters.get("args", []))
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/godot"), ("--headless", "--script", script, "--", *extra))
    if equipment_id == "ffmpeg" and capability == "image.resize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/ffmpeg"), ("-v", "error", "-y", "-i", input_path, "-vf", f"scale={width}:{height}", "-frames:v", "1", output))
    if equipment_id == "rsvg-convert" and capability == "svg.rasterize":
        input_path = str(parameters["input"])
        output = str(parameters["output"])
        width = int(parameters["width"])
        height = int(parameters["height"])
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/rsvg-convert"), ("--width", str(width), "--height", str(height), "-o", output, input_path))
    if equipment_id == "davinci-resolve":
        return EquipmentPlan(equipment_id, capability, "existing-studio-adapter", None, (), ("Use `ordivon-studio resolve ...`; current adapter is version-specific and menu-mediated where required.",))
    if equipment_id == "obs-studio":
        return EquipmentPlan(equipment_id, capability, "obs-websocket", None, (), ("Use authenticated obs-websocket through a secret-bearing authority; do not place the password in Studio source or Runtime argv.",))
    if equipment_id == "figma":
        return EquipmentPlan(equipment_id, capability, "figma-plugin-or-rest", None, (), ("In-editor writes belong to a Figma Plugin; external REST calls require explicit OAuth/token authority and plan capability.",))
    if equipment_id == "reaper":
        return EquipmentPlan(equipment_id, capability, "reascript-or-osc", None, (), ("ReaScript/OSC adapter remains candidate until a local REAPER installation is validated.",))
    raise ValueError(f"unsupported equipment operation: {equipment_id} {capability}")


def summarize_trial(
    *,
    equipment_id: str,
    fallback_id: str | None,
    capability_delta: Sequence[str],
    friction_delta: Mapping[str, Any],
    ceiling_delta: Sequence[str],
    costs: Mapping[str, Any],
    evidence_level: str,
) -> dict[str, Any]:
    """Return typed E7 evidence without collapsing heterogeneous value into one scalar."""
    if evidence_level not in {"executed", "ordinary-production", "external-only", "physical-missing"}:
        raise ValueError("invalid evidence level")
    meaningful_friction = any(
        friction_delta.get(key) not in (None, 0, 0.0, False, "none")
        for key in ("manualHandoffsReduced", "commandsReduced", "argumentTokensReduced", "setupStepsReduced", "recoveryStepsReduced", "batchabilityGain")
    ) or (isinstance(friction_delta.get("medianWallTimeRatio"), (int, float)) and friction_delta["medianWallTimeRatio"] < 0.75)
    unique = bool(capability_delta)
    ceiling = bool(ceiling_delta)
    if evidence_level == "physical-missing":
        disposition = "challenger"
    elif evidence_level == "external-only":
        disposition = "candidate"
    elif unique and (costs.get("highPersistentCost") is True or costs.get("guiStateCoupled") is True):
        disposition = "specialist-on-demand"
    elif unique or meaningful_friction:
        disposition = "retain"
    elif ceiling:
        disposition = "specialist-on-demand"
    else:
        disposition = "reject-or-merge"
    return {
        "equipmentId": equipment_id,
        "fallbackId": fallback_id,
        "evidenceLevel": evidence_level,
        "capabilityDelta": list(capability_delta),
        "frictionDelta": dict(friction_delta),
        "qualityCeilingDelta": list(ceiling_delta),
        "costs": dict(costs),
        "decision": disposition,
        "boundary": "Capability, friction, ceiling, and cost remain typed. The decision is a retention rule, not a universal equipment-quality score.",
    }


def median_runtime_ms(command: Sequence[str], *, repeats: int = 5, cwd: Path | None = None) -> float:
    samples: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        subprocess.run(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=60)
        samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    samples.sort()
    return samples[len(samples) // 2]
