from __future__ import annotations

import glob
import json
import os
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    environment: tuple[tuple[str, str], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "equipmentId": self.equipment_id,
            "capability": self.capability,
            "transport": self.transport,
            "executable": self.executable,
            "args": list(self.args),
            "notes": list(self.notes),
            "environment": dict(self.environment),
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


def discover_equipment_for_capability(world: Mapping[str, Any], capability: str) -> dict[str, Any]:
    """Observe only physical candidates relevant to one Studio capability.

    This is deliberately not a cache: every returned candidate is freshly observed, but
    irrelevant Windows/GUI equipment is not probed merely because it exists in the world.
    """
    scoped = dict(world)
    scoped["equipment"] = [
        item for item in world.get("equipment", [])
        if capability in item.get("capabilities", [])
    ]
    return discover_equipment(scoped)


_DIRECT_OPERATION_CAPABILITIES: dict[str, frozenset[str]] = {
    "typst": frozenset({"document.compile.pdf"}),
    "imagemagick": frozenset({"image.resize"}),
    "inkscape": frozenset({"vector.export"}),
    "blender": frozenset({"scene.create", "scene.edit", "scene.render", "animation.render", "asset.export.gltf", "geometry.procedural", "camera.control", "material.control"}),
    "godot": frozenset({"interactive.run.headless", "interactive.script", "state.trace"}),
    "rsvg-convert": frozenset({"svg.rasterize"}),
    "reaper": frozenset({"audio.project.render"}),
}
_PROVIDER_MEDIATED_EQUIPMENT = frozenset({"davinci-resolve"})
_REAPER_PROVIDER_CAPABILITIES = frozenset({"audio.multitrack", "audio.edit", "audio.mix", "audio.master", "audio.automation", "midi.edit", "script.reascript", "control.osc"})
_STUDIO_NATIVE_CAPABILITIES: dict[str, frozenset[str]] = {
    "ffprobe": frozenset({"media.probe", "stream.inspect", "duration.inspect", "codec.inspect"}),
    "ffmpeg": frozenset({"media.probe", "media.transcode", "video.encode", "audio.transform", "image.extract", "timeline.compose-basic", "stream.capture-basic"}),
}


def operation_support(equipment_id: str, capability: str) -> str:
    """Classify whether one advertised capability has a mechanical Agent action path."""
    if equipment_id == "figma":
        return "AUTH_BLOCKED"
    if equipment_id == "touchdesigner":
        return "LICENSE_BLOCKED"
    if capability in _DIRECT_OPERATION_CAPABILITIES.get(equipment_id, frozenset()):
        return "DIRECTLY_INVOCABLE"
    if equipment_id in _PROVIDER_MEDIATED_EQUIPMENT:
        return "PROVIDER_MEDIATED"
    if equipment_id == "reaper" and capability in _REAPER_PROVIDER_CAPABILITIES:
        return "PROVIDER_MEDIATED"
    if capability in _STUDIO_NATIVE_CAPABILITIES.get(equipment_id, frozenset()):
        return "STUDIO_NATIVE"
    if equipment_id in {"stream-deck", "bhaptics"}:
        return "PHYSICAL_UNPROVEN"
    return "DESCRIPTIVE_ONLY"


def operational_readiness(equipment_id: str, present: bool | None, capability: str) -> str:
    """Project Studio operational readiness without converting physical presence into authority."""
    if present is False:
        return "ABSENT"
    if present is None:
        return "UNKNOWN"
    support = operation_support(equipment_id, capability)
    if support == "AUTH_BLOCKED":
        return "AUTH_REQUIRED"
    if support == "LICENSE_BLOCKED":
        return "LICENSE_REQUIRED"
    if support in {"PHYSICAL_UNPROVEN", "DESCRIPTIVE_ONLY"}:
        return "PRESENT_UNPROVEN"
    if equipment_id in {"davinci-resolve", "obs-studio"}:
        return "READY_WITH_STARTUP"
    if equipment_id == "reaper" and capability != "audio.project.render":
        return "READY_WITH_STARTUP"
    return "READY"


def capability_coverage(world: Mapping[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for item in world.get("equipment", []):
        equipment_id = str(item["id"])
        for capability in item.get("capabilities", []):
            status = operation_support(equipment_id, capability)
            counts[status] = counts.get(status, 0) + 1
            rows.append({"equipmentId": equipment_id, "capability": capability, "actionability": status})
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-equipment-capability-coverage",
        "counts": counts,
        "rows": rows,
        "boundary": "Catalog knowledge and executable affordance are distinct. Only DIRECTLY_INVOCABLE, STUDIO_NATIVE or PROVIDER_MEDIATED rows are mechanically actionable without an external authority transition.",
    }


def select_for_capability(world: Mapping[str, Any], capability: str, *, inventory: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    physical: dict[str, bool | None] | None = None
    if inventory is not None:
        physical = {item["id"]: item["present"] for item in inventory.get("equipment", [])}
    retention_order = {"core-equipment": 0, "external-workstation": 1, "specialist-on-demand": 2, "candidate": 3, "challenger": 4, "reject": 5}
    readiness_order = {"READY": 0, "READY_WITH_STARTUP": 1, "AUTH_REQUIRED": 2, "LICENSE_REQUIRED": 3, "PRESENT_UNPROVEN": 4, "UNKNOWN": 5, "ABSENT": 6}
    matches = []
    for item in world.get("equipment", []):
        if capability not in item.get("capabilities", []):
            continue
        equipment_id = str(item["id"])
        present = physical.get(equipment_id) if physical is not None else None
        actionability = operation_support(equipment_id, capability)
        readiness = operational_readiness(equipment_id, present, capability)
        selectable = readiness in {"READY", "READY_WITH_STARTUP"} and actionability in {"DIRECTLY_INVOCABLE", "STUDIO_NATIVE", "PROVIDER_MEDIATED"}
        matches.append(
            {
                "id": equipment_id,
                "family": item["family"],
                "retention": item.get("retention"),
                "present": present,
                "readiness": readiness,
                "actionability": actionability,
                "selectable": selectable,
                "reason": item.get("reason"),
            }
        )
    matches.sort(key=lambda item: (not item["selectable"], readiness_order.get(item["readiness"], 99), retention_order.get(item["retention"], 99), item["id"]))
    return matches


def external_authority_transition(equipment_id: str) -> dict[str, Any] | None:
    """Describe the external authority evidence needed to graduate a blocked provider.

    This is guidance to the owning boundary, not a credential flow and not authority itself.
    """
    if equipment_id == "figma":
        return {
            "owner": "user-plus-figma-auth-provider",
            "state": "AUTH_REQUIRED",
            "automatic": False,
            "requiredEvidence": [
                "fresh authenticated provider identity",
                "one bounded native design read",
                "one bounded native design write with post-write re-observation",
            ],
            "prohibited": ["inventing OAuth success", "moving access tokens into Studio source or Runtime argv"],
        }
    if equipment_id == "touchdesigner":
        return {
            "owner": "user-plus-derivative-license-authority",
            "state": "LICENSE_REQUIRED",
            "automatic": False,
            "requiredEvidence": [
                "fresh current TouchDesigner license/account state",
                "one bounded project open/create",
                "one machine-observable realtime output or operator-state postcondition",
            ],
            "prohibited": ["license bypass", "treating executable presence as licensed capability"],
        }
    return None


def verification_contract(equipment_id: str, capability: str, parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Return the semantic completion evidence required after physical execution.

    The contract is intentionally owner-specific. It never claims completion itself and it
    never reduces provider-native state to process exit status.
    """
    if equipment_id == "blender":
        expected = [str(value) for value in parameters.get("expectedArtifacts", []) if str(value)]
        return {
            "kind": "DECLARED_ARTIFACTS",
            "required": True,
            "ready": bool(expected),
            "artifacts": expected,
            "reason": "Blender can report a Python traceback while exiting zero; every Agent proposal must name the artifacts/state whose existence will establish semantic completion.",
        }
    if equipment_id == "reaper" and capability == "audio.project.render":
        output = parameters.get("expectedOutput")
        return {
            "kind": "RENDER_ARTIFACT",
            "required": True,
            "ready": isinstance(output, str) and bool(output),
            "artifacts": [str(output)] if output else [],
            "reason": "REAPER process exit is insufficient; verify the independently reconstructed render artifact.",
        }
    if equipment_id == "reaper":
        return {
            "kind": "NATIVE_PROJECT_OR_SESSION_STATE",
            "required": True,
            "ready": True,
            "reason": "Observe the declared .rpp/session/ReaScript postcondition after provider action.",
        }
    if equipment_id == "obs-studio":
        return {
            "kind": "STATE_REOBSERVE_AND_RECOVER",
            "required": True,
            "ready": True,
            "reason": "Mutation acknowledgement is not convergence; re-observe intended OBS state and restore the exact prior default-off listener configuration after bounded use.",
        }
    if equipment_id == "davinci-resolve":
        return {
            "kind": "OPERATION_RESULT_RECONCILIATION",
            "required": True,
            "ready": True,
            "reason": "Read the operation-id-bound Resolve result and inspect declared project/artifact postconditions; do not redispatch after response loss.",
        }
    output = parameters.get("output")
    if isinstance(output, str) and output:
        return {
            "kind": "ARTIFACT_EXISTS",
            "required": True,
            "ready": True,
            "artifacts": [output],
            "reason": "Verify the declared deterministic output artifact after process completion.",
        }
    return {
        "kind": "PROCESS_PLUS_DOMAIN_OBSERVATION",
        "required": False,
        "ready": True,
        "reason": "No additional equipment-specific postcondition is required by this narrow plan; Runtime process evidence still does not itself assert Studio semantic quality.",
    }


def propose_operation(
    world: Mapping[str, Any],
    capability: str,
    parameters: Mapping[str, Any],
    *,
    equipment_id: str | None = None,
    local: bool = True,
) -> dict[str, Any]:
    """Compile one truthful Agent-facing proposal without executing it.

    Selection, physical currentness, actionability, exact plan and completion contract are
    projected together so callers do not reconstruct Studio/Workstation folklore.
    """
    inventory = discover_equipment_for_capability(world, capability) if local else None
    matches = select_for_capability(world, capability, inventory=inventory)
    if equipment_id is not None:
        matches = [item for item in matches if item["id"] == equipment_id]
    if not matches:
        raise ValueError(f"no equipment advertises capability: {capability}")
    candidate = matches[0]
    proposal: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.studio-equipment-operation-proposal",
        "capability": capability,
        "candidate": candidate,
        "plan": None,
        "verification": None,
        "authorityTransition": None,
        "ready": False,
        "blockers": [],
    }
    if not candidate["selectable"]:
        proposal["blockers"].append(candidate["readiness"])
        if candidate["actionability"] not in {"DIRECTLY_INVOCABLE", "STUDIO_NATIVE", "PROVIDER_MEDIATED"}:
            proposal["blockers"].append(candidate["actionability"])
        proposal["authorityTransition"] = external_authority_transition(candidate["id"])
        return proposal
    if candidate["actionability"] == "STUDIO_NATIVE":
        proposal["blockers"].append("USE_STUDIO_NATIVE_COMMAND")
        return proposal
    plan = compile_operation(candidate["id"], capability, parameters)
    verification = verification_contract(candidate["id"], capability, parameters)
    proposal["plan"] = plan.as_dict()
    proposal["verification"] = verification
    if verification.get("ready") is not True:
        proposal["blockers"].append("VERIFICATION_CONTRACT_INCOMPLETE")
        return proposal
    proposal["ready"] = True
    return proposal


def _require_existing(path: str) -> str:
    if not Path(path).is_file():
        raise FileNotFoundError(path)
    return path


def _windows_native_argument(path: str) -> str:
    """Translate a WSL-mounted Windows absolute path for a Windows-native process.

    Relative paths intentionally remain relative: WSL interop can project the Runtime
    Workspace as the Windows process working directory, as proven by Blender dogfood.
    """
    if len(path) >= 7 and path.startswith("/mnt/") and path[5].isalpha() and path[6] == "/":
        drive = path[5].upper()
        rest = path[7:].replace("/", "\\")
        return f"{drive}:\\{rest}"
    return path


def _first_existing(*patterns: str) -> str:
    for pattern in patterns:
        for raw in sorted(glob.glob(pattern)):
            if Path(raw).is_file():
                return raw
    raise FileNotFoundError(patterns[0] if patterns else "no equipment path supplied")


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
        binding = _workstation_equipment_binding("game-inkscape-e1", mode="managed")
        if binding is not None:
            environment = tuple(sorted(_binding_environment(binding).items()))
            return EquipmentPlan(
                equipment_id, capability, "process", str(binding["executable"]), tuple(args),
                (f"Resolved through Workstation EquipmentBinding {binding.get('bindingDigest')}; Studio retains vector semantics and Runtime retains execution authority.",),
                environment,
            )
        return EquipmentPlan(equipment_id, capability, "process", _require_existing("/usr/bin/inkscape"), tuple(args))
    if equipment_id == "blender" and capability in {"scene.create", "scene.edit", "scene.render", "animation.render", "asset.export.gltf", "geometry.procedural", "camera.control", "material.control"}:
        script = str(parameters["script"])
        executable = _first_existing(
            "/usr/bin/blender",
            "/mnt/c/Users/*/AppData/Local/Programs/Blender-5.2-Portable/blender.exe",
        )
        args = ("--background", "--factory-startup", "-Y", "--python", script)
        return EquipmentPlan(
            equipment_id,
            capability,
            "process",
            executable,
            args,
            (
                "Blender Python owns native scene mutation; Runtime owns process execution.",
                "Do not infer script success from Blender exit code alone; require the declared artifact/state postcondition.",
                "-Y disables automatic execution embedded in opened .blend files; the explicit --python script remains caller-selected authority.",
            ),
        )
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
        return EquipmentPlan(
            equipment_id,
            capability,
            "provider-descriptor-only",
            None,
            (),
            (
                "E8 proved authenticated obs-websocket semantics once, but AF8 falsified a reliable autonomous startup/shutdown lifecycle under OBS 32.x unclean-shutdown handling.",
                "Keep the WebSocket server disabled by default and treat all current Live actions as descriptive until a real production need re-earns a bounded provider.",
                "Do not infer current Agent actionability from the installed OBS executable or historical dogfood alone.",
            ),
        )
    if equipment_id == "figma":
        return EquipmentPlan(
            equipment_id,
            capability,
            "figma-mcp-or-plugin",
            None,
            (),
            (
                "Prefer the official Figma MCP for Agent-native node/variable/design context when user OAuth authority is available; in-editor plugin writes remain an alternate bounded transport.",
                "Do not claim remote MCP connectivity until the user has completed Figma OAuth consent and a real design read/write round has been observed.",
            ),
        )
    if equipment_id == "reaper":
        executable = _first_existing(
            "/mnt/c/Program Files/REAPER (x64)/reaper.exe",
            "/mnt/c/Users/*/AppData/Local/Programs/REAPER-Portable/reaper.exe",
            "/usr/bin/reaper",
        )
        if capability == "audio.project.render":
            project = _windows_native_argument(str(parameters["project"]))
            return EquipmentPlan(
                equipment_id,
                capability,
                "process",
                executable,
                ("-nosplash", "-renderproject", project),
                ("The persisted .rpp owns native track/item/mix state; verify the rendered output independently after REAPER exits.",),
            )
        if capability == "script.reascript":
            script = str(parameters["script"])
            return EquipmentPlan(
                equipment_id,
                capability,
                "reaper-workstation",
                executable,
                ("-nonewinst", script),
                ("-nonewinst targets an already-running REAPER workstation instance; observe the script's declared postcondition rather than command admission alone.",),
            )
        return EquipmentPlan(
            equipment_id,
            capability,
            "reascript-or-osc",
            executable,
            (),
            (
                "REAPER 7.78 portable is locally validated for ReaScript-created native multitrack project state and independent -renderproject reconstruction.",
                "Use ReaScript/OSC for native DAW state instead of flattening multitrack editing into FFmpeg command composition.",
            ),
        )
    raise ValueError(f"unsupported equipment operation: {equipment_id} {capability}")



_PROVIDER_MECHANICS: dict[str, dict[str, Any]] = {
    "davinci-resolve": {
        "transport": "studio.resolve-adapter",
        "stateAuthority": "davinci-resolve-project",
        "executionAuthority": "runtime-windows-native-plus-studio-adapter",
        "secretBoundary": "none-for-local-adapter",
        "convergence": "operation-result-plus-project/postcondition-inspection",
        "recovery": "operation-id-bound-result-read; restore prior project/cleanup when declared by adapter",
        "defaultLifecycle": "operator-workstation-state-preserved",
    },
    "obs-studio": {
        "transport": "authenticated-obs-websocket-on-windows-loopback",
        "stateAuthority": "obs-live-scene/source/recording-state",
        "executionAuthority": "runtime-windows-controller-process; Studio owns live semantics",
        "secretBoundary": "external-secret-bearing-authority; never Studio source or Runtime argv",
        "convergence": "mutation-response-is-not-convergence; re-observe intended OBS state",
        "recovery": "restore exact prior websocket configuration and verify listener closure",
        "defaultLifecycle": "websocket-server-disabled-by-default",
    },
    "reaper": {
        "transport": "reascript/osc/or-exact-process",
        "stateAuthority": "native-rpp-project-and-current-reaper-session",
        "executionAuthority": "runtime-process; Studio owns audio-project semantics",
        "secretBoundary": "none-by-default",
        "convergence": "inspect declared project/render/session postcondition",
        "recovery": "persist/reopen native .rpp; do not infer state from installer/process exit alone",
        "defaultLifecycle": "portable-specialist-on-demand",
    },
}


def local_provider_surface(world: Mapping[str, Any]) -> dict[str, Any]:
    """Project validated Studio-local provider mechanics without creating another Tool registry.

    The Equipment World remains the semantic source for capabilities. This projection only
    removes provider-folklore from callers; it neither discovers physical equipment nor
    grants execution authority.
    """
    by_id = {str(item.get("id")): item for item in world.get("equipment", [])}
    providers: list[dict[str, Any]] = []
    for equipment_id, mechanics in _PROVIDER_MECHANICS.items():
        item = by_id.get(equipment_id)
        if item is None:
            continue
        providers.append({
            "equipmentId": equipment_id,
            "capabilities": list(item.get("capabilities", [])),
            "retention": item.get("retention"),
            **mechanics,
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.studio-local-provider-surface",
        "truthRole": "studio-semantic-provider-projection",
        "providers": providers,
        "runtimeOwnsPhysicalExecution": True,
        "workstationOwnsPhysicalEquipmentBinding": True,
        "mcpRequired": False,
        "authorityBoundary": "Studio selects and interprets medium-native providers; this surface does not prove physical presence, grant Runtime execution, expose secrets, or create external-provider truth.",
    }

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
